Component purpose
===================

This component is used for creating Digital Preservation Submission Information Package (SIP). You can use the component for forming SIP or only parts of mets.xml. For example you can extract technical metadata of a file. The component can be used either in command line or over REST. 


Initial Plans
===========

Here is a plan how to build mets. The component is building mets piece by
piece.  The specific mets document can be refered by parameter METS.OBJID.:q

Paketointikomponentti rakentaa METSiä pala palalta, ja tiettyyn METS-dokumenttiin viitataan parametrina välitettävän METS.OBJIDn perusteella. Komponentin avulla voi laatia myös yksittäisiä METS-dokumentin osia, kuten teknisen metatiedon. Koko METS-dokumentin voi pyytää komponentilta niin ikään METS.OBJIDn avulla.

 .. function:: createMetsHeader(p1, p2, p3, p4) 
    Luo METS-dokumentin runko ja header (1 kpl)

    :param  p1: Organisaation nimi 
    :param  p2: vapaaehtoisesti siirtopaketin tunniste sekä luontiaika
    :param  p3: vapaaehtoinen METS.OBJID (generoidaan, jos ei tule)
    :param  p4: Luo hallinnollinen (amdSec) ja rakennekartta (structMap)-runko
    :rtype: METS.OBJID

Jokaista digitaalista objektia kohden (2-7, parametrina annettu METS.OBJID liittää laaditun XML-sanoman tiettyyn METS-sanomaan):

 .. function:: xyz(p1, p2, p3, p4)
    Luo kuvaileva metatieto (1-n kpl), parametrit:

    :param p1: kuvailevan metatiedon XML-formaatti
    :param p2: kuvaileva metatieto annetussa XML-formaatissa
    :param p3: vapaaehtoisesti metatiedon luontiaika
    :param p4: METS.OBJID 
    :rtype: dmdSec.ID

	
   Luo käyttörajoitus (1-n kpl), parametrit:
 :param p1: PREMIS:rights-elementin mukaisia parametreja
 :param p2: METS.OBJID
 :rtype: rigthsMD.ID

Luo lähdetiedot (0-n kpl), paramerit:
 :param  : 	kuvailevan metatiedon XML-formaatti
 :param  : 	kuvaileva metatieto annetussa XML-formaatissa
 :param  : 	vapaaehtoisesti metatiedon luontiaika
 :param  : 	METS.OBJID
:rtype: sourceMD.ID

Luo synty- ja tapahtumahistoria (1-n kpl), parametrit:
 :param : 	Tapahtuman nimi
 :param  : 	tapahtuman kohde
 :param  : 	tapahtuman suorittajat
 :param  : 	METS.OBJID
 :rtype: digiprovMD.ID

Luo tiedostoviite (1 kpl), parametrit:
 :param  : tiedostopolku (1 kpl)
 :param  : viittaus käyttörajoitukseen; RightsMD-elementin tunniste (1-n kpl)
 :param  : viittaus lähdetietoihin; SourceMD-elementin tunniste (1-n kpl)
 :param  : viittaus synty- ja tapahtumahistoriaan; DigiprovMD-elementin tunniste (1-n kpl)
 :param  : vapaaehtoinen tarkistussumma ja algoritmi (1 kpl)
 :rtype: file.ID

 
paketointikomponentti luo tekniset metatiedot: 
* tarkistussumman (jos ei annettu), 
* tiedostomuodon ja sen version, 
* tiedostotyyppikohtaiset metatiedot (TextMD, MIX, AudioMD, VideoMD), 
* sekä lisää viittaukset file-elementistä näihin techMD-elementteihin (1-n kpl)	

 :param : METS.OBJID
:rtype: RETURN file.ID

7.	Luo rakennekarttaan div-elementti (1 kpl), parametrit
 :param  :	tiedostoviite; File-elementin tunniste = file.ID
 :param  :	viittaus kuvailevaan metatietoon, dmdSec-elementin tunniste = dmdSec.ID
 :param  :	vapaaehtoinen isätieto div.ID, luo hierarkian
 :param  :	METS.OBJID
:rtype: div.ID

8.	Anna METS
 *	METS.OBJID
 * RETURN METS

9. Muodosta SIP
 * allekirjoita digitaalisesti
 * zip

Jos kutsuu yksittäistä metodia ilman METS.OBJID –parametria, ko. metodi palauttaa XML-sanoman, esim.

Luo synty- ja tapahtumahistoria, parametrit:
 :param  :	Tapahtuman nimi
 :param  :	tapahtuman kohde
 :param  :	tapahtuman suorittajat

 * RETURN PREMIS


