"""Utility functions for handling XML data with xml.etree.ElementTree data
structures"""

import xml.etree.ElementTree as ET


def indent(elem, level=0):
    """Add indentation for the ElementTree elements

    Modifies the given element tree inplace.

    :elem: Starting element

    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def read_xml(input_file):
    """Read PREMIS data dictionary from XML file and return it as ElementTree
    DOM.

    TODO: Note this has Luigi dependency. Move these to better Luigi-specific
    class as preservation.premis and preservation.xml modules should be as
    generic as possible.

    :input_file: Luigi LocalTarget with open() method
    :returns: PREMIS Data Dictionary as ElementTree DOM

    """
    with input_file.open() as infile:
        return ET.parse(infile.name)


def write_xml(output_file, root_element):
    """write PREMIS data dictionary from ElementTree DOM to XML file.

    TODO: Note this has dependency to preservation.premis and luigi. Move this
    function to some Luigi/premis spesific module.


    Modules preservation.premis and preservation.xml modules should be as
    generic as possible.

    :input_file: Luigi LocalTarget with open() method
    :returns: PREMIS Data Dictionary as ElementTree DOM

    """

    with output_file.open('w') as outfile:
        outfile.write(serialize(root_element))
