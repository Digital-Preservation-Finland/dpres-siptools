"""
Utilities for siptools
"""
from __future__ import unicode_literals

import copy
import hashlib
import os
import pickle
import sys
from collections import defaultdict

import six

import lxml.etree
import mets
import premis
import xml_helpers
from file_scraper.scraper import Scraper

try:
    from urllib.parse import quote_plus, unquote_plus
except ImportError:  # Python 2
    from urllib import quote_plus, unquote_plus


def scrape_file(filename, filerel=None, workspace=None):
    """Return already existing scraping result or create a new one, if
    missing.
    """
    if filerel is None:
        filerel = filename

    ref_exists = False
    if workspace is not None:
        ref = os.path.join(workspace, 'md-references.xml')
        if os.path.isfile(ref):
            ref_exists = True

    if ref_exists:
        root = lxml.etree.parse(ref).getroot()
        filerel = fsdecode_path(filerel)

        amdref = root.xpath("/mdReferences/mdReference[not(@stream) "
                            "and @file='%s']" % filerel)
        pkl_name = None
        if amdref:
            pkl_name = os.path.join(
                workspace, '{}-scraper.pkl'.format(amdref[0].text[1:]))

        if pkl_name and os.path.isfile(pkl_name) and amdref:
            with open(pkl_name, 'rb') as pkl_file:
                return pickle.load(pkl_file)

    scraper = Scraper(filename)
    scraper.scrape(False)
    return scraper.streams


def fix_missing_metadata(streams, filename, allow_unav, allow_zero):
    """If an element is none, use value (:unav) if allowed in the
    specifications. Otherwise raise exception.
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
    """Encode given path to URL encoding with given perfix and suffix
    """
    if isinstance(path, six.text_type):
        path = path.encode("utf-8")

    if isinstance(safe, six.text_type):
        safe = safe.encode("utf-8")

    quoted = quote_plus(path, safe=safe)
    return "{}{}{}".format(prefix, quoted, suffix)


def decode_path(path, suffix=''):
    """Decode given path from URL encoding and remove given suffix
    """
    if six.PY2:
        path = path.encode("utf-8")

    path = unquote_plus(path).decode("utf-8")
    if path.endswith(suffix):
        path = path.replace(suffix, '', 1)
    return path


def fsencode_path(filename):
    """Encode Unicode filenames using the file system encoding"""
    if isinstance(filename, six.text_type):
        return filename.encode(encoding=sys.getfilesystemencoding())
    elif isinstance(filename, six.binary_type):
        return filename

    raise TypeError("Value is not a (byte) string")


def fsdecode_path(filename):
    """Decode byte filenames using the file system encoding"""
    if isinstance(filename, six.binary_type):
        return filename.decode(encoding=sys.getfilesystemencoding())
    elif isinstance(filename, six.text_type):
        return filename

    raise TypeError("Value is not a (byte) string")


def encode_id(text):
    """Give ID to given text with MD5 calculation
    """
    return '_{}'.format(hashlib.md5(text.encode("utf-8")).hexdigest())


def tree():
    """Tree dictionary data structure from
    https://gist.github.com/hrldcpr/2012250
    """
    return defaultdict(tree)


def add(treedict, path):
    """Add new nodes in given path to tree
    """
    root = None
    for node in path:
        treedict = treedict[node]
        root = treedict

    return root


def copy_etree(etree):
    """Copies etree recursively. Returns new identical etree
    """
    return copy.deepcopy(etree)


def _pop_attributes(attributes, attrib_list, path):
    """Pops all the attributes from attributes dict and appends them to
    attrib_list.

    :attributes: lxml.etree.Element.attrib dictionary
    :attrib_list: List of all the attributes
    :path: Path from root XML element to current element
    :returns: None
    """
    for key in attributes:
        attribute = attributes.pop(key)
        attrib_list.append('%s="%s" @ %s\n' % (key, attribute, path))


def _remove_identifiers(metadata, prefix, linking_prefix=None):
    """Removes the unique identifier and the linking identifiers for the
    PREMIS XML metadata.
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


