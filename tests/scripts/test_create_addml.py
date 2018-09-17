"""Tests for ``siptools.scripts.create_addml`` module"""

import os.path
import lxml.etree as ET

import siptools.scripts.create_addml as create_addml


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


def test_create_addml_techmdfile(testpath):
    """
    Test that ``create_addml_techmdfile`` writes addml file and techMD
    reference file without unnecessary duplication.
    """

    # Call create_addml_techmdfile() twice with
    # same metadata, but different filename
    create_addml.create_addml_techmdfile(
        "tests/data/simple_csv.csv", ',', ISHEADER,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR, testpath
    )

    create_addml.create_addml_techmdfile(
        "tests/data/simple_csv_2.csv", ',', ISHEADER,
        CHARSET, RECORDSEPARATOR, QUOTINGCHAR, testpath
    )

    # Call create_addml_techmdfile() with different metadata
    create_addml.create_addml_techmdfile(
        CSV_FILE, DELIMITER, ISHEADER, CHARSET,
        RECORDSEPARATOR, QUOTINGCHAR, testpath
    )

    file1 = os.path.join(
        testpath, '710ad5d65bbb4339fe265820f9ddbf8f-ADDML-techmd.xml'
    )
    file2 = os.path.join(
        testpath, '4368cf94e94b8217f2210b0071dc5175-ADDML-techmd.xml'
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
    assert flat_files1[0].get("name") == "simple_csv_2.csv"
    assert flat_files1[1].get("name") == "simple_csv.csv"

    assert flat_files2[0].get("name") == "csvfile.csv"
