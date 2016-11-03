import pytest
from siptools.scripts import compile_structmap

def test_compile_structmap_ok():
    return_code = compile_structmap.main(['tests/data/TPAS-20', '--workspace',
        './workspace'])

