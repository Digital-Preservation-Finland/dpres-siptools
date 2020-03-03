"""Command line tool for importing digital objects"""
from __future__ import unicode_literals

import datetime
import fnmatch
import os
import platform
import sys
from uuid import uuid4

import click
import six

import premis
from file_scraper.scraper import Scraper
from siptools.utils import MdCreator

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
         "Defaults to ./workspace/")
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
def main(workspace, base_path, skip_wellformed_check, charset, file_format,
         checksum, date_created, identifier, format_registry, order, stdout,
         filepaths):
    """Import files to generate digital objects. If parameters --charset,
    --file_format, --identifier, --checksum or --date_created are not given,
    then these are created automatically.

    FILEPATHS: Files or a directory to import, relative path in relation to
    current directory or to --base_path. It depends on your parameters whether
    you may give several files or a single file. For example --checksum and
    --identifier are file dependent metadata, and if these are used, then use
    the script only for one file.
    """
    import_object(workspace, base_path, skip_wellformed_check, charset,
                  file_format, checksum, date_created, identifier,
                  format_registry, order, stdout, filepaths)
    return 0


def import_object(**kwargs):
    """Import files to generate digital objects. If parameters charset,
    file_format, identifier, checksum or date_created are not given,
    then these are created automatically.

    :returns: Dictionary of the scraped file metadata
    """
    params = _normalize_args(kwargs)
    # Loop files and create premis objects
    files = collect_filepaths(dirs=params["filepaths"],
                              base=params["base_path"])
    for filepath in files:

        # If the given path is an absolute path and base_path is current
        # path (i.e. not given), relpath will return ../../.. sequences, if
        # current path is not part of the absolute path. In such case we will
        # use the absolute path for filerel and omit base_path relation.
        if params["base_path"] not in ['.']:
            filerel = os.path.relpath(filepath, params["base_path"])
        else:
            filerel = filepath

        properties = {}
        if params["order"] is not None:
            properties['order'] = six.text_type(params["order"])
        # Add new properties of a file for other script files, e.g. structMap

        creator = PremisCreator(params["workspace"])
        file_metadata_dict = creator.add_premis_md(filepath, filerel, **params)
        if properties:
            file_metadata_dict[0]['properties'] = properties
        creator.write(stdout=params["stdout"],
                      file_metadata_dict=file_metadata_dict)

    return file_metadata_dict


def _normalize_args(params):
    """
    Normalize values of argument dict to default values if missing.
    :params: Arguments as dict.
    :returns: Normalized dict.
    """
    parameters = {}
    parameters["workspace"] = "./workspace" if not "workspace" in params else \
        params["workspace"],
    parameters["base_path"] = "." if not "base_path" in params else \
        params["base_path"],
    parameters["skip_wellformed_check"] = False if not \
        "skip_wellformed_check" in params else \
        params["skip_wellformed_check"],
    parameters["charset"] = None if not "charset" in params else \
        params["charset"],
    parameters["file_format"] = None if not "file_format" in params else \
        params["file_format"],
    parameters["checksum"] = None if not "checksum" in params else \
        params["checksum"],
    parameters["date_created"] = None if not "date_created" in params else \
        params["date_created"],
    parameters["identifier"] = None if not "identifier" in params else \
        params["identifier"],
    parameters["format_registry"] = None if not "format_registry" in params \
        else params["format_registry"],
    parameters["order"] = None if not "order" in params else params["order"],
    parameters["stdout"] = False if not "stdout" in params else \
        params["stdout"],
    parameters["filepaths"] = None if not "filepaths" in params else \
        params["filepaths"]

    return parameters


