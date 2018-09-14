"""Command line tool for creating ADDML metadata."""

import os
import argparse
import hashlib
import lxml.etree as ET

import addml
import xml_helpers
import siptools.utils


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""

    parser = argparse.ArgumentParser(
        description="Tool for creating ADDML metadata for a CSV file. The "
                    "ADDML metadata is written to <hash>-ADDML-techmd.xml "
                    "METS XML file in the workspace directory. The ADDML "
                    "techMD reference is written to techmd-references.xml. "
                    "If similar ADDML metadata is already found in workspace, "
                    "just the new CSV file name is appended to the existing "
                    "metadata."
    )

    parser.add_argument('--path', type=str, required=True,
                        help="Path to the dir of CSV file")
    parser.add_argument('--fname', type=str, required=True,
                        help="CSV file name")
    parser.add_argument('--delim', type=str, required=True,
                        help="Delimiter used in the CSV file")
    parser.add_argument('--header', dest='header', action='store_true',
                        help="CSV file has a header")
    parser.add_argument('--no-header', dest='header', action='store_false',
                        help="CSV file has not got a header")
    parser.set_defaults(header=False)
    parser.add_argument('--charset', type=str, required=True,
                        help="Charset used in the CSV file")
    parser.add_argument('--sep', type=str, required=True,
                        help="Record separator used in the CSV file")
    parser.add_argument('--quot', type=str, required=True,
                        help="Quoting character used in the CSV file")
    parser.add_argument('--work', type=str, default='./workspace/',
                        help="Workspace directory for the metadata files.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write ADDML metadata for a CSV file."""
    args = parse_arguments(arguments)
    create_addml_techmdfile(
        args.path, args.fname, args.delim, args.header,
        args.charset, args.sep, args.quot, args.work)


def create_addml_techmdfile(
        sip_creation_path, filename, delimiter,
        isheader, charset, record_separator,
        quoting_char, workspace):

    """Creates  ADDML metadata for a CSV file, and writes it into a METS XML
    file in workspace. Adds reference to techMD reference file used in
    compile-structmap script. If similar ADDML metadata already exists in
    workspace, only the techMD reference to the ADDML metadata is created for
    the CSV file.

    :sip_creation_path: Path to the dir of CSV file
    :filename: CSV file name
    :delimiter: Delimiter used in the CSV file
    :isheader: True if CSV has a header else False
    :charset: Charset used in the CSV file
    :record_separator: Char used for separating CSV file fields
    :quoting_char: Quotation char used in the CSV file
    :workspace: Output directory

    :returns: None
    """

    csv_file = os.path.join(sip_creation_path, filename)

    # Create ADDML metadata
    addml_data = create_addml(
        sip_creation_path, filename, delimiter,
        isheader, charset, record_separator, quoting_char)

    digest = hashlib.md5(xml_helpers.utils.serialize(addml_data)).hexdigest()
    techmd_fname = siptools.utils.encode_path("%s-ADDML-techmd.xml" % digest)
    techmd_fname = os.path.join(workspace, techmd_fname)

    # Create METS XML file that contains ADDML metadata
    techmd_id = siptools.utils.create_techmdfile(
        workspace, addml_data, 'OTHER', "8.3", "ADDML")

    # Append flatFile element to the created METS XML file
    new_line = flat_file_str(filename, "ref_001")
    append_line(techmd_fname, "<addml:flatFiles>", new_line)

    # Add reference from image file to techMD
    siptools.utils.add_techmdreference(workspace, techmd_id, csv_file)


def append_line(fname, xml_elem, new_line):
    """ Appends a new line to file fname below
    line with xml_elem.

    :fname: File name
    :xml_elem: Element below which to append
    :new_line: Content of the appended line

    :returns: None
    """

    # Read all the lines into memory
    with open(fname, 'r') as f_in:
        lines = f_in.readlines()

    # Overwrite the file appending line_content
    with open(fname, 'w') as f_out:

        for line in lines:
            f_out.write(line)

            if line.strip() == xml_elem:
                indent = len(line) - len(line.lstrip()) + 2
                f_out.write(" " * indent + new_line)


def flat_file_str(fname, def_ref):
    """Returns addml:flatFile xml element as a string,
    which can be appended to the xml file.

    :fname: Name attribute of the flatFile element
    :def_ref: definitionReference of the flatFile element
    """

    flat_file = '<addml:flatFile name="%s" definitionReference="%s"/>\n' % (
        fname, def_ref)

    return flat_file


def csv_header(csv_file_path, delimiter, isheader=False, headername='header'):
    """Returns header of CSV file if there is one.
    Otherwise generates a header and returns it
    """

    with open(csv_file_path, 'r') as csv_file:
        header = csv_file.readline()

        if not isheader:
            header_count = header.count(delimiter)
            header = headername + "1"

        for i in range(header_count):
            header += delimiter + headername + str(i + 2)

    return header


def create_addml(
        sip_creation_path, filename,
        delimiter, isheader, charset,
        record_separator, quoting_char):

    """Creates ADDML metadata for a csv file
    without flatFile element, which is added
    by create_addml_techmdfile() function.
    This is done to avoid getting different
    hashes for the same metadata, but different
    filename.

    :sip_creation_path: Path to the dir of CSV file
    :filename: CSV file name
    :delimiter: Delimiter used in the CSV file
    :isheader: True if CSV has a header else False
    :charset: Charset used in the CSV file
    :record_separator: Char used for separating CSV file fields
    :quoting_char: Quotation char used in the CSV file

    :returns: ADDML metadata XML element
    """

    header = csv_header(
        os.path.join(sip_creation_path, filename), delimiter, isheader)

    description = ET.Element(addml.addml_ns('description'))
    reference = ET.Element(addml.addml_ns('reference'))

    headers = header.split(delimiter)
    field_definitions = addml.wrapper_elems('fieldDefinitions')

    for col in headers:
        elems = addml.definition_elems('fieldDefinition', col, 'String')
        field_definitions.append(elems)

    record_definition = addml.definition_elems(
        'recordDefinition', 'record',
        'rdef001', [field_definitions])
    record_definitions = addml.wrapper_elems(
        'recordDefinitions', [record_definition])

    flat_file_definition = addml.definition_elems(
        'flatFileDefinition', 'ref001',
        'rec001', [record_definitions])
    flat_file_definitions = addml.wrapper_elems(
        'flatFileDefinitions', [flat_file_definition])

    data_type = addml.addml_basic_elem('dataType', 'string')
    field_type = addml.definition_elems(
        'fieldType', 'String', child_elements=[data_type])
    field_types = addml.wrapper_elems('fieldTypes', [field_type])

    trimmed = ET.Element(addml.addml_ns('trimmed'))
    record_type = addml.definition_elems(
        'recordType', 'rdef001', child_elements=[trimmed])
    record_types = addml.wrapper_elems('recordTypes', [record_type])

    delim_file_format = addml.delimfileformat(
        record_separator, delimiter, quoting_char)
    charset_elem = addml.addml_basic_elem('charset', charset)
    flat_file_type = addml.definition_elems(
        'flatFileType', 'rec001',
        child_elements=[charset_elem, delim_file_format])
    flat_file_types = addml.wrapper_elems('flatFileTypes', [flat_file_type])

    structure_types = addml.wrapper_elems(
        'structureTypes', [flat_file_types, record_types, field_types])
    flatfiles = addml.wrapper_elems(
        'flatFiles', [flat_file_definitions, structure_types])

    addml_root = addml.addml([description, reference, flatfiles])

    return addml_root


if __name__ == '__main__':
    main()
