"""Command line tool for importing digital objects"""

import os
import sys
import fnmatch
from uuid import uuid4
import datetime
import platform
import click
import magic
from file_scraper.scraper import Scraper
import premis
from siptools.utils import AmdCreator


ALLOWED_CHARSETS = ['ISO-8859-15', 'UTF-8', 'UTF-16', 'UTF-32']

DEFAULT_VERSIONS = {
    'application/msword': '11.0',
    'application/vnd.ms-excel': '11.0',
    'application/vnd.ms-powerpoint': '11.0',
    'application/vnd.openxmlformats-'
    'officedocument.presentationml.presentation': '15.0',
    'application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.sheet': '15.0',
    'application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document': '15.0'
}

FILE_VERSION = {
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
    'video/mp4': ''
}


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
    import_object(
        workspace, base_path, skip_wellformed_check, charset, file_format,
        checksum, date_created, identifier, format_registry, order, stdout,
        filepaths
    )
    return 0


def import_object(workspace="./workspace/", base_path=".",
                  skip_wellformed_check=False, charset=None, file_format=None,
                  checksum=None, date_created=None, identifier=None,
                  format_registry=None, order=None, stdout=False,
                  filepaths=None):
    """Import files to generate digital objects. If parameters charset,
    file_format, identifier, checksum or date_created are not given,
    then these are created automatically.

    :returns: Dictionary of the scraped file metadata
    """
    # Loop files and create premis objects
    files = collect_filepaths(dirs=filepaths, base=base_path)
    for filepath in files:

        # If the given path is an absolute path and base_path is current
        # path (i.e. not given), relpath will return ../../.. sequences, if
        # current path is not part of the absolute path. In such case we will
        # use the absolute path for filerel and omit base_path relation.
        if base_path not in ['.']:
            filerel = os.path.relpath(filepath, base_path)
        else:
            filerel = filepath

        properties = {}
        if order:
            properties['order'] = str(order)
        # Add new properties of a file for other script files, e.g. structMap

        creator = PremisCreator(workspace)
        file_metadata_dict = creator.add_premis_md(
            filepath, filerel, skip_wellformed_check, charset, file_format,
            checksum, date_created, identifier, format_registry)
        if properties:
            file_metadata_dict[0]['properties'] = properties
        creator.write(stdout=stdout, file_metadata_dict=file_metadata_dict)

    return file_metadata_dict


class PremisCreator(AmdCreator):
    """Subclass of AmdCreator, which generates PREMIS metadata
    for files and streams.
    """

    def _scrape_file(self, filepath, skip_well_check):
        """Scrape file
        :filepath: Path to file to be scraped
        :skip_well_check: True, if well-formed check is skipped
        :returns: scraper with result attributes
        """
        scraper = Scraper(filepath)
        if not skip_well_check:
            scraper.scrape(True)
            if not scraper.well_formed:
                errors = []
                for _, info in scraper.info.iteritems():
                    if len(info['errors']) > 0:
                        errors.append(info['errors'])
                error_str = "\n".join(errors)
                raise ValueError(error_str)
        else:
            scraper.scrape(False)

        return scraper

    def _premis_for_file(self, filepath, filerel, scraper, charset,
                         file_format, checksum, date_created,
                         identifier, format_registry):
        """Create PREMIS metadata for a file and add it to amd references"""
        premis_elem = create_premis_object(
            filepath, scraper, file_format, checksum,
            date_created, charset, identifier, format_registry
        )
        self.add_md(premis_elem, filerel)
        return premis_elem

    def _premis_for_streams(self, filerel, file_metadata_dict, premis_elem):
        """Create PREMIS metadata for a stream and add it to amd references"""
        premis_list = create_streams(file_metadata_dict, premis_elem)

        if premis_list is not None:
            for index, premis_stream in premis_list.iteritems():
                self.add_md(premis_stream, filerel, index)

    def add_premis_md(self, filepath, filerel=None, skip_well_check=False,
                      charset=None, file_format=None, checksum=None,
                      date_created=None, identifier=None,
                      format_registry=None):
        """
        Metadata creator for PREMIS metadata. This method:
        - Scrapes a file
        - Creates PREMIS metadata with amd references for a file
        - Creates PREMIS metadata with amd references for streams in a file
        - Returns stream dict from scraper
        """
        scraper = self._scrape_file(filepath, skip_well_check)
        premis_elem = self._premis_for_file(
            filepath, filerel, scraper, charset, file_format, checksum,
            date_created, identifier, format_registry
        )
        self._premis_for_streams(filerel, scraper.streams, premis_elem)
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
    for index, stream in streams.iteritems():
        if stream['stream_type'] not in ['video', 'audio']:
            continue

        id_value = str(uuid4())
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
                         'file ' % fname)
    if streams[0]['stream_type'] not in ['videocontainer'] and \
            len(streams) > 1:
        raise ValueError('The file contains multiple streams which '
                         'is supported only for video containers.')
    elif streams[0]['stream_type'] in ['videocontainer'] and \
            len(streams) < 2:
        raise ValueError('Video container format without contained streams '
                         'found.')


