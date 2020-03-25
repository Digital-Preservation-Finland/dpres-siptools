"""Command line tool for creating METS document and copying files to workspace
directory.
"""
from __future__ import unicode_literals, print_function

import datetime
import os
import sys
import uuid
from shutil import copyfile

import click
import six

import lxml.etree
import mets
import xml_helpers.utils as xml_utils
from scandir import scandir
from siptools.mdcreator import get_objectlist, read_md_references
from siptools.xml.mets import (METS_CATALOG, METS_PROFILE, METS_SPECIFICATION,
                               NAMESPACES, RECORD_STATUS_TYPES, mets_extend)

click.disable_unicode_literals_warning = True


@click.command()
@click.argument('mets_profile', type=click.Choice(METS_PROFILE))
@click.argument('organization_name', type=str)
@click.argument('contractid', type=click.UUID)
@click.option('--workspace',
              type=click.Path(exists=True),
              default='./workspace',
              metavar='<WORKSPACE PATH>',
              help='Workspace directory. Defaults to "./workspace".')
@click.option('--base_path',
              metavar='<BASE PATH>',
              type=click.Path(exists=True),
              default='.',
              help='Base path of the digital objects.')
@click.option('--objid', type=str,
              default=six.text_type(uuid.uuid4()),
              metavar='<OBJID>',
              help='Unique identifier for the package')
@click.option('--label',
              type=str,
              metavar='<LABEL>',
              help='Short description of the information package')
@click.option('--contentid',
              type=str,
              metavar='<CONTENTID>',
              help='Identifier for content. Defaults to <OBJID>.')
@click.option('--create_date',
              type=str,
              default=datetime.datetime.utcnow().isoformat(),
              metavar='<CREATION DATE>',
              help='SIP create datetime formatted as '
                   'yyyy-mm-ddThh:mm:ss. Defaults to current time.')
@click.option('--last_moddate',
              type=str,
              metavar='<LAST MODIFICATION DATE>',
              help='Last modification datetime formatted as '
                   'yyyy-mm-ddThh:mm:ss')
@click.option('--record_status',
              type=click.Choice(RECORD_STATUS_TYPES),
              default='submission',
              metavar='<RECORD STATUS>',
              help='Record status. Defaults to "submission".')
@click.option('--clean',
              is_flag=True,
              help='Remove partial METS documents from workspace directory')
@click.option('--copy_files',
              is_flag=True,
              help='Copy digital objects from base path to workspace')
@click.option('--stdout',
              is_flag=True,
              help='Print output to stdout.')
@click.option('--packagingservice',
              type=str,
              metavar='<PACKAGING SERVICE>',
              help='If defined, add packaging service as CREATOR '
                   'agent to METS Header.')
def main(**kwargs):
    """Merge partial METS documents in workspace directory into
    one METS document.

    \b
    METS_PROFILE: METS profile.
    ORGANIZATION_NAME: Creator name (organization)
    CONTRACTID: Contract ID given by the Digital Preservation Service
    """
    compile_mets(**kwargs)
    return 0


def _attribute_values(given_params, fill_contentid=False):
    """
    Give attribute values as a dict for the script.

    :given_params: Arguments as dict.
    :fill_contentid: True sets attribute "contentid" same as "objid" if
                     "objid" is in given_params, but "contentid" is not.
    :returns: Initialized dict.
    """
    attributes = {
        "mets_profile": given_params["mets_profile"],
        "organization_name": given_params["organization_name"],
        "contractid": given_params["contractid"],
        "workspace": "./workspace/",
        "base_path": ".",
        "objid": six.text_type(uuid.uuid4()),
        "contentid": None,
        "create_date": datetime.datetime.utcnow().isoformat(),
        "record_status": "submission",
        "stdout": False,
        "clean": False,
        "copy_files": False,
        "label": None,
        "last_moddate": None,
        "packagingservice": None,
    }
    for key in given_params:
        if given_params[key]:
            attributes[key] = given_params[key]

    if not str(attributes["contractid"]).startswith("urn:uuid:"):
        attributes["contractid"] = "urn:uuid:%s" % attributes["contractid"]
    if fill_contentid and given_params["objid"] and not \
            attributes["contentid"]:
        attributes["contentid"] = given_params["objid"]

    return attributes


