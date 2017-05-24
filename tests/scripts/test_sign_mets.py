from tempfile import NamedTemporaryFile 
import siptools.scripts.sign_mets
import os
import pytest
from shutil import copy

def test_valid_sign_mets(testpath):


    output=os.path.join(testpath, 'signature.sig')
    signing_key='tests/data/rsa-keys.crt'
    source='tests/data/text-file.txt'
    arguments=[source, output, signing_key]

    destination = os.path.join(testpath, os.path.dirname(source))
    if not os.path.exists(destination):
        os.makedirs(destination)

    copy(source, destination)
    assert siptools.scripts.sign_mets.main(arguments) == 0

    with open(output) as fd:
        assert "4ddd69b778405b4072d77762a85f9cf5e8e5ca83" in fd.read()
