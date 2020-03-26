# coding=utf-8
"""Tests for the utility functions."""
from __future__ import unicode_literals

import os
import lxml.etree
from siptools.mdcreator import (MdCreator, get_md_references,
                                remove_dmdsec_references)


def test_create_amdfile(testpath):
    """Test write_md function. Pass a dummy XML element to the
    function and check that XML file with correct filename is created to
    workspace. Check that XML file contains expected elements.
    """

    md_creator = MdCreator(testpath)

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

    md_creator = MdCreator(testpath)

    md_creator.add_reference('abcd1234', 'path/to/file1')
    md_creator.add_reference('abcd1234', 'path/to/file2')

    md_creator.write_references('md-references.xml')

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


def test_get_md_references():
    """Test get_md_references function. Reads the administrative MD IDs from
    a file.
    """
    xml = lxml.etree.parse('tests/data/sample_md-references.xml').getroot()

    # The sample file contains two references for file2
    ids = get_md_references(xml, 'path/to/file2')
    assert set(ids) == set(['abcd1234', 'efgh5678'])


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

    with open(os.path.join(testpath, 'import-description-md-references.xml'),
              'w+') as outfile:
        outfile.write(xml)

    remove_dmdsec_references(testpath)

    assert not os.path.exists(os.path.join(
        testpath, 'import-description-md-references.xml'))
