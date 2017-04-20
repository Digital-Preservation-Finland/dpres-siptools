"""Command line tool for creating tar file from SIP directory"""

import sys
import os
import argparse
import subprocess
from shutil import copyfile
from scandir import scandir
from siptools.utils import decode_path


def main(arguments=None):
    """The main method for compress"""
    args = parse_arguments(arguments)

    if args.copy_files:
        copy_files(args.dir_to_tar)

    command = ['tar', '-cvvf', args.tar_filename, args.dir_to_tar]
    subprocess.Popen(command)

    print "created tar file: %s" % args.tar_filename

    return 0


def copy_files(workspace):
    """Copy digital objects to tar directory
    """
    for entry in scandir(workspace):
        if entry.name.endswith('-techmd.xml') and entry.is_file():
            source = decode_path(entry.name, '-techmd.xml')
            target = os.path.join(workspace, source)
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            copyfile(source, target)


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Create tar file from SIP directory.")
    parser.add_argument("dir_to_tar", help="SIP directory to be tarred.")
    parser.add_argument("--tar_filename", default="sip.tar",
                        help="Filename for tar. Default is sip.tar")
    parser.add_argument("--copy_files", action='store_true',
                        help="Copy files based on techmd-urlpaths")

    return parser.parse_args(arguments)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
