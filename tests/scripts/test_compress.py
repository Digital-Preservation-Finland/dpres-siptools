from tempfile import NamedTemporaryFile
import siptools.scripts.compress
import os
import pytest
import subprocess

def test_compress(testpath):

    output=os.path.join(testpath, 'sip.tar')
    dir_to_tar='tests/data/structured'
    arguments=[dir_to_tar, '--tar_filename', output]

    assert siptools.scripts.compress.main(arguments) == 0

    command = ['tar', '-xf', output, '-C', testpath]
    child = subprocess.Popen(command)
    streamdata = child.communicate()[0]
    assert child.returncode == 0
