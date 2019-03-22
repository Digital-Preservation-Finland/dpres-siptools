# coding=utf-8
"""Command line tool for creating MIX metadata."""

import os
import sys
import argparse
import pickle
import nisomix.mix
from siptools.utils import AmdCreator, scrape_file

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
                    "metadata is written to <hash>-NISOIMG-amd.xml METS "
                    "XML file in the workspace directory. The MIX techMD "
                    "reference is written to amd-references.xml. If "
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


class MixCreator(AmdCreator):
    """Subclass of AmdCreator, which generates MIX metadata for image files.
    """

    def add_mix_md(self, filepath, filerel=None):
        """Creates  MIX metadata for an image file and append it
        to self.md_elements

        :image_file: path to image file
        :file_relpath: relative path to image file to write to reference file
        :returns: None
        """

        # Create MIX metadata
        mix_dict = create_mix(filepath, filerel, self.workspace)

        for index in mix_dict.keys():
            if '0' in mix_dict and len(mix_dict) == 1:
                self.add_md(mix_dict[index],
                            filerel if filerel else filepath)
            else:
                self.add_md(mix_dict[index],
                            filerel if filerel else filepath, index)

    # Change the default write parameters
    def write(self, mdtype="NISOIMG", mdtypeversion="2.0", othermdtype=None):
        super(MixCreator, self).write(mdtype, mdtypeversion, othermdtype)


def create_mix(filename, filerel=None, workspace=None):
    """Create MIX metadata XML element for an image file.

    :image: image file
    :returns: MIX XML element
    """
    streams = scrape_file(filename, filerel=filerel, workspace=workspace)

    mix_dict = {}
    for index, stream_md in streams.iteritems():
        if stream_md['stream_type'] != 'image':
            continue

        mix_compression = nisomix.mix.mix_Compression(
            compressionScheme=stream_md["compression"])

        if not 'byte_order' in stream_md:
            byte_order = None
        else:
            byte_order = stream_md["byte_order"]
        basicdigitalobjectinformation \
            = nisomix.mix.mix_BasicDigitalObjectInformation(
                byteOrder=byte_order,
                Compression_elements=[mix_compression])

        basicimageinformation = nisomix.mix.mix_BasicImageInformation(
            imageWidth=stream_md["width"],
            imageHeight=stream_md["height"],
            colorSpace=stream_md["colorspace"])

        imageassessmentmetadata = nisomix.mix.mix_ImageAssessmentMetadata(
            bitsPerSampleValue_elements=stream_md["bps_value"],
            bitsPerSampleUnit=stream_md["bps_unit"],
            samplesPerPixel=stream_md["samples_per_pixel"]
        )

        mix_root = nisomix.mix.mix_mix(
            BasicDigitalObjectInformation=basicdigitalobjectinformation,
            BasicImageInformation=basicimageinformation,
            ImageAssessmentMetadata=imageassessmentmetadata
        )
        mix_dict[str(index)] = mix_root

    if not mix_dict:
        raise ValueError('Image stream info could not be constructed.')

    return mix_dict


if __name__ == '__main__':
    main(sys.argv[1:])
