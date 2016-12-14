General
--------------------
This tool is intended to be used for generating an OAIS SIP for digital preservation. Tool produces mets.xml containing metadata required by Finnish National Digital Library and Open Science digital preservation. Tool contains code for extracting technical metadata, constructing structural map and digital signing of the package. 
This tool is created by CSC Oy for National Digital Library and Open Science projects. The aim is to provide digital preservation services for Culture and Research to ensure the access and use of materials long in the future. Documentation and specifications for the digital preservation service can be found in http://www.kdk.fi/en/digital-preservation/specifications.

Scripts
----------------------

import_description
    Used for adding decsriptive metadata to mets.xml. Creates a file containing this
    part of mets.xml.

premis_event
    for creating digital provenance part of mets.xml    

import_object
    for adding all digital objects to mets.xml

compile_structmap
    for creating structural map in mets.xml

compile_mets
    compiles all previously created mets parts in a mets.xml file

Usage
---------------------
In order to build a SIP for digital preservation use the scripts in following order. These produce mets.xml and digital signature in the parametrized folder 'workspace'.

Create technical metadata from files located in the folder
tests/data/structured::
    python siptools/scripts/import_object.py --output ./workspace 'tests/data/structured'

Create digital provenance::
    python siptools/scripts/premis_event.py creation  '2016-10-13T12:30:55'
    --event_detail Testing --event_outcome success --event_outcome_detail
    'Outcome detail' --workspace ./workspace --agent_name 'Demo Application'
    --agent_type software

Create descriptive metadata::
    python siptools/scripts/import_description.py
    'tests/data/import_description/metadata/dc_description.xml'  --workspace
    ./workspace

Create structure::
    python siptools/scripts/compile_structmap.py tests/data/structured --workspace ./workspace --dmdsec_id 'e9c8a92e-c2da-4c38-a5a9-fc9aade99a0a'

Compile mets::
    python siptools/scripts/compile_mets.py --workspace workspace/ kdk 'CSC'

Digital signature::
    python siptools/scripts/sign_mets.py workspace/mets.xml
    /home/vagrant/siptools/workspace/signature.sig tests/data/rsa-keys.crt

Building Documentation
----------------------

Documentation is available in HTML and PDF formats. You may build the
documentation with commands::

    cd doc
    make html
    make pdf

Alternatively you may view the documentation with the `docserver` command::

    cd doc
    make docserver

Now point your browser to http://10.0.10.10:8000/html

After finishing the documentation you may stop the `docserver` with command::

    cd doc
    make killdocserver


