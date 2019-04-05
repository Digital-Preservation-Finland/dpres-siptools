"""
Utilities for siptools
"""

import sys
from collections import defaultdict
import hashlib
import os
from urllib import quote_plus, unquote_plus
import copy
import pickle
import lxml.etree
from file_scraper.scraper import Scraper
import xml_helpers
import mets
import premis


def scrape_file(filename, filerel=None, workspace=None):
    """Return already existing scraping result or create a new one, if
    missing.
    """
    if filerel is None:
        filerel = filename

    ref_exists = False
    if workspace is not None:
        ref = os.path.join(workspace, 'amd-references.xml')
        if os.path.isfile(ref):
            ref_exists = True

    if ref_exists:
        root = lxml.etree.parse(ref).getroot()
        amdref = root.xpath("/amdReferences/amdReference[not(@stream) "
                            "and @file='%s']" % filerel.decode(
                                sys.getfilesystemencoding()))[0]
        pkl_name = os.path.join(workspace, '%s-scraper.pkl' % amdref.text[1:])

        streams = None
        if not os.path.isfile(pkl_name):
            scraper = Scraper(filename)
            scraper.scrape(False)
            streams = scraper.streams
        else:
            with open(pkl_name, 'rb') as pkl_file:
                streams = pickle.load(pkl_file)
    else:
        scraper = Scraper(filename)
        scraper.scrape(False)
        streams = scraper.streams

    return streams


def fix_missing_metadata(streams, filenamei, allow_unav, allow_zero):
    """If an element is none, use value (:unav) if allowed in the
    specifications. Otherwise raise exception.
    """
    for index, stream in streams.iteritems():
        for key, element in stream.iteritems():
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
                        'index %s for file %s' % (key, str(index), filename))


def encode_path(path, suffix='', prefix='', safe=None):
    """Encode given path to URL encoding with given perfix and suffix
    """
    if safe:
        return prefix + quote_plus(path.encode('utf8'), safe=safe) + suffix
    return prefix + quote_plus(path.encode('utf8')) + suffix


def decode_path(path, suffix=''):
    """Decode given path from URL encoding and remove given suffix
    """
    path = unquote_plus(path)
    if path.endswith(suffix):
        path = path.replace(suffix, '', 1)
    return path.decode('utf8')


def encode_id(text):
    """Give ID to given text with MD5 calculation
    """
    return '_' + hashlib.md5(text).hexdigest()


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
    string = xml_helpers.utils.serialize(root)

    # Add the sorted attributes at the end of the serialized XML
    for attribute in attrib_list:
        string += attribute

    return hashlib.md5(string).hexdigest()


def get_objectlist(workspace, file_path=None):
    """Get unique and sorted list of files or streams from amd-references.xml

    :workspace: Workspace path
    :file_path: If given, finds streams of the given file.
                If None, finds a sorted list all file paths.
    :returns: Sorted list of files, or streams of a given file
    """
    reference_file = os.path.join(workspace, 'amd-references.xml')
    xml = lxml.etree.parse(reference_file)
    objectset = set()
    if file_path is not None:
        streams = xml.xpath(
            '/amdReferences/amdReference[@file="%s"]/@stream'
            '' % file_path)
        for stream in streams:
            objectset.add(stream)
    else:
        files = xml.xpath('/amdReferences/amdReference/@file')
        for path in files:
            objectset.add(path)
    return sorted(objectset)


