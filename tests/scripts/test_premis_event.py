from tempfile import NamedTemporaryFile
import xml.etree.ElementTree as ET
from siptools.scripts import premis_event
import pytest
import os

def test_premis_event_ok():

    event_type ='creation'

    return_code = premis_event.main([event_type, '2016-10-13T12:30:55',
        '--event_detail', 'Testing', '--event_outcome', 'success',
        '--event_outcome_detail', 'Outcome detail', '--workspace', './workspace'])

    output_file = os.path.join('./workspace', event_type + '.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()
    #print "root: %s" % ET.tostring(root, encoding='UTF-8', method='xml')

    # miten etsitaan digiprovMD?
    assert len(root.findall('{http://www.loc.gov/METS/}amdSec')) == 1

    assert return_code == 0

def test_premis_event_fail():

    event_type ='nonsense'

    with pytest.raises(SystemExit):
        return_code = premis_event.main([event_type, '2016-10-13T12:30:55',
            '--event_detail', 'Testing', '--event_outcome', 'success',
            '--event_outcome_detail', 'Outcome detail', '--workspace', './workspace'])
