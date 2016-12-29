from tempfile import NamedTemporaryFile
import lxml.etree as ET
import siptools.xml.mix as miks
import siptools.xml.mets as m
from siptools.xml.namespaces import NAMESPACES
import pytest
import os
from urllib import quote_plus

def test_mix_ok(testpath):

    testpath = './workspace'
    target_filename = 'tests/data/structured/Software files/koodi.java'
    mets = m.mets_mets()
    techmd = m.techmd('techmd-mix-%s' % target_filename)
    mets.append(techmd)
    mix = miks.mix_mix()
    techmd.append(mix)
    compression = miks.mix_Compression(compressionScheme='JPEG 2000 Lossless',
            compressionSchemeLocalList=None, compressionSchemeLocalValue=None,
            compressionRatio='10')

    basicDigitalObjectInformation = miks.mix_BasicDigitalObjectInformation(byteOrder='big endian',
            Compression_elements=[compression])

    basicImageInformation = miks.mix_BasicImageInformation(imageWidth=1024,
            imageHeight=768, colorSpace='ICCBased', iccProfileName='Adobe RGB',
            iccProfileVersion='1998',
            iccProfileURI='http://www.adobe.com/digitalimag/adobergb.html',
            qualityLayers=12, resolutionLevels=6)

    mix.append(basicDigitalObjectInformation)
    mix.append(basicImageInformation)

    print m.serialize(mets)

    target_filename = quote_plus(os.path.splitext(target_filename)[0]) + '-mix-techmd.xml'
    output_file = os.path.join(testpath, target_filename)
    print "output_file:%s" % output_file
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(m.serialize(mets))

    tree = ET.parse(output_file)
    root = tree.getroot()

    assert root.xpath("/mets:mets/mets:techMD/mix:mix/mix:BasicDigitalObjectInformation/mix:byteOrder",
            namespaces=NAMESPACES)[0].text == 'big endian'
    assert root.xpath("/mets:mets/mets:techMD/mix:mix/mix:BasicDigitalObjectInformation/mix:Compression/mix:compressionScheme",
            namespaces=NAMESPACES)[0].text == 'JPEG 2000 Lossless'
    assert root.xpath("/mets:mets/mets:techMD/mix:mix/mix:BasicDigitalObjectInformation/mix:Compression/mix:compressionRatio",
            namespaces=NAMESPACES)[0].text == '10'
