"""Command line tool for creating tar file from SIP directory"""

import sys
import os
import argparse
import subprocess


def main(arguments=None):
    """The main method for compress"""
    args = parse_arguments(arguments)

    command = 'cd %s' % args.dir_to_tar
    command2 = 'tar -cvvf %s *' % args.tar_filename
    proc = subprocess.Popen(
        '{}; {}'.format(command,command2), shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, close_fds=True)

    (out, err) = proc.communicate()
    returncode = proc.returncode

    print "created tar file: %s" % args.tar_filename

    return 0

def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Create tar file from SIP directory.")
    parser.add_argument('dir_to_tar', help="SIP directory to be tarred.")
    parser.add_argument(
        '--tar_filename', dest='tar_filename', type=str, default='sip.tar',
        help="Filename for tar. Default is sip.tar")

    return parser.parse_args(arguments)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
