
Command Line Usage Instructions
=============================



Commands:
*************************

    * extract-metadata
	Used for extracting technical metadata of a file.
    * extract-checksum
	Used for calculating the checksum of a file.
    * extract-XYZ
    * compile-mets
	Used for compiling mets.xml
    * validate-sip
	Validates
        -> schema
        -> shematron
        -> digital objects
        -> checksums
        -> virus
        ==> OK / ERROR

Examples
------------------------------------

Files to be preserved::


    $ find .
    /home/pekkaliisa/paketit/oma-sippi-0001/
        aineisto/
            kuva.jpg
            teksti.pdf

Extract technical metatdata from files::

    $ extract-metadata kuva.jpg

        packaging-metadata/
            kuva.jpg-<uuid>-metadata.xml

    $ extract-metadata teksti.pdf

        packaging-metadata/
            kuva.jpg-<uuid>-metadata.xml
            teksti.pdf-<uuid>-metadata.xml

    $ extract-metadata *.jpg
    $ extract-metadata *.pdf
    $ extract-metadata -r aineisto

Extract file checksums::

    $ extract-checksums *

Create a SIP::

    $ compile-mets <mets-objid> packaging-metadata


    /home/pekkaliisa/paketit/oma-sippi-0001/

        kuva.jpg
        teksti.pdf
        mets.xml

        metadata.tmp/
            kuva.jpg-<uuid>-metadata.xml
            teksti.pdf-<uuid>-metadata.xml

    $ sign-xml mets.xml


    /home/pekkaliisa/paketit/oma-sippi-0001/
        kuva.jpg
        teksti.pdf
        mets.xml
        signature.sig

        metadata.tmp/
            kuva.jpg-<uuid>-metadata.xml
            teksti.pdf-<uuid>-metadata.xml

            
    $ clean-temp-metadata

    /home/pekkaliisa/paketit/oma-sippi-0001/
        mets.xml
        signature.sig
        aineisto/
            kuva.jpg
            teksti.pdf

    $ cd ..

    $ zip -r oma-sippi-0001.zip oma-sippi-0001
    $ tar czvf oma-sippi-0001.tar.gz oma-sippi-0001

    $ validate-sip mets.xml

        -> ERROR
        -> OK

