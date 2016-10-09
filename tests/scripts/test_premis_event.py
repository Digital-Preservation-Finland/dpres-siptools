from tempfile import NamedTemporaryFile
import xml.etree.ElementTree as ET
from siptools.scripts import premis_event
import pytest
import os

def test_premis_event_ok():

    event_type = 'creation'
    event_datetime = '2016-10-13T12:30:55'
    event_detail = '--event_detail Testing'
    output = '--workspace ./workspace'
    arguments = [event_type, event_datetime, event_detail, output]
    print "arguments: %s" % arguments
    #return_code = premis_event.main(arguments)
    return_code = premis_event.main(['creation','2016-10-13T12:30:55',
        '--event_detail', 'Testing', '--event_outcome', 'success', '--workspace', './workspace'])

    output_file = os.path.join('./workspace', event_type + '.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()

    assert len(root.findall('{http://www.loc.gov/METS/}digiprovMD')) == 1

    assert return_code == 0


#@pytest.mark.parametrize('input_file', ['tests/data/missing-file'])
#def test_import_object_fail(input_file):
#    with pytest.raises(IOError):
#        arguments = [input_file, input_file]
#        import_object.main(arguments)
