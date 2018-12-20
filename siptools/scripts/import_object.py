"""Command line tool for importing digital objects"""

import os
import sys
import hashlib
import fnmatch
from uuid import uuid4
import datetime
import platform
import argparse
import json
import ctypes

try:
    import ffmpeg
except ImportError:
    FFMPEG_INSTALLED = False
else:
    FFMPEG_INSTALLED = True

try:
    from ipt.validator.validators import iter_validators
except ImportError:
    IPT_INSTALLED = False
else:
    IPT_INSTALLED = True

import premis
from siptools.utils import TechmdCreator, encode_path

try:
    ctypes.cdll.LoadLibrary('/opt/file-5.30/lib64/libmagic.so.1')
except OSError:
    print ('/opt/file-5.30/lib64/libmagic.so.1 not found, MS Office detection '
           'may not work properly if file command library is older than 5.30.')

import magic


STREAM_PREMIS = {'h264': ['video/mp4', ''],
                 'aac': ['audio/mp4', '']}


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Tool for importing files to generate digital objects")
    parser.add_argument('files', nargs='+',
                        help="Digital objects to be imported")
    parser.add_argument(
        '--base_path', type=str, default='',
        help="Source base path of digital objects. If used, give objects in"
        "relation to this base path.")
    parser.add_argument(
        '--workspace', type=str, default='./workspace/',
        help="Workspace directory for the metadata files.")
    parser.add_argument(
        '--skip_inspection', action='store_true',
        help='Skip file inspection and give technical metadata as parameters')
    parser.add_argument(
        '--format_name', dest='format_name', type=str,
        help='Mimetype of a file')
    parser.add_argument(
        '--charset', dest='charset', type=str, help='Charset of a file')
    parser.add_argument(
        '--format_version', dest='format_version', type=str,
        help='Version of fileformat')
    parser.add_argument(
        '--digest_algorithm', dest='digest_algorithm', type=str,
        help='Message digest algorithm')
    parser.add_argument(
        '--message_digest', dest='message_digest', type=str,
        help='Message digest of a file')
    parser.add_argument(
        '--date_created', dest='date_created', type=str,
        help='The actual or approximate date and time the object was created')
    parser.add_argument(
        '--identifier', dest='identifier', type=str, nargs=2,
        metavar=('IDENTIFIER_TYPE', 'IDENTIFIER_VALUE'),
        help='The identifier type and value of the digital object')
    parser.add_argument(
        '--format_registry', dest='format_registry', type=str, nargs=2,
        metavar=('REGISTRY_NAME', 'REGISTRY_KEY'),
        help='The format registry name and key of the digital object')
    parser.add_argument(
        '--order', dest='order', type=int,
        help='Order number of the digital object')
    parser.add_argument(
        '--streams', dest='streams', action='store_true',
        help='Given files include streams')
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    # Loop files and create premis objects
    files = collect_filepaths(dirs=args.files, base=args.base_path)
    for filename in files:

        premis_list = {}

        if args.base_path != '':
            filerel = os.path.relpath(filename, args.base_path)
        else:
            filerel = filename

        premis_elem = create_premis_object(
            filename, args.skip_inspection, args.format_name,
            args.format_version, args.digest_algorithm,
            args.message_digest, args.date_created, args.charset,
            args.identifier, args.format_registry)

        if args.streams:
            premis_list = create_streams(filename, premis_elem)
        else:
            premis_list['root'] = premis_elem

        creator = PremisCreator(args.workspace)

        for key in premis_list.keys():
            if key == 'root':
                creator.add_md(premis_list[key], filerel)
            else:
                creator.add_md(premis_list[key], filerel, key)
        creator.write(stdout=args.stdout)

        properties = {}
        if args.order:
            properties['order'] = str(args.order)
        # Add new properties of a file for other script files, e.g. structMap

        if properties != {}:
            append_properties(args.workspace, filerel, properties)

    return 0


class PremisCreator(TechmdCreator):
    """Subclass of TechmdCreator, which generates PREMIS metadata
    for files and streams.
    """

    def write(self, mdtype="PREMIS:OBJECT", mdtypeversion="2.3", stdout=False):
        super(PremisCreator, self).write(mdtype, mdtypeversion)


def append_properties(workspace, fkey, file_properties):
    """Append separate properties of a file for later use

    :workspace: Workspace to work with
    :fkey: File path to be used as a key in the properties dict
    :file_properties: Dict of properties of a file
    """
    file_path = os.path.join(workspace, 'siptools-file-properties.json')
    properties = {}
    if os.path.isfile(file_path):
        with open(file_path) as infile:
            properties = json.load(infile)

    fkey = encode_path(fkey.decode('utf-8'))
    properties[fkey] = file_properties
    with open(file_path, 'w+') as outfile:
        json.dump(properties, outfile)


