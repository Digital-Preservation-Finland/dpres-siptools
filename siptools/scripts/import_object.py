"""Command line tool for importing digital objects"""

import sys
import hashlib
import subprocess
from uuid import uuid4
import argparse

import siptools.xml.premis as p
import siptools.xml.mets as m


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="Tool for importing files "
                                     "which generates digital objects")
    parser.add_argument('output_file', help="Destination file")
    parser.add_argument('files', nargs='+', help="Files to be imported")
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    mets = m._element('mets')

    # Loop files and create premis objects
    for filename in args.files:
        techmd = m.techmd('techmd-%s' % filename)
        mets.append(techmd)
        digital_object = create_premis_object(techmd, filename)

    if args.stdout:
        print m.serialize(mets)

    with open(args.output_file, 'w') as outfile:
        outfile.write(m.serialize(mets))

    return 0


def create_premis_object(tree, filename):
    """Create Premis object for given file."""

    # Create fixity element
    el_fixity = p._element('fixity')
    el_fixity_algorithm = p._subelement(el_fixity, 'digestAlgorithm', 'message')
    el_fixity_algorithm.text = 'MD5'

    el_fixity_checksum = p._subelement(el_fixity, 'digest', 'message')
    el_fixity_checksum.text = calculate_checksum(filename)

    # Create format element
    el_format = p._element('format')
    el_format_name = p._subelement(el_format, 'name', 'format')
    el_format_name.text = get_mimetype(filename)

    # Create object element
    unique = str(uuid4())
    object_identifier = p.premis_identifier(
        identifier_type='digital-object-id',
        identifier_value=unique)

    el_premis_objectp_objectg = p.premis_object(
        object_identifier, filename, child_elements=[el_fixity, el_format])
    tree.append(el_premis_objectp_objectg)

    return tree


def calculate_checksum(fname):
    """Calculate md5 checksum for given file."""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_mimetype(fname):
    """Get mimetype for given file."""
    mime = subprocess.Popen("/usr/bin/file --mime-type %s" % fname, shell=True,
                            stdout=subprocess.PIPE).communicate()[0]
    return mime.split(' ')[1]

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
