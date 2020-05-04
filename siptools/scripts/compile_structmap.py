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
from siptools.mdcreator import (get_objectlist, read_all_amd_references,
                                get_md_references)
from siptools.scripts.create_agent import create_agent
from siptools.scripts.premis_event import premis_event
from siptools.utils import add, encode_path, tree, load_scraper_json, \
    read_md_references
from siptools.xml.mets import NAMESPACES

import siptools

click.disable_unicode_literals_warning = True

ALLOWED_C_SUBS = ['c', 'c01', 'c02', 'c03', 'c04', 'c05', 'c06', 'c07',
                  'c08', 'c09', 'c10', 'c11', 'c12']


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
def main(**kwargs):
    """Tool for generating METS file section and structural map based on
    created/imported administrative metada and descriptive metadata.
    The script will also add order of the file to the structural map
    (via json file), if --order argument was used in import_object script.
    """
    compile_structmap(**kwargs)

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


def get_reference_lists(**attributes):
    """
    Fill the attributes with various lists.

    :attributes: The following keys:
                 workspace: Workspace path
                 object_refs: XML tree of digital objects.
                              Will be created if missing.
                 filelist: ID list of objects. Will be created if missing.
                 all_amd_refs: All administrative metadata references.
                               Will be created if missing.
                 all_dmd_refs: All descriptive metadata references.
                               Will be created if missing.
    :returns: Attributes filled with the lists listed above.
    """
    attributes["object_refs"] = attributes.get(
        "object_refs", read_md_references(
            attributes["workspace"], "import-object-md-references.jsonl"
        ))
    attributes["filelist"] = attributes.get(
        "filelist", get_objectlist(attributes["object_refs"]))
    attributes["all_amd_refs"] = attributes.get(
        "all_amd_refs", read_all_amd_references(attributes["workspace"]))
    attributes["all_dmd_refs"] = attributes.get(
        "all_dmd_refs", read_md_references(
            attributes["workspace"], "import-description-md-references.jsonl"
        ))

    return attributes


def compile_structmap(**kwargs):
    """Generate METS file section and structural map based on
    created/imported administrative metada and descriptive metadata.

    :kwargs: Given arguments:
             workspace: Workspace directory
             structmap_type: Type of structmap
             root_type: Type of root div
             dmdsec_loc: Location of structured descriptive metadata
             file_ids: Dict to be populated with file paths and IDs
             stdout: True to print output to stdout
    """
    attributes = _attribute_values(kwargs)

    # Create an event documenting the structmap creation
    _create_event(
        workspace=attributes["workspace"],
        structmap_type=attributes["structmap_type"],
        root_type=attributes["root_type"]
    )

    # Get reference list only after the structmap creation event
    attributes = get_reference_lists(**attributes)

    if attributes["structmap_type"] == 'EAD3-logical':
        # If structured descriptive metadata for structMap divs is used, also
        # the fileSec element (apparently?) is different. The
        # create_ead3_structmap function populates the fileGrp element.
        filegrp = mets.filegrp()
        filesec_element = mets.filesec(child_elements=[filegrp])
        filesec = mets.mets(child_elements=[filesec_element])

        structmap = create_ead3_structmap(filegrp, attributes)
    else:
        (filesec, file_ids) = create_filesec(**attributes)

        # Add file path and ID dict to attributes
        attributes['file_ids'] = file_ids
        structmap = create_structmap(filesec.getroot(), **attributes)

    if attributes["stdout"]:
        print(xml_utils.serialize(filesec).decode("utf-8"))
        print(xml_utils.serialize(structmap).decode("utf-8"))

    output_sm_file = os.path.join(attributes["workspace"], 'structmap.xml')
    output_fs_file = os.path.join(attributes["workspace"], 'filesec.xml')

    if not os.path.exists(os.path.dirname(output_sm_file)):
        os.makedirs(os.path.dirname(output_sm_file))

    if not os.path.exists(os.path.dirname(output_fs_file)):
        os.makedirs(os.path.dirname(output_fs_file))

    with open(output_sm_file, 'wb+') as outfile:
        outfile.write(xml_utils.serialize(structmap))

    with open(output_fs_file, 'wb+') as outfile:
        outfile.write(xml_utils.serialize(filesec))

    print("compile_structmap created files: %s %s" % (output_sm_file,
                                                      output_fs_file))


def create_filesec(**attributes):
    """
    Creates METS document element tree that contains fileSec element.

    :attributes: Attribute values as a dict
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 filelist: Sorted list of digital objects (file paths)
    :returns: A tuple of METS XML Element tree including file section
              element and a dict of file paths and identifiers
    """
    attributes = get_reference_lists(**_attribute_values(attributes))
    filegrp = mets.filegrp()
    filesec = mets.filesec(child_elements=[filegrp])

    file_ids = {}
    for path in attributes["filelist"]:
        fileid = add_file_to_filesec(attributes["all_amd_refs"],
                                     attributes["object_refs"], path, filegrp)
        file_ids[path] = fileid

    mets_element = mets.mets(child_elements=[filesec])
    ET.cleanup_namespaces(mets_element)
    return (ET.ElementTree(mets_element), file_ids)


