"""
Test TAR packaging.
"""
from __future__ import unicode_literals

import os
import time
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

    time.sleep(2)
    command = ['tar', '-xf', output, '-C', testpath]
    child = subprocess.Popen(command)
    child.communicate()
    assert child.returncode == 0


def test_exclude(testpath, run_cli):
    """
    Test excluding files.
    """
    dir_to_tar = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'single'))
    output = os.path.join(testpath, 'sip.tar')
    arguments = [dir_to_tar, '--tar_filename', output,
                 '--exclude', '*.txt']

    run_cli(siptools.scripts.compress.main, arguments)

    time.sleep(2)
    command = ['tar', '-xf', output, '-C', testpath]
    child = subprocess.Popen(command)
    child.communicate()
    assert os.path.isfile(os.path.join(dir_to_tar, "text-file.txt"))
    assert not os.path.isfile(os.path.join(testpath, "text-file.txt"))
