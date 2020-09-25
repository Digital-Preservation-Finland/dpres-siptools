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
    param3 = [
        '--workspace', workspace, '--skip_wellformed_check',
        'tests/data/structured/Documentation files/readme.txt']

    if order:
        param1.append('--order')
        param1.append('1')
        param2.append('--order')
        param2.append('2')

    run_cli(import_object.main, param1)
    run_cli(import_object.main, param2)
    run_cli(import_object.main, param3)


@pytest.mark.parametrize(('path', 'daosets'), [
    ('tests/data/import_description/metadata/ead3_test.xml', False),
    ('tests/data/import_description/metadata/ead3_daoset_test.xml', True)
])
def test_compile_structmap_ok(testpath, run_cli, path, daosets):
    """Tests the successful compilation of mets:structmap
    by using ead3 metadata as basis. Test that a leading slash
    in the ead3 metadata is removed since only relative paths
    are allowed.
    """
    create_test_data(testpath, run_cli)
    arguments = [
        '--structmap_type', 'EAD3-logical', '--dmdsec_loc',
        path, '--workspace',
        testpath]
    run_cli(compile_structmap.main, arguments)

    output_structmap = os.path.join(testpath, 'structmap.xml')
    sm_tree = ET.parse(output_structmap)
    sm_root = sm_tree.getroot()

    output_filesec = os.path.join(testpath, 'filesec.xml')
    fs_tree = ET.parse(output_filesec)
    fs_root = fs_tree.getroot()

    expected_filesec_length = 2
    expected_archival_files = 2
    fptr_parent = '//mets:div[@LABEL="file"]/mets:div'
    if daosets:
        expected_filesec_length = 3
        expected_archival_files = 1
        fptr_parent = '//mets:div[@TYPE="daoset"]/mets:div[@TYPE="dao"]'

    # Check amount of files created n filesec
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/*'),
        namespaces=NAMESPACES)) == expected_filesec_length

    # Assert that individual file paths are created in filesec
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Software+'
         'files/koodi.java"]'), namespaces=NAMESPACES)) == 1
    assert len(fs_root.xpath(
        ('/mets:mets/mets:fileSec/mets:fileGrp/mets:file/mets:FLocat'
         '[@xlink:href="file://tests/data/structured/Publication+'
         'files/publication.txt"]'), namespaces=NAMESPACES)) == 1

    # Check that the main EAD3 structure is translated to the structmap
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
        namespaces=NAMESPACES)) == expected_archival_files

    # Check that fptr elements and file related attributues are created in
    # the desired locations
    assert sm_root.xpath(
        '%s/*' % fptr_parent,
        namespaces=NAMESPACES)[0].tag == '{http://www.loc.gov/METS/}fptr'
    assert 'FILEID' in sm_root.xpath(
        '%s/*' % fptr_parent, namespaces=NAMESPACES)[0].attrib
    assert sm_root.xpath(
        '%s' % fptr_parent, namespaces=NAMESPACES)[0].get('ORDER') == '1'
    assert sm_root.xpath(
        '%s' % fptr_parent, namespaces=NAMESPACES)[1].get('ORDER') == '2'

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
    ead3 = ('<ead3:daoset xmlns:ead3="http://ead3.archivists.org/schema/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://ead3.archivists.org/schema '
            'http://www.loc.gov/ead/ead3.xsd">'
            '<ead3:dao daotype="derived" href="file1.txt"/>'
            '<ead3:dao daotype="derived" href="/file2.txt"/>'
            '</ead3:daoset>')
    xml = ET.fromstring(ead3)
    hrefs = compile_structmap.collect_dao_hrefs(xml)
    assert hrefs == [('file1.txt', None), ('file2.txt', None)]


@pytest.mark.parametrize(
    ('hrefs', 'length', 'child_elem', 'order'),
    [([('koodi.java', None)], 1, 'div', True),
     ([('koodi.java', None), ('publication.txt', None)], 2, 'div', True),
     ([('koodi.java', None), ('publication.txt', None), ('fooo', None)], 2,
      'div', True),
     ([('koodi.java', None), ('publication.txt', None)], 2, 'fptr', False)],
    ids=('One href: add ORDER to existing div',
         'Two hrefs: add new divs for each href',
         'One non-existing href: add just the existing hrefs',
         'No file properties: just fptr elements added')
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
    filegrp = mets.filegrp()
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
    if order:
        assert 'ORDER' in c_div.xpath('./*')[0].attrib
        assert c_div.xpath('./*')[0].get('TYPE') == 'dao'
    else:
        assert 'ORDER' not in c_div.attrib
