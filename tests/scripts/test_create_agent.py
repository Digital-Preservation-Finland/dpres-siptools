"""Tests for :mod:`siptools.scripts.create_agent` module"""
from __future__ import unicode_literals

import os
import io
import json

import pytest
from siptools.scripts import create_agent


@pytest.mark.parametrize(
    ("given_identifier", "role", "version", "ag_type", "ag_count"), [
        (False, None, None, "person", 1),
        (False, 'tester', None, "person", 1),
        (True, None, None, "person", 1),
        (True, None, '1.0', "person", 1),
        (True, None, '1.0', "software", 1),
        (False, None, None, "person", 3),
    ],
    ids=("Agent with minimum data",
         "Agent with event role",
         "Agent with given identifier that should be written to the output",
         "Agent_version that shouldn't be written due to the agent_type",
         "Agent with agent_version that should be written",
         "Multiple agents, all should be written to the same output"))
# pylint: disable=too-many-arguments
def test_create_agent_ok(
        testpath, run_cli, given_identifier, role, version, ag_type, ag_count):
    """Test that main function produces a json file with
    correct data for different input.
    """
    for i in range(ag_count):
        agent_name = 'test-agent%i' % i
        cli_args = [
            agent_name,
            '--workspace', testpath,
            '--agent_type', ag_type,
            '--agent_version', version,
            '--agent_note', 'Notes',
            '--create_agent_file', 'test-file',
        ]
        if given_identifier:
            cli_args.append('--agent_identifier')
            cli_args.append('test')
            cli_args.append('foo')
        if role:
            cli_args.append('--agent_role')
            cli_args.append(role)
        run_cli(create_agent.main, cli_args)

    identifier_type = 'local'
    if given_identifier:
        identifier_type = 'test'

    # Read output files
    create_agent_file = os.path.join(testpath, 'test-file-AGENTS-amd.json')
    assert os.path.exists(create_agent_file)

    with io.open(create_agent_file, 'rt') as in_file:
        agent_data = json.load(in_file)

    assert len(agent_data) == ag_count
    for agent in agent_data:
        assert agent["identifier_type"] == identifier_type
        assert 'test-agent' in agent["agent_name"]
        assert agent["agent_type"] == ag_type
        if given_identifier:
            assert agent["identifier_value"] == 'foo'
        if role:
            assert agent["agent_role"] == role
        if ag_type != 'software':
            assert "agent_version" not in agent
        if ag_type == 'software':
            assert agent["agent_version"] == version
        assert agent["agent_note"] == 'Notes'
