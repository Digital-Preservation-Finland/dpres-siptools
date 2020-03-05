"""Tests for ``siptools.scripts.sign_mets`` module"""
from __future__ import unicode_literals

import io
import os
import shutil
import siptools.scripts.sign_mets


def test_valid_sign_mets(testpath, run_cli):
    """
    Test signing the SIP.
    """
    output = os.path.join(testpath, 'signature.sig')
    signing_key = 'tests/data/rsa-keys.crt'
    arguments = ['--workspace', testpath, signing_key]

    # Create mets file in workspace
    mets = os.path.join(testpath, 'mets.xml')
    mets_source = 'tests/data/text-file.txt'
    shutil.copy(mets_source, mets)

    run_cli(siptools.scripts.sign_mets.main, arguments)

    with io.open(output, "rt") as open_file:
        assert "4ddd69b778405b4072d77762a85f9cf5e8e5ca83" in open_file.read()
