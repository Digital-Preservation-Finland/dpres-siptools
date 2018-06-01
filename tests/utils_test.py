"""Tests for the utility functions."""

from siptools.utils import encode_path, decode_path


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
