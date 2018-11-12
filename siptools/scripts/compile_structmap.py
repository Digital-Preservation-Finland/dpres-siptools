""""Command line tool for creating structure map and file metadata for a METS
document."""

import sys
import argparse
import os
import json
from uuid import uuid4
import scandir
import lxml.etree as ET
import mets
import xml_helpers.utils as h
from siptools.xml.mets import NAMESPACES
from siptools.utils import encode_id, encode_path, decode_path, tree, add


def ead3_ns(tag):
    """Get tag with EAD3 namespace
    """
    path = '{%s}%s' % ('http://ead3.archivists.org/schema/', tag)
    return path


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line argumets"""

    parser = argparse.ArgumentParser(
        description="Tool for generating METS fileSec and structMap based on "
                    "technical metada files (-premis-techmd.xml -suffix) and "
                    "descriptive metadata files (-dmdsec.xml -suffix) found "
                    "in workspace directory. Outputs two XML files: "
                    "filesec.xml and structmap.xml"
    )
    parser.add_argument('--dmdsec_struct', dest='dmdsec_struct', type=str,
                        help=("Use structured descriptive metadata for "
                              "creating structMap divs"))
    parser.add_argument('--dmdsec_loc', dest='dmdsec_loc', type=str,
                        help="Location of structured descriptive metadata")
    parser.add_argument('--type_attr', dest='type_attr', type=str,
                        help="Type of structmap e.g. 'Fairdata-physical'"
                             " or 'Directory-physical'")
    parser.add_argument('--root_type', dest='root_type', type=str,
                        help="Type of root div")
    parser.add_argument('--workspace', type=str, default='./workspace/',
                        help="Destination directory for output files.")
    parser.add_argument('--stdout', help='Print output also to stdout.')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for compile_structmap"""
    args = parse_arguments(arguments)

    structmap = mets.structmap(type_attr=args.type_attr)
    mets_structmap = mets.mets(child_elements=[structmap])

    filegrp = mets.filegrp()
    filesec = mets.filesec(child_elements=[filegrp])
    mets_filesec = mets.mets(child_elements=[filesec])

    _, dmdsec_id = ids_for_files(args.workspace, None, 'dmdsec.xml',
                                 dash_count=0)

    if args.dmdsec_struct == 'ead3':
        container_div = mets.div(type_attr='logical')
        structmap.append(container_div)
        create_ead3_structmap(args.dmdsec_loc, args.workspace, container_div,
                              filegrp, dmdsec_id)
    else:
        amdids = get_links_event_agent(args.workspace, None)

        if args.type_attr == 'Directory-physical':
            container_div = mets.div(type_attr='directory', label='.',
                                     dmdid=dmdsec_id, admid=amdids)
        else:
            root_type = args.root_type if args.root_type else 'directory'
            container_div = mets.div(type_attr=root_type, dmdid=dmdsec_id,
                                     admid=amdids)

        properties = {}
        property_path = os.path.join(args.workspace,
                                     'siptools-file-properties.txt')
        if os.path.isfile(property_path):
            with open(property_path) as infile:
                properties = json.load(infile)

        structmap.append(container_div)
        divs = div_structure(args.workspace)
        create_structmap(args.workspace, divs, container_div, filegrp,
                         properties=properties, type_attr=args.type_attr)

    if args.stdout:
        print h.serialize(mets_filesec)
        print h.serialize(mets_structmap)

    output_sm_file = os.path.join(args.workspace, 'structmap.xml')
    output_fs_file = os.path.join(args.workspace, 'filesec.xml')

    if not os.path.exists(os.path.dirname(output_sm_file)):
        os.makedirs(os.path.dirname(output_sm_file))

    if not os.path.exists(os.path.dirname(output_fs_file)):
        os.makedirs(os.path.dirname(output_fs_file))

    with open(output_sm_file, 'w+') as outfile:
        outfile.write(h.serialize(mets_structmap))

    with open(output_fs_file, 'w+') as outfile:
        outfile.write(h.serialize(mets_filesec))

    print "compile_structmap created files: %s %s" % (output_sm_file,
                                                      output_fs_file)

    return 0


def div_structure(workspace):
    """Create div structure for directory-based structmap

    :workspace (str): Path to directory
    :returns (defaultdict): Directory tree as a dict like object
    """
    workspace_files = [fname.name for fname in scandir.scandir(workspace)]
    techmd_files = [x for x in workspace_files if '-premis-techmd.xml' in x]
    divs = tree()
    for techmd_file in techmd_files:
        add(divs, decode_path(techmd_file).split('/'))
    return divs


