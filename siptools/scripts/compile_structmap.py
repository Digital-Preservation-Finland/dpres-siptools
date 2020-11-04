""""Command line tool for creating the structural map and file section
metadata for a METS document."""
from __future__ import unicode_literals, print_function

import os
import sys
from uuid import uuid4
import datetime

import click

import lxml.etree as ET
import mets
import xml_helpers.utils as xml_utils
from siptools.scripts.create_agent import create_agent
from siptools.scripts.premis_event import premis_event
from siptools.utils import (add,
                            encode_path,
                            get_md_references,
                            get_objectlist,
                            load_scraper_json,
                            read_all_amd_references,
                            read_md_references,
                            tree)
from siptools.xml.mets import NAMESPACES

import siptools

click.disable_unicode_literals_warning = True

ALLOWED_C_SUBS = ['c', 'c01', 'c02', 'c03', 'c04', 'c05', 'c06', 'c07',
                  'c08', 'c09', 'c10', 'c11', 'c12']

SUPPLEMENTARY_TYPES = {
    'main': 'fi-preservation-supplementary',
    'xml_schema': 'fi-preservation-xml-schemas',
    'native': 'fi-preservation-no-file-format-validation'
}

SUPPLEMENTARY_REFERENCE_FILES = {
    'fi-preservation-xml-schemas': 'define-xml-schemas-references.jsonl'
}


