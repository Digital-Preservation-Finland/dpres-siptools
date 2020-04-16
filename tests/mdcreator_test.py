# coding=utf-8
"""Tests for the utility functions."""
from __future__ import unicode_literals

import os
import json
import lxml.etree
from siptools.mdcreator import (MetsSectionCreator, get_md_references,
                                remove_dmdsec_references)


def test_create_amdfile(testpath):
    """Test write_md function. Pass a dummy XML element to the
    function and check that XML file with correct filename is created to
    workspace. Check that XML file contains expected elements.
    """

    md_creator = MetsSectionCreator(testpath)

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

    md_creator = MetsSectionCreator(testpath)

    md_creator.add_reference('abcd1234', 'path/to/file1')
    md_creator.add_reference('abcd1234', 'path/to/file2')

    md_creator.write_references('md-references.json')

    # Read created file. Reference should be found for both files
    with open(os.path.join(testpath, 'md-references.json')) as in_file:
        references = json.load(in_file)

    reference = references["path/to/file1"]
    assert reference['md_ids'][0] == 'abcd1234'

    reference = references["path/to/file2"]
    assert reference['md_ids'][0] == 'abcd1234'


def test_get_md_references():
    """Test get_md_references function. Reads the administrative MD IDs from
    a file.
    """
    with open('tests/data/sample_md-references.json') as in_file:
        references = json.load(in_file)

    # The sample file contains two references for file2
    ids = get_md_references(references, 'path/to/file2')
    assert set(ids) == set(['abcd1234', 'efgh5678'])


def test_remove_dmdsec_references(testpath):
    """Tests the remove_dmdsec_references function."""
    refs = ('{".": {"path_type": "directory", '
            '"md_ids": ["aabbcc"], "streams": []}}')

    with open(os.path.join(testpath, 'import-description-md-references.json'),
              'w+') as outfile:
        outfile.write(refs)

    remove_dmdsec_references(testpath)

    assert not os.path.exists(os.path.join(
        testpath, 'import-description-md-references.json'))
