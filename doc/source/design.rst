
Lisää tähän suunnitelmat... https://jira.csc.fi/browse/KDKPAS-1082

Paketointipalvelun koodit
===================

Käytä koodille scratch-hakemistoa omassa kotihakemistosssa::

    mkdir -p scratch
    cd scratch
    git clone https://mikko.vatanen@source.csc.fi/scm/git/pas/siptools

Koodin muokkaaminen, kannattaa lisätä aina yksi kokonaisuus kerrallaan / tehdä yhtä asiaa yhdessä commitissa. Pieni tai iso committi. Riippuu vähän tehtävän luonteesta.
Tämä helpottaa katselmointia huomattavasti aka. voi katsoa “miksi tekijä on tehnyt tämän” ja sen jälkeen tarkastaa “ahaa, näinhän se sitten on toteutettu / tehty oikeasti”.

Hae ensin viimeisin koodi / dokumentaatio::

    git fetch
    git checkout develop
    git merge —ff-only origin/develop

    … tee muutokset …

Hyväksy muutokset::

    git status
    git diff
    git add <tiedostonimi> tai git add .
    git status
    git commit -m ‘KDKPAS-XYZ Miksi tein tämän asian’

Toimita muutokset sourcelle::

    git push

Mikäli ei onnistu niin::

    git fetch
    git rebase origin/develop
    git push


Palaverissa suunnitellut asiat
======================

Kirjoitetaan dokumentaatio rst-muodossa, englanniksi. Katso esimerkkiä “preservation” ja “storage” dokumentaatiosta.

Aloitetaan mets-muodostaminen näistä tiedostomuodoista::

    * museoviraston tiedostomuodot
        * pdf
        * tiff


Esimerkki komentorivikäyttöliittymästä
=============================

Huomaa vahva analogia/yhtäläisyys make -komentoon.

Komennot:

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



Esimerkki syötteen kanssa
------------------------------------

Lähtötilanne::


    $ find .
    /home/pekkaliisa/paketit/oma-sippi-0001/
        aineisto/
            kuva.jpg
            teksti.pdf

Metadatan purkaminen tiedostoista::

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





