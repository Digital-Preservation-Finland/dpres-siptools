"""Create METS document that contains descriptive metadata imported from XML
file
"""

import sys
import os

from uuid import uuid4

import click
import lxml.etree
import mets

from siptools.xml.mets import METS_MDTYPES
from siptools.utils import AmdCreator


@click.command()
@click.argument('dmdsec_location', type=click.Path(exists=True),
                metavar='DMDLOCATION')
@click.option('--workspace', type=click.Path(exists=True),
              metavar='<WORKSPACE PATH>',
              default='./workspace',
              help="Workspace directory for the metadata files. "
                   "Defaults to ./workspace/")
@click.option('--dmdsec_target',
              type=str,
              metavar='<DMD TARGET>',
              help='Target of descriptive metadata. '
                   'Default is the root of dataset.')
@click.option('--remove_root', is_flag=True,
              help='Import only child elements from descriptive '
                   'metadata file')
@click.option('--stdout', is_flag=True,
              help='Print output to stdout')
def main(dmdsec_location, dmdsec_target, workspace, remove_root, stdout):
    """Create METS documents that contains descriptive metadata
    imported from XML file.

    DMDLOCATION: Path to XML file that contains descriptive metadata.
    """
    import_description(
        dmdsec_location, dmdsec_target, workspace, remove_root, stdout
    )
    return 0


def import_description(dmdsec_location, dmdsec_target=None,
                       workspace="./workspace", remove_root=False,
                       stdout=False):
    """Create METS documents that contains descriptive metadata
    imported from XML file.
    """
    dmdfile_id = str(uuid4())
    dmd_id = '_' + dmdfile_id
    filename = '%s-dmdsec.xml' % dmdfile_id

    _mets = create_mets(dmdsec_location, dmd_id, remove_root)
    creator = DmdCreator(workspace)
    creator.add_dmdsec(_mets, dmd_id, dmdsec_target)

    if stdout:
        print lxml.etree.tostring(_mets, pretty_print=True)

    output_file = os.path.join(workspace, filename)
    if os.path.isfile(output_file):
        raise OSError('File {} already exists.'.format(output_file))

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    _mets.write(output_file,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8')

    print "import_description created file: %s" % output_file


class DmdCreator(AmdCreator):
    """Subclass of AmdCreator, which generates dmdSec metadata."""

    def add_dmdsec(self, dmd_xml, dmd_id, dmd_target=None):
        """Create METS element tree that contains dmdSec element.
        Descriptive metadata is imported from XML file. The whole XML
        document or just the child elements of root can be imported.

        :param filename: file name for generating dmdSec identifier
        :returns: METS document element tree
        """

        if not dmd_target:
            dmd_target = '.'

        self.add_md(metadata=dmd_xml, directory=dmd_target)
        self.add_reference(dmd_id, None, directory=dmd_target, ref_type='dmd')
        self.write_references()


def create_mets(input_file, dmd_id, remove_root=False):
    """Create METS element tree that contains dmdSec element. Descriptive
    metadata is imported from XML file. The whole XML document or just the
    child elements of root can be imported.

    :param input_file: path to input file
    :param dmd_id: dmdSec identifier
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
    dmdsec_element = mets.dmdsec(dmd_id, child_elements=[mdwrap_element])
    mets_element = mets.mets(child_elements=[dmdsec_element])

    tree = lxml.etree.ElementTree(mets_element)
    lxml.etree.cleanup_namespaces(tree)
    return tree


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
