"""Command line tool for importing digital objects"""

import os
import sys
import fnmatch
from uuid import uuid4
import datetime
import platform
import argparse

import premis
from file_scraper.scraper import Scraper
from siptools.utils import AmdCreator, encode_path


ALLOWED_CHARSETS = ['ISO-8859-15', 'UTF-8', 'UTF-16', 'UTF-32']



def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Tool for importing files to generate digital objects")
    parser.add_argument('files', nargs='+',
                        help="Digital objects to be imported")
    parser.add_argument(
        '--base_path', type=str, default='',
        help="Source base path of digital objects. If used, give objects in"
        "relation to this base path.")
    parser.add_argument(
        '--workspace', type=str, default='./workspace/',
        help="Workspace directory for the metadata files.")
    parser.add_argument(
        '--skip_wellformed', action='store_true',
        help='Skip file wellformed check and give technical metadata as parameters')
    parser.add_argument(
        '--format_name', dest='format_name', type=str,
        help='Mimetype of a file')
    parser.add_argument(
        '--charset', dest='charset', type=str, help='Charset of a file')
    parser.add_argument(
        '--format_version', dest='format_version', type=str,
        help='Version of fileformat')
    parser.add_argument(
        '--digest_algorithm', dest='digest_algorithm', type=str,
        help='Message digest algorithm')
    parser.add_argument(
        '--message_digest', dest='message_digest', type=str,
        help='Message digest of a file')
    parser.add_argument(
        '--date_created', dest='date_created', type=str,
        help='The actual or approximate date and time the object was created')
    parser.add_argument(
        '--identifier', dest='identifier', type=str, nargs=2,
        metavar=('IDENTIFIER_TYPE', 'IDENTIFIER_VALUE'),
        help='The identifier type and value of the digital object')
    parser.add_argument(
        '--format_registry', dest='format_registry', type=str, nargs=2,
        metavar=('REGISTRY_NAME', 'REGISTRY_KEY'),
        help='The format registry name and key of the digital object')
    parser.add_argument(
        '--order', dest='order', type=int,
        help='Order number of the digital object')
    parser.add_argument('--stdout', help='Print output to stdout')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    # Loop files and create premis objects
    files = collect_filepaths(dirs=args.files, base=args.base_path)
    for filename in files:

        premis_list = {}

        if args.base_path != '':
            filerel = os.path.relpath(filename, args.base_path)
        else:
            filerel = filename

        scraper = Scraper(filename)
        if not args.skip_wellformed:
            scraper.scrape(True)
        else:
            scraper.scrape(False)

        premis_elem = create_premis_object(
            filename, args.skip_wellformed, args.format_name,
            args.format_version, args.digest_algorithm,
            args.message_digest, args.date_created, args.charset,
            args.identifier, args.format_registry)

        creator = PremisCreator(args.workspace)
        creator.add_md(premis_elem, filerel)

        premis_list = None
        if scraper.streams[0]['stream_type'] == 'videocontainer':
            premis_list = create_streams(scraper.streams, premis_elem)

        if premis_list is not None:
            for index, premis_stream in premis_list.iteritems():
                creator.add_md(premis_stream, filerel, index)

        properties = {}
        if args.order:
            properties['order'] = str(args.order)
        # Add new properties of a file for other script files, e.g. structMap

        streams_dict = None
        if properties:
            scraper.streams[0]['properties'] = properties
            streams_dict = scraper.streams
        if scraper.streams[0]['stream_type'] in [
                'videocontainer', 'video', 'audio', 'image']:
            streams_dict = scraper.streams

        creator.write(stdout=args.stdout, scraper_streams=streams_dict)

    return 0


class PremisCreator(AmdCreator):
    """Subclass of AmdCreator, which generates PREMIS metadata
    for files and streams.
    """

    def write(self, mdtype="PREMIS:OBJECT", mdtypeversion="2.3",
              othermdtype=None, section=None, stdout=False,
              scraper_streams=None):
        super(PremisCreator, self).write(mdtype=mdtype,
                                         mdtypeversion=mdtypeversion,
                                         scraper_streams=scraper_streams)


