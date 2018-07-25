# coding=utf-8
"""Command line tool for creating MIX metadata."""

import os
import argparse
import wand.image
import PIL.Image
import nisomix.mix
import siptools.utils

SAMPLES_PER_PIXEL = {'1': '1', 'L': '1', 'P': '1', 'RGB': '3', 'YCbCr': '3',
                     'LAB': '3', 'HSV': '3', 'RGBA': '4', 'CMYK': '4',
                     'I': '1', 'F': '1'}


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""
    parser = argparse.ArgumentParser(
        description="Tool for creating mix metadata for an image. The MIX "
                    "metadata is written to NISOIMG-<hash>-othermd.xml METS "
                    "XML file in the workspace directory. The MIX techMD "
                    "reference is written to techmd-references.xml. If "
                    "similar MIX metadata is already found in workspace, the "
                    "file will not be rewritten."
    )
    parser.add_argument('file', type=str,
                        help="Image file to be described as mix metadata")
    parser.add_argument('--workspace', type=str, default='./workspace/',
                        help="Workspace directory for the metadata files.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write MIX metadata for a image file."""
    args = parse_arguments(arguments)
    create_mix_techmdfile(args.file, args.workspace)


def create_mix_techmdfile(image_file, workspace):
    """Creates  MIX metadata for a image file, and writes it into a METS XML
    file in workspace. Adds MIX reference to techMD reference file used in
    compile-structmap script. If similar MIX metadata already exists in
    workspace, only the techMD reference to the MIX metadata is created for
    image file.

    :filename: Filename of image file
    :returns: None
    """
    # Create MIX metadata
    mix = create_mix(os.path.join(image_file))

    # Create METS XML file that contains MIX metadata
    techmd_id = siptools.utils.create_techmdfile(
        workspace, mix, 'NISOIMG', "2.0"
    )

    # Add reference from image file to techMD
    siptools.utils.add_techmdreference(workspace, techmd_id, image_file)


def _inspect_image(img):
    """Create metadata for image file. Use both Wand and Pillow modules to
    extract metadata from image file.

    :img: image file path
    :returns: image file metadata dictionary
    """
    metadata = {}

    with wand.image.Image(filename=img) as i:
        metadata["byteorder"] = None
        metadata["width"] = str(i.width)
        metadata["height"] = str(i.height)
        metadata["colorspace"] = str(i.colorspace)
        metadata["bitspersample"] = str(i.depth)
        metadata["compression"] = str(i.compression)
        for key, value in i.metadata.items():
            if key.startswith('tiff:endian'):
                if value == 'msb':
                    metadata["byteorder"] = 'big endian'
                elif value == 'lsb':
                    metadata["byteorder"] = 'little endian'

    with PIL.Image.open(img) as image:
        mode = image.mode
        if mode == 'F':
            metadata["bpsunit"] = 'floating point'
        else:
            metadata["bpsunit"] = 'integer'

        metadata["samplesperpixel"] = None

        if image.format == 'TIFF':
            tag_info = image.tag_v2
            if 277 in tag_info.keys():
                metadata["samplesperpixel"] = str(tag_info[277])
        elif image.format == 'JPEG':
            exif_info = image._getexif()
            if 277 in exif_info.keys():
                metadata["samplesperpixel"] = str(exif_info[277])

        if not metadata["samplesperpixel"]:
            metadata["samplesperpixel"] = SAMPLES_PER_PIXEL[mode]

    return metadata


def create_mix(image):
    """Create MIX metadata XML element for an image file.

    :image: image file
    :returns: MIX XML element
    """
    metadata = _inspect_image(image)

    mix_compression \
        = nisomix.mix.mix_Compression(
            compressionScheme=metadata["compression"]
        )

    basicdigitalobjectinformation \
        = nisomix.mix.mix_BasicDigitalObjectInformation(
            byteOrder=metadata["byteorder"],
            Compression_elements=[mix_compression]
        )

    basicimageinformation = nisomix.mix.mix_BasicImageInformation(
        imageWidth=metadata["width"],
        imageHeight=metadata["height"],
        colorSpace=metadata["colorspace"]
    )

    imageassessmentmetadata = nisomix.mix.mix_ImageAssessmentMetadata(
        bitsPerSampleValue_elements=metadata["bitspersample"],
        bitsPerSampleUnit=metadata["bpsunit"],
        samplesPerPixel=metadata["samplesperpixel"]
    )

    mix_root = nisomix.mix.mix_mix(
        BasicDigitalObjectInformation=basicdigitalobjectinformation,
        BasicImageInformation=basicimageinformation,
        ImageAssessmentMetadata=imageassessmentmetadata
    )

    return mix_root


if __name__ == '__main__':
    main()
