"""Command line tool for creating the structural map and file section
metadata for a METS document.
"""

import os
import sys
import datetime

import click

import lxml.etree as ET
import mets
import xml_helpers.utils as xml_utils
from siptools.scripts.create_agent import create_agent
from siptools.scripts.premis_event import premis_event
from siptools.ead_utils import compile_ead3_structmap
from siptools.utils import (add,
                            add_file_div,
                            create_filegrp,
                            encode_path,
                            get_md_references,
                            get_reference_lists,
                            iter_supplementary,
                            read_md_references,
                            SUPPLEMENTARY_TYPES,
                            tree)
from siptools.xml.mets import NAMESPACES

import siptools

click.disable_unicode_literals_warning = True

SUPPLEMENTARY_REFERENCE_FILES = {
    'fi-dpres-xml-schemas': 'define-xml-schemas-md-references.jsonl'
}


@click.command()
@click.option('--workspace',
              type=click.Path(exists=True),
              default='./workspace/',
              metavar='<WORKSPACE PATH>',
              help="Workspace directory. Defaults to ./workspace/")
@click.option('--structmap_type',
              type=str,
              metavar='<STRUCTMAP TYPE>',
              help="Type of structmap e.g. 'Fairdata-physical', "
                   "'EAD3-logical', or 'Directory-physical'")
@click.option('--root_type',
              type=str,
              default='directory',
              metavar='<ROOT TYPE>',
              help="Type of root div")
@click.option('--dmdsec_loc',
              type=str,
              metavar='<DMD LOCATION>',
              help="Location of structured descriptive metadata, "
                   "if applicable.")
@click.option('--stdout',
              is_flag=True,
              help='Print output also to stdout.')
def main(workspace, structmap_type, root_type, dmdsec_loc, stdout):
    """Tool for generating METS file section and structural map based on
    created/imported administrative metada and descriptive metadata.
    The script will also add order of the file to the structural map
    (via json file), if --order argument was used in import_object
    script.
    """
    compile_structmap(workspace=workspace,
                      structmap_type=structmap_type,
                      root_type=root_type,
                      dmdsec_loc=dmdsec_loc,
                      stdout=stdout)

    return 0