def create_premis_object(fname, scraper,
                         file_format=None, checksum=None,
                         date_created=None, charset=None,
                         identifier=None, format_registry=None):
    """Create Premis object for given file."""

    if scraper.info[0]['class'] == 'FileExists' and \
            len(scraper.info[0]['errors']) > 0:
        raise IOError(scraper.info[0]['errors'])
    for _, info in scraper.info.iteritems():
        if info['class'] == 'ScraperNotFound':
            raise ValueError('File format is not supported.')

    if checksum in [None, ()]:
        message_digest = scraper.checksum(algorithm='md5')
        digest_algorithm = 'MD5'
    else:
        message_digest = checksum[1]
        digest_algorithm = checksum[0]

    if file_format in [None, ()]:
        format_name = scraper.mimetype
        format_version = scraper.version
        if format_name in DEFAULT_VERSIONS:
            format_version = DEFAULT_VERSIONS[format_name]
    else:
        format_name = file_format[0]
        format_version = file_format[1]

    if not charset and scraper.streams[0]['stream_type'] == 'text':
        charset = scraper.streams[0]['charset']

    check_metadata(format_name, format_version, scraper.streams, fname)

    if charset:
        if charset not in ALLOWED_CHARSETS:
            raise ValueError('Invalid charset.')
        format_name += '; charset=' + charset

    if date_created is None:
        date_created = creation_date(fname)

    if identifier in [None, ()]:
        object_identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=str(uuid4()))
    else:
        object_identifier = premis.identifier(
            identifier_type=identifier[0],
            identifier_value=identifier[1])

    premis_fixity = premis.fixity(message_digest, digest_algorithm)
    premis_format_des = premis.format_designation(format_name, format_version)
    if format_registry in [None, ()]:
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


def metadata_info(fname):
    """Return metadata_info dict for given file."""
    magic_ = magic.open(magic.MAGIC_MIME_TYPE)
    magic_.load()
    mimetype = magic_.file(fname)
    magic_.close()

    magic_ = magic.open(magic.MAGIC_MIME_ENCODING)
    magic_.load()
    charset = magic_.file(fname)
    magic_.close()

    magic_ = magic.open(magic.MAGIC_NONE)
    magic_.load()
    version = magic_.file(fname).split("version ")[-1]
    magic_.close()

    metadata_info_ = {
        'filename': fname,
        'type': 'file',
        'format': {
            'mimetype': mimetype,
            'version': version,
            'charset': charset
        }
    }

    # Return version info from dictionary
    if mimetype in FILE_VERSION:
        metadata_info_['format']['version'] = FILE_VERSION[mimetype]

    # If it's an XML-file, return fixed mimetype and version
    if mimetype == 'application/xml':
        metadata_info_['format']['mimetype'] = 'text/xml'
        metadata_info_['format']['version'] = '1.0'
        mimetype = 'text/xml'

    # Find correct charset
    if mimetype in ['text/plain', 'text/csv', 'application/xhtml+xml',
                    'text/xml', 'text/html', 'application/gml+xml',
                    'application/vnd.google-earth.kml+xml']:
        metadata_info_['format']['charset'] = return_charset(charset.upper())
    else:
        del metadata_info_['format']['charset']

    # If it's a jpeg file, return version
    if mimetype == 'image/jpeg':
        versions = ['1.10', '1.01', '1.02']
        for ver in versions:
            if ver in version:
                metadata_info_['format']['version'] = ver

    # If Broadcast WAVE file return version
    if mimetype == 'audio/x-wav':
        if is_broadcast_wav(fname):
            metadata_info_['format']['version'] = '2'

    return metadata_info_


def return_charset(charset_raw):
    """Returns the charset for text files in a correct format. Charset
    is read from the file using the file command. The function
    raises a ValueError if the charset is unsupported.

    :charset_raw: Original charset name
    :returns: the charset in correct format
    """
    allowed_charsets = ['ISO-8859-15', 'UTF-8',
                        'UTF-16', 'UTF-32']

    if charset_raw == 'US-ASCII':
        charset = 'ISO-8859-15'
    elif charset_raw == 'ISO-8859-1':
        charset = 'ISO-8859-15'
    elif charset_raw == 'UTF-16LE' or charset_raw == 'UTF-16BE':
        charset = 'UTF-16'
    else:
        charset = charset_raw

    if charset not in allowed_charsets:
        raise ValueError('Invalid charset.')

    return charset


def _read_uint(f_in):
    """Read 4 bytes from f_in and return the corresponding
    unsigned integer.
    """
    uint = 0
    binary_num = f_in.read(4)

    for i in range(4):
        uint += ord(binary_num[i]) << (8*i)  # Left shift of 8*i

    return uint


def is_broadcast_wav(fname):
    """Check if file fname is WAV or broadcast WAV file.
    The function reads all the RIFF chunk IDs and returns
    True if "bext" chunk is found.
    """
    with open(fname) as f_in:
        f_in.read(4)  # Skip RIFF ID
        size = _read_uint(f_in) - 4
        f_in.read(4)  # Skip WAVE ID

        # Iterate all WAVE chunks
        while size > 0:
            chunk_id = f_in.read(4)
            chunk_size = _read_uint(f_in)

            if chunk_id == "bext":
                return True
            else:
                size -= (chunk_size + 8)
                f_in.seek(chunk_size, 1)

    return False


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
