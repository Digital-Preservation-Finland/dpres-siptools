"""Command line tool for creating tar file from SIP directory"""

import sys
import os
import argparse
import subprocess


def main(arguments=None):
    """The main method for compress"""
    args = parse_arguments(arguments)

    destination_tar = os.path.join(args.destination, args.tar_filename)
    command = ['tar', '-cvvf', destination_tar, args.dir_to_tar]
    subprocess.Popen(command, cwd=args.dir_to_tar)

    print "created tar file: %s" % destination_tar

    return 0

def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Create tar file from SIP directory.")
    parser.add_argument('dir_to_tar', help="SIP directory to be tarred.")
    parser.add_argument(
        '--tar_filename', dest='tar_filename', type=str, default='sip.tar',
        help="Filename for tar. Default is sip.tar")
    parser.add_argument(
        '--destination', dest='destination', type=str, default='./',
        help="Destination path of tar file. Default is the current directory.")

    return parser.parse_args(arguments)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
