"""
Test TAR packaging.
"""
from __future__ import unicode_literals

import os
import tarfile
import subprocess
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


def test_exclude(testpath, run_cli):
    """
    Test excluding files.
    """
    dir_to_tar = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'structured'))
    output = os.path.join(testpath, 'sip.tar')

    # click.CliRunner interprets a single string argument as Unix command.
    # This is now needed (instead of an argument list) to test single quotes.
    arguments = "%s --tar_filename %s --exclude '*.txt'" % (
        dir_to_tar, output)

    run_cli(siptools.scripts.compress.main, arguments)

    count = 0
    for _, _, files in os.walk(dir_to_tar):
        for name in files:
            if name.endswith(".txt"):
                count += 1
    assert count > 1  # Make sure that we have multiple txt files

    # No txt files present in TAR
    with tarfile.open(output) as tar:
        for name in tar.getnames():
            assert not name.endswith(".txt")
