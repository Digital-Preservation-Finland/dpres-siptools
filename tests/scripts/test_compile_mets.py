"""Tests for ``siptools.scripts.compile_mets`` module"""
from __future__ import unicode_literals

import os

import lxml.etree as ET
from siptools.scripts import (compile_mets, compile_structmap, import_object,
                              premis_event)
from siptools.scripts.import_description import main
from siptools.xml.mets import NAMESPACES


def create_test_data(workspace, run_cli):
    """
    Create test data for the tests.

    :workspace: Workspace path
    """
    # create descriptive metadata
    dmdsec_location \
        = 'tests/data/import_description/metadata/dc_description.xml'
    dmdsec_target = 'tests/data/structured/Software files'

    arguments = [dmdsec_location, '--dmdsec_target', dmdsec_target,
                 '--workspace', workspace, '--remove_root']
    run_cli(main, arguments)

    # create provenance metadata
    arguments = ['creation', '2016-10-13T12:30:55',
                 '--event_target', 'tests/data/structured',
                 '--event_detail', 'Testing',
                 '--event_outcome', 'success',
                 '--event_outcome_detail', 'Outcome detail',
                 '--workspace', workspace,
                 '--agent_name', 'Demo Application',
                 '--agent_type', 'software']
    run_cli(premis_event.main, arguments)

    # create technical metadata
    arguments = ['--workspace', workspace, '--skip_wellformed_check',
                 'tests/data/structured/Software files/koodi.java']
    run_cli(import_object.main, arguments)

    # create structural metadata
    run_cli(compile_structmap.main, ['--workspace', workspace])


def test_compile_mets_ok(testpath, run_cli):
    """
    Test that METS compilation works, no cleanup.
    """
    create_test_data(testpath, run_cli)
    arguments = ['ch',
                 'CSC',
                 'urn:uuid:89e92a4f-f0e4-4768-b785-4781d3299b20',
                 '--objid', 'ABC-123',
                 '--label', 'Test SIP',
                 '--contentid', 'Aineisto-123',
                 '--create_date', '2016-10-28T09:30:55',
                 '--last_moddate', '2016-10-28T09:30:55',
                 '--record_status', 'submission',
                 '--packagingservice', 'Pekka Paketoija',
                 '--workspace', testpath]
    run_cli(compile_mets.main, arguments)

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
        '/mets:mets[@fi:CATALOG="1.7.3"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:SPECIFICATION="1.7.3"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath('/mets:mets[@fi:CONTRACTID="urn:uuid:89e92a4f-f0e4'
                          '-4768-b785-4781d3299b20"]',
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


def test_compile_mets_cleanup_ok(testpath, run_cli):
    """
    Test that METS compilation with cleanup works ok.
    """
    create_test_data(testpath, run_cli)
    arguments = ['ch',
                 'CSC',
                 'urn:uuid:89e92a4f-f0e4-4768-b785-4781d3299b20',
                 '--objid', 'ABC-123',
                 '--label', 'Test SIP',
                 '--contentid', 'Aineisto-123',
                 '--create_date', '2016-10-28T09:30:55',
                 '--last_moddate', '2016-10-28T09:30:55',
                 '--record_status', 'submission',
                 '--workspace', testpath,
                 '--clean']
    run_cli(compile_mets.main, arguments)

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
        '/mets:mets[@fi:CATALOG="1.7.3"]', namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '/mets:mets[@fi:SPECIFICATION="1.7.3"]', namespaces=NAMESPACES)) == 1
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


def test_compile_mets_fail(testpath, run_cli):
    """
    Test that METS compilation terminates on failure.
    """
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
    result = run_cli(compile_mets.main, arguments, success=False)
    assert isinstance(result.exception, SystemExit)
