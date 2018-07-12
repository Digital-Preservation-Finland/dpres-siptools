"""Tests for ``siptools.scripts.create_mix`` module"""
import os
import shutil
import lxml.etree
import siptools.scripts.create_mix


def test_create_mix_techmdfile(testpath):
    """Test for ``create_mix_techmdfile`` function. Creates MIX techMD for
    three different image files. Two of the image files share the same MIX
    metadata, so only two MIX techMD files should be created in workspace.
    References to MIX techMD should be written into techmd-references.xml file.
    """
    os.makedirs(os.path.join(testpath, 'data'))
    for image in ['tiff1.tif', 'tiff2.tif', 'tiff1_compressed.tif']:
        # copy sample image into data directory in temporary workspace
        image_path = os.path.join(testpath, 'data/%s' % image)
        shutil.copy('tests/data/images/%s' % image, image_path)

        # create techmd file and add reference
        siptools.scripts.create_mix.create_mix_techmdfile(image_path, testpath)

    # Count the MIX techMD files, i.e. the files with "mix-" prefix. There
    # should two of them since tiff1.tif and tiff2.tif share the same MIX
    # metadata.
    assert len([x for x in os.listdir(testpath) if x.startswith('mix-')]) == 2

    # Count the references written to techMD reference file. There should be
    # one reference per image file.
    xml = lxml.etree.parse(os.path.join(testpath, 'techmd-references.xml'))
    assert len(xml.xpath('//techmdReference')) == 3


def test_inspect_image():
    """Test for ``_inspect_image`` function. Pass a sample image file for
    function and check that expected metada is found.
    """

    # pylint: disable=protected-access
    metadata = siptools.scripts.create_mix._inspect_image(
        'tests/data/images/tiff1.tif'
    )

    assert metadata["compression"] == 'b44a'
    assert metadata["byteorder"] == "little endian"
    assert metadata["width"] == "2"
    assert metadata["height"] == "2"
    assert metadata["colorspace"] == "srgb"
    assert metadata["bitspersample"] == "8"
    assert metadata["bpsunit"] == "integer"
    assert metadata["samplesperpixel"] == "3"


def test_create_mix():
    """Test ``_create_mix`` function. Pass valid metadata dictionary to
    function and check that result XML element contains expected elements.
    """
    metadata = {"compression": "foo",
                "byteorder": "foo",
                "width": "foo",
                "height": "foo",
                "colorspace": "foo",
                "bitspersample": "1",
                "bpsunit": "foo",
                "samplesperpixel": "foo"}

    # pylint: disable=protected-access
    xml = siptools.scripts.create_mix._create_mix(metadata)
    namespaces = {'ns0': "http://www.loc.gov/mix/v20"}

    # compression
    xpath = '/ns0:mix/ns0:BasicDigitalObjectInformation/ns0:Compression/'\
        'ns0:compressionScheme'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "foo"

    # byteorder
    xpath = '/ns0:mix/ns0:BasicDigitalObjectInformation/ns0:byteOrder'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "foo"

    # width
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
        'ns0:BasicImageCharacteristics/ns0:imageWidth'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "foo"

    # height
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
            'ns0:BasicImageCharacteristics/ns0:imageHeight'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "foo"

    # colorspace
    xpath = '/ns0:mix/ns0:BasicImageInformation/'\
            'ns0:BasicImageCharacteristics/ns0:PhotometricInterpretation/'\
            'ns0:colorSpace'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "foo"

    # bitspresample
    xpath = '/ns0:mix/ns0:ImageAssessmentMetadata/ns0:ImageColorEncoding/'\
            'ns0:BitsPerSample/ns0:bitsPerSampleValue'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "1"

    # bpsunit
    xpath = '/ns0:mix/ns0:ImageAssessmentMetadata/ns0:ImageColorEncoding/'\
            'ns0:BitsPerSample/ns0:bitsPerSampleUnit'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "foo"

    # samplesperpixel
    xpath = '/ns0:mix/ns0:ImageAssessmentMetadata/ns0:ImageColorEncoding/'\
            'ns0:samplesPerPixel'
    assert xml.xpath(xpath, namespaces=namespaces)[0].text == "foo"
