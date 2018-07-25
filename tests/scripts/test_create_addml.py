"""Tests for ``siptools.scripts.create_addml`` module"""
import os.path
import siptools.scripts.create_addml as create_addml


def test_create_addml():
    """Test that ``create_addml`` returns valid addml."""
    # TODO: This test only checks element namespaces and schema. Also element
    # content shoudl be validated.

    addml = create_addml.create_addml('tests/data/simple_csv.csv')

    # Check namespace
    assert addml.nsmap['addml'] == 'http://www.arkivverket.no/standarder/addml'

    # Check schema
    assert addml.get(
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'
    ) == "http://www.arkivverket.no/standarder/addml "\
         "http://schema.arkivverket.no/ADDML/latest/addml.xsd"


def test_create_addml_techmdfile(testpath):
    """
    Test that ``create_addml_techmdfile`` writes addml file and techMD
    reference file.
    """
    create_addml.create_addml_techmdfile('tests/data/simple_csv.csv',
                                         testpath)

    assert os.path.isfile(os.path.join(testpath, 'techmd-references.xml'))
    assert os.path.isfile(os.path.join(
        testpath, 'a9ca3747c974486306adb4ec2691b359-ADDML-techmd.xml'
    ))
