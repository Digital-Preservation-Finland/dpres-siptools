"""Command line tool for creating videoMD metadata."""
from __future__ import unicode_literals

import os
import sys

import click
import six

import videomd
from siptools.utils import MdCreator, fix_missing_metadata, scrape_file

click.disable_unicode_literals_warning = True


FILEDATA_KEYS = [
    'frame_rate', 'data_rate', 'bits_per_sample', 'data_rate_mode', 'color',
    'signal_format', 'sound', 'duration', 'sampling']

ALLOW_UNAV = ['duration', 'codec_creator_app', 'codec_creator_app_version',
              'codec_name', 'dar', 'sampling', 'signal_format']
ALLOW_ZERO = ['data_rate', 'bits_per_sample', 'frame_rate', 'width',
              'height', 'par']


@click.command()
@click.argument(
    'filename', type=str)
@click.option(
    '--workspace', type=click.Path(exists=True), default='./workspace/',
    metavar='<WORKSPACE PATH>',
    help="Workspace directory for the metadata files. "
         "Defaults to ./workspace/")
@click.option(
    '--base_path', type=click.Path(exists=True), default='.',
    metavar='<BASE PATH>',
    help="Source base path of digital objects. If used, give path to "
         "the file in relation to this base path.")
def main(filename, workspace, base_path):
    """Write videoMD metadata for a video file or streams.

    FILENAME: Relative path to the file from current directory or from
              --base_path.
    """
    create_videomd(filename, workspace, base_path)

    return 0


def create_videomd(filename, workspace="./workspace/", base_path="."):
    """
    Write videoMD metadata for a video file or streams.

    :filename: Video file name relative to base path
    :workspace: Workspace path
    :base_path: Base path
    """
    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = VideomdCreator(workspace)
    creator.add_videomd_md(filepath, filerel)
    creator.write()


class VideomdCreator(MdCreator):
    """
    Subclass of MdCreator, which generates videoMD metadata
    for video files.
    """

    def add_videomd_md(self, filepath, filerel=None):
        """Create videoMD metadata and append it to self.md_elements.

        If a file is not a video container, then the video stream metadata is
        processed in file level. Video container includes streams which need
        to be processed separately one at a time.

        :filepath: Video file path
        :filerel: Video file path relative to base path
        """

        # Create videoMD metadata
        videomd_dict = create_videomd_metadata(
            filepath, filerel, self.workspace
        )
        if '0' in videomd_dict and len(videomd_dict) == 1:
            self.add_md(metadata=videomd_dict['0'],
                        filename=(filerel if filerel else filepath))
        else:
            for index, video in six.iteritems(videomd_dict):
                self.add_md(metadata=video,
                            filename=(filerel if filerel else filepath),
                            stream=index)

    def write(self, mdtype="OTHER", mdtypeversion="2.0",
              othermdtype="VideoMD", section=None, stdout=False,
              file_metadata_dict=None):
        super(VideomdCreator, self).write(mdtype, mdtypeversion, othermdtype)


def create_videomd_metadata(filename, filerel=None, workspace=None,
                            streams=None):
    """Creates and returns list of videoMD XML sections.

    :filename: Video file path
    :filerel: Video file path relative to base path
    :workspace: Workspace path
    :streams: Metadata dict of streams. Will be created if None.
    :returns: List of VideoMD XML sections.
    """
    if streams is None:
        streams = scrape_file(filepath=filename, filerel=filerel,
                              workspace=workspace)
    fix_missing_metadata(streams, filename, ALLOW_UNAV, ALLOW_ZERO)

    videomd_dict = {}
    for index, stream_md in six.iteritems(streams):
        if stream_md['stream_type'] != 'video':
            continue

        file_data_elem = _get_file_data(stream_md)

        videomd_elem = videomd.create_videomd(
            file_data=file_data_elem)
        videomd_dict[six.text_type(index)] = videomd_elem

    if not videomd_dict:
        print('The file has no video streams. No VideoMD metadata created.')
        return None

    return videomd_dict


def _get_file_data(stream_dict):
    """Creates and returns the fileData XML element.

    :stream_dict: Stream dictionary from Scraper
    :returns: VideoMD fileData element
    """
    params = {}
    for key in FILEDATA_KEYS:
        keyparts = key.split('_')
        camel_key = keyparts[0] + ''.join(x.title() for x in keyparts[1:])
        params[camel_key] = stream_dict[key]

    compression = (stream_dict['codec_creator_app'],
                   stream_dict['codec_creator_app_version'],
                   stream_dict['codec_name'],
                   stream_dict['codec_quality'])

    params['compression'] = videomd.vmd_compression(*compression)

    frame = videomd.vmd_frame(
        pixels_horizontal=six.text_type(stream_dict['width']),
        pixels_vertical=six.text_type(stream_dict['height']),
        par=stream_dict['par'],
        dar=stream_dict['dar']
    )

    params['frame'] = frame

    return videomd.vmd_file_data(params)


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
