"""Command line tool for creating tar file from SIP directory"""
from __future__ import unicode_literals

import sys
import subprocess
import click

from siptools.utils import fsencode_path


click.disable_unicode_literals_warning = True


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
    command = ['tar', '-cvvf', fsencode_path(tar_filename), '.']
    proc = subprocess.Popen(
        command, cwd=dir_to_tar,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, close_fds=True
    )

    proc.communicate()
    returncode = proc.returncode

    print("created tar file: %s" % tar_filename)

    return returncode


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
