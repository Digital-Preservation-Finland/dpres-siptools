"""Command line tool for creating audioMD metadata."""

import argparse
import ffmpeg
import lxml.etree as ET

import audiomd
from siptools.utils import TechmdCreator, encode_path


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

    def __init__(self, workspace):
        """
        :workspace: Output path
        :etrees: Dict of the generated root elements
        :filenames: Dict of the filenames corresponding to root elements
        """
        super(AudiomdCreator, self).__init__(workspace)
        self.etrees = {}
        self.filenames = {}


    def add_audiomd_md(self, filepath):
        """Append metadata to etrees and filenames dicts.
        All the metadata given as the parameters uniquely defines
        the XML file to be written later. A tuple of the
        metadata is thus used as the dict key, which makes it possible
        to efficiently check if corresponding metadata element has
        already been created. This means that the write_techmdfile()
        function needs to be called only once for each distinct metadata types.

        :csv_file: CSV file name
        :delimiter: Delimiter used in the CSV file
        :isheader: True if CSV has a header else False
        :charset: Charset used in the CSV file
        :record_separator: Char used for separating CSV file fields
        :quoting_char: Quotation char used in the CSV file

        :returns: None
        """

        header = csv_header(csv_file, delimiter)

        key = (delimiter, header, charset, record_separator, quoting_char)

        # If similar metadata already exists,
        # only append filename to self.filenames
        if key in self.etrees:
            self.filenames[key].append(csv_file)
            return

        # If similar metadata does not exist, create it
        metadata = create_addml(
            csv_file, delimiter,
            isheader, charset,
            record_separator, quoting_char
        )

        self.etrees[key] = metadata
        self.filenames[key] = [csv_file]


    def write(self, mdtype="OTHER", mdtypeversion="8.3", othermdtype="ADDML"):
        """ Write all the METS XML files and techmdreference file.
        Base class write is overwritten to handle the references
        correctly and add flatFile fields to METS XML files.

        :returns: None
        """

        for key in self.etrees:
            metadata = self.etrees[key]
            filenames = self.filenames[key]

            # Create METS XML file
            techmd_id, techmd_fname = \
                self.write_md(metadata, mdtype, mdtypeversion, othermdtype)

            # Add all the files to references
            for filename in filenames:
                self.add_reference(techmd_id, filename)

            # Append all the flatFile elements to the METS XML file
            append = [
                flat_file_str(encode_path(filename), "ref001")
                for filename in filenames
            ]
            append_lines(techmd_fname, "<addml:flatFiles>", append)

        # Write techmdreferences
        self.write_references()

        # Clear filenames and etrees
        self.__init__(self.workspace)


def create_audiomd(filename):
    """Creates and returns the root audioMD XML element.
    """

    metadata = ffmpeg.probe(filename)

    file_data_elem = _get_file_data(metadata)
    audio_info_elem = _get_audio_info(metadata)

    audiomd_elem = audiomd.create_audiomd(
        file_data = file_data_elem,
        audio_info = audio_info_elem
    )

    return audiomd_elem


def _get_file_data(metadata):
    """Creates and returns the fileData XML element.
    """

    stream_dict = metadata["streams"][0]
    format_dict = metadata["format"]

    # amd.file_data() params
    bps = str(stream_dict["bits_per_sample"])
    bit_rate = float(stream_dict["bit_rate"])
    channels = int(stream_dict["channels"])
    data_rate = str(int(round(bit_rate/1000)))
    sample_rate = float(stream_dict["sample_rate"])
    sampling_frequency = _strip_zeros("%.2f" % (sample_rate/1000))

    params = {}
    params["audioDataEncoding"] = "PCM"
    params["bitsPerSample"] = bps
    params["compression"] = audiomd.amd_compression(
        "(:unap)",
        "(:unap)",
        "(:unap)",
        "lossless"
    )
    params["dataRate"] = data_rate
    params["dataRateMode"] = "Fixed"
    params["samplingFrequency"] = sampling_frequency

    return audiomd.amd_file_data(params)


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
    if float_str.find(".") is not -1 and float_str[-1] in ['0', '.']:
        return _strip_zeros(float_str[:-1])
    else:
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

if __name__ == '__main__':
    # main()

    print ET.tostring(
        create_audiomd("tests/data/audio/valid-wav.wav"),
        pretty_print=True
    )
