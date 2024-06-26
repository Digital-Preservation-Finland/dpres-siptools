"""Tests for ``siptools.scripts.create_videomd`` module"""

import os.path
import json
import shutil

import pytest

import lxml.etree as ET
import siptools.scripts.create_videomd as create_videomd
from siptools.utils import fsencode_path, read_md_references

VIDEOMD_NS = 'http://www.loc.gov/videoMD/'
NAMESPACES = {"vmd": VIDEOMD_NS}


def test_create_videomd_elem():
    """Test that ``create_videomd_metadata`` returns valid videomd.
    """

    videomd = create_videomd.create_videomd_metadata(
        "tests/data/video/valid_1.m1v")["0"]

    file_data = "/vmd:VIDEOMD/vmd:fileData"

    # Check namespace
    assert videomd.nsmap["vmd"] == "http://www.loc.gov/videoMD/"

    # Check individual elements
    path = "/vmd:VIDEOMD[@ANALOGDIGITALFLAG='FileDigital']"
    assert len(videomd.xpath(path, namespaces=NAMESPACES)) == 1

    path = "%s/vmd:bitsPerSample" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '8'

    path = "%s/vmd:compression/vmd:codecCreatorApp" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:compression/vmd:codecCreatorAppVersion" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:compression/vmd:codecName" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'MPEG Video'

    path = "%s/vmd:compression/vmd:codecQuality" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'lossy'

    path = "%s/vmd:dataRate" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '0.171304'

    path = "%s/vmd:dataRateMode" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Variable'

    path = "%s/vmd:color" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Color'

    path = "%s/vmd:frame/vmd:pixelsHorizontal" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '320'

    path = "%s/vmd:frame/vmd:pixelsVertical" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '180'

    path = "%s/vmd:frame/vmd:PAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1'

    path = "%s/vmd:frame/vmd:DAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1.778'

    path = "%s/vmd:sampling" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '4:2:0'

    path = "%s/vmd:duration" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT1S'

    path = "%s/vmd:signalFormat" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unap)'

    path = "%s/vmd:sound" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'No'


def test_stream():
    """Test that ``create_videomd_metadata`` returns valid videomd from a
       video container.
    """

    videomd = create_videomd.create_videomd_metadata(
        "tests/data/video/valid__h264_aac.mp4"
    )["1"]

    file_data = "/vmd:VIDEOMD/vmd:fileData"

    path = "%s/vmd:bitsPerSample" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '8'

    path = "%s/vmd:compression/vmd:codecCreatorApp" % file_data
    assert videomd.xpath(path,
                         namespaces=NAMESPACES)[0].text == 'Lavf56.40.101'

    path = "%s/vmd:compression/vmd:codecCreatorAppVersion" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '56.40.101'

    path = "%s/vmd:compression/vmd:codecName" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'AVC'

    path = "%s/vmd:compression/vmd:codecQuality" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'lossy'

    path = "%s/vmd:dataRate" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '0.048704'

    path = "%s/vmd:dataRateMode" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Variable'

    path = "%s/vmd:color" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Color'

    path = "%s/vmd:frame/vmd:pixelsHorizontal" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '320'

    path = "%s/vmd:frame/vmd:pixelsVertical" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '180'

    path = "%s/vmd:frame/vmd:PAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1'

    path = "%s/vmd:frame/vmd:DAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1.778'

    path = "%s/vmd:sampling" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '4:2:0'

    path = "%s/vmd:duration" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT1S'

    path = "%s/vmd:signalFormat" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unap)'

    path = "%s/vmd:sound" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Yes'


def test_invalid_file():
    """Test that calling create_videomd_metadata() for file that can not be
    parsed raises ValueError
    """
    with pytest.raises(ValueError):
        create_videomd.create_videomd_metadata("non-existent.mpg")


