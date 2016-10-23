import xml.etree.ElementTree as ET
from siptools.scripts import compile_mets
import pytest
import os


def test_compile_mets_ok():

    return_code = compile_mets.main(['CSC', '--create_date', '2016-10-28T09:30:55',
                                     '--last_moddate', '2016-10-28T09:30:55',
                                     '--record_status', 'submission', '--workspace',
                                     './workspace'])

    output_file = os.path.join('./workspace', 'mets.xml')
    tree = ET.parse(output_file)
    root = tree.getroot()
    # print "root: %s" % ET.tostring(root, encoding='UTF-8', method='xml')

    assert len(root.findall('{http://www.loc.gov/METS/}metsHdr')) == 1
    assert len(root.findall(
        '{http://www.loc.gov/METS/}metsHdr[@CREATEDATE="2016-10-28T09:30:55"]')) == 1
    assert len(root.findall(
        '{http://www.loc.gov/METS/}metsHdr[@LASTMODDATE="2016-10-28T09:30:55"]')) == 1
    assert len(root.findall(
        '{http://www.loc.gov/METS/}metsHdr[@RECORDSTATUS="submission"]')) == 1
    assert root.findall(".//{http://www.loc.gov/METS/}name")[0].text == 'CSC'

    assert return_code == 0


def test_compile_mets_fail():

    with pytest.raises(SystemExit):
        return_code = compile_mets.main(['CSC', '--create_date',
                                         '2016-10-28T09:30:55', '--last_moddate', '2016-10-28T09:30:55',
                                         '--record_status', 'nonsense', '--workspace', './workspace'])
