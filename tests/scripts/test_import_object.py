# encoding: utf-8
"""Unit tests for ``siptools.scripts.import_object`` module."""
from __future__ import unicode_literals

import datetime
import io
import os.path

import pytest
import six

import lxml.etree as ET

from siptools.scripts import import_object
from siptools.utils import fsdecode_path, load_scraper_json, read_md_references
from siptools.xml.mets import NAMESPACES


def get_amd_file(path,
                 input_file,
                 stream=None,
                 ref_file='import-object-md-references.jsonl',
                 suffix='-PREMIS%3AOBJECT-amd.xml'):
    """Get id."""
    refs = read_md_references(path, ref_file)
    reference = refs[fsdecode_path(input_file)]

    if not stream:
        amdrefs = reference['md_ids']
    else:
        amdrefs = reference['streams'][stream]

    output = []
    for amdref in amdrefs:
        output_file = os.path.join(path, amdref[1:] + suffix)
        if os.path.exists(output_file):
            output.append(output_file)

    return output


def test_import_object_ok(testpath, run_cli):
    """Test import_object.main funtion with valid test data."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 input_file]
    run_cli(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1

    # Assert that an event has been created
    event_output = get_amd_file(
        testpath,
        ".",
        ref_file='premis-event-md-references.jsonl',
        suffix='-PREMIS%3AEVENT-amd.xml')
    event_output_path = os.path.join(testpath, event_output[0])
    event_root = ET.parse(event_output_path).getroot()
    assert event_root.xpath('./*/*/*/*/*')[0].tag == ('{info:lc/xmlns/'
                                                      'premis-v2}event')


# pylint: disable=invalid-name
def test_import_object_illegal_html_valid_text(testpath, run_cli):
    """
    Test import_object.main function --skip_well_formed argument.

    Test that a non-wellformed HTML file is passed and valid as
    plain text file.
    """
    input_file = 'tests/data/invalid_4.01_illegal_tags.html'
    arguments = ['--workspace', testpath, input_file,
                 '--file_format', 'text/plain', '',
                 '--checksum', 'MD5', '1qw87geiewgwe9',
                 '--date_created', datetime.datetime.utcnow().isoformat()]
    run_cli(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1


# pylint: disable=invalid-name
def test_import_object_skip_wellformed_check_ok(testpath, run_cli):
    """
    Test import_object.main function --skip_well_formed argument.

    Test that a non-wellformed HTML file is passed with metadata
    collection, since well-formedness checking is bypassed.
    """
    input_file = 'tests/data/invalid_4.01_illegal_tags.html'
    arguments = ['--workspace', testpath, input_file,
                 '--skip_wellformed_check',
                 '--file_format', 'text/html', '',
                 '--checksum', 'MD5', '1qw87geiewgwe9',
                 '--date_created', datetime.datetime.utcnow().isoformat()]
    run_cli(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1


# pylint: disable=invalid-name
def test_import_object_skip_wellformed_check_nodate_ok(testpath, run_cli):
    """
    Test import_object.main function without --date_created argument.

    Test that the script works without a given creation date.
    """
    input_file = 'tests/data/invalid_4.01_illegal_tags.html'
    arguments = ['--workspace', testpath, input_file,
                 '--skip_wellformed_check',
                 '--file_format', 'text/html', '',
                 '--checksum', 'MD5', '1qw87geiewgwe9']
    run_cli(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1


# pylint: disable=invalid-name
def test_import_object_structured_ok(testpath, run_cli):
    # TODO: Missing function docstring. What is the purpose of this test?
    workspace = os.path.abspath(testpath)
    test_data = os.path.abspath(os.path.join(os.curdir,
                                             'tests/data/structured'))
    test_file = ""
    for element in iterate_files(test_data):
        arguments = ['--workspace', workspace, '--skip_wellformed_check',
                     os.path.relpath(element, os.curdir)]
        run_cli(import_object.main, arguments)
        test_file = os.path.relpath(element, os.curdir)

        output = get_amd_file(testpath, test_file)
        tree = ET.parse(output[0])
        root = tree.getroot()

        assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                              namespaces=NAMESPACES)) == 1


# pylint: disable=invalid-name
def test_import_object_multiple(testpath, run_cli):
    """Test importing directory.

    Tests that import object works for multiple files when filepath
    is a directory. The test asserts that an equal amount of premis
    object metadata files have been created to the amount of imported
    files. The test also checks that the numer of links in the reference
    file equals that amount.
    """
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 'tests/data/structured']
    run_cli(import_object.main, arguments)

    expected_files = 9

    refs = read_md_references(testpath, 'import-object-md-references.jsonl')
    assert len(refs) == expected_files

    count = 0
    for filename in os.listdir(testpath):
        if filename.endswith('-PREMIS%3AOBJECT-amd.xml'):
            count += 1
    assert count == expected_files


def test_import_object_order(testpath, run_cli):
    """Test file order."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 '--order', '5', input_file]
    run_cli(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    path = output[0].replace('-PREMIS%3AOBJECT-amd.xml', '-scraper.json')
    assert os.path.isfile(path)

    streams = load_scraper_json(path)
    assert 'properties' in streams[0]
    assert 'order' in streams[0]['properties']
    assert streams[0]['properties']['order'] == '5'


def test_import_object_supplementary(testpath, run_cli):
    """Test importing supplementary file."""
    input_file = "tests/data/structured/Documentation files/readme.txt"
    arguments = ["--workspace", testpath,
                 "--supplementary", "xml_schema", input_file]
    run_cli(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    path = output[0].replace("-PREMIS%3AOBJECT-amd.xml", "-scraper.json")
    assert os.path.isfile(path)

    streams = load_scraper_json(path)
    assert "xml_schema" in streams[0]["properties"]["supplementary"]


def test_import_object_identifier(testpath, run_cli):
    """Test digital object identifier argument."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 '--identifier', 'local', 'test-id', input_file]
    run_cli(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert root.xpath('//premis:objectIdentifierType',
                      namespaces=NAMESPACES)[0].text == 'local'
    assert root.xpath('//premis:objectIdentifierValue',
                      namespaces=NAMESPACES)[0].text == 'test-id'


# pylint: disable=invalid-name
def test_import_object_format_registry(testpath, run_cli):
    """Test digital object format registry argument."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 '--format_registry', 'local', 'test-key', input_file]
    run_cli(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert root.xpath('//premis:formatRegistryName',
                      namespaces=NAMESPACES)[0].text == 'local'
    assert root.xpath('//premis:formatRegistryKey',
                      namespaces=NAMESPACES)[0].text == 'test-key'


def test_import_object_creating_application(testpath, run_cli):
    """Test adding creating application metadata."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 '--creating_application', 'My app', '1.0', input_file]
    run_cli(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    assert root.xpath('//premis:creatingApplicationName',
                      namespaces=NAMESPACES)[0].text == 'My app'
    assert root.xpath('//premis:creatingApplicationVersion',
                      namespaces=NAMESPACES)[0].text == '1.0'


def test_import_object_utf8(testpath, run_cli):
    """Test that import_object supports utf-8.

    Test that importing works for file that:

    * is a utf-8 encoded text file
    * has utf-8 encoded filename
    * is in utf-8 encoded directory

    import_object.main should create TechMD-file with utf8-encoded
    filename.
    """
    # Create directory that contains one file
    utf8_directory = os.path.join(testpath, 'directory Ä')
    os.mkdir(utf8_directory)
    utf8_file = os.path.join(utf8_directory, 'testfile Ö')
    with io.open(utf8_file, 'wt') as file_:
        file_.write('Voi änkeröinen.')

    # Run function
    arguments = ['--workspace', testpath, '--skip_wellformed_check', utf8_file]
    run_cli(import_object.main, arguments)

    # Check output
    output = get_amd_file(testpath, utf8_file)
    tree = ET.parse(output[0])
    root = tree.getroot()
    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1


def test_unap_version(testpath, run_cli):
    """Test that given (:unap) version is normalized as empty.
    """
    input_file = "tests/data/structured/Documentation files/readme.txt"
    arguments = ["--file_format", 'text/plain', '(:unap)',
                 "--workspace", testpath, input_file]
    run_cli(import_object.main, arguments)

    # Check output
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()
    assert len(root.xpath(".//premis:formatName",
                          namespaces=NAMESPACES)) == 1
    assert len(root.xpath(".//premis:formatVersion",
                          namespaces=NAMESPACES)) == 0


def test_original_name(testpath, run_cli):
    """Test that given original name is added.
    """
    input_file = "tests/data/structured/Documentation files/readme.txt"
    arguments = ["--original_name", "readme.txt",
                 "--workspace", testpath, input_file]
    run_cli(import_object.main, arguments)

    # Check output
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()
    assert root.xpath(".//premis:originalName",
                      namespaces=NAMESPACES)[0].text == "readme.txt"


def test_import_object_native(testpath, run_cli):
    """Test that import_object can import native formats.

    In such cases, no validation event is created even if we are performing
    the well-formedness check.
    """
    input_file = "tests/data/video/invalid__prores_lpcm8.mov"
    arguments = ["--workspace", testpath, input_file]
    run_cli(import_object.main, arguments)

    # Check output
    events_output = get_amd_file(
        testpath,
        ".",
        ref_file='premis-event-md-references.jsonl',
        suffix='-PREMIS%3AEVENT-amd.xml'
    )
    event_trees = [ET.parse(path).getroot() for path in events_output]
    allowed_types = [
        'metadata extraction',
        'format identification',
        'message digest calculation'
    ]

    # All events except for 'validation' are created. Since we are importing
    # a native file, validation event is not created even if we have the
    # well-formedness check enabled.
    assert len([
        True for tree in event_trees
        if tree.xpath(
            "//premis:eventType",
            namespaces=NAMESPACES
        )[0].text in allowed_types
    ]) == 3
    assert len(event_trees) == 3


def test_bit_level(testpath, run_cli):
    """Test import_object with '--bit_level' argument."""
    input_file = "tests/data/text-file.txt"
    arguments = ["--workspace", testpath,
                 "--bit_level",
                 "--file_format", "text/plain", "",
                 input_file]
    run_cli(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    path = output[0].replace("-PREMIS%3AOBJECT-amd.xml", "-scraper.json")
    assert os.path.isfile(path)

    streams = load_scraper_json(path)
    assert streams[0]["properties"]["bit_level"]

    tree = ET.parse(output[0])
    root = tree.getroot()
    assert (root.xpath("//premis:formatName", namespaces=NAMESPACES)[0].text ==
            "text/plain; charset=UTF-8")


def test_bit_level_missing_format(testpath, run_cli):
    """Test that import_object raises an error if '--bit_level' argument is
    given without a '--file_format' value.
    """
    input_file = "tests/data/text-file.txt"
    arguments = ["--workspace", testpath,
                 "--bit_level",
                 input_file]
    result = run_cli(import_object.main, arguments, success=False)
    assert result.exception


# TODO: Combine this test with test_import_object_cases_for_lite once we're
#       using version that pytest supports pytest.param.
#       This test is identical to it except no additional option is provided
#       and this test is marked "validate"
# TODO: Replace with pytest.param(*args, id=test_case) once we're using the
#       version that pytest supports it so that we'll have easier time to see
#       what each parametrize test case is testing.
@pytest.mark.validate
@pytest.mark.parametrize(
    ('input_file', 'expected_mimetype', 'expected_version', 'case_name'), [
        ('tests/data/test_import.pdf', 'application/pdf', '1.4', 'pdf'),
        ('tests/data/valid_tiff.tif', 'image/tiff', '6.0', 'tiff'),
        ('tests/data/valid_jpeg.jpeg', 'image/jpeg', ('1.0', '1.01', '1.02'),
         'jpeg'),
        ('tests/data/text-file.txt', 'text/plain; charset=UTF-8', None,
         'text'),
        ('tests/data/csvfile.csv', 'text/plain; charset=UTF-8', None, 'csv'),
        ('tests/data/mets_valid_minimal.xml', 'text/xml; charset=UTF-8', '1.0',
         'xml'),
        ('tests/data/ODF_Text_Document.odt',
         'application/vnd.oasis.opendocument.text', '1.1', 'odt'),
        ('tests/data/MS_Excel_97-2003.xls', 'application/vnd.ms-excel',
         '8X', 'excel'),
        ('tests/data/MS_Word_2007-2013_XML.docx',
         'application/vnd.openxmlformats-officedocument.'
         'wordprocessingml.document', '2007 onwards', 'word docx'),
        ('tests/data/audio/valid__wav.wav', 'audio/x-wav', None,
         'audio wav no version'),
        ('tests/data/audio/valid_2_bwf.wav', 'audio/x-wav', '2',
         'audio wav v2'),
    ]
)
# pylint: disable=too-many-arguments
def test_import_object_cases(testpath, input_file, expected_mimetype,
                             expected_version, case_name, run_cli):
    """Test the import_object tool function when run as terminal client.

    In addition to getting the metadata, we're also validating.

    :param expected_version: Depending on the type of value provided,
        comparison logic differs for version comparison:
            - string: exact match is expected.
            - tuple: premis version must match any of the value
              provided.
            - None: premis version must be a falsy value.
    """
    _ = case_name
    arguments = ['--workspace', testpath, input_file]
    run_cli(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    comparison = {
        six.text_type: lambda element, expected: element[0] == expected,
        tuple: lambda element, expected: element[0] in expected,
        None.__class__: lambda element, expected: not element
    }

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName/text()',
                      namespaces=NAMESPACES)[0] == expected_mimetype

    assert comparison[expected_version.__class__](
        root.xpath('//premis:formatVersion/text()',
                   namespaces=NAMESPACES),
        expected_version
    )


# TODO: Once pytest version is upgraded, combine this test with above
#       test_import_object_cases. This test is identical to it except
#       "--skip_wellformed_check" option is provided and this is not marked
#       as "validate".
@pytest.mark.parametrize(
    ('input_file', 'expected_mimetype', 'expected_version', 'case_name'), [
        ('tests/data/test_import.pdf', 'application/pdf', '1.4', 'pdf'),
        ('tests/data/valid_tiff.tif', 'image/tiff', '6.0', 'tiff'),
        ('tests/data/valid_jpeg.jpeg', 'image/jpeg', ('1.0', '1.01', '1.02'),
         'jpeg'),
        ('tests/data/text-file.txt', 'text/plain; charset=UTF-8', None,
         'text'),
        ('tests/data/csvfile.csv', 'text/plain; charset=UTF-8', None, 'csv'),
        ('tests/data/mets_valid_minimal.xml', 'text/xml; charset=UTF-8', '1.0',
         'xml'),
        ('tests/data/ODF_Text_Document.odt',
         'application/vnd.oasis.opendocument.text', '1.1', 'odt'),
        ('tests/data/MS_Excel_97-2003.xls', 'application/vnd.ms-excel',
         '8X', 'excel'),
        ('tests/data/MS_Word_2007-2013_XML.docx',
         'application/vnd.openxmlformats-officedocument.'
         'wordprocessingml.document', '2007 onwards', 'word docx'),
        ('tests/data/audio/valid__wav.wav', 'audio/x-wav', None,
         'audio wav no version'),
        ('tests/data/audio/valid_2_bwf.wav', 'audio/x-wav', '2',
         'audio wav v2'),
    ]
)
# pylint: disable=invalid-name
# pylint: disable=too-many-arguments
def test_import_object_cases_for_lite(testpath, input_file, expected_mimetype,
                                      expected_version, case_name, run_cli):
    """Test the import_object tool function when run as terminal client
    to see if we could fetch the metadata.

    :param expected_version: Depending on the type of value provided,
        comparison logic differs for version comparison:
            - string: exact match is expected.
            - tuple: premis version must match any of the value
              provided.
            - None: premis version must be a falsy value.
    """
    _ = case_name
    arguments = ['--workspace', testpath, input_file,
                 '--skip_wellformed_check']
    run_cli(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()

    comparison = {
        six.text_type: lambda element, expected: element[0] == expected,
        tuple: lambda element, expected: element[0] in expected,
        None.__class__: lambda element, expected: not element
    }

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName/text()',
                      namespaces=NAMESPACES)[0] == expected_mimetype

    assert comparison[expected_version.__class__](
        root.xpath('//premis:formatVersion/text()',
                   namespaces=NAMESPACES),
        expected_version
    )


def test_import_object_fail(run_cli):
    """Test importing missing file.

    Test that import_object.main raises error if target file does not
    exist.
    """
    result = run_cli(
        import_object.main, ['tests/data/missing-file'],
        success=False
    )
    assert result.exception


def iterate_files(path):
    """Iterate through all files inside a directory."""
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            yield os.path.join(root, name)


def test_streams(testpath, run_cli):
    """Test importing file with streams.

    The test file contains one video and one audio stream.
    """
    input_file = 'tests/data/video/valid__h264_aac.mp4'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 input_file]
    run_cli(import_object.main, arguments)

    # Streams
    stream_id = []
    for i in [1, 2]:
        output = get_amd_file(testpath, input_file, six.text_type(i))
        tree = ET.parse(output[0])
        root = tree.getroot()
        if i == 2:
            mime = 'audio/mp4'
        else:
            mime = 'video/mp4'
        stream_id.append(root.xpath('//premis:objectIdentifierValue',
                                    namespaces=NAMESPACES)[0].text)
        assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                              namespaces=NAMESPACES)) == 1
        assert root.xpath('//premis:formatName',
                          namespaces=NAMESPACES)[0].text == mime
        assert len(root.xpath('//premis:formatVersion',
                              namespaces=NAMESPACES)) == 0
        assert not root.xpath('//premis:messageDigest',
                              namespaces=NAMESPACES)
        assert not root.xpath('//premis:relationship',
                              namespaces=NAMESPACES)
        assert root.xpath('//premis:object/@xsi:type',
                          namespaces=NAMESPACES)[0] == 'premis:bitstream'

    # Container
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output[0])
    root = tree.getroot()
    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName',
                      namespaces=NAMESPACES)[0].text == 'video/mp4'
    assert len(root.xpath('//premis:messageDigest',
                          namespaces=NAMESPACES)) == 1
    assert len(root.xpath('//premis:relationship',
                          namespaces=NAMESPACES)) == 2
    assert root.xpath('//premis:object/@xsi:type',
                      namespaces=NAMESPACES)[0] == 'premis:file'
    assert len(root.xpath(
        '//premis:relatedObjectIdentifierValue[.="%s"]' % stream_id[0],
        namespaces=NAMESPACES)) == 1
    assert len(root.xpath(
        '//premis:relatedObjectIdentifierValue[.="%s"]' % stream_id[1],
        namespaces=NAMESPACES)) == 1


@pytest.mark.parametrize(
    ('file_format', 'checksum', 'skip_wellformed_check', 'count_events'), [
        (('text/plain', ''), ('MD5', 'aabbccdd'), True, 1),
        (None, ('MD5', 'aabbccdd'), True, 2),
        (None, None, True, 3),
        (None, None, False, 4)]
)
# pylint: disable=too-many-locals
def test_import_object_event_agent(
        testpath,
        run_cli,
        file_format,
        checksum,
        skip_wellformed_check,
        count_events):
    """Test that the script import_object creates events and
    agents with the proper metadata.
    """
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, input_file]
    if file_format:
        arguments.append('--file_format')
        arguments.append(file_format[0])
        arguments.append(file_format[1])
    if skip_wellformed_check:
        arguments.append('--skip_wellformed_check')
    if checksum:
        arguments.append('--checksum')
        arguments.append(checksum[0])
        arguments.append(checksum[1])

    run_cli(import_object.main, arguments)

    events_output = get_amd_file(
        testpath,
        ".",
        ref_file='premis-event-md-references.jsonl',
        suffix='-PREMIS%3AEVENT-amd.xml')

    # Allow only part of values in the lists based on the number of
    # different events created
    allowed_types = ['metadata extraction',
                     'format identification',
                     'message digest calculation',
                     'validation'][:count_events]
    allowed_details = [('Premis metadata successfully created from extracted '
                        'technical metadata.'),
                       ('File MIME type and format version successfully '
                        'identified.'),
                       ('Checksum(s) successfully calculated for digital '
                        'object(s).'),
                       ('Digital object(s) evaluated as well-formed and '
                        'valid.')][:count_events]

    # Assert that the event metadata is as expected
    assert len(events_output) == count_events
    for event_output in events_output:
        event_output_path = os.path.join(testpath, event_output)
        event_root = ET.parse(event_output_path).getroot()
        event_tag = event_root.xpath('./*/*/*/*/*')[0].tag
        assert event_tag == '{info:lc/xmlns/premis-v2}event'
        assert event_root.xpath(
            './/premis:eventType',
            namespaces=NAMESPACES)[0].text in allowed_types
        assert event_root.xpath(
            './/premis:eventOutcomeDetailNote',
            namespaces=NAMESPACES)[0].text in allowed_details

    # Assert that at least one agent is linked to the event
    assert event_root.xpath('.//premis:linkingAgentIdentifier',
                            namespaces=NAMESPACES)

    agent_output = get_amd_file(
        testpath,
        ".",
        ref_file='premis-event-md-references.jsonl',
        suffix='-PREMIS%3AAGENT-amd.xml')
    agent_output_path = os.path.join(testpath, agent_output[0])
    agent_root = ET.parse(agent_output_path).getroot()
    assert agent_root.xpath('./*/*/*/*/*')[0].tag == ('{info:lc/xmlns/'
                                                      'premis-v2}agent')
    assert agent_root.xpath(
        './/premis:agentType',
        namespaces=NAMESPACES)[0].text == 'software'


def test_import_object_event(testpath, run_cli):
    """
    Test that we create only decent number of events when repeating
    importing. If the calendar day changes during the test, we may have two
    events instead of one. This is OK as we create events based on accuracy
    of a calendar day.
    """
    day_start = datetime.datetime.utcnow().strftime("%d")
    images = ["tiff1.tif", "tiff2.tif", "tiff_icc_profile_sRGB.tif"]
    for img in images:
        input_file = os.path.join("tests/data/images", img)
        arguments = ["--workspace", testpath, "--skip_wellformed_check",
                     "--file_format", "image/tiff", "6.0", "--checksum",
                     "MD5", "aabbccdd", input_file]
        run_cli(import_object.main, arguments)
    day_end = datetime.datetime.utcnow().strftime("%d")

    # Only one or two events should have been created
    new_ev_count = 0
    for filename in os.listdir(testpath):
        if filename.endswith('-PREMIS%3AEVENT-amd.xml'):
            new_ev_count += 1
    if day_start != day_end:
        assert new_ev_count in [1, 2]
    else:
        assert new_ev_count == 1


def test_import_object_event_target(testpath, run_cli):
    """Test given event target."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 input_file, '--event_target', input_file]
    run_cli(import_object.main, arguments)

    # Assert that an event with given target has been created
    event_output = get_amd_file(
        testpath,
        input_file,  # Find events targeted to input_file
        ref_file='premis-event-md-references.jsonl',
        suffix='-PREMIS%3AEVENT-amd.xml')
    assert len(event_output) == 3


def test_import_object_event_target_date(testpath, run_cli):
    """Test that the script import_object creates only one event
    when run several times but with the same event_target. Also checks
    that new agents aren't created or linked.
    """
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 input_file, '--event_target', '.', '--event_datetime',
                 '2020', '--file_format', 'text/plain', '', '--checksum',
                 'MD5', 'aabbccdd']
    run_cli(import_object.main, arguments)

    ev_count = 0
    for filename in os.listdir(testpath):
        if filename.endswith('-PREMIS%3AEVENT-amd.xml'):
            ev_count += 1
    assert ev_count == 1

    ag_count = 0
    for filename in os.listdir(testpath):
        if filename.endswith('-PREMIS%3AAGENT-amd.xml'):
            ag_count += 1
    assert ag_count > 0

    input_files = ['tests/data/structured/Documentation files/readme.txt']

    for input_file in input_files:
        arguments = ['--workspace', testpath, '--skip_wellformed_check',
                     input_file, '--event_target', '.', '--event_datetime',
                     '2020', '--file_format', 'text/plain', '', '--checksum',
                     'MD5', 'aabbccdd']
        run_cli(import_object.main, arguments)

    # Still only one event should have been created
    new_ev_count = 0
    for filename in os.listdir(testpath):
        if filename.endswith('-PREMIS%3AEVENT-amd.xml'):
            new_ev_count += 1
    assert new_ev_count == 1

    new_ag_count = 0
    for filename in os.listdir(testpath):
        if filename.endswith('-PREMIS%3AAGENT-amd.xml'):
            new_ag_count += 1
    assert new_ag_count == ag_count


@pytest.mark.parametrize(
    [
        "input_file",
        "expected_grade"
    ],
    (
        [
            'tests/data/ODF_Text_Document.odt',
            'fi-dpres-recommended-file-format'
        ],
        [
            'tests/data/MS_Word_2007-2013_XML.docx',
            'fi-dpres-acceptable-file-format'
        ]
    )
)
def test_import_object_grading(testpath, run_cli, input_file, expected_grade):
    """Test that DP grade is included in file properties."""
    arguments = ['--workspace', testpath, input_file]
    run_cli(import_object.main, arguments)

    # Read scraper.json
    output = get_amd_file(testpath, input_file)
    path = output[0].replace('-PREMIS%3AOBJECT-amd.xml', '-scraper.json')
    streams = load_scraper_json(path)

    # Digital preservation grade should be included in file properties
    assert streams[0]['properties']['grade'] == expected_grade


def test_import_object_unacceptable(testpath, run_cli):
    """Test importing file that has unacceptable format.

    Exception with clear error message should be raised.
    """
    unaccepted_file = 'tests/data/video/unaccepted_format_h264_aac.mkv'
    arguments = ['--workspace', testpath, unaccepted_file]
    expected_error_message = ('The format of file {} is unacceptable'
                              .format(unaccepted_file))
    with pytest.raises(ValueError, match=expected_error_message):
        run_cli(import_object.main, arguments)


def test_import_object_not_recognized(testpath, run_cli):
    """Test importing file that is not recognized.

    Exception with clear error message should be raised.
    """
    arguments \
        = ['--workspace', testpath, 'tests/data/invalid_empty_text-file.txt']
    expected_error_message \
        = 'Proper scraper was not found. The file was not analyzed'
    with pytest.raises(ValueError, match=expected_error_message):
        run_cli(import_object.main, arguments)
