"""Tests for the utility functions."""

import os
import lxml.etree
import xml_helpers
import siptools.utils as utils


def test_encode_path():
    """Tests for the encode_path function."""

    encoded_path = utils.encode_path('tests/testpath')
    assert encoded_path == 'tests%2Ftestpath'

    encoded_path = utils.encode_path(
        'tests/testpath', suffix='-testsuffix', prefix='testprefix-'
    )
    assert encoded_path == 'testprefix-tests%2Ftestpath-testsuffix'

    encoded_path = utils.encode_path(u't\u00e4sts/t\u00f8stpath')
    assert encoded_path == u't%C3%A4sts%2Ft%C3%B8stpath'


def test_decode_path():
    """Tests for the decode_path function."""

    decoded_path = utils.decode_path('tests%2Ftestpath')
    assert decoded_path == 'tests/testpath'

    decoded_path = utils.decode_path(
        'tests%2Ftestpath-testsuffix', suffix='-testsuffix'
    )
    assert decoded_path == 'tests/testpath'

    decoded_path = utils.decode_path('t%C3%A4sts%2Ft%C3%B8stpath')
    assert decoded_path == u't\u00e4sts/t\u00f8stpath'


def test_create_amdfile(testpath):
    """Test write_md function. Pass a dummy XML element to the
    function and check that XML file with correct filename is created to
    workspace. Check that XML file contains expected elements.
    """

    md_creator = utils.MdCreator(testpath)

    sample_data = lxml.etree.Element('sampleData')
    md_creator.write_md(sample_data, 'NISOIMG', '2.0')

    element_tree = lxml.etree.parse(
        os.path.join(
            testpath,
            '455752263d67f67402b0dc9e7119e5b3-NISOIMG-amd.xml'
        )
    )

    # The file should contain one techmd element
    amd_elements = element_tree.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces={"mets": "http://www.loc.gov/METS/"}
    )
    assert len(amd_elements) == 1

    # The techMD element should contain one sampleData element wrapped in
    # mdWrap and xmlData elements
    sample_data_elements \
        = amd_elements[0].xpath(
            '//mets:mdWrap/mets:xmlData/sampleData',
            namespaces={"mets": "http://www.loc.gov/METS/"}
        )
    assert len(sample_data_elements) == 1


def test_add_mdreference(testpath):
    """Test add_reference function. Calls function two times and
    write the mdreference file.
    """

    md_creator = utils.MdCreator(testpath)

    md_creator.add_reference('abcd1234', 'path/to/file1')
    md_creator.add_reference('abcd1234', 'path/to/file2')

    md_creator.write_references()

    # Read created file. Reference should be found for both files
    etree = lxml.etree.parse(os.path.join(testpath, 'md-references.xml'))
    reference = etree.xpath(
        '/mdReferences/mdReference[@file="path/to/file1"]'
    )
    assert reference[0].text == 'abcd1234'
    reference = etree.xpath(
        '/mdReferences/mdReference[@file="path/to/file2"]'
    )
    assert reference[0].text == 'abcd1234'


def test_copy_etree():
    """Test that copy_etree creates a new lxml.etree
    instance with identical data.
    """
    etree1 = lxml.etree.parse("tests/data/sample_md-references.xml")
    etree2 = utils.copy_etree(etree1)

    assert id(etree1) != id(etree2)
    assert lxml.etree.tostring(etree1) == lxml.etree.tostring(etree2)


def test_hashing_same_attribute():
    """Test that identical attributes with other elements produces
    different digests.
    """
    root1 = lxml.etree.Element("root")
    lxml.etree.SubElement(root1, "sub1", attribute="value")
    lxml.etree.SubElement(root1, "sub2")

    root2 = lxml.etree.Element("root")
    lxml.etree.SubElement(root2, "sub1")
    lxml.etree.SubElement(root2, "sub2", attribute="value")

    assert utils.generate_digest(root1) != utils.generate_digest(root2)


def test_hashing_attribute_order():
    """Test that same metadata with different attribute order produces
    same digests.
    """
    root1 = lxml.etree.Element("root")
    lxml.etree.SubElement(root1, "sub", attribute1="value", attribute2="value")

    root2 = lxml.etree.Element("root")
    lxml.etree.SubElement(root2, "sub", attribute2="value", attribute1="value")

    assert utils.generate_digest(root1) == utils.generate_digest(root2)


def test_same_metadata_same_hash():
    """Tests that same metadata produces the same digest.
    """
    root = lxml.etree.parse(
        "tests/data/sample_md-references.xml").getroot()
    digest = utils.generate_digest(root)

    for _ in range(10):
        root = lxml.etree.parse(
            "tests/data/sample_md-references.xml").getroot()
        assert digest == utils.generate_digest(root)


def test_different_ids_same_hash():
    """Test that the generate_digest function returns the same hash for
    two premis metadata sections with different identifiers.
    """
    event1 = '<premis:event xmlns:premis="info:lc/xmlns/premis-v2">' \
             '<premis:eventIdentifier><premis:eventIdentifierType>a' \
             '</premis:eventIdentifierType><premis:eventIdentifierValue>b' \
             '</premis:eventIdentifierValue>123</premis:eventIdentifier>' \
             '</premis:event>'

    event2 = '<premis:event xmlns:premis="info:lc/xmlns/premis-v2">' \
             '<premis:eventIdentifier><premis:eventIdentifierType>a' \
             '</premis:eventIdentifierType><premis:eventIdentifierValue>b' \
             '</premis:eventIdentifierValue>134</premis:eventIdentifier>' \
             '</premis:event>'

    xml1 = lxml.etree.fromstring(event1)
    xml2 = lxml.etree.fromstring(event2)

    assert utils.generate_digest(xml1) == utils.generate_digest(xml2)


def test_remove_dmdsec_references(testpath):
    """Tests the remove_dmdsec_references function."""
    xml = ('<mdReferences><mdReference file="sample_images/sample_tiff1.tif">'
           '_e50655691d21e110a3c4b38da52fb91c</mdReference><mdReference '
           'file="sample_images/sample_tiff2.tif">'
           '_e50655691d21e110a3c4b38da52fb91c'
           '</mdReference><mdReference '
           'file="sample_images/sample_tiff1_compressed.tif">'
           '_c08061e439bd40407c9e5332fec6084e</mdReference>'
           '<mdReference directory="." ref_type="dmd">'
           'aabbcc</mdReference></mdReferences>')

    with open(os.path.join(testpath, 'md-references.xml'), 'w+') as outfile:
        outfile.write(xml)

    utils.remove_dmdsec_references(testpath)

    root = lxml.etree.parse(
        os.path.join(testpath, 'md-references.xml')).getroot()

    assert not root.xpath('/mdReferences/mdReference[@ref_type="dmd"]')
    assert len(root.xpath('/mdReferences/*')) == 3
