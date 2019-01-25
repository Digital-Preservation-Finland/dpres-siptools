# encoding: utf-8
"""Tests for ``siptools.scripts.create_mix`` module"""
import os
import sys
import shutil
import pytest
import lxml.etree
import siptools.scripts.create_mix as create_mix


def test_create_mix_techmdfile(testpath):
    """Test for ``create_mix_techmdfile`` function. Creates MIX techMD for
    three different image files. Two of the image files share the same MIX
    metadata, so only two MIX techMD files should be created in workspace.
    References to MIX techMD should be written into amd-references.xml file.
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

    # Count the references written to techMD reference file. There should be
    # one reference per image file.
    xml = lxml.etree.parse(os.path.join(testpath, 'amd-references.xml'))
    assert len(xml.xpath('//amdReference')) == 3


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

    # Run main function inside testpath. Siptools does not work if data is not
    # in current working directory
    last_path = os.getcwd()
    os.chdir(testpath)
    try:
        # Call main function with encoded filename as parameter
        create_mix.main(
            ['--workspace', testpath,
             image_relative_path.encode(sys.getfilesystemencoding())]
        )
    finally:
        os.chdir(last_path)

    # Check that filename is found in techMD reference file.
    xml = lxml.etree.parse(os.path.join(testpath, 'amd-references.xml'))
    assert len(xml.xpath(u'//amdReference[@file="data/äöå.tif"]')) == 1


def test_inspect_image():
    """Test for ``_inspect_image`` function. Pass a sample image file for
    function and check that expected metada is found.
    """

    # pylint: disable=protected-access
    metadata = create_mix._inspect_image(
        'tests/data/images/tiff1.tif'
    )

    # python-wand returns different values for versions 0.4.x and 0.5.x
    assert metadata["compression"] in ['b44a', 'no']

    assert metadata["byteorder"] == "little endian"
    assert metadata["width"] == "2"
    assert metadata["height"] == "2"
    assert metadata["colorspace"] == "srgb"
    assert metadata["bitspersample"] == "8"
    assert metadata["bpsunit"] == "integer"
    assert metadata["samplesperpixel"] == "3"


def test_create_mix():
    """Test ``create_mix`` function. Pass valid metadata dictionary to
    function and check that result XML element contains expected elements.
    """

    xml = create_mix.create_mix('tests/data/images/tiff1.tif')
    namespaces = {'ns0': "http://www.loc.gov/mix/v20"}

    # compression
    xpath = '/ns0:mix/ns0:BasicDigitalObjectInformation/ns0:Compression/'\
        'ns0:compressionScheme'
    # python-wand returns different values for versions 0.4.x and 0.5.x
    assert xml.xpath(xpath, namespaces=namespaces)[0].text in ["b44a", "no"]

    # byteorder
    xpath = '/ns0:mix/ns0:BasicDigitalObjectInformation/ns0:byteOrder'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "little endian"

    # width
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
        'ns0:BasicImageCharacteristics/ns0:imageWidth'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "2"

    # height
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
            'ns0:BasicImageCharacteristics/ns0:imageHeight'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "2"

    # colorspace
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
            'ns0:BasicImageCharacteristics/ns0:PhotometricInterpretation/'\
            'ns0:colorSpace'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "srgb"

    # bitspresample
    xpath = '/ns0:mix/ns0:ImageAssessmentMetadata/ns0:ImageColorEncoding/'\
            'ns0:BitsPerSample/ns0:bitsPerSampleValue'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "8"

    # bpsunit
    xpath = '/ns0:mix/ns0:ImageAssessmentMetadata/ns0:ImageColorEncoding/'\
            'ns0:BitsPerSample/ns0:bitsPerSampleUnit'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "integer"

    # samplesperpixel
    xpath = '/ns0:mix/ns0:ImageAssessmentMetadata/ns0:ImageColorEncoding/'\
            'ns0:samplesPerPixel'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "3"


def test_mix_multiple_images():
    """Test ``create_mix`` functions generates metadata for the largest image
    in the file if there are multiple images present.
    """
    xml = create_mix.create_mix("tests/data/images/multiple_images.tif")
    namespaces = {'ns0': "http://www.loc.gov/mix/v20"}

    # width
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
        'ns0:BasicImageCharacteristics/ns0:imageWidth'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "640"

    # height
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
            'ns0:BasicImageCharacteristics/ns0:imageHeight'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "400"


@pytest.mark.parametrize("file, base_path", [
    ('tests/data/images/tiff1.tif', ''),
    ('./tests/data/images/tiff1.tif', ''),
    ('images/tiff1.tif', 'tests/data'),
    ('./images/tiff1.tif', './tests/data'),
    ('data/images/tiff1.tif', 'absolute')
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
        create_mix.main(['--workspace', testpath, '--base_path',
                         base_path, file])
    else:
        create_mix.main(['--workspace', testpath, file])

    assert "file=\"" + os.path.normpath(file) + "\"" in \
        open(os.path.join(testpath, 'amd-references.xml')).read()

    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file)))
