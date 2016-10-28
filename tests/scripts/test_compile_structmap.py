import pytest
from siptools.scripts import compile_structmap
import os
import lxml.etree as ET
from siptools.xml.namespaces import NAMESPACES
from urllib import quote_plus


def test_compile_structmap_ok():
    return_code = compile_structmap.main(['tests/data/TPAS-20', '--workspace',
                                          './workspace'])

    output_file = os.path.join('./workspace', 'structmap.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat[@xlink:href="file://tests/data/TPAS-20/Documentation files/readme.txt"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets/mets:structMap/mets:div/mets:div[@TYPE="Documentation files"]', namespaces=NAMESPACES)) == 1

    assert return_code == 0


def test_structmap_links():
    dmdsec_location = 'tests/data/import_description/metadata/dc_description.xml'
    dmdsec_url = quote_plus(dmdsec_location)
    dmdsec_file = os.path.join('./workspace', dmdsec_url)
    dmdsec_tree = ET.parse(dmdsec_file)
    dmdsec_root = dmdsec_tree.getroot()
    dmdsec_id = dmdsec_root.xpath('/mets:mets/mets:dmdSec/@ID',
            namespaces=NAMESPACES)[0]

    return_code = compile_structmap.main(['tests/data/TPAS-20', '--workspace',
        './workspace', '--dmdsec_id' , dmdsec_id])
    output_file = os.path.join('./workspace', 'structmap.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()
    assert root.xpath(
        '/mets:mets/mets:structMap/mets:div/@DMDID',
        namespaces=NAMESPACES)[0] == dmdsec_id


def test_compile_structmap_not_ok():
    with pytest.raises(SystemExit):
        return_code = compile_structmap.main(['tests/data/notfound', '--workspace',
                                              './workspace'])