def test_create_videomd(testpath):
    """Test that ``create_videomd`` writes VideoMD file and
    md-reference file.
    """
    creator = create_videomd.VideomdCreator(testpath)

    # Debug print
    print("\n\n%s" % ET.tostring(
        create_videomd.create_videomd_metadata(
            "tests/data/video/valid_1.m1v"
        )["0"], pretty_print=True
    ))

    # Append same file twice
    creator.add_videomd_md("tests/data/video/valid_1.m1v")
    creator.add_videomd_md("tests/data/video/valid_1.m1v")

    creator.write()

    # Check that mdreference and one VideoMD-amd files are created
    assert os.path.isfile(os.path.join(testpath,
                                       'create-videomd-md-references.jsonl'))

    filepath = os.path.join(
        testpath, '36260c626dac2f82359d7c22ef378392-VideoMD-amd.xml'
    )

    assert os.path.isfile(filepath)


def test_main_utf8_files(testpath, run_cli):
    """Test for ``main`` function with filenames that contain non-ascii
    characters.
    """
    # Create sample data directory with file that has non-ascii characters in
    # filename
    os.makedirs(os.path.join(testpath, 'data'))
    relative_path = os.path.join('data', 'äöå.m1v')
    full_path = os.path.join(testpath, relative_path)
    shutil.copy('tests/data/video/valid_1.m1v', full_path)

    # Call main function with encoded filename as parameter
    run_cli(
        create_videomd.main, [
            '--workspace', testpath, '--base_path', testpath,
            fsencode_path(relative_path)
        ]
    )

    # Check that filename is found in md-reference file.
    refs = read_md_references(testpath, 'create-videomd-md-references.jsonl')
    assert refs["data/äöå.m1v"]


def test_existing_scraper_result(testpath):
    """Test that existing json file from import_object is used.
    We just need to check duration, since it's different from the real
    duration.
    """
    amdid = '36260c626dac2f82359d7c22ef378392'
    file_ = 'tests/data/video/valid_1.m1v'
    ref = {
        file_: {
            "path_type": "file",
            "streams": {},
            "md_ids": ["_" + amdid]
        }
    }
    with open(os.path.join(testpath,
                           'import-object-md-references.jsonl'), 'w') as out:
        json.dump(ref, out)

    stream_dict = {0: {
        'mimetype': 'video/mpeg', 'index': 0, 'par': '1', 'frame_rate': '30',
        'data_rate': '0.171304', 'bits_per_sample': '8',
        'data_rate_mode': 'Variable', 'color': 'Color',
        'codec_quality': 'lossy', 'signal_format': '(:unap)', 'dar': '1.778',
        'height': '180', 'sound': 'No', 'version': '1',
        'codec_name': 'MPEG Video',
        'codec_creator_app_version': '(:unav)',
        'duration': 'PT50S', 'sampling': '4:2:0', 'stream_type': 'video',
        'width': '320', 'codec_creator_app': '(:unav)'}}
    with open(os.path.join(testpath, ('%s-scraper.json' % amdid)), 'w') \
            as outfile:
        json.dump(stream_dict, outfile)

    videomd = create_videomd.create_videomd_metadata(
        file_, workspace=testpath
    )["0"]

    path = "/vmd:VIDEOMD/vmd:fileData/vmd:duration"
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT50S'


@pytest.mark.parametrize("file_, base_path", [
    ('tests/data/video/valid_1.m1v', ''),
    ('./tests/data/video/valid_1.m1v', ''),
    ('video/valid_1.m1v', 'tests/data'),
    ('./video/valid_1.m1v', './tests/data'),
    ('data/video/valid_1.m1v', 'absolute')
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
        run_cli(create_videomd.main, [
            '--workspace', testpath, '--base_path', base_path, file_])
    else:
        run_cli(create_videomd.main, [
            '--workspace', testpath, file_])

    references = read_md_references(
        testpath,
        'create-videomd-md-references.jsonl')
    assert os.path.normpath(file_) in references

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file_)))
