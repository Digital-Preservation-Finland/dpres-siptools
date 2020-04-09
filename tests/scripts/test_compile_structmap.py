"""Tests for the compile_structmap script."""
from __future__ import unicode_literals

import os
import shutil

import lxml.etree
import mets
from siptools.scripts import (compile_structmap, create_audiomd,
                              import_description, import_object, premis_event)
from siptools.xml.mets import NAMESPACES


def create_test_data(workspace, run_cli):
    """Create technical metadata test data."""
    run_cli(import_object.main, [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Software files/koodi.java'])
    run_cli(premis_event.main, [
        'creation', '2016-10-13T12:30:55',
        '--event_outcome_detail', 'Test ok',
        '--event_detail', 'Testing', '--event_outcome',
        'success', '--workspace', workspace, '--event_target',
        'tests/data/structured/Software files'])


def test_compile_structmap_ok(testpath, run_cli):
    """Test the compile_structmap script."""
    create_test_data(testpath, run_cli)
    run_cli(compile_structmap.main, ['--workspace', testpath])

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = lxml.etree.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = lxml.etree.parse(output_filesec)
    fs_root = fs_tree.getroot()

    assert len(fs_root.xpath(
        '/mets:mets/mets:fileSec/mets:fileGrp/mets:file/'
        'mets:FLocat[@xlink:href="file://tests/data/structured/'
        'Software+files/koodi.java"]',
        namespaces=NAMESPACES
    )) == 1

    assert len(sm_root.xpath('//mets:div[@TYPE="Software files"]',
                             namespaces=NAMESPACES)) == 1

    # Assert that an event has been created
    root = lxml.etree.parse(
        os.path.join(testpath, 'premis-event-md-references.xml')).getroot()
    id_xpath = "/mdReferences/mdReference[@directory='.']"
    for amdref in root.xpath(id_xpath):
        output = os.path.join(
            testpath, amdref.text[1:] + '-PREMIS%3AEVENT-amd.xml')
        if os.path.exists(output):
            event_output = output
    event_output_path = os.path.join(testpath, event_output)
    event_root = lxml.etree.parse(event_output_path).getroot()
    assert event_root.xpath('./*/*/*/*/*')[0].tag == \
        '{info:lc/xmlns/premis-v2}event'
    assert event_root.xpath(
        '//premis:eventDetail',
        namespaces=NAMESPACES)[0].text == 'Creation of structural metadata'


def test_compile_structmap_dmdsecid(testpath, run_cli):
    """Test the compile_structmap script for workspace that contains
    descriptive metadata in dmdsec.xml file. The ID of dmdSec should be
    included in structMap.
    """
    # Create -premis-amd.xml and dmdsec.xml files in workspace
    run_cli(import_object.main, [
        '--workspace', testpath, '--skip_wellformed_check',
        'tests/data/structured/Software files/koodi.java'])
    import_description.import_description(
        dmdsec_location='tests/data/import_description/metadata/'
                        'dc_description.xml',
        workspace=testpath)

    # Create structmap
    run_cli(compile_structmap.main, ['--workspace', testpath])

    # The root div of structMap should have reference to dmdSec element in
    # dmdsec.xml

    ref = os.path.join(testpath, 'import-description-md-references.xml')
    root = lxml.etree.parse(ref).getroot()
    dmdref = root.xpath("/mdReferences/mdReference"
                        "[@directory='.']")[0]
    dmdsecid = dmdref.text

    structmap = lxml.etree.parse(os.path.join(testpath, 'structmap.xml'))
    assert len(
        structmap.xpath(
            '/mets:mets/mets:structMap/mets:div[@DMDID="%s"]' % dmdsecid,
            namespaces=NAMESPACES
        )
    ) == 1


def test_compile_structmap_not_ok(testpath, run_cli):
    """Test that error is raised for non-existent folders."""
    result = run_cli(
        compile_structmap.main,
        ['tests/data/notfound', '--workspace', testpath],
        success=False
    )
    assert isinstance(result.exception, SystemExit)


def test_file_and_dir(testpath, run_cli):
    """Test the cmpile_structmap with a file and directory case."""
    run_cli(import_object.main, [
        '--workspace', testpath, '--skip_wellformed_check',
        'tests/data/file_and_dir'])
    run_cli(compile_structmap.main, ['--workspace', testpath])
    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = lxml.etree.parse(output_structmap)
    sm_root = sm_tree.getroot()
    elementlist = sm_root.xpath(
        '/mets:mets/mets:structMap/mets:div/mets:div/mets:div/mets:div/*',
        namespaces=NAMESPACES)
    assert elementlist[0].tag == '{%s}fptr' % NAMESPACES['mets']
    assert elementlist[1].tag == '{%s}div' % NAMESPACES['mets']


def test_othermd_references(testpath, run_cli):
    """Test that main function creates references to othermd-metadata from file
    element in fileSec. A sample workspace contains aMD files, MIX metadata
    files, and aMD reference file for three image files. Two of the images
    are similar and therefore have same MIX metadata.
    """

    # Copy workspace to temporary directory
    workspace = os.path.join(testpath, 'workspace')
    shutil.copytree('tests/data/compile_structmap_workspace', workspace)

    # Compile structmap
    run_cli(compile_structmap.main, ['--workspace', workspace])

    # Read filesec.xml
    mets_document = lxml.etree.parse(os.path.join(workspace, 'filesec.xml'))
    namespaces = {'mets': "http://www.loc.gov/METS/",
                  'xlink': "http://www.w3.org/1999/xlink"}

    # fileGrp section should contain 3 file elements
    files = mets_document.xpath(
        '/mets:mets/mets:fileSec/mets:fileGrp/mets:file', namespaces=namespaces
    )
    assert len(files) == 3

    # This dictonary maps filepath to MIX techMD IDs excpected to be referenced
    # in fileSec
    amd_ids = {"sample_images/sample_tiff1_compressed.tif":
               "_c08061e439bd40407c9e5332fec6084e",
               "sample_images/sample_tiff1.tif":
               "_e50655691d21e110a3c4b38da52fb91c",
               "sample_images/sample_tiff2.tif":
               "_e50655691d21e110a3c4b38da52fb91c"}

    for filepath in amd_ids:
        # Find file element from mets based on filepath
        xpath = '//mets:FLocat[@xlink:href="file://%s"]/parent::mets:file' \
            % filepath
        file_element = mets_document.xpath(xpath, namespaces=namespaces)

        # The file element should have reference to techMD element defined in
        # ``amd_ids`` dictionary
        assert amd_ids[filepath] in file_element[0].get('ADMID')


# pylint: disable=invalid-name
def test_compile_structmap_directory(testpath, run_cli):
    """Test the compile_structmap script. Assert that directory
    structure is transferred to the structmap and that the premis
    event ID created in the test data is linked to the correct div
    element.
    """
    create_test_data(testpath, run_cli)
    run_cli(compile_structmap.main, [
        '--workspace', testpath, '--structmap_type', 'Directory-physical'
    ])
    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = lxml.etree.parse(output_structmap)
    sm_root = sm_tree.getroot()

    assert len(sm_root.xpath('//mets:div[@TYPE="directory" and '
                             '@LABEL="Software files"]',
                             namespaces=NAMESPACES)) == 1

    assert sm_root.xpath(
        '//mets:div[@TYPE="directory" and @LABEL="Software files"]',
        namespaces=NAMESPACES
    )[0].get('ADMID') == '_7c1eea4ea4ac7ccadb9199773a026121'


def test_compile_structmap_order(testpath, run_cli):
    """Test the compile_structmap script."""
    run_cli(import_object.main, [
        '--workspace', testpath,
        '--skip_wellformed_check',
        '--order', '5',
        'tests/data/audio/valid__wav.wav'])

    run_cli(create_audiomd.main, [
        '--workspace', testpath, 'tests/data/audio/valid__wav.wav'])

    run_cli(compile_structmap.main, ['--workspace', testpath])

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = lxml.etree.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = lxml.etree.parse(output_filesec)
    fs_root = fs_tree.getroot()

    assert len(fs_root.xpath(
        '/mets:mets/mets:fileSec/mets:fileGrp/mets:file/'
        'mets:FLocat[@xlink:href="file://tests/data/audio/valid__wav.wav"]',
        namespaces=NAMESPACES
    )) == 1

    assert len(sm_root.xpath('//mets:div[@TYPE="file" and @ORDER="5"]',
                             namespaces=NAMESPACES)) == 1


def test_get_fileid():
    """Test get_fileid function. Create a fileGrp element with few files and
    test that the function finds correct file IDs.
    """

    # Create fileGrp element that contains three file elements with different
    # identifiers and paths
    files = [mets.file_elem(file_id='identifier%s' % num,
                            admid_elements=['foo', 'bar'],
                            loctype='foo',
                            xlink_href='file://path/to/file+name%s' % num,
                            xlink_type='foo') for num in range(3)]

    filegrp = mets.filegrp(child_elements=files)

    assert compile_structmap.get_fileid(filegrp, 'path/to/file name1') \
        == 'identifier1'
