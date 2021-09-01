"""Command line tool for creating audioMD metadata."""
from __future__ import unicode_literals, print_function

import os
import sys

import click
import six

import audiomd
from siptools.mdcreator import MetsSectionCreator
from siptools.utils import fix_missing_metadata, scrape_file

click.disable_unicode_literals_warning = True

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
    """
    Write audioMD metadata for an audio file or streams.

    :filename: Audio file path relative to base path
    :workspace: Workspace path
    :base_path: Base path
    """

    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = AudiomdCreator(workspace)
    creator.add_audiomd_md(filepath, filerel)
    creator.write()


class AudiomdCreator(MetsSectionCreator):
    """
    Subclass of MetsSectionCreator, which generates audioMD metadata for audio
    files.
    """

    def add_audiomd_md(self, filepath, filerel=None):
        """Create audioMD metadata for a audio file and append it
        to self.md_elements.

        If a file is not a video container, then the audio stream metadata is
        processed in file level. Video container includes streams which need
        to be processed separately one at a time.

        :filepath: Audio file path
        :filerel: Audio file path relative to base path
        """

        # Create audioMD metadata
        audiomd_dict = create_audiomd_metadata(
            filepath, filerel, self.workspace
        )

        if '0' in audiomd_dict and len(audiomd_dict) == 1:
            self.add_md(metadata=audiomd_dict['0'],
                        filename=(filerel if filerel else filepath))
        else:
            for index, audio in six.iteritems(audiomd_dict):
                self.add_md(metadata=audio,
                            filename=(filerel if filerel else filepath),
                            stream=index)

    # pylint: disable=too-many-arguments
    def write(self, mdtype="OTHER", mdtypeversion="2.0",
              othermdtype="AudioMD", section=None, stdout=False,
              file_metadata_dict=None,
              ref_file="create-audiomd-md-references.jsonl"):
        """
        Write AudioMD metadata.
        """
        super(AudiomdCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion,
            othermdtype=othermdtype, ref_file=ref_file
        )


def create_audiomd_metadata(filename, filerel=None, workspace=None,
                            streams=None):
    """Creates and returns list of audioMD XML sections.

    :filename: Audio file path
    :filrel: Audio file path relative to base path
    :workspace: Workspace path
    :streams: Metadata dict of streams. Will be created if None.
    :returns: Dict of AudioMD XML sections.
    """
    if streams is None:
        (streams, _, _) = scrape_file(filepath=filename,
                                      filerel=filerel,
                                      workspace=workspace,
                                      skip_well_check=True)
    fix_missing_metadata(streams, filename, ALLOW_UNAV, ALLOW_ZERO)

    audiomd_dict = {}
    for index, stream_md in six.iteritems(streams):
        if stream_md['stream_type'] != 'audio':
            continue
        stream_md = _fix_data_rate(stream_md)
        file_data_elem = _get_file_data(stream_md)
        audio_info_elem = _get_audio_info(stream_md)

        audiomd_elem = audiomd.create_audiomd(
            file_data=file_data_elem,
            audio_info=audio_info_elem
        )
        audiomd_dict[six.text_type(index)] = audiomd_elem

    if not audiomd_dict:
        print('The file has no audio streams. No AudioMD metadata created.')
        return None

    return audiomd_dict


def _fix_data_rate(stream_dict):
    """Changes the data_rate to an integer if it is of a
    float type by rounding the number. The value is saved as
    a string in the dictionary.

    :stream_dict: Metadata dict of a stream
    :returns: Fixed metadata dict
    """
    for key in stream_dict:
        if key == 'data_rate':
            data_rate = stream_dict[key]

    if data_rate:
        try:
            data_rate = float(data_rate)
            stream_dict['data_rate'] = six.text_type(int(round(data_rate)))
        except ValueError:
            pass

    return stream_dict


def _get_file_data(stream_dict):
    """Creates and returns the fileData XML element.

    :stream_dict: Metadata dict of a stream
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

    :stream_dict: Metadata dict of a stream
    :returns: AudioMD audioInfo element
    """
    return audiomd.amd_audio_info(
        duration=stream_dict['duration'],
        num_channels=stream_dict['num_channels'])


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