def compile_mets(**kwargs):
    """
    Merge partial METS documents in workspace directory into
    one METS document.

    :kwargs: Given arguments:
             mets_profile: METS profile (mandatory)
             organization_name: Creator name (mandatory)
             contractid: Contract ID (mandatory)
             objid: Unique identifier for the package
             contentid: Identifier of the content
             create_date: Package creation date
             last_moddate: Last modification date
             workspace: Workspace path
             base_path: Base path of the digital objects
             record_status: Record status
             label: Short description about the package
             clean: True for cleaning the workspace from temporary files
             copy_files: True copies the digital objects from base_path to
                         workspace
             stdout: True prints the output to stdout
             packagingservice: Packaging service specific parameter
    """
    attributes = _attribute_values(kwargs, True)

    mets_document = create_mets(**attributes)

    if attributes["stdout"]:
        print(xml_utils.serialize(mets_document.getroot()))

    output_file = os.path.join(attributes["workspace"], 'mets.xml')

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'wb+') as outfile:
        outfile.write(xml_utils.serialize(mets_document.getroot()))

    print("compile_mets created file: %s" % output_file)

    if attributes["copy_files"]:
        copy_objects(attributes["workspace"], attributes["base_path"])
        print("compile_mets copied objects from %s to "
              "workspace" % attributes["base_path"])

    if attributes["clean"]:
        clean_metsparts(attributes["workspace"])
        print("compile_mets cleaned work files from workspace.")


def create_mets(fill_contentid=False, **attributes):
    """Creates METS document element tree. Looks for files with prefix
    "-amd.xml", "dmdsec.xml", "structmap.xml", "filesec.xml", and
    "rightsmd.xml" from workspace and merges the dmdSec,
    amdSec, fileSec, and structMap elements (one element from each file) into
    one METS document. Also metsHdr element is created and included in
    document.

    :fill_contentid: True sets attribute "contentid" same as "objid" if
                     "objid" is given, but "contentid" is not.
    :attributes: The following keys:
                 mets_profile: METS Profile (mandatory)
                 organization_name: Creator name (mandatory)
                 contractid: Contract ID (mandatory)
                 objid: Unique identifier for the package
                 contentid: Identifier of the content
                 create_date: Package creation date
                 last_moddate: Last modification date
                 workspace: Workspace path
                 record_status: Record status
                 label: Short description about the package
                 packagingservice: Packaging service specific parameter
    :returns: METS document ElementTree object
    """
    attributes = _attribute_values(attributes, fill_contentid)
    # Create list of agent elements
    if attributes["packagingservice"]:
        agents = [mets.agent(attributes["organization_name"],
                             agent_role='ARCHIVIST')]
        agents.append(mets.agent(attributes["packagingservice"],
                                 agent_type='OTHER',
                                 agent_role='CREATOR',
                                 othertype='SOFTWARE'))
    else:
        agents = [mets.agent(attributes["organization_name"],
                             agent_role='CREATOR')]

    # Create mets header
    metshdr = mets.metshdr(attributes["create_date"],
                           attributes["last_moddate"],
                           attributes["record_status"],
                           agents)

    # Collect elements from workspace XML files
    elements = []
    for entry in scandir(attributes["workspace"]):
        if entry.name.endswith(('-amd.xml', 'dmdsec.xml',
                                'structmap.xml', 'filesec.xml',
                                'rightsmd.xml')) and entry.is_file():
            element = lxml.etree.parse(entry.path).getroot()[0]
            elements.append(element)

    elements = mets.merge_elements('{%s}amdSec' % NAMESPACES['mets'], elements)
    elements.sort(key=mets.order)

    # Create METS element
    mets_element = mets.mets(METS_PROFILE[attributes["mets_profile"]],
                             objid=attributes["objid"],
                             label=attributes["label"],
                             namespaces=NAMESPACES)
    mets_element = mets_extend(mets_element,
                               METS_CATALOG,
                               METS_SPECIFICATION,
                               attributes["contentid"],
                               attributes["contractid"])
    mets_element.append(metshdr)
    for element in elements:
        mets_element.append(element)
    lxml.etree.cleanup_namespaces(mets_element)

    return lxml.etree.ElementTree(mets_element)


def clean_metsparts(path):
    """
    Clean mets parts from workspace.

    :path: Workspace path
    """
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            if (name.endswith(('-amd.xml', 'dmdsec.xml', 'structmap.xml',
                               'filesec.xml', 'rightsmd.xml',
                               'md-references.xml',
                               '-scraper.json'))):
                os.remove(os.path.join(root, name))


def copy_objects(workspace, data_dir):
    """
    Copy digital objects to workspace.

    :workspace: Workspace path
    :data_dir: Path to digital objects
    """
    files = get_objectlist(read_md_references(
        workspace, "import-object-md-references.xml"
    ))
    for source in files:
        target = os.path.join(workspace, source)
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        copyfile(os.path.join(data_dir, source), target)


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
