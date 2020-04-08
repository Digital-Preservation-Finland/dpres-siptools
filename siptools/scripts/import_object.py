"""Command line tool for importing digital objects"""
from __future__ import unicode_literals

import datetime
import fnmatch
import os
import platform
import sys
from uuid import uuid4
import pkg_resources

import click
import six

import premis
from siptools.mdcreator import MetsSectionCreator
from siptools.utils import scrape_file, calc_checksum
from siptools.scripts.premis_event import premis_event
from siptools.scripts.create_agent import create_agent

click.disable_unicode_literals_warning = True

ALLOWED_CHARSETS = ['ISO-8859-15', 'UTF-8', 'UTF-16', 'UTF-32']

DEFAULT_VERSIONS = {
    'text/xml': '1.0',
    'text/plain': '',
    'text/csv': '',
    'image/tiff': '6.0',
    'application/vnd.oasis.opendocument.text': '1.0',
    'application/vnd.oasis.opendocument.spreadsheet': '1.0',
    'application/vnd.oasis.opendocument.presentation': '1.0',
    'application/vnd.oasis.opendocument.graphics': '1.0',
    'application/vnd.oasis.opendocument.formula': '1.0',
    'application/vnd.openxmlformats-officedocument'
    '.wordprocessingml.document': '15.0',
    'application/vnd.openxmlformats-officedocument'
    '.spreadsheetml.sheet': '15.0',
    'application/vnd.openxmlformats-officedocument'
    '.presentationml.presentation': '15.0',
    'application/msword': '11.0',
    'application/vnd.ms-excel': '11.0',
    'application/vnd.ms-powerpoint': '11.0',
    'audio/x-wav': '',
    'video/mp4': '',
    'image/jp2': '',
    'video/dv': '',
    'audio/mp4': '',
    'video/MP1S': '',
    'video/MP2P': '',
    'video/MP2T': '',
}

# For mimetypes that has no version applicable for them.
NO_VERSION = '(:unap)'

# For cases where scraper does not know the version
UNKNOWN_VERSION = '(:unav)'


@click.command()
@click.argument('filepaths', nargs=-1, type=str)
@click.option(
    '--workspace', type=click.Path(exists=True), default='./workspace/',
    metavar='<WORKSPACE PATH>',
    help="Workspace directory for the metadata files. "
         "Defaults to ./workspace")
@click.option(
    '--base_path', type=click.Path(exists=True), default='.',
    metavar='<BASE PATH>',
    help="Source base path of digital objects. If used, give objects in "
         "relation to this base path.")
@click.option(
    '--skip_wellformed_check', is_flag=True,
    help='Skip file format well-formed check')
@click.option(
    '--charset', type=str, metavar='<CHARSET>',
    help='Charset encoding of a file')
@click.option(
    '--file_format', nargs=2, type=str,
    metavar='<MIMETYPE> <FORMAT VERSION>',
    help='Mimetype and file format version of a file. Use "" for empty '
         'version string.')
@click.option(
    '--format_registry', type=str, nargs=2,
    metavar='<REGISTRY NAME> <REGISTRY KEY>',
    help='The format registry name and key of the digital object')
@click.option(
    '--identifier', nargs=2, type=str,
    metavar='<IDENTIFIER TYPE> <IDENTIFIER VALUE>',
    help='The identifier type and value of a digital object')
@click.option(
    '--checksum', nargs=2, type=str,
    metavar='<CHECKSUM ALGORITHM> <CHECKSUM VALUE>',
    help='Checksum algorithm and value of a given file')
@click.option(
    '--date_created', type=str,
    metavar='<EDTF TIME>',
    help='The actual or approximate date and time the object was created')
@click.option(
    '--order', type=int,
    metavar='<ORDER NUMBER>',
    help='Order number of the digital object')
@click.option(
    '--stdout', is_flag=True, help='Print result also to stdout')
# pylint: disable=too-many-arguments
def main(**kwargs):
    """Import files to generate digital objects. If attributes --charset,
    --file_format, --identifier, --checksum or --date_created are not given,
    then these are created automatically.

    FILEPATHS: Files or a directory to import, relative path in relation to
    current directory or to --base_path. It depends on your attributes whether
    you may give several files or a single file. For example --checksum and
    --identifier are file dependent metadata, and if these are used, then use
    the script only for one file.
    """
    import_object(**kwargs)
    return 0


