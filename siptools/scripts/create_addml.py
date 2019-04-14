"""Command line tool for creating ADDML metadata."""
import sys
import os
import click
import lxml.etree as ET

import addml
from siptools.utils import AmdCreator, encode_path


@click.command()
@click.argument('filename', type=str)
@click.option('--workspace', type=click.Path(exists=True),
              default='./workspace/',
              metavar='<WORKSPACE PATH>',
              help="Workspace directory for the metadata files. "
                   "Defaults to ./workspace/")
@click.option('--base_path', type=click.Path(exists=True), default='.',
              metavar='<BASE PATH>',
              help="Source base path of digital objects. If used, "
                   "give path to the CSV file in relation to this "
                   "base path.")
@click.option('--header', is_flag=True,
              help="Use if the CSV file contains a header")
@click.option('--charset', type=str, required=True,
              metavar='<CHARSET>',
              help="Character encoding used in the CSV file")
@click.option('--delim', type=str, required=True,
              metavar='<DELIMITER CHAR>',
              help="Delimiter character used in the CSV file")
@click.option('--sep', type=str, required=True,
              metavar='<SEPARATOR CHAR>',
              help="Record separating character used in the CSV file")
@click.option('--quot', type=str, required=True,
              metavar='<QUOTING CHAR>',
              help="Quoting character used in the CSV file")
def main(filename, header, charset, delim, sep, quot, workspace, base_path):
    """
    Tool for creating ADDML metadata for a CSV file. The
    ADDML metadata is written to <hash>-ADDML-amd.xml
    METS XML file in the workspace directory. The ADDML
    techMD reference is written to amd-references.xml.
    If similar ADDML metadata is already found in workspace,
    just the new CSV file name is appended to the existing
    metadata.

    FILENAME: Relative path to the file from current directory or from
              --base_path.
    """

    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = AddmlCreator(workspace)
    creator.add_addml_md(
        filepath, delim,
        header, charset,
        sep, quot
    )
    creator.write(filerel=filerel)

    return 0


class AddmlCreator(AmdCreator):
    """Subclass of AmdCreator, which generates ADDML metadata
    for CSV files.
    """

    def __init__(self, workspace):
        """
        :workspace: Output path
        :etrees: Dict of the generated root elements
        :filenames: Dict of the filenames corresponding to root elements
        """
        super(AddmlCreator, self).__init__(workspace)
        self.etrees = {}
        self.filenames = {}

    def add_addml_md(self, csv_file, delimiter, isheader,
                     charset, record_separator, quoting_char):

        """Append metadata to etrees and filenames dicts.
        All the metadata given as the parameters uniquely defines
        the XML file to be written later. A tuple of the
        metadata is thus used as the dict key, which makes it possible
        to efficiently check if corresponding metadata element has
        already been created. This means that the write_md()
        function needs to be called only once for each distinct metadata types.

        :csv_file: CSV file name
        :delimiter: Delimiter used in the CSV file
        :isheader: True if CSV has a header else False
        :charset: Charset used in the CSV file
        :record_separator: Char used for separating CSV file fields
        :quoting_char: Quotation char used in the CSV file

        :returns: None
        """

        header = csv_header(csv_file, delimiter)

        key = (delimiter, header, charset, record_separator, quoting_char)

        # If similar metadata already exists,
        # only append filename to self.filenames
        if key in self.etrees:
            self.filenames[key].append(csv_file)
            return

        # If similar metadata does not exist, create it
        metadata = create_addml(
            csv_file, delimiter,
            isheader, charset,
            record_separator, quoting_char
        )

        self.etrees[key] = metadata
        self.filenames[key] = [csv_file]

    def write(self, mdtype="OTHER", mdtypeversion="8.3", othermdtype="ADDML",
              filerel=None, section=None, stdout=False,
              file_metadata_dict=None):
        """ Write all the METS XML files and amd-reference file.
        Base class write is overwritten to handle the references
        correctly and add flatFile fields to METS XML files.

        :returns: None
        """

        for key in self.etrees:
            metadata = self.etrees[key]
            filenames = self.filenames[key]

            # Create METS XML file
            amd_id, amd_fname = \
                self.write_md(metadata, mdtype, mdtypeversion, othermdtype)

            # Add all the files to references
            for filename in filenames:
                self.add_reference(amd_id, filerel if filerel else filename)

            # Append all the flatFile elements to the METS XML file
            append = [
                flat_file_str(encode_path(filename), "ref001")
                for filename in filenames
            ]
            append_lines(amd_fname, "<addml:flatFiles>", append)

        # Write amd-references
        self.write_references()

        # Clear filenames and etrees
        self.__init__(self.workspace)


