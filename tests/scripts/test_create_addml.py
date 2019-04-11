"""Tests for ``siptools.scripts.create_addml`` module"""

import os
import pytest
import lxml.etree as ET
from click.testing import CliRunner
import siptools.scripts.create_addml as create_addml
from siptools.utils import decode_path


CSV_FILE = "tests/data/csvfile.csv"
DELIMITER = ";"
CHARSET = "UTF-8"
RECORDSEPARATOR = "CR+LF"
QUOTINGCHAR = '"'

ADDML_NS = './/{http://www.arkivverket.no/standarder/addml}'


@pytest.mark.parametrize('is_header', [False, True])
def test_create_addml(is_header):
    """Test that ``create_addml`` returns valid addml."""

    addml_etree = create_addml.create_addml(
        CSV_FILE, DELIMITER, is_header,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR
    )

    # Check namespace
    assert addml_etree.nsmap['addml'] == \
        'http://www.arkivverket.no/standarder/addml'

    # Check schema
    assert addml_etree.get(
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'
    ) == "http://www.arkivverket.no/standarder/addml "\
         "http://schema.arkivverket.no/ADDML/latest/addml.xsd"

    # Check individual elements
    tags = ["fieldSeparatingChar", "charset", "recordSeparator", "quotingChar"]
    vals = [";", "UTF-8", "CR+LF", '"']

    for i, tag in enumerate(tags):
        val = addml_etree.find(ADDML_NS + tag).text
        assert val == vals[i]

    # Check that flatFile element is not added
    assert addml_etree.find(ADDML_NS + "flatFile") is None

    # Check that correct amount of headers is created
    assert len(addml_etree.find(ADDML_NS + "fieldDefinitions")) == 3


@pytest.mark.parametrize('is_header', [False, True])
def test_create_addml_with_flatfile(is_header):
    """Tests that ``create_addml`` adds flatFile element if optional
    parameter flatfile_name is provided.
    """

    addml_etree = create_addml.create_addml(
        CSV_FILE, DELIMITER, is_header,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR,
        flatfile_name="path/to/test"
    )

    # Check that URL encoded path is written to flatFile element
    flatfile = addml_etree.find(ADDML_NS + "flatFile")
    assert decode_path(flatfile.get("name")) == "path/to/test"


@pytest.mark.parametrize('is_header', [False, True])
def test_create_addml_creator(testpath, is_header):
    """
    Test that ``create_addml`` writes addml file and
    amd-reference file without unnecessary duplication.
    """

    creator = create_addml.AddmlCreator(testpath)

    # Append two csv files with same
    # metadata, but different filename
    creator.add_addml_md(
        "tests/data/simple_csv.csv", ',', is_header,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR
    )

    creator.add_addml_md(
        "tests/data/simple_csv_2.csv", ',', is_header,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR
    )

    # Append csv file with different metadata
    creator.add_addml_md(
        CSV_FILE, DELIMITER, is_header, CHARSET,
        RECORDSEPARATOR, QUOTINGCHAR
    )

    creator.write()

    if is_header:
        file1 = os.path.join(
            testpath, 'f2d98110001385875d56ef940394f826-ADDML-amd.xml'
        )
        file2 = os.path.join(
            testpath, 'c27d34506bd21076849458c6214095c9-ADDML-amd.xml'
        )
    else:
        file1 = os.path.join(
            testpath, 'ec816a14242f3984e483fa23174881d5-ADDML-amd.xml'
        )
        file2 = os.path.join(
            testpath, 'dd678fd96b655fd95efbb9fe4a77483a-ADDML-amd.xml'
        )

    # Check that amd-reference and the two ADDML-amd files are created
    assert os.path.isfile(os.path.join(testpath, 'amd-references.xml'))
    assert os.path.isfile(file1)
    assert os.path.isfile(file2)

    # Parse ADDML-amd files to check that right flatFiles are added
    root1 = ET.parse(file1)
    root2 = ET.parse(file2)

    flat_files1 = root1.find(ADDML_NS + "flatFiles")
    flat_files2 = root2.find(ADDML_NS + "flatFiles")

    # Check number of child elements
    assert len(flat_files1) == 4
    assert len(flat_files2) == 3

    # Check flatFile name attributes
    path1 = decode_path(flat_files1[0].get("name"))
    path2 = decode_path(flat_files1[1].get("name"))
    path3 = decode_path(flat_files2[0].get("name"))

    assert path1 == "tests/data/simple_csv.csv"
    assert path2 == "tests/data/simple_csv_2.csv"
    assert path3 == "tests/data/csvfile.csv"

    field_definitions1 = root1.find(ADDML_NS + "fieldDefinitions")
    field_definitions2 = root2.find(ADDML_NS + "fieldDefinitions")
    if is_header:
        assert field_definitions1[0].get('name') == '1'
        assert field_definitions1[1].get('name') == '2'
        assert field_definitions1[2].get('name') == '3'
        assert field_definitions2[0].get('name') == 'test'
        assert field_definitions2[1].get('name') == 'test'
        assert field_definitions2[2].get('name') == 'test'
    else:
        assert field_definitions1[0].get('name') == 'header1'
        assert field_definitions1[1].get('name') == 'header2'
        assert field_definitions1[2].get('name') == 'header3'
        assert field_definitions2[0].get('name') == 'header1'
        assert field_definitions2[1].get('name') == 'header2'
        assert field_definitions2[2].get('name') == 'header3'


@pytest.mark.parametrize("file_, base_path", [
    ('tests/data/csvfile.csv', ''),
    ('./tests/data/csvfile.csv', ''),
    ('csvfile.csv', 'tests/data'),
    ('./csvfile.csv', './tests/data'),
    ('data/csvfile.csv', 'absolute')
])
def test_paths(testpath, file_, base_path):
    """ Test the following path arguments:
    (1) Path without base_path
    (2) Path without base bath, but with './'
    (3) Path with base path
    (4) Path with base path and with './'
    (5) Absolute base path
    """
    if 'absolute' in base_path:
        base_path = os.path.join(os.getcwd(), 'tests')

    runner = CliRunner()
    if base_path != '':
        runner.invoke(create_addml.main, [
            '--delim', DELIMITER, '--charset', CHARSET,
            '--sep', RECORDSEPARATOR, '--quot', QUOTINGCHAR,
            '--workspace', testpath, '--base_path', base_path, file_])
    else:
        runner.invoke(create_addml.main, [
            '--delim', DELIMITER, '--charset', CHARSET,
            '--sep', RECORDSEPARATOR, '--quot', QUOTINGCHAR,
            '--workspace', testpath, file_])

    assert "file=\"" + os.path.normpath(file_) + "\"" in \
        open(os.path.join(testpath, 'amd-references.xml')).read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file_)))
