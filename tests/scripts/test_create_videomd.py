"""Tests for ``siptools.scripts.create_videomd`` module"""

import os.path
import pytest
import lxml.etree as ET

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
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '0'

    path = "%s/vmd:compression/vmd:codecCreatorApp" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:compression/vmd:codecCreatorAppVersion" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:compression/vmd:codecName" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == \
        'MPEG-1 video'

    path = "%s/vmd:compression/vmd:codecQuality" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

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
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '4/3'

    path = "%s/vmd:sampling" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '4:2:0'

    path = "%s/vmd:duration" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT19.03S'

    path = "%s/vmd:signalFormat" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:sound" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'No'


def test_stream():
    """Test that ``create_videomd`` returns valid videomd from a
       video container.
    """

    videomd = create_videomd.create_videomd(
        "tests/data/video/mp4.mp4")["0"]

    file_data = "/vmd:VIDEOMD/vmd:fileData"

    path = "%s/vmd:bitsPerSample" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '8'

    path = "%s/vmd:compression/vmd:codecCreatorApp" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:compression/vmd:codecCreatorAppVersion" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:compression/vmd:codecName" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == \
        'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10'

    path = "%s/vmd:compression/vmd:codecQuality" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

    path = "%s/vmd:dataRate" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1.21'

    path = "%s/vmd:dataRateMode" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Fixed'

    path = "%s/vmd:color" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'Color'

    path = "%s/vmd:frame/vmd:pixelsHorizontal" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1280'

    path = "%s/vmd:frame/vmd:pixelsVertical" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '720'

    path = "%s/vmd:frame/vmd:PAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '1'

    path = "%s/vmd:frame/vmd:DAR" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '16/9'

    path = "%s/vmd:sampling" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '4:2:0'

    path = "%s/vmd:duration" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == 'PT5.28S'

    path = "%s/vmd:signalFormat" % file_data
    assert videomd.xpath(path, namespaces=NAMESPACES)[0].text == '(:unav)'

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
        testpath, '8b8e24235c6cf62922219ec71aa9f927-VideoMD-amd.xml'
    )

    assert os.path.isfile(filepath)


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
