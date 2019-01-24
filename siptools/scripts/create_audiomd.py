"""Command line tool for creating audioMD metadata."""

import os
import argparse
import ffmpeg

import audiomd
from siptools.utils import AmdCreator, iso8601_duration, strip_zeros


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""

    parser = argparse.ArgumentParser(
        description="Tool for creating audioMD metadata for an audio or "
                    "video file. The audioMD metadata is written to "
                    "<hash>-AudioMD-techmd.xml METS XML file in the "
                    "workspace directory. The audioMD techMD reference is "
                    "written to techmd-references.xml. "
                    "If the same audioMD metadata is already found in "
                    "workspace, just the new file name or stream is appended "
                    "the the existing metadata."
    )

    parser.add_argument('file', type=str, help="Path to the audio file")
    parser.add_argument(
        '--workspace', type=str, default='./workspace/',
        help="Workspace directory for the metadata files.")
    parser.add_argument(
        '--streams', dest='streams', action='store_true',
        help='Given files include streams')
    parser.add_argument(
        '--base_path', type=str, default='',
        help="Source base path of digital objects. If used, give path to "
             "the audio file in relation to this base path.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write audioMD metadata for an audio file."""

    args = parse_arguments(arguments)

    filerel = os.path.normpath(args.file)
    filepath = os.path.normpath(os.path.join(args.base_path, args.file))

    is_streams = False
    if args.streams:
        is_streams = True

    creator = AudiomdCreator(args.workspace)
    creator.add_audiomd_md(filepath, filerel, is_streams)
    creator.write()


class AudiomdCreator(AmdCreator):
    """Subclass of AmdCreator, which generates audioMD metadata
    for audio files.
    """

    def add_audiomd_md(self, filepath, filerel=None, is_streams=False):
        """Create audioMD metadata for a WAV file and append it
        to self.md_elements.
        """

        # Create audioMD metadata
        audiomd_list = create_audiomd(filepath)
        for index in audiomd_list.keys():
            if is_streams:
                self.add_md(audiomd_list[index],
                            filerel if filerel else filepath, index)
            else:
                self.add_md(audiomd_list[index],
                            filerel if filerel else filepath)

    def write(self, mdtype="OTHER", mdtypeversion="2.0",
              othermdtype="AudioMD"):
        super(AudiomdCreator, self).write(mdtype, mdtypeversion, othermdtype)


def create_audiomd(filename):
    """Creates and returns list of audioMD XML sections.
    :filename: Audio file path
    :returns: List of AudioMD XML sections.
    """

    try:
        metadata = ffmpeg.probe(filename)
    except ffmpeg.Error:
        raise ValueError("File '%s' could not be parsed by ffprobe" % filename)

    audiomd_list = {}
    for stream_md in metadata["streams"]:
        if stream_md['codec_type'] != 'audio':
            continue
        file_data_elem = _get_stream_data(stream_md)
        audio_info_elem = _get_audio_info(stream_md)

        audiomd_elem = audiomd.create_audiomd(
            file_data=file_data_elem,
            audio_info=audio_info_elem
        )
        audiomd_list[str(stream_md['index'])] = audiomd_elem

    return audiomd_list


def _get_stream_data(stream_dict):
    """Creates and returns the fileData XML element.
    :stream_dict: Stream dictionary given by FFMPEG
    :returns: AudioMD fileData element
    """

    # amd.file_data() params
    bps = str(stream_dict["bits_per_sample"])
    if bps == "0":
        bps = "(:unap)"
    bit_rate = float(stream_dict["bit_rate"])
    data_rate = str(int(round(bit_rate/1000)))
    sample_rate = float(stream_dict["sample_rate"])
    sampling_frequency = strip_zeros("%.2f" % (sample_rate/1000))
    codec = _get_encoding(stream_dict)

    if codec == "PCM":
        compression_params = ("(:unap)", "(:unap)",
                              stream_dict["codec_long_name"], "lossless")
    else:
        compression_params = ("(:unav)", "(:unav)",
                              stream_dict["codec_long_name"], "(:unav)")

    params = {}
    params["audioDataEncoding"] = codec
    params["bitsPerSample"] = bps
    params["compression"] = audiomd.amd_compression(*compression_params)
    params["dataRate"] = data_rate
    params["dataRateMode"] = "Fixed" # TODO
    params["samplingFrequency"] = sampling_frequency

    return audiomd.amd_file_data(params)


def _get_encoding(stream_dict):
    """Get the used codec from the stream_dict. Return PCM if codec is
    any form of PCM and full codec description otherwise.
    :stream_dict: Stream dictionary given by FFMPEG
    :returns: File encoding string
    """
    encoding = stream_dict["codec_long_name"]

    if encoding.split()[0] == "PCM":
        return "PCM"
    elif encoding.split()[0] == "AAC":
        return "AAC"

    return encoding


def _get_audio_info(stream_dict):
    """Creates and returns the audioInfo XML element.
    :stream_dict: Stream dictionary given by FFMPEG
    :returns: AudioMD audioInfo element
    """

    time = float(stream_dict["duration"])
    duration = iso8601_duration(time)
    channels = str(stream_dict["channels"])

    return audiomd.amd_audio_info(duration=duration, num_channels=channels)


if __name__ == '__main__':
    main()