def _attribute_values(given_params):
    """
    Give attribute values as a dict for the script.

    :given_params: Arguments as dict.
    :returns: Attribute value dict
    """
    attributes = {
        "filepaths": given_params["filepaths"],
        "workspace": "./workspace/",
        "base_path": ".",
        "skip_wellformed_check": False,
        "charset": None,
        "file_format": (),
        "format_registry": (),
        "identifier": (),
        "checksum": (),
        "date_created": None,
        "order": None,
        "stdout": False,
    }
    for key in given_params:
        if given_params[key]:
            attributes[key] = given_params[key]

    return attributes


def import_object(**kwargs):
    """Import files to generate digital objects. If attributes charset,
    file_format, identifier, checksum or date_created are not given,
    then these are created automatically.

    :attributes: Given arguments
                 filepaths: Files or a directory to import
                 workspace: Workspace path
                 base_path: Base path of digital objects
                 skip_wellformed_check: True skips well-formedness checking
                 charset: Character encoding of a file,
                 file_format: File format and version (tuple) of a file,
                 format_registry: Format registry name and value (tuple),
                 identifier: File identifier type and value (tuple),
                 checksum: Checksum algorithm and value (tuple),
                 date_created: Creation date of a file,
                 order: Order number of a file,
                 stdout: True prints output to stdout
    :returns: Dictionary of the scraped file metadata
    """
    attributes = _attribute_values(kwargs)
    # Loop files and create premis objects
    files = collect_filepaths(dirs=attributes["filepaths"],
                              base=attributes["base_path"])
    creator = PremisCreator(attributes["workspace"])
    agents = set()
    for filepath in files:

        # If the given path is an absolute path and base_path is current
        # path (i.e. not given), relpath will return ../../.. sequences, if
        # current path is not part of the absolute path. In such case we will
        # use the absolute path for filerel and omit base_path relation.
        if attributes["base_path"] not in ['.']:
            filerel = os.path.relpath(filepath, attributes["base_path"])
        else:
            filerel = filepath

        properties = {}
        if attributes["order"] is not None:
            properties['order'] = six.text_type(attributes["order"])

        (_, scraper_info) = creator.add_premis_md(
            filepath, attributes, filerel=filerel, properties=properties)
        for index in scraper_info:
            agents.add(_parse_scraper_tools(scraper_info[index]))

    creator.write(stdout=attributes["stdout"])

    # Create events documenting the technical metadata creation
    _create_events(
        workspace=attributes["workspace"],
        base_path=attributes["base_path"],
        event_targets=attributes["filepaths"],
        checksum_event=not bool(attributes["checksum"]),
        validation_event=not attributes["skip_wellformed_check"],
        identification_event=not bool(attributes["file_format"]),
        agents=agents
    )


class PremisCreator(MetsSectionCreator):
    """Subclass of MetsSectionCreator, which generates PREMIS metadata
    for files and streams.
    """

    def add_premis_md(
            self, filepath, attributes, filerel=None, properties=None):
        """
        Create metadata for PREMIS metadata. This method:
        - Scrapes a file
        - Creates PREMIS metadata with amd references for a file
        - Creates PREMIS metadata with amd references for streams in a file
        - Returns stream dict from scraper

        :filepath: Full path to file (including base_path)
        :attributes: The following keys
                     skip_wellformed_check: True skips well-formedness checking
                     charset: Character encoding of a file,
                     file_format: File format and version (tuple) of a file,
                     format_registry: Format registry name and value (tuple),
                     identifier: File identifier type and value (tuple),
                     checksum: Checksum algorithm and value (tuple),
                     date_created: Creation date of a file
        :filerel: Relative path from base_path to file
        :returns: Stream dict and info from file-scraper as a tuple
        """
        if not attributes["file_format"]:
            mimetype = None
            version = None
        else:
            mimetype = attributes["file_format"][0]
            version = attributes["file_format"][1]

        (streams, info) = scrape_file(
            filepath=filepath,
            skip_well_check=attributes["skip_wellformed_check"],
            mimetype=mimetype,
            version=version,
            charset=attributes["charset"],
            skip_json=True
        )

        # Add new properties of a file for other script files, e.g. structMap
        if properties:
            streams[0]['properties'] = properties

        premis_elem = create_premis_object(filepath, streams, **attributes)
        self.add_md(premis_elem, filerel, given_metadata_dict=streams)
        premis_list = create_streams(streams, premis_elem)

        if premis_list is not None:
            for index, premis_stream in six.iteritems(premis_list):
                self.add_md(
                    premis_stream, filerel, index, given_metadata_dict=streams)

        return (streams, info)

    # pylint: disable=too-many-arguments
    def write(self, mdtype="PREMIS:OBJECT", mdtypeversion="2.3",
              othermdtype=None, section=None, stdout=False,
              file_metadata_dict=None,
              ref_file="import-object-md-references.xml"):
        """
        Write PREMIS metadata.
        """
        super(PremisCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion,
            file_metadata_dict=file_metadata_dict, ref_file=ref_file
        )


