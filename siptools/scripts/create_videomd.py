"""Command line tool for creating videoMD metadata."""
import sys
import os
import click
import pickle
import videomd
from siptools.utils import AmdCreator, scrape_file


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
    help="Workspace directory for the metadata files.")
@click.option(
    '--base_path', type=click.Path(exists=True), default='.',
    metavar='<BASE PATH>',
    help="Source base path of digital objects. If used, give path to "
         "the file in relation to this base path.")
def main(workspace, base_path, filename):
    """
    Write videoMD metadata for a video file or streams.

    FILENAME: Relative path to the file from current directory or from
              --base_path.
    """

    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = VideomdCreator(workspace)
    creator.add_videomd_md(filepath, filerel)
    creator.write()


class VideomdCreator(AmdCreator):
    """Subclass of AmdCreator, which generates videoMD metadata
    for video files.
    """

    def add_videomd_md(self, filepath, filerel=None):
        """Create videoMD metadata and append it to self.md_elements.
        """

        # Create videoMD metadata
        videomd_dict = create_videomd(filepath, filerel, self.workspace)
        if '0' in videomd_dict and len(videomd_dict) == 1:
            self.add_md(videomd_dict['0'],
                filerel if filerel else filepath)
        else:
            for index in videomd_dict.keys():
                self.add_md(videomd_dict[index],
                            filerel if filerel else filepath, index)

    def write(self, mdtype="OTHER", mdtypeversion="2.0",
              othermdtype="VideoMD"):
        super(VideomdCreator, self).write(mdtype, mdtypeversion, othermdtype)


def fix_missing_metadata(streams, filename):
    """If an element is none, use value (:unav) if allowed in the
    specifications. Otherwise raise exception.
    """
    for index, stream in streams.iteritems():
        for key, element in stream.iteritems():
            if key in ['mimetype', 'stream_type', 'index', 'version']:
                continue
            if element in [None, '(:unav)']:
                if key in ALLOW_UNAV:
                    stream[key] = '(:unav)'
                elif key in ALLOW_ZERO:
                    stream[key] = '0'
                else:
                    raise ValueError('Missing metadata value for key %s in '
                                     'index %s for file %s' % (
                                        key, str(index), filename))


def create_videomd(filename, filerel=None, workspace=None):
    """Creates and returns list of videoMD XML sections.
    :filename: Audio file path
    :returns: List of VideoMD XML sections.
    """
    streams = scrape_file(filename, filerel=filerel, workspace=workspace)
    fix_missing_metadata(streams, filename)

    videomd_dict = {}
    for index, stream_md in streams.iteritems():
        if stream_md['stream_type'] != 'video':
            continue

        file_data_elem = _get_stream_data(stream_md)

        videomd_elem = videomd.create_videomd(
            file_data=file_data_elem)
        videomd_dict[str(index)] = videomd_elem

    if not videomd_dict:
        raise ValueError('Video stream info could not be constructed.')

    return videomd_dict


def _get_stream_data(stream_dict):
    """Creates and returns the fileData XML element.
    :stream_dict: Stream dictionary from Scraper
    :sound: Value of the sound element
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

    frame = videomd.vmd_frame(pixels_horizontal=str(stream_dict['width']),
                              pixels_vertical=str(stream_dict['height']),
                              par=stream_dict['par'],
                              dar=stream_dict['dar'])

    params['frame'] = frame

    return videomd.vmd_file_data(params)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
