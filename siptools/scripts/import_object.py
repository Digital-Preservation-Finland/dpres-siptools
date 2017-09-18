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

from ipt.validator.validators import iter_validators
from siptools.utils import encode_path, encode_id
import premis.premis as p
import premis.object
import mets


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
        premis_object = create_premis_object(
            xmldata, filename, args.skip_inspection,
            args.format_name, args.format_version, args.digest_algorithm,
            args.message_digest, args.date_created, args.charset)

        xmldata = mets.mdwrap.xmldata(child_elements=[premis_object])
        mdwrap = mets.mdwrap.mdwrap(child_elements=[xmldata])
        techmd = mets.amdsec.techmd(
            encode_id(encode_path(filerel, suffix="-techmd.xml")),
            child_elements=[mdwrap])        
        amdsec = mets.amdsec.amdsec(child_elements=[techmd])
        mets = mets.mets.mets(child_elements=[amdsec])

        if args.stdout:
            print h.serialize(mets)

        if not os.path.exists(args.workspace):
            os.makedirs(args.workspace)

        filename = encode_path(filerel, suffix="-techmd.xml")

        with open(os.path.join(args.workspace, filename), 'w+') as outfile:
            outfile.write(h.serialize(mets))
            print "Wrote METS technical metadata to file %s" % outfile.name

    return 0


def create_premis_object(tree, fname, skip_inspection=None,
                         format_name=None, format_version=None,
                         digest_algorithm='MD5', message_digest=None,
                         date_created=None, charset=None):
    """Create Premis object for given file."""

    techmd = {}
    if not skip_inspection:
        for validator in iter_validators(fileinfo(fname)):
            validation_result = validator.result()
            if not validation_result['is_valid']:
                raise Exception('File %s is not valid: %s', fname,
                                validation_result['errors'])

        techmd = validation_result['result']

    
    if message_digest is None:
        message_digest = md5(fname)
    if format_name is None:
        format_name = techmd['format']['mimetype']
    if format_version is None or (techmd and 'version' in techmd['format']):
        format_version = techmd['format']['version']
    if charset or (techmd and 'charset' in techmd['format']):
        format_name += '; charset=' + charset \
            if charset else '; charset=' + techmd['format']['charset']
    if date_created is None:
        date_created = creation_date(fname)

    premis_fixity = premis.object.fixity(message_digest, digest_algorithm)
    premis_format_des = premis.object.format_designation(format_name, format_version)
    premis_format = premis.object.format(child_elements=[format_des])
    premis_date_created = premis.object.date_created(date_created)
    premis_create = premis.object.creating_application(child_elements=[premis_date_created])
    premis_objchar = premis.object.object_characteristics(
        child_elements=[premi_fixity, premis_format, premis_create])

    # Create object element
    object_identifier = p.premis_identifier(
        identifier_type='UUID',
        identifier_value=str(uuid4()))

    el_premis_object = premis.premis_object.premis_object(
        object_identifier, child_elements=[premis_objchar])
    tree.append(el_premis_object)

    return tree


def fileinfo(fname):
    """Return fileinfo dict for given file."""
    m = magic.open(magic.MAGIC_MIME_TYPE)
    m.load()
    mimetype = m.file(fname)
    m.close()

    m = magic.open(magic.MAGIC_MIME_ENCODING)
    m.load()
    charset = m.file(fname)
    m.close()

    m = magic.open(magic.MAGIC_NONE)
    m.load()
    version = m.file(fname).split("version ")[-1]
    m.close()

    fileinfo = {
        'filename': fname,
        'format': {
            'mimetype': mimetype,
            'version': version,
            'charset': charset
        }
    }

    if mimetype in ['text/plain', 'text/csv', 'application/xhtml+xml',
                    'text/xml', 'text/html', 'application/gml+xml',
                    'application/vnd.google-earth.kml+xml']:
        fileinfo['format']['charset'] = 'UTF-8' if 'UTF-8' in charset else 'ISO-8859-15'
    else:
        del fileinfo['format']['charset']

    if mimetype in ['text/plain', 'text/csv']:
        fileinfo['format']['version'] = ''

    if mimetype == 'image/tiff':
        fileinfo['format']['version'] = '6.0'

    return fileinfo

def md5(fname):
    """Calculate md5 checksum for given file."""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def collect_filepaths(dirs=['.'], pattern='*', base=''):
    """Collect file paths recursively from given directory. Raises IOError
    if given path does not exist."""
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
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
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

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
