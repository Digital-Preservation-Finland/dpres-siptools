# encoding: utf-8
"""Unit tests for ``siptools.scripts.import_object`` module"""
import sys
import os.path
import datetime
import pickle
from click.testing import CliRunner
import lxml.etree as ET
import pytest
from siptools.scripts import import_object
from siptools.xml.mets import NAMESPACES


def get_amd_file(path, input_file, stream=None):
    """Get id"""
    ref = os.path.join(path, 'md-references.xml')

    root = ET.parse(ref).getroot()
    decoded_input_file = input_file.decode(sys.getfilesystemencoding())
    if stream is None:
        amdref = root.xpath("/mdReferences/mdReference[not(@stream) and "
                            "@file='%s']" % decoded_input_file)[0]
    else:
        amdref = root.xpath("/mdReferences/mdReference[@stream='%s' and "
                            "@file='%s']" % (stream, decoded_input_file))[0]
    output = os.path.join(path, amdref.text[1:] +
                          "-PREMIS%3AOBJECT-amd.xml")
    return output


def test_import_object_ok(testpath):
    """Test import_object.main funtion with valid test data."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 input_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1

    assert result.exit_code == 0


def test_import_object_skip_wellformed_check_ok(testpath):
    """Test import_object.main function --skip-inspection argument."""
    input_file = 'tests/data/text-file.txt'
    arguments = ['--workspace', testpath, input_file,
                 '--skip_wellformed_check',
                 '--file_format', 'image/dpx', '1.0',
                 '--checksum', 'MD5', '1qw87geiewgwe9',
                 '--date_created', datetime.datetime.utcnow().isoformat()]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1

    assert result.exit_code == 0


def test_import_object_skip_wellformed_check_nodate_ok(testpath):
    """Test import_object.main function without --date_created argument."""
    input_file = 'tests/data/text-file.txt'
    arguments = ['--workspace', testpath, input_file,
                 '--skip_wellformed_check',
                 '--file_format', 'image/dpx', '1.0',
                 '--checksum', 'MD5', '1qw87geiewgwe9']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert result.exit_code == 0


def test_import_object_structured_ok(testpath):
    # TODO: Missing function docstring. What is the purpose of this test?
    workspace = os.path.abspath(testpath)
    test_data = os.path.abspath(os.path.join(os.curdir,
                                             'tests/data/structured'))
    test_file = ""
    for element in iterate_files(test_data):
        arguments = ['--workspace', workspace, '--skip_wellformed_check',
                     os.path.relpath(element, os.curdir)]
        runner = CliRunner()
        result = runner.invoke(import_object.main, arguments)
        test_file = os.path.relpath(element, os.curdir)

        output = get_amd_file(testpath, test_file)
        tree = ET.parse(output)
        root = tree.getroot()

        assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                              namespaces=NAMESPACES)) == 1
        assert result.exit_code == 0


def test_import_object_order(testpath):
    """Test file order"""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 '--order', '5', input_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    path = output.replace('-PREMIS%3AOBJECT-amd.xml',
                          '-scraper.pkl')
    assert os.path.isfile(path)

    streams = {}
    with open(path) as infile:
        streams = pickle.load(infile)

    assert 'properties' in streams[0]
    assert 'order' in streams[0]['properties']
    assert streams[0]['properties']['order'] == '5'

    assert result.exit_code == 0


def test_import_object_identifier(testpath):
    """Test digital object identifier argument"""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 '--identifier', 'local', 'test-id', input_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert root.xpath('//premis:objectIdentifierType',
                      namespaces=NAMESPACES)[0].text == 'local'
    assert root.xpath('//premis:objectIdentifierValue',
                      namespaces=NAMESPACES)[0].text == 'test-id'

    assert result.exit_code == 0


def test_import_object_format_registry(testpath):
    """Test digital object format registry argument"""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 '--format_registry', 'local', 'test-key', input_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert root.xpath('//premis:formatRegistryName',
                      namespaces=NAMESPACES)[0].text == 'local'
    assert root.xpath('//premis:formatRegistryKey',
                      namespaces=NAMESPACES)[0].text == 'test-key'

    assert result.exit_code == 0


def test_import_object_utf8(testpath):
    """Test importing works for file that:

    * is a utf-8 encoded text file
    * has utf-8 encoded filename
    * is in utf-8 encoded directory

    import_object.main should create TechMD-file with utf8-encoded filename.
    """

    # Create directory that contains one file
    utf8_directory = os.path.join(testpath, 'directory Ä')
    os.mkdir(utf8_directory)
    utf8_file = os.path.join(utf8_directory, 'testfile Ö')
    with open(utf8_file, 'w') as file_:
        file_.write('Voi änkeröinen.')

    # Run function
    arguments = ['--workspace', testpath, '--skip_wellformed_check', utf8_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)
    assert result.exit_code == 0

    # Check output
    output = get_amd_file(testpath, utf8_file)
    tree = ET.parse(output)
    root = tree.getroot()
    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1


@pytest.mark.validation
@pytest.mark.parametrize(
    ('input_file', 'expected_mimetype', 'expected_version'), [
        pytest.param('tests/data/test_import.pdf', 'application/pdf', '1.4',
                     id='pdf'),
        pytest.param('tests/data/valid_tiff.tif', 'image/tiff', '6.0',
                     id='tiff'),
        pytest.param('tests/data/valid_jpeg.jpeg', 'image/jpeg',
                     ('1.0', '1.01', '1.02'), id='jpeg'),
        pytest.param('tests/data/text-file.txt', 'text/plain; charset=UTF-8',
                     None, id='text'),
        pytest.param('tests/data/csvfile.csv', 'text/plain; charset=UTF-8',
                     None, id='csv'),
        pytest.param('tests/data/mets_valid_minimal.xml',
                     'text/xml; charset=UTF-8',
                     '1.0', id='xml'),
        pytest.param('tests/data/ODF_Text_Document.odt',
                     'application/vnd.oasis.opendocument.text',
                     '1.1', id='odt'),
        pytest.param('tests/data/MS_Excel_97-2003.xls',
                     'application/vnd.ms-excel',
                     '11.0', id='excel'),
        pytest.param('tests/data/MS_Word_2007-2013_XML.docx',
                     'application/vnd.openxmlformats-officedocument.'
                     'wordprocessingml.document',
                     '15.0', id='word docx'),
        pytest.param('tests/data/audio/valid__wav.wav',
                     'audio/x-wav', None, id='audio wav no version'),
        pytest.param('tests/data/audio/valid_2_bwf.wav',
                     'audio/x-wav', '2', id='audio wav v2'),
    ]
)
def test_import_object_validation_cases(testpath, input_file, expected_mimetype,
                                        expected_version):
    """Test validation wtih import_object.main function when run as terminal
    client.
    """
    arguments = ['--workspace', testpath, input_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    comparison = {
        str: lambda element, expected: element[0] == expected,
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

    assert result.exit_code == 0


def test_import_object_fail():
    """Test that import_object.main raises error if target file does not
    exist
    """
    runner = CliRunner()
    result = runner.invoke(import_object.main, ['tests/data/missing-file'])
    assert result.exception


def iterate_files(path):
    """Iterate through all files inside a directory."""
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            yield os.path.join(root, name)


def test_streams(testpath):
    """Test with streams, the test file contains one video and one audio
       stream.
    """
    input_file = 'tests/data/video/valid__h264_aac.mp4'
    arguments = ['--workspace', testpath, '--skip_wellformed_check',
                 input_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    # Streams
    stream_id = []
    for i in [1, 2]:
        output = get_amd_file(testpath, input_file, str(i))
        tree = ET.parse(output)
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
        assert len(root.xpath('//premis:messageDigest',
                              namespaces=NAMESPACES)) == 0
        assert len(root.xpath('//premis:relationship',
                              namespaces=NAMESPACES)) == 0
        assert root.xpath('//premis:object/@xsi:type',
                          namespaces=NAMESPACES)[0] == 'premis:bitstream'

    # Container
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
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

    assert result.exit_code == 0
