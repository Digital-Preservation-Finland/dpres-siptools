"""Tests for ``siptools.scripts.create_audiomd`` module"""

import os.path
import pytest
import lxml.etree as ET

import siptools.scripts.create_audiomd as create_audiomd


AUDIOMD_NS = 'http://www.loc.gov/audioMD/'
NAMESPACES = {"amd" : AUDIOMD_NS}


def test_create_audiomd_elem():
    """Test that ``create_addml`` returns valid audiomd.
    """

    audiomd = create_audiomd.create_audiomd(
        "tests/data/audio/valid-wav.wav"
    )

    file_data = "/amd:AUDIOMD/amd:fileData"
    audio_info = "/amd:AUDIOMD/amd:audioInfo"

    # Check namespace
    assert audiomd.nsmap["amd"] == "http://www.loc.gov/audioMD/"

    # Check individual elements
    path = "/amd:AUDIOMD[@ANALOGDIGITALFLAG='FileDigital']"
    assert len(audiomd.xpath(path, namespaces=NAMESPACES)) == 1

    path = "%s/amd:audioDataEncoding" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PCM'

    path = "%s/amd:bitsPerSample" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '16'

    path = "%s/amd:compression/amd:codecCreatorApp" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unap)'

    path = "%s/amd:compression/amd:codecCreatorAppVersion" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unap)'

    path = "%s/amd:compression/amd:codecName" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unap)'

    path = "%s/amd:compression/amd:codecQuality" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'lossless'

    path = "%s/amd:dataRate" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '768'

    path = "%s/amd:dataRateMode" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Fixed'

    path = "%s/amd:samplingFrequency" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '48'

    path = "%s/amd:duration" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT0.77S'

    path = "%s/amd:numChannels" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '1'


def test_invalid_wav_file():
    """Test that calling create_audiomd() for file that can not be parsed
    raises ValueError
    """
    with pytest.raises(ValueError):
        create_audiomd.create_audiomd("non-existent.wav")


def test_create_audiomd_techmdfile(testpath):
    """Test that ``create_audiomd_techmdfile`` writes AudioMD file and techMD
    reference file.
    """
    creator = create_audiomd.AudiomdCreator(testpath)

    # Debug print
    print "\n\n%s" % ET.tostring(
        create_audiomd.create_audiomd("tests/data/audio/valid-wav.wav"),
        pretty_print=True
    )

    # Append WAV and broadcast WAV files with identical metadata
    creator.add_audiomd_md("tests/data/audio/valid-wav.wav")
    creator.add_audiomd_md("tests/data/audio/valid-bwf.wav")

    creator.write()

    # Check that techmdreference and one AudioMD-techmd files are created
    assert os.path.isfile(os.path.join(testpath, 'techmd-references.xml'))


    filepath1 = os.path.join(
        testpath, 'd5281d2582dc5e5240a45749faf9c206-AudioMD-techmd.xml'
    )
    filepath2 = os.path.join(
        testpath, 'ba6a79aa17288ac82245689e5c2ea98b-AudioMD-techmd.xml'
    )

    # Different hashes locally and at Pouta are caused by different
    # attribute orders. This will be addressed in ticket TPASPKT-153
    assert os.path.isfile(filepath1) or os.path.isfile(filepath2)


def test_is_broadcast_wav():
    """Test that WAV and broadcast WAV files are properly identified.
    """
    path = "tests/data/audio"
    assert create_audiomd.is_broadcast_wav("%s/valid-bwf.wav" % path)
    assert not create_audiomd.is_broadcast_wav("%s/valid-wav.wav" % path)
