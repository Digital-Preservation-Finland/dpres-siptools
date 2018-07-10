"""Tests for the compile_structmap script."""

import os
import shutil
import pytest
import lxml.etree as ET
from siptools.xml.mets import NAMESPACES
from siptools.scripts import compile_structmap
from siptools.scripts import import_object


def create_test_data(workspace):
    """Create technical metadata test data."""
    import_object.main(['--workspace', workspace,
                        'tests/data/structured/Software files/koodi.java'])


def test_compile_structmap_ok(testpath):
    """Test the compile_structmap script."""
    create_test_data(testpath)
    return_code = compile_structmap.main(['--workspace', testpath])

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = ET.parse(output_filesec)
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
    import_object.main(['--workspace', testpath,
                        'tests/data/file_and_dir'])
    return_code = compile_structmap.main(['--workspace', testpath])
    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
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
