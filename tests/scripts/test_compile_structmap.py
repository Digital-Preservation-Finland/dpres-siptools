import pytest
from siptools.scripts import compile_structmap
import os
import lxml.etree as ET
from siptools.xml.namespaces import NAMESPACES


def test_compile_structmap_ok():
    return_code = compile_structmap.main(['tests/data/TPAS-20', '--workspace',
                                          './workspace'])

    output_file = os.path.join('./workspace', 'mets.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat[@xlink:href="file://tests/data/TPAS-20/Documentation files/readme.txt"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets/mets:structMap/mets:div/mets:div[@TYPE="Documentation files"]', namespaces=NAMESPACES)) == 1

    assert return_code == 0


def test_compile_structmap_not_ok():
    with pytest.raises(SystemExit):
        return_code = compile_structmap.main(['tests/data/notfound', '--workspace',
            './workspace'])
