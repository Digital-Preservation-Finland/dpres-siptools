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
        refs_file = os.path.join(workspace,
                                 'import-object-md-references.jsonl')
        if os.path.isfile(refs_file):
            ref_exists = True

    if ref_exists:
        refs = read_md_references(workspace,
                                  'import-object-md-references.jsonl')
        filerel = fsdecode_path(filerel)
        try:
            amdrefs = refs[filerel]['md_ids']
        except KeyError:
            amdrefs = []

        json_name = None
        for amdref in amdrefs:
            json_name = os.path.join(
                workspace, '{}-scraper.json'.format(amdref[1:]))
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
        error_str = ensure_str(error_str)
        if skip_well_check:
            error_head = ensure_str(
                "Metadata of file %s could not " \
                "be collected due to errors.\n") % ensure_str(filepath)
            error_str = error_head + error_str
        # Ensure exception is printed in full on both Python 2 & 3 by coercing
        # to 'str'
        raise ValueError(error_str)

    if scraper.info[0]['class'] == 'FileExists' and scraper.info[0]['errors']:
        raise IOError(scraper.info[0]['errors'])
    for _, info in six.iteritems(scraper.info):
        if info['class'] == 'ScraperNotFound':
            raise ValueError('File format is not supported.')

    return (scraper.streams, scraper.info)

# Adaptation of ensure_str function from version 1.15 of six,
# included for compatibility with older six versions
def ensure_str(s, encoding='utf-8', errors='strict'):
    """Coerce *s* to `str`.
    For Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`
    For Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`

    Adapted from release 1.15 of six::
        https://github.com/benjaminp/six/blob/master/six.py#L900

    :encoding: Used encoding
    :errors: Error handling level
    """
    if six.PY3:
        text_type = str
        binary_type = bytes
    else:
        text_type = unicode
        binary_type = str

    if type(s) is str:
        return s
    if six.PY2 and isinstance(s, text_type):
        return s.encode(encoding, errors)
    elif six.PY3 and isinstance(s, binary_type):
        return s.decode(encoding, errors)
    elif not isinstance(s, (text_type, binary_type)):
        raise TypeError("not expecting type '%s'" % type(s))
    return s

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


def _remove_elements(metadata, element_name):
    """
    Removes the unique elements like identifiers and the linking
    agents for the PREMIS XML metadata.

    :metadata: Metadata where identifiers and linking elements are
               removed
    :element_name: The name of the element to be removed
    :returns: Edited metadata
    """
    for element_to_remove in premis.iter_elements(
            metadata, element_name):
        element_to_remove.getparent().remove(element_to_remove)

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

    # Remove premis identifiers and linking elements before metadata comparison
    elem_tree = _remove_elements(elem_tree, 'eventIdentifierValue')
    elem_tree = _remove_elements(elem_tree, 'agentIdentifierValue')
    elem_tree = _remove_elements(elem_tree, 'linkingAgentIdentifier')

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


def read_md_references(workspace, ref_file):
    """If MD reference file exists in workspace, read
    all the MD IDs as a dictionary.

    :workspace: path to workspace directory
    :ref_file: Metadata reference file
    :returns: A dict of references or None if reference file doesn't exist
    """
    reference_file = os.path.join(workspace, ref_file)

    if os.path.isfile(reference_file):
        references = {}
        with open(reference_file) as in_file:
            for line in in_file:
                references.update(json.loads(line))
        return references
    return None


def get_objectlist(refs_dict, file_path=None):
    """Get unique and sorted list of files or streams from
    md-references.jsonl

    :refs_dict: Dictionary of objects
    :file_path: If given, finds streams of the given file.
                If None, finds a sorted list all file paths.
    :returns: Sorted list of files, or streams of a given file
    """
    objectset = set()
    if file_path is not None:
        for stream in refs_dict[file_path]['streams']:
            objectset.add(stream)
    elif refs_dict:
        for key, value in six.iteritems(refs_dict):
            if value['path_type'] == 'file':
                objectset.add(key)

    return sorted(objectset)


def remove_dmdsec_references(workspace):
    """
    Removes the reference to the dmdSecs in the md-references.jsonl file.

    :workspace: Workspace path
    """
    refs_file = os.path.join(workspace,
                             'import-description-md-references.jsonl')
    if os.path.exists(refs_file):
        os.remove(refs_file)


def read_all_amd_references(workspace):
    """
    Collect all administrative references.

    :workspace: path to workspace directory
    :returns: a set of administrative MD IDs
    """
    references = {}
    for ref_file in ["import-object-md-references.jsonl",
                     "create-addml-md-references.jsonl",
                     "create-audiomd-md-references.jsonl",
                     "create-mix-md-references.jsonl",
                     "create-videomd-md-references.jsonl",
                     "premis-event-md-references.jsonl"]:
        refs = read_md_references(workspace, ref_file)
        if refs:
            for ref in refs:
                if ref in references:
                    references[ref]['md_ids'].extend(refs[ref]['md_ids'])

                    for stream in refs[ref]['streams']:
                        if stream in references[ref]['streams']:
                            references[ref]['streams'][stream].extend(
                                refs[ref]['streams'][stream])
                        else:
                            references[ref]['streams'][stream] = \
                                refs[ref]['streams'][stream]

                else:
                    references[ref] = refs[ref]

    return references


def get_md_references(refs_dict, path=None, stream=None, directory=None):
    """
    Return filtered references from a set of given references.
    :refs_dict: Dictionary of references to be filtered
    :path: Filter by given file path
    :stream: Filter by given strean index
    :directory: Filter by given directory path
    """
    if refs_dict is None:
        return None

    md_ids = []
    try:
        if directory is None and path is None and stream is None:
            for ref_path in refs_dict:
                md_ids.extend(refs_dict[ref_path]['md_ids'])
        elif directory:
            directory = os.path.normpath(directory)
            md_ids = refs_dict[directory]['md_ids']

        elif stream is None:
            md_ids = refs_dict[path]['md_ids']
        else:
            md_ref = refs_dict[path]
            for ref_stream in md_ref['streams']:
                if ref_stream == stream:
                    md_ids = md_ref['streams'][ref_stream]
    except KeyError:
        pass

    return set(md_ids)
