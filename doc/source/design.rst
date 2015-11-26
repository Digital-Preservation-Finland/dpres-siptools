Component purpose
===================

This component is used for creating Digital Preservation Submission Information Package (SIP). You can use the component for forming SIP or only parts of mets.xml. For example you can extract technical metadata of a file. The component can be used either in command line or over REST. 


Initial Plans
===========


Työkalu sisältää toimintoja, jotka suorittamalla saa koostettua SIP-paketin. Työkalun komennot luovat xml-tiedostoja, jotka ovat osia mets.xml:stä. Työkalu luo tätä varten myös tilapäisiä tiedostoja. Työkalun komennot suoritetaan alla kuvatussa järjestyksessä, jotta mets.xml saadaan luotua.

import-description:

Kuvailevat metatiedot tuodaan työkalulle kutsumalla import-description-toimintoa. Kuvailevat metatiedot ovat valmiiksi KDK:n xml-formaatissa. Komentoa voidaan kutsua erikseen n-kertaa jokaiselle metatiedolle tai parametrina voidaan antaa hakemisto. Työkalu luo kuvaileva-metatieto-elementin (dmdSec).

::
        
       import-description  files/*.xml

import-object:

Kaikki digitaaliset objektit tuodaan työkalulle kutsumalla import-object-toimintoa. Parametrina annetaan tiedosto tai hakemistopolku. Työkalu luo techMD-elementin ja tähän Premis:objektin sekä sopivan teknisen metatiedon formaatin (esim. textMD). Premis:objektiin tallennetaan tarkistussumma ja sen muodostamisessa käytetty 
algoritmi sekä tiedoston formaatti.

::
 
        import-object files/*.jpg


premis-event:

Syntyhistoria luodaan premis-event-komennnolla. Premis-event -komennolle annetaan parametrina tapahtuman tyyppi (premis-event-type, kontrolloitu 
sanasto, esim. creation tai processing), tapahtuman kuvaus ja kohteena oleva 
digitaalinen objekti. Komento luo tapahtumatyypin mukaisen txml-tiedoston, 
esim. creation.xml

:: 

        premis-event creation "Digitointi xyz" "HP superjet" 

add-event:

Syntyhistoria lisätään add-event-komennnolla. Add-event -komennolle annetaan 
parametrina tiedosto, jossa on premis-eventien ja agentien tiedot ja toisena 
parametrina niihin liittyvä digitaalinen objekti. Komento luo viittauksen 
syntyhistorian premis:eventistä premis:objektiin.

::

        add-event creation.xml -R kuva.jpg

describe-object:

Tällä toiminnolla saadaan liitettyä metatiedot tiedostoihin. Parametrina annetaan kuvailevan metatietotiedoston polku ja siihen liittyvien digitaalisten objektin hakemistopolku.
Työkalu luo tiedostometatiedon(fileSec), jossa liitetään yhteen tiedostot ja niihin liittyvät hallinnolliset metatiedot. Tiedostometatiedon file-elementissä on listattu tiedostoon liittyvät tekniset metatiedot ja syntyhistoria-tapahtumat.
Työkalu luo rakennekartan, jossa kuvailevat metatiedot on liitetty tiedostoihin. Rakennekartan div-elementissä on listana viittaukset kuvaileviin metatietoihin ja ftpr-elementistä on viittaus file-elementin tiedostoid:hen. Työkalun ensimmäisessä vaiheessa toteutetaan vain yksitasoinen tiedostorakenne, jossa siis kuvailu liittyy tiettyyn joukkoon tiedostoja, eikä alikansioita tai muita rakenteita ole. 

::

        n x describe-object files/dublincore1.xml files/


compile-mets:

Tuottaa mets.xml:n. Toiminto luo mets-headerin ja koostaa sitten koko mets.xml:n työkalun aiemmin luomista xml-paloista. Parametrina annetaan organisaation nimi.

::

        compile-mets organisaation_nimi


validate-sip:

Toiminto tarkistaa mets.xml:n mukaan puuttuvat ja ylimääräiset tiedostot.


compress:

Koostaa sip-paketin. Poistaa työkalun luomat temp-hakemistot ja pakkaa tiedostot. 



Alla on esimerkki hakemistorakenteesta, jossa on työkalulle annettavia tiedostoja ja työkalun tuottamia tiedostoja:

kuvailevat metatiedot: workspace/metadata/description1.xml 

digitaaliset objektit: workspace/sip_source/files/kuva.jpg

syntyhistoria: workspace/events/[creation][processing].xml

työkalun tuottamat mets.xml:n osat: workspace/mets-parts

lopullinen sip-paketti: compressed-sip/sip.tar.gz
