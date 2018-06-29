# coding=utf-8
"""Creates PREMIS file metadata for objects by reading METAX data
and using siptools for creation of data.
"""

import os
import sys
import argparse
import subprocess

import lxml.etree as ET
from wand.image import Image

from siptools.scripts import import_object
from siptools.utils import encode_path
from siptools.xml.namespaces import NAMESPACES
import siptools.xml.mets as m
import siptools.xml.premis as p
import siptools.xml.mix as mix
from siptools_research.utils.metax import Metax
from urllib import quote_plus


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line
    arguments.
    """
    parser = argparse.ArgumentParser(description='Tool for '
                                     'creating premis events')
    parser.add_argument("dataset_id", type=str, help="Metax id of dataset")
    parser.add_argument('--workspace', dest='workspace', type=str,
                        default='./workspace', help="Workspace directory")

    return parser.parse_args(arguments)


def create_premis_object(digital_object, filepath, formatname, creation_date,
                         hashalgorithm, hashvalue, format_version, workspace):
    """Calls import_object from siptools to create
    PREMIS file metadata.
    """
    #  For some reason the "files"-argument has to be a directory that is found in
    #  base_path, not a file. Therefore "files" is set to "./".
    import_object.main(['./', '--base_path', filepath,
                        '--workspace', workspace, '--skip_inspection',
                        '--format_name', formatname,
                        '--digest_algorithm', hashalgorithm,
                        '--message_digest', hashvalue,
                        '--date_created', creation_date,
                        '--format_version', format_version])


def create_objects(file_id=None, metax_filepath=None, workspace=None):
    """Gets file metadata from Metax and calls create_premis_object function"""

    metadata = Metax().get_data('files', file_id)

    filename = metadata["file_name"]
    # Assume that files are found in 'sip-in-progress' directory in workspace
    filepath = os.path.join(workspace, 'sip-in-progress')
    #Remove this line, when the metax test data is valid
    metax_filepath = metadata["file_path"].strip('/')
    hashalgorithm = metadata["checksum"]["algorithm"]
    hashvalue = metadata["checksum"]["value"]
    creation_date = metadata["file_characteristics"]["file_created"]
    formatname = metadata["file_format"]
    # formatversion hardcoded. Not in METAX yet. could be retrieved from file:
    formatversion = "1.0"

    # Picks name of hashalgorithm from its length if it's not valid
    allowed_hashs = {128: 'MD5', 160: 'SHA-1', 224: 'SHA-224',
                     256: 'SHA-256', 384: 'SHA-384', 512: 'SHA-512'}
    hash_bit_length = len(hashvalue) * 4

    if hashalgorithm in allowed_hashs.values():
        hashalgorithm = hashalgorithm
    elif hash_bit_length in allowed_hashs:
        hashalgorithm = allowed_hashs[hash_bit_length]
    else:
        hashalgorithm = 'ERROR'

    create_premis_object(filename, filepath, formatname,
                         creation_date, hashalgorithm,
                         hashvalue, formatversion,
                         workspace)

    #write xml if it exists
    xml = Metax().get_data('files', file_id + '/xml')
    for i in xml:
        if i not in NAMESPACES.values():
            raise TypeError("Invalid XML namespace: %s" % i)
        xml_data = Metax().get_data('files', file_id + '/xml?namespace=' + i)
        tree = ET.parse(xml_data)
        root = tree.getroot()

        ns_key = next((ns for ns, ns_url in NAMESPACES.items() if ns_url == i), None)
        target_filename = quote_plus(metax_filepath + '-' + ns_key + '-techmd.xml')
        output_file = os.path.join(workspace, target_filename)
        with open(output_file, 'w+') as outfile:
            outfile.write(ET.tostring(root))

    return 0


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    metax_dataset = Metax().get_data('datasets', args.dataset_id)
    for file_section in metax_dataset["research_dataset"]["files"]:
        file_id = file_section["identifier"]
        #get directory structure from Metax. 
        #doesn't work because of invalid test data in metax
        #metax_filepath = file_section['type']['label']['default'].strip('/')
        metax_filepath = None
        create_objects(file_id, metax_filepath, args.workspace)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
