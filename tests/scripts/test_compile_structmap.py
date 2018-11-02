"""Tests for the compile_structmap script."""

import os
import shutil
import pytest
import lxml.etree
from siptools.xml.mets import NAMESPACES
from siptools.scripts import compile_structmap
from siptools.scripts import import_object


def create_test_data(workspace):
    """Create technical metadata test data."""
    import_object.main(['--workspace', workspace, '--skip_inspection',
                        'tests/data/structured/Software files/koodi.java'])


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
        'Software+files/koodi.java"]', namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div[@TYPE="Software files"]', namespaces=NAMESPACES)) == 1

    assert return_code == 0


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


def test_get_techmd_references(testpath):
    """Test get_techmd_references function. Copies sample techMD reference file
    to workspace and reads the techMD IDs for a file.
    """
    shutil.copy('tests/data/sample_techmd-references.xml',
                os.path.join(testpath, 'techmd-references.xml'))

    # The sample file contains two references for file2
    ids = compile_structmap.get_techmd_references(testpath, 'path/to/file2')
    assert set(ids) == set(['abcd1234', 'efgh5678'])


def test_othermd_references(testpath):
    """Test that main function creates references to othermd-metadata from file
    element in fileSec. A sample workspace contains techMD files, MIX metadata
    files, and techMD reference file for three image files. Two of the images
    are similar and therefore have same MIX metadata.
    """

    # Copy workspace to temporary directory
    workspace = os.path.join(testpath, 'workspace')
    shutil.copytree('tests/data/compile_structmap_workspace', workspace)

    # Compile structmap
    compile_structmap.main(['--workspace', workspace])

    # Read filesec.xml
    mets = lxml.etree.parse(os.path.join(workspace, 'filesec.xml'))
    namespaces = {'mets': "http://www.loc.gov/METS/",
                  'xlink': "http://www.w3.org/1999/xlink"}

    # fileGrp section should contain 3 file elements
    files = mets.xpath('/mets:mets/mets:fileSec/mets:fileGrp/mets:file',
                       namespaces=namespaces)
    assert len(files) == 3

    # This dictonary maps filepath to MIX techMD IDs excpected to be referenced
    # in fileSec
    techmd_ids = {"sample_images/sample_tiff1_compressed.tif":
                  "_c08061e439bd40407c9e5332fec6084e",
                  "sample_images/sample_tiff1.tif":
                  "_e50655691d21e110a3c4b38da52fb91c",
                  "sample_images/sample_tiff2.tif":
                  "_e50655691d21e110a3c4b38da52fb91c"}

    for filepath in techmd_ids:
        # Find file element from mets based on filepath
        xpath = '//mets:FLocat[@xlink:href="file://%s"]/parent::mets:file' \
            % filepath
        file_element = mets.xpath(xpath, namespaces=namespaces)

        # The file element should have reference to techMD element defined in
        # ``techmd_ids`` dictionary
        assert techmd_ids[filepath] in file_element[0].get('ADMID')


def test_compile_structmap_directory_label(testpath):
    """Test the compile_structmap script."""
    create_test_data(testpath)
    return_code = compile_structmap.main(
        ['--workspace', testpath, '--type_attr', 'Directory-physical'])

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = lxml.etree.parse(output_structmap)
    sm_root = sm_tree.getroot()

    assert len(sm_root.xpath(
        '//mets:div[@TYPE="directory" and @LABEL="Software files"]',
        namespaces=NAMESPACES)) == 1

    assert return_code == 0


def test_compile_structmap_order(testpath):
    """Test the compile_structmap script."""
    import_object.main(['--workspace', testpath, '--skip_inspection',
                        '--order', '5',
                        'tests/data/structured/Software files/koodi.java'])
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
        'Software+files/koodi.java"]', namespaces=NAMESPACES)) == 1

    assert len(sm_root.xpath(
        '//mets:div[@TYPE="file" and @ORDER="5"]',
        namespaces=NAMESPACES)) == 1
