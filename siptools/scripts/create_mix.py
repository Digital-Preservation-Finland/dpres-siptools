# coding=utf-8
"""Command line tool for creating MIX metadata."""
from __future__ import unicode_literals, print_function

import os
import sys

import click

import nisomix
from file_scraper.defaults import UNAV
from siptools.mdcreator import MetsSectionCreator
from siptools.utils import scrape_file

click.disable_unicode_literals_warning = True

SAMPLES_PER_PIXEL = {'1': '1', 'L': '1', 'P': '1', 'RGB': '3', 'YCbCr': '3',
                     'LAB': '3', 'HSV': '3', 'RGBA': '4', 'CMYK': '4',
                     'I': '1', 'F': '1'}


class MixGenerationError(ValueError):
    """Exception raised when mix metadata generation fails."""

    def __init__(self, message, filename=""):
        super(MixGenerationError, self).__init__(message)
        self.filename = filename

    def __str__(self):
        return self.message + self.filename


@click.command()
@click.argument(
    'filename', type=str)
@click.option(
    '--workspace', type=click.Path(exists=True),
    default='./workspace/',
    metavar='<WORKSPACE PATH>',
    help="Workspace directory for the metadata files. "
         "Defaults to ./workspace/")
@click.option(
    '--base_path', type=click.Path(exists=True), default='.',
    metavar='<BASE PATH>',
    help="Source base path of digital objects. If used, give path to "
         "the file in relation to this base path.")
def main(filename, workspace, base_path):
    """Write MIX metadata for an image file.

    FILENAME: Relative path to the file from current directory or from
              --base_path.
    """
    if not os.path.exists(os.path.join(base_path, filename)):
        raise click.UsageError("File does not exist")

    create_mix(filename, workspace, base_path)

    return 0


def create_mix(filename, workspace="./workspace/", base_path="."):
    """
    Write MIX metadata for an image file.

    :filename: Image file path relative to base path
    :workspace: Workspace path
    :base_path: Base path
    """

    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = MixCreator(workspace)
    creator.add_mix_md(filepath, filerel)
    creator.write()


class MixCreator(MetsSectionCreator):
    """
    Subclass of MetsSectionCreator, which generates MIX metadata for image
    files.
    """

    def add_mix_md(self, filepath, filerel=None):
        """Creates  MIX metadata for an image file and append it
        to self.md_elements

        :filepath: path to image file
        :filerel: relative path to image file to write to reference file
        :returns: None
        """

        # Create MIX metadata
        mix_dict = create_mix_metadata(filepath, filerel, self.workspace)
        for index, mix in mix_dict.items():
            self.add_md(metadata=mix,
                        filename=(filerel if filerel else filepath),
                        stream=(index if len(mix_dict) > 1 else None))

    # Change the default write parameters
    # pylint: disable=too-many-arguments
    def write(self, mdtype="NISOIMG", mdtypeversion="2.0", othermdtype=None,
              section=None, stdout=False, file_metadata_dict=None,
              ref_file="create-mix-md-references.jsonl"):
        """
        Write MIX metadata.
        """
        super(MixCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion,
            othermdtype=othermdtype, ref_file=ref_file
        )


def check_missing_metadata(stream, filename):
    """
    If an element is none, use value (:unav) if allowed in the
    specifications. Otherwise raise exception.

    :stream: Image metadata stream.
    :filename: Image file name
    """
    allowed_keys = ('icc_profile_name',
                    'index',
                    'mimetype',
                    'stream_type',
                    'version')
    for key, element in stream.items():
        if key in allowed_keys:
            continue
        if element in [None, UNAV]:
            raise MixGenerationError(
                'Missing metadata value for key %s for file %s' % (key,
                                                                   filename)
            )


def create_mix_metadata(filename, filerel=None, workspace=None, streams=None):
    """Create MIX metadata for an image file.

    :filename: Image file name
    :filerel: Image file name relative to base path
    :workspace: Workspace path
    :streams: Metadata dict of streams. Will be created if None.
    :returns: Dict of MIX XML elements
    """
    if streams is None:
        (streams, _, _) = scrape_file(filepath=filename,
                                      filerel=filerel,
                                      workspace=workspace,
                                      skip_well_check=True)

    mix_dict = {}

    for index, stream_md in streams.items():
        check_missing_metadata(stream_md, filename)

        if stream_md['stream_type'] != 'image':
            print("This is not an image file. No MIX metadata created.")
            return None

        mix_dict[str(index)] = _create_mix_item(stream_md, filename)

    return mix_dict


def _create_mix_item(stream_md, filename):
    """
    Create a single MIX metadata item.
    :stream_md: Item from metadata stream dict
    :filename: Image file name
    :returns: MIX XML metadata of a single image
    """
    mix_compression = nisomix.compression(
        compression_scheme=stream_md["compression"])
    if 'byte_order' not in stream_md:
        if stream_md['mimetype'] == 'image/tiff':
            raise MixGenerationError(
                'Byte order missing from TIFF image file ', filename
            )
        byte_order = None
    else:
        byte_order = stream_md["byte_order"]

    if stream_md['icc_profile_name'] is not UNAV:
        color_profile = [nisomix.color_profile(
            icc_name=stream_md['icc_profile_name'])]
    else:
        color_profile = None

    basic_do_info = nisomix.digital_object_information(
        byte_order=byte_order, child_elements=[mix_compression])

    photom_interpret = nisomix.photometric_interpretation(
        color_space=stream_md["colorspace"],
        child_elements=color_profile)
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
        raise MixGenerationError('Image info could not be constructed.')

    return mix_root


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
