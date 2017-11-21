""""Command line tool for compile structmap"""

import sys
import argparse
import os
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
    """ Create arguments parser and return parsed command line argumets"""

    parser = argparse.ArgumentParser(
        description="Tool for generating fileSec and structMap")
    parser.add_argument('--dmdsec_struct', dest='dmdsec_struct', type=str,
                        help=("Use structured descriptive metadata for "
                              "creating structMap divs"))
    parser.add_argument('--dmdsec_loc', dest='dmdsec_loc', type=str,
                        help="Location of  structured descriptive metadata")
    parser.add_argument('--workspace', type=str, default='./workspace/',
                        help="Destination file")
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for compile_sturctmap"""
    args = parse_arguments(arguments)

    structmap = mets.structmap()
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
        container_div = mets.div(type_attr='directory', dmdid=dmdsec_id, admid=amdids)
        structmap.append(container_div)
        divs = div_structure(args.workspace)
        create_structmap(args.workspace, divs, container_div, filegrp)

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
    """
    workspace_files = [fname.name for fname in scandir.scandir(workspace)]
    techmd_files = [x for x in workspace_files if 'techmd' in x]
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
                tech_file = encode_path(
                    files.xpath("./ead3:dao/@href", namespaces=NAMESPACES)[0])
            else:
                tech_file = encode_path(files.xpath("./@href")[0])
            amdids = get_links_event_agent(workspace, tech_file)
            fileid = add_file_to_filesec(workspace, tech_file, filegrp, amdids)
            dao = mets.fptr(fileid=fileid)
            c_div.append(dao)

    structmap.append(c_div)


def add_file_to_filesec(workspace, path, filegrp, amdids):
    """Add file element to fileSec.
    """
    othermd_types = ['addml', 'mix', 'videomd', 'audiomd', 'textmd']
    techmd_files, techmd_ids = ids_for_files(workspace, path, 'techmd.xml')
    fileid = '_' + str(uuid4())
    filepath = decode_path(techmd_files[0], '-techmd.xml')
    othermd_ids = []
    for mdtype in othermd_types:
        othermd_ids = read_temp_othermdfile(workspace, mdtype, filepath,
                othermd_ids)
    file_el = mets.file_elem(
        fileid, admid_elements=techmd_ids+amdids+othermd_ids, loctype='URL',
        xlink_href='file://%s' % filepath,
        xlink_type='simple', groupid=None)
    filegrp.append(file_el)
    return fileid


def read_temp_othermdfile(workspace, mdtype, path, othermd_ids):
    """Append id to othermd_ids if file exists in temporary
    othermd_types file.
    """
    mdfile = os.path.join(workspace, '%sfile.xml' % mdtype)

    if os.path.isfile(mdfile):
        import_mdfile= ET.parse(mdfile)
        root = import_mdfile.getroot()

        for fileid in root.findall('.//fileid'):
            if fileid.get('path') == path:
                othermd_ids.append(fileid.text)

    return othermd_ids


def get_links_event_agent(workspace, path):
    """Get link identifiers for events and agents
    """
    _, links_e = ids_for_files(workspace, path, 'event.xml', dash_count=1)
    _, links_a = ids_for_files(workspace, path, 'agent.xml', dash_count=1)
    return links_e + links_a


def create_structmap(workspace, divs, structmap, filegrp, path=''):
    """Create structmap based on directory structure
    """
    fptr_list = []
    div_list = []
    for div in divs.keys():
        # It's a file if there is "-techmd.xml", lets create file+fptr
        # elements
        if div.endswith('-techmd.xml'):
            div = div[:-len('-techmd.xml')]
            div_path = encode_path(os.path.join(decode_path(path), div))
            amdids = get_links_event_agent(workspace, div_path)
            fileid = add_file_to_filesec(workspace, div_path, filegrp, amdids)
            fptr = mets.fptr(fileid)
            fptr_list.append(fptr)
        # It's not a file, lets create a div element
        else:
            div_path = encode_path(os.path.join(decode_path(path), div))
            amdids = get_links_event_agent(workspace, div_path)
            _, dmdsec_id = ids_for_files(workspace, div_path, 'dmdsec.xml')
            div_el = mets.div(type_attr=div, dmdid=dmdsec_id, admid=amdids)
            div_list.append(div_el)

            create_structmap(workspace, divs[div], div_el, filegrp, div_path)

    # Add fptr list first, then div list
    for fptr_elem in fptr_list:
        structmap.append(fptr_elem)
    for div_elem in div_list:
        structmap.append(div_elem)


def ids_for_files(workspace, path, idtype, dash_count=0):
    """Get ids for metadata files
    """
    workspace_files = [fname.name for fname in scandir.scandir(workspace)]
    md_files = [x for x in workspace_files if idtype in x]
    if path:
        files_result = [x for x in md_files
                        if path in x and (path+'%2F') not in x]
    else:
        files_result = [x for x in md_files if x.count('-') == dash_count]
    id_result = [encode_id(x) for x in files_result]
    return files_result, id_result


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
