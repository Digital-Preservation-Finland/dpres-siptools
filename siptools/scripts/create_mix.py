# coding=utf-8
"""Command line tool for creating mix metadata."""

import os
import argparse
import wand.image
import PIL.Image
import nisomix.mix
import mets
import xml_helpers.utils
from siptools.utils import encode_path, encode_id


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""
    parser = argparse.ArgumentParser(
        description="Tool for creating mix metadata for an image. The MIX "
                    "metadata is written to "
                    "MIX<url-encoded-file-path>-othermd.xml -file in the "
                    "workspace directory."
    )
    parser.add_argument('filename', type=str,
                        help="Image file to be described as mix metadata")
    parser.add_argument('--workspace', type=str, default='./workspace/',
                        help="Workspace directory for the metadata files.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write MIX metadata for a image file."""
    args = parse_arguments(arguments)

    filename = encode_path(args.filename, prefix='MIX', suffix="-othermd.xml")
    fileid = encode_id(filename)
    mets_ = create_mix_techmd(args.filename, fileid)

    with open(os.path.join(args.workspace, filename), 'w+') as outfile:
        outfile.write(xml_helpers.utils.serialize(mets_))
    print "Wrote METS MIX technical metadata to file %s" % outfile.name


def create_mix_techmd(filename, fileid=None):
    """Creates METS XML element that contains techMD element with MIX metadata.

    :filename: Filename of MIX metadata file
    :fileid: ID of MIX metadata file
    :returns: METS XML element
    """
    mddata = create_mix(os.path.join(filename))
    if fileid is None:
        filename = encode_path(filename, prefix='MIX', suffix="-othermd.xml")
        fileid = encode_id(filename)
    mets_ = mets.mets()
    amdsec = mets.amdsec()
    techmd = mets.techmd(fileid)
    mdwrap = mets.mdwrap('NISOIMG', "2.0")
    xmldata = mets.xmldata()

    xmldata.append(mddata)
    mdwrap.append(xmldata)
    techmd.append(mdwrap)
    amdsec.append(techmd)
    mets_.append(amdsec)

    return mets_


def create_mix(img):
    """Create MIX technical metadata XML element for an image file. Use both
    Wand and Pillow modules to extract metadata from image file.

    :img: image file path
    :returns: MIX XML element
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

    with PIL.Image.open(img) as image:
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

    mix_compression \
        = nisomix.mix.mix_Compression(compressionScheme=compression)

    basicdigitalobjectinformation \
        = nisomix.mix.mix_BasicDigitalObjectInformation(
            byteOrder=byteorder,
            Compression_elements=[mix_compression]
        )

    basicimageinformation = nisomix.mix.mix_BasicImageInformation(
        imageWidth=width,
        imageHeight=height,
        colorSpace=colorspace)

    imageassessmentmetadata = nisomix.mix.mix_ImageAssessmentMetadata(
        bitsPerSampleValue_elements=bitspersample,
        bitsPerSampleUnit=bpsunit, samplesPerPixel=samplesperpixel)

    mix_root = nisomix.mix.mix_mix(
        BasicDigitalObjectInformation=basicdigitalobjectinformation,
        BasicImageInformation=basicimageinformation,
        ImageAssessmentMetadata=imageassessmentmetadata)

    return mix_root


if __name__ == '__main__':
    main()
