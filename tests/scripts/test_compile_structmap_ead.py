"""Tests the compile_structmap module with ead3 metadata."""
from __future__ import unicode_literals

import os
import mets
import pytest

import lxml.etree as ET
import premis

from siptools.utils import read_md_references
from siptools.scripts import compile_structmap, import_object
from siptools.xml.mets import NAMESPACES


def create_test_data(workspace, run_cli, order=True):
    """Create technical metadata test data."""
    param1 = [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Software files/koodi.java']
    param2 = [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Publication files/publication.txt']

    if order:
        param1.append('--order')
        param1.append('0001')
        param2.append('--order')
        param2.append('0002')

    run_cli(import_object.main, param1)
    run_cli(import_object.main, param2)


def test_compile_structmap_ok(testpath, run_cli):
    """Tests the successful compilation of mets:structmap
    by using ead3 metadata as basis. Test that a leading slash
    in the ead3 metadata is removed since only relative paths
    are allowed.
    """
    create_test_data(testpath, run_cli)
    arguments = [
        '--structmap_type', 'EAD3-logical', '--dmdsec_loc',
        'tests/data/import_description/metadata/ead3_test.xml', '--workspace',
        testpath]
    run_cli(compile_structmap.main, arguments)

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = ET.parse(output_filesec)
    fs_root = fs_tree.getroot()

    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/*'),
        namespaces=NAMESPACES)) == 2
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Software+'
         'files/koodi.java"]'), namespaces=NAMESPACES)) == 1
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Publication+'
         'files/publication.txt"]'), namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div[@LABEL="fonds"]', namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div[@LABEL="subseries"]',
        namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div/mets:div[@LABEL="item"]',
        namespaces=NAMESPACES)) == 1
    assert len(sm_root.xpath(
        '//mets:div/mets:div/mets:div/mets:div/mets:div[@LABEL="file"]',
        namespaces=NAMESPACES)) == 2
    assert sm_root.xpath(
        '//mets:div[@LABEL="file"]/*',
        namespaces=NAMESPACES)[0].tag == '{http://www.loc.gov/METS/}fptr'
    assert 'FILEID' in sm_root.xpath(
        '//mets:div[@LABEL="file"]/*', namespaces=NAMESPACES)[0].attrib
    assert sm_root.xpath(
        '//mets:div[@LABEL="file"]',
        namespaces=NAMESPACES)[0].get('ORDER') == '1'
    assert sm_root.xpath(
        '//mets:div[@LABEL="file"]',
        namespaces=NAMESPACES)[1].get('ORDER') == '2'

    # Assert that an event has been created
    references = read_md_references(testpath,
                                    'premis-event-md-references.jsonl')

    for amdref in references['.']['md_ids']:
        output = os.path.join(
            testpath, amdref[1:] + '-PREMIS%3AEVENT-amd.xml')
        if os.path.exists(output):
            event_output_path = os.path.join(testpath, output)
            event_root = ET.parse(event_output_path).getroot()
            if premis.parse_event_type(event_root) != 'creation':
                continue
            found_root = event_root
    assert found_root.xpath('./*/*/*/*/*')[0].tag == ('{info:lc/xmlns/'
                                                      'premis-v2}event')
    assert found_root.xpath(
        '//premis:eventDetail',
        namespaces=NAMESPACES)[0].text == ('Creation of structural metadata '
                                           'with the compile-structmap script')
    assert found_root.xpath(
        '//premis:eventOutcomeDetailNote',
        namespaces=NAMESPACES)[0].text == ('Created METS structural map of '
                                           'type EAD3-logical')


def test_collect_dao_hrefs():
    """Tests that the function collect_dao_hrefs returns a list with
    hrefs without leading slashes from ead3 test data.
    """
    ead3 = ('<ead3:c xmlns:ead3="http://ead3.archivists.org/schema/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://ead3.archivists.org/schema '
            'http://www.loc.gov/ead/ead3.xsd"><ead3:did><ead3:daoset>'
            '<ead3:dao daotype="derived" href="file1.txt"/>'
            '<ead3:dao daotype="derived" href="/file2.txt"/>'
            '</ead3:daoset></ead3:did></ead3:c>')
    xml = ET.fromstring(ead3)
    hrefs = compile_structmap.collect_dao_hrefs(xml)
    assert hrefs == ['file1.txt', 'file2.txt']


@pytest.mark.parametrize(
    ('hrefs', 'length', 'child_elem', 'order'),
    [(['koodi.java'], 1, 'fptr', True),
     (['koodi.java', 'publication.txt'], 2, 'div', True),
     (['koodi.java', 'publication.txt', 'fooo'], 2, 'div', True),
     (['koodi.java', 'publication.txt'], 2, 'fptr', False)],
    ids=(
            'One href: add ORDER to existing div',
            'Two hrefs: add new divs for each href',
            'One non-existing href: add just the existing hrefs',
            'No file properties: just fptr elements added'
    )
)
# pylint: disable=too-many-arguments
def test_add_fptrs_div_ead(testpath, run_cli, hrefs, length, child_elem,
                           order):
    """Tests the add_fptrs_div_ead function by asserting that the c_div
    element has been modified with fptrs and divs correctly according to
    the test cases.
    """
    create_test_data(testpath, run_cli, order=order)
    div_elem = '<mets:div xmlns:mets="http://www.loc.gov/METS/"></mets:div>'

    xml = ET.fromstring(div_elem)
    attrs = {}
    attrs["all_amd_refs"] = read_md_references(
        testpath,
        "import-object-md-references.jsonl"
    )
    attrs["object_refs"] = attrs["all_amd_refs"]
    attrs["workspace"] = testpath
    attrs["filelist"] = [
        'tests/data/structured/Publication files/publication.txt',
        'tests/data/structured/Software files/koodi.java']
    filegrp = filegrp = mets.filegrp()
    c_div = compile_structmap.add_fptrs_div_ead(
        xml, hrefs, filegrp, attrs)

    # Child elements are either new divs or fptrs
    assert c_div.xpath(
        './*')[0].tag == '{http://www.loc.gov/METS/}%s' % child_elem

    # Number of child elements should equal the number of valid hrefs
    assert len(c_div.xpath('./*')) == length

    # Number of fptr elements should equal the number of valid hrefs
    assert len(c_div.findall('.//{http://www.loc.gov/METS/}fptr')) == length

    # If file properties exist, it is written to the divs
    if order and length == 1:
        assert 'ORDER' in c_div.attrib
    elif order:
        assert 'ORDER' in c_div.xpath('./*')[0].attrib
        assert c_div.xpath('./*')[0].get('TYPE') == 'dao'
    else:
        assert 'ORDER' not in c_div.attrib