def ead3_ns(tag):
    """Get tag with EAD3 namespace
    """
    path = '{%s}%s' % ('http://ead3.archivists.org/schema/', tag)
    return path


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
    (via json file), if --order argument was used in import_object script.
    """
    compile_structmap(workspace=workspace,
                      structmap_type=structmap_type,
                      root_type=root_type,
                      dmdsec_loc=dmdsec_loc,
                      stdout=stdout)

    return 0


def get_reference_lists(workspace):
    """
    Get reference lists.

    :param workspace: Workspace path
    :returns: Tuple of following things:
        - all_amd_refs: All administrative metadata references.
        - all_dmd_refs: All descriptive metadata references.
        - object_refs: XML tree of digital objects.
        - filelist: ID list of objects.
        - file_properties: Properties of all the files discvoered in filelist.
    """
    object_refs = read_md_references(workspace,
                                     "import-object-md-references.jsonl")
    filelist = get_objectlist(object_refs)
    all_amd_refs = read_all_amd_references(workspace)
    all_dmd_refs = read_md_references(workspace,
                                      "import-description-md-references.jsonl")

    # Get file properties for all the files after fetching reference lists.
    file_properties = {}
    for path in filelist:
        file_properties[path] = get_file_properties(path=path,
                                                    all_amd_refs=all_amd_refs,
                                                    workspace=workspace)
    return (all_amd_refs,
            all_dmd_refs,
            object_refs,
            filelist,
            file_properties)


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
    file_ids = {}

    if structmap_type == 'EAD3-logical':
        # If structured descriptive metadata for structMap divs is used, also
        # the fileSec element (apparently?) is different. The
        # create_ead3_structmap function populates the fileGrp element.
        filegrp = mets.filegrp()
        filesec_child_elems = [filegrp]

        structmap = create_ead3_structmap(
            filegrp=filegrp,
            all_amd_refs=all_amd_refs,
            all_dmd_refs=all_dmd_refs,
            dmdsec_loc=dmdsec_loc,
            structmap_type=structmap_type,
            workspace=workspace,
            object_refs=object_refs,
            file_properties=file_properties,
            supplementary_files=supplementary_files,
            supplementary_types=supplementary_types)

        for supplementary_type in supplementary_types:
            (s_filegrp, file_ids) = _create_filegrp(
                file_ids=file_ids,
                supplementary_files=supplementary_files,
                all_amd_refs=all_amd_refs,
                object_refs=object_refs,
                file_properties=file_properties,
                supplementary_type=supplementary_type)
            filesec_child_elems.append(s_filegrp)

        filesec_element = mets.filesec(child_elements=filesec_child_elems)
        filesec = mets.mets(child_elements=[filesec_element])
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
    Creates METS document element tree that contains fileSec element.

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
    (filegrp, file_ids) = _create_filegrp(
        file_ids=file_ids,
        supplementary_files=supplementary_files,
        all_amd_refs=all_amd_refs,
        object_refs=object_refs,
        file_properties=file_properties)
    child_elements.append(filegrp)

    # Create file group for supplementary files if they exist
    for supplementary_type in supplementary_types:
        (s_filegrp, file_ids) = _create_filegrp(
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
    Creates METS document element tree that contains structural map.

    :param filesec: fileSec element
    :param all_amd_refs: XML element tree of administrative metadata
        references. Will be created if missing.
    :param all_dmd_refs: XML element tree of descriptive metadata
        references. Will be created if missing.
    :param filelist: Sorted list of digital objects (file paths).
        Will be created if missing.
    :param supplementary_files: ID list of supplementary objects.
    :param supplementary_types: Supplementary types.
    :param structmap_type: TYPE attribute of structMap element If missing,
        default value is None.
    :param file_ids: Dict with file paths and identifiers. Required by
        create_div(). Will be computed if missing.
    :param file_properties: Dictionary collection of file properties.
    :param workspace: Workspace path, required by create_div(). If missing,
        default value is "./workspace/".
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
            # Supplementary structure is flat, but with one div surrounding the
            # files
            root_div = divs[SUPPLEMENTARY_TYPES[supplementary_type]]
            for amd_file in supplementary_files:
                if supplementary_files[amd_file] == supplementary_type:
                    add(root_div, [amd_file])
    else:
        # Directory based structure is like a directory tree
        for amd_file in filelist:
            # Do not add supplementary files to the directory based strictmap
            if amd_file not in supplementary_files:
                add(divs, amd_file.split('/'))
    return divs


def create_ead3_structmap(filegrp,
                          all_amd_refs,
                          all_dmd_refs,
                          dmdsec_loc,
                          structmap_type,
                          workspace,
                          object_refs,
                          file_properties,
                          supplementary_files=None,
                          supplementary_types=None):
    """Create structmap based on ead3 descriptive metadata structure.

    :param filegrp: fileGrp element
    :param all_amd_refs: XML element tree of administrative metadata
        references
    :param all_dmd_refs: XML element tree of descriptive metadata
        references
    :param dmdsec_loc: EAD3 descriptive metadata file
    :param structmap_type: TYPE attribute of structMap element
    :param workspace: Workspace path, required by ead3_c_div()
    :param object_refs: Object references.
    :param file_properties: Dictionary collection of file properties.
    :param supplementary_files: Supplementary files.
    :param supplementary_types: Supplementary types.
    :returns: Struct map XML element tree.
    """
    if supplementary_files is None:
        supplementary_files = {}
    if supplementary_types is None:
        supplementary_types = set()

    structmap = mets.structmap(type_attr=structmap_type)
    container_div = mets.div(type_attr='logical')

    root = ET.parse(dmdsec_loc).getroot()

    try:
        label = root.xpath(("//ead3:archdesc/@otherlevel | "
                            "//ead3:archdesc/@level"),
                           namespaces=NAMESPACES)[0]
    except IndexError:
        label = 'archdesc'

    amdids = get_md_references(all_amd_refs, directory='.')
    dmdids = get_md_references(all_dmd_refs, directory='.')

    div_ead = mets.div(type_attr='archdesc', label=label, dmdid=dmdids,
                       admid=amdids)

    if root.xpath("//ead3:archdesc/ead3:dsc", namespaces=NAMESPACES):
        for elem in root.xpath("//ead3:dsc/*", namespaces=NAMESPACES):
            if ET.QName(elem.tag).localname in ALLOWED_C_SUBS:
                ead3_c_div(parent=elem,
                           div=div_ead,
                           filegrp=filegrp,
                           all_amd_refs=all_amd_refs,
                           object_refs=object_refs,
                           supplementary_files=supplementary_files,
                           supplementary_types=supplementary_types,
                           file_properties=file_properties,
                           workspace=workspace)

    container_div.append(div_ead)
    structmap.append(container_div)
    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def ead3_c_div(parent,
               div,
               filegrp,
               all_amd_refs,
               object_refs,
               supplementary_files,
               supplementary_types,
               file_properties,
               workspace):
    """Create div elements based on ead3 c elements. Fptr elements are
    created based on ead dao elements. The Ead3 elements tags are put
    into @type and the @level or @otherlevel attributes from ead3 will
    be put into @label.

    Daoset elements within the ead3 c element will be looped over and
    create their own divs if they exist, containing the dao elements.

    :param parent: Element to follow in EAD3
    :param div: Div element in structmap
    :param filegrp: fileGrp element
    :param all_amd_refs: XML element tree of administrative metadata
        references.
    :param object_refs: Object references.
    :param supplementary_files: Supplementary files.
    :param supplementary_types: Supplementary types.
    :param file_properties: Dictionary collection of file properties.
    :param workspace: Workspace path, required by add_fptrs_div_ead()
    """

    c_div = mets.div(type_attr=(ET.QName(parent.tag).localname),
                     label=_parse_label(parent))

    # Create child divs based on the child c elements
    for elem in parent.findall("./*"):
        if ET.QName(elem.tag).localname in ALLOWED_C_SUBS:
            ead3_c_div(parent=elem,
                       div=c_div,
                       filegrp=filegrp,
                       all_amd_refs=all_amd_refs,
                       object_refs=object_refs,
                       supplementary_files=supplementary_files,
                       supplementary_types=supplementary_types,
                       file_properties=file_properties,
                       workspace=workspace)

    # Create divs for daoset elements, appending the dao elements and file
    # references to the daoset elements
    for elem in parent.xpath("./ead3:did/*", namespaces=NAMESPACES):
        if ET.QName(elem.tag).localname == 'daoset':
            daoset_div = mets.div(type_attr='daoset', label=_parse_label(elem))

            daoset_hrefs = collect_dao_hrefs(elem)
            daoset_div = add_fptrs_div_ead(
                c_div=daoset_div,
                hrefs=daoset_hrefs,
                filegrp=filegrp,
                all_amd_refs=all_amd_refs,
                object_refs=object_refs,
                file_properties=file_properties)
            c_div.append(daoset_div)

    # Collect dao elements and file references as fptr elements if they
    # exist directly under the ead3 c element
    c_hrefs = collect_dao_hrefs(parent)
    c_div = add_fptrs_div_ead(c_div=c_div,
                              hrefs=c_hrefs,
                              filegrp=filegrp,
                              all_amd_refs=all_amd_refs,
                              object_refs=object_refs,
                              file_properties=file_properties)

    div.append(c_div)


def _parse_label(elem):
    """Helper function to return the label attribute for a tag based
    on existing EAD3 attributes. If none of the exist, return the
    element name instead.

    :elem: lxml.etree element whose attributes (or name) is parsed
    :returns: The parsed label as a string
    """
    try:
        label = elem.xpath(("./@label | ./@otherlevel | ./@level"),
                           namespaces=NAMESPACES)[0]
    except IndexError:
        label = ET.QName(elem.tag).localname

    return label


def add_file_to_filesec(all_amd_refs,
                        object_refs,
                        path,
                        filegrp,
                        properties=None,
                        supplementary_type=None):
    """Add file element to fileGrp element given as parameter.

    If the file group is for content files, but the file has a
    supplementary property, a file element is not created and the file
    is not added to the fileSec.

    If the file group is for supplementary files, only supplementary
    files should be added to the fileSec.

    :param all_amd_refs: XML element tree of administrative metadata
        references.
    :param object_refs: XML tree of digital objects.
    :param path: url encoded path of the file
    :param filegrp: fileGrp element
    :param properties: Properties for single file.
    :param supplementary_type: Which supplementary type the files belong to.
    :returns: unique identifier of file element
    """
    fileid = '_{}'.format(uuid4())

    # Create list of IDs of amdID elements
    amdids = get_md_references(refs_dict=all_amd_refs, path=path)

    use = None
    if properties:
        if 'bit_level' in properties and properties["bit_level"] == "native":
            use = "no-file-format-validation"

        # Do not add supplementary files to normal file group and vice versa
        if all(('supplementary' in properties,
                properties['supplementary'],
                not supplementary_type)):
            return None
        elif all(('supplementary' in properties,
                  properties['supplementary'],
                  supplementary_type)):
            if not supplementary_type in properties['supplementary']:
                return None

    # Create XML element and add it to fileGrp
    file_el = mets.file_elem(
        fileid,
        admid_elements=set(amdids),
        loctype='URL',
        xlink_href='file://%s' % encode_path(path, safe='/'),
        xlink_type='simple',
        groupid=None,
        use=use
    )

    streams = get_objectlist(object_refs, path)
    if streams:
        for stream in streams:
            stream_ids = get_md_references(refs_dict=all_amd_refs,
                                           path=path,
                                           stream=stream)
            stream_el = mets.stream(admid_elements=stream_ids)
            file_el.append(stream_el)

    filegrp.append(file_el)

    return fileid


def get_fileid(filesec, path, file_ids=None):
    """Returns the ID for a file. Either finds a file with `path` from
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

    :param divs: Current directory or file in directory structure walkthrough
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


