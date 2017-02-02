import pytest
from siptools.scripts import compile_structmap
from siptools.scripts import import_object
import os
import lxml.etree as ET
from siptools.xml.namespaces import NAMESPACES
from urllib import quote_plus


def create_test_data(workspace):
    # create technical metadata
    import_object.main(['--output', workspace,
                        'tests/data/structured/Software files/koodi.java'])


def test_compile_structmap_ok(testpath):
    create_test_data(testpath)
    return_code = compile_structmap.main(['tests/data/structured/Software files', '--workspace',
                                          testpath])

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = ET.parse(output_filesec)
    fs_root = fs_tree.getroot()

    assert len(fs_root.xpath(
        '/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat[@w3_xlink:href="file://tests/data/structured/Software files/koodi.java"]', namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '/mets:mets/mets:structMap/mets:div[@TYPE="Software files"]', namespaces=NAMESPACES)) == 1

    assert return_code == 0


def test_compile_structmap_not_ok(testpath):
    with pytest.raises(SystemExit):
        return_code = compile_structmap.main(['tests/data/notfound', '--workspace',
                                              testpath])
