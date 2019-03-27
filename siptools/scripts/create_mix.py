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
        mix = create_mix(filepath, filerel, self.workspace)
        if mix is not None:
            self.add_md(mix, filerel if filerel else filepath)

    # Change the default write parameters
    def write(self, mdtype="NISOIMG", mdtypeversion="2.0", othermdtype=None):
        super(MixCreator, self).write(mdtype, mdtypeversion, othermdtype)


def check_missing_metadata(stream, filename):
    """If an element is none, use value (:unav) if allowed in the
    specifications. Otherwise raise exception.
    """
    for key, element in stream.iteritems():
        if key in ['mimetype', 'stream_type', 'index', 'version']:
            continue
        if element in [None, '(:unav)']:
            raise ValueError('Missing metadata value for key %s '
                             'for file %s' % (
                                key, filename))


def create_mix(filename, filerel=None, workspace=None):
    """Create MIX metadata XML element for an image file.

    :image: image file
    :returns: MIX XML element
    """
    streams = scrape_file(filename, filerel=filerel, workspace=workspace)
    stream_md = streams[0]
    check_missing_metadata(stream_md, filename)
    

    if stream_md['stream_type'] != 'image':
        print "This is not an image file. No MIX metadata created."
        return None
    if len(streams) > 1:
        raise ValueError('File containing multiple images not supported. '
                         'File: %s' % filename)

    mix_compression = nisomix.mix.mix_Compression(
        compressionScheme=stream_md["compression"])
    if not 'byte_order' in stream_md:
        if stream_md['mimetype'] == 'image/tiff':
            raise ValueError('Byte order missing from TIFF image file '
                             '%s' % filename)
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

    if not mix_root:
        raise ValueError('Image info could not be constructed.')

    return mix_root


if __name__ == '__main__':
    main(sys.argv[1:])
