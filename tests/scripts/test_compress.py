"""
Test TAR packaging.
"""
from __future__ import unicode_literals

import os
import tarfile
import subprocess
import pytest
import siptools.scripts.compress


def test_compress(testpath, run_cli):
    """
    Test TAR packaging script.
    """
    dir_to_tar = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'structured'))
    output = os.path.join(testpath, 'sip.tar')
    arguments = [dir_to_tar, '--tar_filename', output]

    run_cli(siptools.scripts.compress.main, arguments)

    command = ['tar', '-xf', output, '-C', testpath]
    child = subprocess.Popen(command)
    child.communicate()
    assert child.returncode == 0


@pytest.mark.parametrize(("directory", "ending"), [
    ("structured", ".txt"),
    ("images", ".tif")
])
def test_exclude(testpath, run_cli, directory, ending):
    """
    Test excluding files. In test case 1 we have several txt files in various
    subdirectories. In test case 2 we have several tiff files in a single
    directory.
    """
    dir_to_tar = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', directory))
    output = os.path.join(testpath, 'sip.tar')

    # click.CliRunner interprets a single string argument as Unix command.
    # This is now needed (instead of an argument list) to test single quotes.
    arguments = "%s --tar_filename %s --exclude '*%s'" % (
        dir_to_tar, output, ending)

    run_cli(siptools.scripts.compress.main, arguments)

    count = 0
    for _, _, files in os.walk(dir_to_tar):
        for name in files:
            if name.endswith(ending):
                count += 1
    assert count > 1  # Make sure that we have multiple files to exclude

    # No excluded files present in TAR
    with tarfile.open(output) as tar:
        for name in tar.getnames():
            assert not name.endswith(ending)
