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

Release notes and backwards compability
---------------------------------------

See RELEASE-NOTES.rst

Installation
------------

Installation and usage requires Python 2.7.
The software is tested with Python 2.7 with Centos 7.x / RHEL 7.x releases.

Packages openssl-devel, swig and gcc are required in your system to install M2Crypto,
which is used for signing the packages with digital signature.

Get python-virtualenv software::

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

To deactivate the virtual environment, run ``deactivate``.
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

create-agent
    helper function to create detailed agent metadata to be used with the premis-event script

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
There are also lots of other options that can be given to this script in command line. See::

    import-object --help

For information on provenance metadata created during the importing of digital objects,
see the section on Provenance metadata in the packaging process below.

**Create file format specific technical metadata**

If your dataset contains image data, create MIX metadata for each of the image files::

    create-mix path/to/images/image.tif --workspace ./workspace
    
ADDML metadata for a CSV file can be created by running::
    
    create-addml path/to/csv_file.csv --workspace ./workspace --charset 'UTF8' --sep 'CR+LF' --quot '"' --delim ';'

A flag --header should be given if CSV file has headers. --sep flag defines the character used to 
separate records and --delim the character used to separate fields. --quot defines the 
quotation character used.

AudioMD metadata for an audio stream file can be created by running::

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

If several digital objects are linked to the same event and agent, use --event_target
multiple times. You may also want to consider using --linking_object and --add_object_links
in the following way::

    premis-event --linking_object source pat/to/source_file --add_object_links ...

This will create an object link to the event with a given role ``source``.  --linking_object
may be used several times. --event_target is same as using --linking_object with a
role ``target``. The role is stored only if ``--add_object_links`` is also used.

The helper script called ``create-agent`` can be used to create detailed agent metadata
and to link several agents to the same event. If used, this helper script must be run
before the ``premis-event`` script. This script will, unlike the other scripts, not
produce ready XML data, but rather collect metadata to a JSON file. This JSON data is
then passed to the ``premis-event`` script as an argument. An example how to use the
script::

    create-agent 'my software' --agent_type software --agent_version 1.0 --agent_role 'executing program' --create_agent_file 'my_event_1'

This will create an agent which is a software used to execute something. The '--agent_role'
argument specifies the role of the agent in relation to the event and is used when linking
the agent to the event. The required argument '--create_agent_file' is the name of the
JSON file that collects the agent metadata. If multiple agents are created for the same
event by running the ``create-agent`` script several times, they should all use the same
value for the '--create_agent_file' argument. This value is then passed on to
``premis-event`` like this::

    premis-event creation '2016-10-13T12:30:55' --workspace ./workspace --event_detail Testing --event_outcome success --event_outcome_detail 'Outcome detail'  --create_agent_file 'my_event_1'

The ``premis-event`` script will the create the actual XML data for every agent in the
"my_event_1" JSON file and link the agent(s) to the event created by the script. Note
that when the '--create_agent_file' argument is used, this will override any eventual
agent information passed to the premis-event script by the arguments '--agent_name' and
--agent_type'. The '--create_agent_file' value should be unique for each event, presuming
that the events have different agents linked to them.

**Add existing descriptive metadata**

Script appends descriptive metadata into a METS XML wrapper. Metadata must be in an accepted format::

    import-description 'tests/data/import_description/metadata/dc_description.xml' --workspace ./workspace --dmdsec_target 'tests/data/structured' --dmd_source 'my database' --dmd_agent 'database client' 'software' --remove_root 

The argument '--remove_root' removes the root element from the given descriptive metadata.
This may be needed, if the metadata is given in a container element belonging to another metadata format.
If the argument is not given, the descriptive metadata is fully included. The argument
'--dmdsec_target  <target>' is the directory where the descriptive metadata applies.
If the argument is not given, the target is the whole dataset. Do not use argument --dmdsec_target,
if the structural map is created based on EAD3 structure with compile_structmap.py.

