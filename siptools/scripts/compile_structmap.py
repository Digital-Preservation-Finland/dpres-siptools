""""Command line tool for compile structmap"""

import sys
import argparse
import os
import siptools.xml.mets as m
import scandir
from uuid import uuid4
from urllib import quote_plus
import lxml.etree as ET
from siptools.xml.namespaces import NAMESPACES, METS_PROFILE
from siptools.xml.premis_event_types import PREMIS_EVENT_TYPES
from siptools.utils import encode_id, decode_path, tree, add

def ead3_ns(tag):

    EAD3_NS = 'http://ead3.archivists.org/schema/'

    path = '{%s}%s' % (EAD3_NS, tag)

    return path

def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""

    parser = argparse.ArgumentParser(description="Tool for importing files"
                                     "which generates digital objects")
    parser.add_argument('input_directory',
                        help="Input directory to create a structMap",
                        type=lambda x: is_valid_dir(parser, x))
    parser.add_argument('--dmdsec_struct', dest='dmdsec_struct',type=str,
                        help=("Use structured descriptive metadata for "
						"creating structMap divs"))
    parser.add_argument('--dmdsec_loc', dest='dmdsec_loc',type=str,
                        help="Location of  structured descriptive metadata")
    parser.add_argument('--workspace', type=str, default='./workspace/',
                        help="Destination file")
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def is_valid_dir(parser, arg):
    """Check if directory exists"""
    if not os.path.exists(os.path.abspath(arg)):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    mets_structmap = m.mets_mets()
    mets_filesec = m.mets_mets()

    structmap = m.structmap()
    filesec = m.filesec()
    filegrp = m.filegrp()
    filesec.append(filegrp)
    mets_filesec.append(filesec)
    mets_structmap.append(structmap)
    container_div = m.div(type='directory')
    structmap.append(container_div)

    if args.dmdsec_struct == 'ead3':
        divs = div_ead_structure(args.dmdsec_loc, container_div)
    else:
        divs = div_structure(args.workspace)
        create_structmap(args.workspace, divs, container_div, filegrp)

    if args.stdout:
        print m.serialize(mets)

    output_sm_file = os.path.join(args.workspace, 'structmap.xml')
    output_fs_file = os.path.join(args.workspace, 'filesec.xml')

    if not os.path.exists(os.path.dirname(output_sm_file)):
        os.makedirs(os.path.dirname(output_sm_file))

    if not os.path.exists(os.path.dirname(output_fs_file)):
        os.makedirs(os.path.dirname(output_fs_file))

    with open(output_sm_file, 'w+') as outfile:
        outfile.write(m.serialize(mets_structmap))

    with open(output_fs_file, 'w+') as outfile:
        outfile.write(m.serialize(mets_filesec))

    print "compile_structmap created files: %s %s" % (output_sm_file, output_fs_file)

    return 0


def div_structure(workspace):
    workspace_files = [fname.name for fname in scandir.scandir(workspace)]
    techmd_files = filter(lambda x: 'techmd' in x, workspace_files)

    divs = tree()
    for techmd_file in techmd_files:
        add(divs, decode_path(techmd_file, '-techmd.xml').split('/'),
                decode_path(techmd_file, '-techmd.xml'))
    return divs

def div_ead_structure(descfile, structmap):

    import_xml = ET.parse(descfile)
    root = import_xml.getroot()

    if root.xpath("//ead3:archdesc/@otherlevel", namespaces=NAMESPACES):
        level = root.xpath("//ead3:archdesc/@otherlevel",
                namespaces=NAMESPACES)[0]
    else:
        level = root.xpath("//ead3:archdesc/@level",
                namespaces=NAMESPACES)[0]

    div_ead = m.div(type='archdesc', label=level)

    if len(root.xpath("//ead3:archdesc/ead3:dsc", namespaces=NAMESPACES)) > 0:
        for c in root.xpath("//ead3:dsc/*", namespaces=NAMESPACES):
            if len(ET.QName(c.tag).localname) > 1:
				cnum = str(ET.QName(c.tag).localname)[-2:]
            else:
                cnum = None
            ead3_c = ead3_c_div(c, div_ead, cnum=cnum)

    structmap.append(div_ead)

def ead3_c_div(parent, structmap, cnum=None):

    allowed_c_subs = ['c', 'c01', 'c02', 'c03', 'c04', 'c05', 'c06', 'c07',
            'c08', 'c09', 'c10', 'c11', 'c12']

    if cnum:
        c = 'c' + str(cnum)
    else:
        c = 'c'

    if parent.xpath("./@otherlevel"):
        level = parent.xpath("./@otherlevel")[0]
    else:
        level = parent.xpath("./@level")[0]

    c_div = m.div(type=c, label=level)

    if cnum:
        cnum_sub = str('0') + str(int(cnum) + 1)

    for elem in parent.findall("./*"):
        tag = ET.QName(elem.tag).localname
        if tag in allowed_c_subs:
            if cnum:
                ead3_c_div(elem, c_div, cnum=cnum_sub)
            else:
                ead3_c_div(elem, c_div)

    for files in parent.xpath("./ead3:did/*", namespaces=NAMESPACES):
        tag = ET.QName(files.tag).localname
        if tag == 'dao' or tag == 'daoset':
            dao = m.fptr(fileid='test')
            c_div.append(dao)

    structmap.append(c_div)

def create_structmap(workspace, divs, structmap, filegrp):

    for div in divs.keys():
        # It's a file if there is file extension, lets create file+fptr
        # elements
        if os.path.splitext(div)[1]:

            techmd_files = id_for_file(workspace, div, 'techmd.xml')
            techmd_id = [encode_id(id) for id in techmd_files]
            fileid = '_' + str(uuid4())
            filepath = decode_path(os.path.relpath(div, os.curdir))

            amdids = [encode_id(id) for id in id_for_file(workspace, div,
                'creation-event.xml')]
            amdids += [encode_id(id) for id in id_for_file(workspace, div,
                'creation-agent.xml')]
            file = m.file(fileid, admid_elements=techmd_id+amdids, loctype='URL',
                       xlink_href='file://%s' % decode_path(techmd_files[0],
                           '-techmd.xml'), xlink_type='simple',
                       groupid=None)
            filegrp.append(file)
            fptr = m.fptr(fileid)
            structmap.append(fptr)

        # Skip divs with invalid type
        #elif div not in m.DIV_TYPES:
        #    create_structmap(workspace, divs[div], structmap, filegrp)
        # It's not a file, lets create a div element
        else:
            dmdsec_id = [encode_id (id) for id in id_for_file(workspace, div,
                'dmdsec.xml')]
            div_el = m.div(type=div, dmdid=dmdsec_id)
            structmap.append(div_el)

            create_structmap(workspace, divs[div], div_el, filegrp)

def id_for_file(workspace, path, idtype):

    workspace_files = [fname.name for fname in scandir.scandir(workspace)]
    techmd_files = filter(lambda x: idtype in x, workspace_files)
    path = path.strip(workspace)
    ids = [id for id in techmd_files if path in id]

    return ids

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
