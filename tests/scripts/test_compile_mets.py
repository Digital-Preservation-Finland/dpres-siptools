import lxml.etree as ET
from siptools.scripts import compile_mets
import pytest
import os
from siptools.xml.namespaces import NAMESPACES


def test_compile_mets_ok():

    return_code = compile_mets.main(['http://www.kdk.fi/kdk-mets-profile',
                                     'CSC', '--objid', 'ABC-123',
                                     '--label', 'Test SIP',
                                     '--catalog', '1.5.0',
                                     '--specification', '1.5.0',
                                     '--contentid', 'Aineisto-123',
                                     '--create_date', '2016-10-28T09:30:55',
                                     '--last_moddate', '2016-10-28T09:30:55',
                                     '--record_status', 'submission', '--workspace',
                                     './workspace'])

    output_file = os.path.join('./workspace', 'mets.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()
    # print "root: %s" % ET.tostring(root, encoding='UTF-8', method='xml')

    assert len(root.xpath(
        '/mets:mets[@PROFILE="http://www.kdk.fi/kdk-mets-profile"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@OBJID="ABC-123"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@LABEL="Test SIP"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:CATALOG="1.5.0"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:SPECIFICATION="1.5.0"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:CONTENTID="Aineisto-123"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets/mets:metsHdr',
                          namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@CREATEDATE="2016-10-28T09:30:55"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@LASTMODDATE="2016-10-28T09:30:55"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@RECORDSTATUS="submission"]', namespaces=NAMESPACES)) == 1
    assert root.xpath("/mets:mets/mets:metsHdr/mets:agent/mets:name",
                      namespaces=NAMESPACES)[0].text == 'CSC'

    assert return_code == 0


def test_compile_mets_fail():

    with pytest.raises(SystemExit):
        return_code = compile_mets.main(['http://www.kdk.fi/kdk-mets-profile',
                                         'CSC', '--objid', 'ABC-123',
                                         '--label', 'Test SIP',
                                         '--catalog', '1.5.0',
                                         '--specification', '1.5.0',
                                         '--contentid', 'Aineisto-123',
                                         '--create_date', '2016-10-28T09:30:55',
                                         '--last_moddate', '2016-10-28T09:30:55',
                                         '--record_status', 'nonsense', '--workspace',
                                         './workspace'])
