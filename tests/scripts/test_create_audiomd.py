# encoding: utf-8
"""Tests for ``siptools.scripts.create_audiomd`` module"""
from __future__ import unicode_literals

import io
import os.path
import pickle
import shutil
import sys

import pytest
from click.testing import CliRunner

import lxml.etree as ET
import siptools.scripts.create_audiomd as create_audiomd

AUDIOMD_NS = 'http://www.loc.gov/audioMD/'
NAMESPACES = {"amd": AUDIOMD_NS}


def test_create_audiomd_elem():
    """Test that ``create_audiomd`` returns valid audiomd.
    """

    audiomd = create_audiomd.create_audiomd_metadata(
        "tests/data/audio/valid__wav.wav")["0"]

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
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '8'

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
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '706'

    path = "%s/amd:dataRateMode" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Fixed'

    path = "%s/amd:samplingFrequency" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '44.1'

    path = "%s/amd:duration" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT0.86S'

    path = "%s/amd:numChannels" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '2'


def test_stream():
    """Test that ``create_audiomd`` returns valid audiomd from a
       video container.
    """
    audiomd = create_audiomd.create_audiomd_metadata(
        "tests/data/video/valid__h264_aac.mp4")["2"]

    file_data = "/amd:AUDIOMD/amd:fileData"
    audio_info = "/amd:AUDIOMD/amd:audioInfo"

    path = "%s/amd:audioDataEncoding" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'AAC'

    path = "%s/amd:bitsPerSample" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '0'

    path = "%s/amd:compression/amd:codecCreatorApp" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == \
        'Lavf56.40.101'

    path = "%s/amd:compression/amd:codecCreatorAppVersion" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '56.40.101'

    path = "%s/amd:compression/amd:codecName" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'AAC'

    path = "%s/amd:compression/amd:codecQuality" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'lossy'

    path = "%s/amd:dataRate" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '135'

    path = "%s/amd:dataRateMode" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Fixed'

    path = "%s/amd:samplingFrequency" % file_data
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '44.1'

    path = "%s/amd:duration" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT0.86S'

    path = "%s/amd:numChannels" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == '2'


def test_invalid_wav_file():
    """Test that calling create_audiomd_metadata() for file that can not be
    parsed raises ValueError
    """
    with pytest.raises(ValueError):
        create_audiomd.create_audiomd_metadata("non-existent.wav")


def test_create_audiomd(testpath):
    """Test that ``create_audiomd`` writes AudioMD file and
    md-reference file.
    """
    creator = create_audiomd.AudiomdCreator(testpath)

    # Debug print
    print("\n\n%s" % ET.tostring(
        create_audiomd.create_audiomd_metadata(
            "tests/data/audio/valid__wav.wav"
        )["0"], pretty_print=True
    ))

    # Append WAV and broadcast WAV files with identical metadata
    creator.add_audiomd_md("tests/data/audio/valid__wav.wav")
    creator.add_audiomd_md("tests/data/audio/valid_2_bwf.wav")

    creator.write()

    # Check that md-reference and one AudioMD-amd files are created
    assert os.path.isfile(os.path.join(testpath, 'md-references.xml'))

    filepath = os.path.join(
        testpath, 'eae4d239422e21f3a8cfa57bb2afcb9e-AudioMD-amd.xml'
        # testpath, '704fbd57169eac3af9388e03c89dd919-AudioMD-amd.xml'
        # testpath, '4dab7d9d5bab960188ea0f25e478cb17-AudioMD-amd.xml'
    )

    assert os.path.isfile(filepath)


def test_main_utf8_files(testpath):
    """Test for ``main`` function with filenames that contain non-ascii
    characters.
    """
    # Create sample data directory with file that has non-ascii characters in
    # filename
    os.makedirs(os.path.join(testpath, 'data'))
    relative_path = os.path.join('data', 'äöå.wav')
    full_path = os.path.join(testpath, relative_path)
    shutil.copy('tests/data/audio/valid__wav.wav', full_path)

    # Call main function with encoded filename as parameter
    runner = CliRunner()
    runner.invoke(
        create_audiomd.main, [
            '--workspace', testpath, '--base_path', testpath,
            relative_path.encode(sys.getfilesystemencoding())
        ]
    )

    # Check that filename is found in amd-reference file.
    xml = ET.parse(os.path.join(testpath, 'md-references.xml'))
    assert len(xml.xpath('//mdReference[@file="data/äöå.wav"]')) == 1


def test_existing_scraper_result(testpath):
    """Test that existing pickle file from import_object is used.
    We just need to check duration, since it's different from the real
    duration.
    """
    amdid = 'eeca492963963af467f844701ad28104'
    file_ = 'tests/data/audio/valid__wav.wav'
    xml = """<?xml version='1.0' encoding='UTF-8'?>
          <mdReferences>
          <mdReference file="{}">_{}</mdReference>
          </mdReferences>""".format(file_, amdid).encode("utf-8")
    with open(os.path.join(testpath, 'md-references.xml'), 'wb') as out:
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

    audiomd = create_audiomd.create_audiomd_metadata(
        file_, workspace=testpath
    )["0"]

    audio_info = "/amd:AUDIOMD/amd:audioInfo"
    path = "%s/amd:duration" % audio_info
    assert audiomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT50S'


@pytest.mark.parametrize("file_, base_path", [
    ('tests/data/audio/valid__wav.wav', ''),
    ('./tests/data/audio/valid__wav.wav', ''),
    ('audio/valid__wav.wav', 'tests/data'),
    ('./audio/valid__wav.wav', './tests/data'),
    ('data/audio/valid__wav.wav', 'absolute')
])
def test_paths(testpath, file_, base_path):
    """ Test the following path arguments:
    (1) Path without base_path
    (2) Path without base bath, but with './'
    (3) Path with base path
    (4) Path with base path and with './'
    (5) Absolute base path
    """
    if 'absolute' in base_path:
        base_path = os.path.join(os.getcwd(), 'tests')
    runner = CliRunner()
    if base_path != '':
        runner.invoke(create_audiomd.main, [
            '--workspace', testpath, '--base_path', base_path, file_])
    else:
        runner.invoke(create_audiomd.main, [
            '--workspace', testpath, file_])

    assert "file=\"" + os.path.normpath(file_) + "\"" in \
        io.open(os.path.join(testpath, 'md-references.xml'), "rt").read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file_)))
