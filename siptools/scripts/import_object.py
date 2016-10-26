"""Command line tool for importing digital objects"""

import os
import sys
from uuid import uuid4
from urllib import quote_plus
import argparse

import siptools.scraper
import siptools.xml.premis as p
import siptools.xml.mets as m


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="Tool for importing files "
                                     "which generates digital objects")
    parser.add_argument('files', nargs='+', help="Files to be imported")
    parser.add_argument('--output', type=str, default='./workspace/',
                        help="Destination file")
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    # Loop files and create premis objects
    for filename in args.files:
        mets = m._element('mets')
        techmd = m.techmd('techmd-%s' % filename)
        mets.append(techmd)
        digital_object = create_premis_object(techmd, filename)

        if args.stdout:
            print m.serialize(mets)

        if not os.path.exists(args.output):
            os.makedirs(args.output)

        filename = quote_plus(os.path.splitext(filename)[0]) + '-dmdsec.xml'

        with open(os.path.join(args.output, filename), 'w+') as outfile:
            outfile.write(m.serialize(mets))

    return 0


def create_premis_object(tree, fname):
    """Create Premis object for given file."""
    scraper = siptools.scraper.scraper(fname)

    # Create fixity element
    el_fixity = p._element('fixity')
    el_fixity_algorithm = p._subelement(
        el_fixity, 'digestAlgorithm', 'message')
    el_fixity_algorithm.text = 'MD5'

    el_fixity_checksum = p._subelement(el_fixity, 'digest', 'message')
    el_fixity_checksum.text = scraper.md5

    # Create format element
    el_format = p._element('format')
    el_format_name = p._subelement(el_format, 'name', 'format')
    el_format_name.text = scraper.mimetype
    el_format_version = p._subelement(el_format, 'version', 'format')
    el_format_version.text = scraper.file_version

    # Create object element
    unique = str(uuid4())
    object_identifier = p.premis_identifier(
        identifier_type='digital-object-id',
        identifier_value=unique)

    el_premis_objectp_objectg = p.premis_object(
        object_identifier, fname, child_elements=[el_fixity, el_format])
    tree.append(el_premis_objectp_objectg)

    return tree


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
