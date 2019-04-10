Pre-Ingest Tool
===============

This tool is intended to be used for generating an OAIS SIP for digital preservation.
It produces METS document (mets.xml) that contains metadata for digital preservation
required by the specifications used in Finnish national digital preservation services.
The tool contains code for extracting metadata, creating and digitally signing the
METS document.

The aim is to provide digital preservation services for culture and research to ensure
the access and use of materials long in the future. Documentation and specifications
for the digital preservation service can be found in: http://digitalpreservation.fi

The Pre-Ingest Tool currently supports specification version 1.7.1.

Backwards compatibility
-----------------------

This version of the tool is not backward-compatible with older versions. The non-compatible differences in the script arguments are the following:

    * import_object.py

        * ``--skip_inspection`` is changed to ``--skip_wellformed_check``.
        * ``--digest_algorithm`` and ``--message_digest`` have been combined to ``--checksum``.
        * ``--format_name`` and ``--format_version`` have been combined to ``--file_format``.
        
    * create_addml.py

        * ``--no-header`` has been removed as unnecessary.

    * import_description.py

        * ``--desc_root`` has been changed to ``--remove_root``.

    * compile_structmap.py

        * ``--dmdsec_struct`` is removed and merged to ``--structmap_type``.
        * ``--type_attr`` is changed to ``--structmap_type``.

Installation
------------

Installation and usage require Python 2.7.
The software is tested with Python 2.7 with Centos 7.x / RHEL 7.x releases.

Get python-virtuelenv software::

    sudo pip install virtualenv

Run the following to activate the virtual environment::

    virtualenv .venv
    source ./.venv/bin/activate

Install the required software with command::

    pip install -r requirements_github.txt

Also, openssl-devel and gcc packages are required in your system to install M2Crypto.

See the README from file-scraper repository for additional installation requirements:
https://github.com/Digital-Preservation-Finland/file-scraper/blob/master/README.rst

Scripts
-------

import_description
    for adding a descriptive metadata section.

premis_event
    for creating digital provenance metadata.

import_object
    for adding the digital objects to a METS document.

create_mix
    for creating MIX metadata for image files.

create_addml
    for creating ADDML metadata for csv files.

create_audiomd
    for creating AudioMD metadata for audio files.

create_videomd
    for creating VideoMD metadata for video files.

compile_structmap
    for creating file section and structural map.

compile_mets
    for compiling all previously created metadata files in a METS document.

sign_mets
    for digitally signing the submission information package.

compress
    for wrapping the created submission information package directory to a TAR file.

Usage
-----

In order to build a SIP for digital preservation, use the scripts in the following order.
These scripts produce a digitally signed METS document in the parametrized folder 'workspace'.

For a short description about other optional arguments which are not listed here, see::

    python siptools/scripts/<scriptname>.py --help

**Import digital objects and create general technical metadata**

You can create technical metadata elements of a METS document from files located in the folder
tests/data/structured followingly::

    python siptools/scripts/import_object.py --workspace ./workspace 'tests/data/structured'

You may use this script as many times as needed to import all your digital object.

**Create file format specific technical metadata**

If your dataset contains image data, create also MIX metadata for each of the image files::

    python siptools/scripts/create_mix.py path/to/images/image.tif --workspace ./workspace
    
ADDML metadata for a CSV file can be created by running::
    
    python siptools/scripts/create_addml.py path/to/csv_file.csv --charset 'UTF8' --sep 'CR+LF' --quot '"' --delim ';' --workspace ./workspace

A flag --header should be given if CSV file has headers. --sep flag defines the character used to 
separate records and --delim the character used to separate fields. --quot defines the 
quotation character used.

AudioMD metadata for a audio stream file can be created by running::

    python siptools/scripts/create_audiomd.py path/to/audio/audio.wav --workspace ./workspace

VideoMD metadata for a video stream file can be created by running::

    python siptools/scripts/create_videomd.py path/to/video/video.wav --workspace ./workspace

Call the scripts above for each file needed in your data set.

**Create provenance metadata**

An example how to create digital provenance metadata for a METS document.
Values for the parameters --event_outcome and --event_type are predefined lists::

    python siptools/scripts/premis_event.py creation '2016-10-13T12:30:55' --event_detail Testing --event_outcome success --event_outcome_detail 'Outcome detail' --workspace ./workspace --agent_name 'Demo Application' --agent_type software --event_target 'tests/data/structured'

The argument --event_target is the object (file or directory) where the event applies.
If the argument is not given, the target is the whole dataset. Do not use argument
--event_target for directories, if the structural map is created based on EAD3 structure
with compile_structmap.py. If argument --agent_name is not given, agent metadata is
not created.

You may call this script several times to create multiple provenance metadata sections.

**Add existing descriptive metadata**

Script creates an xml file containing the descriptive metadata. Metadata must be in accepted format::

    python siptools/scripts/import_description.py 'tests/data/import_description/metadata/dc_description.xml' --workspace ./workspace --remove_root --dmdsec_target 'tests/data/structured'

Argument '--remove_root' removes the root element from the given descriptive metadata.
This may be needed, if the metadata is given in a container element belonging to another metadata format.
If the argument is not given, the descriptive metadata is fully included. The argument
'--dmdsec_target  <target>' is the directory where the descriptive metadata applies.
If the argument is not given, the target is the whole dataset. Do not use argument --dmdsec_target,
if the structural map is created based on EAD3 structure with compile_structmap.py.

You may call this script several times to import multiple descriptive metadata files.

**Compile file section and structural map**

The folder structure of a dataset is turned into files containing the file section and structural map of the METS document::

    python siptools/scripts/compile_structmap.py --workspace ./workspace

Optionally, the structural map can be created based on given EAD3 structure instead of folder structure,
and here a valid EAD3 file is given with --dmdsec_loc argument::

    python siptools/scripts/compile_structmap.py --workspace ./workspace --type_structmap 'EAD3-logical' --dmdsec_loc tests/data/import_description/metadata/ead3_test.xml

**Compile METS document and Submission Information Package**

Compile a METS document file from the previous results::

    python siptools/scripts/compile_mets.py --workspace ./workspace ch 'CSC' 'contract-id-1234' --copy_files --clean

The argument --copy_files copies the files to the workspace.
The argument --clean cleans the workspace from the METS parts created in previous scripts.

Digitally sign the a METS document::

    python siptools/scripts/sign_mets.py --workspace ./workspace tests/data/rsa-keys.crt

Create a TAR file::

    python siptools/scripts/compress.py --tar_filename sip.tar ./workspace

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