# pylint: disable=too-many-locals
def compile_structmap(workspace='./workspace/',
                      structmap_type=None,
                      root_type='directory',
                      dmdsec_loc=None,
                      stdout=False):
    """Generate METS file section and structural map based on
    created/imported administrative metada and descriptive metadata.

    Supplementary files are put in a separate fileGrp section and
    a separate structmap file is created for these files.

    :param workspace: Workspace directory
    :param structmap_type: Type of structmap
    :param root_type: Type of root div
    :param dmdsec_loc: Location of structured descriptive metadata
    :param stdout: True to print output to stdout
    """
    # Create an event documenting the structmap creation
    _create_event(
        workspace=workspace,
        structmap_type=structmap_type,
        root_type=root_type
    )

    # Get reference list only after the structmap creation event
    (all_amd_refs,
     all_dmd_refs,
     object_refs,
     filelist,
     file_properties) = get_reference_lists(workspace=workspace)

    # Get all supplementary files.
    (supplementary_files, supplementary_types) = iter_supplementary(
        file_properties=file_properties
    )

    # Create EAD3 based structMap and fileSec for EAD3-logical types
    if structmap_type == 'EAD3-logical':
        (structmap, filesec, file_ids) = compile_ead3_structmap(
            dmdsec_loc=dmdsec_loc,
            workspace=workspace,
            all_amd_refs=all_amd_refs,
            all_dmd_refs=all_dmd_refs,
            object_refs=object_refs,
            file_properties=file_properties,
            supplementary_files=supplementary_files,
            supplementary_types=supplementary_types)

    else:
        (filesec, file_ids) = create_filesec(
            all_amd_refs=all_amd_refs,
            object_refs=object_refs,
            file_properties=file_properties,
            supplementary_files=supplementary_files,
            supplementary_types=supplementary_types)

        # Add file path and ID dict to attributes
        structmap = create_structmap(filesec=filesec,
                                     all_amd_refs=all_amd_refs,
                                     all_dmd_refs=all_dmd_refs,
                                     filelist=filelist,
                                     supplementary_files=supplementary_files,
                                     supplementary_types=supplementary_types,
                                     structmap_type=structmap_type,
                                     root_type=root_type,
                                     file_ids=file_ids,
                                     file_properties=file_properties,
                                     workspace=workspace)

    # Create a separate structmap for supplementary files if they exist
    if supplementary_files:
        root_type = SUPPLEMENTARY_TYPES['main']
        suppl_structmap = create_structmap(
            filesec=filesec,
            all_amd_refs=all_amd_refs,
            all_dmd_refs=all_dmd_refs,
            filelist=filelist,
            supplementary_files=supplementary_files,
            supplementary_types=supplementary_types,
            structmap_type='logical',
            root_type=root_type,
            file_ids=file_ids,
            file_properties=file_properties,
            workspace=workspace)

    if stdout:
        print(xml_utils.serialize(filesec).decode("utf-8"))
        print(xml_utils.serialize(structmap).decode("utf-8"))
        if supplementary_files:
            print(xml_utils.serialize(suppl_structmap).decode("utf-8"))

    output_sm_file = os.path.join(workspace, 'structmap.xml')
    output_fs_file = os.path.join(workspace, 'filesec.xml')
    created_files = [output_sm_file, output_fs_file]

    if not os.path.exists(os.path.dirname(output_sm_file)):
        os.makedirs(os.path.dirname(output_sm_file))

    if not os.path.exists(os.path.dirname(output_fs_file)):
        os.makedirs(os.path.dirname(output_fs_file))

    with open(output_sm_file, 'wb+') as outfile:
        outfile.write(xml_utils.serialize(structmap))

    with open(output_fs_file, 'wb+') as outfile:
        outfile.write(xml_utils.serialize(filesec))

    if supplementary_files:
        output_suppl_sm_file = os.path.join(workspace,
                                            'supplementary_structmap.xml')
        if not os.path.exists(os.path.dirname(output_suppl_sm_file)):
            os.makedirs(os.path.dirname(output_suppl_sm_file))
        with open(output_suppl_sm_file, 'wb+') as outfile:
            outfile.write(xml_utils.serialize(suppl_structmap))
        created_files.append(output_suppl_sm_file)

    print("compile_structmap created files: " + " ".join(created_files))


