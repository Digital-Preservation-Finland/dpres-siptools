# coding=utf-8
"""Command line tool for creating MIX metadata."""

import os
import sys
import click
import nisomix
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


@click.command()
@click.argument(
    'filename', type=str)
@click.option(
    '--workspace', type=click.Path(exists=True),
    default='./workspace/',
    metavar='<WORKSPACE PATH>',
    help="Workspace directory for the metadata files.")
@click.option(
    '--base_path', type=click.Path(exists=True), default='.',
    metavar='<BASE PATH>',
    help="Source base path of digital objects. If used, give path to "
         "the file in relation to this base path.")
def main(workspace, base_path, filename):
    """
    Write MIX metadata for an image file.

    FILENAME: Relative path to the file from current directory or from
              --base_path.
    """

    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = MixCreator(workspace)
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
    def write(self, mdtype="NISOIMG", mdtypeversion="2.0", othermdtype=None,
              section=None, stdout=False, scraper_streams=None):
        super(MixCreator, self).write(mdtype, mdtypeversion, othermdtype)


def check_missing_metadata(stream, filename):
    """If an element is none, use value (:unav) if allowed in the
    specifications. Otherwise raise exception.
    """
    for key, element in stream.iteritems():
        if key in ['mimetype', 'stream_type', 'index', 'version']:
            continue
        if element in [None, '(:unav)']:
            raise ValueError(
                'Missing metadata value for key %s '
                'for file %s' % (key, filename))


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

    mix_compression = nisomix.compression(
        compression_scheme=stream_md["compression"])
    if 'byte_order' not in stream_md:
        if stream_md['mimetype'] == 'image/tiff':
            raise ValueError('Byte order missing from TIFF image file '
                             '%s' % filename)
        byte_order = None
    else:
        byte_order = stream_md["byte_order"]

    basic_do_info = nisomix.digital_object_information(
        byte_order=byte_order, child_elements=[mix_compression])

    photom_interpret = nisomix.photometric_interpretation(
        color_space=stream_md["colorspace"])
    img_characteristics = nisomix.image_characteristics(
        width=stream_md["width"], height=stream_md["height"],
        child_elements=[photom_interpret])
    img_info = nisomix.image_information(
        child_elements=[img_characteristics])

    bit_depth = nisomix.bits_per_sample(
        sample_values=stream_md["bps_value"],
        sample_unit=stream_md["bps_unit"])
    color_encoding = nisomix.color_encoding(
        samples_pixel=stream_md["samples_per_pixel"],
        child_elements=[bit_depth])
    img_assessment = nisomix.image_assessment_metadata(
        child_elements=[color_encoding])

    mix_root = nisomix.mix(
        child_elements=[basic_do_info, img_info, img_assessment])

    if mix_root is None:
        raise ValueError('Image info could not be constructed.')

    return mix_root


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
