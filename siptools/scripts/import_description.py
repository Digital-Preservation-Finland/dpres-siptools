"""
Create METS document that contains descriptive metadata imported from XML file
"""
from __future__ import unicode_literals, print_function

import sys
import os
import datetime

from uuid import uuid4

import click
import lxml.etree
import mets

from siptools.xml.mets import METS_MDTYPES
from siptools.mdcreator import MetsSectionCreator
from siptools.scripts.premis_event import premis_event

click.disable_unicode_literals_warning = True


@click.command()
@click.argument('dmdsec_location', type=click.Path(exists=True),
                metavar='DMDLOCATION')
@click.option('--workspace', type=click.Path(exists=True),
              metavar='<WORKSPACE PATH>',
              default='./workspace',
              help="Workspace directory for the metadata files. "
                   "Defaults to ./workspace/")
@click.option('--base_path', type=click.Path(exists=True), default='.',
              metavar='<BASE PATH>',
              help=("Source base path of dmdsec_target. If used, give "
                    "dmdsec_target in relation to this base path."))
@click.option('--dmdsec_target',
              type=str,
              metavar='<DMD TARGET>',
              help='Target of descriptive metadata. '
                   'Default is the root of dataset.')
@click.option('--dmd_source',
              type=str,
              metavar='<DMD SOURCE>',
              help=('The source, e.g. database or system, that the '
                    'descriptive metadata was imported from'))
@click.option('--dmd_agent', nargs=2,
              type=str,
              metavar='<AGENT NAME> <AGENT TYPE>',
              help=('The agent name and type that was used in importing the '
                    'descriptive metadata from the source to XML'))
@click.option('--without_uuid', is_flag=True,
              help='Outputs a dmdsec.xml file without UUID prefix.')
@click.option('--remove_root', is_flag=True,
              help='Import only child elements from descriptive '
                   'metadata file')
@click.option('--stdout', is_flag=True,
              help='Print output to stdout')
#pylint: disable=too-many-arguments
def main(**kwargs):
    """Create METS documents that contains descriptive metadata
    imported from XML file.

    DMDLOCATION: Path to XML file that contains descriptive metadata.
    """
    import_description(**kwargs)
    return 0


def _attribute_values(given_params):
    """
    Give attribute values as a dict for the script.

    :given_params: Arguments as dict.
    :returns: Attribute value dict
    """
    attributes = {
        "dmdsec_location": given_params["dmdsec_location"],
        "workspace": "./workspace/",
        "base_path": ".",
        "dmdsec_target": None,
        "dmd_source": "external source",
        "dmd_agent": (),
        "dmdsec_target": None,
        "without_uuid": False,
        "remove_root": False,
        "stdout": False,
    }
    for key in given_params:
        if given_params[key]:
            attributes[key] = given_params[key]

    return attributes


def import_description(**kwargs):
    """
    Create METS documents that contains descriptive metadata
    imported from XML file.

    :kwargs: Given arguments
             dmdsec_location: Path of the descriptive metadata file
             workspace: Workspace path
             base_path: Base path of the digital objects
             dmdsec_target: Target of descriptive metadata
             dmd_source: The source that the descriptive metadata was
                         extracted from
             agent: The agent name and type that extracted the
                    descriptive metadata
             dmdsec_target: Target of descriptive metadata
             without_uuid: If true, output file named without UUID prefix
             remove_root: If true, remove root element from metadata
             stdout: If true, print output to stdout
    :raises: OSError if descriptive metadata file exists
    """
    attributes = _attribute_values(kwargs)
    dmd_target = dmd_target_path(attributes["base_path"],
                                 attributes["dmdsec_target"])
    dmdfile_id = str(uuid4())
    dmd_id = '_' + dmdfile_id
    if attributes["without_uuid"]:
        filename = 'dmdsec.xml'
    else:
        filename = '%s-dmdsec.xml' % dmdfile_id

    _mets = create_mets(attributes["dmdsec_location"], dmd_id,
                        attributes["remove_root"])
    creator = DmdCreator(attributes["workspace"])
    creator.write_dmd_ref(_mets, dmd_id, dmd_target)

    if attributes["stdout"]:
        print(lxml.etree.tostring(_mets, pretty_print=True).decode("utf-8"))

    output_file = os.path.join(attributes["workspace"], filename)
    if os.path.isfile(output_file):
        raise OSError('File {} already exists.'.format(output_file))

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    _mets.write(output_file,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8')

    # Create events documenting the technical metadata creation
    _create_event(
         workspace=attributes["workspace"],
         base_path=attributes["base_path"],
         event_target=attributes["dmdsec_target"],
         dmd_source=attributes["dmd_source"],
         dmd_agent=attributes["dmd_agent"]
     )

    print("import_description created file: %s" % output_file)


def dmd_target_path(base_path, dmdsec_target):
    """"
    Returns the path to the dmdsec_target based on the base_path and
    dmdsec_target. If dmdsec_target is None, the dmdsec concerns the whole
    package.

    :base_path: Base path
    :dmdsec_target: Target directory of the descriptive metadata
    """
    if dmdsec_target:
        if base_path not in ['.']:
            dmd_target = os.path.normpath(os.path.join(base_path,
                                                       dmdsec_target))
        else:
            dmd_target = os.path.normpath(dmdsec_target)

        if not os.path.isdir(dmd_target):
            raise IOError

    else:
        dmdsec_target = '.'

    return os.path.normpath(dmdsec_target)


class DmdCreator(MetsSectionCreator):
    """
    Subclass of MetsSectionCreator, which generates dmdSec metadata.
    """

    def write_dmd_ref(self, dmd_xml, dmd_id, dmd_target=None):
        """
        Adds references to the dmdSec and writes them to the
        external reference file.

        :dmd_xml: Descriptive metadata as XML
        :dmd_id: ID of the descriptive metadata
        :dmd_target: Target directory of the descriptive metadata
        """

        if not dmd_target:
            dmd_target = '.'

        self.add_md(metadata=dmd_xml, directory=dmd_target)
        self.add_reference(dmd_id, None, directory=dmd_target)
        self.write_references(ref_file="import-description-md-references.xml")


def create_mets(input_file, dmd_id, remove_root=False):
    """Create METS element tree that contains dmdSec element. Descriptive
    metadata is imported from XML file. The whole XML document or just the
    child elements of root can be imported.

    :input_file: path to input file
    :dmd_id: dmdSec identifier
    :remove_root: import only child elements
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


def _create_event(
        workspace,
        base_path,
        event_target,
        dmd_source,
        dmd_agent=None):
    """Function to create an event for documenting the import of
    descriptive metadata and the source from where the metadata was
    extracted.

    :workspace: The path to the workspace
    :base_path: Base path (see --base_path)
    :event_target: The target of the descriptive metadata
    :dmd_source: The source that the descriptive metadata was extracted
                 from
    :dmd_agent: The agent software that extracted the descriptive
                metadata
    """
    agent_name = None
    agent_type = None
    if source_agent:
        (agent_name, agent_type) = source_agent

    event_datetime = datetime.datetime.now().isoformat()
    premis_event(event_type="metadata extraction",
                 event_datetime=event_datetime,
                 event_detail=("Descriptive metadata import from external "
                               "source"),
                 event_outcome="success",
                 event_outcome_detail=("Descriptive metadata imported to "
                                       "mets dmdSec from %s" % dmd_source),
                 workspace=workspace,
                 base_path=base_path,
                 agent_name=agent_name,
                 agent_type=agent_type,
                 event_target=event_target)


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
