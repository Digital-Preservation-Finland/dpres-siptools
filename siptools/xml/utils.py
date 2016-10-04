"""Utility functions for handling XML data with xml.etree.ElementTree data
structures"""

import xml.etree.ElementTree as ET
import siptools.xml.namespaces


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


def serialize(root_element):
    """Serialize ElementTree structure with PREMIS namespace mapping.

    This modifies the default "ns0:tag" style prefixes to "premis:tag"
    prefixes.

    :element: Starting element to serialize
    :returns: Serialized XML as string

    """

    def register_namespace(prefix, uri):
        """foo"""
        ns_map = getattr(ET, '_namespace_map')
        ns_map[uri] = prefix

    namespaces =  siptools.xml.namespaces.iter_ns()

    for namespace in namespaces:
        register_namespace('mets', METS_NS)

    siptools.xml.xmlutil.indent(root_element)

    return ET.tostring(root_element)


