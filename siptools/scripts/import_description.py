"""import_description"""

import sys
import argparse
import os
import lxml.etree
import mets
import xml_helpers.utils as h
from siptools.xml.mets import METS_MDTYPES

from siptools.utils import encode_path, encode_id


def main(arguments=None):
    """The main method for import_description"""
    args = parse_arguments(arguments)

    if args.dmdsec_target:
        url_t_path = encode_path(args.dmdsec_target, suffix='-dmdsec.xml')
    else:
        url_t_path = 'dmdsec.xml'

    with open(args.dmdsec_location, 'r') as content_file:
        content = content_file.read()

    _mets = mets.mets()

    tree = lxml.etree.fromstring(content)

    if args.desc_root == 'remove':
        childs = tree.findall('*')
    else:
        childs = [tree]
    xmldata_e = mets.xmldata(child_elements=childs)
    namespace = h.get_namespace(childs[0])

    if namespace in METS_MDTYPES.keys():
        mdtype = METS_MDTYPES[namespace]['mdtype']
        if 'othermdtype' in METS_MDTYPES[namespace]:
            othermdtype = METS_MDTYPES[namespace]['othermdtype']
        else:
            othermdtype = None
        version = METS_MDTYPES[namespace]['version']
    else:
        raise TypeError("Invalid namespace: %s" % namespace)

    mdwrap_e = mets.mdwrap(mdtype=mdtype,
                           othermdtype=othermdtype,
                           mdtypeversion=version,
                           child_elements=[xmldata_e])
    dmdsec_e = mets.dmdsec(encode_id(url_t_path), child_elements=[mdwrap_e])

    _mets.append(dmdsec_e)

    if args.stdout:
        print h.serialize(_mets)

    output_file = os.path.join(args.workspace, url_t_path)
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(h.serialize(_mets))

    print "import_description created file: %s" % output_file

    return 0


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Create descriptive metadata"
    )
    parser.add_argument('dmdsec_location',
                        type=str,
                        help='Location of descriptive metadata')
    parser.add_argument('--dmdsec_target',
                        dest='dmdsec_target',
                        type=str,
                        help='Target of descriptive metadata. '
                             'Default is the root of dataset')
    parser.add_argument('--workspace',
                        dest='workspace',
                        type=str,
                        default='./workspace',
                        help="Workspace directory")
    parser.add_argument('--desc_root',
                        type=str,
                        help='Preserve or remove root element of descriptive '
                             'metadata')
    parser.add_argument('--stdout',
                        help='Print output to stdout')

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