Currently importing multiple descriptive metadata files for the same --dmdsec_target is not supported.
However, it is possible to add multiple descriptive metadata files, when each of these have different targets.

For information on provenance metadata created during the importing of descriptive
metadata, see the section on Provenance metadata in the packaging process below. 

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

Digitally sign the METS document::

    sign-mets tests/data/rsa-keys.crt --workspace ./workspace

Create a TAR file::

    compress ./workspace --tar_filename sip.tar

Adding native files to package with corresponding normalized files
------------------------------------------------------------------

A native file is an original file which is applicable only for bit-level preservation.
Using the native file functionality requires a migrated file suitable for preservation
and a normalization event. In this case the ``import-object`` script must be run before
the ``premis-event`` script. In ``import-object``, the argument ``--file_format`` is
mandatory for native files. Use the value ``normalization`` or ``migration`` as event
type in ``premis-event``. Here is the basic functionality::

    import-object --file_format my_mimetype my_version --bit_level native ... path/to/native_file
    import-object ... path/to/migrated_file
    premis_event normalization ... --linking_object source path/to/native_file --linking_object outcome path/to/migrated_file --add_object_links
    ...

Sometimes a migration may be a combination of multiple source and/or outcome files.
In such case, use ``import-object`` for each of them and create the migration event
using ``--linking_object`` multiple times. For example combining two native files to
one migrated file, do the following::

    import-object --file_format my_mimetype my_version --bit_level native ... path/to/native_file
    import-object --file_format my_mimetype my_version --bit_level native ... path/to/another_native_file
    import-object ... path/to/migrated_file
    premis_event migration ... --linking_object source path/to/native_file --linking_object source path/to/another_native_file --linking_object outcome path/to/migrated_file --add_object_links
    ...

We omit some of the required parameters above, for example timestamp or ``--event_detail``.
However, these parameters are still required.

For a native file, file format identification and file well-formedness validation are
skipped in the ``import-object`` script.

Please note that importing native files in a submission information package for the Finnish
National Digital Preservation Services requires acceptance from the service beforehand.
If you are planning to use this feature, please contact the service for more information.

Provenance metadata in the packaging process
--------------------------------------------

The Pre-Ingest Tool documents the packaging process by creating provenance metadata
as PREMIS events and agents when running the scripts. The following scripts will
produce provenance metadata when running them:

import-object
    creates ``metadata extraction``, ``validation``, ``message digest calculation``
    and ``format identification`` type events, depending on the arguments supplied to
    the script. This provenance metadata documents the creation of the technical metadata
    and the software used in that process
import-description
    creates a ``metadata extraction`` type event, documenting the source of the
    descriptive metadata
compile-structmap
    creates a ``creation`` type event, documenting the creation of the structural
    metadata

The script import-object has two arguments relating to provenance metadata, ``--event_target``
and ``--event_datetime``. The first argument ``--event_target`` allows the provenance
metadata to be linked to a specific part of the contents, for example the package root,
regardless of the file path(s) given to the script. The second argument
``--event_datetime`` sets the timestamp of the event, which allows reusing the
same provenance metadata each time import-object is run::

    import-object 'tests/data/structured' --workspace ./workspace --event_datetime 2020-06-05 --event_target '.' 

The example above allows import-object to be run multiple times for different file paths
while still creating the provenance metadata only once with the timestamp ``2020-06-05`` and
linking the provenance metadata to the package root ``.``.

**Note that is highly recommended to use both arguments if import-object is run
separately for each individual digital object in a package!** By supplying the same
values for these arguments each time the script is run all digital objects will link
to the same provenance metadata in the METS document. Otherwise, new provenance
metadata is created each time the script is run.

For documenting the source of the descriptive metadata, the script import-description
has two arguments:, ``--dmd_source`` and ``--dmd_agent``. These are used for documenting
the source, e.g. database or system, for the descriptive metadata and the agent used
to export the metadata from the source, e.g. a database client or API.

For a native file, ``validation`` and ``format identification`` type events are not
created.

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
