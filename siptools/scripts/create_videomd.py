"""Command line tool for creating videoMD metadata."""

import os
import argparse
from fractions import Fraction
import ffmpeg

import videomd
from siptools.utils import AmdCreator, iso8601_duration, strip_zeros


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""

    parser = argparse.ArgumentParser(
        description="Tool for creating videoMD metadata for a video file. The "
                    "videoMD metadata is written to <hash>-VideoMD-amd.xml "
                    "METS XML file in the workspace directory. The videoMD "
                    "techMD reference is written to amd-references.xml. "
                    "If the same videoMD metadata is already found in "
                    "workspace, just the new file or stream is appended to "
                    "the existing metadata."
    )

    parser.add_argument('file', type=str, help="Path to the video file")
    parser.add_argument(
        '--workspace', type=str, default='./workspace/',
        help="Workspace directory for the metadata files.")
    parser.add_argument(
        '--streams', dest='streams', action='store_true',
        help='Given file include streams')
    parser.add_argument(
        '--base_path', type=str, default='',
        help="Source base path of digital objects. If used, give path to "
             "the video file in relation to this base path.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write videoMD metadata for a video file."""

    args = parse_arguments(arguments)

    filerel = os.path.normpath(args.file)
    filepath = os.path.normpath(os.path.join(args.base_path, args.file))

    is_streams = False
    if args.streams:
        is_streams = True

    creator = VideomdCreator(args.workspace)
    creator.add_videomd_md(filepath, filerel, is_streams)
    creator.write()


class VideomdCreator(AmdCreator):
    """Subclass of AmdCreator, which generates videoMD metadata
    for video files.
    """

    def add_videomd_md(self, filepath, filerel=None, is_streams=False):
        """Create videoMD metadata and append it to self.md_elements.
        """

        # Create videoMD metadata
        videomd_list = create_videomd(filepath)
        for index in videomd_list.keys():
            if is_streams:
                self.add_md(videomd_list[index],
                            filerel if filerel else filepath, index)
            else:
                self.add_md(videomd_list[index],
                            filerel if filerel else filepath)

    def write(self, mdtype="OTHER", mdtypeversion="2.0",
              othermdtype="VideoMD"):
        super(VideomdCreator, self).write(mdtype, mdtypeversion, othermdtype)


def create_videomd(filename):
    """Creates and returns list of videoMD XML sections.
    :filename: Audio file path
    :returns: List of VideoMD XML sections.
    """

    try:
        metadata = ffmpeg.probe(filename)
    except ffmpeg.Error:
        raise ValueError("File '%s' could not be parsed by ffprobe" % filename)

    videomd_list = {}
    audio = "No"
    for stream_md in metadata["streams"]:
        if stream_md['codec_type'] == 'audio':
            audio = "Yes"
    for stream_md in metadata["streams"]:
        if stream_md['codec_type'] != 'video':
            continue
        file_data_elem = _get_stream_data(stream_md, audio)

        videomd_elem = videomd.create_videomd(
            file_data=file_data_elem)
        videomd_list[str(stream_md['index'])] = videomd_elem

    return videomd_list


def _get_stream_data(stream_dict, sound):
    """Creates and returns the fileData XML element.
    :stream_dict: Stream dictionary from FFMPEG
    :sound: Value of the sound element
    :returns: VideoMD fileData element
    """

    if 'bits_per_raw_sample' in stream_dict:
        bps = str(stream_dict["bits_per_raw_sample"])
    else:
        bps = "0"
    bit_rate = float(stream_dict["bit_rate"])
    data_rate = strip_zeros("%.2f" % (float(bit_rate)/1000000))
    frame_rate = stream_dict["avg_frame_rate"].split('/')[0]

    par = strip_zeros("%.2f" % float(Fraction(
        stream_dict['sample_aspect_ratio'].replace(':', '/'))))
    dar = stream_dict['display_aspect_ratio'].replace(':', '/')

    compression = videomd.vmd_compression(
        '(:unav)', '(:unav)', stream_dict["codec_long_name"], '(:unav)')

    frame = videomd.vmd_frame(pixels_horizontal=str(stream_dict['width']),
                              pixels_vertical=str(stream_dict['height']),
                              par=par,
                              dar=dar)

    time = float(stream_dict["duration"])
    duration = iso8601_duration(time)

    sampling = "(:unav)"
    for sampling_code in ["444", "422", "420", "440", "411", "410"]:
        if sampling_code in stream_dict["pix_fmt"]:
            sampling = ":".join(sampling_code)
            break

    if stream_dict["pix_fmt"] in ["gray"]:
        color = "Grayscale"
    if stream_dict["pix_fmt"] in ["monob", "monow"]:
        color = "B&W"
    else:
        color = "Color"

    params = {}
    params["duration"] = duration
    params["bitsPerSample"] = bps
    params["compression"] = compression
    params["dataRate"] = data_rate
    params["dataRateMode"] = "Fixed"  # TODO
    params["color"] = color
    params["frameRate"] = frame_rate
    params["frame"] = frame
    params["sampling"] = sampling
    params["signalFormat"] = '(:unav)'
    params["sound"] = sound

    return videomd.vmd_file_data(params)


if __name__ == '__main__':
    main()
