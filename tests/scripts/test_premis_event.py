from tempfile import NamedTemporaryFile
import xml.etree.ElementTree as ET
from siptools.scripts import premis_event
import pytest
import os


def test_premis_event_ok(testpath):

    event_type = 'creation'

    return_code = premis_event.main([event_type, '2016-10-13T12:30:55',
                                     '--event_detail', 'Testing', '--event_outcome', 'success',
                                     '--event_outcome_detail', 'Outcome detail', '--workspace',
                                     testpath, '--agent_name', 'Demo Application', '--agent_type', 'software'])

    output_file = os.path.join(testpath, event_type + '.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()

    assert len(root.findall('{http://www.loc.gov/METS/}amdSec')) == 1
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventType")[0].text == 'creation'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventDateTime")[0].text == '2016-10-13T12:30:55'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventDetail")[0].text == 'Testing'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventOutcome")[0].text == 'success'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}eventOutcomeDetailNote")[0].text == 'Outcome detail'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}agentName")[0].text == 'Demo Application'
    assert root.findall(
        ".//{info:lc/xmlns/premis-v2}agentType")[0].text == 'software'

    assert return_code == 0


def test_premis_event_fail(testpath):

    event_type = 'nonsense'

    with pytest.raises(SystemExit):
        return_code = premis_event.main([event_type, '2016-10-13T12:30:55',
                                         '--event_detail', 'Testing', '--event_outcome', 'success',
                                         '--event_outcome_detail', 'Outcome detail', '--workspace', testpath])