def create_structmap(filesec, **attributes):
    """
    Creates METS document element tree that contains structural map.

    :filesec: fileSec element
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 all_dmd_refs: XML element tree of descriptive metadata
                               references
                 filelist: Sorted list of digital objects (file paths)
                 structmap_type: TYPE attribute of structMap element
                 root_type: TYPE attribute of root div element
                 file_ids: Dict with file paths and identifiers
                 workspace: Workspace path
    :returns: structural map element
    """
    attributes = get_reference_lists(**_attribute_values(attributes))
    amdids = get_md_references(attributes["all_amd_refs"], directory='.')
    dmdids = get_md_references(attributes["all_dmd_refs"], directory='.')

    if attributes["structmap_type"] == 'Directory-physical':
        container_div = mets.div(type_attr='directory', label='.',
                                 dmdid=dmdids, admid=amdids)
    else:
        container_div = mets.div(type_attr=attributes["root_type"],
                                 dmdid=dmdids,
                                 admid=amdids)

    structmap = mets.structmap(type_attr=attributes["structmap_type"])
    structmap.append(container_div)
    divs = div_structure(attributes["filelist"])
    create_div(divs, container_div, filesec, attributes)

    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def div_structure(filelist):
    """Create div structure for directory-based structmap

    :filelist: Sorted list of digital objects (file paths)
    :returns: Directory tree as a dict like object
    """
    divs = tree()
    for amd_file in filelist:
        add(divs, amd_file.split('/'))
    return divs


def create_ead3_structmap(filegrp, attributes):
    """Create structmap based on ead3 descriptive metadata structure.

    :filegrp: fileGrp element
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 all_dmd_refs: XML element tree of descriptive metadata
                               references
                 filelist: Sorted list of digital objects (file paths)
                 dmdsec_loc: EAD3 descriptive metadata file
                 structmap_type: TYPE attribute of structMap element
                 workspace: Workspace path
    """
    structmap = mets.structmap(type_attr=attributes["structmap_type"])
    container_div = mets.div(type_attr='logical')

    root = ET.parse(attributes["dmdsec_loc"]).getroot()

    try:
        label = root.xpath(("//ead3:archdesc/@otherlevel | "
                            "//ead3:archdesc/@level"),
                           namespaces=NAMESPACES)[0]
    except IndexError:
        label = 'archdesc'

    amdids = get_md_references(attributes["all_amd_refs"], directory='.')
    dmdids = get_md_references(attributes["all_dmd_refs"], directory='.')

    div_ead = mets.div(type_attr='archdesc', label=label, dmdid=dmdids,
                       admid=amdids)

    if len(root.xpath("//ead3:archdesc/ead3:dsc", namespaces=NAMESPACES)) > 0:
        for elem in root.xpath("//ead3:dsc/*", namespaces=NAMESPACES):
            if ET.QName(elem.tag).localname in ALLOWED_C_SUBS:
                ead3_c_div(elem, div_ead, filegrp, attributes)

    container_div.append(div_ead)
    structmap.append(container_div)
    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def ead3_c_div(parent, div, filegrp, attributes):
    """Create div elements based on ead3 c elements. Fptr elements are
    created based on ead dao elements. The Ead3 elements tags are put
    into @type and the @level or @otherlevel attributes from ead3 will
    be put into @label.

    :parent: Element to follow in EAD3
    :div: Div element in structmap
    :filegrp: fileGrp element
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 filelist: Sorted list of digital objects (file paths)
                 workspace: Workspace path
    """

    try:
        label = parent.xpath(("./@otherlevel | ./@level"),
                             namespaces=NAMESPACES)[0]
    except IndexError:
        label = ET.QName(parent.tag).localname

    c_div = mets.div(type_attr=(ET.QName(parent.tag).localname), label=label)

    for elem in parent.findall("./*"):
        if ET.QName(elem.tag).localname in ALLOWED_C_SUBS:
            ead3_c_div(elem, c_div, filegrp, attributes)

    hrefs = collect_dao_hrefs(parent)
    c_div = add_fptrs_div_ead(c_div=c_div, hrefs=hrefs, filegrp=filegrp,
                              attributes=attributes)

    div.append(c_div)


