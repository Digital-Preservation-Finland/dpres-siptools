"""
Utilities for siptools
"""

import sys
from collections import defaultdict
import hashlib
import os
from urllib import quote_plus, unquote_plus
import copy
import lxml.etree

import xml_helpers
import mets


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


def generate_digest(etree):
    """Generating MD5 digest from etree. Identical metadata must generate
    same digest even if attributes of any given element are ordered
    differently.

    This function creates a copy of the etree. All the attributes of the copy
    are removed and collected to a separete list with path information to the
    XML element the attributes belong to. This list is sorted and appended
    to the end of the serialized XML string without the attributes. Thus
    creating a string with all the original information except the information
    about attribute ordering inside any given XML element. This string is
    hashed and the digest returned.

    :etree: XML element for which the MD5 hash is generated
    :returns: MD5 hash
    """

    # Creating copy of the original etree to avoid editing it
    root = copy_etree(etree)
    elem_tree = lxml.etree.ElementTree(root)
    attrib_list = []

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


def get_files(workspace):
    """Get unique and sorted set of files from amd-references.xml

    :workspace: Workspace path
    :returns: Set of files
    """
    reference_file = os.path.join(workspace, 'amd-references.xml')
    xml = lxml.etree.parse(reference_file)
    fileset = set()
    files = xml.xpath('/amdReferences/amdReference/@file')
    for path in files:
        fileset.add(path)
    return sorted(fileset)


def strip_zeros(float_str):
    """Recursively strip trailing zeros from a float i.e. strip_zeros("44.10")
    returns "44.1" and _srip_zeros("44.0") returns "44"
    """

    # if '.' is found in the string and string
    # ends in '0' or '.' strip last character
    if float_str.find(".") != -1 and float_str[-1] in ['0', '.']:
        return strip_zeros(float_str[:-1])

    return float_str


def iso8601_duration(time):
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
        seconds = strip_zeros("%.2f" % seconds)
        duration += "%sS" % seconds

    return duration


class AmdCreator(object):
    """ Class for generating METS XML and amd-references files efficiently.
    """

    def __init__(self, workspace):
        """
        :workspace: Output path
        :md_elements: List of tuples (XML Element, filename, stream)
        :references: List of tuples (amd_id, filename, stream)
        """
        self.workspace = workspace
        self.md_elements = []
        self.references = []

    def add_reference(self, amd_id, filepath, stream=None):
        """Add administrative metadata reference information to the
        references list, which is written into amd-references after
        self.write() is called. amd-references is read by the
        compile-structmap script when fileSec elements are created for
        METS XML.

        :amd_id: ID of administrative MD element to be referenced
        :filepath: path of the file linking to the MD element

        :returns: None
        """

        reference = (amd_id, filepath, stream)
        self.references.append(reference)

    def add_md(self, metadata, filename, stream=None):
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
        :filename: path of the file linking to the MD element
        :stream: Stream index, or None if not a stream

        :returns: None
        """

        md_element = (metadata, filename, stream)
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
        for amd_id, filepath, stream in self.references:
            reference = lxml.etree.Element('amdReference')
            reference.text = amd_id
            if isinstance(filepath, str):
                reference.set(
                    'file', filepath.decode(sys.getfilesystemencoding()))
            else:
                reference.set('file', filepath)
            if stream is not None:
                reference.set('stream', stream)
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
            if section == 'digiprovMd':
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

    def write(self, mdtype="type", mdtypeversion="version", othermdtype=None,
              section=None, stdout=False):
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
        for metadata, filename, stream in self.md_elements:
            amd_id, _ = self.write_md(
                metadata, mdtype, mdtypeversion, othermdtype=othermdtype,
                section=section, stdout=stdout
            )
            self.add_reference(amd_id, filename, stream)

        # Write amd-references
        self.write_references()

        # Clear references and md_elements
        self.__init__(self.workspace)
