# encoding: utf-8
"""Tests for ``siptools.scripts.create_audiomd`` module"""
from __future__ import unicode_literals

import io
import os.path
import json
import shutil
import sys

import lxml.etree as ET
import pytest
import siptools.scripts.create_audiomd as create_audiomd
from siptools.utils import read_md_references

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

    file_data_paths = (
        ('%s/amd:audioDataEncoding', 'PCM'),
        ('%s/amd:bitsPerSample', '8'),
        ('%s/amd:compression/amd:codecCreatorApp', 'Lavf56.40.101'),
        ('%s/amd:compression/amd:codecCreatorAppVersion', '56.40.101'),
        ('%s/amd:compression/amd:codecName', 'PCM'),
        ('%s/amd:compression/amd:codecQuality', 'lossless'),
        ('%s/amd:dataRate', '706'),
        ('%s/amd:dataRateMode', 'Fixed'),
        ('%s/amd:samplingFrequency', '44.1'),
    )
    audio_info_paths = (
        ('%s/amd:duration', 'PT0.86S'),
        ('%s/amd:numChannels', '2')
    )
    for prefix, paths in ((file_data, file_data_paths),
                          (audio_info, audio_info_paths)):
        for path, expected in paths:
            assert audiomd.xpath(path % prefix,
                                 namespaces=NAMESPACES)[0].text == expected


def test_stream():
    """Test that ``create_audiomd`` returns valid audiomd from a
       video container.
    """
    audiomd = create_audiomd.create_audiomd_metadata(
        "tests/data/video/valid__h264_aac.mp4")["2"]

    file_data = "/amd:AUDIOMD/amd:fileData"
    audio_info = "/amd:AUDIOMD/amd:audioInfo"

    file_data_paths = (
        ('%s/amd:audioDataEncoding', 'AAC'),
        ('%s/amd:bitsPerSample', '0'),
        ('%s/amd:compression/amd:codecCreatorApp', 'Lavf56.40.101'),
        ('%s/amd:compression/amd:codecCreatorAppVersion', '56.40.101'),
        ('%s/amd:compression/amd:codecName', 'AAC'),
        ('%s/amd:compression/amd:codecQuality', 'lossy'),
        ('%s/amd:dataRate', '135'),
        ('%s/amd:dataRateMode', 'Fixed'),
        ('%s/amd:samplingFrequency', '44.1'),
    )
    audio_info_paths = (
        ('%s/amd:duration', 'PT0.86S'),
        ('%s/amd:numChannels', '2')
    )
    for prefix, paths in ((file_data, file_data_paths),
                          (audio_info, audio_info_paths)):
        for path, expected in paths:
            assert audiomd.xpath(path % prefix,
                                 namespaces=NAMESPACES)[0].text == expected


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
    assert os.path.isfile(os.path.join(testpath,
                                       'create-audiomd-md-references.jsonl'))

    filepath = os.path.join(
        testpath, 'eae4d239422e21f3a8cfa57bb2afcb9e-AudioMD-amd.xml'
        # testpath, '704fbd57169eac3af9388e03c89dd919-AudioMD-amd.xml'
        # testpath, '4dab7d9d5bab960188ea0f25e478cb17-AudioMD-amd.xml'
    )

    assert os.path.isfile(filepath)


def test_main_utf8_files(testpath, run_cli):
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
    run_cli(
        create_audiomd.main, [
            '--workspace', testpath, '--base_path', testpath,
            relative_path.encode(sys.getfilesystemencoding())
        ]
    )

    # Check that filename is found in amd-reference file.
    refs = read_md_references(testpath, 'create-audiomd-md-references.jsonl')
    assert refs["data/äöå.wav"]


def test_existing_scraper_result(testpath):
    """Test that existing json file from import_object is used.
    We just need to check duration, since it's different from the real
    duration.
    """
    amdid = 'eeca492963963af467f844701ad28104'
    file_ = 'tests/data/audio/valid__wav.wav'
    ref = {
        file_: {
            "path_type": "file",
            "streams": {},
            "md_ids": ["_" + amdid]
        }
    }
    with open(os.path.join(testpath,
                           'import-object-md-references.jsonl'), 'wt') as out:
        json.dump(ref, out)

    stream_dict = {0: {
        'audio_data_encoding': 'PCM', 'bits_per_sample': '8',
        'codec_creator_app': 'Lavf56.40.101',
        'codec_creator_app_version': '56.40.101',
        'codec_name': 'PCM', 'codec_quality': 'lossless',
        'data_rate': '705.6', 'data_rate_mode': 'Fixed', 'duration': 'PT50S',
        'index': 0, 'mimetype': 'audio/x-wav', 'num_channels': '2',
        'sampling_frequency': '44.1', 'stream_type': 'audio', 'version': ''}}
    with open(os.path.join(testpath, ('%s-scraper.json' % amdid)), 'wt') \
            as outfile:
        json.dump(stream_dict, outfile)

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
def test_paths(testpath, file_, base_path, run_cli):
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
        run_cli(create_audiomd.main, [
            '--workspace', testpath, '--base_path', base_path, file_
        ])
    else:
        run_cli(create_audiomd.main, ['--workspace', testpath, file_])

    with io.open(os.path.join(testpath,
                              'create-audiomd-md-references.jsonl'),
                 "rt") as in_file:
        references = json.load(in_file)
    assert os.path.normpath(file_) in references

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file_)))