class AmdCreator(object):
    """ Class for generating METS XML and amd-references files efficiently.
    """

    def __init__(self, workspace):
        """
        :workspace: Output path
        :md_elements: List of tuples (XML Element, filename, stream,
                      directory)
        :references: List of tuples (amd_id, filename, stream, directory)
        """
        self.workspace = workspace
        self.md_elements = []
        self.references = []

    def add_reference(self, amd_id, filepath, stream=None, directory=None):
        """Add administrative metadata reference information to the
        references list, which is written into amd-references after
        self.write() is called. amd-references is read by the
        compile-structmap script when fileSec elements are created for
        METS XML.

        :amd_id: ID of administrative MD element to be referenced
        :filepath: path of the file linking to the MD element
        :stream: id of the stream linking to the MD element
        :directory: path of the directory linking to the MD element

        :returns: None
        """
        references = {}
        references['amd_id'] = amd_id
        references['file'] = filepath
        references['stream'] = stream
        references['directory'] = directory
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
        AmdCreator.

        :metadata: Metadata XML element
        :filename: Path of the file linking to the MD element
        :stream: Stream index, or None if not a stream
        :directory: Path of the directory linking to the MD element

        :returns: None
        """

        md_element = (metadata, filename, stream, directory)
        self.md_elements.append(md_element)

    def write_references(self):
        """Write "amd-references.xml" file, which is read by
        the compile-structmap script when fileSec elements are
        created for METS XML.
        """

        reference_file = os.path.join(self.workspace, 'amd-references.xml')

        # read existing reference list file or create new file
        if os.path.exists(reference_file):
            with open(reference_file) as file_:
                # Remove blank text to enable pretty printing
                parser = lxml.etree.XMLParser(remove_blank_text=True)
                references_tree = lxml.etree.parse(file_, parser)
                references = references_tree.getroot()
        else:
            references = lxml.etree.Element('amdReferences')
            references_tree = lxml.etree.ElementTree(references)

        # Add all the references
        for ref in self.references:
            reference = lxml.etree.Element('amdReference')
            reference.text = ref['amd_id']
            for key in ref:
                if key == 'amd_id':
                    pass
                elif isinstance(ref[key], str):
                    reference.set(
                        key, ref[key].decode(sys.getfilesystemencoding()))
                elif isinstance(ref[key], unicode):
                    reference.set(key, ref[key])
                elif ref[key]:
                    reference.set(key, str(ref[key]))
                references.append(reference)

        # Write reference list file
        references_tree.write(reference_file,
                              pretty_print=True,
                              xml_declaration=True,
                              encoding="utf-8")

    def write_md(self, metadata, mdtype, mdtypeversion, othermdtype=None,
                 section=None, stdout=False):
        """Wraps XML metadata into administrative MD element and writes
        it to a METS XML file in the workspace. The output filename is
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

        :returns: amd_id, filename
        """
        digest = generate_digest(metadata)
        suffix = othermdtype if othermdtype else mdtype
        filename = encode_path("%s-%s-amd.xml" % (digest, suffix))
        amd_id = '_' + digest
        filename = os.path.join(self.workspace, filename)

        if not os.path.exists(filename):

            xmldata = mets.xmldata()
            xmldata.append(metadata)
            mdwrap = mets.mdwrap(mdtype, mdtypeversion, othermdtype)
            mdwrap.append(xmldata)
            if section == 'digiprovmd':
                amd = mets.digiprovmd(amd_id)
            else:
                amd = mets.techmd(amd_id)
            amd.append(mdwrap)
            amdsec = mets.amdsec()
            amdsec.append(amd)
            mets_ = mets.mets()
            mets_.append(amdsec)

            with open(filename, 'w+') as outfile:
                outfile.write(xml_helpers.utils.serialize(mets_))
                if stdout:
                    print xml_helpers.utils.serialize(mets_)
                print "Wrote METS %s administrative metadata to file %s" \
                      % (mdtype, outfile.name)

        return amd_id, filename

    def write_dict(self, scraper_streams, premis_amd_id):
        """Write streams to a file for further scripts.
        :streams: Streams from scraper
        :premis_amd_id: The AMDID of corresponding premis FILE object
        """
        digest = premis_amd_id[1:]
        filename = encode_path("%s-scraper.pkl" % digest)
        filename = os.path.join(self.workspace, filename)

        if not os.path.exists(filename):
            with open(filename, 'wb') as outfile:
                pickle.dump(scraper_streams, outfile)
            print "Wrote technical data to: %s" % (outfile.name)

    def write(self, mdtype="type", mdtypeversion="version", othermdtype=None,
              section=None, stdout=False, scraper_streams=None):
        """Write METS XML and amd-reference files. First, METS XML files are
        written and self.references is appended. Second, amd-references is
        written.

        If subclasses is optimized to call add_md once for each metadata type,
        self.references needs to be appended by the subclass for the instances
        where add_md was not called or write() function needs to be implemented
        differently.

        :mdtype (string): Value of mdWrap MDTYPE attribute
        :mdtypeversion (string): Value of mdWrap MDTYPEVERSION attribute
        :othermdtype (string): Value of mdWrap OTHERMDTYPE attribute
        :stdout (boolean): Print also to stdout

        :returns: None
        """

        # Write METS XML and append self.references
        for metadata, filename, stream, directory in self.md_elements:
            amd_id, _ = self.write_md(
                metadata, mdtype, mdtypeversion, othermdtype=othermdtype,
                section=section, stdout=stdout
            )
            if scraper_streams and stream is None:
                self.write_dict(scraper_streams, amd_id)
            self.add_reference(amd_id, filename, stream, directory)

        # Write amd-references
        self.write_references()

        # Clear references and md_elements
        self.__init__(self.workspace)
