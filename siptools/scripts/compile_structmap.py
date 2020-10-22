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
from siptools.utils import add, encode_path, tree, load_scraper_json, \
    read_md_references, get_objectlist, read_all_amd_references, \
    get_md_references
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


def ead3_ns(tag):
    """Get tag with EAD3 namespace
    """
    path = '{%s}%s' % ('http://ead3.archivists.org/schema/', tag)
    return path


@click.command()
@click.option('--workspace',
              type=click.Path(exists=True), default='./workspace/',
              metavar='<WORKSPACE PATH>',
              help="Workspace directory. Defaults to ./workspace/")
@click.option('--structmap_type',
              type=str,
              metavar='<STRUCTMAP TYPE>',
              help="Type of structmap e.g. 'Fairdata-physical', "
                   "'EAD3-logical', or 'Directory-physical'")
@click.option('--root_type',
              metavar='<ROOT TYPE>',
              type=str, help="Type of root div")
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

    :param workspace: Workspace directory. Defaults to ./workspace/.
    :param structmap_type: Type of structmap e.g. 'Fairdata-physical',
        'EAD3-logical', or 'Directory-physical'.
    :param root_type: Type of root div.
    :param dmdsec_loc: Location of structured descriptive metadata, if
        applicable.
    :param stdout: Whether or not to print output also to stdout.
    """
    compile_structmap(workspace=workspace,
                      structmap_type=structmap_type,
                      root_type=root_type,
                      dmdsec_loc=dmdsec_loc,
                      stdout=stdout)

    return 0


def _attribute_values(given_params):
    """
    Give attribute values as a dict for the script.

    :given_params: Arguments as dict.
    :returns: Attribute value dict
    """
    attributes = {
        "workspace": "./workspace/",
        "root_type": "directory",
        "structmap_type": None,
        "dmdsec_loc": None,
        "file_ids": {},
        "stdout": False,
    }
    for key in given_params:
        if given_params[key]:
            attributes[key] = given_params[key]

    return attributes


def zget_reference_lists(**attributes):
    """
    Fill the attributes with various lists.

    :attributes: The following keys:
                 workspace: Workspace path
                 object_refs: XML tree of digital objects.
                              Will be created if missing.
                 filelist: ID list of objects. Will be created if missing.
                 supplementary_files: ID list of supplementary objects.
                                      Will be populated if supplementary
                                      objects exist.
                 all_amd_refs: All administrative metadata references.
                               Will be created if missing.
                 all_dmd_refs: All descriptive metadata references.
                               Will be created if missing.
                 supplementary_types A set of supplementary_types
    :returns: Attributes filled with the lists listed above.
    """
    attributes["object_refs"] = attributes.get(
        "object_refs", read_md_references(
            attributes["workspace"], "import-object-md-references.jsonl"
        ))
    attributes["filelist"] = attributes.get(
        "filelist", get_objectlist(attributes["object_refs"]))
    attributes["supplementary_files"] = attributes.get(
        "supplementary_files", {})
    attributes["all_amd_refs"] = attributes.get(
        "all_amd_refs", read_all_amd_references(attributes["workspace"]))
    attributes["all_dmd_refs"] = attributes.get(
        "all_dmd_refs", read_md_references(
            attributes["workspace"], "import-description-md-references.jsonl"
        ))
    attributes["supplementary_types"] = attributes.get(
        "supplementary_types", set())

    return attributes


def get_reference_lists(workspace):
    """
    Fill the attributes with various lists.

    :param workspace: Workspace path
    :param object_refs: XML tree of digital objects. Will be created if
        missing.
    :param filelist: ID list of objects. Will be created if missing.
    :param supplementary_files: ID list of supplementary objects.
        Will be populated if supplementary objects exist.
    :param all_amd_refs: All administrative metadata references. Will be
        created if missing.
    :param all_dmd_refs: All descriptive metadata references. Will be created
        if missing.
    :param supplementary_types: A set of supplementary_types
    :returns: Attributes filled with the lists listed above.
    """
    object_refs = read_md_references(workspace,
                                     "import-object-md-references.jsonl")
    filelist = get_objectlist(object_refs)
    supplementary_files = {}
    all_amd_refs = read_all_amd_references(workspace)
    all_dmd_refs = read_md_references(workspace,
                                      "import-description-md-references.jsonl")
    supplementary_types = set()

    return (object_refs,
            filelist,
            supplementary_files,
            all_amd_refs,
            all_dmd_refs,
            supplementary_types)


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
    file_ids_z = {}

    # Create an event documenting the structmap creation
    _create_event(
        workspace=workspace,
        structmap_type=structmap_type,
        root_type=root_type
    )

    # Get reference list only after the structmap creation event
    (object_refs,
     filelist,
     supplementary_files,
     all_amd_refs,
     all_dmd_refs,
     supplementary_types) = get_reference_lists(workspace=workspace)

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
            filelist=filelist,
            dmdsec_loc=dmdsec_loc,
            structmap_type=structmap_type,
            workspace=workspace,
            object_refs=object_refs,
            supplementary_files=supplementary_files,
            supplementary_types=supplementary_types)

        (supplementary_files, supplementary_types) = _iter_supplementary(
            **attributes)
        attributes['supplementary_files'] = supplementary_files
        attributes['supplementary_types'] = supplementary_types

        if supplementary_types:
            file_ids = {}
            for supplementary_type in supplementary_types:
                (s_filegrp, file_ids) = _create_filegrp(
                    file_ids,
                    attributes,
                    supplementary_type=supplementary_type)
            filesec_child_elems.append(s_filegrp)

        filesec_element = mets.filesec(child_elements=filesec_child_elems)
        filesec = mets.mets(child_elements=[filesec_element])

        if supplementary_types:
            structmap_type = 'logical'
            root_type = SUPPLEMENTARY_TYPES['main']
            suppl_structmap = create_structmap(filesec, **attributes)
    else:
        (filesec,
         file_ids,
         supplementary_files,
         supplementary_types) = create_filesec(**attributes)

        # Add file path and ID dict to attributes
        file_ids_z = file_ids
        attributes['supplementary_files'] = supplementary_files
        attributes['supplementary_types'] = supplementary_types
        structmap = create_structmap(filesec.getroot(), **attributes)

        # Create a separate structmap for supplementary files if they exist
        if attributes['supplementary_files']:
            structmap_type = 'logical'
            root_type = SUPPLEMENTARY_TYPES['main']
            suppl_structmap = create_structmap(filesec.getroot(), **attributes)

    if stdout:
        print(xml_utils.serialize(filesec).decode("utf-8"))
        print(xml_utils.serialize(structmap).decode("utf-8"))
        if attributes['supplementary_files']:
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

    if attributes['supplementary_files']:
        output_suppl_sm_file = os.path.join(workspace,
                                            'supplementary_structmap.xml')
        if not os.path.exists(os.path.dirname(output_suppl_sm_file)):
            os.makedirs(os.path.dirname(output_suppl_sm_file))
        with open(output_suppl_sm_file, 'wb+') as outfile:
            outfile.write(xml_utils.serialize(suppl_structmap))
        created_files.append(output_suppl_sm_file)

    print("compile_structmap created files: " + " ".join(created_files))


def create_filesec(**attributes):
    """
    Creates METS document element tree that contains fileSec element.

    Supplementary files are put in a separate fileGrp and will populate
    the supplementary_files attribute when they are discovered.

    :attributes: Attribute values as a dict
                 all_amd_refs: XML element tree of administrative metadata
                               references. Will be created if missing.
                 object_refs: XML tree of digital objects. Will be created
                              if missing.
                 filelist: Sorted list of digital objects (file paths).
                           Will be created if missing.
                 supplementary_files: ID list of supplementary objects.
                                      Will be populated if supplementary
                                      objects exist.
    :returns: A tuple of METS XML Element tree including file section
              element and a dict of file paths and identifiers
    """
    attributes = get_reference_lists(**_attribute_values(attributes))
    child_elements = []
    file_ids = {}
    (filegrp, file_ids) = _create_filegrp(file_ids, attributes)
    child_elements.append(filegrp)

    # Create file group for supplementary files if they exist
    for supplementary_type in attributes['supplementary_types']:
        (s_filegrp, file_ids) = _create_filegrp(
            file_ids,
            attributes,
            supplementary_type=supplementary_type)
        child_elements.append(s_filegrp)

    filesec = mets.filesec(child_elements=child_elements)
    mets_element = mets.mets(child_elements=[filesec])
    ET.cleanup_namespaces(mets_element)
    return (ET.ElementTree(mets_element),
            file_ids,
            attributes['supplementary_files'],
            attributes['supplementary_types'])


def create_structmap(filesec, **attributes):
    """
    Creates METS document element tree that contains structural map.

    :filesec: fileSec element
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references. Will be created if missing.
                 all_dmd_refs: XML element tree of descriptive metadata
                               references. Will be created if missing.
                 filelist: Sorted list of digital objects (file paths).
                           Will be created if missing.
                 supplementary_files: ID list of supplementary objects.
                                      Will be populated if supplementary
                                      objects exist.
                 structmap_type: TYPE attribute of structMap element
                                 If missing, default value is None.
                 root_type: TYPE attribute of root div element.
                            If missing, default value is "directory".
                 file_ids: Dict with file paths and identifiers.
                           Required by create_div(). Will be computed
                           if missing.
                 workspace: Workspace path, required by create_div().
                            If missing, default value is "./workspace/".
    :returns: structural map element
    """
    attributes = get_reference_lists(**_attribute_values(attributes))
    amdids = get_md_references(attributes["all_amd_refs"], directory='.')
    dmdids = get_md_references(attributes["all_dmd_refs"], directory='.')

    is_supplementary = False
    if attributes["structmap_type"] == 'Directory-physical':
        container_div = mets.div(type_attr='directory', label='.',
                                 dmdid=dmdids, admid=amdids)
    elif attributes["root_type"] == SUPPLEMENTARY_TYPES['main']:
        is_supplementary = True
        container_div = mets.div(type_attr=attributes["root_type"],
                                 dmdid=None,
                                 admid=None)
    else:
        container_div = mets.div(type_attr=attributes["root_type"],
                                 dmdid=dmdids,
                                 admid=amdids)

    structmap = mets.structmap(type_attr=attributes["structmap_type"])
    structmap.append(container_div)

    divs = div_structure(attributes, is_supplementary)
    create_div(divs,
               container_div,
               filesec,
               attributes,
               is_supplementary=is_supplementary)

    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def div_structure(attributes, is_supplementary):
    """Create div structure for either a directory-based structmap
    or for supplementary files.

    :filelist: Sorted list of digital objects (file paths)
    :supplementary_files: Sorted list of supplementary objects
                          (file paths)
    :is_supplementary: Boolean to indicate whether the structure
                       should be for supplemenjtary files or not
    :returns: The div structure as a dict like object
    """
    divs = tree()
    if is_supplementary:
        for supplementary_type in attributes["supplementary_types"]:
            # Supplementary structure is flat, but with one div surrounding the
            # files
            root_div = divs[SUPPLEMENTARY_TYPES[supplementary_type]]
            for amd_file in attributes["supplementary_files"]:
                if attributes[
                    "supplementary_files"][amd_file] == supplementary_type:
                    add(root_div, [amd_file])
    else:
        # Directory based structure is like a directory tree
        for amd_file in attributes["filelist"]:
            # Do not add supplementary files to the directory based strictmap
            if amd_file not in attributes["supplementary_files"]:
                add(divs, amd_file.split('/'))
    return divs


def create_ead3_structmap(filegrp,
                          all_amd_refs,
                          all_dmd_refs,
                          filelist,
                          dmdsec_loc,
                          structmap_type,
                          workspace,
                          object_refs,
                          supplementary_files,
                          supplementary_types):
    """Create structmap based on ead3 descriptive metadata structure.

    :param filegrp: fileGrp element
    :param all_amd_refs: XML element tree of administrative metadata
        references
    :param all_dmd_refs: XML element tree of descriptive metadata
        references
    :param filelist: Sorted list of digital objects (file paths)
    :param dmdsec_loc: EAD3 descriptive metadata file
    :param structmap_type: TYPE attribute of structMap element
    :param workspace: Workspace path, required by ead3_c_div()
    :param object_refs: Object references.
    :param supplementary_files: Supplementary files.
    :param supplementary_types: Supplementary types.
    """
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
                           filelist=filelist,
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
               filelist,
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
    :param filelist: Sorted list of digital objects (file paths)
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
                       filelist=filelist,
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
                supplementary_files=supplementary_files,
                supplementary_types=supplementary_types,
                filelist=filelist,
                workspace=workspace)
            c_div.append(daoset_div)

    # Collect dao elements and file references as fptr elements if they
    # exist directly under the ead3 c element
    c_hrefs = collect_dao_hrefs(parent)
    c_div = add_fptrs_div_ead(c_div=c_div,
                              hrefs=c_hrefs,
                              filegrp=filegrp,
                              all_amd_refs=all_amd_refs,
                              object_refs=object_refs,
                              supplementary_files=supplementary_files,
                              supplementary_types=supplementary_types,
                              filelist=filelist,
                              workspace=workspace)

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
                        supplementary_files,
                        workspace,
                        supplementary_types,
                        path,
                        filegrp,
                        supplementary_type=None):
    """Add file element to fileGrp element given as parameter.

    If the file group is for content files, but the file has a
    supplementary property, a file element is not created and the file
    is not added to the fileSec. Rather, the attribute value
    supplementary_files is populated with the file's path.

    If the file group is for supplementary files, only supplementary
    files should be added to the fileSec.

    :param all_amd_refs: XML element tree of administrative metadata
        references.
    :param object_refs: XML tree of digital objects.
    :param supplementary_files: ID list of supplementary objects. Will be
        populated if supplementary objects exist.
    :param workspace: Workspace path, required by file_properties()
    :param supplementary_types: Set of supplementary types.
    :param path: url encoded path of the file
    :param filegrp: fileGrp element
    :param is_supplementary: A boolean True to indicate if a supplementary file
        is expected, otherwise None.
    :returns: unique identifier of file element
    """
    fileid = '_{}'.format(uuid4())

    # Create list of IDs of amdID elements
    amdids = get_md_references(refs_dict=all_amd_refs, path=path)

    use = None
    properties = file_properties(path=path,
                                 all_amd_refs=all_amd_refs,
                                 workspace=workspace)
    if properties:
        if 'bit_level' in properties and properties["bit_level"] == "native":
            use = "no-file-format-validation"

        # Do not add supplementary files to normal file group and vice versa,
        # but rather populate the supplementary_files attribute with
        # supplementary files when encountered
        if all(('supplementary' in properties,
                properties['supplementary'],
                not supplementary_type)):
            supplementary_files[path] = properties['supplementary'][0]
            supplementary_types.add(properties['supplementary'][0])
            return None
        elif all(('supplementary' in properties,
                  properties['supplementary'],
                  supplementary_type)):
            is_match = False
            for supplementary_property in properties['supplementary']:
                if supplementary_property == supplementary_type:
                    is_match = True
            if not is_match:
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
               attributes,
               path='',
               is_supplementary=False):
    """Recursively create fileSec and structmap divs based on directory
    structure.

    :divs: Current directory or file in directory structure walkthrough
    :parent: Parent element in structMap
    :filesec: filesec element
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 all_dmd_refs: XML element tree of descriptive metadata
                               references
                 filelist: Sorted list of digital objects (file paths)
                 supplementary_files: ID list of supplementary objects.
                                      Will be populated if supplementary
                                      objects exist.
                 type_attr: Structmap type
                 file_ids: Dict with file paths and identifiers
                 workspace: Workspace path, required by add_file_div()
    :path: Current path in directory structure walkthrough
    :is_supplementary: A boolean to indicate if a supplementary
                       structure is expected or not
    :returns: ``None``
    """
    fptr_list = []
    property_list = []
    div_list = []
    filelist = attributes["filelist"]
    for div in divs.keys():
        div_path = os.path.join(path, div)
        if is_supplementary:
            filelist = attributes["supplementary_files"]
            # Remove supplementary root div from current div path
            supplementary_type = div_path.split('/')[0]
            div_path = div_path[len(supplementary_type) + 1:]
        # It's a file, lets create file+fptr elements
        if div_path in filelist:
            fptr = mets.fptr(
                get_fileid(filesec, div_path, attributes['file_ids']))
            div_elem = add_file_div(div_path, fptr, attributes)
            if div_elem is not None:
                property_list.append(div_elem)
            else:
                fptr_list.append(fptr)

        # It's not a file, lets create a div element
        else:
            amdids = get_md_references(
                attributes["all_amd_refs"], directory=div_path)
            dmdsec_id = get_md_references(
                attributes["all_dmd_refs"], directory=div_path)

            if attributes["structmap_type"] == 'Directory-physical':
                div_elem = mets.div(type_attr='directory', label=div,
                                    dmdid=dmdsec_id, admid=amdids)
            else:
                div_elem = mets.div(type_attr=div, dmdid=dmdsec_id,
                                    admid=amdids)
            div_list.append(div_elem)
            create_div(divs[div], div_elem, filesec, attributes, div_path)

    # Add fptr list first, then div list
    for fptr in fptr_list:
        parent.append(fptr)
    for div_elem in property_list:
        parent.append(div_elem)
    for div_elem in div_list:
        parent.append(div_elem)


def add_file_div(path,
                 fptr,
                 all_amd_refs,
                 workspace,
                 type_attr='file',
                 label=None):
    """Create a div element with file properties

    :param path: File path
    :param fptr: Element fptr for file
    :param all_amd_refs: XML element tree of administrative metadata
        references.
    :param workspace: Workspace path, required by file_properties()
    :param type_attr: The TYPE attribute value for the div
    :param label: The LABEL attribute value for the div.
    :returns: Div element with properties or None
    """

    properties = file_properties(path=path,
                                 all_amd_refs=all_amd_refs,
                                 workspace=workspace)
    if any((properties and 'order' in properties, label)):
        div_el = mets.div(type_attr=type_attr,
                          order=properties.get('order', None),
                          label=label)
        div_el.append(fptr)
        return div_el

    return None


def file_properties(path, all_amd_refs, workspace):
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
                      supplementary_files,
                      supplementary_types,
                      filelist,
                      workspace):
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
    :param supplementary_files: Set of supplementary files.
    :param supplementary_types: Supplementary types.
    :param filelist: Sorted list of digital objects (file paths)
    :param workspace: Workspace path, required by file_properties()
    :returns: The modified c_div element
    """
    for href, label in hrefs:
        amd_file = [x for x in filelist if href in x]

        # href strings that do not match any file don't add anything new
        if not amd_file:
            break
        amd_file = amd_file[0]
        properties = file_properties(path=amd_file,
                                     all_amd_refs=all_amd_refs,
                                     workspace=workspace)
        fileid = add_file_to_filesec(all_amd_refs=all_amd_refs,
                                     object_refs=object_refs,
                                     supplementary_files=supplementary_files,
                                     workspace=workspace,
                                     supplementary_types=supplementary_types,
                                     path=amd_file,
                                     filegrp=filegrp)
        if fileid:
            fptr = mets.fptr(fileid=fileid)

        if any((properties and 'order' in properties, label)):

            # Create new div elements for each fptr
            file_div = add_file_div(path=amd_file,
                                    fptr=fptr,
                                    all_amd_refs=all_amd_refs,
                                    workspace=workspace,
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


def _iter_supplementary(**attributes):
    """Checks whether supplementary files exist in package and return
    the supplementary type if it exists.
    Also populates the supplementary_files attribute while looping
    through th files.
    """
    attributes = get_reference_lists(**_attribute_values(attributes))
    supplementary_type = None
    for path in attributes['filelist']:
        properties = file_properties(path, attributes)
        if properties and 'supplementary' in properties:
            if properties['supplementary']:
                supplementary_type = properties['supplementary'][0]
                attributes['supplementary_files'][path] = supplementary_type
                attributes['supplementary_types'].add(supplementary_type)
    return (attributes['supplementary_files'],
            attributes['supplementary_types'])


def _create_filegrp(file_ids, attributes, supplementary_type=None):
    """Creates a mets fileGrp.

    :file_ids: A dict of file paths and identifiers
    :filelist: A list of file paths
    is_supplementary: A boolean of whether the created file group
                      consists of supplementary files or not

    :returns: A tuple of METS XML Element tree including file group
              element and a dict of file paths and identifiers
    """
    use = None
    filelist = attributes['filelist']
    if supplementary_type:
        use = SUPPLEMENTARY_TYPES[supplementary_type]
        filelist = attributes['supplementary_files']
    filegrp = mets.filegrp(use=use)
    for path in filelist:
        fileid = add_file_to_filesec(attributes,
                                     path,
                                     filegrp,
                                     supplementary_type=supplementary_type)
        if fileid:
            file_ids[path] = fileid
    return filegrp, file_ids


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
