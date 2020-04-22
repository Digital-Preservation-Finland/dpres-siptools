# coding=utf-8
"""Tests for the utility functions."""
from __future__ import unicode_literals

import os
import json
import pytest
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


@pytest.mark.parametrize(('references', 'expected'), [
    ([['abcd1234', 'path/to/file1', None]],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': ['abcd1234'],
                         'streams': {}}})),
    ([['abcd1234', 'path/to/file1', '1']],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': [],
                         'streams': {'1': ['abcd1234']}}})),
    ([['abcd1234', 'path/to/file1', None],
      ['abcd5678', 'path/to/file1', None]],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': ['abcd1234', 'abcd5678'],
                         'streams': {}}})),
    ([['abcd1234', 'path/to/file1', 1],
      ['abcd5678', 'path/to/file1', 1]],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': [],
                         'streams': {'1': ['abcd1234', 'abcd5678']}}})),
    ([['abcd1234', 'path/to/file1', None],
      ['abcd5678', 'path/to/file2', None]],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': ['abcd1234'],
                         'streams': {}},
       'path/to/file2': {'path_type': 'file',
                         'md_ids': ['abcd5678'],
                         'streams': {}}})),
    ([['abcd1234', 'path/to/file1', 1],
      ['abcd5678', 'path/to/file1', 2]],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': [],
                         'streams': {'1': ['abcd1234'],
                                     '2': ['abcd5678']}}})),
    ([['abcd1234', 'path/to/file1', None],
      ['abcd5678', 'path/to/file1', 1]],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': ['abcd1234'],
                         'streams': {'1': ['abcd5678']}}})),
    ([['abcd1234', 'path/to/file1', None],
      ['abcd5678', 'path/to/file2', None],
      ['efgh1234', 'path/to/file3', None],
      ['efgh5678', 'path/to/file1', 1],
      ['ijkl1234', 'path/to/file1', 2],
      ['ijkl5678', 'path/to/file2', 1],
      ['mnop1234', 'path/to/file1', None],
      ['mnop5678', 'path/to/file2', 1]],
     ({'path/to/file1': {'path_type': 'file',
                         'md_ids': ['abcd1234', 'mnop1234'],
                         'streams': {'1': ['efgh5678'],
                                     '2': ['ijkl1234']}},
       'path/to/file2': {'path_type': 'file',
                         'md_ids': ['abcd5678'],
                         'streams': {'1': ['ijkl5678', 'mnop5678']}},
       'path/to/file3': {'path_type': 'file',
                         'md_ids': ['efgh1234'],
                         'streams': {}}})),
], ids=[
    'One file with one reference',
    'One bitstream with one reference',
    'One file with two references',
    'One bitstream with two references',
    'Two files, one reference each, no streams',
    'Two bitstreams, one reference each',
    'One file reference and one bistream reference for same path',
    'Multiple file and bistream references'
])
def test_add_mdreference(testpath, references, expected):
    """Test add_reference and write_references functions. Calls
    the add_reference function for each reference in references and
    assert that the write_references writes the expected output.

    This test test with different scenarios of references, invluding
    one or multiple files and bitstreams and a combination thereof.
    """

    md_creator = MetsSectionCreator(testpath)

    for reference in references:
        md_creator.add_reference(
            md_id=reference[0], filepath=reference[1], stream=reference[2])

    md_creator.write_references('md-references.json')

    with open(os.path.join(testpath, 'md-references.json')) as in_file:
        created_references = json.load(in_file)

    assert len(created_references) == len(expected)

    for path in expected:
        assert path in created_references
        assert len(created_references[path]['md_ids']) \
            == len(expected[path]['md_ids'])
        assert len(created_references[path]['streams']) \
            == len(expected[path]['streams'])
        for ref in expected[path]['md_ids']:
            assert ref in created_references[path]['md_ids']
        for stream in expected[path]['streams']:
            assert stream in created_references[path]['streams']
            assert len(created_references[path]['streams'][stream]) \
                == len(expected[path]['streams'][stream])
            for stream_id in expected[path]['streams'][stream]:
                assert stream_id in created_references[path]['streams'][stream]


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
    refs = {
        ".": {
            "path_type": "directory",
            "md_ids": ["aabbcc"],
            "streams": []
        }
    }

    with open(os.path.join(testpath, 'import-description-md-references.json'),
              'w+') as outfile:
        outfile.write(json.dumps(refs))

    remove_dmdsec_references(testpath)

    assert not os.path.exists(os.path.join(
        testpath, 'import-description-md-references.json'))
