import lxml.etree as ET
from siptools.scripts import compile_mets
import pytest
import os
from siptools.xml.mets import NAMESPACES
from siptools.scripts.import_description import main
from siptools.scripts import premis_event
from siptools.scripts import import_object
from siptools.scripts import compile_structmap
from urllib import quote


def create_test_data(workspace):
    # create descriptive metadata
    dmdsec_location = 'tests/data/import_description/metadata/dc_description.xml'
    dmdsec_target = 'tests/data/structured/Software files'

    main([dmdsec_location, '--dmdsec_target', dmdsec_target, '--workspace',
            workspace, '--desc_root', 'remove'])

    # create provenance metadata
    premis_event.main(['creation', '2016-10-13T12:30:55', '--event_target',
        'tests/data/structured', '--event_detail', 'Testing', '--event_outcome', 'success',
        '--event_outcome_detail', 'Outcome detail', '--workspace',
        workspace, '--agent_name', 'Demo Application', '--agent_type', 'software'])

    #create technical metadata
    import_object.main(['--workspace', workspace,
        'tests/data/structured/Software files/koodi.java'])

    #create structural metadata
    compile_structmap.main(['--workspace', workspace])


def test_compile_mets_ok(testpath):
    create_test_data(testpath)
    return_code = compile_mets.main(['ch',
                                     'CSC',
                                     'contract-id-1234',
                                     '--objid', 'ABC-123',
                                     '--label', 'Test SIP',
                                     '--contentid', 'Aineisto-123',
                                     '--create_date', '2016-10-28T09:30:55',
                                     '--last_moddate', '2016-10-28T09:30:55',
                                     '--record_status', 'submission',
                                     '--packagingservice', 'Pekka Paketoija',
                                     '--workspace', testpath])

    output_file = os.path.join(testpath, 'mets.xml')
    tree = ET.parse(output_file)

    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets[@PROFILE="http://digitalpreservation.fi/mets-profiles/cultural-heritage"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@OBJID="ABC-123"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@LABEL="Test SIP"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:CATALOG="1.7.0"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:SPECIFICATION="1.7.0"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:CONTRACTID="contract-id-1234"]', namespaces=NAMESPACES)) == 1
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
    assert root.xpath("/mets:mets/mets:metsHdr/mets:agent/mets:name",
                      namespaces=NAMESPACES)[2].text == 'Pekka Paketoija'

    assert return_code == 0


def test_compile_mets_cleanup_ok(testpath):
    create_test_data(testpath)
    return_code = compile_mets.main(['ch',
                                     'CSC',
                                     'contract-id-1234',
                                     '--objid', 'ABC-123',
                                     '--label', 'Test SIP',
                                     '--contentid', 'Aineisto-123',
                                     '--create_date', '2016-10-28T09:30:55',
                                     '--last_moddate', '2016-10-28T09:30:55',
                                     '--record_status', 'submission', '--workspace',
                                     testpath, '--clean'])

    output_file = os.path.join(testpath, 'mets.xml')
    tree = ET.parse(output_file)

    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets[@PROFILE="http://digitalpreservation.fi/mets-profiles/cultural-heritage"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@OBJID="ABC-123"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@LABEL="Test SIP"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:CATALOG="1.7.0"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:SPECIFICATION="1.7.0"]', namespaces=NAMESPACES)) == 1
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

def test_compile_mets_fail(testpath):

    with pytest.raises(SystemExit):
        return_code = compile_mets.main(['ch',
                                         'CSC',
                                         'contract-id-1234',
                                         '--objid', 'ABC-123',
                                         '--label', 'Test SIP',
                                         '--contentid', 'Aineisto-123',
                                         '--create_date', '2016-10-28T09:30:55',
                                         '--last_moddate', '2016-10-28T09:30:55',
                                         '--record_status', 'nonsense', '--workspace',
                                         testpath])