def create_ead3_structmap(descfile, workspace, structmap, filegrp, dmdsec_id):
    """Create structmap based on ead3 descriptive metadata structure.
    """
    import_xml = ET.parse(descfile)
    root = import_xml.getroot()

    if root.xpath("//ead3:archdesc/@otherlevel", namespaces=NAMESPACES):
        level = root.xpath("//ead3:archdesc/@otherlevel",
                           namespaces=NAMESPACES)[0]
    else:
        level = root.xpath("//ead3:archdesc/@level",
                           namespaces=NAMESPACES)[0]
    amdids = get_links_event_agent(workspace, None)
    div_ead = mets.div(type_attr='archdesc', label=level, dmdid=dmdsec_id,
                       admid=amdids)

    if len(root.xpath("//ead3:archdesc/ead3:dsc", namespaces=NAMESPACES)) > 0:
        for ead3_c in root.xpath("//ead3:dsc/*", namespaces=NAMESPACES):
            if len(ET.QName(ead3_c.tag).localname) > 1:
                cnum = str(ET.QName(ead3_c.tag).localname)[-2:]
            else:
                cnum = None
            ead3_c_div(ead3_c, div_ead, filegrp, workspace, cnum=cnum)

    structmap.append(div_ead)


def ead3_c_div(parent, structmap, filegrp, workspace, cnum=None):
    """Create div elements based on ead3 c elements. Fptr elements are
    created based on ead dao elements. The Ead3 elements tags are put
    into @type and the @level or @otherlevel attributes from ead3 will
    be put into @label.
    """
    allowed_c_subs = ['c', 'c01', 'c02', 'c03', 'c04', 'c05', 'c06', 'c07',
                      'c08', 'c09', 'c10', 'c11', 'c12']

    if parent.xpath("./@otherlevel"):
        level = parent.xpath("./@otherlevel")[0]
    else:
        level = parent.xpath("./@level")[0]

    if cnum:
        c_div = mets.div(type_attr=('c' + str(cnum)), label=level)
        cnum_sub = str('0') + str(int(cnum) + 1)
    else:
        c_div = mets.div(type_attr='c', label=level)
        cnum_sub = None

    for elem in parent.findall("./*"):
        if ET.QName(elem.tag).localname in allowed_c_subs:
            ead3_c_div(elem, c_div, filegrp, workspace, cnum=cnum_sub)

    for files in parent.xpath("./ead3:did/*", namespaces=NAMESPACES):
        if ET.QName(files.tag).localname in ['dao', 'daoset']:
            if ET.QName(files.tag).localname == 'daoset':
                ead3_file = files.xpath(
                    "./ead3:dao/@href", namespaces=NAMESPACES)[0]
            else:
                ead3_file = files.xpath("./@href")[0]
            if ead3_file.startswith('/'):
                ead3_file = ead3_file[1:]
            tech_file = encode_path(ead3_file)
            amdids = get_links_event_agent(workspace, tech_file)
            fileid = add_file_to_filesec(workspace, tech_file, filegrp, amdids)
            dao = mets.fptr(fileid=fileid)
            c_div.append(dao)

    structmap.append(c_div)


def add_file_to_filesec(workspace, path, filegrp, amdids):
    """Add file element to fileSec element given as parameter.

    :workspace: Workspace directorye from which techMD files and techMD
                reference files searched.
    :path: url encoded path of the file
    :filegrp (lxml.etree.Element): fileSec element
    :amdids (list): list of administrative metadata associated with the file
    :returns (str): id of file added to fileSec
    """
    techmd_files, techmd_ids = ids_for_files(workspace, path,
                                             '-premis-techmd.xml')
    fileid = '_' + str(uuid4())
    # TODO When calling encode(decode(string)) you should get the original
    # string back, but this does something else (also). Should be refactored.
    # -vvainio 26.06.2018
    filepath = encode_path(decode_path(techmd_files[0], '-premis-techmd.xml'),
                           safe='/')

    # Create list of IDs of techmD elements that contain othermd metadata
    othermd_ids = get_techmd_references(workspace, decode_path(path))

    # Create XML element and add it to fileSec
    file_el = mets.file_elem(
        fileid,
        admid_elements=techmd_ids+amdids+othermd_ids,
        loctype='URL',
        xlink_href='file://%s' % filepath,
        xlink_type='simple',
        groupid=None
    )
    filegrp.append(file_el)

    return fileid


