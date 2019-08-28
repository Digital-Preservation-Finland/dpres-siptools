"""Tests the compile_structmap module with ead3 metadata."""

import os
from click.testing import CliRunner
import lxml.etree as ET
from siptools.scripts import compile_structmap
from siptools.scripts import import_object
from siptools.xml.mets import NAMESPACES


def create_test_data(workspace):
    """Create technical metadata test data."""
    runner = CliRunner()
    runner.invoke(import_object.main, [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Software files/koodi.java'])
    runner = CliRunner()
    runner.invoke(import_object.main, [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Publication files/publication.txt'])


def test_compile_structmap_ok(testpath):
    """Tests the successful compilation of mets:structmap
    by using ead3 metadata as basis. Test that a leading slash
    in the ead3 metadata is removed since only relative paths
    are allowed.
    """
    create_test_data(testpath)
    arguments = [
        '--structmap_type', 'EAD3-logical', '--dmdsec_loc',
        'tests/data/import_description/metadata/ead3_test.xml', '--workspace',
        testpath]
    runner = CliRunner()
    result = runner.invoke(compile_structmap.main, arguments)

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = ET.parse(output_filesec)
    fs_root = fs_tree.getroot()

    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/*'),
        namespaces=NAMESPACES)) == 2
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Software+'
         'files/koodi.java"]'), namespaces=NAMESPACES)) == 1
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Publication+'
         'files/publication.txt"]'), namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div[@LABEL="fonds"]', namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div[@LABEL="subseries"]',
        namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div/mets:div[@LABEL="item"]',
        namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div/mets:div/mets:div[@LABEL="file"]',
        namespaces=NAMESPACES)) == 2
    assert sm_root.xpath(
        '//mets:div[@LABEL="file"]/*',
        namespaces=NAMESPACES)[0].tag == '{http://www.loc.gov/METS/}fptr'
    assert 'FILEID' in sm_root.xpath(
        '//mets:div[@LABEL="file"]/*', namespaces=NAMESPACES)[0].attrib

    assert result.exit_code == 0


def test_daoset_ok(testpath):
    """Tests the successful compilation of mets:structmap with
    an ead3:daoset element containing multiple ead3:dao elements
    by using ead3 metadata as basis and that both mets:fptr elements
    are within the same mets:div element.
    """
    create_test_data(testpath)
    arguments = [
        '--structmap_type', 'EAD3-logical', '--dmdsec_loc',
        'tests/data/import_description/metadata/ead3_daoset_test.xml',
        '--workspace',
        testpath]
    runner = CliRunner()
    result = runner.invoke(compile_structmap.main, arguments)

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = ET.parse(output_filesec)
    fs_root = fs_tree.getroot()

    print ET.tostring(sm_root)

    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/*'),
        namespaces=NAMESPACES)) == 2
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Software+'
         'files/koodi.java"]'), namespaces=NAMESPACES)) == 1
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Publication+'
         'files/publication.txt"]'), namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div/mets:div/mets:div[@LABEL="file"]',
        namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div/mets:div/mets:div[@LABEL="file"]/*',
        namespaces=NAMESPACES)) == 2

    assert result.exit_code == 0
