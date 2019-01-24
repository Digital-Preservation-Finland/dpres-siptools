"""Tests for :mod:`siptools.scripts.premis_event` module"""
import os
import sys
import lxml.etree as ET
import pytest
from siptools.scripts import premis_event


def get_techmd_file(path, input_file):
    """Get id"""
    ref = os.path.join(path, 'amd-references.xml')
    root = ET.parse(ref).getroot()
    amdref = root.xpath("/amdreferences/amdreference[not(@stream) "
                        "and @file='%s']" % input_file.decode(
                            sys.getfilesystemencoding()))[0]
    output = os.path.join(path, amdref.text[1:] +
                          "-PREMIS%3AEVENT-amd.xml")
    return output


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
        os.path.join(
            testpath,
            '4a4a5d87842b048eef1c59ab3fef286d-PREMIS%3AEVENT-amd.xml')
    ).getroot()
    agent_xml = ET.parse(
        os.path.join(
            testpath,
            'd4e928570d571cb1ba79e3b7ba23cd89-PREMIS%3AAGENT-amd.xml')
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


def test_amd_links_root(testpath):
    """Tests that premis_event script writes reference links correctly
    to the amd-references file.
    """
    return_code = premis_event.main(
        [
            'creation',
            '2016-10-13T12:30:55',
            '--event_detail', 'Testing',
            '--event_outcome', 'success',
            '--workspace', testpath
        ]
    )

    # Main function should return 0
    assert return_code == 0

    ref = os.path.join(testpath, 'amd-references.xml')
    assert os.path.isfile(ref)

    root = ET.parse(ref).getroot()
    dir_ref = root.xpath("/amdReferences/amdReference")[0].get('directory')
    assert dir_ref == '.'


def test_amd_links_file(testpath):
    """Tests that premis_event script writes reference links correctly
    to the amd-references file with a proper file target.
    """
    target = 'tests/data/test_import.pdf'
    return_code = premis_event.main(
        [
            'creation',
            '2016-10-13T12:30:55',
            '--event_detail', 'Testing',
            '--event_outcome', 'success',
            '--workspace', testpath,
            '--event_target', target
        ]
    )

    # Main function should return 0
    assert return_code == 0

    ref = os.path.join(testpath, 'amd-references.xml')
    assert os.path.isfile(ref)

    root = ET.parse(ref).getroot()
    dir_ref = root.xpath("/amdReferences/amdReference")[0].get('file')
    assert dir_ref == target


def test_amd_links_dir(testpath):
    """Tests that premis_event script writes reference links correctly
    to the amd-references file with a directory target.
    """
    target = 'tests/data'
    return_code = premis_event.main(
        [
            'creation',
            '2016-10-13T12:30:55',
            '--event_detail', 'Testing',
            '--event_outcome', 'success',
            '--workspace', testpath,
            '--event_target', target
        ]
    )

    # Main function should return 0
    assert return_code == 0

    ref = os.path.join(testpath, 'amd-references.xml')
    assert os.path.isfile(ref)

    root = ET.parse(ref).getroot()
    dir_ref = root.xpath("/amdReferences/amdReference")[0].get('directory')
    assert dir_ref == target


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