def get_techmd_references(workspace, path):
    """If techMD reference file exists in workspace, read the techMD IDs that
    should be referenced by a file.

    :workspace (str): path to directory from which othermd
    :path (str): path of the file for which the IDs are read
    :returns (list): list of techMD IDs
    """
    reference_file = os.path.join(workspace, 'techmd-references.xml')
    techmd_ids = []

    if os.path.isfile(reference_file):
        element_tree = ET.parse(reference_file)
        reference_elements = element_tree.xpath(
            '/techmdReferences/techmdReference[@file="%s"]' % path
        )
        techmd_ids = [element.text for element in reference_elements]

    return techmd_ids


def get_links_event_agent(workspace, path):
    """Get link identifiers for events and agents
    """
    _, links_e = ids_for_files(workspace, path, 'event.xml', dash_count=1)
    _, links_a = ids_for_files(workspace, path, 'agent.xml', dash_count=1)
    return links_e + links_a


def create_structmap(workspace, divs, parent, filegrp, path='',
                     properties={}, type_attr=None):
    """Create structmap based on directory structure and fileSec
    :workspace: Workspace path
    :divs: Current directory or file in directory structure walkthrough
    :parent: Parent element in structMap
    :filegrp: filegrp element in fileSec
    :path: Current path in directory structure walkthrough
    :properties: Properties of files created in import_object.py
    :type_attr: Structmap type
    """
    fptr_list = []
    property_list = []
    div_list = []
    for div in divs.keys():
        # It's a file if there is "-techmd.xml", lets create file+fptr
        # elements
        if div.endswith('-premis-techmd.xml'):
            div = div[:-len('-premis-techmd.xml')]
            div_path = encode_path(os.path.join(decode_path(path), div))
            amdids = get_links_event_agent(workspace, div_path)
            fileid = add_file_to_filesec(workspace, div_path, filegrp, amdids)
            fptr = mets.fptr(fileid)
            div_el = add_file_properties(properties, div_path, fptr)
            if div_el:
                property_list.append(div_el)
            else:
                fptr_list.append(fptr)

        # It's not a file, lets create a div element
        else:
            div_path = encode_path(os.path.join(decode_path(path), div))
            amdids = get_links_event_agent(workspace, div_path)
            _, dmdsec_id = ids_for_files(workspace, div_path, 'dmdsec.xml')
            if type_attr == 'Directory-physical':
                div_el = mets.div(type_attr='directory', label=div,
                                  dmdid=dmdsec_id, admid=amdids)
            else:
                div_el = mets.div(type_attr=div, dmdid=dmdsec_id,
                                  admid=amdids)
            div_list.append(div_el)
            create_structmap(workspace, divs[div], div_el, filegrp, div_path,
                             properties, type_attr)

    # Add fptr list first, then div list
    for fptr_elem in fptr_list:
        parent.append(fptr_elem)
    for div_elem in property_list:
        parent.append(div_elem)
    for div_elem in div_list:
        parent.append(div_elem)


def add_file_properties(properties, path, fptr):
    """Create a div element with file properties
    :properties: File properties
    :path: File path
    :fptr: Element fptr for file
    :returns: Div element with properties or None
    """
    if path in properties:
        file_properties = properties[path]
        if 'order' in file_properties:
            div_el = mets.div(type_attr='file',
                              order=file_properties['order'])
            div_el.append(fptr)
            return div_el
    return None


def ids_for_files(workspace, path, idtype, dash_count=0):
    """Search files in workspace based on keywords or number of dashes in
    filename, and create ID for each found file.

    :workspace (str): Path to directory from which the files are searched
    :path (str): If not None, False, or 0, only return filenames that contain
                 this word
    :idtype (str): Only return filenames that contain this word
    :dash_count (int): If path is None, False, or 0, return filenames that have
                       this many dashes
    :returns (list, list): List of found files and list of Ids of files
    """
    # Find all files from workspace directory and filter out filenames that do
    # not contain idtype
    workspace_filenames = [fname.name for fname in scandir.scandir(workspace)]
    md_files = [x for x in workspace_filenames if idtype in x]

    if path:
        # Filter filenames based on path
        files_result = [x for x in md_files
                        if path in x and (path+'%2F') not in x]
    else:
        # Filter filenames based on number of '-'-characters in filename
        files_result = [x for x in md_files if x.count('-') == dash_count]

    # Create IDs for files
    id_result = [encode_id(x) for x in files_result]

    return files_result, id_result


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