def create_filesec(all_amd_refs,
                   object_refs,
                   file_properties,
                   supplementary_files,
                   supplementary_types):
    """
    Create METS document element tree that contains fileSec element.

    Supplementary files are put in a separate fileGrp and will populate
    the supplementary_files attribute when they are discovered.

    :param all_amd_refs: XML element tree of administrative metadata
        references. Will be created if missing.
    :param object_refs: XML tree of digital objects. Will be created
        if missing.
    :param file_properties: Dictionary collection of file properties.
    :param supplementary_files: ID list of supplementary objects.
        Will be populated if supplementary objects exist.
    :param supplementary_types: Supplementary types.
    :returns: A tuple of METS XML Element including file section
              element and a dict of file paths and identifiers
    """
    child_elements = []
    file_ids = {}
    (filegrp, file_ids) = create_filegrp(
        file_ids=file_ids,
        supplementary_files=supplementary_files,
        all_amd_refs=all_amd_refs,
        object_refs=object_refs,
        file_properties=file_properties)
    child_elements.append(filegrp)

    # Create file group for supplementary files if they exist
    for supplementary_type in supplementary_types:
        (s_filegrp, file_ids) = create_filegrp(
            file_ids=file_ids,
            supplementary_files=supplementary_files,
            all_amd_refs=all_amd_refs,
            object_refs=object_refs,
            file_properties=file_properties,
            supplementary_type=supplementary_type)
        child_elements.append(s_filegrp)

    filesec = mets.filesec(child_elements=child_elements)
    mets_element = mets.mets(child_elements=[filesec])
    ET.cleanup_namespaces(mets_element)
    return mets_element, file_ids


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def create_structmap(filesec,
                     all_amd_refs,
                     all_dmd_refs,
                     filelist,
                     supplementary_files,
                     supplementary_types,
                     structmap_type,
                     file_ids,
                     file_properties,
                     workspace,
                     root_type='directory'):
    """
    Create METS document element tree that contains structural map.

    :param filesec: fileSec element
    :param all_amd_refs: XML element tree of administrative metadata
        references. Will be created if missing.
    :param all_dmd_refs: XML element tree of descriptive metadata
        references. Will be created if missing.
    :param filelist: Sorted list of digital objects (file paths).
        Will be created if missing.
    :param supplementary_files: ID list of supplementary objects.
    :param supplementary_types: Supplementary types.
    :param structmap_type: TYPE attribute of structMap element If
                           missing, default value is None.
    :param file_ids: Dict with file paths and identifiers. Required by
        create_div(). Will be computed if missing.
    :param file_properties: Dictionary collection of file properties.
    :param workspace: Workspace path, required by create_div(). If
                      missing, default value is "./workspace/".
    :param root_type: TYPE attribute of root div element. If missing,
        default value is "directory".
    :returns: structural map element
    """
    amdids = get_md_references(all_amd_refs, directory='.')
    dmdids = get_md_references(all_dmd_refs, directory='.')

    is_supplementary = False
    if structmap_type == 'Directory-physical':
        container_div = mets.div(type_attr='directory',
                                 label='.',
                                 dmdid=dmdids,
                                 admid=amdids)
    elif root_type == SUPPLEMENTARY_TYPES['main']:
        is_supplementary = True
        container_div = mets.div(type_attr=root_type,
                                 dmdid=None,
                                 admid=None)
    else:
        container_div = mets.div(type_attr=root_type,
                                 dmdid=dmdids,
                                 admid=amdids)

    structmap = mets.structmap(type_attr=structmap_type)
    structmap.append(container_div)

    divs = div_structure(filelist=filelist,
                         supplementary_files=supplementary_files,
                         supplementary_types=supplementary_types,
                         is_supplementary=is_supplementary)
    create_div(divs=divs,
               parent=container_div,
               filesec=filesec,
               all_amd_refs=all_amd_refs,
               all_dmd_refs=all_dmd_refs,
               supplementary_files=supplementary_files,
               file_ids=file_ids,
               structmap_type=structmap_type,
               workspace=workspace,
               file_properties=file_properties,
               is_supplementary=is_supplementary)

    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def div_structure(filelist,
                  supplementary_files,
                  supplementary_types,
                  is_supplementary):
    """Create div structure for either a directory-based structmap
    or for supplementary files.

    :param filelist: Sorted list of digital objects (file paths).
    :param supplementary_files: Sorted list of supplementary objects
        (file paths).
    :param supplementary_types: Supplementary types.
    :param is_supplementary: Boolean to indicate whether the structure
        should be for supplemenjtary files or not.
    :returns: The div structure as a dict like object
    """
    divs = tree()
    if is_supplementary:
        for supplementary_type in supplementary_types:
            # Supplementary structure is flat, but with one div
            # surrounding the files
            root_div = divs[SUPPLEMENTARY_TYPES[supplementary_type]]
            for amd_file in supplementary_files:
                if supplementary_files[amd_file] == supplementary_type:
                    add(root_div, [amd_file])
    else:
        # Directory based structure is like a directory tree
        for amd_file in filelist:
            # Do not add supplementary files to the directory based
            # structmap
            if amd_file not in supplementary_files:
                add(divs, amd_file.split('/'))
    return divs


