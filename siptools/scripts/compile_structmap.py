""""Command line tool for compile structmap"""

import argparse
import os
import siptools.xml.mets as m
import scandir
from uuid import uuid4


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
    mets = m._element('mets')
    # Tama pitaa lisata mets_mets-funktioon, kunhan TPAS-9 on mergattu
    # developpiin
    mets.set('xmlns:' + 'xlink', 'http://www.w3.org/1999/xlink')
    structmap = m.structmap()
    filesec = m.filesec()
    filegrp = m.filegrp()
    filesec.append(filegrp)
    mets.append(filesec)
    mets.append(structmap)
    create_structMap(structmap, source_path, filegrp)

    if args.stdout:
        print m.serialize(mets)

    output_file = os.path.join(args.workspace, 'mets.xml')

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(m.serialize(mets))

    return 0


def create_structMap(tree, path, filegrp):
    """create structMap and fileSec elements from directories and files"""
    if os.path.isdir(path):
        div = m.div(type=os.path.basename(path), order=None, contentids=None,
                    label=None, orderlabel=None, dmdid=None,
                    amdid=None, div_elements=None, fptr_elements=None,
                    mptr_elements=None)
        tree.append(div)
        for item in scandir.scandir(path):
            create_structMap(div, item.path, filegrp)
    else:
        fileid = str(uuid4())
        file = m.file(fileid, admid=str(uuid4()), loctype='URL',
                      xlink_href='file://%s' % os.path.relpath(path, os.curdir), xlink_type='simple',
                      groupid=None)
        filegrp.append(file)
        fptr = m.fptr(fileid)
        tree.append(fptr)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
