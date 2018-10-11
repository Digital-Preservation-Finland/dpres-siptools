"""Command line tool for creating audioMD metadata."""

import argparse
import ffmpeg

import audiomd
from siptools.utils import TechmdCreator


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""

    parser = argparse.ArgumentParser(
        description="Tool for creating audioMD metadata for a WAV file. The "
                    "audioMD metadata is written to <hash>-ADDML-techmd.xml "
                    "METS XML file in the workspace directory. The audioMD "
                    "techMD reference is written to techmd-references.xml. "
                    "If similar audioMD metadata is already found in workspace, "
                    "just the new WAV file name is appended to the existing "
                    "metadata."
    )

    parser.add_argument('file', type=str, help="WAV file name")
    parser.add_argument('--workspace', type=str, default='./workspace/',
                        help="Workspace directory for the metadata files.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write audioMD metadata for a WAV file."""

    args = parse_arguments(arguments)

    creator = AudiomdCreator(args.workspace)
    creator.add_audiomd_md(args.file)
    creator.write()


class AudiomdCreator(TechmdCreator):
    """Subclass of TechmdCreator, which generates audioMD metadata
    for WAV files.
    """

    def add_audiomd_md(self, filepath):
        """Create audioMD metadata for a WAV file and append it
        to self.md_elements.
        """

        # Create audioMD metadata
        metadata = create_audiomd(filepath)
        md_element = (metadata, filepath)
        self.md_elements.append(md_element)


    def write(self, mdtype="OTHER", mdtypeversion="2.0", othermdtype="AudioMD"):
        super(AudiomdCreator, self).write(mdtype, mdtypeversion, othermdtype)


def create_audiomd(filename):
    """Creates and returns the root audioMD XML element.
    """

    try:
        metadata = ffmpeg.probe(filename)
    except ffmpeg.Error:
        raise ValueError("File '%s' could not be parsed by ffprobe" % filename)

    file_data_elem = _get_file_data(metadata)
    audio_info_elem = _get_audio_info(metadata)

    audiomd_elem = audiomd.create_audiomd(
        file_data=file_data_elem,
        audio_info=audio_info_elem
    )

    return audiomd_elem


def _get_file_data(metadata):
    """Creates and returns the fileData XML element.
    """

    stream_dict = metadata["streams"][0]

    # amd.file_data() params
    bps = str(stream_dict["bits_per_sample"])
    bit_rate = float(stream_dict["bit_rate"])
    data_rate = str(int(round(bit_rate/1000)))
    sample_rate = float(stream_dict["sample_rate"])
    sampling_frequency = _strip_zeros("%.2f" % (sample_rate/1000))
    codec = _get_encoding(stream_dict)

    if codec == "PCM":
        compression_params = ("(:unap)", "(:unap)", "(:unap)", "lossless")
    else:
        compression_params = ("(:unav)", "(:unav)", "(:unav)", "(:unav)")

    params = {}
    params["audioDataEncoding"] = codec
    params["bitsPerSample"] = bps
    params["compression"] = audiomd.amd_compression(*compression_params)
    params["dataRate"] = data_rate
    params["dataRateMode"] = "Fixed"
    params["samplingFrequency"] = sampling_frequency

    return audiomd.amd_file_data(params)


def _get_encoding(stream_dict):
    """Get the used codec from the stream_dict. Return PCM if codec is
    any form of PCM and full codec description otherwise.
    """
    encoding = stream_dict["codec_long_name"]

    if encoding.split()[0] == "PCM":
        return "PCM"

    return encoding


def _get_audio_info(metadata):
    """Creates and returns the audioInfo XML element.
    """

    stream_dict = metadata["streams"][0]
    format_dict = metadata["format"]

    time = float(format_dict["duration"])
    duration = _iso8601_duration(time)
    channels = str(stream_dict["channels"])

    return audiomd.amd_audio_info(duration=duration, num_channels=channels)


def _strip_zeros(float_str):
    """Recursively strip trailing zeros from a float i.e. _strip_zeros("44.10")
    returns "44.1" and _srip_zeros("44.0") returns "44"
    """

    # if '.' is found in the string and string
    # ends in '0' or '.' strip last character
    if float_str.find(".") != -1 and float_str[-1] in ['0', '.']:
        return _strip_zeros(float_str[:-1])

    return float_str


def _iso8601_duration(time):
    """Convert seconds into ISO 8601 duration PT[hours]H[minutes]M[seconds]S
    with seconds given in two decimal precision.
    """

    hours = time // (60*60)
    minutes = time // 60 % 60
    seconds = time % 60

    duration = "PT"

    if hours:
        duration += "%dH" % hours
    if minutes:
        duration += "%dM" % minutes
    if seconds:
        seconds = _strip_zeros("%.2f" % seconds)
        duration += "%sS" % seconds

    return duration


def _read_uint(f_in):
    """Read 4 bytes from f_in and return the corresponding
    unsigned integer.
    """
    uint = 0
    binary_num = f_in.read(4)

    for i in range(4):
        uint += ord(binary_num[i]) * 256**i

    return uint


def is_broadcast_wav(fname):
    """Check if file fname is WAV or broadcast WAV file.
    The function reads all the RIFF chunk IDs and returns
    True if "bext" chunk is found.
    """
    with open(fname) as f_in:
        f_in.read(4) # Skip RIFF ID
        size = _read_uint(f_in) - 4
        f_in.read(4) # Skip WAVE ID

        # Iterate all WAVE chunks
        while size > 0:
            chunk_id = f_in.read(4)
            chunk_size = _read_uint(f_in)

            if chunk_id == "bext":
                return True
            else:
                size -= (chunk_size + 8)
                f_in.seek(chunk_size, 1)

    return False


if __name__ == '__main__':
    main()
