""" import_description"""

import sys
import argparse
import os
import lxml.etree
import siptools.xml.mets as m
from urllib import quote_plus

from siptools.utils import encode_path

def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    path = os.path.join(args.workspace, args.dmdsec_target)
    url_t_path = encode_path(args.dmdsec_target, suffix='-dmdsec.xml')

    with open(args.dmdsec_location, 'r') as content_file:
        content = content_file.read()

    mets = m.mets_mets()

    parser = lxml.etree.XMLParser(
            dtd_validation=False, no_network=True)
    tree = lxml.etree.fromstring(content)

    childNodeList = tree.findall('*')
    dmdsec = m.dmdSec(element_id=url_t_path, child_elements=childNodeList)
    mets.append(dmdsec)

    if args.stdout:
        print m.serialize(mets)

    output_file = os.path.join(args.workspace, url_t_path)
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(m.serialize(mets))

    print "import_description created file: %s" % output_file

    return 0


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="A short description of this "
                                     "program")
    parser.add_argument('dmdsec_location', type=str,
            help='Location of descriptive metadata')
    parser.add_argument('--dmdsec_target', dest='dmdsec_target', type=str,
            default='./', help='Digital object (or file) which is the target of descriptive'
            'metadata. Default is the root of digital objects')
    parser.add_argument('--workspace', dest='workspace', type=str,
            default='./', help="Workspace directory")
    parser.add_argument('--stdout', help='Print output to stdout')

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
