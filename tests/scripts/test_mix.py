from tempfile import NamedTemporaryFile
import lxml.etree as ET
import nisomix.mix as miks
import mets as m
from siptools.xml.mets import NAMESPACES
import xml_helpers.utils as h
import pytest
import os
from urllib import quote_plus


def test_mix_ok(testpath):

    target_filename = 'tests/data/structured'
    mets = m.mets()
    techmd = m.techmd('techmd-mix-%s' % target_filename)
    mets.append(techmd)
    mix = miks.mix_mix()
    techmd.append(mix)
    compression = miks.mix_Compression(compressionScheme='JPEG 2000 Lossless',
                                       compressionRatio='10')

    basicDigitalObjectInformation = miks.mix_BasicDigitalObjectInformation(byteOrder='big endian',
                                                                           Compression_elements=[compression])

    basicImageInformation = miks.mix_BasicImageInformation(imageWidth='1024',
                                                           imageHeight='768', colorSpace='ICCBased', iccProfileName='Adobe RGB',
                                                           iccProfileVersion='1998',
                                                           iccProfileURI='http://www.adobe.com/digitalimag/adobergb.html',
                                                           qualityLayers='12', resolutionLevels='6')

    imageAssessmentMetadata = miks.mix_ImageAssessmentMetadata(bitsPerSampleValue_elements=['16, 16, 16'],
                                                               bitsPerSampleUnit='integer', samplesPerPixel='4',
                                                               extraSamples_elements=[
        'unspecified data'],
        colormapReference='http://foo.bar')

    mix.append(basicDigitalObjectInformation)
    mix.append(basicImageInformation)
    mix.append(imageAssessmentMetadata)

    target_filename = quote_plus(os.path.splitext(
        target_filename)[0]) + '-mix-techmd.xml'
    output_file = os.path.join(testpath, target_filename)
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(h.serialize(mets))

    tree = ET.parse(output_file)
    root = tree.getroot()

    assert root.xpath("/mets:mets/mets:techMD/mix:mix/mix:BasicDigitalObjectInformation/mix:byteOrder",
                      namespaces=NAMESPACES)[0].text == 'big endian'
    assert root.xpath("/mets:mets/mets:techMD/mix:mix/mix:BasicDigitalObjectInformation/mix:Compression/mix:compressionScheme",
                      namespaces=NAMESPACES)[0].text == 'JPEG 2000 Lossless'
    assert root.xpath("/mets:mets/mets:techMD/mix:mix/mix:BasicDigitalObjectInformation/mix:Compression/mix:compressionRatio",
                      namespaces=NAMESPACES)[0].text == '10'
