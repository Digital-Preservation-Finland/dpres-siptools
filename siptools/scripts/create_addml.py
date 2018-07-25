"""Command line tool for creating ADDML metadata."""

import os
import argparse
import siptools.utils
import addml


def parse_arguments(arguments):
    """Parse arguments commandline arguments."""
    parser = argparse.ArgumentParser(
        description="THIS SCRIPT IS UNDER DEVELOPMENT AND DOES NOT PRODUCE VALID ADDML. "
                    "Tool for creating ADDML metadata for an CSV file. The "
                    "ADDML metadata is written to <hash>-ADDML-techmd.xml "
                    "METS XML file in the workspace directory. The ADDML "
                    "techMD reference is written to techmd-references.xml. "
                    "If similar ADDML metadata is already found in workspace, "
                    "the file will not be rewritten."
    )
    parser.add_argument('file', type=str,
                        help="CSV file to be described by ADDML metadata")
    parser.add_argument('--workspace', type=str, default='./workspace/',
                        help="Workspace directory for the metadata files.")

    return parser.parse_args(arguments)


def main(arguments=None):
    """Write ADDML metadata for a CSV file."""
    args = parse_arguments(arguments)
    create_addml_techmdfile(args.file, args.workspace)


def create_addml_techmdfile(csv_file, workspace):
    """Creates  ADDML metadata for a CSV file, and writes it into a METS XML
    file in workspace. Adds reference to techMD reference file used in
    compile-structmap script. If similar ADDDML metadata already exists in
    workspace, only the techMD reference to the ADDML metadata is created for
    the CSV file.

    :filename: CSV file path
    :returns: None
    """
    # Create ADDML metadata
    addml_data = create_addml(os.path.join(csv_file))

    # Create METS XML file that contains ADDML metadata
    techmd_id = siptools.utils.create_techmdfile(
        workspace, addml_data, 'OTHER', "8.3", "ADDML"
    )

    # Add reference from image file to techMD
    siptools.utils.add_techmdreference(workspace, techmd_id, csv_file)


def create_addml(csv_file):
    """NOT IMPLEMENTED
    Reads CSV file and creates ADDML metadata.

    :filename: CSV file path
    :returns: ADDML metadata XML element
    """
    #--------------------------------------------------------------------------
    # TODO: implement creation of addml
    #--------------------------------------------------------------------------

    addml_data = addml.addml()

    return addml_data

if __name__ == '__main__':
    main()