def add_file_div(fptr,
                 properties=None,
                 type_attr='file',
                 label=None):
    """Create a div element with file properties

    :param fptr: Element fptr for file
    :param properties: Properties of the given file.
    :param type_attr: The TYPE attribute value for the div
    :param label: The LABEL attribute value for the div.
    :returns: Div element with properties or None
    """

    if any((properties and 'order' in properties, label)):
        div_el = mets.div(type_attr=type_attr,
                          order=properties.get('order', None),
                          label=label)
        div_el.append(fptr)
        return div_el

    return None


def get_file_properties(path, all_amd_refs, workspace):
    """Return file properties from the json data file

    :param path: File path
    :param all_amd_refs: XML element tree of administrative metadata
        references.
    :param workspace: Workspace path
    :returns: A dict with properties or None
    """
    json_name = None
    for amdref in get_md_references(all_amd_refs, path=path):
        json_name = os.path.join(workspace,
                                 '{}-scraper.json'.format(amdref[1:]))
        if os.path.isfile(json_name):
            break

    if json_name is None or not os.path.isfile(json_name):
        return None
    file_metadata_dict = load_scraper_json(json_name)

    if 'properties' not in file_metadata_dict[0]:
        return None

    return file_metadata_dict[0]['properties']


def add_fptrs_div_ead(c_div,
                      hrefs,
                      filegrp,
                      all_amd_refs,
                      object_refs,
                      file_properties):
    """Creates fptr elements for hrefs. If the files contain
    file properties, like ordering data, the data is written to the
    parent div element.
    If file properties exist and the number of hrefs is more than one,
    the hrefs need to be split into own div elements since the ORDER
    attribute is at the div level.

    :param c_div: The div element as lxml.etree
    :param hrefs: a list of tuples (href, label)
    :param filegrp: fileGrp element
    :param all_amd_refs: XML element tree of administrative
        metadata references.
    :param object_refs: Object references.
    :param file_properties: Dictionary collection of file properties.
    :returns: The modified c_div element
    """

    for href, label in hrefs:
        amd_file = None
        for path in file_properties:
            if href in path:
                amd_file = path
                break
        # href strings that do not match any file don't add anything new
        if not amd_file:
            break

        properties = file_properties[amd_file]
        fileid = add_file_to_filesec(all_amd_refs=all_amd_refs,
                                     object_refs=object_refs,
                                     path=amd_file,
                                     filegrp=filegrp,
                                     properties=properties)
        if fileid:
            fptr = mets.fptr(fileid=fileid)

        if any((properties and 'order' in properties, label)):

            # Create new div elements for each fptr
            file_div = add_file_div(fptr=fptr,
                                    properties=properties,
                                    type_attr='dao',
                                    label=label)
            c_div.append(file_div)
        else:
            c_div.append(fptr)

    return c_div


