"""Command line tool for importing digital objects"""

import os
import sys
import hashlib
import fnmatch
from uuid import uuid4
import datetime
import platform
import argparse
import magic
import subprocess

from ipt.validator.validators import iter_validators
from siptools.utils import encode_path, encode_id
import premis
import mets
import xml_helpers.utils as h


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
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    # Loop files and create premis objects
    files = collect_filepaths(dirs=args.files, base=args.base_path)
    for filename in files:
        if args.base_path != '':
            filerel = os.path.relpath(filename, args.base_path)
        else:
            filerel = filename

        xmldata = mets.xmldata()
        create_premis_object(xmldata, filename, args.skip_inspection,
                             args.format_name, args.format_version,
                             args.digest_algorithm, args.message_digest,
                             args.date_created, args.charset)

        mdwrap = mets.mdwrap('PREMIS:OBJECT', '2.3', child_elements=[xmldata])
        techmd = mets.techmd(
            encode_id(encode_path(filerel.decode(sys.getfilesystemencoding()),
                                  suffix="-premis-techmd.xml")),
            child_elements=[mdwrap])
        amdsec = mets.amdsec(child_elements=[techmd])
        _mets = mets.mets(child_elements=[amdsec])

        if args.stdout:
            print h.serialize(_mets)

        if not os.path.exists(args.workspace):
            os.makedirs(args.workspace)

        filename = encode_path(filerel.decode(sys.getfilesystemencoding()),
                               suffix="-premis-techmd.xml")


        with open(os.path.join(args.workspace, filename), 'w+') as outfile:
            outfile.write(h.serialize(_mets))
            print "Wrote METS technical metadata to file %s" % outfile.name

    return 0


def create_premis_object(tree, fname, skip_inspection=None,
                         format_name=None, format_version=None,
                         digest_algorithm='MD5', message_digest=None,
                         date_created=None, charset=None):
    """Create Premis object for given file."""

    validator_info = {}
    if not skip_inspection:
        for validator in iter_validators(metadata_info(fname)):
            validation_result = validator.result()
            if not validation_result['is_valid']:
                raise Exception('File %s is not valid: %s', fname,
                                validation_result['errors'])
        validator_info = validation_result['result']

    if message_digest is None:
        message_digest = md5(fname)
    if digest_algorithm is None:
        digest_algorithm = 'MD5'
    if format_name is None:
        format_name = metadata_info(fname)['format']['mimetype']
    if format_version is None and \
            (metadata_info(fname) and 'version' in metadata_info(fname)['format']):
        format_version = metadata_info(fname)['format']['version']
    if charset or (metadata_info(fname) and 'charset' in metadata_info(fname)['format']):
        format_name += '; charset=' + charset \
            if charset else '; charset=' + metadata_info(fname)['format']['charset']

    if date_created is None:
        date_created = creation_date(fname)

    premis_fixity = premis.fixity(message_digest, digest_algorithm)
    premis_format_des = premis.format_designation(format_name, format_version)
    premis_format = premis.format(child_elements=[premis_format_des])
    premis_date_created = premis.date_created(date_created)
    premis_create = \
        premis.creating_application(child_elements=[premis_date_created])
    premis_objchar = premis.object_characteristics(
        child_elements=[premis_fixity, premis_format, premis_create])

    # Create object element
    object_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=str(uuid4()))

    el_premis_object = premis.object(
        object_identifier, child_elements=[premis_objchar])
    tree.append(el_premis_object)

    return tree


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
    raises a CharsetError if the charset is unsupported.

    :filepath: path to file

    :returns: the charset as a string
    """
    allowed_charsets = ['ISO-8859-15', 'UTF-8',
                        'UTF-16', 'UTF-32']

    #command = ['file', '-bi', filepath]
    #charset_raw = str(subprocess.Popen(
    #    command,
    #    stdout=subprocess.PIPE).stdout.read()).rsplit(
    #        '=', 1)[-1].upper()[:-1]
    if charset_raw == 'US-ASCII':
        charset = 'ISO-8859-15'
    elif charset_raw == 'ISO-8859-1':
        charset = 'ISO-8859-15'
    elif charset_raw == 'UTF-16LE' or charset_raw == 'UTF-16BE':
        charset = 'UTF-16'
    else:
        charset = charset_raw

    if charset not in allowed_charsets:
        raise CharsetError('Invalid charset.')

    return charset


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)