def create_streams(streams, premis_file):
    """Create PREMIS objects for streams

    :streams: Stream dict
    :premis_file: Created PREMIS XML file for the digital object file
    :returns: List of PREMIS etree objects
    """
    if len(streams) < 2:
        return None

    premis_list = {}
    for index, stream in six.iteritems(streams):
        if stream['stream_type'] not in ['video', 'audio']:
            continue

        id_value = six.text_type(uuid4())
        identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=id_value)
        premis_format_des = premis.format_designation(
            stream['mimetype'], stream['version'])
        premis_format = premis.format(child_elements=[premis_format_des])
        premis_objchar = premis.object_characteristics(
            child_elements=[premis_format])
        el_premis_object = premis.object(
            identifier, child_elements=[premis_objchar], bitstream=True)

        premis_list[index] = el_premis_object

        premis_file.append(
            premis.relationship('structural', 'includes', el_premis_object))

    return premis_list


def check_metadata(mimetype, version, streams, fname):
    """
    Check that we will not get None nor (:unav) values to mimetype and
    version. Check that multiple streams are found and found only in
    video containers.

    :mimetype: MIME type
    :version: File format version
    :streams: Streams returned from Scraper
    :fname: File name of the digital object
    :raises: ValueError if metadata checking results errors
    """
    if mimetype is None:
        raise ValueError('MIME type could not be identified for '
                         'file %s' % fname)
    if version is None:
        raise ValueError('File format version could not be identified for '
                         'file %s' % fname)
    if streams[0]['stream_type'] not in ['videocontainer'] and \
            len(streams) > 1:
        raise ValueError('The file contains multiple streams which '
                         'is supported only for video containers.')
    elif streams[0]['stream_type'] in ['videocontainer'] and \
            len(streams) < 2:
        raise ValueError('Video container format without contained streams '
                         'found.')


# pylint: disable=too-many-locals
def create_premis_object(fname, streams, **attributes):
    """
    Create Premis object for given file.

    :fname: File name of the digital object
    :streams: Streams from the Scraper
    :attributes: The following keys:
                 charset: Character encoding of a file,
                 file_format: File format and version (tuple) of a file,
                 format_registry: Format registry name and value (tuple),
                 identifier: File identifier type and value (tuple),
                 checksum: Checksum algorithm and value (tuple),
                 date_created: Creation date of a file
    :returns: PREMIS object as etree
    :raises: ValueError if character set is invalid for text files.
    """
    attributes = _attribute_values(attributes)
    if not attributes["checksum"]:
        attributes["checksum"] = ("MD5", calc_checksum(fname))
    date_created = attributes["date_created"] or creation_date(fname)
    if streams[0]['stream_type'] == 'text':
        charset = attributes["charset"] or streams[0]['charset']
    else:
        charset = None

    if not attributes["file_format"]:
        if streams[0]["version"] and streams[0]["version"] != UNKNOWN_VERSION:
            format_version = '' if streams[0]["version"] == NO_VERSION else \
                streams[0]["version"]
        else:
            format_version = DEFAULT_VERSIONS.get(streams[0]["mimetype"], None)

        file_format = (streams[0]["mimetype"], format_version)
    else:
        file_format = (attributes["file_format"][0],
                       attributes["file_format"][1])

    check_metadata(file_format[0], file_format[1], streams, fname)

    charset_mime = ""
    if charset:
        if charset not in ALLOWED_CHARSETS:
            raise ValueError('Invalid charset.')
        charset_mime = '; charset={}'.format(charset)

    if attributes["identifier"]:
        identifier_type = attributes["identifier"][0]
        identifier_value = attributes["identifier"][1]
    else:
        identifier_type = 'UUID'
        identifier_value = six.text_type(uuid4())

    object_identifier = premis.identifier(
        identifier_type=identifier_type,
        identifier_value=identifier_value
    )

    premis_fixity = premis.fixity(attributes["checksum"][1],
                                  attributes["checksum"][0])
    premis_format_des = premis.format_designation(
        file_format[0] + charset_mime, file_format[1])
    if not attributes["format_registry"]:
        premis_format = premis.format(child_elements=[premis_format_des])
    else:
        premis_registry = premis.format_registry(
            attributes["format_registry"][0],
            attributes["format_registry"][1])
        premis_format = premis.format(child_elements=[premis_format_des,
                                                      premis_registry])
    premis_date_created = premis.date_created(date_created)
    premis_create = \
        premis.creating_application(child_elements=[premis_date_created])
    premis_objchar = premis.object_characteristics(
        child_elements=[premis_fixity, premis_format, premis_create])

    # Create object element
    el_premis_object = premis.object(
        object_identifier, child_elements=[premis_objchar])

    return el_premis_object


