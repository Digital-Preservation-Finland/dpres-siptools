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


def create_techmdfile(workspace, metadatatype, metadata):
    """Wraps XML metadata into techMD element and writes it to a METS XML file
    in the workspace. The output filename is <metadatatype>-<hash>-othermd.xml,
    where <metadatatype> is the type of metadata given as parameter and <hash>
    is a string generated from the metadata.

    :workspace: directory where file is created
    :metadatype (string): type of metadata
    :metadata (Element): metadata XML element
    :returns: ID of techMD element written into the file
    """
    digest = hashlib.md5(xml_helpers.utils.serialize(metadata)).hexdigest()
    filename = encode_path("%s-%s-%s" % (metadatatype, digest, "othermd.xml"))
    techmd_id = encode_id(filename)

    if not os.path.exists(filename):

        techmd = mets.techmd(techmd_id)
        techmd.append(metadata)
        amdsec = mets.amdsec()
        amdsec.append(techmd)
        mets_ = mets.mets()
        mets_.append(amdsec)

        with open(os.path.join(workspace, filename), 'w+') as outfile:
            outfile.write(xml_helpers.utils.serialize(mets_))
            print "Wrote METS %s technical metadata to file %s" \
                  % (metadatatype, outfile.name)

    return techmd_id


def add_techmdreference(workspace, techmd_id, filepath):
    """Add techMD reference information to the reference list file:
    "techmd-references.xml", which is read by compile-structmap script when
    fileSec elements are created for METS XML.

    :workspace: directory where linking file is written
    :techmd_id: ID of techMD element to be referenced
    :filepath: path of the file described in techMD element
    :returns: None
    """

    reference_file = os.path.join(workspace, 'techmd-references.xml')

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

    # Add new reference
    reference = lxml.etree.Element('techmdReference')
    reference.text = techmd_id
    reference.set('file', filepath)
    references.append(reference)

    # Write reference list file
    references_tree.write(reference_file,
                          pretty_print=True,
                          xml_declaration=True,
                          encoding="utf-8")
