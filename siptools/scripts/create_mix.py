# coding=utf-8
""" Command line tool for creating mix
"""

import os
import sys
import wand.image
from PIL import Image
import argparse
import nisomix.mix as mix
import mets as m
import xml_helpers.utils as h
from siptools.utils import encode_path, encode_id


def parse_arguments(arguments):
    """Parse arguments
    """
    parser = argparse.ArgumentParser(
        description="Tool for creating mix metadata for an image")
    parser.add_argument('filename', type=str,
        help="Image file to be described as mix metadata")
    parser.add_argument(
        '--workspace', type=str, default='./workspace/',
        help="Workspace directory for the metadata files.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    #mddata = write_mix(os.path.join(args.workspace, args.filename))
    filename = encode_path(args.filename, prefix='mix-', suffix="-othermd.xml")
    fileid = encode_id(filename)
    mets = create_mix_techmd(args.filename, fileid)

    with open(os.path.join(args.workspace, filename), 'w+') as outfile:
        outfile.write(h.serialize(mets))
    print "Wrote METS MIX technical metadata to file %s" % outfile.name


def create_mix_techmd(filename, fileid=None):
    mddata = write_mix(os.path.join(filename))
    if fileid is None:
      filename = encode_path(filename, prefix='mix-', suffix="-othermd.xml")
      fileid = encode_id(filename)
    mets = m.mets()
    amdsec = m.amdsec()
    techmd = m.techmd(fileid)
    mdwrap = m.mdwrap('NISOIMG', "2.0")
    xmldata = m.xmldata()

    xmldata.append(mddata)
    mdwrap.append(xmldata)
    techmd.append(mdwrap)
    amdsec.append(techmd)
    mets.append(amdsec)

    return mets


def write_mix(img):
    """Write MIX technical metadata if it's an image file. Use both
    Wand and Pillow modules to extract metadata from image file.
    """
    with wand.image.Image(filename=img) as i:
        byteorder = None
        width = str(i.width)
        height = str(i.height)
        colorspace = str(i.colorspace)
        bitspersample = str(i.depth)
        compression = str(i.compression)
        metadata = i.metadata.items()
        for key, value in metadata:
            if key.startswith('tiff:endian'):
                if value == 'msb':
                    byteorder = 'big endian'
                elif value == 'lsb':
                    byteorder = 'little endian'

    with Image.open(img) as image:
        mode = image.mode
        if mode == 'F':
            bpsunit = 'floating point'
        else:
            bpsunit = 'integer'

        samplesperpixel = None

        if image.format == 'TIFF':
            tag_info = image.tag_v2
            if tag_info:
                for tag, value in tag_info.items():
                    if tag == 277:
                        samplesperpixel = str(value)
        elif image.format == 'JPEG':
            exif_info = image._getexif()
            if exif_info:
                for tag, value in exif_info.items():
                    if tag == 277:
                        samplesperpixel = str(value)

        if not samplesperpixel:
            modes = {'1': '1', 'L': '1', 'P': '1', 'RGB': '3', 'YCbCr': '3',
                     'LAB': '3', 'HSV': '3', 'RGBA': '4', 'CMYK': '4',
                     'I': '1', 'F': '1'}
            for key, value in modes.items():
                if key == mode:
                    samplesperpixel = value

    mix_compression = mix.mix_Compression(compressionScheme=compression)

    basicdigitalobjectinformation = mix.mix_BasicDigitalObjectInformation(
        byteOrder=byteorder, Compression_elements=[mix_compression])

    basicimageinformation = mix.mix_BasicImageInformation(
        imageWidth=width,
        imageHeight=height,
        colorSpace=colorspace)

    imageassessmentmetadata = mix.mix_ImageAssessmentMetadata(
        bitsPerSampleValue_elements=bitspersample,
        bitsPerSampleUnit=bpsunit, samplesPerPixel=samplesperpixel)

    mix_root = mix.mix_mix(
        BasicDigitalObjectInformation=basicdigitalobjectinformation,
        BasicImageInformation=basicimageinformation,
        ImageAssessmentMetadata=imageassessmentmetadata)

    return mix_root


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)

