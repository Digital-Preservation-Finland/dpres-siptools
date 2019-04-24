"""Command line tool for creating tar file from SIP directory"""

import sys
import subprocess
import click


@click.command()
@click.argument('dir_to_tar', type=click.Path(exists=True))
@click.option(
    '--tar_filename', type=str, default='sip.tar',
    metavar='<TAR FILE>',
    help="Filename for tar. Default is sip.tar")
def main(dir_to_tar, tar_filename):
    """Create tar file from SIP directory.

    DIR_TO_TAR: Directory to be added in the TAR file.
    """
    return compress(dir_to_tar, tar_filename)


def compress(dir_to_tar, tar_filename):
    """Create tar file from SIP directory."""
    command = 'cd %s' % dir_to_tar
    command2 = 'tar -cvvf %s *' % tar_filename
    proc = subprocess.Popen(
        '{}; {}'.format(command, command2), shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, close_fds=True)

    proc.communicate()
    returncode = proc.returncode

    print "created tar file: %s" % tar_filename

    return returncode


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
