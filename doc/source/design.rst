Component purpose
===================

This component is used for creating Digital Preservation Submission Information Package (SIP). You can use the component for forming SIP or only parts of mets.xml. For example you can extract tec
hnical metadata of a file. The component can be used either in command line or over REST. 


Initial Plans
===========


Työkalu sisältää toimintoja, jotka suorittamalla saa koostettua SIP-paketin. Työkalun komennot luovat xml-tiedostoja, jotka ovat osia mets.xml:stä. Työkalu luo tätä varten myös tilapäisiä tiedostoja. Työkalun komennot suoritetaan alla kuvatussa järjestyksessä, jotta mets.xml saadaan luotua.

import-description:

Kuvailevat metatiedot tuodaan työkalulle kutsumalla import-description-toimintoa. Kuvailevat metatiedot ovat valmiiksi KDK:n xml-formaatissa. Komentoa voidaan kutsua erikseen jokaiselle metatiedolle tai parametrina voidaan antaa hakemisto. Työkalu luo kuvaileva-metatieto-elementin (dmdSec).

::
        
        import_description  files/*.xml

import-object:

Kaikki digitaaliset objektit tuodaan työkalulle kutsumalla import-object-toimintoa. Parametrina annetaan tiedosto tai hakemistopolku. Työkalu luo techMD-elementin ja tähän Premis:objektin sekä sopivan teknisen metatiedon formaatin (esim. textMD). Premis:objektiin tallennetaan tarkistussumma. 

::
 
        import_objecr files/*.jpg



describe-object:

Tällä toiminnolla saadaan liitettyä metatiedot tiedostoihin. Työkalun ensimmäisessä vaiheessa toteutetaan vain yksitasoinen tiedostorakenne, jossa siis kuvailu liittyy tiettyyn joukkoon tiedostoja, eikä alikansioita tai muita rakenteita ole. 
Työkalu luo tiedostometatiedon(fileSec), jossa liitetään yhteen tiedostot ja niihin liittyvät hallinnolliset metatiedot. Tiedostometatiedon file-elementissä on listattu tiedostoon liittyvät tekniset metatiedot ja syntyhistoria-tapahtumat.
Työkalu luo rakennekartan, jossa kuvailevat metatiedot on liitetty tiedostoihin. Rakennekartan div-elementissä on listana viittaukset kuvaileviin metatietoihin ja ftpr-elementistä on viittaus file-elementin tiedostoid:hen.

::

        n x describe_object files/de1.xml files/

Syntyhistoria luodaan add-event-komennnolla. Add-event -komennolle annetaan parametrina tiedosto, jossa on premis-eventien ja agentien tiedot ja toisena parametrina niihin liittyvä digitaalinen objekti. Komento luo viittauksen premis:objektista syntyhistorian premis:eventiin ja premis:agentiin.

:: 

        add_event creation.xml -R movie.dcp  

compile_mets:

Tuottaa mets.xml:n. Toiminto luo mets-headerin ja koostaa sitten koko mets.xml:n työkalun aiemmin luomista xml-paloista. Parametrina annetaan organisaation nimi.

::

        compile_mets organisaation_nimi


validate_sip:

Toiminto tarkistaa mets.xml:n mukaan puuttuvat ja ylimääräiset tiedostot.


compress:

Koostaa sip-paketin. Poistaa työkalun luomat temp-hakemistot ja pakkaa tiedostot. 


