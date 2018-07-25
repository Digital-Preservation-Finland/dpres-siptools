# encoding: utf-8
"""Unit tests for ``siptools.scripts.import_object`` module"""
import os.path
import datetime
import lxml.etree as ET
import pytest
from siptools.scripts import import_object
from siptools.utils import encode_path
from siptools.xml.mets import NAMESPACES


def test_import_object_ok(testpath):
    """Test import_object.main funtion with valid test data."""
    input_file = 'tests/data/structured/Documentation files/readme.txt'
    arguments = ['--workspace', testpath, input_file]
    return_code = import_object.main(arguments)

    output = os.path.join(testpath, encode_path(input_file.decode('utf-8'),
                                                suffix='-premis-techmd.xml'))

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1

    assert return_code == 0


def test_import_object_skip_inspection_ok(testpath):
    """Test import_object.main function --skip-inspection argument."""
    input_file = 'tests/data/text-file.txt'
    arguments = ['--workspace', testpath, input_file, '--skip_inspection',
                 '--format_name', 'image/dpx', '--format_version', '1.0',
                 '--digest_algorithm', 'MD5', '--message_digest',
                 '1qw87geiewgwe9',
                 '--date_created', datetime.datetime.utcnow().isoformat()]
    return_code = import_object.main(arguments)

    output = os.path.join(testpath, encode_path(input_file,
                                                suffix='-premis-techmd.xml'))

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1

    assert return_code == 0


def test_import_object_skip_inspection_nodate_ok(testpath):
    """Test import_object.main function without --date_created argument."""
    input_file = 'tests/data/text-file.txt'
    arguments = ['--workspace', testpath, input_file, '--skip_inspection',
                 '--format_name', 'image/dpx', '--format_version', '1.0',
                 '--digest_algorithm', 'MD5', '--message_digest',
                 '1qw87geiewgwe9']
    return_code = import_object.main(arguments)

    output = os.path.join(testpath, encode_path(input_file,
                                                suffix='-premis-techmd.xml'))

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert return_code == 0


def test_import_object_structured_ok(testpath):
    #TODO: Missing function docstring. What is the purpose of this test?
    workspace = os.path.abspath(testpath)
    test_data = os.path.abspath(os.path.join(os.curdir,
                                             'tests/data/structured'))
    test_file = ""
    for element in iterate_files(test_data):
        arguments = ['--workspace', workspace,
                     os.path.relpath(element, os.curdir)]
        return_code = import_object.main(arguments)
        test_file = os.path.relpath(element, os.curdir)
        output = os.path.join(testpath, encode_path(test_file,
                                                    suffix='-premis-techmd.xml'))

        tree = ET.parse(output)
        root = tree.getroot()

        assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                              namespaces=NAMESPACES)) == 1
        assert return_code == 0


def test_import_object_validate_pdf_ok(testpath):
    """Test PDF validation in import_object.main funciton."""
    input_file = 'tests/data/test_import.pdf'
    arguments = ['--workspace', testpath, 'tests/data/test_import.pdf']
    return_code = import_object.main(arguments)

    output = os.path.join(testpath, encode_path(input_file,
                                                suffix='-premis-techmd.xml'))

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1
    assert root.xpath('//premis:formatName/text()',
                      namespaces=NAMESPACES)[0] == 'application/pdf'
    assert root.xpath('//premis:formatVersion/text()',
                      namespaces=NAMESPACES)[0] == '1.4'

    assert return_code == 0


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
    assert import_object.main(['--workspace', testpath, utf8_file]) == 0

    # Check output
    output = os.path.join(testpath, encode_path(utf8_file.decode('utf-8'),
                                                suffix='-premis-techmd.xml'))
    tree = ET.parse(output)
    root = tree.getroot()
    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                          namespaces=NAMESPACES)) == 1


def test_import_object_fail():
    """Test that import_object.main raises error if target file does not
    exist
    """
    input_file = 'tests/data/missing-file'
    with pytest.raises(IOError):
        arguments = [input_file]
        import_object.main(arguments)


def iterate_files(path):
    """Iterate through all files inside a directory."""
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            yield os.path.join(root, name)
