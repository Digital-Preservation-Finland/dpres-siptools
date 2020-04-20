"""
Utilities for siptools
"""
from __future__ import unicode_literals, print_function

import copy
import hashlib
import os
import json
import sys
from collections import defaultdict

import six

import lxml.etree
import premis
import xml_helpers
from file_scraper.scraper import Scraper

try:
    from urllib.parse import quote_plus, unquote_plus
except ImportError:  # Python 2
    from urllib import quote_plus, unquote_plus


def calc_checksum(filepath, algorithm="md5"):
    """
    Calculate checksum of a file.

    :filepath: File path
    :algorithm: Algorithm name
    :returns: Checksum of the file
    """
    scraper = Scraper(filepath)
    return scraper.checksum(algorithm=algorithm)


def load_scraper_json(json_name):
    """
    Load scraper stream from JSON file.

    :json_name: JSON file name
    :returns: Stream metadata from JSON file.
    """
    with open(json_name, 'rt') as json_file:
        streams = json.load(json_file)
    new_streams = {}
    for index in streams:
        new_streams[int(index)] = streams[index]
        new_streams[int(index)]["index"] = \
            int(new_streams[int(index)]["index"])
    return new_streams


def read_json_streams(filerel, workspace):
    """
    Find out JSON file name from references and read it as
    metadata dict of streams.

    :filerel: Digital object file path relative to base_path
    :workspace: Workspace path
    """
    ref_exists = False
    if workspace is not None:
        ref = os.path.join(workspace, 'import-object-md-references.xml')
        if os.path.isfile(ref):
            ref_exists = True

    if ref_exists:
        root = lxml.etree.parse(ref).getroot()
        filerel = fsdecode_path(filerel)

        amdref = root.xpath("/mdReferences/mdReference[not(@stream) "
                            "and @file='%s']" % filerel)
        json_name = None
        for ref in amdref:
            json_name = os.path.join(
                workspace, '{}-scraper.json'.format(ref.text[1:]))
            if json_name and os.path.isfile(json_name):
                break
        if json_name:
            return load_scraper_json(json_name)
    return None


# pylint: disable=too-many-arguments
def scrape_file(filepath, filerel=None, workspace=None, mimetype=None,
                version=None, charset=None, skip_well_check=False,
                skip_json=False):
    """
    Return already existing scraping result or create a new one, if
    missing.

    :filepath: Digital object path
    :filerel: Digital object path relative to base path
    :workspace: Workspace path
    :mimetype: MIME type of digital object
    :version: File format version of digital object
    :charset: Encoding of digital object (if text file)
    :skip_well_check: True skips well-formedness checking
    :skip_json: True does scraping and does not try to find JSON file
    :returns: Metadata dict of streams and scraper info as a tuple
    :raises: ValueError If metadata collecting fails.
             IOError If file does not exist.
    """
    filerel = filepath if filerel is None else filerel
    streams = None
    if not skip_json:
        streams = read_json_streams(filerel, workspace)
    if streams is not None:
        return (streams, None)

    scraper = Scraper(filepath, mimetype=mimetype,
                      version=version, charset=charset)
    scraper.scrape(not skip_well_check)

    if scraper.well_formed is False:  # Must not be None
        errors = []
        for _, info in six.iteritems(scraper.info):
            errors.append("\n".join(info['errors']))
        error_str = "\n".join(errors)
        if skip_well_check:
            error_head = "Metadata of file %s could not " \
                "be collected due to errors.\n" % filepath
            error_str = error_head + error_str
        raise ValueError(six.text_type(error_str))

    if scraper.info[0]['class'] == 'FileExists' and \
            len(scraper.info[0]['errors']) > 0:
        raise IOError(scraper.info[0]['errors'])
    for _, info in six.iteritems(scraper.info):
        if info['class'] == 'ScraperNotFound':
            raise ValueError('File format is not supported.')

    return (scraper.streams, scraper.info)


def fix_missing_metadata(streams, filename, allow_unav, allow_zero):
    """
    If an element is none, use value (:unav) if allowed in the
    specifications. Otherwise raise exception.

    :streams: Metadata dict of streams
    :filename: File name of digital object
    :allow_unav: List of keys where (:unav) is allowed
    :allow_zero: List of keys where 0 is allowed
    """
    for index, stream in streams.items():
        for key, element in stream.items():
            if key in ['mimetype', 'stream_type', 'index', 'version']:
                continue
            if element in [None, '(:unav)']:
                if key in allow_unav:
                    stream[key] = '(:unav)'
                elif key in allow_zero:
                    stream[key] = '0'
                else:
                    raise ValueError(
                        'Missing metadata value for key %s in '
                        'index %s for file %s' % (key, index, filename))


def encode_path(path, suffix='', prefix='', safe=""):
    """
    Encode given path to URL encoding with given perfix and suffix.

    :path: Path to encode
    :suffix: Suffix to add
    :prefix: Prefix to add
    :safe: Characters safe from URL quoting
    :returns: Encoded string with given prefix and suffix
    """
    if isinstance(path, six.text_type):
        path = path.encode("utf-8")

    if isinstance(safe, six.text_type):
        safe = safe.encode("utf-8")

    quoted = quote_plus(path, safe=safe)
    return "{}{}{}".format(prefix, quoted, suffix)


