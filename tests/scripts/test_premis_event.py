"""Tests for :mod:`siptools.scripts.premis_event` module"""
import os
import xml.etree.ElementTree as ET
from siptools.scripts import premis_event
import pytest


def test_premis_event_ok(testpath):
    """Test that main function produces xml file with correct elements."""

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

    output_file = os.path.join(testpath,
                               'tests%2Fdata%2Fstructured-creation-event.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()

    assert len(root.findall('{http://www.loc.gov/METS/}amdSec')) == 1
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventType"
    )[0].text == 'creation'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventDateTime"
    )[0].text == '2016-10-13T12:30:55'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventDetail"
    )[0].text == 'Testing'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventOutcome"
    )[0].text == 'success'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventOutcomeDetailNote"
    )[0].text == 'Outcome detail'

    assert return_code == 0


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
