"""Command line tool for importing digital objects."""

import datetime
import fnmatch
import os
import platform
import sys
from uuid import uuid4
import errno

import click

import file_scraper
import premis
from siptools.mdcreator import MetsSectionCreator
from siptools.utils import scrape_file, calc_checksum
from siptools.scripts.premis_event import premis_event, create_premis_event
from siptools.scripts.create_agent import create_agent
from siptools.utils import generate_digest, encode_path


click.disable_unicode_literals_warning = True

ALLOWED_CHARSETS = ['ISO-8859-15', 'UTF-8', 'UTF-16', 'UTF-32']

# For mimetypes that has no version applicable for them.
NO_VERSION = '(:unap)'

# For cases where scraper does not know the version
UNKNOWN_VERSION = '(:unav)'

# Supported bit-level preservation types
SUPPLEMENTARY_TYPES = ["xml_schema"]


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
    help='Skip file format well-formed check.')
@click.option(
    '--charset', type=str, metavar='<CHARSET>',
    help='Charset encoding of a file.')
@click.option(
    '--original_name', type=str, metavar='<NAME>',
    help='Original name of the file.')
@click.option(
    '--file_format', nargs=2, type=str,
    metavar='<MIMETYPE> <FORMAT VERSION>',
    help='Mimetype and file format version of a file. Use "" for empty '
         'version string.')
@click.option(
    '--format_registry', type=str, nargs=2,
    metavar='<REGISTRY NAME> <REGISTRY KEY>',
    help='The format registry name and key of the digital object.')
@click.option(
    '--identifier', nargs=2, type=str,
    metavar='<IDENTIFIER TYPE> <IDENTIFIER VALUE>',
    help='The identifier type and value of a digital object.')
@click.option(
    '--checksum', nargs=2, type=str,
    metavar='<CHECKSUM ALGORITHM> <CHECKSUM VALUE>',
    help='Checksum algorithm and value of a given file.')
@click.option(
    '--date_created', type=str,
    metavar='<ISO-8601 TIME>',
    help='The actual or approximate date and time the object was created.')
@click.option(
    '--creating_application', nargs=2, type=str,
    metavar='<SOFTWARE NAME> <SOFTWARE VERSION>',
    help='The software and software version that was used to create the '
         'object. Use "" for empty version string.')
@click.option(
    '--order', type=int,
    metavar='<ORDER NUMBER>',
    help='Order number of the digital object.')
@click.option(
    '--event_datetime', type=str,
    metavar='<EVENT DATETIME>',
    help='Timestamp of the event documenting the script actions.')
@click.option(
    '--event_target', type=str,
    metavar='<EVENT TARGET>',
    help='Target for events, if it is not given the package root is used.')
@click.option(
    '--stdout', is_flag=True, help='Print result also to stdout.')
@click.option(
    '--bit_level', is_flag=True,
    help='Mark only for bit-level preservation. If used, then --file_format '
         'is mandatory.')
@click.option(
    '--supplementary', type=click.Choice(SUPPLEMENTARY_TYPES),
    multiple=True, metavar='<SUPPLEMENTARY TYPE>',
    help='Used to mark supplementary files, files that are not part of the '
         'contents per se, but are to be included in the SIP. May be used '
         'multiple times, but currently only "xml_schema" type is supported.')