def decode_path(path, suffix=''):
    """
    Decode given path from URL encoding and remove given suffix.

    :path: Path to decode
    :suffix: Suffix to remove
    :returns: Decoded string without given suffix
    """
    if six.PY2:
        path = unquote_plus(path.encode("utf-8")).decode("utf-8")
    else:
        path = unquote_plus(path)

    if path.endswith(suffix):
        path = path.replace(suffix, '', 1)
    return path


def fsencode_path(filename):
    """
    Encode Unicode filenames using the file system encoding.

    :filename: File path to encode
    :returns: Encoded path
    :raises: TypeError if wrong type given
    """
    if isinstance(filename, six.text_type):
        return filename.encode(encoding=sys.getfilesystemencoding())
    elif isinstance(filename, six.binary_type):
        return filename

    raise TypeError("Value is not a (byte) string")


def fsdecode_path(filename):
    """
    Decode byte filenames using the file system encoding.

    :filename: File path to decode
    :returns: Decoded path
    :raises: TypeError if wrong type given
    """
    if isinstance(filename, six.binary_type):
        return filename.decode(encoding=sys.getfilesystemencoding())
    elif isinstance(filename, six.text_type):
        return filename

    raise TypeError("Value is not a (byte) string")


def encode_id(text):
    """
    Give ID to given text with MD5 calculation.

    :text: Text to calculate
    :returns: MD5 hash of text prefixed with underscore.
    """
    return '_{}'.format(hashlib.md5(text.encode("utf-8")).hexdigest())


def tree():
    """
    Tree dictionary data structure from
    https://gist.github.com/hrldcpr/2012250

    :returns: Tree dictionary data structure
    """
    return defaultdict(tree)


def add(treedict, path):
    """
    Add new nodes in given path to tree.

    :treedict: Tree dictionary
    :path: Path to add
    :returns: Updated tree
    """
    root = None
    for node in path:
        treedict = treedict[node]
        root = treedict

    return root


def copy_etree(etree):
    """
    Copies etree recursively.

    :etree: Tree to copy.
    :returns: New identical etree.
    """
    return copy.deepcopy(etree)


def _pop_attributes(attributes, attrib_list, path):
    """
    Pops all the attributes from attributes dict and appends them to
    attrib_list.

    :attributes: lxml.etree.Element.attrib dictionary
    :attrib_list: List of all the attributes
    :path: Path from root XML element to current element
    """
    for key in attributes:
        attribute = attributes.pop(key)
        attrib_list.append('%s="%s" @ %s\n' % (key, attribute, path))


def _remove_identifiers(metadata, prefix, linking_prefix=None):
    """
    Removes the unique identifier and the linking identifiers for the
    PREMIS XML metadata.

    :metadata: Metadata where identifiers are removed
    :prefix: Prefix in the identifier element name
    :linking_prefix: Prefix in the linking identifier element name
    :returns: Edited metadata
    """
    for identifier in premis.iter_elements(
            metadata, '%sIdentifierValue' % prefix):
        identifier.getparent().remove(identifier)
    if linking_prefix:
        for linking_identifier in premis.iter_elements(
                metadata, 'linking%sIdentifierValue' % linking_prefix):
            linking_identifier.getparent().remove(linking_identifier)

    return metadata


def generate_digest(etree):
    """Generating MD5 digest from etree. Identical metadata must generate
    same digest even if attributes of any given element are ordered
    differently. Also some metadata sections contain unique identifiers
    that have to be removed if digest comparison is to work.

    This function creates a copy of the etree. All the attributes of the copy
    are removed and collected to a separete list with path information to the
    XML element the attributes belong to. This list is sorted and appended
    to the end of the serialized XML string without the attributes. Thus
    creating a string with all the original information except the information
    about attribute ordering inside any given XML element. This string is
    hashed and the digest returned. For some PREMIS metadata identifiers are
    also removed.

    :etree: XML element for which the MD5 hash is generated
    :returns: MD5 hash
    """

    # Creating copy of the original etree to avoid editing it
    root = copy_etree(etree)
    elem_tree = lxml.etree.ElementTree(root)
    attrib_list = []

    # Remove premis identifiers before metadata comparison
    elem_tree = _remove_identifiers(elem_tree, 'event', 'Agent')
    elem_tree = _remove_identifiers(elem_tree, 'agent')

    # pop all attributes
    for element in root.iter():
        attributes = element.attrib
        path = elem_tree.getpath(element)
        _pop_attributes(attributes, attrib_list, path)

    attrib_list.sort()
    xml_data = xml_helpers.utils.serialize(root)

    # Add the sorted attributes at the end of the serialized XML
    attr_data = b"".join([attr.encode("utf-8") for attr in attrib_list])
    xml_data = b"".join([xml_data, attr_data])

    return hashlib.md5(xml_data).hexdigest()


def list2str(lst):
    """Create a human readable list of words from list of strings.

    :param lst: list of strings
    :returns: list formatted as single string
    """
    first_words = ['"{}"'.format(string) for string in lst[:-1]]
    last_word = '"{}"'.format(lst[-1])
    return ', '.join(first_words) + ', and ' + last_word
