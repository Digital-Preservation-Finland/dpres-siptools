""" Test"""
from __future__ import unicode_literals

import os
import sys

import pytest

import lxml.etree as ET
from siptools.scripts import import_description
from siptools.scripts.import_description import main
from siptools.utils import fsdecode_path


try:
    from urllib import quote_plus
except ImportError:  # Python 3
    from urllib.parse import quote_plus


def get_md_file(path, input_target):
    """Get id"""
    ref = os.path.join(path, 'md-references.xml')

    root = ET.parse(ref).getroot()
    amdref = root.xpath("/mdReferences/mdReference"
                        "[@directory='%s']" % fsdecode_path(input_target))[0]
    output = os.path.join(path, amdref.text[1:] +
                          "-dmdsec.xml")
    return output


def test_import_description_valid_file(testpath, run_cli):
    """ Test case for single valid xml-file"""
    dmdsec_location = 'tests/data/import_description/metadata/' \
        'dc_description.xml'
    dmdsec_target = 'tests/data/structured'

    run_cli(main, [
        dmdsec_location, '--dmdsec_target', dmdsec_target,
        '--workspace', testpath, '--remove_root'])
    output = get_md_file(testpath, dmdsec_target)

    output_path = os.path.join(testpath, output)
    tree = ET.parse(output_path)
    root = tree.getroot()
    assert len(root.xpath('./*/*/*/*')) == 4
    assert root.xpath('./*/*/*/*')[0].tag == \
        '{http://purl.org/dc/elements/1.1/}title'


@pytest.mark.parametrize((
    'base_path', 'dmdsec_target', 'dmd_target'), [
        # No base_path
        ('.', 'tests/data/structured', 'tests/data/structured'),
        # No base_path or dmdsec_target, target is package root
        ('.', None, '.'),
        # No dmdsec_target, target is still package root
        ('tests/data', None, '.'),
        # Target is a directory
        ('tests/data/', 'structured', 'structured'),
        ])
def test_dmd_target_path(base_path, dmdsec_target, dmd_target):
    """Tests the dmd_target_path function."""
    out_target = import_description.dmd_target_path(
        base_path, dmdsec_target)

    assert out_target == dmd_target


def test_invalid_dmd_target_path():
    """Tests that event_target_path raises IOError if given
    event_target path doesn't exist.
    """
    with pytest.raises(IOError):
        import_description.dmd_target_path('.', 'foo/bar')


def test_import_description_file_not_found(testpath, run_cli):
    """ Test case for not existing xml-file."""
    dmdsec_location = 'tests/data/import_description/metadata/' \
        'dc_description_not_found.xml'
    dmdsec_target = 'tests/data/structured/'

    result = run_cli(main, [
        dmdsec_location, '--dmdsec_target', dmdsec_target,
        '--workspace', testpath],
        success=False)
    assert isinstance(result.exception, SystemExit)


def test_import_description_no_xml(testpath, run_cli):
    """ test case for invalid XML file """
    dmdsec_location = 'tests/data/import_description/plain_text.xml'
    dmdsec_target = 'tests/data/structured/'

    result = run_cli(main, [
        dmdsec_location, '--workspace', dmdsec_target,
        '--workspace', testpath],
        success=False)
    assert isinstance(result.exception, ET.XMLSyntaxError)


def test_import_description_invalid_namespace(testpath, run_cli):
    """ test case for invalid namespace in XML file """
    dmdsec_location = 'tests/data/import_description/dc_invalid_ns.xml'
    dmdsec_target = 'tests/data/structured/'

    result = run_cli(main, [
        dmdsec_location, '--workspace', dmdsec_target,
        '--workspace', testpath],
        success=False)
    assert isinstance(result.exception, TypeError)