# pylint: disable=too-many-arguments
def main(**kwargs):
    """Import files to generate digital objects.

    If attributes --charset, --file_format, --identifier, --checksum or
    --date_created are not given, then these are created automatically.

    FILEPATHS: Files or a directory to import, relative path in relation
    to current directory or to --base_path. It depends on your
    attributes whether you may give several files or a single file. For
    example --checksum and --identifier are file dependent metadata, and
    if these are used, then use the script only for one file.
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
        "original_name": None,
        "file_format": (),
        "format_registry": (),
        "identifier": (),
        "checksum": (),
        "date_created": None,
        "creating_application": (),
        "order": None,
        "event_datetime": None,
        "event_target": None,
        "stdout": False,
        "bit_level": None,
        "supplementary": ()
    }
    for key in given_params:
        if given_params[key]:
            attributes[key] = given_params[key]

    if attributes["bit_level"]:
        if not attributes["file_format"]:
            raise ValueError(
                "Argument --file_format is mandatory if --bit_level is given.")
        attributes["skip_wellformed_check"] = True

    return attributes


def import_object(**kwargs):
    """Import files to generate digital objects.

    If attributes charset, file_format, identifier, checksum or
    date_created are not given, then these are created automatically.

    :attributes: Given arguments
                 filepaths: Files or a directory to import
                 workspace: Workspace path
                 base_path: Base path of digital objects
                 skip_wellformed_check: True skips well-formedness
                                        checking
                 charset: Character encoding of a file
                 original_name: Original filename
                 file_format: File format and version (tuple) of a file
                 format_registry: Format registry name and value (tuple)
                 identifier: File identifier type and value (tuple)
                 checksum: Checksum algorithm and value (tuple)
                 date_created: Creation date of a file
                 creating_application: Software and its version that created
                                       the file
                 order: Order number of a file
                 event_datetime: Timestamp of the events. Defaults to
                                 current date YYYY-MM-DD.
                 event_target: The target of the events
                 stdout: True prints output to stdout
                 bit_level: True marks files for bit-level preservation only
                 supplementary: Object type for supplementary files
    """
    attributes = _attribute_values(kwargs)
    date_now = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    # Loop files and create premis objects
    files = collect_filepaths(dirs=attributes["filepaths"],
                              base=attributes["base_path"])
    creator = PremisCreator(attributes["workspace"])
    agents = []
    for filepath in files:

        # If the given path is an absolute path and base_path is current
        # path (i.e. not given), relpath will return ../../.. sequences,
        # if current path is not part of the absolute path. In such case
        # we will use the absolute path for filerel and omit base_path
        # relation.
        if attributes["base_path"] not in ['.']:
            filerel = os.path.relpath(filepath, attributes["base_path"])
        else:
            filerel = filepath

        properties = {}
        if attributes["order"] is not None:
            properties['order'] = str(attributes["order"])
        properties["bit_level"] = attributes["bit_level"]
        properties["supplementary"] = attributes["supplementary"]

        (streams, scraper_info) = creator.add_premis_md(
            filepath, attributes, filerel=filerel, properties=properties)
        for index in scraper_info:
            agents.append(_parse_scraper_tools(scraper_info[index]))

        grade = streams[0]['properties']['grade']

    is_native = grade in (
        file_scraper.defaults.BIT_LEVEL,
        file_scraper.defaults.BIT_LEVEL_WITH_RECOMMENDED
    )

    is_validated = (
        not bool(attributes["skip_wellformed_check"])
        and not is_native
    )

    creator.write(stdout=attributes["stdout"])

    # Resolve event target
    event_target = attributes["event_target"]
    if not event_target:
        event_target = "."

    # Resolve event datetime
    event_datetime = None
    if attributes["event_datetime"] is None:
        event_datetime = date_now
    else:
        event_datetime = attributes["event_datetime"]

    # Create events documenting the technical metadata creation
    _create_events(
        workspace=attributes["workspace"],
        base_path=attributes["base_path"],
        event_datetime=event_datetime,
        event_target=event_target,
        identification_event=not bool(attributes["file_format"]),
        validation_event=is_validated,
        checksum_event=not bool(attributes["checksum"]),
        agents=agents
    )


class PremisCreator(MetsSectionCreator):
    """PREMIS metadata generator for files and streams."""

    def add_premis_md(
            self, filepath, attributes, filerel=None, properties=None):
        """
        Create metadata for PREMIS metadata.

        This method:
        - Scrapes a file
        - Creates PREMIS metadata with amd references for a file
        - Creates PREMIS metadata with amd references for streams in a
          file
        - Returns stream dict from scraper

        :filepath: Full path to file (including base_path)
        :attributes: The following keys
                     skip_wellformed_check: True skips well-formedness
                                            checking
                     charset: Character encoding of a file
                     original_nme: Original filename
                     file_format: File format and version (tuple) of a
                                  file
                     format_registry: Format registry name and value
                                      (tuple)
                     identifier: File identifier type and value (tuple)
                     checksum: Checksum algorithm and value (tuple)
                     date_created: Creation date of a file
        :filerel: Relative path from base_path to file
        :returns: Stream dict and info dict from file-scraper as a tuple
        """
        if not attributes["file_format"]:
            mimetype = "(:unav)"
            version = "(:unav)"
        else:
            mimetype = attributes["file_format"][0]
            version = attributes["file_format"][1]

        (streams, info, grade) = scrape_file(
            filepath=filepath,
            skip_well_check=attributes["skip_wellformed_check"],
            mimetype=mimetype,
            version=version,
            charset=attributes["charset"],
            skip_json=True
        )

        # Add new properties of a file for other script files, e.g.
        # structMap
        streams[0]['properties'] = {'grade': grade}
        if properties:
            streams[0]['properties'].update(properties)

        premis_elem = create_premis_object(filepath, streams, **attributes)
        self.add_md(premis_elem, filerel, given_metadata_dict=streams)
        premis_list = create_streams(streams, premis_elem)

        if premis_list is not None:
            for index, premis_stream in premis_list.items():
                self.add_md(
                    premis_stream, filerel, index, given_metadata_dict=streams)

        return (streams, info)

    # pylint: disable=too-many-arguments
    def write(self, mdtype="PREMIS:OBJECT", mdtypeversion="2.3",
              othermdtype=None, section=None, stdout=False,
              file_metadata_dict=None,
              ref_file="import-object-md-references.jsonl"):
        """Write PREMIS metadata."""
        super().write(
            mdtype=mdtype, mdtypeversion=mdtypeversion,
            file_metadata_dict=file_metadata_dict, ref_file=ref_file
        )


def create_streams(streams, premis_file):
    """Create PREMIS objects for streams.

    :streams: Stream dict
    :premis_file: Created PREMIS XML file for the digital object file
    :returns: List of PREMIS etree objects
    """
    if len(streams) < 2:
        return None

    premis_list = {}
    for index, stream in streams.items():
        if stream['stream_type'] not in ['video', 'audio']:
            continue

        id_value = str(uuid4())
        identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=id_value)
        version = "" if stream['version'] == NO_VERSION else stream['version']
        premis_format_des = premis.format_designation(
            stream['mimetype'], version)
        premis_format = premis.format(child_elements=[premis_format_des])
        premis_objchar = premis.object_characteristics(
            child_elements=[premis_format])
        el_premis_object = premis.object(
            identifier, child_elements=[premis_objchar], bitstream=True)

        premis_list[index] = el_premis_object

        premis_file.append(
            premis.relationship('structural', 'includes', [el_premis_object]))

    return premis_list


def check_metadata(mimetype, version, streams, fname):
    """Validate metadata.

    Check that we will not get None nor (:unav) values to mimetype and
    version. Check that multiple streams are found in
    video containers, and exist only for images or video containers.

    :mimetype: MIME type
    :version: File format version
    :streams: Streams returned from Scraper
    :fname: File name of the digital object
    :raises: ValueError if metadata checking results errors
    """
    if mimetype in [None, "(:unav)"]:
        raise ValueError('MIME type could not be identified for '
                         'file %s' % fname)
    if version in [None, "(:unav)"]:
        raise ValueError('File format version could not be identified for '
                         'file %s' % fname)
    if streams[0]['stream_type'] not in ['videocontainer', 'image'] and \
            len(streams) > 1:
        raise ValueError('The file contains multiple streams which '
                         'is supported only for images and video containers.')
    if streams[0]['stream_type'] in ['videocontainer'] and len(streams) < 2:
        raise ValueError('Video container format without contained streams '
                         'found.')


# pylint: disable=too-many-locals
def create_premis_object(fname, streams, **attributes):
    """
    Create Premis object for given file.

    :fname: File name of the digital object
    :streams: Streams from the Scraper
    :attributes: The following keys:
                 charset: Character encoding of a file
                 original_name: Original filename
                 file_format: File format and version (tuple) of a file
                 format_registry: Format registry name and value (tuple)
                 identifier: File identifier type and value (tuple)
                 checksum: Checksum algorithm and value (tuple)
                 date_created: Creation date of a file
                 creating_application: Software and its version that created
                                       the file
    :returns: PREMIS object as etree
    :raises: ValueError if character set is invalid for text files.
    """
    attributes = _attribute_values(attributes)
    date_created = attributes["date_created"] or creation_date(fname)
    if not attributes["checksum"]:
        attributes["checksum"] = ("MD5", calc_checksum(fname))

    application = None
    application_version = None
    if attributes["creating_application"]:
        (application, application_version) = attributes["creating_application"]

    if streams[0]['stream_type'] == 'text':
        charset = attributes["charset"] or streams[0]['charset']
    else:
        charset = None

    if not attributes["file_format"]:
        if streams[0]["version"] == UNKNOWN_VERSION:
            # Unknown version should cause exception already in
            # scrape_file function, where the file is also graded. So
            # this part is probably unnecessary.
            raise ValueError('Unknown file format version')
        if streams[0]["version"] == NO_VERSION:
            format_version = ''
        else:
            format_version = streams[0]["version"]

        file_format = (streams[0]["mimetype"], format_version)
    else:
        version = "" if attributes["file_format"][1] == NO_VERSION else \
            attributes["file_format"][1]
        file_format = (attributes["file_format"][0], version)

    check_metadata(file_format[0], file_format[1], streams, fname)

    charset_mime = ""
    if charset:
        if charset not in ALLOWED_CHARSETS:
            raise ValueError('Invalid charset.')
        charset_mime = f'; charset={charset}'

    if attributes["identifier"]:
        identifier_type = attributes["identifier"][0]
        identifier_value = attributes["identifier"][1]
    else:
        identifier_type = 'UUID'
        identifier_value = str(uuid4())

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
    application_elements = []
    if application:
        application_elements.append(
            premis.creating_application_name(application)
        )
    if application_version:
        application_elements.append(
            premis.creating_application_version(application_version)
        )
    application_elements.append(premis.date_created(date_created))

    premis_create = premis.creating_application(
        child_elements=application_elements
    )
    premis_objchar = premis.object_characteristics(
        child_elements=[premis_fixity, premis_format, premis_create])

    # Create object element
    el_premis_object = premis.object(
        object_identifier,
        original_name=attributes["original_name"],
        child_elements=[premis_objchar])

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
            raise OSError

    return files


def creation_date(path_to_file):
    """Return creation date for file.

    Try to get the date that a file was created, falling back to when it
    was last modified if that isn't possible.  See
    http://stackoverflow.com/a/39501288/1709587 for explanation.

    :path_to_file: File path
    :returns: Timestamp for a file
    """
    if platform.system() == 'Windows':
        return datetime.datetime.fromtimestamp(
            os.path.getctime(path_to_file)).isoformat()

    stat = os.stat(path_to_file)
    try:
        return datetime.datetime.fromtimestamp(
            stat.st_birthtime).isoformat()
    except AttributeError:
        # We're probably on Linux. No easy way to get creation dates
        # here, so we'll settle for when its content was last modified.
        return datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()


def _parse_scraper_tools(scraper_info):
    """Helper function to parse the used third party components used
    when identifying files and extracting technical metadata to be used
    as agents when creating events documenting the packaging process.

    :returns: a dict of agent metadata
    """
    agent = {'agent_name': None,
             'detector': False,
             'agent_version': None,
             'tools': None,
             'detail_note': None}

    agent['agent_name'] = scraper_info['class']
    if 'Detector' in scraper_info['class']:
        agent['detector'] = True
    agent['agent_version'] = file_scraper.__version__
    tools = ''
    tools_list = []
    if 'tools' in scraper_info:
        for tool in scraper_info['tools']:
            tools_list.append(tool)
    if tools_list:
        tools = 'Used tools (name-version): ' + ', '.join(tools_list)
        agent['tools'] = tools
    detail_notes = scraper_info['messages'] + scraper_info['errors']
    agent['detail_note'] = ', '.join(detail_notes)

    return agent


def _create_events(
        workspace,
        base_path,
        event_datetime,
        event_target,
        identification_event=False,
        validation_event=False,
        checksum_event=False,
        agents=None):
    """Function to create events documenting the extraction of technical
    metadata as well as the potential message digest calculation and
    the identification and validation of digital objects.

    :workspace: The path to the workspace
    :base_path: Base path (see --base_path)
    :event_datetime: The timestamp for the event
    :event_target: The target of the metadata creation
    :identification_event: Boolean to indicate whether the file formats
                           were identified during the extraction
                           of technical metadata. If True, creates an
                           file format identifiaction event.
    :validation_event: Boolean to indicate whether the digital
                       objects were validated during the extraction
                       of technical metadata. If True, creates a digital
                       object validation event.
    :checksum_event: Boolean to indicate whether the message digest for
                     digital objects were calculated during the
                     extraction of technical metadata. If True, creates
                     a message digest calculation event.
    :agents: A list of the software, as dicts, used to extract the
             metadata
    """
    events = {
        'extraction': {
            'event_type': 'metadata extraction',
            'event_datetime': event_datetime,
            'event_detail': ('Technical metadata extraction as premis '
                             'metadata from digital objects'),
            'event_outcome': 'success',
            'event_outcome_detail': ('Premis metadata successfully created '
                                     'from extracted technical metadata.')},
        'identification': {
            'event_type': 'format identification',
            'event_datetime': event_datetime,
            'event_detail': 'MIME type and version identification',
            'event_outcome': 'success',
            'event_outcome_detail': ('File MIME type and format version '
                                     'successfully identified.')},
        'validation': {
            'event_type': 'validation',
            'event_datetime': event_datetime,
            'event_detail': 'Digital object validation',
            'event_outcome': 'success',
            'event_outcome_detail': ('Digital object(s) evaluated as '
                                     'well-formed and valid.')},
        'checksum': {
            'event_type': 'message digest calculation',
            'event_datetime': event_datetime,
            'event_detail': 'Checksum calculation for digital objects',
            'event_outcome': 'success',
            'event_outcome_detail': ('Checksum(s) successfully calculated '
                                     'for digital object(s).')},
    }

    # Do not create events for steps that haven't been performed by the
    # script
    if not identification_event:
        del events['identification']
    if not validation_event:
        del events['validation']
    if not checksum_event:
        del events['checksum']

    for event_name, event in events.items():
        found_event = _find_event(workspace,
                                  event['event_type'],
                                  event['event_datetime'],
                                  event['event_detail'],
                                  event['event_outcome'],
                                  event['event_outcome_detail'])

        if not found_event:

            if event_name == 'checksum':
                create_agent(
                    workspace=workspace,
                    agent_name='file-scraper',
                    agent_version=file_scraper.__version__,
                    agent_type='software',
                    agent_role='executing program',
                    create_agent_file='import-object-%s' % event_name)

            for agent in agents:
                if event_name == 'identification' and not agent['detector']:
                    continue
                if event_name == 'checksum':
                    break
                create_agent(
                    workspace=workspace,
                    agent_name=agent['agent_name'],
                    agent_version=agent['agent_version'],
                    agent_note=agent['tools'],
                    agent_type='software',
                    agent_role='executing program',
                    create_agent_file='import-object-%s' % event_name)

            premis_event(event_type=event['event_type'],
                         event_datetime=event['event_datetime'],
                         event_detail=event['event_detail'],
                         event_outcome=event['event_outcome'],
                         event_outcome_detail=event[
                             'event_outcome_detail'],
                         workspace=workspace,
                         base_path=base_path,
                         event_target=(event_target, ),
                         create_agent_file='import-object-%s' % event_name)

            agent_file = os.path.join(
                workspace, "import-object-%s-AGENTS-amd.json" % event_name)
            try:
                os.remove(agent_file)
            except OSError as exc:  # FileNotFoundError on Python 3
                if exc.errno != errno.ENOENT:
                    raise


def _find_event(workspace,
                event_type,
                event_datetime,
                event_detail,
                event_outcome,
                event_outcome_detail):
    """Helper function to find if a similar event already is created
    by using the digest of the metadata to see if a file already
    exist.
    """

    event = create_premis_event(
        event_type=event_type,
        event_datetime=event_datetime,
        event_detail=event_detail,
        event_outcome=event_outcome,
        event_outcome_detail=event_outcome_detail)

    digest = generate_digest(event)
    expected_filename = encode_path("%s-PREMIS:EVENT-amd.xml" % digest)

    return os.path.exists(os.path.join(workspace, expected_filename))


if __name__ == "__main__":
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