def get_fileid(filesec, path, file_ids=None):
    """Return the ID for a file.

    Either finds a file with `path` from
    fileSec or reads the ID from a dict of `path` and `ID`. Returns the
    ID attribute of the matching file element.

    :filesec: fileSec element
    :path: path of the file
    :file_ids: Dict of file paths and file IDs
    :returns: file identifier
    """
    if not file_ids:
        encoded_path = encode_path(path, safe='/')
        element = filesec.xpath(
            '//mets:fileGrp/mets:file/mets:FLocat[@xlink:href="file://%s"]/..'
            % encoded_path,
            namespaces=NAMESPACES
        )[0]

        fileid = element.attrib['ID']
    else:
        fileid = file_ids[path]

    return fileid


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
def create_div(divs,
               parent,
               filesec,
               all_amd_refs,
               all_dmd_refs,
               supplementary_files,
               file_ids,
               structmap_type,
               workspace,
               file_properties,
               path='',
               is_supplementary=False):
    """Recursively create fileSec and structmap divs based on directory
    structure.

    :param divs: Current directory or file in directory structure
                 walkthrough
    :param parent: Parent element in structMap
    :param filesec: filesec element
    :param all_amd_refs: XML element tree of administrative metadata
        references.
    :param all_dmd_refs: XML element tree of descriptive metadata
        references.
    :param supplementary_files: ID list of supplementary objects.
        Will be populated if supplementary objects exist.
    :param file_ids: Dict with file paths and identifiers.
    :param workspace: Workspace path, required by add_file_div().
    :param file_properties: Dictionary collection of file properties.
    :param path: Current path in directory structure walkthrough
    :param is_supplementary: A boolean to indicate if a supplementary
                       structure is expected or not
    :returns: ``None``
    """
    fptr_list = []
    property_list = []
    div_list = []
    collection = file_properties
    for div in divs.keys():
        div_path = os.path.join(path, div)
        if is_supplementary:
            collection = supplementary_files
            # Remove supplementary root div from current div path
            supplementary_type = div_path.split('/')[0]
            div_path = div_path[len(supplementary_type) + 1:]
        # It's a file, lets create file+fptr elements
        if div_path in collection:
            fptr = mets.fptr(get_fileid(filesec, div_path, file_ids))
            div_elem = add_file_div(fptr=fptr,
                                    properties=file_properties[div_path])
            if div_elem is not None:
                property_list.append(div_elem)
            else:
                fptr_list.append(fptr)

        # It's not a file, lets create a div element
        else:
            amdids = get_md_references(all_amd_refs, directory=div_path)
            dmdsec_id = get_md_references(all_dmd_refs, directory=div_path)

            # Some supplementary divs require links to the amdSec
            if is_supplementary:
                try:
                    amdids = get_md_references(
                        read_md_references(
                            workspace,
                            SUPPLEMENTARY_REFERENCE_FILES[div]),
                        directory='.')
                except KeyError:
                    pass

            if structmap_type == 'Directory-physical':
                div_elem = mets.div(type_attr='directory',
                                    label=div,
                                    dmdid=dmdsec_id,
                                    admid=amdids)
            else:
                div_elem = mets.div(type_attr=div,
                                    dmdid=dmdsec_id,
                                    admid=amdids)
            div_list.append(div_elem)
            create_div(divs=divs[div],
                       parent=div_elem,
                       filesec=filesec,
                       all_amd_refs=all_amd_refs,
                       all_dmd_refs=all_dmd_refs,
                       supplementary_files=supplementary_files,
                       file_ids=file_ids,
                       structmap_type=structmap_type,
                       workspace=workspace,
                       file_properties=file_properties,
                       path=div_path)

    # Add fptr list first, then div list
    for fptr in fptr_list:
        parent.append(fptr)
    for div_elem in property_list:
        parent.append(div_elem)
    for div_elem in div_list:
        parent.append(div_elem)


def _create_event(
        workspace='./workspace/',
        structmap_type=None,
        root_type='directory'):
    """Helper function to create an event for documenting the
    creation of the structural map and its type (either the
    structmap type or the root type).

    The function calls the premis_event script for creating the premis
    event and agent metadata.

    :workspace: The path to the workspace
    :structmap_type: Type of structmap
    :root_type: Type of root div
    """
    if not structmap_type:
        if root_type:
            structmap_type = root_type
        else:
            structmap_type = 'directory'

    create_agent(
        workspace=workspace,
        agent_name='dpres-siptools',
        agent_version=siptools.__version__,
        agent_type='software',
        agent_role='executing program',
        create_agent_file='compile-structmap-agents')

    event_datetime = "{}+00:00".format(
        datetime.datetime.utcnow().replace(microsecond=0).isoformat())
    premis_event(event_type="creation",
                 event_datetime=event_datetime,
                 event_detail=("Creation of structural metadata with the "
                               "compile-structmap script"),
                 event_outcome="success",
                 event_outcome_detail=("Created METS structural map of type %s"
                                       % structmap_type),
                 workspace=workspace,
                 create_agent_file='compile-structmap-agents')


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
