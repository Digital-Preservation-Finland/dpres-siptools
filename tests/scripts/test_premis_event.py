"""Tests for :mod:`siptools.scripts.premis_event` module"""
import os
import xml.etree.ElementTree as ET
from siptools.scripts import premis_event
import pytest


def test_premis_event_ok(testpath):
    """Test that main function produces event.xml and agent.xml files with
    correct elements.
    """

    return_code = premis_event.main(
        [
            'creation',
            '2016-10-13T12:30:55',
            '--event_target', 'tests/data/structured',
            '--event_detail', 'Testing',
            '--event_outcome', 'success',
            '--event_outcome_detail', 'Outcome detail',
            '--workspace', testpath,
            '--agent_name', 'Demo Application',
            '--agent_type', 'software'
        ]
    )

    # Main function should return 0
    assert return_code == 0

    # Read output files
    event_xml = ET.parse(
        os.path.join(testpath, 'tests%2Fdata%2Fstructured-creation-event.xml')
    ).getroot()
    agent_xml = ET.parse(
        os.path.join(testpath, 'tests%2Fdata%2Fstructured-creation-agent.xml')
    ).getroot()

    namespaces = {'mets': 'http://www.loc.gov/METS/',
                  'premis': 'info:lc/xmlns/premis-v2'}

    # Both output files should have one amdSec element
    assert len(event_xml.findall('mets:amdSec', namespaces=namespaces)) == 1
    assert len(agent_xml.findall('mets:amdSec', namespaces=namespaces)) == 1

    # Check thait event.xml contains required elements with correct content
    for element, content in (
            (".//premis:eventType", 'creation'),
            (".//premis:eventDateTime", '2016-10-13T12:30:55'),
            (".//premis:eventDetail", 'Testing'),
            (".//premis:eventOutcome", 'success'),
            (".//premis:eventOutcomeDetailNote", 'Outcome detail')
    ):
        assert event_xml.findall(element, namespaces=namespaces)[0].text \
            == content

    # Check thait agent.xml contains required elements with correct content
    for element, content in (
            (".//premis:agentName", 'Demo Application'),
            (".//premis:agentType", 'software')
    ):
        assert agent_xml.findall(element, namespaces=namespaces)[0].text \
            == content

    # event.xml file should contain link to agent-element in agent.xml file
    assert \
        event_xml.findall('.//premis:linkingAgentIdentifierValue',
                          namespaces=namespaces)[0].text \
        == \
        agent_xml.findall('.//premis:agentIdentifierValue',
                          namespaces=namespaces)[0].text


def test_premis_event_fail(testpath):
    """Test that main function raises `SystemExit` if `event_outcome`
    parameter is incorrect."""

    with pytest.raises(SystemExit):
        premis_event.main(
            [
                'creation', '2016-10-13T12:30:55',
                '--event_detail', 'Testing',
                '--event_outcome', 'nonsense',
                '--event_outcome_detail', 'Outcome detail',
                '--workspace', testpath
            ]
        )
