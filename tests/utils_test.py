# coding=utf-8
"""Tests for the utility functions."""
from __future__ import unicode_literals

import pytest
import lxml.etree
from file_scraper.scraper import Scraper

import siptools.utils as utils


def test_encode_path():
    """Tests for the encode_path function."""
    encoded_path = utils.encode_path('tests/testpath')
    assert encoded_path == 'tests%2Ftestpath'

    encoded_path = utils.encode_path(
        'tests/testpath', suffix='-testsuffix', prefix='testprefix-'
    )
    assert encoded_path == 'testprefix-tests%2Ftestpath-testsuffix'

    encoded_path = utils.encode_path('tästs/tøstpath')
    assert encoded_path == 't%C3%A4sts%2Ft%C3%B8stpath'


def test_decode_path():
    """Tests for the decode_path function."""
    decoded_path = utils.decode_path('tests%2Ftestpath')
    assert decoded_path == 'tests/testpath'

    decoded_path = utils.decode_path(
        'tests%2Ftestpath-testsuffix', suffix='-testsuffix'
    )
    assert decoded_path == 'tests/testpath'

    decoded_path = utils.decode_path('t%C3%A4sts%2Ft%C3%B8stpath')
    assert decoded_path == 't\u00e4sts/t\u00f8stpath'


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
    """Tests that same metadata produces the same digest."""
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


def test_filescraper_error(monkeypatch):
    """Test that file scraper error works if message contains non-ascii
    characters.
    """
    # pylint: disable = unused-argument, missing-docstring
    def mock_scrape(self, check_wellformed=True):
        self.well_formed = False
        self.info = {0: {'errors': ["Testing åäö"]}}

    monkeypatch.setattr(Scraper, 'scrape', mock_scrape)

    filepath = utils.ensure_str("tests/data/invalid_empty_text-file.txt")
    message = utils.ensure_str("Testing åäö")
    with pytest.raises(ValueError) as error:
        utils.scrape_file(filepath, skip_well_check=True)

    assert "ValueError" in error.typename
    assert message in str(error.value)