def add_file_to_filesec(all_amd_refs, object_refs, path, filegrp):
    """Add file element to fileGrp element given as parameter.

    :all_amd_refs: XML element tree of administrative metadata references
    :object_refs: XML tree of object references
    :path: url encoded path of the file
    :filegrp: fileGrp element
    :returns: unique identifier of file element
    """
    fileid = '_{}'.format(uuid4())

    # Create list of IDs of amdID elements
    amdids = get_md_references(all_amd_refs, path=path)

    # Create XML element and add it to fileGrp
    file_el = mets.file_elem(
        fileid,
        admid_elements=set(amdids),
        loctype='URL',
        xlink_href='file://%s' % encode_path(path, safe='/'),
        xlink_type='simple',
        groupid=None
    )

    streams = get_objectlist(object_refs, path)
    if streams:
        for stream in streams:
            stream_ids = get_md_references(
                all_amd_refs, path=path, stream=stream)
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
def create_div(divs, parent, filesec, attributes, path=''):
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
                 type_attr: Structmap type
                 file_ids: Dict with file paths and identifiers
                 workspace: Workspace path
    :path: Current path in directory structure walkthrough
    :returns: ``None``
    """
    fptr_list = []
    property_list = []
    div_list = []
    for div in divs.keys():
        div_path = os.path.join(path, div)
        # It's a file, lets create file+fptr elements
        if div_path in attributes["filelist"]:
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


def add_file_div(path, fptr, attributes, type_attr='file'):
    """Create a div element with file properties

    :path: File path
    :fptr: Element fptr for file
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 workspace: Workspace path
    :type_attr: The TYPE attribute value for the div

    :returns: Div element with properties or None
    """

    properties = file_properties(path, attributes)
    if properties and 'order' in properties:
        div_el = mets.div(type_attr=type_attr,
                          order=properties['order'])
        div_el.append(fptr)
        return div_el

    return None


def file_properties(path, attributes):
    """Return file properties from the json data file

    :path: File path
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 workspace: Workspace path
    :returns: A dict with properties or None
    """

    json_name = None
    for amdref in get_md_references(attributes["all_amd_refs"], path=path):
        json_name = os.path.join(
            attributes["workspace"], '{}-scraper.json'.format(amdref[1:]))
        if os.path.isfile(json_name):
            break

    if json_name is None or not os.path.isfile(json_name):
        return None
    file_metadata_dict = load_scraper_json(json_name)

    if 'properties' not in file_metadata_dict[0]:
        return None

    return file_metadata_dict[0]['properties']


def add_fptrs_div_ead(c_div, hrefs, filegrp, attributes):
    """Creates fptr elements for hrefs. If the files contain
    file properties, like ordering data, the data is written to the
    parent div element.
    If file properties exist and the number of hrefs is more than one,
    the hrefs need to be split into own div elements since the ORDER
    attribute is at the div level.

    :c_div: The div element as lxml.etree
    :hrefs: a list of hrefs
    :filegrp: fileGrp element
    :attributes: The following keys:
                 all_amd_refs: XML element tree of administrative metadata
                               references
                 filelist: Sorted list of digital objects (file paths)
                 workspace: Workspace path
    :returns: The modified c_div element
    """
    for href in hrefs:
        amd_file = [x for x in attributes["filelist"] if href in x]

        # href strings that do not match any file don't add anything new
        if not amd_file:
            break
        amd_file = amd_file[0]
        properties = file_properties(amd_file, attributes)
        fileid = add_file_to_filesec(attributes["all_amd_refs"],
                                     attributes["object_refs"],
                                     amd_file,
                                     filegrp)
        fptr = mets.fptr(fileid=fileid)

        if properties and 'order' in properties:

            # Create new div elements for each fptr if there is more than
            # one file, otherwise add the ORDER attribute to the current
            # div element
            if len(hrefs) > 1:
                file_div = add_file_div(amd_file, fptr, attributes,
                                        type_attr='dao')
                c_div.append(file_div)
            else:
                c_div.attrib['ORDER'] = properties['order']
                c_div.append(fptr)
        else:
            c_div.append(fptr)

    return c_div


def collect_dao_hrefs(ead3_c):
    """Returns the href attribute values from ead3 dao elements.

    :ead3_c: EAD3 c level element XML as lxml.etree structure
    :returns: A list of hrefs
    """
    hrefs = []
    for elem in ead3_c.xpath("./ead3:did/*", namespaces=NAMESPACES):
        if ET.QName(elem.tag).localname in ['dao', 'daoset']:
            if ET.QName(elem.tag).localname == 'daoset':
                for dao_href in elem.xpath(
                        "./ead3:dao/@href",
                        namespaces=NAMESPACES):
                    hrefs.append(dao_href.lstrip('/'))
            else:
                hrefs.append(elem.xpath("./@href")[0].lstrip('/'))

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
                 event_outcome_detail=(
                     "Created METS structural map of type %s"
                     % structmap_type),
                 workspace=workspace,
                 create_agent_file='compile-structmap-agents')


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
