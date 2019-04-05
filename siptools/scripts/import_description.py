"""Create METS document that contains descriptive metadata imported from XML
file
"""

import sys
import os

import click
import lxml.etree
import mets

from siptools.xml.mets import METS_MDTYPES
from siptools.utils import encode_path, encode_id


@click.command()
@click.argument('dmdsec_location', type=click.Path(exists=True),
                metavar='DMDLOCATION')
@click.option('--dmdsec_target',
              type=str,
              metavar='<DMD TARGET>',
              help='Target of descriptive metadata. '
                   'Default is the root of dataset.')
@click.option('--workspace', type=click.Path(exists=True),
              metavar='<WORKSPACE PATH>',
              default='./workspace',
              help="Directory where output is created")
@click.option('--remove_root', is_flag=True,
              help='Import only child elements from descriptive '
                   'metadata file')
@click.option('--stdout', is_flag=True,
              help='Print output to stdout')
def main(dmdsec_location, dmdsec_target, workspace, remove_root, stdout):
    """
    Create METS documents that contains descriptive metadata
    imported from XML file.

    DMDLOCATION: Path to XML file that contains descriptive metadata.

    """
    if dmdsec_target:
        filename = encode_path(dmdsec_target, suffix='-dmdsec.xml')
    else:
        filename = 'dmdsec.xml'

    _mets = create_mets(dmdsec_location, filename, remove_root)

    if stdout:
        print lxml.etree.tostring(_mets, pretty_print=True)

    output_file = os.path.join(workspace, filename)
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


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
