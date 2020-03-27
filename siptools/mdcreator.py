"""
Utilities for siptools
"""
from __future__ import unicode_literals, print_function

import os
import sys
import json

import six

import lxml.etree
import mets
import xml_helpers
from siptools.utils import generate_digest, encode_path


class MetsSectionCreator(object):
    """
    Class for generating lxml.etree XML for different METS metadata sections
    and corresponing md-references files efficiently.
    """

    def __init__(self, workspace):
        """
        Initialize metadata creator.

        :workspace: Output path
        """
        self.workspace = workspace
        self.md_elements = []
        self.references = []

    #pylint: disable=too-many-arguments
    def add_reference(self, md_id, filepath, stream=None, directory=None):
        """
        Add metadata reference information to the references list, which is
        written into md-references after self.write() is called. md-references
        is read by the compile-structmap script when fileSec and structMap
        elements are created for lxml.etree XML.

        :md_id: ID of MD element to be referenced
        :filepath: path of the file linking to the MD element
        :stream: id of the stream linking to the MD element
        :directory: path of the directory linking to the MD element
        """
        references = {}
        references['md_id'] = md_id
        references['file'] = filepath
        references['stream'] = stream
        references['directory'] = directory
        self.references.append(references)

    def add_md(self, metadata, filename=None, stream=None, directory=None):
        """
        Append metadata XML element into self.md_elements list.
        self.md_elements is read by write() function and all the elements
        are written into corresponding lxml.etree XML files.

        When write() is called write_md() automatically writes
        corresponding metadata to the same lxml.etree XML file. However,
        serializing and hashing the XML elements can be rather time consuming.
        If the metadata can be easily separated without serializing and
        hashing, this function should only be called once for each distinct
        metadata. This should be implemented by the subclasses of
        MetsSectionCreator.

        :metadata: Metadata XML element
        :filename: Path of the file linking to the MD element
        :stream: Stream index, or None if not a stream
        :directory: Path of the directory linking to the MD element
        """

        md_element = (metadata, filename, stream, directory)
        self.md_elements.append(md_element)

    def write_references(self, ref_file):
        """
        Write "md-references.xml" file, which is read by the compile-structmap
        script when fileSec and structMap elements are created for lxml.etree
        XML.
        """

        reference_file = os.path.join(self.workspace, ref_file)

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

    #pylint: disable=too-many-arguments
    #pylint: disable=too-many-locals
    def write_md(self, metadata, mdtype, mdtypeversion, othermdtype=None,
                 section=None, stdout=False):
        """
        Wraps XML metadata into MD element and writes it to a lxml.etree XML
        file in the workspace. The output filename is
            <mdtype>-<hash>-othermd.xml,
        where <mdtype> is the type of metadata given as parameter and <hash>
        is a string generated from the metadata.

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
        :returns: md_id, filename - Metadata id and filename
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
                    "Wrote lxml.etree %s administrative metadata to file "
                    "%s" % (mdtype, outfile.name)
                )

        return md_id, filename

    def write_dict(self, file_metadata_dict, premis_amd_id):
        """
        Write streams to a file for further scripts.

        :file_metadata_dict: File metadata dict
        :premis_amd_id: The AMDID of corresponding premis FILE object
        """
        digest = premis_amd_id[1:]
        filename = encode_path("%s-scraper.json" % digest)
        filename = os.path.join(self.workspace, filename)

        if not os.path.exists(filename):
            with open(filename, 'wt') as outfile:
                json.dump(file_metadata_dict, outfile)
            print("Wrote technical data to: %s" % (outfile.name))

    #pylint: disable=too-many-arguments
    def write(self, mdtype="type", mdtypeversion="version",
              othermdtype=None, section=None, stdout=False,
              file_metadata_dict=None, ref_file=None):
        """
        Write lxml.etree XML and md-reference files. First, METS XML files
        are written and self.references is appended. Second, md-references is
        written.

        If subclasses is optimized to call add_md once for each metadata type,
        self.references needs to be appended by the subclass for the instances
        where add_md was not called or write() function needs to be implemented
        differently.

        :mdtype (string): Value of mdWrap MDTYPE attribute
        :mdtypeversion (string): Value of mdWrap MDTYPEVERSION attribute
        :othermdtype (string): Value of mdWrap OTHERMDTYPE attribute
        :section (string): lxml.etree section type
        :stdout (boolean): Print also to stdout
        :file_metadat_dict (dict): File metadata dict
        :ref_file (string): Reference file name
        """
        # Write lxml.etree XML and append self.references
        for metadata, filename, stream, directory in self.md_elements:
            md_id, _ = self.write_md(
                metadata, mdtype, mdtypeversion, othermdtype=othermdtype,
                section=section, stdout=stdout
            )
            if file_metadata_dict and stream is None:
                self.write_dict(file_metadata_dict, md_id)
            self.add_reference(md_id, filename, stream, directory)

        # Write md-references
        self.write_references(ref_file)

        # Clear references and md_elements
        self.__init__(self.workspace)


def get_objectlist(xml, file_path=None):
    """Get unique and sorted list of files or streams from md-references.xml

    :xml: XML tree of objects
    :file_path: If given, finds streams of the given file.
                If None, finds a sorted list all file paths.
    :returns: Sorted list of files, or streams of a given file
    """
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


def remove_dmdsec_references(workspace):
    """
    Removes the reference to the dmdSecs in the md-references.xml file.

    :workspace: Workspace path
    """
    refs_file = os.path.join(workspace,
                             'import-description-md-references.xml')
    if os.path.exists(refs_file):
        os.remove(refs_file)


def read_all_amd_references(workspace):
    """
    Collect all administrative references.

    :workspace: path to workspace directory
    :returns: a set of administrative MD IDs
    """
    references = None
    for ref_file in ["import-object-md-references.xml",
                     "create-addml-md-references.xml",
                     "create-audiomd-md-references.xml",
                     "create-mix-md-references.xml",
                     "create-videomd-md-references.xml",
                     "premis-event-md-references.xml"]:
        if references is None:
            references = read_md_references(workspace, ref_file)
        else:
            refs = read_md_references(workspace, ref_file)
            if refs is not None:
                for ref in refs:
                    references.append(ref)

    return references


def read_md_references(workspace, ref_file):
    """If MD reference file exists in workspace, read
    all the MD IDs as element_tree.

    :workspace: path to workspace directory
    :ref_file: Metadata reference file
    :returns: Root of the reference tree
    """
    reference_file = os.path.join(workspace, ref_file)

    if os.path.isfile(reference_file):
        return lxml.etree.parse(reference_file).getroot()
    return None

def get_md_references(element_tree, path=None, stream=None, directory=None):
    """
    Return filtered references from a set of given references.
    :element_tree: XML etree of references to be filtered
    :path: Filter by given file path
    :stream: Filter by given strean index
    :directory: Filter by given directory path
    """
    if element_tree is None:
        return None

    if directory is None and path is None and stream is None:
        reference_elements = element_tree.xpath(
            '/mdReferences/mdReference'
        )
    elif directory:
        directory = os.path.normpath(directory)
        reference_elements = element_tree.xpath(
            '/mdReferences/mdReference'
            '[@directory="%s"]' % directory
        )
    elif stream is None:
        reference_elements = element_tree.xpath(
            '/mdReferences/mdReference[@file="%s" '
            'and not(@stream)]' % path
        )
    else:
        reference_elements = element_tree.xpath(
            '/mdReferences/mdReference[@file="%s" '
            'and @stream="%s"]' % (path, stream)
        )
    md_ids = [element.text for element in reference_elements]

    return set(md_ids)
