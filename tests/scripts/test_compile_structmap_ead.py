"""Tests the compile_structmap module with ead3 metadata."""
from __future__ import unicode_literals

import os

import lxml.etree as ET
from siptools.scripts import compile_structmap, import_object
from siptools.xml.mets import NAMESPACES


def create_test_data(workspace, run_cli):
    """Create technical metadata test data."""
    run_cli(import_object.main, [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Software files/koodi.java'])
    run_cli(import_object.main, [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Publication files/publication.txt'])


def test_compile_structmap_ok(testpath, run_cli):
    """Tests the successful compilation of mets:structmap
    by using ead3 metadata as basis. Test that a leading slash
    in the ead3 metadata is removed since only relative paths
    are allowed.
    """
    create_test_data(testpath, run_cli)
    arguments = [
        '--structmap_type', 'EAD3-logical', '--dmdsec_loc',
        'tests/data/import_description/metadata/ead3_test.xml', '--workspace',
        testpath]
    run_cli(compile_structmap.main, arguments)

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
