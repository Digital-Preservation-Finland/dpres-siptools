from siptools.scraper.jhove import JhovePDF
import pytest


def test_JhovePDF():
    jhove = JhovePDF('tests/data/sample_1_3.pdf')

    assert jhove.mimetype == 'application/pdf'
    assert jhove.file_version == "1.3"
