""" Test"""
import os
from urllib import quote_plus
import lxml.etree as ET
import pytest
from click.testing import CliRunner
from siptools.scripts.import_description import main


def test_import_description_valid_file(testpath):
    """ Test case for single valid xml-file"""
    dmdsec_location = 'tests/data/import_description/metadata/' \
        'dc_description.xml'
    dmdsec_target = 'tests/data/structured/'

    url_location = quote_plus(dmdsec_target, safe='') + '-dmdsec.xml'

    runner = CliRunner()
    result = runner.invoke(main, [
        dmdsec_location, '--dmdsec_target', dmdsec_target,
        '--workspace', testpath, '--remove_root'])
    output_file = os.path.join(testpath, url_location)
    tree = ET.parse(output_file)
    root = tree.getroot()


def test_import_description_file_not_found(testpath):
    """ Test case for not existing xml-file."""
    dmdsec_location = 'tests/data/import_description/metadata/' \
        'dc_description_not_found.xml'
    dmdsec_target = 'tests/data/structured/'

    runner = CliRunner()
    result = runner.invoke(main, [
        dmdsec_location, '--dmdsec_target', dmdsec_target,
        '--workspace', testpath])
    assert type(result.exception) == SystemExit


def test_import_description_no_xml(testpath):
    """ test case for invalid XML file """
    dmdsec_location = 'tests/data/import_description/plain_text.xml'
    dmdsec_target = 'tests/data/structured/'

    runner = CliRunner()
    result = runner.invoke(main, [
        dmdsec_location, '--workspace', dmdsec_target,
        '--workspace', testpath])
    assert type(result.exception) == ET.XMLSyntaxError


def test_import_description_invalid_namespace(testpath):
    """ test case for invalid namespace in XML file """
    dmdsec_location = 'tests/data/import_description/dc_invalid_ns.xml'
    dmdsec_target = 'tests/data/structured/'

    runner = CliRunner()
    result = runner.invoke(main, [
        dmdsec_location, '--workspace', dmdsec_target,
        '--workspace', testpath])
    assert type(result.exception) == TypeError