def create_streams(streams, premis_file):
    """Create PREMIS objects for streams

    :fname: Digital object file path
    :premis_file: Created PREMIS XML file for the digital object file
    """
    premis_list = {}
    for index, stream in streams.iteritems():
        if stream['stream_type'] not in ['video', 'audio']:
            continue

        id_value = str(uuid4())
        identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=id_value)
        premis_format_des = premis.format_designation(
            stream['mimetype'], stream['version'])
        premis_format = premis.format(child_elements=[premis_format_des])
        premis_objchar = premis.object_characteristics(
            child_elements=[premis_format])
        el_premis_object = premis.object(
            identifier, child_elements=[premis_objchar], bitstream=True)

        premis_list[index] = el_premis_object

        premis_file.append(
            premis.relationship('structural', 'includes', el_premis_object))

    return premis_list


def create_premis_object(fname, skip_wellformed=None,
                         format_name=None, format_version=None,
                         digest_algorithm='MD5', message_digest=None,
                         date_created=None, charset=None,
                         identifier=None, format_registry=None):
    """Create Premis object for given file."""

    scraper = Scraper(fname)
    if not skip_wellformed:
        scraper.scrape(True)
    else:
        scraper.scrape(False)

    if message_digest is None or digest_algorithm is None:
        message_digest = scraper.checksum(algorithm='md5')
        digest_algorithm = 'MD5'

    if format_name is None:
        format_name = scraper.mimetype
    if format_version is None:
        format_version = scraper.version
    if not charset and 'charset' in scraper.streams[0]:
        charset = scraper.streams[0]['charset']
    if charset:
        if charset not in ALLOWED_CHARSETS:
            raise ValueError('Invalid charset.')
        format_name += '; charset=' + charset

    if date_created is None:
        date_created = creation_date(fname)

    if identifier is None:
        object_identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=str(uuid4()))
    else:
        object_identifier = premis.identifier(
            identifier_type=identifier[0],
            identifier_value=identifier[1])

    premis_fixity = premis.fixity(message_digest, digest_algorithm)
    premis_format_des = premis.format_designation(format_name, format_version)
    if format_registry is None:
        premis_format = premis.format(child_elements=[premis_format_des])
    else:
        premis_registry = premis.format_registry(format_registry[0],
                                                 format_registry[1])
        premis_format = premis.format(child_elements=[premis_format_des,
                                                      premis_registry])
    premis_date_created = premis.date_created(date_created)
    premis_create = \
        premis.creating_application(child_elements=[premis_date_created])
    premis_objchar = premis.object_characteristics(
        child_elements=[premis_fixity, premis_format, premis_create])

    # Create object element
    el_premis_object = premis.object(
        object_identifier, child_elements=[premis_objchar])

    return el_premis_object


def collect_filepaths(dirs=None, pattern='*', base=''):
    """Collect file paths recursively from given directory. Raises IOError
    if given path does not exist."""

    if dirs is None:
        dirs = ['.']
    files = []

    for directory in dirs:
        directory = os.path.normpath(os.path.join(base, directory))
        if os.path.isdir(directory):
            files += [os.path.join(looproot, filename)
                      for looproot, _, filenames in os.walk(directory)
                      for filename in filenames
                      if fnmatch.fnmatch(filename, pattern)]
        elif os.path.isfile(directory):
            files += [directory]
        else:
            raise IOError

    return files


def creation_date(path_to_file):
    """Try to get the date that a file was created, falling back to when it
    was last modified if that isn't possible.  See
    http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return datetime.datetime.fromtimestamp(
            os.path.getctime(path_to_file)).isoformat()
    else:
        stat = os.stat(path_to_file)
        try:
            return datetime.datetime.fromtimestamp(
                stat.st_birthtime).isoformat()
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
