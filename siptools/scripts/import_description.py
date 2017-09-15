""" import_description"""

import sys
import argparse
import os
import lxml.etree
import mets
import xml_helpers.utils as h
import siptools.xml

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

    mets = mets.mets.mets_mets()

    tree = lxml.etree.fromstring(content)

    if args.desc_root == 'remove':
        childs = tree.findall('*')
    else:
        childs = [tree]
    xmldata_e = mets.mdwrap.xmldata(child_elements=childs)
    ns = xml_helpers.get_namespace(childs[0])

    if ns in siptools.xml.NAMESPACES.keys():
        mdt = siptools.xml.NAMESPACES[ns]['mdtype']
        mdo = siptools.xml.NAMESPACES[ns]['othermdtype']
        mdv = siptools.xml.NAMESPACES[ns]['mdtypeversion']
    else:
        raise TypeError("Invalid namespace: %s" % ns)

    mdwrap_e = mets.mdwrap.mdwrap(mdtype=mdt, othermdtype=mdo, mdtypeversion=mdv,
                      child_elements=[xmldata_e])
    dmdsec_e = mets.dmdsec.dmdsec(encode_id(url_t_path), child_elements=[mdwrap_e])

    mets.append(dmdsec_e)

    if args.stdout:
        print h.serialize(mets)

    output_file = os.path.join(args.workspace, url_t_path)
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(h.serialize(mets))

    print "import_description created file: %s" % output_file

    return 0


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Create descriptive metadata")
    parser.add_argument('dmdsec_location', type=str,
                        help='Location of descriptive metadata')
    parser.add_argument('--dmdsec_target', dest='dmdsec_target', type=str,
                        help='Target of descriptive metadata.'
                             'Default is the root of dataset')
    parser.add_argument('--workspace', dest='workspace', type=str,
                        default='./workspace', help="Workspace directory")
    parser.add_argument('--desc_root', type=str,
                        help='Preserve or remove root element of descriptive '
                             'metadata')
    parser.add_argument('--stdout', help='Print output to stdout')

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
