
Command Line Usage Instructions
=============================



Commands:
*************************

    * import_description
	Used for creating descriptive metadata (dmdSec) part of mets. Creates an xml file.
    * import_object
	Used for extracting technical metadata of a file. Calculates the checksum of a file. Creates an xml file containing amdSec part of mets. 
    * premis_event
	Used for creating digital provenance (digiprovMD)of mets. Creates premis_agent and premis_event.
    * compile_structmap
	Used for creating structMap and fileSec of mets. Links descriptive metadata to the content, links files to administrative metadata and structure.
    * compile_mets
	Used for compiling mets.xml
    * sign_mets
    Used for signing mets.xml file  
    * compress
	Compiles a SIP. Removes all temp files.

   

Examples
------------------------------------

Files to be preserved::

    $ find .
    /tests/data/structured
            
            
Create technical metadata mets elements from files located in the folder /tests/data/structured::
    python siptools/scripts/import_object.py --output ./workspace 'tests/data/structured'
Results in folder workspace::
   ??? -techmd.xml
     
Create digital provenance mets elements::
        python siptools/scripts/premis_event.py creation  '2016-10-13T12:30:55'
            --event_detail Testing --event_outcome success
            --event_outcome_detail 'Outcome detail' --workspace ./workspace --agent_name 'Demo Application'
            --agent_type software
Results in the folder workspace::
    creation.xml

Import descriptive metadata for a dataset. Call for each descriptive metadata file separately::
        python siptools/scripts/import_description.py
                            'tests/data/import_description/metadata/dc_description.xml' --dmdsec_target tests/data/structured
                            --workspace ./workspace

Results in the folder workspace::

    
    
Create structure::
         python siptools/scripts/compile_structmap.py
                                    tests/data/structured --workspace ./workspace

Compile mets::
        python siptools/scripts/compile_mets.py --workspace workspace/ kdk 'CSC'
Results in the folder workspace::
    mets.xml

Digital signature::
        python siptools/scripts/sign_mets.py workspace/mets.xml /home/vagrant/siptools/workspace/signature.sig
                                                tests/data/rsa-keys.crt


   

