"""Command line tool for importing digital objects"""

import os
import sys
import hashlib
import fnmatch
from uuid import uuid4
from urllib import quote_plus
import magic
import argparse

from ipt.validator import validate
from siptools.utils import encode_path, encode_id
import siptools.xml.premis as p
import siptools.xml.mets as m

import xml.etree.ElementTree as ET
import datetime
import platform


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="Tool for importing files "
                                     "which generates digital objects")
    parser.add_argument('files', nargs='+', help="Files to be imported")
    parser.add_argument('--output', type=str, default='./workspace/',
                        help="Destination file")
    parser.add_argument('--skip_inspection', action='store_true',
                        help='Skip file inspection and give technical metadata as parameters')
    parser.add_argument('--format_name', dest='format_name', type=str,
                        help='Mimetype of a file')
    parser.add_argument('--format_version', dest='format_version', type=str,
                        help='Version of fileformat')
    parser.add_argument('--digest_algorithm', dest='digest_algorithm', type=str,
                        help='Message digest algorithm')
    parser.add_argument('--message_digest', dest='message_digest', type=str,
                        help='Message digest of a file')
    parser.add_argument('--date_created', dest='date_created', type=str,
                        help='The actual or approximate date and time the object was created')
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    # Loop files and create premis objects
    files = collect_filepaths(args.files)
    for filename in files:
        mets = m.mets_mets()
        amdsec = m.amdsec()
        techmd = m.techmd(encode_id(encode_path(filename, suffix="-techmd.xml")))
        mdwrap = m.mdwrap()
        xmldata = m.xmldata()
        create_premis_object(xmldata, filename, args.skip_inspection, args.format_name, args.format_version,
                args.digest_algorithm, args.message_digest, args.date_created)

        mdwrap.append(xmldata)
        techmd.append(mdwrap)
        amdsec.append(techmd)
        mets.append(amdsec)

        if args.stdout:
            print m.serialize(mets)

        if not os.path.exists(args.output):
            os.makedirs(args.output)

        filename = encode_path(filename, suffix="-techmd.xml")

        with open(os.path.join(args.output, filename), 'w+') as outfile:
            outfile.write(m.serialize(mets))
            print "Wrote METS technical metadata to file %s" % outfile.name

    return 0


def create_premis_object(tree, fname, skip_inspection=None,
                         format_name=None, format_version=None, digest_algorithm=None,
                         message_digest=None, date_created=None):
    """Create Premis object for given file."""

    techmd = {}
    if not skip_inspection:
        validation_result = validate(fileinfo(fname))

        if not validation_result['is_valid']:
            raise Exception('File %s is not valid: %s', fname,
                            validation_result['errors'])

        techmd = validation_result['result']

    # Create objectCharacteristics element
    el_objectCharacteristics = p._element('objectCharacteristics')

    el_composition_level = p._subelement(el_objectCharacteristics, 'compositionLevel')
    el_composition_level.text = '0'

    # Create fixity element
    el_fixity = p._subelement(el_objectCharacteristics, 'fixity')
    el_fixity_algorithm = p._subelement(
        el_fixity, 'digestAlgorithm', 'message')
    el_fixity_algorithm.text = digest_algorithm or 'MD5'
    el_fixity_checksum = p._subelement(el_fixity, 'digest', 'message')
    el_fixity_checksum.text = message_digest or md5(fname)

    # Create format element
    el_format = p._subelement(el_objectCharacteristics, 'format')
    el_formatDesignation = p._subelement(el_format, 'formatDesignation')
    el_format_name = p._subelement(el_formatDesignation, 'name', 'format')
    el_format_name.text = format_name or techmd['format']['mimetype']

    if format_version or (techmd and 'version' in techmd['format']):
        el_format_version = p._subelement(
            el_formatDesignation, 'version', 'format')
        el_format_version.text = format_version if format_version else techmd[
            'format']['version']

    if techmd['format']['charset']:
        el_format_name.text += '; charset=' + techmd['format']['charset']

    # Create creatingApplication element
    el_creatingApplication = p._subelement(el_objectCharacteristics,
                                           'creatingApplication')
    el_dateCreatedByApplication = p._subelement(el_creatingApplication,
                                                'dateCreatedByApplication')
    el_dateCreatedByApplication.text = date_created or creation_date(fname)

    # Create object element
    unique = str(uuid4())
    object_identifier = p.premis_identifier(
        identifier_type='digital-object-id',
        identifier_value=unique)

    el_premis_object = p.premis_object(
        object_identifier, child_elements=[el_objectCharacteristics])
    tree.append(el_premis_object)

    return tree


def fileinfo(fname):
    """Return fileinfo dict for given file."""
    fm = magic.Magic(mime=True)
    mimetype = fm.from_file(fname)

    fm = fm = magic.Magic(mime=False)
    version = fm.from_file(fname).split("version ")[-1]

    charset = None
    if mimetype == 'text/plain':
        charset = 'UTF-8' if 'UTF-8' in version else 'ISO-8859-15'
        version = None

    return {
        'filename': fname,
        'format': {
            'mimetype': mimetype,
            'version': version,
            'charset': charset
        }
    }


def md5(fname):
    """Calculate md5 checksum for given file."""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def collect_filepaths(dirs=['.'], pattern='*'):
    """Collect file paths recursively from given directory. Raises IOError
    if given path does not exist."""
    files = []
    for directory in dirs:
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
        return datetime.datetime.fromtimestamp(os.path.getctime(path_to_file)).isoformat()
    else:
        stat = os.stat(path_to_file)
        try:
            return datetime.datetime.fromtimestamp(stat.st_birthtime).isoformat()
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return datetime.datetime.fromtimestamp(stat.st_mtime).isoformat() 

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
