"""import_description"""

import sys
import argparse
import os
import lxml.etree
import mets
from siptools.xml.mets import METS_MDTYPES

from siptools.utils import encode_path, encode_id


def main(arguments=None):
    """The main method for import_description"""
    args = parse_arguments(arguments)

    if args.dmdsec_target:
        filename = encode_path(args.dmdsec_target, suffix='-dmdsec.xml')
    else:
        filename = 'dmdsec.xml'

    _mets = create_mets(args.dmdsec_location, filename, args.desc_root)

    if args.stdout:
        print lxml.etree.tostring(_mets, pretty_print=True)

    output_file = os.path.join(args.workspace, filename)
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    _mets.write(output_file,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8')

    print "import_description created file: %s" % output_file

    return 0


def create_mets(input_file, filename, remove_root=False):
    """Create METS element tree that contains dmdSec element. Descriptive
    metadata is imported from XML file. The whole XML document or just the
    child elements of root can be imported.

    :param input_file: path to input file
    :param filename: file name for generating dmdSec identifier
    :param remove_root: import only child elements
    :returns: METS document element tree
    """

    # Read metadata from XML file.
    tree = lxml.etree.parse(input_file)
    if remove_root:
        metadata = tree.findall('*')
    else:
        metadata = [tree.getroot()]

    # Check metadata type
    namespace = metadata[0].nsmap[metadata[0].prefix]
    if namespace in METS_MDTYPES.keys():
        mdtype = METS_MDTYPES[namespace]['mdtype']
    else:
        raise TypeError("Invalid namespace: %s" % namespace)
    othermdtype = METS_MDTYPES[namespace].get('othermdtype', None)
    version = METS_MDTYPES[namespace]['version']

    # Create METS Element
    xmldata_element = mets.xmldata(child_elements=metadata)
    mdwrap_element = mets.mdwrap(mdtype=mdtype,
                                 othermdtype=othermdtype,
                                 mdtypeversion=version,
                                 child_elements=[xmldata_element])
    dmdsec_element = mets.dmdsec(encode_id(filename),
                                 child_elements=[mdwrap_element])
    mets_element = mets.mets(child_elements=[dmdsec_element])

    tree = lxml.etree.ElementTree(mets_element)
    lxml.etree.cleanup_namespaces(tree)
    return tree


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
