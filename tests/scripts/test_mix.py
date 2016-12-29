from tempfile import NamedTemporaryFile
import lxml.etree as ET
import siptools.xml.mix as miks
from siptools.xml.namespaces import NAMESPACES
import pytest
import os

def test_mix_ok(testpath):

    mix = miks.mix_mix()
    compression = miks.mix_Compression(compressionScheme='JPEG 2000 Lossless',
            compressionSchemeLocalList=None, compressionSchemeLocalValue=None,
            compressionRatio='10')

    basicDigitalObjectInformation = miks.mix_BasicDigitalObjectInformation(byteOrder='big endian',
            Compression_elements=[compression])

    mix.append(basicDigitalObjectInformation)

    print miks.serialize(mix)

    output_file = os.path.join(testpath, 'mix.xml')
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(miks.serialize(mix))

    tree = ET.parse(output_file)
    root = tree.getroot()

    assert root.xpath("/mix:mix/mix:BasicDigitalObjectInformation/mix:byteOrder",
            namespaces=NAMESPACES)[0].text == 'big endian'
    assert root.xpath("/mix:mix/mix:BasicDigitalObjectInformation/mix:Compression/mix:compressionScheme",
            namespaces=NAMESPACES)[0].text == 'JPEG 2000 Lossless'
    assert root.xpath("/mix:mix/mix:BasicDigitalObjectInformation/mix:Compression/mix:compressionRatio",
            namespaces=NAMESPACES)[0].text == '10'
