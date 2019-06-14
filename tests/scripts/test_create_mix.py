# encoding: utf-8
"""Tests for ``siptools.scripts.create_mix`` module"""
import os
import sys
import shutil
import pickle
import pytest
import lxml.etree
from click.testing import CliRunner
import siptools.scripts.create_mix as create_mix


def test_create_mix_techmdfile(testpath):
    """Test for ``create_mix_techmdfile`` function. Creates MIX techMD for
    three different image files. Two of the image files share the same MIX
    metadata, so only two MIX techMD files should be created in workspace.
    References to MIX techMD should be written into md-references.xml file.
    """

    creator = create_mix.MixCreator(testpath)

    os.makedirs(os.path.join(testpath, 'data'))
    for image in ['tiff1.tif', 'tiff2.tif', 'tiff1_compressed.tif']:
        # copy sample image into data directory in temporary workspace
        image_path = os.path.join(testpath, 'data/%s' % image)
        shutil.copy('tests/data/images/%s' % image, image_path)

        # Add metadata
        creator.add_mix_md(image_path)

    # Write metadata
    creator.write()

    # Count the MIX techMD files, i.e. the files with "NISOIMG-" prefix. There
    # should two of them since tiff1.tif and tiff2.tif share the same MIX
    # metadata.
    files = os.listdir(testpath)
    assert len([x for x in files if x.endswith('NISOIMG-amd.xml')]) == 2

    # Count the references written to md-reference file. There should be
    # one reference per image file.
    xml = lxml.etree.parse(os.path.join(testpath, 'md-references.xml'))
    assert len(xml.xpath('//mdReference')) == 3


def test_main_utf8_files(testpath):
    """Test for ``main`` function with filenames that contain non-ascii
    characters.
    """
    # Create sample data directory with image that has non-ascii characters in
    # filename
    os.makedirs(os.path.join(testpath, 'data'))
    image_relative_path = os.path.join('data', u'äöå.tif')
    image_full_path = os.path.join(testpath, image_relative_path)
    shutil.copy('tests/data/images/tiff1.tif', image_full_path)

    # Call main function with encoded filename as parameter
    runner = CliRunner()
    runner.invoke(
        create_mix.main, [
            '--workspace', testpath, '--base_path', testpath,
            image_relative_path.encode(sys.getfilesystemencoding())
        ]
    )

    # Check that filename is found in md-reference file.
    xml = lxml.etree.parse(os.path.join(testpath, 'md-references.xml'))
    assert len(xml.xpath(u'//mdReference[@file="data/äöå.tif"]')) == 1


def test_create_mix():
    """Test ``create_mix`` function. Pass valid metadata dictionary to
    function and check that result XML element contains expected elements.
    """

    xml = create_mix.create_mix_metadata('tests/data/images/tiff1.tif')
    namespaces = {'mix': "http://www.loc.gov/mix/v20"}

    # compression
    xpath = '/mix:mix/mix:BasicDigitalObjectInformation/mix:Compression/'\
        'mix:compressionScheme'
    # python-wand returns different values for versions 0.4.x and 0.5.x
    assert xml.xpath(xpath, namespaces=namespaces)[0].text in ["b44a", "no"]

    # byteorder
    xpath = '/mix:mix/mix:BasicDigitalObjectInformation/mix:byteOrder'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "little endian"

    # width
    xpath = '/mix:mix/mix:BasicImageInformation/'\
        'mix:BasicImageCharacteristics/mix:imageWidth'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "2"

    # height
    xpath = '/mix:mix/mix:BasicImageInformation/'\
            'mix:BasicImageCharacteristics/mix:imageHeight'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "2"

    # colorspace
    xpath = '/mix:mix/mix:BasicImageInformation/'\
            'mix:BasicImageCharacteristics/mix:PhotometricInterpretation/'\
            'mix:colorSpace'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "srgb"

    # bitspresample
    xpath = '/mix:mix/mix:ImageAssessmentMetadata/mix:ImageColorEncoding/'\
            'mix:BitsPerSample/mix:bitsPerSampleValue'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "8"

    # bpsunit
    xpath = '/mix:mix/mix:ImageAssessmentMetadata/mix:ImageColorEncoding/'\
            'mix:BitsPerSample/mix:bitsPerSampleUnit'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "integer"

    # samplesperpixel
    xpath = '/mix:mix/mix:ImageAssessmentMetadata/mix:ImageColorEncoding/'\
            'mix:samplesPerPixel'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "3"


def test_existing_scraper_result(testpath):
    """Test that existing pickle file from import_object is used.
    We just need to check width, since it's different from the real one.
    """
    amdid = 'f54380dfc2960793badf5e81c9b1627c'
    file_ = 'tests/data/images/tiff1.tif'
    namespaces = {'mix': "http://www.loc.gov/mix/v20"}
    xml = """<?xml version='1.0' encoding='UTF-8'?>
          <mdReferences>
          <mdReference file="%s">_%s</mdReference>
          </mdReferences>""" % (file_, amdid)
    with open(os.path.join(testpath, 'md-references.xml'), 'w') as out:
        out.write(xml)

    stream_dict = {0: {
        'bps_unit': 'integer', 'bps_value': '8', 'colorspace': 'srgb',
        'compression': 'lzw', 'height': '400', 'mimetype': 'image/tiff',
        'samples_per_pixel': '3', 'stream_type': 'image', 'version': '6.0',
        'width': '1234', 'byte_order': 'little endian'}}
    with open(os.path.join(testpath, ('%s-scraper.pkl' % amdid)), 'wb') \
            as outfile:
        pickle.dump(stream_dict, outfile)

    mix = create_mix.create_mix_metadata(file_, workspace=testpath)
    path = "//mix:imageWidth"
    assert mix.xpath(path, namespaces=namespaces)[0].text == '1234'


def test_mix_multiple_images():
    """Test ``create_mix`` functions raises error if there are multiple
    images present.
    """
    with pytest.raises(ValueError):
        create_mix.create_mix_metadata("tests/data/images/multiple_images.tif")


@pytest.mark.parametrize("file_, base_path", [
    ('tests/data/images/tiff1.tif', ''),
    ('./tests/data/images/tiff1.tif', ''),
    ('images/tiff1.tif', 'tests/data'),
    ('./images/tiff1.tif', './tests/data'),
    ('data/images/tiff1.tif', 'absolute')
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
        runner.invoke(create_mix.main, [
            '--workspace', testpath, '--base_path', base_path, file_])
    else:
        runner.invoke(create_mix.main, [
            '--workspace', testpath, file_])

    assert "file=\"" + os.path.normpath(file_) + "\"" in \
        open(os.path.join(testpath, 'md-references.xml')).read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file_)))
