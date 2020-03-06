"""Command line tool for creating ADDML metadata."""
from __future__ import unicode_literals

import io
import os
import sys

import csv
import six
import click

import addml
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
@click.option('--header', 'isheader', is_flag=True,
              help="Use if the CSV file contains a header")
@click.option('--charset', type=str, required=True,
              metavar='<CHARSET>',
              help="Character encoding used in the CSV file")
@click.option('--delim', 'delimiter', type=str, required=True,
              metavar='<DELIMITER CHAR>',
              help="Delimiter character used in the CSV file")
@click.option('--sep', 'record_separator', type=str, required=True,
              metavar='<SEPARATOR CHAR>',
              help="Record separating character used in the CSV file")
@click.option('--quot', 'quoting_char', type=str, required=True,
              metavar='<QUOTING CHAR>',
              help="Quoting character used in the CSV file")
#pylint: disable=too-many-arguments
def main(filename, charset, delimiter, record_separator, quoting_char,
         isheader, workspace, base_path):
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
    create_addml(
        filename=filename, charset=charset, delimiter=delimiter,
        record_separator=record_separator, quoting_char=quoting_char,
        isheader=isheader, workspace=workspace, base_path=base_path
    )
    return 0


def create_addml(**kwargs):
    """
    Create ADDML metadata for a CSV file.

    :kwargs: Given arguments
    """
    _initialize_args(kwargs)
    filerel = os.path.normpath(kwargs["filename"])
    filepath = os.path.normpath(os.path.join(kwargs["base_path"],
                                             kwargs["filename"]))
    kwargs["csv_file"] = filepath
    creator = AddmlCreator(kwargs["workspace"], filerel)
    creator.add_addml_md(**kwargs)
    creator.write()


def _initialize_args(kwargs):
    """
    Initalize given arguments to new dict by adding the missing keys with
    initial values.

    :kwargs: Arguments as dict.
    :returns: Initialized dict.
    """
    kwargs["workspace"] = "./workspace" if not "workspace" in kwargs \
        else kwargs["workspace"]
    kwargs["base_path"] = "." if not "base_path" in kwargs else \
        kwargs["base_path"]
    kwargs["isheader"] = False if not "isheader" in kwargs else \
        kwargs["isheader"]


class AddmlCreator(MdCreator):
    """Subclass of MdCreator, which generates ADDML metadata
    for CSV files.
    """

    def __init__(self, workspace, filerel=None):
        """
        Initialize ADDML creator.

        :workspace: Output path
        """
        super(AddmlCreator, self).__init__(workspace)
        self.etrees = {}
        self.filenames = {}
        self.filerel = filerel

    def add_addml_md(self, **kwargs):

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
        _initialize_args(kwargs)
        header = csv_header(**kwargs)
        headerstr = kwargs["delimiter"].join(header)
        key = (kwargs["delimiter"], headerstr, kwargs["charset"],
               kwargs["record_separator"], kwargs["quoting_char"])

        # If similar metadata already exists,
        # only append filename to self.filenames
        if key in self.etrees:
            self.filenames[key].append(kwargs["csv_file"])
            return

        # If similar metadata does not exist, create it
        metadata = create_addml_metadata(**kwargs)

        self.etrees[key] = metadata
        self.filenames[key] = [kwargs["csv_file"]]

    #pylint: disable=too-many-arguments
    def write(self, mdtype="OTHER", mdtypeversion="8.3", othermdtype="ADDML",
              section=None, stdout=False, file_metadata_dict=None):
        """
        Write all the METS XML files and md-reference file.
        Base class write is overwritten to handle the references
        correctly and add flatFile fields to METS XML files.
        """

        for key in self.etrees:
            metadata = self.etrees[key]
            filenames = self.filenames[key]

            # Create METS XML file
            amd_id, amd_fname = \
                self.write_md(metadata, mdtype, mdtypeversion, othermdtype)

            # Add all the files to references
            for filename in filenames:
                self.add_reference(
                    amd_id, self.filerel if self.filerel else filename
                )

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
    """
    Return addml:flatFile xml element as a string,
    which can be appended to the xml file.

    :fname: Name attribute of the flatFile element
    :def_ref: definitionReference of the flatFile element
    :returns: flatFile element string
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


def csv_header(headername='header', **kwargs):
    """
    Returns header of CSV file if there is one.
    Otherwise generates a header and returns it

    :headername: Default header name if file does not have header
    :csv_file: CSV file path
    :delimiter: Field delimiter in CSV
    :charset: Character encoding of CSV file
    :isheader: True id file has a header, False otherwise
    :returns: Header list of CSV columns
    """
    _initialize_args(kwargs)
    csv_file = _open_csv_file(kwargs["csv_file"], kwargs["charset"])
    csv.register_dialect(
        "new_dialect",
        # 'delimiter' accepts only byte strings on Python 2 and
        # only Unicode strings on Python 3
        delimiter=str(kwargs["delimiter"])
    )

    first_row = next(csv.reader(csv_file, dialect="new_dialect"))
    if six.PY2:
        header = [item.decode(kwargs["charset"]) for item in first_row]
    else:
        header = first_row
    csv_file.close()

    if not kwargs["isheader"]:
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


#pylint: disable=too-many-locals
def create_addml_metadata(**kwargs):
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
    :flatfile_name: flatFile elements name attribute
    :delimiter: Delimiter used in the CSV file
    :isheader: True if CSV has a header else False
    :charset: Charset used in the CSV file
    :record_separator: Char used for separating CSV file fields
    :quoting_char: Quotation char used in the CSV file
    :returns: ADDML metadata XML element
    """
    _initialize_args(kwargs)
    kwargs["flatfile_name"] = None if "flatfile_name" not in kwargs else \
        kwargs["flatfile_name"]
    headers = csv_header(**kwargs)

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
        kwargs["record_separator"], kwargs["delimiter"],
        kwargs["quoting_char"]
    )
    charset_elem = addml.addml_basic_elem('charset', kwargs["charset"])
    flat_file_type = addml.definition_elems(
        'flatFileType', 'rec001',
        child_elements=[charset_elem, delim_file_format]
    )
    flat_file_types = addml.wrapper_elems('flatFileTypes', [flat_file_type])

    structure_types = addml.wrapper_elems(
        'structureTypes', [flat_file_types, record_types, field_types]
    )

    if kwargs["flatfile_name"]:
        flatfile = addml.definition_elems(
            'flatFile',
            encode_path(kwargs["flatfile_name"]),
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
