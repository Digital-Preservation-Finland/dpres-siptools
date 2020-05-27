"""Command line tool for creating ADDML metadata."""
from __future__ import unicode_literals

import io
import os
import sys

import six
import click

import addml
import csv
import lxml.etree as ET
from siptools.utils import MdCreator, encode_path

click.disable_unicode_literals_warning = True


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
def main(filename, charset, delim, sep, quot, header, workspace, base_path):
    """Tool for creating ADDML metadata for a CSV file. The
    ADDML metadata is written to <hash>-ADDML-amd.xml
    METS XML file in the workspace directory. The ADDML
    techMD reference is written to md-references.xml.
    If similar ADDML metadata is already found in workspace,
    just the new CSV file name is appended to the existing
    metadata.

    FILENAME: Relative path to the file from current directory or from
              --base_path.
    """
    if not os.path.exists(os.path.join(base_path, filename)):
        raise click.UsageError("File does not exist")

    create_addml(
        filename, charset, delim, sep, quot, header, workspace, base_path
    )
    return 0


def create_addml(filename, charset, delim, sep, quot,
                 header=False, workspace="./workspace/", base_path="."):
    """Create ADDML metadata for a CSV file."""
    filerel = os.path.normpath(filename)
    filepath = os.path.normpath(os.path.join(base_path, filename))

    creator = AddmlCreator(workspace)
    creator.add_addml_md(
        filepath, delim,
        header, charset,
        sep, quot
    )
    creator.write(filerel=filerel)


class AddmlCreator(MdCreator):
    """Subclass of MdCreator, which generates ADDML metadata
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

        header = csv_header(csv_file, delimiter, charset)
        headerstr = delimiter.join(header)
        key = (delimiter, headerstr, charset, record_separator, quoting_char)

        # If similar metadata already exists,
        # only append filename to self.filenames
        if key in self.etrees:
            self.filenames[key].append(csv_file)
            return

        # If similar metadata does not exist, create it
        metadata = create_addml_metadata(
            csv_file, delimiter,
            isheader, charset,
            record_separator, quoting_char
        )

        self.etrees[key] = metadata
        self.filenames[key] = [csv_file]

    def write(self, mdtype="OTHER", mdtypeversion="8.3", othermdtype="ADDML",
              filerel=None, section=None, stdout=False,
              file_metadata_dict=None):
        """ Write all the METS XML files and md-reference file.
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

        # Write md-references
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


def _open_csv_file(file_path, charset):
    """
    Open the file in mode dependent on the python version.

    :file_path: CSV file path
    :charset: Charset of the CSV file
    :returns: handle to the newly-opened file
    :raises: IOError if the file cannot be read
    """
    if six.PY2:
        return io.open(file_path, "rb")
    else:
        return io.open(file_path, "rt", encoding=charset)


def csv_header(csv_file_path, delimiter, charset, isheader=False,
               headername='header'):
    """
    Returns header of CSV file if there is one.
    Otherwise generates a header and returns it

    :csv_file_path: CSV file path
    :delimiter: Field delimiter in CSV
    :charset: Character encoding of CSV file
    :isheader: True id file has a header, False otherwise
    :headername: Default header name if file does not have header
    :returns: Header list of CSV columns
    """
    csv_file = _open_csv_file(csv_file_path, charset)
    csv.register_dialect(
        "new_dialect",
        # 'delimiter' accepts only byte strings on Python 2 and
        # only Unicode strings on Python 3
        delimiter=str(delimiter)
    )

    first_row = next(csv.reader(csv_file, dialect="new_dialect"))
    if six.PY2:
        header = [item.decode(charset) for item in first_row]
    else:
        header = first_row
    csv_file.close()

    if not isheader:
        header_count = len(header)
        header = []
        for i in range(header_count):
            header.append("{}{}".format(headername, i + 1))

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
    with io.open(fname, 'rt') as f_in:
        lines = f_in.readlines()

    # Overwrite the file appending line_content
    with io.open(fname, 'wt') as f_out:

        for line in lines:
            f_out.write(line)

            if line.strip() == xml_elem:
                indent = len(line) - len(line.lstrip()) + 2

                for new_line in append:
                    f_out.write(" " * indent + new_line)


def create_addml_metadata(
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

    headers = csv_header(
        csv_file, delimiter, charset, isheader
    )

    description = ET.Element(addml.addml_ns('description'))
    reference = ET.Element(addml.addml_ns('reference'))

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
