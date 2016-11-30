from tempfile import NamedTemporaryFile 
import siptools.scripts.sign_mets
import os
import pytest

def test_valid_sign_mets(testpath):


    output=os.path.join(testpath, 'signature.sig')
    signing_key='tests/data/rsa-keys.crt'
    arguments=['tests/data/text-file.txt', output, signing_key]

    assert siptools.scripts.sign_mets.main(arguments) == 0

    with open(output) as fd:
        assert "4ddd69b778405b4072d77762a85f9cf5e8e5ca83" in fd.read()
