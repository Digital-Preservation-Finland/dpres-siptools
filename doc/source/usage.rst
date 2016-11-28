
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
    * compile-mets
	Used for compiling mets.xml
    * compress
	Compiles a SIP. Removes all temp files.

   

Examples
------------------------------------

Files to be preserved::


    $ find .
    /home/pekkaliisa/paketit/oma-sippi-0001/
        aineisto/
            kuva.jpg
            teksti.pdf
            dcdescription.xml



Import descriptive metadata::

    $ import_description workspace aineisto

        workspace/dcdescription-dmdsec.xml

Import files:: 
    $ import_object kuva.pdf
    $ import_object teksti.pdf 

        workspace/
            kuva-amdsec.xml
            teksti-amdsec.xml

    $ import_object aineisto*
    
Create digital provenance::
    $ premis_event creation 2011-03-15T11:12:13

        workspace/
            creation.xml    

Create structure::    
    $ compile_structmap aineisto workspace

    workspace/
            structmap.xml



Create a SIP::

    $ compile-mets kdk CSC


   

