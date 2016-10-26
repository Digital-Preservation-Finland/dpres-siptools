import os.path
from urllib import quote_plus
from tempfile import mkdtemp
import xml.etree.ElementTree as ET

from siptools.scripts import import_object

import pytest


@pytest.mark.parametrize('input_file', ['tests/data/text-file.txt'])
def test_import_object_ok(input_file):

    output = mkdtemp()
    arguments = ['--output', output, input_file]
    return_code = import_object.main(arguments)

    output = os.path.join(output,
                          quote_plus(os.path.splitext(input_file)[0]) + '-dmdsec.xml')

    tree = ET.parse(output)
    root = tree.getroot()

    assert len(root.findall('{http://www.loc.gov/METS/}techMD')) == 1
    assert return_code == 0


@pytest.mark.parametrize('input_file', ['tests/data/missing-file'])
def test_import_object_fail(input_file):
    with pytest.raises(IOError):
        arguments = [input_file, input_file]
        import_object.main(arguments)
