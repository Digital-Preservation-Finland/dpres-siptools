"""Tests for ``siptools.scripts.create_audiomd`` module"""

import os.path
import pytest
import lxml.etree as ET

import pickle
import siptools.scripts.create_audiomd as create_audiomd

AUDIOMD_NS = 'http://www.loc.gov/audioMD/'
NAMESPACES = {"amd": AUDIOMD_NS}


def test_create_audiomd_elem():
    """Test that ``create_audiomd`` returns valid audiomd.
    """

    audiomd = create_audiomd.create_audiomd(
        "tests/data/audio/valid-wav.wav")["0"]

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
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == \
        'Lavf56.40.101'

    path = "%s/amd:compression/amd:codecCreatorAppVersion" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '56.40.101'

    path = "%s/amd:compression/amd:codecName" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PCM'

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


def test_stream():
    """Test that ``create_audiomd`` returns valid audiomd from a
       video container.
    """
    audiomd = create_audiomd.create_audiomd(
        "tests/data/video/mp4.mp4")["2"]

    file_data = "/amd:AUDIOMD/amd:fileData"
    audio_info = "/amd:AUDIOMD/amd:audioInfo"

    path = "%s/amd:audioDataEncoding" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'AAC'

    path = "%s/amd:bitsPerSample" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '0'

    path = "%s/amd:compression/amd:codecCreatorApp" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Lavf53.24.2'

    path = "%s/amd:compression/amd:codecCreatorAppVersion" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '53.24.2'

    path = "%s/amd:compression/amd:codecName" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'AAC'

    path = "%s/amd:compression/amd:codecQuality" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'lossy'

    path = "%s/amd:dataRate" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '384'

    path = "%s/amd:dataRateMode" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Variable'

    path = "%s/amd:samplingFrequency" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '48'

    path = "%s/amd:duration" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT5.31S'

    path = "%s/amd:numChannels" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '6'


def test_invalid_wav_file():
    """Test that calling create_audiomd() for file that can not be parsed
    raises ValueError
    """
    with pytest.raises(ValueError):
        create_audiomd.create_audiomd("non-existent.wav")


def test_create_audiomd(testpath):
    """Test that ``create_audiomd`` writes AudioMD file and
    amd-reference file.
    """
    creator = create_audiomd.AudiomdCreator(testpath)

    # Debug print
    print "\n\n%s" % ET.tostring(
        create_audiomd.create_audiomd("tests/data/audio/valid-wav.wav")["0"],
        pretty_print=True
    )

    # Append WAV and broadcast WAV files with identical metadata
    creator.add_audiomd_md("tests/data/audio/valid-wav.wav")
    creator.add_audiomd_md("tests/data/audio/valid-bwf.wav")

    creator.write()

    # Check that amd-reference and one AudioMD-amd files are created
    assert os.path.isfile(os.path.join(testpath, 'amd-references.xml'))

    filepath = os.path.join(
        testpath, 'f85dc91ce342e4d7067552b9d13613f2-AudioMD-amd.xml'
        # testpath, '704fbd57169eac3af9388e03c89dd919-AudioMD-amd.xml'
        # testpath, '4dab7d9d5bab960188ea0f25e478cb17-AudioMD-amd.xml'
    )

    assert os.path.isfile(filepath)


def test_existing_scraper_result(testpath):
    """Test that existing pickle file from import_object is used.
    We just need to check duration, since it's different from the real
    duration.
    """
    amdid = 'f85dc91ce342e4d7067552b9d13613f2'
    file_ = 'tests/data/audio/valid-wav.wav'
    xml = """<?xml version='1.0' encoding='UTF-8'?>
          <amdReferences>
          <amdReference file="%s">_%s</amdReference>
          </amdReferences>""" % (file_, amdid)
    with open(os.path.join(testpath, 'amd-references.xml'), 'w') as out:
        out.write(xml)

    stream_dict = {0: {
        'audio_data_encoding': 'PCM', 'bits_per_sample': '8',
        'codec_creator_app': 'Lavf56.40.101',
        'codec_creator_app_version': '56.40.101',
        'codec_name': 'PCM', 'codec_quality': 'lossless',
        'data_rate': '705.6', 'data_rate_mode': 'Fixed', 'duration': 'PT50S',
        'index': 0, 'mimetype': 'audio/x-wav', 'num_channels': '2',
        'sampling_frequency': '44.1', 'stream_type': 'audio', 'version': ''}}
    with open(os.path.join(testpath, ('%s-scraper.pkl' % amdid)), 'wb') \
            as outfile:
        pickle.dump(stream_dict, outfile)

    audiomd = create_audiomd.create_audiomd(file_, workspace=testpath)["0"]

    audio_info = "/amd:AUDIOMD/amd:audioInfo"
    path = "%s/amd:duration" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT50S'


@pytest.mark.parametrize("file, base_path", [
    ('tests/data/audio/valid-wav.wav', ''),
    ('./tests/data/audio/valid-wav.wav', ''),
    ('audio/valid-wav.wav', 'tests/data'),
    ('./audio/valid-wav.wav', './tests/data'),
    ('data/audio/valid-wav.wav', 'absolute')
])
def test_paths(testpath, file, base_path):
    """ Test the following path arguments:
    (1) Path without base_path
    (2) Path without base bath, but with './'
    (3) Path with base path
    (4) Path with base path and with './'
    (5) Absolute base path
    """
    if 'absolute' in base_path:
        base_path = os.path.join(os.getcwd(), 'tests')

    if base_path != '':
        create_audiomd.main(['--workspace', testpath, '--base_path',
                             base_path, file])
    else:
        create_audiomd.main(['--workspace', testpath, file])

    assert "file=\"" + os.path.normpath(file) + "\"" in \
        open(os.path.join(testpath, 'amd-references.xml')).read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file)))
