"""
Utilities for siptools
"""
from __future__ import unicode_literals, print_function

import os
import sys
import json

import mets
import xml_helpers
from siptools.utils import generate_digest, encode_path


def _parse_refs(ref):
    """A helper function to parse the given reference according
    to the type.
    """
    reference = ''
    if isinstance(ref, bytes):
        reference = ref.decode(sys.getfilesystemencoding())
    elif isinstance(ref, str):
        reference = ref
    elif ref:
        reference = str(ref)

    return reference


def _uniques_list(reference_list, reference):
    """A helper function to append only unique values to a list."""
    set_list = set(reference_list)
    set_list.add(reference)

    return list(set_list)


def _get_path_from_reference_file(reference_file, ref_path):
    """An inner function to help read an existing JSON lines file.

    :reference_file: JSON Line reference file to read from.
    :ref_path: The ref_path key to look for.
    :return: Dictionary on finding, None when none is found.
    """
    with open(reference_file, 'r') as out_file:
        for line in out_file:
            try:
                return json.loads(line)[ref_path]
            except KeyError:
                continue
    return None


def _setup_new_path(path_type):
    """Sets up a new path dictionary. For cases when no prior path data
    is found among references.

    :path_type: Path type in question in string.
    :return: Newly constructed dictionary.
    """
    return dict(
        path_type=path_type,
        streams=dict(),
        md_ids=list()
    )


class MetsSectionCreator(object):
    """
    Class for generating lxml.etree XML for different METS metadata sections
    and corresponding md-references files efficiently.
    """

    def __init__(self, workspace):
        """
        Initialize metadata creator.

        :workspace: Output path
        """
        self.workspace = workspace
        self.md_elements = []
        self.references = []

    # pylint: disable=too-many-arguments
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
        references['stream'] = stream

        references['path'] = filepath
        references['path_type'] = 'file'
        if directory:
            references['path'] = directory
            references['path_type'] = 'directory'

        self.references.append(references)

    def add_md(self,
               metadata,
               filename=None,
               stream=None,
               directory=None,
               given_metadata_dict=None):
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
        :given_metadata_dict: Dict of file metadata
        """

        md_element = (
            metadata, filename, stream, directory, given_metadata_dict)
        self.md_elements.append(md_element)

    def write_references(self, ref_file):
        """
        Write "md-references.jsonl" file, which is read by the
        compile-structmap script when fileSec and structMap elements are
        created for lxml.etree XML.
        """

        reference_file = os.path.join(self.workspace, ref_file)

        path_map = {}
        paths = []
        # Whether or not the file initially exists.
        file_exists = os.path.exists(reference_file)
        # Collection of paths that underwent an update.
        paths_updated = set()
        for ref in self.references:
            ref_path = _parse_refs(ref['path'])

            # We'll first set data to path-variable for processing.
            try:
                # Set a reference if path being processed already exists.
                path = paths[path_map[ref_path]][ref_path]
            except KeyError:
                path = None
                if file_exists:
                    # Get existing path entry from a file.
                    path = _get_path_from_reference_file(reference_file,
                                                         ref_path)
                    if path is not None:
                        # Existing entry found.
                        paths_updated.add(ref_path)
                if path is None:
                    # No prior existing path so setting up new one.
                    path = _setup_new_path(ref['path_type'])
                # Map to list of paths that underwent processing.
                paths.append({ref_path: path})
                path_map[ref_path] = len(paths) - 1

            # Based on whether or not stream exists for the reference, we'll
            # update the reference list.
            if ref['stream']:
                try:
                    path['streams'][ref['stream']] = _uniques_list(
                        path['streams'][ref['stream']],
                        ref['md_id']
                    )
                except KeyError:
                    path['streams'][ref['stream']] = list()
                    path['streams'][ref['stream']].append(ref['md_id'])
            else:
                path['md_ids'] = _uniques_list(path['md_ids'], ref['md_id'])

            # After path-variable has been modified enough, set the updated
            # path dictionary back paths-collection.
            paths[path_map[ref_path]][ref_path] = path

        # Write reference list JSON line file
        if paths_updated:
            # Existing entries in reference file must be updated.
            # We'll proceed to write to a separate temporary file.
            with open(reference_file,
                      'rt') as in_file, open('%s.tmp' % reference_file,
                                             'at') as out_file:
                for line in in_file:
                    existing_json_data = json.loads(line)
                    for key in existing_json_data:
                        if key not in paths_updated:
                            out_file.write(line)

            for path in paths:
                with open('%s.tmp' % reference_file, 'at') as out_file:
                    json.dump(path, out_file)
                    out_file.write('\n')
        else:
            # If no existing entries required update, we'll append directly
            # to reference file.
            for path in paths:
                with open(reference_file, 'at') as out_file:
                    json.dump(path, out_file)
                    out_file.write('\n')

        # If temporary file was written, it'll replace the existing reference
        # file as a whole.
        if os.path.exists('%s.tmp' % reference_file):
            os.rename('%s.tmp' % reference_file, reference_file)

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
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

    # pylint: disable=too-many-arguments
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
        :file_metadata_dict (dict): File metadata dict
        :ref_file (string): Reference file name
        """
        # Write lxml.etree XML and append self.references
        for (metadata,
             filename,
             stream,
             directory,
             given_metadata_dict) in self.md_elements:
            md_id, _ = self.write_md(
                metadata, mdtype, mdtypeversion, othermdtype=othermdtype,
                section=section, stdout=stdout
            )
            if given_metadata_dict:
                file_metadata_dict = given_metadata_dict
            if file_metadata_dict and stream is None:
                self.write_dict(file_metadata_dict, md_id)
            self.add_reference(md_id, filename, stream, directory)

        # Write md-references
        self.write_references(ref_file)

        # Clear references and md_elements
        self.__init__(self.workspace)
