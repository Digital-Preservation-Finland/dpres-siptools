""" Test"""
import sys
import os
import lxml.etree as ET
from click.testing import CliRunner
from siptools.scripts.import_description import main


def get_md_file(path, input_target):
    """Get id"""
    ref = os.path.join(path, 'amd-references.xml')

    root = ET.parse(ref).getroot()
    amdref = root.xpath("/amdReferences/amdReference"
                        "[@directory='%s']" % input_target.decode(
                            sys.getfilesystemencoding()))[0]
    output = os.path.join(path, amdref.text[1:] +
                          "-dmdsec.xml")
    return output


def test_import_description_valid_file(testpath):
    """ Test case for single valid xml-file"""
    dmdsec_location = 'tests/data/import_description/metadata/' \
        'dc_description.xml'
    dmdsec_target = 'tests/data/structured/'

    runner = CliRunner()
    runner.invoke(main, [
        dmdsec_location, '--dmdsec_target', dmdsec_target,
        '--workspace', testpath, '--remove_root'])
    output = get_md_file(testpath, dmdsec_target)

    output_path = os.path.join(testpath, output)
    tree = ET.parse(output_path)
    root = tree.getroot()
    assert len(root.xpath('./*/*/*/*')) == 4
    assert root.xpath('./*/*/*/*')[0].tag == \
        '{http://purl.org/dc/elements/1.1/}title'


def test_import_description_file_not_found(testpath):
    """ Test case for not existing xml-file."""
    dmdsec_location = 'tests/data/import_description/metadata/' \
        'dc_description_not_found.xml'
    dmdsec_target = 'tests/data/structured/'

    runner = CliRunner()
    result = runner.invoke(main, [
        dmdsec_location, '--dmdsec_target', dmdsec_target,
        '--workspace', testpath])
    assert isinstance(result.exception, SystemExit)


def test_import_description_no_xml(testpath):
    """ test case for invalid XML file """
    dmdsec_location = 'tests/data/import_description/plain_text.xml'
    dmdsec_target = 'tests/data/structured/'

    runner = CliRunner()
    result = runner.invoke(main, [
        dmdsec_location, '--workspace', dmdsec_target,
        '--workspace', testpath])
    assert isinstance(result.exception, ET.XMLSyntaxError)


def test_import_description_invalid_namespace(testpath):
    """ test case for invalid namespace in XML file """
    dmdsec_location = 'tests/data/import_description/dc_invalid_ns.xml'
    dmdsec_target = 'tests/data/structured/'

    runner = CliRunner()
    result = runner.invoke(main, [
        dmdsec_location, '--workspace', dmdsec_target,
        '--workspace', testpath])
    assert isinstance(result.exception, TypeError)
