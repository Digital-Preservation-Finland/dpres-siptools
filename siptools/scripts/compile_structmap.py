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
from siptools.utils import encode_id
from siptools.utils import decode_path

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
    create_structMap(structmap, args.workspace, filegrp, args.workspace, admids)

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
        dmdsec_id = [encode_id (id) for id in id_for_file(workspace, path, 
            'dmdsec.xml')]
        amdids = [encode_id(id) for id in id_for_file(workspace, path,
            'creation-event.xml')]
        amdids += [encode_id(id) for id in id_for_file(workspace, path,
            'creation-agent.xml')]
        div = m.div(type=os.path.basename(path), order=None, contentids=None,
                    label=None, orderlabel=None, dmdid=dmdsec_id,
                    admid=amdids, div_elements=None, fptr_elements=None,
                    mptr_elements=None)
        tree.append(div)
        for item in scandir.scandir(path):
            create_structMap(div, item.path, filegrp,
                             workspace, admids, dmdsec_id)
    else:
        techmd_id = [encode_id(id) for id in id_for_file(workspace, path,
            'techmd.xml')]
        if not techmd_id:
            return
        fileid = '_' + str(uuid4())
        filepath = decode_path(os.path.relpath(path, os.curdir))
	    # remove workspace and techmd.xml from path
        filepath =filepath[len(workspace)-1:-11]

        file = m.file(fileid, admid_elements=techmd_id, loctype='URL',
                   xlink_href='file://%s' % filepath, xlink_type='simple',
                   groupid=None)
        filegrp.append(file)
        fptr = m.fptr(fileid)
        tree.append(fptr)


def id_for_file(workspace, path, idtype):
    import scandir
    from siptools.utils import encode_path

    workspace_files = [fname.name for fname in scandir.scandir(workspace)]
    techmd_files = filter(lambda x: idtype in x, workspace_files)
    path = path.strip(workspace)
    ids = [id for id in techmd_files if path in id]

    return ids


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
