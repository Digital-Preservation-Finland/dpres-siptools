"""Tests for ``siptools.scripts.create_addml`` module"""
import os.path
import siptools.scripts.create_addml as create_addml
import addml
import lxml.etree as ET


sip_creation_path = "tests/data/"
csv_filename = "csvfile.csv"
delimiter = ";"
isheader = False
charset = "UTF-8"
recordSeparator = "CR+LF"
quotingChar = '"'


def test_create_addml_etree():
    """Test that ``create_addml`` returns valid addml."""

    addml_ns = './/{http://www.arkivverket.no/standarder/addml}'

    addml_etree = create_addml.create_addml_etree(
            sip_creation_path, csv_filename, delimiter,
            isheader, charset, recordSeparator, quotingChar)

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

    for i in range(len(tags)):
        val = addml_etree.find(addml_ns + tags[i]).text
        assert val == vals[i]

    # Check that flatFile element is not added
    assert addml_etree.find(addml_ns + "flatFile") is None

    # Check that correct amount of headers is created
    assert len(addml_etree.find(addml_ns + "fieldDefinitions")) == 3
    

def test_create_addml_techmdfile(testpath):
    """
    Test that ``create_addml_techmdfile`` writes addml file and techMD
    reference file.
    """
    create_addml.create_addml_techmdfile(
            sip_creation_path, csv_filename, delimiter, isheader,
            charset, recordSeparator, quotingChar, testpath)

    assert os.path.isfile(os.path.join(testpath, 'techmd-references.xml'))
    assert os.path.isfile(os.path.join(
        testpath, '4368cf94e94b8217f2210b0071dc5175-ADDML-techmd.xml'
    ))

    # TODO: Implement tests for adding multiple 
    #       CSV files to a single techMD file
