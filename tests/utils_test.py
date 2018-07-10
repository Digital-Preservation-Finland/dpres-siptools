"""Tests for the utility functions."""

import os
import lxml.etree
from siptools.utils import encode_path, decode_path, create_techmdfile


def test_encode_path():
    """Tests for the encode_path function."""

    encoded_path = encode_path('tests/testpath')
    assert encoded_path == 'tests%2Ftestpath'

    encoded_path = encode_path('tests/testpath', suffix='-testsuffix',
                               prefix='testprefix-')
    assert encoded_path == 'testprefix-tests%2Ftestpath-testsuffix'

    encoded_path = encode_path(u't\u00e4sts/t\u00f8stpath')
    assert encoded_path == u't%C3%A4sts%2Ft%C3%B8stpath'


def test_decode_path():
    """Tests for the decode_path function."""

    decoded_path = decode_path('tests%2Ftestpath')
    assert decoded_path == 'tests/testpath'

    decoded_path = decode_path('tests%2Ftestpath-testsuffix',
                               suffix='-testsuffix')
    assert decoded_path == 'tests/testpath'

    decoded_path = decode_path('t%C3%A4sts%2Ft%C3%B8stpath')
    assert decoded_path == u't\u00e4sts/t\u00f8stpath'


def test_create_techmdfile(testpath):
    """Test create_techmdfile function. Pass a dummy XML element to the
    function and check that XML file with correct filename is created to
    workspace. Check that XML file contains expected elements.
    """

    sample_data = lxml.etree.Element('sampleData')
    create_techmdfile(testpath, 'mix', sample_data)

    element_tree = lxml.etree.parse(
        os.path.join(
            testpath,
            'mix-455752263d67f67402b0dc9e7119e5b3-othermd.xml'
        )
    )

    # The file should contain one techmd element
    techmd_elements = element_tree.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces={"mets": "http://www.loc.gov/METS/"}
    )
    assert len(techmd_elements) == 1

    # The techMD element should contain one sampleData element
    sample_data_elements = techmd_elements[0].xpath('//sampleData')
    assert len(sample_data_elements) == 1
