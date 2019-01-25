"""Tests for the compile_structmap script."""

import os
import shutil
import pytest
import lxml.etree
import mets
from siptools.xml.mets import NAMESPACES
from siptools.scripts import compile_structmap
from siptools.scripts import import_object
from siptools.scripts import premis_event
from siptools.scripts import import_description


def create_test_data(workspace):
    """Create technical metadata test data."""
    import_object.main(['--workspace', workspace, '--skip_inspection',
                        'tests/data/structured/Software files/koodi.java'])
    premis_event.main(['creation', '2016-10-13T12:30:55',
                       '--event_detail', 'Testing', '--event_outcome',
                       'success', '--workspace', workspace, '--event_target',
                       'tests/data/structured/Software files'])


def test_compile_structmap_ok(testpath):
    """Test the compile_structmap script."""
    create_test_data(testpath)
    return_code = compile_structmap.main(['--workspace', testpath])

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

    assert return_code == 0


def test_compile_structmap_dmdsecid(testpath):
    """Test the compile_structmap script for workspace that contains
    descriptive metadata in dmdsec.xml file. The ID of dmdSec should be
    included in structMap.
    """
    # Create -premis-amd.xml and dmdsec.xml files in workspace
    import_object.main(['--workspace', testpath, '--skip_inspection',
                        'tests/data/structured/Software files/koodi.java'])
    dmdsec = import_description.create_mets(
        'tests/data/import_description/metadata/dc_description.xml',
        'dmdsec.xml'
    )
    dmdsec.write(os.path.join(testpath, 'dmdsec.xml'))

    # Create structmap
    compile_structmap.main(['--workspace', testpath])

    # The root div of structMap should have reference to dmdSec element in
    # dmdsec.xml
    dmdsecid = dmdsec.xpath('/mets:mets/mets:dmdSec',
                            namespaces=NAMESPACES)[0].attrib['ID']
    structmap = lxml.etree.parse(os.path.join(testpath, 'structmap.xml'))
    assert len(
        structmap.xpath(
            '/mets:mets/mets:structMap/mets:div[@DMDID="%s"]' % dmdsecid,
            namespaces=NAMESPACES
        )
    ) == 1


def test_compile_structmap_not_ok(testpath):
    """Test that error is raised for non-existent folders."""
    with pytest.raises(SystemExit):
        compile_structmap.main(['tests/data/notfound', '--workspace',
                                testpath])


def test_file_and_dir(testpath):
    """Test the cmpile_structmap with a file and directory case."""
    import_object.main(['--workspace', testpath, '--skip_inspection',
                        'tests/data/file_and_dir'])
    return_code = compile_structmap.main(['--workspace', testpath])
    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = lxml.etree.parse(output_structmap)
    sm_root = sm_tree.getroot()
    elementlist = sm_root.xpath(
        '/mets:mets/mets:structMap/mets:div/mets:div/mets:div/mets:div/*',
        namespaces=NAMESPACES)
    assert elementlist[0].tag == '{%s}fptr' % NAMESPACES['mets']
    assert elementlist[1].tag == '{%s}div' % NAMESPACES['mets']
    assert return_code == 0


def test_get_amd_references(testpath):
    """Test get_amd_references function. Copies sample MD reference file
    to workspace and reads the administrative MD IDs for a file.
    """
    shutil.copy('tests/data/sample_amd-references.xml',
                os.path.join(testpath, 'amd-references.xml'))

    # The sample file contains two references for file2
    ids = compile_structmap.get_amd_references(testpath, 'path/to/file2')
    assert set(ids) == set(['abcd1234', 'efgh5678'])


def test_othermd_references(testpath):
    """Test that main function creates references to othermd-metadata from file
    element in fileSec. A sample workspace contains aMD files, MIX metadata
    files, and aMD reference file for three image files. Two of the images
    are similar and therefore have same MIX metadata.
    """

    # Copy workspace to temporary directory
    workspace = os.path.join(testpath, 'workspace')
    shutil.copytree('tests/data/compile_structmap_workspace', workspace)

    # Compile structmap
    compile_structmap.main(['--workspace', workspace])

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
def test_compile_structmap_directory(testpath):
    """Test the compile_structmap script. Assert that directory
    structure is transferred to the structmap and that the premis
    event ID created in the test data is linked to the correct div
    element.
    """
    create_test_data(testpath)
    return_code = compile_structmap.main(
        ['--workspace', testpath, '--type_attr', 'Directory-physical']
    )

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = lxml.etree.parse(output_structmap)
    sm_root = sm_tree.getroot()

    assert len(sm_root.xpath('//mets:div[@TYPE="directory" and '
                             '@LABEL="Software files"]',
                             namespaces=NAMESPACES)) == 1

    assert sm_root.xpath(
        '//mets:div[@TYPE="directory" and @LABEL="Software files"]',
        namespaces=NAMESPACES)[0].get(
            'ADMID') == '_47244c09fb49dfd4d0577d29820bfa6c'

    assert return_code == 0


def test_compile_structmap_order(testpath):
    """Test the compile_structmap script."""
    import_object.main(['--workspace', testpath,
                        '--skip_inspection',
                        '--order', '5',
                        'tests/data/structured/Software files/koodi.java'])

    compile_structmap.main(['--workspace', testpath])

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
                            xlink_href=u'file://path/to/file+name%s' % num,
                            xlink_type='foo') for num in range(3)]

    filegrp = mets.filegrp(child_elements=files)

    assert compile_structmap.get_fileid(filegrp, 'path/to/file name1') \
        == 'identifier1'
