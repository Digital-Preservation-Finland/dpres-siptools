# coding=utf-8
"""Command line tool for creating MIX metadata."""

import os
import sys
import argparse
import wand.image
import PIL.Image
import nisomix.mix
from siptools.utils import TechmdCreator

SAMPLES_PER_PIXEL = {'1': '1', 'L': '1', 'P': '1', 'RGB': '3', 'YCbCr': '3',
                     'LAB': '3', 'HSV': '3', 'RGBA': '4', 'CMYK': '4',
                     'I': '1', 'F': '1'}


def str_to_unicode(string):
    """Convert string to unicode string. Assumes that string encoding is the
    encoding of filesystem (unicode() assumes ASCII by default).

    :param string: encoded string
    :returns: decoded string
    """
    return unicode(string, sys.getfilesystemencoding())


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""
    parser = argparse.ArgumentParser(
        description="Tool for creating mix metadata for an image. The MIX "
                    "metadata is written to <hash>-NISOIMG-techmd.xml METS "
                    "XML file in the workspace directory. The MIX techMD "
                    "reference is written to techmd-references.xml. If "
                    "similar MIX metadata is already found in workspace, the "
                    "file will not be rewritten."
    )
    parser.add_argument('file', type=str_to_unicode,
                        help="Path to the image file")
    parser.add_argument('--workspace', type=str_to_unicode,
                        default='./workspace/',
                        help="Workspace directory for the metadata files.")
    parser.add_argument('--base_path', type=str, default='',
                        help="Source base path of digital objects. If used, "
                             "give path to the image file in relation to "
                             "this base path.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write MIX metadata for a image file."""
    args = parse_arguments(arguments)

    filerel = os.path.normpath(args.file)
    filepath = os.path.normpath(os.path.join(args.base_path, args.file))

    creator = MixCreator(args.workspace)
    creator.add_mix_md(filepath, filerel)
    creator.write()


class MixCreator(TechmdCreator):
    """Subclass of TechmdCreator, which generates MIX metadata for image files.
    """

    def add_mix_md(self, image_file, file_relpath=None):
        """Creates  MIX metadata for an image file and append it
        to self.md_elements

        :image_file: path to image file
        :file_relpath: relative path to image file to write to reference file
        :returns: None
        """

        # Create MIX metadata
        mix = create_mix(os.path.join(image_file))
        self.add_md(mix, file_relpath if file_relpath else image_file)

    # Change the default write parameters
    def write(self, mdtype="NISOIMG", mdtypeversion="2.0", othermdtype=None):
        super(MixCreator, self).write(mdtype, mdtypeversion, othermdtype)


def _find_largest_img(img):
    """Iterate over all images in the image file and return the index
    of the largest image file.

    :img: wand.image.Image instance
    :returns: Index of the largest image
    """

    largest_size = 0
    idx = 0

    for i, image in enumerate(img.sequence):
        size = image.width * image.height

        if size > largest_size:
            largest_size = size
            idx = i

    return idx


def _inspect_image(img):
    """Create metadata for image file. Use both Wand and Pillow modules to
    extract metadata from image file.

    :img: image file path
    :returns: image file metadata dictionary
    """
    metadata = {}
    idx = 0

    with wand.image.Image(filename=img) as i:

        if len(i.sequence) > 1:
            idx = _find_largest_img(i)

        image = i.sequence[idx]

        metadata["byteorder"] = None
        metadata["width"] = str(image.width)
        metadata["height"] = str(image.height)
        metadata["colorspace"] = str(image.colorspace)
        metadata["bitspersample"] = str(image.depth)
        metadata["compression"] = str(i.compression)

        for key, value in i.metadata.items():
            if key.startswith('tiff:endian'):
                if value == 'msb':
                    metadata["byteorder"] = 'big endian'
                elif value == 'lsb':
                    metadata["byteorder"] = 'little endian'

    with PIL.Image.open(img) as image:

        image.seek(idx)
        mode = image.mode
        if mode == 'F':
            metadata["bpsunit"] = 'floating point'
        else:
            metadata["bpsunit"] = 'integer'

        metadata["samplesperpixel"] = None

        if image.format == 'TIFF':
            tag_info = image.tag_v2
            if tag_info and 277 in tag_info.keys():
                metadata["samplesperpixel"] = str(tag_info[277])
        elif image.format == 'JPEG':
            exif_info = image._getexif()
            if exif_info and 277 in exif_info.keys():
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
    main(sys.argv[1:])
