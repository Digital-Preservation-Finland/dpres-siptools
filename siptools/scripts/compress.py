"""Command line tool for creating tar file from SIP directory"""

import sys
import os
import argparse
import subprocess

def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    command = ['tar', '-cvvf', args.tar_filename, args.dir_to_tar]
    subprocess.Popen(command)

    print "created tar file: %s" % args.tar_filename

    return 0


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="Create tar "
            "file from SIP directory.")

    parser.add_argument("dir_to_tar", help="SIP directory to be tarred.")
    parser.add_argument("--tar_filename", default="sip.tar", 
            help="Filename for tar. Default is sip.tar")

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
