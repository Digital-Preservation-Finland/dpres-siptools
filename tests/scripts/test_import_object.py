import os.path
from urllib import quote_plus
from tempfile import mkdtemp
import xml.etree.ElementTree as ET

from siptools.scripts import import_object

import pytest
import scandir


@pytest.mark.parametrize('input_file', ['tests/data/text-file.txt'])
def test_import_object_ok(input_file):

    output = mkdtemp()
    arguments = ['--output', output, input_file]
    return_code = import_object.main(arguments)

    output = os.path.join(output,
                          quote_plus(os.path.splitext(input_file)[0]) +
                          '-techmd.xml')

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.findall('{http://www.loc.gov/METS/}techMD')) == 1
    assert return_code == 0

def test_import_object_TPAS20_ok():

    output = os.path.abspath('./workspace') 
    do = os.path.abspath(os.path.join(os.curdir,
                'tests/data/TPAS-20'))
    test_file = ""
    for element in iterate_files(do):
        arguments = ['--output', output, os.path.relpath(element,os.curdir)]
        return_code = import_object.main(arguments)
        test_file = os.path.relpath(element, os.curdir)

    output = os.path.join(output,
                          quote_plus(os.path.splitext(test_file)[0]) +
                          '-techmd.xml')

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.findall('{http://www.loc.gov/METS/}techMD')) == 1
    assert return_code == 0


def iterate_files(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
             yield os.path.join(root, name)


@pytest.mark.parametrize('input_file', ['tests/data/missing-file'])
def test_import_object_fail(input_file):
    with pytest.raises(IOError):
        arguments = [input_file, input_file]
        import_object.main(arguments)
