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
    ref = os.path.join(path, 'amd-references.xml')

    root = ET.parse(ref).getroot()
    if stream is None:
        amdref = root.xpath("/amdReferences/amdReference[not(@stream) "
                            "and @file='%s']" % input_file.decode(
                                sys.getfilesystemencoding()))[0]
    else:
        amdref = root.xpath("/amdReferences/amdReference[@stream='%s' "
                            "and @file='%s']" % (stream, input_file.decode(
                                sys.getfilesystemencoding())))[0]
    output = os.path.join(path, amdref.text[1:] +
                          "-PREMIS%3AOBJECT-amd.xml")
    return output


def test_import_object_ok(testpath):
    """Test import_object.main funtion with valid test data."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, '--skip_wellformed_check', input_file]
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
    arguments = ['--workspace', testpath, input_file, '--skip_wellformed_check',
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
    arguments = ['--workspace', testpath, input_file, '--skip_wellformed_check',
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
    #TODO: Missing function docstring. What is the purpose of this test?
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


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
def test_import_object_validate_pdf_ok(testpath):
    """Test PDF validation in import_object.main funciton."""
    input_file = 'tests/data/test_import.pdf'
    arguments = ['--workspace', testpath, 'tests/data/test_import.pdf']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName/text()',
                      namespaces=NAMESPACES)[0] == 'application/pdf'
    assert root.xpath('//premis:formatVersion/text()',
                      namespaces=NAMESPACES)[0] == '1.4'

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


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file', ['tests/data/valid_tiff.tif'])
def test_import_object_validate_tiff_ok(input_file, testpath):
    arguments = ['--workspace', testpath, 'tests/data/valid_tiff.tif']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces=NAMESPACES)) == 1
    assert root.xpath(
        '//premis:formatName/text()',
        namespaces=NAMESPACES)[0] == 'image/tiff'
    assert root.xpath(
        '//premis:formatVersion/text()',
        namespaces=NAMESPACES)[0] == '6.0'

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file', ['tests/data/valid_jpeg.jpeg'])
def test_import_object_validate_jpeg_ok(input_file, testpath):
    arguments = ['--workspace', testpath, 'tests/data/valid_jpeg.jpeg']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces=NAMESPACES)) == 1
    assert root.xpath(
        '//premis:formatName/text()',
        namespaces=NAMESPACES)[0] == 'image/jpeg'
    assert root.xpath(
        '//premis:formatVersion/text()',
        namespaces=NAMESPACES)[0] in ['1.0', '1.01', '1.02']

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file', ['tests/data/text-file.txt'])
def test_import_object_validate_text_ok(input_file, testpath):
    arguments = ['--workspace', testpath, 'tests/data/text-file.txt']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces=NAMESPACES)) == 1
    assert root.xpath(
        '//premis:formatName/text()',
        namespaces=NAMESPACES)[0] == 'text/plain; charset=UTF-8'
    assert len(root.xpath(
        '//premis:formatVersion/text()',
        namespaces=NAMESPACES)) == 0

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file', ['tests/data/csvfile.csv'])
def test_import_object_validate_csv_ok(input_file, testpath):
    arguments = ['--workspace', testpath, 'tests/data/csvfile.csv']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces=NAMESPACES)) == 1
    assert root.xpath(
        '//premis:formatName/text()',
        namespaces=NAMESPACES)[0] == 'text/plain; charset=UTF-8'
    assert len(root.xpath(
        '//premis:formatVersion/text()',
        namespaces=NAMESPACES)) == 0

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file', ['tests/data/mets_valid_minimal.xml'])
def test_import_object_validate_mets_xml_ok(input_file, testpath):
    arguments = ['--workspace', testpath, 'tests/data/mets_valid_minimal.xml']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces=NAMESPACES)) == 1
    assert root.xpath(
        '//premis:formatName/text()',
        namespaces=NAMESPACES)[0] == 'text/xml; charset=UTF-8'
    assert root.xpath(
        '//premis:formatVersion/text()',
        namespaces=NAMESPACES)[0] == '1.0'

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file', ['tests/data/ODF_Text_Document.odt'])
def test_import_object_validate_odt_ok(input_file, testpath):
    arguments = ['--workspace', testpath, 'tests/data/ODF_Text_Document.odt']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath(
        '/mets:mets/mets:amdSec/mets:techMD',
        namespaces=NAMESPACES)) == 1
    assert root.xpath(
        '//premis:formatName/text()',
        namespaces=NAMESPACES)[0] == 'application/vnd.oasis.opendocument.text'
    assert root.xpath(
        '//premis:formatVersion/text()',
        namespaces=NAMESPACES)[0] == '1.1'

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file', ['tests/data/MS_Excel_97-2003.xls'])
def test_import_object_validate_msexcel_ok(input_file, testpath):
    arguments = ['--workspace', testpath, 'tests/data/MS_Excel_97-2003.xls']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName/text()',
                      namespaces=NAMESPACES)[0] == 'application/vnd.ms-excel'
    assert root.xpath('//premis:formatVersion/text()',
                      namespaces=NAMESPACES)[0] == '11.0'

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file',
                         ['tests/data/MS_Word_2007-2013_XML.docx'])
def test_import_object_validate_msword_ok(input_file, testpath):
    arguments = ['--workspace', testpath,
                 'tests/data/MS_Word_2007-2013_XML.docx']
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)

    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName/text()',
                      namespaces=NAMESPACES)[0] == \
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.'
         'document')
    assert root.xpath('//premis:formatVersion/text()',
                      namespaces=NAMESPACES)[0] == '15.0'

    assert result.exit_code == 0


@pytest.mark.skipif('file-scraper-full' not in sys.modules,
                    reason='Requires full file scarper')
@pytest.mark.parametrize('input_file, version',
                         [('tests/data/audio/valid_2_bwf.wav', '2'),
                          ('tests/data/audio/valid__wav.wav', '')])
def test_import_object_validate_wav_ok(input_file, version, testpath):
    arguments = ['--workspace', testpath, input_file]
    runner = CliRunner()
    result = runner.invoke(import_object.main, arguments)
    output = get_amd_file(testpath, input_file)
    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName/text()',
                      namespaces=NAMESPACES)[0] == 'audio/x-wav'
    if version == '':
        assert len(root.xpath('//premis:formatVersion/text()',
                              namespaces=NAMESPACES)) == 0
    else:
        assert root.xpath('//premis:formatVersion/text()',
                          namespaces=NAMESPACES)[0] == '2'

    assert result.exit_code == 0


def test_import_object_fail():
    """Test that import_object.main raises error if target file does not
    exist
    """
    input_file = 'tests/data/missing-file'
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
    arguments = ['--workspace', testpath, '--skip_wellformed_check', input_file]
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
