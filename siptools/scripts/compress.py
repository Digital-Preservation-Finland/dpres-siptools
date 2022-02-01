"""Command line tool for creating tar file from SIP directory"""
from __future__ import unicode_literals, print_function

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
@click.option(
    '--exclude', type=str, default=None,
    metavar='<FILE PATTERN>',
    help="Pattern for files to be excluded from the package.")
def main(dir_to_tar, tar_filename, exclude):
    """Create tar file from SIP directory.

    DIR_TO_TAR: Directory to be added in the TAR file.
    """
    return compress(dir_to_tar, tar_filename, exclude)


def compress(dir_to_tar, tar_filename, exclude=None):
    """
    Create tar file from SIP directory.

    :dir_to_tar: Directory to pack in tar package
    :tar_filename: File name of the tar file
    ::
    """
    if exclude is None:
        command = ['tar', '-cvvf', fsencode_path(tar_filename), '.']
    else:
        command = ['tar', '--exclude=%s' % exclude, '-cvvf',
                   fsencode_path(tar_filename), '.']

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
