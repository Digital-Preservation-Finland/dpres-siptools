"""Tests for ``siptools.scripts.create_addml`` module"""

import os
import pytest
import lxml.etree as ET

import siptools.scripts.create_addml as create_addml
from siptools.utils import decode_path, encode_path


CSV_FILE = "tests/data/csvfile.csv"
DELIMITER = ";"
ISHEADER = False
CHARSET = "UTF-8"
RECORDSEPARATOR = "CR+LF"
QUOTINGCHAR = '"'

ADDML_NS = './/{http://www.arkivverket.no/standarder/addml}'


def test_create_addml():
    """Test that ``create_addml`` returns valid addml."""

    addml_etree = create_addml.create_addml(
        CSV_FILE, DELIMITER, ISHEADER,
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


def test_create_addml_with_flatfile():
    """Tests that ``create_addml`` adds flatFile element if optional
    parameter flatfile_name is provided.
    """

    addml_etree = create_addml.create_addml(
        CSV_FILE, DELIMITER, ISHEADER,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR,
        flatfile_name="path/to/test"
    )

    # Check that URL encoded path is written to flatFile element
    flatfile = addml_etree.find(ADDML_NS + "flatFile")
    assert decode_path(flatfile.get("name")) == "path/to/test"


def test_create_addml_techmdfile(testpath):
    """
    Test that ``create_addml_techmdfile`` writes addml file and techMD
    reference file without unnecessary duplication.
    """

    creator = create_addml.AddmlCreator(testpath)

    # Append two csv files with same
    # metadata, but different filename
    creator.add_addml_md(
        "tests/data/simple_csv.csv", ',', ISHEADER,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR
    )

    creator.add_addml_md(
        "tests/data/simple_csv_2.csv", ',', ISHEADER,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR
    )

    # Append csv file with different metadata
    creator.add_addml_md(
        CSV_FILE, DELIMITER, ISHEADER, CHARSET,
        RECORDSEPARATOR, QUOTINGCHAR
    )

    creator.write()

    file1 = os.path.join(
        testpath, 'ec816a14242f3984e483fa23174881d5-ADDML-techmd.xml'
    )
    file2 = os.path.join(
        testpath, 'dd678fd96b655fd95efbb9fe4a77483a-ADDML-techmd.xml'
    )

    # Check that techmdreference and the two ADDML-techmd files are created
    assert os.path.isfile(os.path.join(testpath, 'techmd-references.xml'))
    assert os.path.isfile(file1)
    assert os.path.isfile(file2)

    # Parse ADDML-techmd files to check that right flatFiles are added
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


@pytest.mark.parametrize("file, base_path", [
    ('tests/data/csvfile.csv', ''),
    ('./tests/data/csvfile.csv', ''),
    ('csvfile.csv', 'tests/data'),
    ('./csvfile.csv', './tests/data'),
    ('data/csvfile.csv', 'absolute')
])
def test_paths(testpath, file, base_path):
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
        create_addml.main(['--delim', DELIMITER, '--charset', CHARSET,
                           '--sep', RECORDSEPARATOR, '--quot', QUOTINGCHAR,
                           '--workspace', testpath, '--base_path',
                           base_path, file])
    else:
        create_addml.main(['--delim', DELIMITER, '--charset', CHARSET,
                           '--sep', RECORDSEPARATOR, '--quot', QUOTINGCHAR,
                           '--workspace', testpath, file])

    assert "file=\"" + encode_path(os.path.normpath(file).decode('utf-8')) + "\"" in \
        open(os.path.join(testpath, 'techmd-references.xml')).read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file)))
