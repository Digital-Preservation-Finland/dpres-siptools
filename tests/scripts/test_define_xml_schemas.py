# encoding: utf-8
"""Unit tests for ``siptools.scripts.define_xml_schemas`` module"""
from __future__ import unicode_literals

import os

import lxml.etree as ET

from siptools.scripts import define_xml_schemas
from siptools.utils import read_md_references
from siptools.xml.mets import NAMESPACES


def get_amd_file(path):
    """Get id"""
    refs = read_md_references(path, 'define-xml-schemas-references.jsonl')
    reference = refs['.']

    amdrefs = reference['md_ids']

    output = []
    for amdref in amdrefs:
        output_file = os.path.join(
            path, amdref[1:] + '-PREMIS%3AOBJECT-amd.xml')
        if os.path.exists(output_file):
            output.append(output_file)

    return output


def test_define_xml_schemas_ok(testpath, run_cli):
    """Test define_xml_schemas.main funtion with valid test data. The
    test assert that a PREMIS XML file has been created and linked to
    from the references json file and that the XML metadata is as
    expected.
    """
    input_file = 'tests/data/mets_valid_minimal.xml'
    arguments = ['--workspace', testpath,
                 '--uri_pairs', 'myuri', input_file,
                 '--uri_pairs', 'myuri2', input_file]
    run_cli(define_xml_schemas.main, arguments)

    output = get_amd_file(testpath)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1

    assert root.xpath('//premis:object', namespaces=NAMESPACES)[0].get(
            '{http://www.w3.org/2001/XMLSchema-instance}type') == (
                'premis:representation')
    assert len(root.xpath('//premis:environment/premis:dependency',
                          namespaces=NAMESPACES)) == 2
    for dependency in root.xpath('//premis:environment/premis:dependency',
                                 namespaces=NAMESPACES):
        assert dependency.xpath('./premis:dependencyName',
                                namespaces=NAMESPACES)[0].text == input_file
        assert dependency.xpath(
            './premis:dependencyIdentifier/premis:dependencyIdentifierType',
            namespaces=NAMESPACES)[0].text == 'URI'
        assert dependency.xpath(
            './premis:dependencyIdentifier/premis:dependencyIdentifierValue',
            namespaces=NAMESPACES)[0].text in ['myuri', 'myuri2']


def test_define_xml_schemas_base_path_ok(testpath, run_cli):
    """Test define_xml_schemas.main funtion with valid test data using
    the base_path argument.
    """
    input_file = 'mets_valid_minimal.xml'
    arguments = ['--workspace', testpath, '--uri_pairs',
                 'myuri', input_file,
                 '--base_path', 'tests/data']
    run_cli(define_xml_schemas.main, arguments)

    output = get_amd_file(testpath)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1


def test_define_xml_schemas_invalid(testpath, run_cli):
    """Test define_xml_schemas.main funtion with an invalid schema
    path. An exception should be raised.
    """
    input_file = 'tests/data/non-existing-file.xml'
    arguments = ['--workspace', testpath, '--uri_pairs',
                 'myuri', input_file]
    result = run_cli(define_xml_schemas.main, arguments, success=False)
    assert result.exception