def flat_file_str(fname, def_ref):
    """Returns addml:flatFile xml element as a string,
    which can be appended to the xml file.

    :fname: Name attribute of the flatFile element
    :def_ref: definitionReference of the flatFile element
    """

    flat_file = '<addml:flatFile name="%s" definitionReference="%s"/>\n' % (
        fname, def_ref
    )

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


def append_lines(fname, xml_elem, append):
    """Append all the lines in list append to file fname below
    the line with xml_elem.

    :fname: File name
    :xml_elem: Element below which to append
    :append: List of lines to append

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

                for new_line in append:
                    f_out.write(" " * indent + new_line)


def create_addml(
        csv_file, delimiter, isheader, charset,
        record_separator, quoting_char, flatfile_name=None
):

    """Creates ADDML metadata for a CSV file by default
    without flatFile element, which is added by the
    write() method of the AddmlCreator class. This is done to
    avoid getting different hashes for the same metadata,
    but different filename.

    flatFile elements is added if optional parameter
    flatfile_name is provided. csv_file parameter is not
    used as the flatFile element name attribute since that will
    differ from the original filepath e.g. when it is a tmpfile
    downloaded from IDA.

    :csv_file: Path to the CSV file
    :delimiter: Delimiter used in the CSV file
    :isheader: True if CSV has a header else False
    :charset: Charset used in the CSV file
    :record_separator: Char used for separating CSV file fields
    :quoting_char: Quotation char used in the CSV file
    :flatfile_name: flatFile elements name attribute

    :returns: ADDML metadata XML element
    """

    header = csv_header(
        csv_file, delimiter, isheader
    )

    description = ET.Element(addml.addml_ns('description'))
    reference = ET.Element(addml.addml_ns('reference'))

    headers = header.split(delimiter)
    field_definitions = addml.wrapper_elems('fieldDefinitions')

    for col in headers:
        elems = addml.definition_elems('fieldDefinition', col, 'String')
        field_definitions.append(elems)

    record_definition = addml.definition_elems(
        'recordDefinition', 'record',
        'rdef001', [field_definitions]
    )
    record_definitions = addml.wrapper_elems(
        'recordDefinitions', [record_definition]
    )

    flat_file_definition = addml.definition_elems(
        'flatFileDefinition', 'ref001',
        'rec001', [record_definitions]
    )
    flat_file_definitions = addml.wrapper_elems(
        'flatFileDefinitions', [flat_file_definition]
    )

    data_type = addml.addml_basic_elem('dataType', 'string')
    field_type = addml.definition_elems(
        'fieldType', 'String', child_elements=[data_type]
    )
    field_types = addml.wrapper_elems('fieldTypes', [field_type])

    trimmed = ET.Element(addml.addml_ns('trimmed'))
    record_type = addml.definition_elems(
        'recordType', 'rdef001', child_elements=[trimmed]
    )
    record_types = addml.wrapper_elems('recordTypes', [record_type])

    delim_file_format = addml.delimfileformat(
        record_separator, delimiter, quoting_char)
    charset_elem = addml.addml_basic_elem('charset', charset)
    flat_file_type = addml.definition_elems(
        'flatFileType', 'rec001',
        child_elements=[charset_elem, delim_file_format]
    )
    flat_file_types = addml.wrapper_elems('flatFileTypes', [flat_file_type])

    structure_types = addml.wrapper_elems(
        'structureTypes', [flat_file_types, record_types, field_types]
    )

    if flatfile_name:
        flatfile = addml.definition_elems(
            'flatFile',
            encode_path(flatfile_name),
            'ref001'
        )
        elems = [flatfile, flat_file_definitions, structure_types]
    else:
        elems = [flat_file_definitions, structure_types]

    flatfiles = addml.wrapper_elems('flatFiles', elems)
    addml_root = addml.addml([description, reference, flatfiles])

    return addml_root


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
