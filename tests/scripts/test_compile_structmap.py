import pytest
from siptools.scripts import compile_structmap
import os
import lxml.etree as ET
from siptools.xml.namespaces import NAMESPACES
from urllib import quote_plus


def test_compile_structmap_ok():
    return_code = compile_structmap.main(['tests/data/structured', '--workspace',
                                          './workspace'])

    output_structmap = os.path.join('./workspace', 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join('./workspace', 'filesec.xml')
    fs_tree = ET.parse(output_filesec)
    fs_root = fs_tree.getroot()

    assert len(fs_root.xpath(
        '/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat[@xlink:href="file://tests/data/structured/Documentation files/readme.txt"]', namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '/mets:mets/mets:structMap/mets:div/mets:div[@TYPE="Documentation files"]', namespaces=NAMESPACES)) == 1

    assert return_code == 0


def test_compile_structmap_not_ok():
    with pytest.raises(SystemExit):
        return_code = compile_structmap.main(['tests/data/notfound', '--workspace',
                                              './workspace'])
