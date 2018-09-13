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

addml_ns = './/{http://www.arkivverket.no/standarder/addml}'

def test_create_addml():
    """Test that ``create_addml`` returns valid addml."""

    addml_etree = create_addml.create_addml(
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
    reference file without unnecessary duplication.
    """
    
    # Call create_addml_techmdfile() twice with 
    # same metadata, but different filename
    create_addml.create_addml_techmdfile(
            sip_creation_path, "simple_csv.csv", ',', isheader,
            charset, recordSeparator, quotingChar, testpath)

    create_addml.create_addml_techmdfile(
            sip_creation_path, "simple_csv_2.csv", ',', isheader,
            charset, recordSeparator, quotingChar, testpath)

    # Call create_addml_techmdfile() with different metadata
    create_addml.create_addml_techmdfile(
            sip_creation_path, csv_filename, delimiter, isheader,
            charset, recordSeparator, quotingChar, testpath)

    file1 = os.path.join(
            testpath, '710ad5d65bbb4339fe265820f9ddbf8f-ADDML-techmd.xml')
    
    file2 = os.path.join(
            testpath, '4368cf94e94b8217f2210b0071dc5175-ADDML-techmd.xml')

    # Check that techmdreference and the two ADDML-techmd files are created
    assert os.path.isfile(os.path.join(testpath, 'techmd-references.xml'))
    assert os.path.isfile(file1)
    assert os.path.isfile(file2)

    # Parse ADDML-techmd files to check that right flatFiles are added
    root1 = ET.parse(file1)
    root2 = ET.parse(file2)
    
    flatFiles1 = root1.find(addml_ns + "flatFiles")    
    flatFiles2 = root2.find(addml_ns + "flatFiles")

    # Check number of child elements
    assert len(flatFiles1) == 4
    assert len(flatFiles2) == 3

    # Check flatFile name attributes
    assert flatFiles1[0].get("name") == "simple_csv_2.csv"
    assert flatFiles1[1].get("name") == "simple_csv.csv"

    assert flatFiles2[0].get("name") == "csvfile.csv"
