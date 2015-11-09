{\rtf1\ansi\ansicpg1252\cocoartf1348\cocoasubrtf170
{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
\paperw11900\paperh16840\margl1440\margr1440\vieww10800\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural

\f0\fs24 \cf0 Esimerkki komentorivik\'e4ytt\'f6liittym\'e4st\'e4\
=============================\
\
Huomaa vahva analogia/yht\'e4l\'e4isyys make -komentoon.\
\
Komennot:\
\
    * extract-metadata\
    * extract-checksum\
    * extract-XYZ\
    * compile-mets\
    * validate-sip\
        -> schema\
        -> shematron\
        -> digital objects\
        -> checksums\
        -> virus\
        ==> OK / ERROR\
\
\
\
Esimerkki sy\'f6tteen kanssa\
------------------------------------\
\
L\'e4ht\'f6tilanne::\
\
\
    $ find .\
    /home/pekkaliisa/paketit/oma-sippi-0001/\
        aineisto/\
            kuva.jpg\
            teksti.pdf\
\
Metadatan purkaminen tiedostoista::\
\
    $ extract-metadata kuva.jpg\
\
        packaging-metadata/\
            kuva.jpg-<uuid>-metadata.xml\
\
    $ extract-metadata teksti.pdf\
\
        packaging-metadata/\
            kuva.jpg-<uuid>-metadata.xml\
            teksti.pdf-<uuid>-metadata.xml\
\
    $ extract-metadata *.jpg\
    $ extract-metadata *.pdf\
    $ extract-metadata -r aineisto\
\
    $ extract-checksums *\
\
\
    $ compile-mets <mets-objid> packaging-metadata\
\
\
    /home/pekkaliisa/paketit/oma-sippi-0001/\
\
        kuva.jpg\
        teksti.pdf\
        mets.xml\
\
        metadata.tmp/\
            kuva.jpg-<uuid>-metadata.xml\
            teksti.pdf-<uuid>-metadata.xml\
    \
\
    $ sign-xml mets.xml\
\
\
    /home/pekkaliisa/paketit/oma-sippi-0001/\
        kuva.jpg\
        teksti.pdf\
        mets.xml\
        signature.sig\
\
        metadata.tmp/\
            kuva.jpg-<uuid>-metadata.xml\
            teksti.pdf-<uuid>-metadata.xml\
\
\
    $ clean-temp-metadata\
\
    /home/pekkaliisa/paketit/oma-sippi-0001/\
        mets.xml\
        signature.sig\
        aineisto/\
            kuva.jpg\
            teksti.pdf\
\
    $ cd ..\
\
    $ zip -r oma-sippi-0001.zip oma-sippi-0001\
    $ tar czvf oma-sippi-0001.tar.gz oma-sippi-0001\
\
\
    $ validate-sip mets.xml\
\
        -> ERROR\
        -> OK\
\
\
\
\
\
}