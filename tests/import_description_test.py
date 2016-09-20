""" Test"""
from siptools.scripts.import_description import main
import os
import lxml.etree
from lxml.etree import Element, SubElement, tostring
import pytest
from urllib import quote

# Testi oikealle datalle: Tutki syntyneen dmdsec-oikeellisuus
# lukemalla lxml.etree.fromstring -funktiolla
# Tee testit myos epaonnistuneille tapauksille: Jos tiedostoa ei
# loydy, tiedosto ei ole xml:aa, metadata ei ole luettelossa (vaara
# nimiavaruus

def validate_dmd_files(workspace, dmdsec_location):
    """ Validate created xml-file by parser"""

    dmd_path = os.path.abspath(dmdsec_location)
    workspace_path = os.path.abspath(workspace)
    if os.path.isdir(dmd_path):
        for root, dirs, files in os.walk(dmd_path, topdown=False):
             for name in files:
                 url_t_path = quote(dmdsec_location,safe='') + name
                 t_path = os.path.join(workspace, url_t_path)
                 with open(t_path, 'r') as content_file:
                     content = content_file.read()
                     parser = lxml.etree.XMLParser(
                             dtd_validation=False, no_network=True)
                     tree = lxml.etree.fromstring(content)
    else:
        if not os.path.isfile(dmd_path):
            raise IOError( "File or directory not found: %s" % dmd_path )
        filename = os.path.basename(dmd_path)
        url_t_path = quote(dmdsec_location,safe='')
        t_path = os.path.join(workspace, url_t_path)
        with open(t_path, 'r') as content_file:
            content = content_file.read()
            parser = lxml.etree.XMLParser(
                    dtd_validation=False, no_network=True)
            tree = lxml.etree.fromstring(content)

def test_import_description_valid_file():
    """ Test case for single valid xml-file"""
    dmdsec_location = 'tests/import_description/metadata/dc_description.xml'
    url_location = quote(dmdsec_location, safe='')
    workspace = './workspace/mets-parts'
    main([dmdsec_location,  '--workspace', workspace])
    validate_dmd_files(workspace, dmdsec_location)

def test_import_description_no_workspace():
    """ Test case for single valid xml-file. Uses default workspace location."""
    dmdsec_location = 'tests/import_description/metadata/dc_description.xml'
    main([dmdsec_location])
    validate_dmd_files("./", dmdsec_location)

def test_import_description_valid_directory():
    """ Test case for metadata directory, which consists of several valid
    xml-files."""
    dmdsec_location = 'tests/import_description/metadata/'
    workspace = './workspace/mets-parts'
    main([dmdsec_location,  '--workspace', workspace])
    validate_dmd_files(workspace, dmdsec_location)

def test_import_description_file_not_found():
    """ Test case for not existing xml-file."""
    dmdsec_location = 'tests/import_description/metadata/dc_description_not_found.xml'
    workspace = './workspace/mets-parts'
    with pytest.raises(IOError):
        main([dmdsec_location,  '--workspace', workspace])

def test_import_description_no_xml():
    """ test case for invalid XML file """
    dmdsec_location = 'tests/import_description/metadata/plain_text.xml'
    workspace = './workspace/mets-parts'
    main([dmdsec_location,  '--workspace', workspace])
    validate_dmd_files(workspace, dmdsec_location)

def test_import_description_invalid_namespace():
    """ test case for invalid namespace in XML file """
    dmdsec_location = 'tests/import_description/dc_invalid_ns.xml'
    workspace = './workspace/mets-parts'
    with pytest.raises(TypeError):
        main([dmdsec_location,  '--workspace', workspace])