def get_objectlist(workspace, file_path=None):
    """Get unique and sorted list of files or streams from md-references.xml

    :workspace: Workspace path
    :file_path: If given, finds streams of the given file.
                If None, finds a sorted list all file paths.
    :returns: Sorted list of files, or streams of a given file
    """
    reference_file = os.path.join(workspace, 'md-references.xml')
    xml = lxml.etree.parse(reference_file)
    objectset = set()
    if file_path is not None:
        streams = xml.xpath(
            '/mdReferences/mdReference[@file="%s"]/@stream'
            '' % file_path)
        for stream in streams:
            objectset.add(stream)
    else:
        files = xml.xpath('/mdReferences/mdReference/@file')
        for path in files:
            objectset.add(path)
    return sorted(objectset)


class MdCreator(object):
    """ Class for generating METS XML and md-references files efficiently.
    """

    def __init__(self, workspace):
        """
        :workspace: Output path
        :md_elements: List of tuples (XML Element, filename, stream,
                      directory)
        :references: List of tuples (md_id, filename, stream, directory)
        """
        self.workspace = workspace
        self.md_elements = []
        self.references = []

    def add_reference(self, md_id, filepath, stream=None, directory=None,
                      ref_type='amd'):
        """Add metadata reference information to the
        references list, which is written into md-references after
        self.write() is called. md-references is read by the
        compile-structmap script when fileSec and structMap elements
        are created for METS XML.

        :md_id: ID of MD element to be referenced
        :filepath: path of the file linking to the MD element
        :stream: id of the stream linking to the MD element
        :directory: path of the directory linking to the MD element
        :ref_type: type of MD section, e.g. 'amd' or 'dmd'

        :returns: None
        """
        references = {}
        references['md_id'] = md_id
        references['file'] = filepath
        references['stream'] = stream
        references['directory'] = directory
        references['ref_type'] = ref_type
        self.references.append(references)

    def add_md(self, metadata, filename=None, stream=None, directory=None):
        """Append metadata XML element into self.md_elements list.
        self.md_elements is read by write() function and all the elements
        are written into corresponding METS XML files.

        When write() is called write_md() automatically writes
        corresponding metadata to the same METS XML file. However,
        serializing and hashing the XML elements can be rather time consuming.
        If the metadata can be easily separated without serializing and
        hashing, this function should only be called once for each distinct
        metadata. This should be implemented by the subclasses of
        MdCreator.

        :metadata: Metadata XML element
        :filename: Path of the file linking to the MD element
        :stream: Stream index, or None if not a stream
        :directory: Path of the directory linking to the MD element

        :returns: None
        """

        md_element = (metadata, filename, stream, directory)
        self.md_elements.append(md_element)

    def write_references(self):
        """Write "md-references.xml" file, which is read by
        the compile-structmap script when fileSec and structMap elements
        are created for METS XML.
        """

        reference_file = os.path.join(self.workspace, 'md-references.xml')

        # read existing reference list file or create new file
        if os.path.exists(reference_file):
            with open(reference_file) as file_:
                # Remove blank text to enable pretty printing
                parser = lxml.etree.XMLParser(remove_blank_text=True)
                references_tree = lxml.etree.parse(file_, parser)
                references = references_tree.getroot()
        else:
            references = lxml.etree.Element('mdReferences')
            references_tree = lxml.etree.ElementTree(references)

        # Add all the references
        for ref in self.references:
            reference = lxml.etree.Element('mdReference')
            reference.text = ref['md_id']
            for key in ref:
                if key == 'md_id':
                    pass
                elif isinstance(ref[key], six.binary_type):
                    reference.set(
                        key, ref[key].decode(sys.getfilesystemencoding()))
                elif isinstance(ref[key], six.text_type):
                    reference.set(key, ref[key])
                elif ref[key]:
                    reference.set(key, six.text_type(ref[key]))
                references.append(reference)

        # Write reference list file
        references_tree.write(reference_file,
                              pretty_print=True,
                              xml_declaration=True,
                              encoding="utf-8")

    def write_md(self, metadata, mdtype, mdtypeversion, othermdtype=None,
                 section=None, stdout=False):
        """Wraps XML metadata into MD element and writes it to a METS XML
        file in the workspace. The output filename is
        <mdtype>-<hash>-othermd.xml, where <mdtype> is the type of metadata
        given as parameter and <hash> is a string generated from the metadata.

        Serializing and hashing the root xml element can be rather time
        consuming and as such this method should not be called for each file
        unless more efficient way of separating files by the metadata can't
        be easily implemented. This implementation should be done by the
        subclasses of metadata_creator.

        :metadata (Element): metadata XML element
        :mdtype (string): Value of mdWrap MDTYPE attribute
        :mdtypeversion (string): Value of mdWrap MDTYPEVERSION attribute
        :othermdtype (string): Value of mdWrap OTHERMDTYPE attribute
        :section (string): Type of mets metadata section
        :stdout (boolean): Print also to stdout

        :returns: md_id, filename
        """
        digest = generate_digest(metadata)
        suffix = othermdtype if othermdtype else mdtype
        filename = encode_path("%s-%s-amd.xml" % (digest, suffix))
        md_id = '_{}'.format(digest)
        filename = os.path.join(self.workspace, filename)

        if not os.path.exists(filename):

            xmldata = mets.xmldata()
            xmldata.append(metadata)
            mdwrap = mets.mdwrap(mdtype, mdtypeversion, othermdtype)
            mdwrap.append(xmldata)
            if section == 'digiprovmd':
                amd = mets.digiprovmd(md_id)
            else:
                amd = mets.techmd(md_id)
            amd.append(mdwrap)
            amdsec = mets.amdsec()
            amdsec.append(amd)
            mets_ = mets.mets()
            mets_.append(amdsec)

            with open(filename, 'wb+') as outfile:
                outfile.write(xml_helpers.utils.serialize(mets_))
                if stdout:
                    print(xml_helpers.utils.serialize(mets_).decode("utf-8"))
                print(
                    "Wrote METS %s administrative metadata to file %s" %
                    (mdtype, outfile.name)
                )

        return md_id, filename

    def write_dict(self, file_metadata_dict, premis_amd_id):
        """Write streams to a file for further scripts.
        :file_metadata_dict: File metadata dict
        :premis_amd_id: The AMDID of corresponding premis FILE object
        """
        digest = premis_amd_id[1:]
        filename = encode_path("%s-scraper.pkl" % digest)
        filename = os.path.join(self.workspace, filename)

        if not os.path.exists(filename):
            with open(filename, 'wb') as outfile:
                # TODO: pickle is overkill for serializing simple dicts
                # and might lead to remote code execution if the user
                # can find a way to modify the pickled file
                pickle.dump(file_metadata_dict, outfile)
            print("Wrote technical data to: %s" % (outfile.name))

    def write(self, mdtype="type", mdtypeversion="version", othermdtype=None,
              section=None, stdout=False, file_metadata_dict=None):
        """Write METS XML and md-reference files. First, METS XML files are
        written and self.references is appended. Second, md-references is
        written.

        If subclasses is optimized to call add_md once for each metadata type,
        self.references needs to be appended by the subclass for the instances
        where add_md was not called or write() function needs to be implemented
        differently.

        :mdtype (string): Value of mdWrap MDTYPE attribute
        :mdtypeversion (string): Value of mdWrap MDTYPEVERSION attribute
        :othermdtype (string): Value of mdWrap OTHERMDTYPE attribute
        :section (string): METS section type
        :stdout (boolean): Print also to stdout
        :file_metadat_dict (dict): File metadata dict
        :returns: None
        """

        # Write METS XML and append self.references
        for metadata, filename, stream, directory in self.md_elements:
            md_id, _ = self.write_md(
                metadata, mdtype, mdtypeversion, othermdtype=othermdtype,
                section=section, stdout=stdout
            )
            if file_metadata_dict and stream is None:
                self.write_dict(file_metadata_dict, md_id)
            self.add_reference(md_id, filename, stream, directory)

        # Write md-references
        self.write_references()

        # Clear references and md_elements
        self.__init__(self.workspace)


def remove_dmdsec_references(workspace):
    """
    Removes the reference to the dmdSecs in the 'md-references.xml'
    file.
    """
    refs_file = os.path.join(workspace, 'md-references.xml')
    if os.path.exists(refs_file):
        with open(refs_file) as file_:
            parser = lxml.etree.XMLParser(remove_blank_text=True)
            references_tree = lxml.etree.parse(file_, parser)
            refs = references_tree.getroot()
        for dmd in refs.xpath('/mdReferences/mdReference[@ref_type="dmd"]'):
            dmd.getparent().remove(dmd)

        references_tree.write(refs_file,
                              pretty_print=True,
                              xml_declaration=True,
                              encoding="utf-8")
