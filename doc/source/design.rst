Design
=====

Component purpose
**************

This component is used for creating Digital Preservation Submission Information Package (SIP). You can use the component for forming a SIP or only parts of mets.xml. For example you can extract technical metadata of a file. The component can be used either in command line or over REST. 


Initial Plans
***********

Here is a plan how the component builds mets.xml. The component is building mets piece by
piece. Each task creates a new piece of output, so that the input is not modified. The specific mets document can be referred by parameter METS.OBJID. 

Paketointikomponentti rakentaa METSiä pala palalta, ja tiettyyn METS-dokumenttiin viitataan parametrina välitettävän METS.OBJIDn perusteella. Komponentin avulla voi laatia myös yksittäisiä METS-dokumentin osia, kuten teknisen metatiedon. Koko METS-dokumentin voi pyytää komponentilta niin ikään METS.OBJIDn avulla.

 
1. Luo METS-dokumentin runko ja header (1 kpl)

	input: 	

	* Organisaation nimi 
    	* vapaaehtoisesti siirtopaketin tunniste sekä luontiaika
    	* vapaaehtoinen METS.OBJID (generoidaan, jos ei tule)
    	* Luo hallinnollinen (amdSec) ja rakennekartta (structMap)-runko

	output: 

	* METS.OBJID
   	* mets.xml

Jokaista digitaalista objektia kohden (2-7, parametrina annettu METS.OBJID liittää laaditun XML-sanoman tiettyyn METS-sanomaan):


2. Luo kuvaileva metatieto (1-n kpl)
    input:

	* kuvailevan metatiedon XML-formaatti
	* kuvaileva metatieto annetussa XML-formaatissa
	* vapaaehtoisesti metatiedon luontiaika
	* METS.OBJID 

    output: 
	* dmdSec.ID
	* dmdSec.xml

3. Luo käyttörajoitus
	* PREMIS-rights-elementin mukaisia parametreja
	* METS.OBJID
	* rightsMD.ID

4. Luo lähdetiedot
	input:
	* kuvailevan metatiedon XML-formaatti
	* kuvaileva metatieto annetussa XML-formaatissa
	* vapaaehtoisesti metatiedon luontiaika
	* METS.OBJID
	output:
	* sourceMD.ID
	* digiprov.xml

5. Luo synty- ja tapahtumahistoria (1-n kpl) 
	input:
 	* Tapahtuman nimi
 	* tapahtuman kohde
 	* tapahtuman suorittajat
 	* METS.OBJID
	output: 
	* digiprovMD.ID

6. Luo tiedostoviite (1 kpl) 
	
	input:
	* tiedostopolku (1 kpl)
	* viittaus käyttörajoitukseen; RightsMD-elementin tunniste (1-n kpl)
	* viittaus lähdetietoihin; SourceMD-elementin tunniste (1-n kpl)
	* viittaus synty- ja tapahtumahistoriaan; DigiprovMD-elementin tunniste (1-n kpl)
	* vapaaehtoinen tarkistussumma ja algoritmi (1 kpl)
	output:
 	* file.ID

 
paketointikomponentti luo tekniset metatiedot:

	* tarkistussumman (jos ei annettu), 
	* tiedostomuodon ja sen version, 
	* tiedostotyyppikohtaiset metatiedot (TextMD, MIX, AudioMD, VideoMD), 
	* sekä lisää viittaukset file-elementistä näihin techMD-elementteihin (1-n kpl)	

	input: METS.OBJID
	output: file.ID

7. Luo rakennekarttaan div-elementti (1 kpl)
	input:
	* tiedostoviite; File-elementin tunniste = file.ID
	* viittaus kuvailevaan metatietoon, dmdSec-elementin tunniste = dmdSec.ID
	input:
 	* vapaaehtoinen isätieto div.ID, luo hierarkian
	* METS.OBJID
	output: div.ID

8.	Anna METS
 * METS.OBJID
 * output: METS

9. Muodosta SIP
 * allekirjoita digitaalisesti
 * zip

Jos kutsuu yksittäistä metodia ilman METS.OBJID –parametria, ko. metodi palauttaa XML-sanoman, esim.

Luo synty- ja tapahtumahistoria,
input:
 *	Tapahtuman nimi
 *	tapahtuman kohde
 *	tapahtuman suorittajat

 * output PREMIS


