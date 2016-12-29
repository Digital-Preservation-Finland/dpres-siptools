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


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""

    parser = argparse.ArgumentParser(description="Tool for importing files"
                                     "which generates digital objects")
    parser.add_argument('input_directory',
                        help="Input directory to create a structMap",
                        type=lambda x: is_valid_dir(parser, x))
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

    source_path = os.path.abspath(args.input_directory)
    mets_structmap = m.mets_mets()
    mets_filesec = m.mets_mets()

    structmap = m.structmap()
    filesec = m.filesec()
    filegrp = m.filegrp()
    filesec.append(filegrp)
    mets_filesec.append(filesec)
    mets_structmap.append(structmap)
    admids = []
    admids = get_digiprovmd_id(admids, args.workspace)
    create_structMap(structmap, source_path, filegrp, args.workspace, admids)

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


def create_structMap(tree, path, filegrp, workspace, admids, dmdsec_id=None):
    """create structMap and fileSec elements from directories and files"""
    if os.path.isdir(path):
        dmdsec_id = get_md_id(path, workspace, '/mets:mets/mets:dmdSec/@ID',
                              '-dmdsec.xml', dmdsec_id)
        techmd_mix_id = get_md_id(path, workspace,
                                  '/mets:mets/mets:techMD/@ID', '-mix-techmd.xml')
        if techmd_mix_id:
            admids.append(techmd_mix_id)
        div = m.div(type=os.path.basename(path), order=None, contentids=None,
                    label=None, orderlabel=None, dmdid=dmdsec_id,
                    amdid=None, div_elements=None, fptr_elements=None,
                    mptr_elements=None)
        tree.append(div)
        for item in scandir.scandir(path):
            create_structMap(div, item.path, filegrp,
                             workspace, admids, dmdsec_id)
        if techmd_mix_id:
            del admids[-1]
    else:
        techmd_id = get_md_id(
            path, workspace, '/mets:mets/mets:techMD/@ID', '-techmd.xml')
        techmd_mix_id = get_md_id(path, workspace,
                                  '/mets:mets/mets:techMD/@ID', '-mix-techmd.xml')
        admids.append(techmd_id)
        if techmd_mix_id:
            admids.append(techmd_mix_id)
        fileid = str(uuid4())
        file = m.file(fileid, admid_elements=admids, loctype='URL',
                      xlink_href='file://%s' % os.path.relpath(path, os.curdir), xlink_type='simple',
                      groupid=None)
        del admids[-1]
        if techmd_mix_id:
            del admids[-1]
        filegrp.append(file)
        fptr = m.fptr(fileid)
        tree.append(fptr)


def get_md_id(path, workspace, xpos, suffix='', md_id=None):

    relpath = os.path.relpath(path, os.curdir)
    url_path = quote_plus(os.path.splitext(relpath)[0]) + suffix
    md_path = os.path.join(workspace, url_path)
    if os.path.isfile(md_path):
        md_tree = ET.parse(md_path)
        md_root = md_tree.getroot()
        md_id = md_root.xpath(xpos,
                              namespaces=NAMESPACES)[0]
    return md_id


def get_digiprovmd_id(admids, workspace):
    for ETYPE in PREMIS_EVENT_TYPES:
        md_file = os.path.join(workspace, ETYPE + ".xml")
        if os.path.isfile(md_file):
            md_tree = ET.parse(md_file)
            md_root = md_tree.getroot()
            digiprovid = md_root.xpath(
                '/mets:mets/mets:amdSec/mets:digiprovMD[2]/@ID', namespaces=NAMESPACES)[0]
            admids.append(digiprovid)
    return admids


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
