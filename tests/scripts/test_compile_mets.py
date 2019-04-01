"""Tests for ``siptools.scripts.compile_mets`` module"""
import os
import lxml.etree as ET
import pytest
from click.testing import CliRunner
from siptools.xml.mets import NAMESPACES
from siptools.scripts.import_description import main
from siptools.scripts import compile_mets
from siptools.scripts import premis_event
from siptools.scripts import import_object
from siptools.scripts import compile_structmap


def create_test_data(workspace):
    # TODO: Missing docstring
    # create descriptive metadata
    runner = CliRunner()
    dmdsec_location \
        = 'tests/data/import_description/metadata/dc_description.xml'
    dmdsec_target = 'tests/data/structured/Software files'

    arguments = [dmdsec_location, '--dmdsec_target', dmdsec_target,
                 '--workspace', workspace, '--desc_root']
    result = runner.invoke(main, arguments)


    # create provenance metadata
    arguments = ['creation', '2016-10-13T12:30:55',
                 '--event_target', 'tests/data/structured',
                 '--event_detail', 'Testing',
                 '--event_outcome', 'success',
                 '--event_outcome_detail', 'Outcome detail',
                 '--workspace', workspace,
                 '--agent_name', 'Demo Application',
                 '--agent_type', 'software']
    result = runner.invoke(premis_event.main, arguments)

    #create technical metadata
    arguments = ['--workspace', workspace, '--skip_validation',
                 'tests/data/structured/Software files/koodi.java']
    result = runner.invoke(import_object.main, arguments)

    #create structural metadata
    result = runner.invoke(import_object.main, ['--workspace', workspace])

def test_compile_mets_ok(testpath):
    # TODO: Missing docstring
    create_test_data(testpath)
    arguments = ['ch',
                 'CSC',
                 'contract-id-1234',
                 '--objid', 'ABC-123',
                 '--label', 'Test SIP',
                 '--contentid', 'Aineisto-123',
                 '--create_date', '2016-10-28T09:30:55',
                 '--last_moddate', '2016-10-28T09:30:55',
                 '--record_status', 'submission',
                 '--packagingservice', 'Pekka Paketoija',
                 '--workspace', testpath]
    runner = CliRunner()
    result = runner.invoke(compile_mets.main, arguments)

    output_file = os.path.join(testpath, 'mets.xml')
    tree = ET.parse(output_file)

    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets[@PROFILE="http://digitalpreservation.fi'
        '/mets-profiles/cultural-heritage"]',
        namespaces=NAMESPACES
    )) == 1
    assert len(root.xpath(
        '/mets:mets[@OBJID="ABC-123"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@LABEL="Test SIP"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:CATALOG="1.7.1"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:SPECIFICATION="1.7.1"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets[@fi:CONTRACTID="contract-id-1234"]',
                          namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets[@fi:CONTENTID="Aineisto-123"]',
                          namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets/mets:metsHdr',
                          namespaces=NAMESPACES)) == 1
    assert len(
        root.xpath(
            '/mets:mets/mets:metsHdr[@CREATEDATE="2016-10-28T09:30:55"]',
            namespaces=NAMESPACES
        )
    ) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@LASTMODDATE="2016-10-28T09:30:55"]',
        namespaces=NAMESPACES
    )) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@RECORDSTATUS="submission"]',
        namespaces=NAMESPACES
    )) == 1
    assert root.xpath("/mets:mets/mets:metsHdr/mets:agent/mets:name",
                      namespaces=NAMESPACES)[0].text == 'CSC'
    assert root.xpath("/mets:mets/mets:metsHdr/mets:agent/mets:name",
                      namespaces=NAMESPACES)[1].text == 'Pekka Paketoija'

    assert result.exit_code == 0


def test_compile_mets_cleanup_ok(testpath):
    #TODO: Missing docstring
    create_test_data(testpath)
    arguments = ['ch',
                 'CSC',
                 'contract-id-1234',
                 '--objid', 'ABC-123',
                 '--label', 'Test SIP',
                 '--contentid', 'Aineisto-123',
                 '--create_date', '2016-10-28T09:30:55',
                 '--last_moddate', '2016-10-28T09:30:55',
                 '--record_status', 'submission',
                 '--workspace', testpath,
                 '--clean']
    runner = CliRunner()
    result = runner.invoke(compile_mets.main, arguments)

    output_file = os.path.join(testpath, 'mets.xml')
    tree = ET.parse(output_file)

    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets[@PROFILE="http://digitalpreservation.fi/'
        'mets-profiles/cultural-heritage"]',
        namespaces=NAMESPACES
    )) == 1
    assert len(root.xpath(
        '/mets:mets[@OBJID="ABC-123"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@LABEL="Test SIP"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:CATALOG="1.7.1"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:SPECIFICATION="1.7.1"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets[@fi:CONTENTID="Aineisto-123"]',
                          namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets/mets:metsHdr',
                          namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@CREATEDATE="2016-10-28T09:30:55"]',
        namespaces=NAMESPACES
    )) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@LASTMODDATE="2016-10-28T09:30:55"]',
        namespaces=NAMESPACES
    )) == 1
    assert len(root.xpath(
        '/mets:mets/mets:metsHdr[@RECORDSTATUS="submission"]',
        namespaces=NAMESPACES
    )) == 1
    assert root.xpath("/mets:mets/mets:metsHdr/mets:agent/mets:name",
                      namespaces=NAMESPACES)[0].text == 'CSC'

    assert result.exit_code == 0


def test_compile_mets_fail(testpath):
    #TODO: Missing docstring
    arguments = ['ch',
                 'CSC',
                 'contract-id-1234',
                 '--objid', 'ABC-123',
                 '--label', 'Test SIP',
                 '--contentid', 'Aineisto-123',
                 '--create_date', '2016-10-28T09:30:55',
                 '--last_moddate', '2016-10-28T09:30:55',
                 '--record_status', 'nonsense',
                 '--workspace', testpath]
    runner = CliRunner()
    result = runner.invoke(compile_mets.main, arguments)
    assert type(result.exception) == SystemExit
