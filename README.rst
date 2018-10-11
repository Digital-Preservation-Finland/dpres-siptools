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

The Pre-Ingest Tool currently supports specification version 1.7.0.

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

openssl-devel and gcc packages might be required in your system to install M2Crypto.

Optional: To make digital object validation possible, install the validation software listed in dpres-ipt README file,
see: https://github.com/Digital-Preservation-Finland/dpres-ipt
Otherwise, use argument --skip_inspection in import_object script.

Scripts
-------

import_description
    for creating a file containing descriptive metadata element of mets.xml.

premis_event
    for creating digital provenance elements of mets.xml.

import_object
    for adding all digital objects to mets.xml.

create_mix
    for creating MIX metadata for image files.

create_addml
    for creating ADDML metadata for csv files.

create_audiomd
    for creating AudioMD metadata for WAV files.

compile_structmap
    for creating structural map in mets.xml.

compile_mets
    for compiling all previously created files in a mets.xml file.

sign_mets
    for digitally signing the mets.xml file.

Usage
-----

In order to build a SIP for digital preservation, use the scripts in the following order.
These scripts produce a digitally signed mets.xml file in the parametrized folder 'workspace'.

You can create technical metadata elements of mets.xml from files located in the folder
tests/data/structured followingly::

    python siptools/scripts/import_object.py --workspace ./workspace 'tests/data/structured'

If your dataset contains image data, create also MIX metadata for each of the image files::

    python siptools/scripts/create_mix.py path/to/images/image.tif --workspace ./workspace
    
ADDML metadata for a CSV file can be created by running::
    
    python siptools/scripts/create_addml.py path/to/csv_file.csv --no-header --charset 'UTF8' --sep 'CR+LF' --quot '"' --delim ';' --workspace ./workspace

AudioMD metadata for a WAV file can be created by running::

    python siptools/scripts/create_audiomd.py path/to/audio/audio.wav --workspace ./workspace

Flags --header and --no-header define whether or not the CSV file has headers. If neither
is given, CSV file is assumed not to have headers. --sep flag defines the character used to 
separate records and --delim the character used to separate fields. --quot defines the 
quotation character used.

An example how to create digital provenance metadata for mets.xml.
Values for the parameters --event_outcome and --event_type are predefined lists::

    python siptools/scripts/premis_event.py creation '2016-10-13T12:30:55' --event_detail Testing --event_outcome success --event_outcome_detail 'Outcome detail' --workspace ./workspace --agent_name 'Demo Application' --agent_type software --event_target 'tests/data/structured'

The argument --event_target is the object (file or directory) where the event applies.
If the argument is not given, the target is the whole dataset. Do not use argument
--event_target for directories, if the structural map is created based on EAD3 structure
with compile_structmap.py. If argument --agent_name is not given, agent metadata is
not created.

Script creates an xml file containing the descriptive metadata. Metadata must be in accepted format::

    python siptools/scripts/import_description.py 'tests/data/import_description/metadata/dc_description.xml' --workspace ./workspace --desc_root remove --dmdsec_target 'tests/data/structured'

Argument '--desc_root remove' removes the root element from the given descriptive metadata.
This may be needed, if the metadata is given in a container element belonging to another metadata format.
If the argument is not given, the descriptive metadata is fully included. The argument
'--dmdsec_target  <target>' is the directory where the descriptive metadata applies.
If the argument is not given, the target is the whole dataset. Do not use argument --dmdsec_target,
if the structural map is created based on EAD3 structure with compile_structmap.py.

The folder structure of a dataset is turned into a file containing the structmap element of mets.xml::

    python siptools/scripts/compile_structmap.py --workspace ./workspace

Optionally, the structural map can be created based on given EAD3 structure instead of folder structure,
and here a valid EAD3 file is given with --dmdsec_loc argument::

    python siptools/scripts/compile_structmap.py --workspace ./workspace --dmdsec_struct ead3 --dmdsec_loc tests/data/import_description/metadata/ead3_test.xml

Compile a mets.xml file from the previous results::

    python siptools/scripts/compile_mets.py --workspace ./workspace ch 'CSC' 'contract-id-1234' --copy_files --clean

The argument --copy_files copies the files to the workspace.
The argument --clean cleans the workspace from the METS parts created in previous scripts.

Digitally sign the mets.xml::

    python siptools/scripts/sign_mets.py --workspace ./workspace tests/data/rsa-keys.crt

Create a TAR file::

    python siptools/scripts/compress.py --tar_filename sip.tar ./workspace


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
