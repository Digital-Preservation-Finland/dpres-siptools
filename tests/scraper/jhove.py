from siptools.scraper.jhove import JhovePDF
import pytest


def test_JhovePDF_success():
    jhove = JhovePDF('tests/data/sample_1_3.pdf')

    assert jhove.mimetype == 'application/pdf'
    assert jhove.file_version == "1.3"

def test_JhovePDF_failure():

    with pytest.raises(IOError):
        jhove = JhovePDF('tests/data/MISSING_FILE')
