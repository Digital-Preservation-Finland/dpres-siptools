Pre-Ingest Tool
===============

This tool is intended to be used for generating an OAIS SIP for digital preservation.
It produces a METS document (mets.xml) that contains metadata for digital preservation
required by the specifications used in the Finnish national Digital Preservation Services.
The tool contains code for extracting metadata, creating and digitally signing the
METS document.

The aim is to provide digital preservation services for culture and research to ensure
the access and use of materials long in the future. Documentation and specifications
for the digital preservation services can be found in: http://digitalpreservation.fi

The Pre-Ingest Tool currently supports the specification version 1.7.1.

Backwards compatibility
-----------------------

This version of the tool is not backward-compatible with older versions. The
non-compatible differences in the script arguments are following:

    * import-object

        * ``--skip_inspection`` is changed to ``--skip_wellformed_check``.
        * ``--digest_algorithm`` and ``--message_digest`` have been combined to ``--checksum``.
        * ``--format_name`` and ``--format_version`` have been combined to ``--file_format``.
        
    * create-addml

        * ``--no-header`` has been removed as unnecessary.

    * import-description

        * ``--desc_root`` has been changed to ``--remove_root``.

    * compile-structmap

        * ``--dmdsec_struct`` is removed and merged to ``--structmap_type``.
        * ``--type_attr`` is changed to ``--structmap_type``.

Installation
------------

Installation and usage requires Python 2.7.
The software is tested with Python 2.7 with Centos 7.x / RHEL 7.x releases.

Packages openssl-devel, swig and gcc are required in your system to install M2Crypto,
which is used for signing the packages with digital signature.

Get python-virtuelenv software::

    sudo yum install python-virtualenv

Run the following to activate the virtual environment::

    virtualenv venv
    source venv/bin/activate

Install the required software with command::

    pip install --upgrade pip
    pip install -r requirements_github.txt
    pip install .

See the README from file-scraper repository for additional installation requirements:
https://github.com/Digital-Preservation-Finland/file-scraper/blob/master/README.rst

To deactivate the virtual enviroment, run ``deactivate``.
To reactivate it, run the ``source`` command above.

Scripts
-------

import-description
    for adding a descriptive metadata section to a METS document.

premis-event
    for creating digital provenance metadata.

import-object
    for adding technical metadata for digital objects to a METS document.

create-mix
    for creating MIX metadata for image files.

create-addml
    for creating ADDML metadata for csv files.

create-audiomd
    for creating AudioMD metadata for audio streams.

create-videomd
    for creating VideoMD metadata for video streams.

compile-structmap
    for creating the file section and structural map.

compile-mets
    for compiling all previously created metadata files in a METS document.

sign-mets
    for digitally signing the submission information package.

compress
    for wrapping the created submission information package directory to a TAR file.

Usage
-----

In order to build a SIP for digital preservation, use the scripts in the following order.
These scripts produce a digitally signed METS document in the parametrized folder 'workspace'.

For a short description about other optional arguments which are not listed here, see::

    <scriptname> --help

**Import digital objects and create general technical metadata**

You can create technical metadata elements of a METS document from files located in the folder
tests/data/structured followingly::

    import-object 'tests/data/structured' --workspace ./workspace

You may use this script as many times as needed to import all your digital object.

**Create file format specific technical metadata**

If your dataset contains image data, create MIX metadata for each of the image files::

    create-mix path/to/images/image.tif --workspace ./workspace
    
ADDML metadata for a CSV file can be created by running::
    
    create-addml path/to/csv_file.csv --workspace ./workspace --charset 'UTF8' --sep 'CR+LF' --quot '"' --delim ';'

A flag --header should be given if CSV file has headers. --sep flag defines the character used to 
separate records and --delim the character used to separate fields. --quot defines the 
quotation character used.

AudioMD metadata for a audio stream file can be created by running::

    create-audiomd path/to/audio/audio.wav --workspace ./workspace

If a video container file contains audio stream data, the create_audiomd script
above needs to be run for all audio streams in video files.

VideoMD metadata for a video stream file can be created by running::

    create-videomd path/to/video/video.wav --workspace ./workspace

Call the scripts above for each file needed in your data set.

**Create provenance metadata**

An example how to create digital provenance metadata for a METS document.
Values for the parameters --event_outcome and --event_type are predefined lists::

    premis-event creation '2016-10-13T12:30:55' --workspace ./workspace --event_target 'tests/data/structured' --event_detail Testing --event_outcome success --event_outcome_detail 'Outcome detail' --agent_name 'Demo Application' --agent_type software

The argument --event_target is the object (file or directory) where the event applies.
If the argument is not given, the target is the whole dataset. Do not use argument
--event_target for directories, if the structural map is created based on EAD3 structure
with compile_structmap.py. If argument --agent_name is not given, agent metadata is
not created.

You may call this script several times to create multiple provenance metadata sections.

If several digital objects are linked to the same event and agent, run the
script for each object with only the --event_target changed in the parameters.
This will create links to the same event for each digital object.

**Add existing descriptive metadata**

Script appends descriptive metadata into a METS XML wrapper. Metadata must be in a accepted format::

    import-description 'tests/data/import_description/metadata/dc_description.xml' --workspace ./workspace --dmdsec_target 'tests/data/structured' --remove_root

The argument '--remove_root' removes the root element from the given descriptive metadata.
This may be needed, if the metadata is given in a container element belonging to another metadata format.
If the argument is not given, the descriptive metadata is fully included. The argument
'--dmdsec_target  <target>' is the directory where the descriptive metadata applies.
If the argument is not given, the target is the whole dataset. Do not use argument --dmdsec_target,
if the structural map is created based on EAD3 structure with compile_structmap.py.

Currently importing multiple descriptive metadata files for the same --dmdsec_target is not supported.
However, it is possible to add multiple descriptive metadata files, when each of these have different targets.

**Compile file section and structural map**

The folder structure of a dataset is turned into files containing the file
section and structural map of the METS document::

    compile-structmap --workspace ./workspace

Optionally, the structural map can be created based on given EAD3 structure instead of folder structure,
and here a valid EAD3 file is given with --dmdsec_loc argument::

    compile-structmap --workspace ./workspace --structmap_type 'EAD3-logical' --dmdsec_loc tests/data/import_description/metadata/ead3_test.xml

**Compile METS document and Submission Information Package**

Compile a METS document file from the previous results::

    compile-mets ch 'CSC' 'e48a7051-2247-4d4d-ae90-44c8ee94daca' --workspace ./workspace --copy_files --clean

The argument --copy_files copies the files to the workspace.
The argument --clean cleans the workspace from the METS parts created in previous scripts.

Digitally sign the a METS document::

    sign-mets tests/data/rsa-keys.crt --workspace ./workspace

Create a TAR file::

    compress ./workspace --tar_filename sip.tar

Additional notes
----------------
This software is able to collect metadata and check well-formedness of a limited set of file
formats. Please see the file-scraper repository for more information.

The Pre-Ingest Tool does not support well-formedness checks of the following file formats:

    * text/csv file
    * text/xml file against XML schema or schematron files

Should you append these files to your workspace, use the --skip_wellformed_check argument on them.

Copyright
---------
Copyright (C) 2018 CSC - IT Center for Science Ltd.

This program is free software: you can redistribute it and/or modify it under the terms
of the GNU Lesser General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with
this program.  If not, see <https://www.gnu.org/licenses/>.
