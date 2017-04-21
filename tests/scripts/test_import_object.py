import os.path
from urllib import quote_plus
import lxml.etree as ET
import pytest
import scandir
import datetime
from siptools.scripts import import_object
from siptools.utils import encode_path
from siptools.xml.namespaces import NAMESPACES


@pytest.mark.parametrize('input_file', ['tests/data/structured/Documentation '
    'files/readme.txt'])
def test_import_object_ok(input_file, testpath):

    arguments = ['--workspace', testpath, input_file]
    return_code = import_object.main(arguments)

    output = os.path.join(testpath, encode_path(input_file,
        suffix='-techmd.xml'))

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD', namespaces=NAMESPACES)) == 1

    assert return_code == 0


@pytest.mark.parametrize('input_file', ['tests/data/text-file.txt'])
def test_import_object_skip_inspection_ok(input_file, testpath):

    arguments = ['--workspace', testpath, input_file, '--skip_inspection',
                 '--format_name', 'image/dpx', '--format_version', '1.0',
                 '--digest_algorithm', 'MD5', '--message_digest',
                 '1qw87geiewgwe9',
                 '--date_created', datetime.datetime.utcnow().isoformat()]
    return_code = import_object.main(arguments)

    output = os.path.join(testpath, encode_path(input_file,
        suffix='-techmd.xml'))

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD', namespaces=NAMESPACES)) == 1

    assert return_code == 0


@pytest.mark.parametrize('input_file', ['tests/data/text-file.txt'])
def test_import_object_skip_inspection_nodate_ok(input_file, testpath):

    arguments = ['--workspace', testpath, input_file, '--skip_inspection',
                 '--format_name', 'image/dpx', '--format_version', '1.0',
                 '--digest_algorithm', 'MD5', '--message_digest',
                 '1qw87geiewgwe9']
    return_code = import_object.main(arguments)

    output = os.path.join(testpath, encode_path(input_file,
        suffix='-techmd.xml'))

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
         namespaces=NAMESPACES)) == 1
    assert return_code == 0

def test_import_object_structured_ok(testpath):

    workspace = os.path.abspath(testpath)
    do = os.path.abspath(os.path.join(os.curdir,
                                      'tests/data/structured'))
    test_file = ""
    for element in iterate_files(do):
        arguments = ['--workspace', workspace,
                     os.path.relpath(element, os.curdir)]
        return_code = import_object.main(arguments)
        test_file = os.path.relpath(element, os.curdir)
        output = os.path.join(testpath, encode_path(test_file,
                suffix='-techmd.xml'))

        tree = ET.parse(output)
        root = tree.getroot()

        assert len(root.xpath('/mets:mets/mets:amdSec/mets:techMD',
                  namespaces=NAMESPACES)) == 1
        assert return_code == 0


def iterate_files(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            yield os.path.join(root, name)


@pytest.mark.parametrize('input_file', ['tests/data/missing-file'])
def test_import_object_fail(input_file):
    with pytest.raises(IOError):
        arguments = [input_file]
        import_object.main(arguments)
