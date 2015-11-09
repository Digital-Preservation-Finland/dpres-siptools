Component purpose
===================

This component is used for creating Digital Preservation Submission Information Package (SIP). You can use the component for forming SIP or only parts of mets.xml. For example you can extract technical metadata of a file. The component can be used either in command line or over REST. 


Initial Plans
===========


Paketointikomponentti rakentaa METSiä pala palalta, ja tiettyyn METS-dokumenttiin viitataan parametrina välitettävän METS.OBJIDn perusteella. Komponentin avulla voi laatia myös yksittäisiä METS-dokumentin osia, kuten teknisen metatiedon. Koko METS-dokumentin voi pyytää komponentilta niin ikään METS.OBJIDn avulla.

1. Luo METS-dokumentin runko ja header (1 kpl)
parametrit:

 :param  : Organisaation nimi 
 :param  : vapaaehtoisesti siirtopaketin tunniste sekä luontiaika
 :param  : vapaaehtoinen METS.OBJID (generoidaan, jos ei tule)
 :param  : Luo hallinnollinen (amdSec) ja rakennekartta (structMap)-runko

 RETURN METS.OBJID

Jokaista digitaalista objektia kohden (2-7, parametrina annettu METS.OBJID liittää laaditun XML-sanoman tiettyyn METS-sanomaan):

2. Luo kuvaileva metatieto (1-n kpl), parametrit:

 :param  : kuvailevan metatiedon XML-formaatti
 :param  : kuvaileva metatieto annetussa XML-formaatissa
 :param  : vapaaehtoisesti metatiedon luontiaika
 :param  : METS.OBJID 

 *RETURN dmdSec.ID

3.	Luo käyttörajoitus (1-n kpl), parametrit:
 :param  : PREMIS:rights-elementin mukaisia parametreja
 :param  : 	METS.OBJID
 
 *RETURN rigthsMD.ID

4.	Luo lähdetiedot (0-n kpl), paramerit:
 :param  : 	kuvailevan metatiedon XML-formaatti
 :param  : 	kuvaileva metatieto annetussa XML-formaatissa
 :param  : 	vapaaehtoisesti metatiedon luontiaika
 :param  : 	METS.OBJID

 *RETURN sourceMD.ID

5.	Luo synty- ja tapahtumahistoria (1-n kpl), parametrit:
 :param  : 	Tapahtuman nimi
 :param  : 	tapahtuman kohde
 :param  : 	tapahtuman suorittajat
 :param  : 	METS.OBJID

 *RETURN digiprovMD.ID

6.	Luo tiedostoviite (1 kpl), parametrit:
 :param  :tiedostopolku (1 kpl)
 :param  :viittaus käyttörajoitukseen; RightsMD-elementin tunniste (1-n kpl)
 :param  :viittaus lähdetietoihin; SourceMD-elementin tunniste (1-n kpl)
 :param  :viittaus synty- ja tapahtumahistoriaan; DigiprovMD-elementin tunniste (1-n kpl)
 :param  :vapaaehtoinen tarkistussumma ja algoritmi (1 kpl)
 :param  :paketointikomponentti luo tekniset metatiedot: 
       
	*tarkistussumman (jos ei annettu), 
        *tiedostomuodon ja sen version, 
        *tiedostotyyppikohtaiset metatiedot (TextMD, MIX, AudioMD, VideoMD), 
        *sekä lisää viittaukset file-elementistä näihin techMD-elementteihin (1-n kpl)	

 :param  :METS.OBJID

 *RETURN file.ID

7.	Luo rakennekarttaan div-elementti (1 kpl), parametrit
 :param  :	tiedostoviite; File-elementin tunniste = file.ID
 :param  :	viittaus kuvailevaan metatietoon, dmdSec-elementin tunniste = dmdSec.ID
 :param  :	vapaaehtoinen isätieto div.ID, luo hierarkian
 :param  :	METS.OBJID

 *RETURN div.ID

8.	Anna METS
 *	METS.OBJID
 *RETURN METS

9. Muodosta SIP
 *allekirjoita digitaalisesti
 *zip

Jos kutsuu yksittäistä metodia ilman METS.OBJID –parametria, ko. metodi palauttaa XML-sanoman, esim.

Luo synty- ja tapahtumahistoria, parametrit:
 :param  :	Tapahtuman nimi
 :param  :	tapahtuman kohde
 :param  :	tapahtuman suorittajat

 *RETURN PREMIS