def collect_filepaths(dirs=None, pattern='*', base='.'):
    """
    Collect file paths recursively from given directory.

    :dirs: Directories from arguments
    :pattern: Filter to match the file names
    :base: Base path (see --base_path)
    :raises: IOError if given path does not exist.
    """
    if dirs is None:
        dirs = ['.']
    files = []

    for directory in dirs:
        directory = os.path.normpath(os.path.join(base, directory))
        if os.path.isdir(directory):
            files += [os.path.join(looproot, filename)
                      for looproot, _, filenames in os.walk(directory)
                      for filename in filenames
                      if fnmatch.fnmatch(filename, pattern)]
        elif os.path.isfile(directory):
            files += [directory]
        else:
            raise IOError

    return files


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it
    was last modified if that isn't possible.  See
    http://stackoverflow.com/a/39501288/1709587 for explanation.

    :path_to_file: File path
    :returns: Timestamp for a file
    """
    if platform.system() == 'Windows':
        return datetime.datetime.fromtimestamp(
            os.path.getctime(path_to_file)).isoformat()
    else:
        stat = os.stat(path_to_file)
        try:
            return datetime.datetime.fromtimestamp(
                stat.st_birthtime).isoformat()
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()


def _parse_scraper_tools(scraper_info):
    """Helper function to parse the used third party components used
    when identifying files and extracting technical metadata to be used
    as agents when creating events documenting the packaging process.

    :returns: a list of agents
    """
    scraper_version = pkg_resources.get_distribution('file-scraper').version
    agent_name = scraper_info['class']
    agent_version = scraper_version
    tools = ''
    tools_list = []
    if 'tools' in scraper_info:
        for tool in scraper_info['tools']:
            tools_list.append(tool)
    if tools_list:
        tools = 'Used tools (name-version): ' + ', '.join(tools_list)
    return (agent_name, agent_version, tools)


# TODO: The checksum_event, validation_event and identifiecation_event are
# placeholders. Creating events based on these boolean values is not in the
# scope of this ticket SAPA-381
def _create_events(
        workspace,
        base_path,
        event_targets,
        agents=None,
        checksum_event=False,
        validation_event=False,
        identification_event=False):
    """Function to create events documenting the extraction of technical
    metadata as well as the potential message digest calculation and
    the identification and validation of digital objects.

    :workspace: The path to the workspace
    :base_path: Base path (see --base_path)
    :event_targets: The targets of the metadata creation,
                    i.e. "filepaths"
    :agents: The software name and version used to extract the metadata
             as a tuple
    :checksum_event: Boolean to indicate whether the message digest of
                     digital objects were calculated. False if they were
                     given to the script.
    :validation_event:  Boolean to indicate whether the digital objects
                        were validated during the extraction of technical
                        metadata.
    :identification_event: Boolean to indicate whether the digital
                           objects were identified (mimetype and version)
                           during the extraction of technical metadata.
    """
    for agent in agents:
        create_agent(
            workspace=workspace,
            agent_name=agent[0],
            agent_version=agent[1],
            agent_note=agent[2],
            agent_type='software',
            agent_role='executing program',
            create_agent_file='import-object')
    event_datetime = datetime.datetime.now().isoformat()
    for event_target in event_targets:
        premis_event(event_type="metadata extraction",
                     event_datetime=event_datetime,
                     event_detail=("Technical metadata extraction as premis "
                                   "metadata from digital objects"),
                     event_outcome="success",
                     event_outcome_detail=("Premis metadata successfully "
                                           "created from extracted technical "
                                           "metadata."),
                     workspace=workspace,
                     base_path=base_path,
                     event_target=event_target,
                     create_agent_file='import-object')


if __name__ == "__main__":
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