def create_streams(fname, premis_file):
    """Create PREMIS objects for streams

    :fname: Digital object file path
    :premis_file: Created PREMIS XML file for the digital object file
    """
    if not FFMPEG_INSTALLED:
        raise Exception('ffmpeg module is required for streams. '
                        'Please install ffmpeg module or do not use'
                        '--streams parameter.')
    probe = ffmpeg.probe(fname)
    premis_list = {}
    premis_list['root'] = premis_file
    for stream in probe['streams']:
        id_value = str(uuid4())
        identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=id_value)
        format = STREAM_PREMIS[stream['codec_name']]
        index = str(stream['index'])
        premis_format_des = premis.format_designation(
            format[0], format[1])
        premis_format = premis.format(child_elements=[premis_format_des])
        premis_objchar = premis.object_characteristics(
            child_elements=[premis_format])
        el_premis_object = premis.object(
            identifier, child_elements=[premis_objchar], bitstream=True)

        premis_list[index] = el_premis_object

        premis_file.append(
            premis.relationship('structural', 'includes', el_premis_object))

    return premis_list


def create_premis_object(fname, skip_inspection=None,
                         format_name=None, format_version=None,
                         digest_algorithm='MD5', message_digest=None,
                         date_created=None, charset=None,
                         identifier=None, format_registry=None):
    """Create Premis object for given file."""

    metadata_info_ = metadata_info(fname)
    if not skip_inspection:
        if not IPT_INSTALLED:
            raise Exception('ipt module is required for file validation. '
                            'Please install dpres-ipt or skip file validation '
                            'with --skip_inspection parameter.')
        for validator in iter_validators(metadata_info_):
            validation_result = validator.result()
            if not validation_result['is_valid']:
                raise Exception(
                    'File %s is not valid: %s' % (fname,
                                                  validation_result['errors'])
                )

    if message_digest is None:
        message_digest = md5(fname)
    if digest_algorithm is None:
        digest_algorithm = 'MD5'
    if format_name is None:
        format_name = metadata_info_['format']['mimetype']
    if format_version is None and (metadata_info_ and 'version'
                                   in metadata_info_['format']):
        format_version = metadata_info_['format']['version']
    if charset or (metadata_info_ and 'charset'
                   in metadata_info_['format']):
        format_name += '; charset=' + charset if charset \
            else '; charset=' + metadata_info_['format']['charset']

    if date_created is None:
        date_created = creation_date(fname)

    if identifier is None:
        object_identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=str(uuid4()))
    else:
        object_identifier = premis.identifier(
            identifier_type=identifier[0],
            identifier_value=identifier[1])

    premis_fixity = premis.fixity(message_digest, digest_algorithm)
    premis_format_des = premis.format_designation(format_name, format_version)
    if format_registry is None:
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

    # If it's an XML-file, return fixed mimetype with charset and version
    if mimetype == 'text/xml' or mimetype == 'application/xml':
        metadata_info_['format']['mimetype'] = 'text/xml'
        metadata_info_['format']['version'] = '1.0'
        mimetype = 'text/xml'

    if mimetype in ['text/plain', 'text/csv', 'application/xhtml+xml',
                    'text/xml', 'text/html', 'application/gml+xml',
                    'application/vnd.google-earth.kml+xml']:
        metadata_info_['format']['charset'] = return_charset(charset.upper())
    else:
        del metadata_info_['format']['charset']

    if mimetype in ['text/plain', 'text/csv']:
        metadata_info_['format']['version'] = ''

    elif mimetype == 'image/tiff':
        metadata_info_['format']['version'] = '6.0'

    # If it's a PDF-file, return version
    #elif formatname == 'application/pdf':
    #    formatversion = version_command.rsplit(None, 1)[-1]

    # If it's an Open Office document return fixed version
    elif mimetype.startswith('application/vnd.oasis.opendocument'):
        metadata_info_['format']['version'] = '1.0'

    # I it's a jpeg file, return version
    elif mimetype == 'image/jpeg':
        versions = ['1.10', '1.01', '1.02']
        for ver in versions:
            if ver in version:
                metadata_info_['format']['version'] = ver

    # If it is an openxml MS Office file return version
    elif mimetype in ['application/vnd.openxmlformats-officedocument.'
                      'wordprocessingml.document',
                      'application/vnd.openxmlformats-officedocument.'
                      'spreadsheetml.sheet',
                      'application/vnd.openxmlformats-officedocument.'
                      'presentationml.presentation']:
        metadata_info_['format']['version'] = '15.0'

    # If it is an binary MS Office file return version
    elif mimetype in ['application/msword', 'application/vnd.ms-excel',
                      'application/vnd.ms-powerpoint']:
        metadata_info_['format']['version'] = '11.0'

    # If WAVE-file return version
    elif mimetype == 'audio/x-wav':
        if is_broadcast_wav(fname):
            metadata_info_['format']['version'] = '2'
        else:
            metadata_info_['format']['version'] = ''

    return metadata_info_


def md5(fname):
    """Calculate md5 checksum for given file."""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as file_:
        for chunk in iter(lambda: file_.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def collect_filepaths(dirs=None, pattern='*', base=''):
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


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
