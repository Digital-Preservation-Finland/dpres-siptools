import os
import time
import subprocess
from click.testing import CliRunner
import siptools.scripts.compress


def test_compress(testpath):

    dir_to_tar = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'structured'))
    output = os.path.join(testpath, 'sip.tar')
    arguments = [dir_to_tar, '--tar_filename', output]

    runner = CliRunner()
    result = runner.invoke(siptools.scripts.compress.main, arguments)
    assert result.exit_code == 0

    time.sleep(2)
    command = ['tar', '-xf', output, '-C', testpath]
    child = subprocess.Popen(command)
    child.communicate()
    assert child.returncode == 0