class PremisCreator(MdCreator):
    """Subclass of MdCreator, which generates PREMIS metadata
    for files and streams.
    """

    def _scrape_file(self, filepath, skip_well_check, file_format=None,
                     charset=None):
        """Scrape file
        :filepath: Path to file to be scraped
        :skip_well_check: True, if well-formed check is skipped
        :file_format: File format and version from the command line argument
                      parser, originally given as a value pair by the user.
                      The mimetype is in index 0 and version in index 1.
        :charset: Character encoding from arguments
        :returns: scraper with result attributes
        """
        if not file_format:
            file_format = (None, None)
        scraper = Scraper(filepath, mimetype=file_format[0],
                          version=file_format[1], charset=charset)
        if not skip_well_check:
            scraper.scrape(True)
            if not scraper.well_formed:
                errors = []
                for _, info in six.iteritems(scraper.info):
                    if len(info['errors']) > 0:
                        for error in info['errors']:
                            errors.append(error)
                error_str = "\n".join(errors)
                # Ensure the error string is binary on Py2, Unicode on Py3.
                # This ensures the message is not truncated on Py2 if it
                # contains Unicode.
                raise ValueError(six.ensure_str(error_str))
        else:
            scraper.scrape(False)

        return scraper

    def add_premis_md(self, filepath, filerel=None, **params):
        """
        Metadata creator for PREMIS metadata. This method:
        - Scrapes a file
        - Creates PREMIS metadata with amd references for a file
        - Creates PREMIS metadata with amd references for streams in a file
        - Returns stream dict from scraper
        """
        params = _normalize_args(params)
        scraper = self._scrape_file(
            filepath=filepath, skip_well_check=params["skip_wellformed_check"],
            file_format=params["file_format"], charset=params["charset"]
        )

        premis_elem = create_premis_object(filepath, scraper, **params)
        self.add_md(premis_elem, filerel)
        premis_list = create_streams(scraper.streams, premis_elem)

        if premis_list is not None:
            for index, premis_stream in six.iteritems(premis_list):
                self.add_md(premis_stream, filerel, index)

        return scraper.streams

    def write(self, mdtype="PREMIS:OBJECT", mdtypeversion="2.3",
              othermdtype=None, section=None, stdout=False,
              file_metadata_dict=None):
        super(PremisCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion,
            file_metadata_dict=file_metadata_dict)


def create_streams(streams, premis_file):
    """Create PREMIS objects for streams

    :streams: Stream dict
    :premis_file: Created PREMIS XML file for the digital object file
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


def check_metadata(format_name, format_version, streams, fname):
    """Check that we will not get None values"""
    if format_name is None:
        raise ValueError('Mimetype could not be identified for '
                         'file %s' % fname)
    if format_version is None:
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


def create_premis_object(fname, scraper, **kwargs):
    """Create Premis object for given file."""
    if scraper.info[0]['class'] == 'FileExists' and \
            len(scraper.info[0]['errors']) > 0:
        raise IOError(scraper.info[0]['errors'])
    for _, info in six.iteritems(scraper.info):
        if info['class'] == 'ScraperNotFound':
            raise ValueError('File format is not supported.')

    params = _normalize_args(kwargs)
    checksum = params["checksum"] or ("MD5", scraper.checksum(algorithm='md5'))
    date_created = params["date_created"] or creation_date(fname)
    identifier = params["identifier"] or ("UUID", six.text_type(uuid4()))
    format_registry = params["format_registry"]
    if scraper.streams[0]['stream_type'] == 'text':
        charset = params["charset"] or scraper.streams[0]['charset']
    else:
        charset = None

    # Scraper's version information will override the version
    # information if any is found.
    if scraper.version and scraper.version != UNKNOWN_VERSION:
        format_version = '' if scraper.version == NO_VERSION else \
            scraper.version
    else:
        format_version = DEFAULT_VERSIONS.get(scraper.mimetype, None)

    file_format = params["file_format"] or (scraper.mimetype, format_version)
    check_metadata(file_format[0], file_format[1], scraper.streams, fname)

    charset_mime = ""
    if charset:
        if charset not in ALLOWED_CHARSETS:
            raise ValueError('Invalid charset.')
        charset_mime = '; charset={}'.format(charset)

    object_identifier = premis.identifier(identifier_type=identifier[0],
                                          identifier_value=identifier[1])

    premis_fixity = premis.fixity(checksum[1], checksum[0])
    premis_format_des = premis.format_designation(
        file_format[0] + charset_mime, file_format[1])
    if not format_registry:
        premis_format = premis.format(child_elements=[premis_format_des])
    else:
        premis_registry = premis.format_registry(format_registry[0],
                                                 format_registry[1])
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
    """Collect file paths recursively from given directory. Raises IOError
    if given path does not exist."""

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
    """Try to get the date that a file was created, falling back to when it
    was last modified if that isn't possible.  See
    http://stackoverflow.com/a/39501288/1709587 for explanation.
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


if __name__ == "__main__":
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
