
Command Line Usage Instructions
=============================



Commands:
*************************

    * extract-metadata
    * extract-checksum
    * extract-XYZ
    * compile-mets
    * validate-sip
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

    $ extract-checksums *

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

