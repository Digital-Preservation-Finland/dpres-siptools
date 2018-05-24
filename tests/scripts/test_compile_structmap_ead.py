"""Tests the compile_structmap module with ead3 metadata."""

import os
import lxml.etree as ET
from siptools.scripts import compile_structmap
from siptools.scripts import import_object
from siptools.xml.mets import NAMESPACES


def create_test_data(workspace):
    """Create technical metadata test data."""
    import_object.main(['--workspace', workspace,
                        'tests/data/structured/Software files/koodi.java'])
    import_object.main(
        ['--workspace', workspace,
         'tests/data/structured/Publication files/publication.txt'])


def test_compile_structmap_ok(testpath):
    """Tests the successful compilation of mets:structmap
    by using ead3 metadata as basis. Test that a leading slash
    in the ead3 metadata is removed since only relative paths
    are allowed.
    """
    create_test_data(testpath)
    return_code = compile_structmap.main(
        ['--dmdsec_struct', 'ead3', '--dmdsec_loc',
         'tests/data/import_description/metadata/ead3_test.xml', '--workspace',
         testpath])

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
         '[@xlink:href="file://tests/data/structured/Software '
         'files/koodi.java"]'), namespaces=NAMESPACES)) == 1
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Publication '
         'files/publication.txt"]'), namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div[@LABEL="fonds"]', namespaces=NAMESPACES)) == 1

    assert return_code == 0
