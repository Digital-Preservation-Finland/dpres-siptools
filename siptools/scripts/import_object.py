"""Command line tool for importing digital objects"""

import os
import sys
import fnmatch
from uuid import uuid4
import datetime
import platform
import click
from file_scraper.scraper import Scraper
import premis
from siptools.utils import AmdCreator, encode_path, scrape_file


ALLOWED_CHARSETS = ['ISO-8859-15', 'UTF-8', 'UTF-16', 'UTF-32']

DEFAULT_VERSIONS = {
    'application/msword': '11.0', 
    'application/vnd.ms-excel': '11.0',
    'application/vnd.ms-powerpoint': '11.0',
    'application/vnd.openxmlformats-'
    'officedocument.presentationml.presentation': '15.0',
    'application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.sheet': '15.0',
    'application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document': '15.0'}


@click.command()
@click.argument('filepaths', nargs=-1, type=str)
@click.option(
        '--base_path', type=click.Path(exists=True), default='.',
        metavar='<BASE PATH>',
        help="Source base path of digital objects. If used, give objects in"
        "relation to this base path.")
@click.option(
        '--workspace', type=click.Path(exists=True), default='./workspace/',
        metavar='<WORKSPACE PATH>',
        help="Workspace directory for the metadata files.")
@click.option(
        '--skip_validation', is_flag=True,
        help='Skip file format well-formed check')
@click.option(
        '--charset', type=str,
        metavar='<CHARSET>',
        help='Charset encoding of a file')
@click.option(
        '--file_format', nargs=2, type=str,
        metavar='<MIMETYPE> <FORMAT VERSION>',
        help='Mimetype and file format version of a file')
@click.option(
        '--identifier', nargs=2, type=str,
        metavar='<IDENTIFIER TYPE> <IDENTIFIER VALUE>',
        help='The identifier type and value of a digital object')
@click.option(
        '--checksum', nargs=2, type=str,
        metavar='<CHECKSUM ALGORITHM> <CHECKSUM VALUE>',
        help='Checksum algorithm and value of a given file')
@click.option(
        '--date_created', type=str,
        metavar='<TIMESTAMP>',
        help='The actual or approximate date and time the object was created')
@click.option(
        '--format_registry', type=str, nargs=2,
        metavar='<REGISTRY NAME> <REGISTRY KEY>',
        help='The format registry name and key of the digital object')
@click.option(
        '--order', type=int,
        metavar='<ORDER NUMBER>',
        help='Order number of the digital object')
@click.option('--stdout', is_flag=True,
              help='Print result also to stdout')
def main(workspace, base_path, skip_validation, charset, file_format,
         checksum, date_created, identifier, format_registry, order,
         stdout,  filepaths):
    """
    Import digital objects to Submission Imformation Package.

    FILEPATHS: One or more files to add as a list, or a directory.

    """

    # Loop files and create premis objects
    files = collect_filepaths(dirs=filepaths, base=base_path)
    for filepath in files:
        if base_path not in ['.']:
            filerel = os.path.relpath(filepath, base_path)
        else:
            filerel = filepath

        properties = {}
        if order:
            properties['order'] = str(order)
        # Add new properties of a file for other script files, e.g. structMap

        creator = PremisCreator(workspace)
        streams_dict = creator.add_premis_md(
            filepath, filerel, skip_validation, charset, file_format, checksum,
            date_created, identifier, format_registry, stdout, properties)
        creator.write(stdout=stdout, scraper_streams=streams_dict)

    return 0


def modify_streams(streams, properties):
    streams_dict = None
    if properties:
        streams[0]['properties'] = properties
        return streams
    if streams[0]['stream_type'] in [
            'videocontainer', 'video', 'audio', 'image']:
        return streams
    return None


def check_tuple_arguments(argument, error):
    if argument is not None:
        if len(argument) < 2:
            raise ValueError(error)
    return argument


class PremisCreator(AmdCreator):
    """Subclass of AmdCreator, which generates PREMIS metadata
    for files and streams.
    """

    def add_premis_md(self, filepath, filerel=None, skip_validation=False,
                      charset=None, file_format=None, checksum=None,
                      date_created=None, identifier=None,
                      format_registry=None, stdout=False,
                      properties=None):

        scraper = Scraper(filepath)
        if not skip_validation:
            scraper.scrape(True)
            errors = ''
            for _, info in scraper.info.iteritems():
                if len(info['errors']) > 0:
                    errors = "%s\n%s" % (errors, info['errors']) \
                        if len(errors) > 0 else info['errors']
            if len(errors) > 0:
                raise ValueError(errors)
        else:
            scraper.scrape(False)

        streams_dict = modify_streams(scraper.streams, properties)

        premis_elem = create_premis_object(
            filepath, scraper, file_format, checksum, date_created, charset,
            identifier, format_registry)

        self.add_md(premis_elem, filerel)

        premis_list = create_streams(scraper.streams, premis_elem)

        if premis_list is not None:
            for index, premis_stream in premis_list.iteritems():
                self.add_md(premis_stream, filerel, index)

        return streams_dict


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
    if len(streams) < 2:
        return None

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


def check_metadata(format_name, format_version, streams, fname):
    """Check that we will not get None values"""
    if format_name is None:
        raise ValueError('Mimetype could not be identified for '
                         'file %s' % fname)
    if format_version is None:
        raise ValueError('File format version could not be identified for '
                         'file ' % fname)
    if streams[0]['stream_type'] not in ['videocontainer'] and \
            len(streams) > 1:
        raise ValueError('The file contains multiple streams which '
                         'is supported only for video containers.')
    elif streams[0]['stream_type'] in ['videocontainer'] and \
            len(streams) < 2:
        raise ValueError('Video container format without contained streams found.')


def create_premis_object(fname, scraper,
                         file_format=None, checksum=None,
                         date_created=None, charset=None,
                         identifier=None, format_registry=None):
    """Create Premis object for given file."""

    if scraper.info[0]['class'] == 'FileExists' and \
            len(scraper.info[0]['errors']) > 0:
        raise IOError(scraper.info[0]['errors'])
    for _, info in scraper.info.iteritems():
        if info['class'] == 'ScraperNotFound':
            raise ValueError('File format is not supported.')

    if checksum in [None, ()]:
        message_digest = scraper.checksum(algorithm='md5')
        digest_algorithm = 'MD5'
    else:
        message_digest = checksum[1]
        digest_algorithm = checksum[0]

    if file_format in [None, ()]:
        format_name = scraper.mimetype
        format_version = scraper.version
        if format_name in DEFAULT_VERSIONS:
            format_version = DEFAULT_VERSIONS[format_name]
    else:
        format_name = file_format[0]
        format_version = file_format[1]

    if not charset and scraper.streams[0]['stream_type'] == 'text':
        charset = scraper.streams[0]['charset']

    check_metadata(format_name, format_version, scraper.streams, fname)

    if charset:
        if charset not in ALLOWED_CHARSETS:
            raise ValueError('Invalid charset.')
        format_name += '; charset=' + charset

    if date_created is None:
        date_created = creation_date(fname)

    if identifier in [None, ()]:
        object_identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=str(uuid4()))
    else:
        object_identifier = premis.identifier(
            identifier_type=identifier[0],
            identifier_value=identifier[1])

    premis_fixity = premis.fixity(message_digest, digest_algorithm)
    premis_format_des = premis.format_designation(format_name, format_version)
    if format_registry in [None, ()]:
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


if __name__ == "__main__":
    RETVAL = main()
    sys.exit(RETVAL)
