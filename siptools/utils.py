"""
Utilities for siptools
"""

from collections import defaultdict
import hashlib
import os
from urllib import quote_plus, unquote_plus
import xml_helpers
import mets
import lxml.etree


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


class TechmdCreator(object):
    """ Class for generating METS XML and techmd-references files efficiently.
    """

    def __init__(self, workspace):
        """
        :workspace: Output path
        :md_elements: List of tuples (XML Element, filename)
        :references: List of tuples (techmd_id, filename)
        """
        self.workspace = workspace
        self.md_elements = []
        self.references = []


    def add_reference(self, techmd_id, filepath):
        """Add techMD reference information to the references list,
        which is written into techmdreferences after self.write() is
        called. techmdreferences is read by compile-structmap script when
        fileSec elements are created for METS XML.

        :techmd_id: ID of techMD element to be referenced
        :filepath: path of the file described in techMD element

        :returns: None
        """

        reference = (techmd_id, filepath)
        self.references.append(reference)


    def add_md(self, metadata, filename):
        """Append metadata XML element into self.md_elements list.
        self.md_elements is read by write() function and all the elements
        are written into corresponding METS XML files.

        When write() is called create_techmdfile() automatically writes
        corresponding metadata to the same METS XML file. However,
        serializing and hashing the XML elements can be rather time consuming.
        If the metadata can be easily separated without serializing and hashing,
        this function should only be called once for each distinct metadata.
        This should be implemented by the subclasses of TechmdCreator.

        :metadata: Metadata XML element

        :returns: None
        """

        md = (metadata, filename)
        self.md_elements.append(md)


    def write_references(self):
        """Write "techmd-references.xml" file, which is read by
        compile-structmap script when fileSec elements are
        created for METS XML.
        """

        reference_file = os.path.join(self.workspace, 'techmd-references.xml')

        # read existing reference list file or create new file
        if os.path.exists(reference_file):
            with open(reference_file) as file_:
                # Remove blank text to enable pretty printing
                parser = lxml.etree.XMLParser(remove_blank_text=True)
                references_tree = lxml.etree.parse(file_, parser)
                references = references_tree.getroot()
        else:
            references = lxml.etree.Element('techmdReferences')
            references_tree = lxml.etree.ElementTree(references)

        # Add all the references
        for techmd_id, filepath in self.references:
            reference = lxml.etree.Element('techmdReference')
            reference.text = techmd_id
            reference.set('file', filepath)
            references.append(reference)

        # Write reference list file
        references_tree.write(reference_file,
                              pretty_print=True,
                              xml_declaration=True,
                              encoding="utf-8")


    def write_md(self, metadata, mdtype, mdtypeversion, othermdtype=None):
        """Wraps XML metadata into techMD element and writes it to a METS XML
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
        :returns: techmd_id, filename
        """
        digest = hashlib.md5(xml_helpers.utils.serialize(metadata)).hexdigest()
        suffix = othermdtype if othermdtype else mdtype
        filename = encode_path("%s-%s-techmd.xml" % (digest, suffix))
        techmd_id = encode_id(filename)
        filename = os.path.join(self.workspace, filename)

        if not os.path.exists(filename):

            xmldata = mets.xmldata()
            xmldata.append(metadata)
            mdwrap = mets.mdwrap(mdtype, mdtypeversion, othermdtype)
            mdwrap.append(xmldata)
            techmd = mets.techmd(techmd_id)
            techmd.append(mdwrap)
            amdsec = mets.amdsec()
            amdsec.append(techmd)
            mets_ = mets.mets()
            mets_.append(amdsec)

            with open(filename, 'w+') as outfile:
                outfile.write(xml_helpers.utils.serialize(mets_))
                print "Wrote METS %s technical metadata to file %s" \
                      % (mdtype, outfile.name)

        return techmd_id, filename


    def write(self, mdtype, mdtypeversion, othermdtype=None):
        """Write METS XML and techmdreference files. First, METS XML files are
        written and self.references is appended. Second, techmd-references is
        written.

        If subclasses is optimized to call add_md once for each metadata type,
        self.references needs to be appended by the subclass for the instances
        where add_md was not called or write() function needs to be implemented
        differently.

        :returns: None
        """

        # Write METS XML and append self.references
        for metadata, filename in self.md_elements:

            techmd_id, techmd_fname = self.write_md(
                metadata, mdtype, mdtypeversion, othermdtype=othermdtype
            )

            self.add_reference(techmd_id, filename)

        # Write techmd-references
        self.write_references()

        # Clear references and md_elements
        self.__init__(self.workspace)
