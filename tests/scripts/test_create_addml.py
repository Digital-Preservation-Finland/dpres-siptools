"""Tests for ``siptools.scripts.create_addml`` module"""
from __future__ import unicode_literals

import os

import pytest

import lxml.etree as ET
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

    addml_etree = create_addml.create_addml_metadata(
        csv_file=CSV_FILE, delimiter=DELIMITER, isheader=is_header,
        charset=CHARSET, record_separator=RECORDSEPARATOR,
        quoting_char=QUOTINGCHAR
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

    addml_etree = create_addml.create_addml_metadata(
        csv_file=CSV_FILE, delimiter=DELIMITER, isheader=is_header,
        charset=CHARSET, record_separator=RECORDSEPARATOR,
        quoting_char=QUOTINGCHAR, flatfile_name="path/to/test"
    )

    # Check that URL encoded path is written to flatFile element
    flatfile = addml_etree.find(ADDML_NS + "flatFile")
    assert decode_path(flatfile.get("name")) == "path/to/test"


@pytest.mark.parametrize(
    'isheader, exp_amd_files, exp_fields',
    [(False,
      ['ec816a14242f3984e483fa23174881d5-ADDML-amd.xml',
       'dd678fd96b655fd95efbb9fe4a77483a-ADDML-amd.xml'],
      [['header1', 'header2', 'header3'], ['header1', 'header2', 'header3']]),
     (True,
      ['f2d98110001385875d56ef940394f826-ADDML-amd.xml',
       'c27d34506bd21076849458c6214095c9-ADDML-amd.xml'],
      [['1', '2', '3'], ['test', 'test', 'test']])]
)
def test_create_addml_creator(testpath, isheader, exp_amd_files, exp_fields):
    """
    Test that ``create_addml`` creates addml files and
    md-reference file without unnecessary duplication.
    """
    # Common expectations
    exp_csvs = [
        ['tests/data/simple_csv.csv', 'tests/data/simple_csv_2.csv'],
        ['tests/data/csvfile.csv']
    ]
    exp_flatfiles_child_count = [4, 3]

    _create_addml(testpath, isheader)

    # Check that md-reference and the ADDML-amd files with correct content
    # are created
    assert os.path.isfile(
        os.path.join(testpath, 'create-addml-md-references.xml')
    )

    for amd_file_index, exp_amd_file in enumerate(exp_amd_files):
        amd_file = os.path.join(testpath, exp_amd_file)
        assert os.path.isfile(amd_file)

        root = ET.parse(amd_file)
        flat_files = root.find(ADDML_NS + "flatFiles")

        # Verify the number of child elements in flatFiles
        assert len(flat_files) == exp_flatfiles_child_count[amd_file_index]

        # Verify that right CSV files are in flatFiles
        for index, exp_csv in enumerate(exp_csvs[amd_file_index]):
            assert decode_path(flat_files[index].get('name')) == exp_csv

        # Verify fields within flatFiles
        field_definitions = root.find(ADDML_NS + "fieldDefinitions")
        for index, field in enumerate(field_definitions):
            assert field.get('name') == exp_fields[amd_file_index][index]


@pytest.mark.parametrize("file_, base_path", [
    ('tests/data/csvfile.csv', ''),
    ('./tests/data/csvfile.csv', ''),
    ('csvfile.csv', 'tests/data'),
    ('./csvfile.csv', './tests/data'),
    ('data/csvfile.csv', 'absolute')
])
def test_paths(testpath, file_, base_path, run_cli):
    """ Test the following path arguments:
    (1) Path without base_path
    (2) Path without base bath, but with './'
    (3) Path with base path
    (4) Path with base path and with './'
    (5) Absolute base path
    """
    if 'absolute' in base_path:
        base_path = os.path.join(os.getcwd(), 'tests')

    if base_path != '':
        run_cli(create_addml.main, [
            '--delim', DELIMITER, '--charset', CHARSET,
            '--sep', RECORDSEPARATOR, '--quot', QUOTINGCHAR,
            '--workspace', testpath, '--base_path', base_path, file_])
    else:
        run_cli(create_addml.main, [
            '--delim', DELIMITER, '--charset', CHARSET,
            '--sep', RECORDSEPARATOR, '--quot', QUOTINGCHAR,
            '--workspace', testpath, file_])

    assert "file=\"" + os.path.normpath(file_) + "\"" in \
        open(os.path.join(testpath,
                          'create-addml-md-references.xml')).read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file_)))


@pytest.mark.parametrize("filename, charset", [
    ("tests/data/valid_utf8.csv", "UTF-8"),
    ("tests/data/valid_iso8859-15.csv", "ISO-8859-15"),
    ("tests/data/valid_utf8.csv", "UTF-8"),
    ("tests/data/valid_iso8859-15.csv", "ISO-8859-15"),
])
def test_csv_header_charset(filename, charset):
    """
    Test CSV header read with different character encodings.

    :filename: Test file
    :charset: Character encoding of test file
    """
    header = create_addml.csv_header(attributes={
        "csv_file": filename, "delimiter": ",", "charset": charset,
        "isheader": True
    })
    assert header == ["year", "br\xe4nd", "m\xf6del", "detail", "other"]

    header = create_addml.csv_header(attributes={
        "csv_file": filename, "delimiter": ",", "charset": charset,
        "isheader": False
    })
    assert header == ["header1", "header2", "header3", "header4", "header5"]


def _create_addml(testpath, isheader):
    creator = create_addml.AddmlCreator(testpath)

    # Append two csv files with same
    # metadata, but different filename
    creator.add_addml_md(attributes={
        "csv_file": "tests/data/simple_csv.csv", "delimiter": ",",
        "isheader": isheader, "charset": CHARSET,
        "record_separator": RECORDSEPARATOR,
        "quoting_char": QUOTINGCHAR
    })

    creator.add_addml_md(attributes={
        "csv_file": "tests/data/simple_csv_2.csv", "delimiter": ",",
        "isheader": isheader, "charset": CHARSET,
        "record_separator": RECORDSEPARATOR,
        "quoting_char": QUOTINGCHAR
    })

    # Append csv file with different metadata
    creator.add_addml_md(attributes={
        "csv_file": CSV_FILE, "delimiter": DELIMITER, "isheader": isheader,
        "charset": CHARSET, "record_separator": RECORDSEPARATOR,
        "quoting_char": QUOTINGCHAR
    })

    creator.write()
