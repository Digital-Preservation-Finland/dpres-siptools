"""Tests for :mod:`siptools.scripts.premis_event` module"""
from __future__ import unicode_literals

import os
import json

import lxml.etree as ET

import pytest

from siptools.scripts.create_agent import create_agent
from siptools.scripts import premis_event
from siptools.utils import fsdecode_path, read_md_references
from siptools.xml.mets import NAMESPACES


def get_md_file(path,
                input_target='.',
                ref_file='premis-event-md-references.jsonl',
                output_suffix='-PREMIS%3AEVENT-amd.xml'):
    """Get id"""
    with open(os.path.join(path, ref_file)) as in_file:
        refs = json.load(in_file)
    reference = refs[fsdecode_path(input_target)]
    for amdref in reference['md_ids']:
        output = os.path.join(path, amdref[1:] + output_suffix)
        if os.path.exists(output):
            return output
    return None


def test_premis_event_ok(testpath, run_cli):
    """Test that main function produces event.xml and agent.xml files with
    correct elements.
    """
    run_cli(premis_event.main, [
        'creation',
        '2016-10-13T12:30:55',
        '--event_target', 'tests/data/structured',
        '--event_detail', 'Testing',
        '--event_outcome', 'success',
        '--event_outcome_detail', 'Outcome detail',
        '--workspace', testpath,
        '--agent_name', 'Demo Application',
        '--agent_type', 'software'
    ])

    # Read output files
    event_xml = ET.parse(
        os.path.join(
            testpath,
            'ab5a33c51b05845a1a050361652752de-PREMIS%3AEVENT-amd.xml')
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


def test_amd_links_root(testpath, run_cli):
    """Tests that premis_event script writes reference links correctly
    to the md-references file.
    """
    run_cli(premis_event.main, [
        'creation',
        '2016-10-13T12:30:55',
        '--event_detail', 'Testing',
        '--event_outcome', 'success',
        '--event_outcome_detail', 'Test ok',
        '--workspace', testpath
    ])
    refs_file = os.path.join(testpath, 'premis-event-md-references.jsonl')
    assert os.path.isfile(refs_file)
    refs = read_md_references(testpath, 'premis-event-md-references.jsonl')
    assert '.' in refs
    assert refs['.']['path_type'] == 'directory'


def test_amd_links_file(testpath, run_cli):
    """Tests that premis_event script writes reference links correctly
    to the md-references file with a proper file target.
    """
    target = 'tests/data/test_import.pdf'
    run_cli(premis_event.main, [
        'creation',
        '2016-10-13T12:30:55',
        '--event_detail', 'Testing',
        '--event_outcome', 'success',
        '--event_outcome_detail', 'Test ok',
        '--workspace', testpath,
        '--event_target', target
    ])

    refs_file = os.path.join(testpath, 'premis-event-md-references.jsonl')
    assert os.path.isfile(refs_file)
    refs = read_md_references(testpath, 'premis-event-md-references.jsonl')
    assert target in refs


def test_amd_links_dir(testpath, run_cli):
    """Tests that premis_event script writes reference links correctly
    to the md-references file with a directory target.
    """
    target = 'tests/data'
    run_cli(premis_event.main, [
        'creation',
        '2016-10-13T12:30:55',
        '--event_detail', 'Testing',
        '--event_outcome', 'success',
        '--event_outcome_detail', 'Test ok',
        '--workspace', testpath,
        '--event_target', target
    ])

    refs_file = os.path.join(testpath, 'premis-event-md-references.jsonl')
    assert os.path.isfile(refs_file)
    refs = read_md_references(testpath, 'premis-event-md-references.jsonl')
    assert target in refs


def test_premis_event_fail(testpath, run_cli):
    """Test that main function raises `SystemExit` if `event_outcome`
    parameter is incorrect."""

    result = run_cli(premis_event.main, [
        'creation', '2016-10-13T12:30:55',
        '--event_detail', 'Testing',
        '--event_outcome', 'nonsense',
        '--event_outcome_detail', 'Outcome detail',
        '--workspace', testpath
    ], success=False)
    assert isinstance(result.exception, SystemExit)


@pytest.mark.parametrize(
    ('base_path', 'event_target', 'directory', 'event_file'),
    # No base_path, target is directory
    [('.', 'tests/data/structured', 'tests/data/structured', None),
     # No base_path or event_target, target is package root
     ('.', None, '.', None),
     # No event_target, target is still package root
     ('tests/data', None, '.', None),
     # Target is a directory
     ('tests/data/', 'structured', 'structured', None),
     # Target is a file
     ('tests/data/',
      'structured/Access and use rights files/access_file.txt', None,
      'structured/Access and use rights files/access_file.txt')]
)
def test_event_target_path(base_path, event_target, directory, event_file):
    """Tests the event_target_path function."""
    (ev_directory, ev_file) = premis_event.event_target_path(
        base_path, event_target)

    assert ev_directory == directory
    assert ev_file == event_file


def test_invalid_event_target_path():
    """Tests that event_target_path raises IOError if given
    event_target path doesn't exist.
    """
    with pytest.raises(IOError):
        premis_event.event_target_path('.', 'foo/bar')


def test_reuse_agent(testpath, run_cli):
    """Test that identical agent will be reused in events if found
    """
    # Create two events
    for i in range(1, 3):
        run_cli(premis_event.main, [
            'creation',
            '2016-10-13T12:30:55',
            '--event_target', 'tests/data/structured',
            '--event_detail', 'Testing: act %s' % i,
            '--event_outcome', 'success',
            '--event_outcome_detail', 'Outcome detail',
            '--workspace', testpath,
            '--agent_name', 'Demo Application',
            '--agent_type', 'software'
        ])

    event_files = [
        "df6c33ef84d498880516439770f9e641-PREMIS%3AEVENT-amd.xml",
        "dc76068c4e317b0b25eb239d08db2437-PREMIS%3AEVENT-amd.xml"
    ]
    events = [
        ET.parse(os.path.join(testpath, path)).getroot()
        for path in event_files
    ]
    event_details = [
        event.find(".//premis:eventDetail", namespaces=NAMESPACES).text
        for event in events
    ]
    agent_identifiers = [
        event.find(
            ".//premis:linkingAgentIdentifierValue",
            namespaces=NAMESPACES
        ).text
        for event in events
    ]

    # Events are different but link to same agent using an identical UUID
    assert event_details == ["Testing: act 1", "Testing: act 2"]

    assert len(agent_identifiers[0]) == 36
    assert agent_identifiers[0] == agent_identifiers[1]


@pytest.mark.parametrize(
    ("agent_identifier_type", "agent_identifier_value",
     "create_agent_file", "agents_count"), [
        (None, "", "", 1),
        ("acme", "foo", "", 1),
        ("acme", "foo", "testing", 1),
        ("acme", "foo", "testing", 2),
    ])
def test_import_agents(
        testpath,
        run_cli,
        agent_identifier_type,
        agent_identifier_value,
        create_agent_file,
        agents_count):
    """Tests that the correct number of  agents are created and linked
    as intended.

    Tests with following cases:
    1) agent_name and agent_type given
    2) agent_identifier given in addition to name and type
    3) create_agent_file is given, that should override the other agent
       information given
    4) Multiple agents given through the create_agent_file
    """
    agent_name = 'testing agent'
    agent_type = 'person'

    agent_identifier_values = []

    # Create agent testdata
    agent_id = create_agent(
        workspace=testpath,
        agent_type=agent_type,
        create_agent_file=create_agent_file,
        agent_name=agent_name,
        agent_role='testing')

    if create_agent_file:
        agent_identifier_type = 'local'
        agent_identifier_values.append(agent_id)
    elif agent_identifier_value:
        agent_identifier_values.append(agent_identifier_value)

    if agents_count > 1:
        second_agent_id = create_agent(
            workspace=testpath,
            agent_type=agent_type,
            create_agent_file=create_agent_file,
            agent_name='second agent')
        agent_identifier_values.append(second_agent_id)

    cli_args = [
        "creation",
        "2020-02-02T20:20:20",
        "--workspace", testpath,
        "--event_detail", "foo",
        "--event_outcome", "success",
        "--event_outcome_detail", "Test ok",
        "--agent_name", agent_name,
        "--agent_type", agent_type,
        "--create_agent_file", create_agent_file,
    ]
    if agent_identifier_value:
        cli_args.append("--agent_identifier")
        cli_args.append(agent_identifier_type)
        cli_args.append(agent_identifier_value)

    run_cli(premis_event.main, cli_args)

    # Set UUID type for agents that had the identifier created by the script
    if not agent_identifier_type:
        agent_identifier_type = 'UUID'

    event_output = get_md_file(testpath)

    event_root = ET.parse(event_output).getroot()

    # Assert that the correct number of agents have been linked
    assert len(event_root.xpath('//premis:linkingAgentIdentifierValue',
                                namespaces=NAMESPACES)) == agents_count

    # assert that the correct identifer is linked based on the given options
    assert event_root.xpath(
        '//premis:linkingAgentIdentifierType',
        namespaces=NAMESPACES)[0].text == agent_identifier_type
    if agent_identifier_values:
        assert event_root.xpath(
            '//premis:linkingAgentIdentifierValue',
            namespaces=NAMESPACES)[0].text in agent_identifier_values
    if create_agent_file:
        assert event_root.xpath(
            '//premis:linkingAgentRole',
            namespaces=NAMESPACES)[0].text == 'testing'

    # Assert that the correct number of agent XML files have been created
    count = 0
    for filename in os.listdir(testpath):
        if filename.endswith('-PREMIS%3AAGENT-amd.xml'):
            count += 1
    assert count == agents_count


@pytest.mark.parametrize("file_, base_path", [
    ("tests/data/audio/valid__wav.wav", ""),
    ("./tests/data/audio/valid__wav.wav", ""),
    ("audio/valid__wav.wav", "tests/data"),
    ("./audio/valid__wav.wav", "./tests/data"),
    ("data/audio/valid__wav.wav", "absolute")
])
def test_paths(testpath, file_, base_path, run_cli):
    """ Test the following path arguments:
    (1) Path without base_path
    (2) Path without base bath, but with "./"
    (3) Path with base path
    (4) Path with base path and with "./"
    (5) Absolute base path
    """
    if "absolute" in base_path:
        base_path = os.path.join(os.getcwd(), "tests")
    if base_path:
        run_cli(premis_event.main, [
            "--workspace", testpath, "--base_path", base_path,
            "--event_target", file_, "--event_detail", "foo",
            "--event_outcome", "success", "creation",
            "--event_outcome_detail", "Test ok",
            "2020-02-02T20:20:20"
        ])
    else:
        run_cli(premis_event.main, [
            "--workspace", testpath, "--event_target", file_,
            "--event_outcome_detail", "Test ok",
            "--event_detail", "foo", "--event_outcome",
            "success", "creation", "2020-02-02T20:20:20"
        ])

    md_references = read_md_references(testpath,
                                       'premis-event-md-references.jsonl')
    assert os.path.normpath(file_) in md_references
    assert os.path.isfile(os.path.normpath(os.path.join(base_path, file_)))
