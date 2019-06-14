"""Command line tool for creating audioMD metadata."""
import sys
import os
import click
import audiomd
from siptools.utils import MdCreator, scrape_file, fix_missing_metadata

FILEDATA_KEYS = ['audio_data_encoding', 'bits_per_sample',
                 'data_rate', 'data_rate_mode', 'sampling_frequency']

AUDIOINFO_KEYS = ['duration', 'num_channels']

ALLOW_UNAV = ['audio_data_encoding', 'codec_creator_app',
              'codec_creator_app_version', 'codec_name',
              'duration', 'num_channels']
ALLOW_ZERO = ['bits_per_sample', 'data_rate', 'sampling_frequency']


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
    """Write audioMD metadata for an audio file or streams.

    FILENAME: Relative path to the file from current directory or from
              --base_path.
    """
    create_audiomd(filename, workspace, base_path)

    return 0


def create_audiomd(filename, workspace="./workspace/", base_path="."):
    """Write audioMD metadata for an audio file or streams."""

    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = AudiomdCreator(workspace)
    creator.add_audiomd_md(filepath, filerel)
    creator.write()


class AudiomdCreator(MdCreator):
    """Subclass of MdCreator, which generates audioMD metadata
    for audio files.
    """

    def add_audiomd_md(self, filepath, filerel=None):
        """Create audioMD metadata for a audio file and append it
        to self.md_elements.

        If a file is not a video container, then the audio stream metadata is
        processed in file level. Video container includes streams which need
        to be processed separately one at a time.
        """

        # Create audioMD metadata
        audiomd_dict = create_audiomd_metadata(
            filepath, filerel, self.workspace
        )

        if '0' in audiomd_dict and len(audiomd_dict) == 1:
            self.add_md(metadata=audiomd_dict['0'],
                        filename=(filerel if filerel else filepath))
        else:
            for index, audio in audiomd_dict.iteritems():
                self.add_md(metadata=audio,
                            filename=(filerel if filerel else filepath),
                            stream=index)

    def write(self, mdtype="OTHER", mdtypeversion="2.0",
              othermdtype="AudioMD", section=None, stdout=False,
              file_metadata_dict=None):
        super(AudiomdCreator, self).write(mdtype, mdtypeversion, othermdtype)


def create_audiomd_metadata(filename, filerel=None, workspace=None):
    """Creates and returns list of audioMD XML sections.
    :filename: Audio file path
    :returns: List of AudioMD XML sections.
    """
    streams = scrape_file(filename, filerel=filerel, workspace=workspace)
    fix_missing_metadata(streams, filename, ALLOW_UNAV, ALLOW_ZERO)

    audiomd_dict = {}
    for index, stream_md in streams.iteritems():
        if stream_md['stream_type'] != 'audio':
            continue
        file_data_elem = _get_file_data(stream_md)
        audio_info_elem = _get_audio_info(stream_md)

        audiomd_elem = audiomd.create_audiomd(
            file_data=file_data_elem,
            audio_info=audio_info_elem
        )
        audiomd_dict[str(index)] = audiomd_elem

    if not audiomd_dict:
        raise ValueError('Audio stream info could not be constructed.')

    return audiomd_dict


def _get_file_data(stream_dict):
    """Creates and returns the fileData XML element.
    :stream_dict: Stream dictionary given by Scraper
    :returns: AudioMD fileData element
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

    params['compression'] = audiomd.amd_compression(*compression)

    return audiomd.amd_file_data(params)


def _get_audio_info(stream_dict):
    """Creates and returns the audioInfo XML element.
    :stream_dict: Stream dictionary given by Scraper
    :returns: AudioMD audioInfo element
    """
    return audiomd.amd_audio_info(
        duration=stream_dict['duration'],
        num_channels=stream_dict['num_channels'])


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
