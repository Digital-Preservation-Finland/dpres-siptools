from __future__ import unicode_literals

import os
import time
import subprocess
import siptools.scripts.compress


def test_compress(testpath, run_cli):

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