def collect_dao_hrefs(parent):
    """Returns the href and label attribute values from ead3 dao elements.

    :parent: EAD3 element XML as lxml.etree structure containing dao
             children (can be either a c level or daoset element)
    :returns: A list of hrefs in tuple (href, label)
    """
    hrefs = []

    # The daos exist either directly under the parent element or within
    # the did element, depending on the parent tag
    xpath = './ead3:did/*'
    if ET.QName(parent.tag).localname == 'daoset':
        xpath = './*'

    for elem in parent.xpath("%s" % xpath, namespaces=NAMESPACES):
        if ET.QName(elem.tag).localname == 'dao':
            hrefs.append((elem.xpath("./@href")[0].lstrip('/'),
                          elem.get('label', None)))

    return hrefs


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

    event_datetime = datetime.datetime.now().isoformat()
    premis_event(event_type="creation",
                 event_datetime=event_datetime,
                 event_detail=("Creation of structural metadata with the "
                               "compile-structmap script"),
                 event_outcome="success",
                 event_outcome_detail=("Created METS structural map of type %s"
                                       % structmap_type),
                 workspace=workspace,
                 create_agent_file='compile-structmap-agents')


def iter_supplementary(file_properties):
    """Checks whether supplementary files exist in package and return
    the supplementary type if it exists.

    :param file_properties: Dictionary of file properties.
    :returns: A tuple of supplementary files (dict) and supplementary
        types (set).
    """
    supplementary_files = {}
    supplementary_types = set()
    for path in file_properties:
        properties = file_properties[path]
        try:
            supplementary_type = properties['supplementary'][0]
            supplementary_files[path] = supplementary_type
            supplementary_types.add(supplementary_type)
        except (TypeError, KeyError, IndexError):
            pass

    return supplementary_files, supplementary_types


def _create_filegrp(file_ids,
                    supplementary_files,
                    all_amd_refs,
                    object_refs,
                    file_properties,
                    supplementary_type=None):
    """Creates a mets fileGrp.

    :param file_ids: A dict of file paths and identifiers.
    :param supplementary_files: Supplementary files.
    :param all_amd_refs: XML element tree of administrative metadata
        references.
    :param object_refs: XML tree of digital objects.
    :param supplementary_files: ID list of supplementary objects. Will be
        populated if supplementary objects exist.
    :param file_properties: Dictionary collection of file properties.
    :param supplementary_type: Which supplementary type the files belong to.

    :returns: A tuple of METS XML Element tree including file group
              element and a dict of file paths and identifiers
    """
    use = None
    collection = file_properties

    if supplementary_type:
        use = SUPPLEMENTARY_TYPES[supplementary_type]
        collection = supplementary_files
    filegrp = mets.filegrp(use=use)

    for path in collection:
        fileid = add_file_to_filesec(all_amd_refs=all_amd_refs,
                                     object_refs=object_refs,
                                     path=path,
                                     filegrp=filegrp,
                                     supplementary_type=supplementary_type,
                                     properties=file_properties[path])
        if fileid:
            file_ids[path] = fileid
    return filegrp, file_ids


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
