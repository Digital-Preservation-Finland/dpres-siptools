""" Test"""
from siptools.scripts.import_description import main
import os
import lxml.etree
from lxml.etree import Element, SubElement, tostring

# Testi oikealle datalle: Tutki syntyneen dmdsec-oikeellisuus
# lukemalla lxml.etree.fromstring -funktiolla
# Tee testit myos epaonnistuneille tapauksille: Jos tiedostoa ei
# loydy, tiedosto ei ole xml:aa, metadata ei ole luettelossa (vaara
# nimiavaruus



    #print "File: %s" % os.path.isfile(dmdsec_location)
    #main([dmdsec_location,  '--workspace', workspace])
    #if not os.path.isdir(workspace):
    #    assert False

def validate_dmd_files(workspace, dmdsec_location):
    """ test """

    dmd_path = os.path.abspath(dmdsec_location)
    workspace_path = os.path.abspath(workspace)
    if os.path.isdir(dmd_path):
        for root, dirs, files in os.walk(dmd_path, topdown=False):
             for name in files:
                 t_path = os.path.join(workspace, name)
                 with open(t_path, 'r') as content_file:
                     content = content_file.read()
                     try:
                         parser = lxml.etree.XMLParser(
                                 dtd_validation=False, no_network=True)
                         tree = lxml.etree.fromstring(content)
                         print "isdir tree"
                     except lxml.etree.XMLSyntaxError as exception:
                         assert False
    else:
        filename = os.path.basename(dmd_path)
        t_path = os.path.join(workspace, filename)
        with open(t_path, 'r') as content_file:
            content = content_file.read()
            try:
                 parser = lxml.etree.XMLParser(
                         dtd_validation=False, no_network=True)
                 tree = lxml.etree.fromstring(content)
                 print "isfile tree"
            except lxml.etree.XMLSyntaxError as exception:
                assert False

    assert True

def test_import_description_valid_file():
    """ test """
    dmdsec_location = './workspace/metadata/dc_description.xml'
    workspace = './workspace/mets-parts'
    main([dmdsec_location,  '--workspace', workspace])
    validate_dmd_files(workspace, dmdsec_location)

def test_import_description_valid_directory():
    """ test """
    dmdsec_location = './workspace/metadata/'
    workspace = './workspace/mets-parts'
    main([dmdsec_location,  '--workspace', workspace])
    validate_dmd_files(workspace, dmdsec_location)

def test_import_description_file_not_found():
    """ test """
    dmdsec_location = './workspace/metadata/dc_description_not_found.xml'
    workspace = './workspace/mets-parts'
    main([dmdsec_location,  '--workspace', workspace])
    validate_dmd_files(workspace, dmdsec_location)

def test_import_description_no_workspace():
    """ test """
    dmdsec_location = './workspace/metadata/dc_description_not_found.xml'
    #workspace = './workspace/mets-parts'
    main([dmdsec_location])
    validate_dmd_files("./", dmdsec_location)

