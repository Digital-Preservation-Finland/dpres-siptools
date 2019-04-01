"""Command line tool for creating tar file from SIP directory"""

import sys
import click
import subprocess


@click.command()
@click.argument('dir_to_tar', type=str)
@click.option(
    '--tar_filename', type=str, default='sip.tar',
    help="Filename for tar. Default is sip.tar")
def main(dir_to_tar, tar_filename):
    """The main method for compress"""
    command = 'cd %s' % dir_to_tar
    command2 = 'tar -cvvf %s *' % tar_filename
    proc = subprocess.Popen(
        '{}; {}'.format(command, command2), shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, close_fds=True)

    (out, err) = proc.communicate()
    returncode = proc.returncode

    print "created tar file: %s" % tar_filename

    return 0


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
