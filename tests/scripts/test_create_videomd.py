"""Tests for ``siptools.scripts.create_videomd`` module"""

import os.path
import pytest
import lxml.etree as ET
import pickle
import siptools.scripts.create_videomd as create_videomd

VIDEOMD_NS = 'http://www.loc.gov/videoMD/'
NAMESPACES = {"vmd": VIDEOMD_NS}


def test_create_videomd_elem():
    """Test that ``create_videomd`` returns valid videomd.
    """

    videomd = create_videomd.create_videomd(
        "tests/data/video/mpg1.mpg")["0"]

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
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == \
        'MPEG Video'

    path = "%s/vmd:compression/vmd:codecQuality" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'lossy'

    path = "%s/vmd:dataRate" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '0.32'

    path = "%s/vmd:dataRateMode" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Fixed'

    path = "%s/vmd:color" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Color'

    path = "%s/vmd:frame/vmd:pixelsHorizontal" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '320'

    path = "%s/vmd:frame/vmd:pixelsVertical" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '240'

    path = "%s/vmd:frame/vmd:PAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1'

    path = "%s/vmd:frame/vmd:DAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1.333'

    path = "%s/vmd:sampling" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '4:2:0'

    path = "%s/vmd:duration" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT19.02S'

    path = "%s/vmd:signalFormat" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unap)'

    path = "%s/vmd:sound" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'No'


def test_stream():
    """Test that ``create_videomd`` returns valid videomd from a
       video container.
    """

    videomd = create_videomd.create_videomd(
        "tests/data/video/mp4.mp4")["1"]

    file_data = "/vmd:VIDEOMD/vmd:fileData"

    path = "%s/vmd:bitsPerSample" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '8'

    path = "%s/vmd:compression/vmd:codecCreatorApp" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Lavf53.24.2'

    path = "%s/vmd:compression/vmd:codecCreatorAppVersion" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '53.24.2'

    path = "%s/vmd:compression/vmd:codecName" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'AVC'

    path = "%s/vmd:compression/vmd:codecQuality" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'lossy'

    path = "%s/vmd:dataRate" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1.205959'

    path = "%s/vmd:dataRateMode" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Variable'

    path = "%s/vmd:color" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Color'

    path = "%s/vmd:frame/vmd:pixelsHorizontal" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1280'

    path = "%s/vmd:frame/vmd:pixelsVertical" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '720'

    path = "%s/vmd:frame/vmd:PAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1'

    path = "%s/vmd:frame/vmd:DAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1.778'

    path = "%s/vmd:sampling" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '4:2:0'

    path = "%s/vmd:duration" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT5.28S'

    path = "%s/vmd:signalFormat" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unap)'

    path = "%s/vmd:sound" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Yes'


def test_invalid_file():
    """Test that calling create_videomd() for file that can not be parsed
    raises ValueError
    """
    with pytest.raises(ValueError):
        create_videomd.create_videomd("non-existent.mpg")


def test_create_videomd(testpath):
    """Test that ``create_videomd`` writes VideoMD file and
    amd-reference file.
    """
    creator = create_videomd.VideomdCreator(testpath)

    # Debug print
    print "\n\n%s" % ET.tostring(
        create_videomd.create_videomd("tests/data/video/mpg1.mpg")["0"],
        pretty_print=True
    )

    # Append same file twice
    creator.add_videomd_md("tests/data/video/mpg1.mpg")
    creator.add_videomd_md("tests/data/video/mpg1.mpg")

    creator.write()

    # Check that amdreference and one VideoMD-amd files are created
    assert os.path.isfile(os.path.join(testpath, 'amd-references.xml'))

    filepath = os.path.join(
        testpath, '1276adbe0c85be09d0416ce04fbc1e87-VideoMD-amd.xml'
    )

    assert os.path.isfile(filepath)


def test_existing_scraper_result(testpath):
    """Test that existing pickle file from import_object is used.
    We just need to check duration, since it's different from the real
    duration.
    """
    amdid = '1276adbe0c85be09d0416ce04fbc1e87'
    file_ = 'tests/data/video/mpg1.mpg'
    xml = """<?xml version='1.0' encoding='UTF-8'?>
          <amdReferences>
          <amdReference file="%s">_%s</amdReference>
          </amdReferences>""" % (file_, amdid)
    with open(os.path.join(testpath, 'amd-references.xml'), 'w') as out:
        out.write(xml)

    stream_dict = {0: {
        'mimetype': 'video/mpeg', 'index': 0, 'par': '1', 'frame_rate': '30',
        'data_rate': '0.171304', 'bits_per_sample': '8',
        'data_rate_mode':'Variable', 'color': 'Color',
        'codec_quality': 'lossy', 'signal_format': '(:unap)', 'dar': '1.778',
        'height': '180', 'sound': 'No', 'version': '1',
        'codec_name': 'MPEG Video',
        'codec_creator_app_version': '(:unav)',
        'duration': 'PT50S', 'sampling': '4:2:0', 'stream_type': 'video',
        'width': '320', 'codec_creator_app': '(:unav)'}}
    with open(os.path.join(testpath, ('%s-scraper.pkl' % amdid)), 'wb') \
            as outfile:
        pickle.dump(stream_dict, outfile)

    videomd = create_videomd.create_videomd(file_, workspace=testpath)["0"]

    path = "/vmd:VIDEOMD/vmd:fileData/vmd:duration"
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT50S'


@pytest.mark.parametrize("file, base_path", [
    ('tests/data/video/mpg1.mpg', ''),
    ('./tests/data/video/mpg1.mpg', ''),
    ('video/mpg1.mpg', 'tests/data'),
    ('./video/mpg1.mpg', './tests/data'),
    ('data/video/mpg1.mpg', 'absolute')
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
        create_videomd.main(['--workspace', testpath, '--base_path',
                             base_path, file])
    else:
        create_videomd.main(['--workspace', testpath, file])

    assert "file=\"" + os.path.normpath(file) + "\"" in \
        open(os.path.join(testpath, 'amd-references.xml')).read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file)))
