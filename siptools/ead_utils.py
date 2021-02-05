""""Utility functions for EAD3 structmap creation."""
from __future__ import unicode_literals, print_function

import lxml.etree as ET
import mets
from siptools.utils import (add_file_div,
                            add_file_to_filesec,
                            create_filegrp,
                            get_md_references)
from siptools.xml.mets import NAMESPACES


ALLOWED_C_SUBS = ['c', 'c01', 'c02', 'c03', 'c04', 'c05', 'c06', 'c07',
                  'c08', 'c09', 'c10', 'c11', 'c12']


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def compile_ead3_structmap(dmdsec_loc,
                           workspace,
                           all_amd_refs,
                           all_dmd_refs,
                           object_refs,
                           file_properties,
                           supplementary_files,
                           supplementary_types):
    """The function creates a METS structMap and fileSec section
    based on EAD3 metadata structure and the files listed in the
    EAD3 metadata.
    """
    file_ids = {}
    filegrp = mets.filegrp()
    filesec_child_elems = [filegrp]

    structmap = _create_structmap(
        filegrp=filegrp,
        all_amd_refs=all_amd_refs,
        all_dmd_refs=all_dmd_refs,
        dmdsec_loc=dmdsec_loc,
        structmap_type='EAD3-logical',
        workspace=workspace,
        object_refs=object_refs,
        file_properties=file_properties,
        supplementary_files=supplementary_files,
        supplementary_types=supplementary_types)

    for supplementary_type in supplementary_types:
        (s_filegrp, file_ids) = create_filegrp(
            file_ids=file_ids,
            supplementary_files=supplementary_files,
            all_amd_refs=all_amd_refs,
            object_refs=object_refs,
            file_properties=file_properties,
            supplementary_type=supplementary_type)
        filesec_child_elems.append(s_filegrp)

    filesec_element = mets.filesec(child_elements=filesec_child_elems)
    filesec = mets.mets(child_elements=[filesec_element])

    return structmap, filesec, file_ids


# pylint: disable=too-many-arguments
def _create_structmap(filegrp,
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
    :param workspace: Workspace path, required by _ead3_c_div()
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
                _ead3_c_div(parent=elem,
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


def _ead3_c_div(parent,
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
            _ead3_c_div(parent=elem,
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
