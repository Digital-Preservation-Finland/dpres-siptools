import os
import time
import subprocess
import pytest
import siptools.scripts.compress

def test_compress(testpath):

    dir_to_tar = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'structured'))
    output = os.path.join(testpath, 'sip.tar')
    arguments = [dir_to_tar, '--tar_filename', output]

    assert siptools.scripts.compress.main(arguments) == 0

    time.sleep(2)
    command = ['tar', '-xf', output, '-C', testpath]
    child = subprocess.Popen(command)
    streamdata = child.communicate()[0]
    assert child.returncode == 0
