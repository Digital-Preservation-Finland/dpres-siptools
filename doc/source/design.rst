

https://jira.csc.fi/browse/KDKPAS-1082
Komponentin avulla voidaan tuottaa SIP-paketti tai mets.xml:n osia kuten esim. tekniset metatiedot tiedostosta.
Paketointikomponenttia voidaan käyttää komentoriviltä ja REST-rajapinnan kautta. Myös paketointikirjastot tarjotaan asiakkaille käytettäviksi asiakkaan omassa ympäristössä (esim. githubin kautta).

Alustavaa suunnittelua:

Paketointikomponentti rakentaa METSiä pala palalta, ja tiettyyn METS-dokumenttiin viitataan parametrina välitettävän METS.OBJIDn perusteella. Komponentin avulla voi laatia myös yksittäisiä METS-dokumentin osia, kuten teknisen metatiedon. Koko METS-dokumentin voi pyytää komponentilta niin ikään METS.OBJIDn avulla.
1.	Luo METS-dokumentin runko ja header (1 kpl), parametrit:
-	Organisaation nimi 
-	vapaaehtoisesti siirtopaketin tunniste sekä luontiaika
-	vapaaehtoinen METS.OBJID (generoidaan, jos ei tule)
-	Luo hallinnollinen (amdSec) ja rakennekartta (structMap)-runko
RETURN METS.OBJID

Jokaista digitaalista objektia kohden (2-7, parametrina annettu METS.OBJID liittää laaditun XML-sanoman tiettyyn METS-sanomaan):

2.	Luo kuvaileva metatieto (1-n kpl), parametrit:
-	kuvailevan metatiedon XML-formaatti
-	kuvaileva metatieto annetussa XML-formaatissa
-	vapaaehtoisesti metatiedon luontiaika
-	METS.OBJID 
RETURN dmdSec.ID
3.	Luo käyttörajoitus (1-n kpl), parametrit:
-	PREMIS:rights-elementin mukaisia parametreja
-	METS.OBJID
RETURN rigthsMD.ID
4.	Luo lähdetiedot (0-n kpl), paramerit:
-	kuvailevan metatiedon XML-formaatti
-	kuvaileva metatieto annetussa XML-formaatissa
-	vapaaehtoisesti metatiedon luontiaika
-	METS.OBJID
RETURN sourceMD.ID
5.	Luo synty- ja tapahtumahistoria (1-n kpl), parametrit:
-	Tapahtuman nimi
-	tapahtuman kohde
-	tapahtuman suorittajat
-	METS.OBJID
RETURN digiprovMD.ID
6.	Luo tiedostoviite (1 kpl), parametrit:
-	tiedostopolku (1 kpl)
-	viittaus käyttörajoitukseen; RightsMD-elementin tunniste (1-n kpl)
-	viittaus lähdetietoihin; SourceMD-elementin tunniste (1-n kpl)
-	viittaus synty- ja tapahtumahistoriaan; DigiprovMD-elementin tunniste (1-n kpl)
-	vapaaehtoinen tarkistussumma ja algoritmi (1 kpl)
-	paketointikomponentti luo tekniset metatiedot: 
        - tarkistussumman (jos ei annettu), 
        - tiedostomuodon ja sen version, 
        - tiedostotyyppikohtaiset metatiedot (TextMD, MIX, AudioMD, VideoMD), 
        - sekä lisää viittaukset file-elementistä näihin techMD-elementteihin (1-n kpl)
-	METS.OBJID
RETURN file.ID
7.	Luo rakennekarttaan div-elementti (1 kpl), parametrit
-	tiedostoviite; File-elementin tunniste = file.ID
-	viittaus kuvailevaan metatietoon, dmdSec-elementin tunniste = dmdSec.ID
-	vapaaehtoinen isätieto div.ID, luo hierarkian
-	METS.OBJID
RETURN div.ID

8.	Anna METS
-	METS.OBJID
RETURN METS

9. Muodosta SIP
- allekirjoita digitaalisesti
- zip

Jos kutsuu yksittäistä metodia ilman METS.OBJID –parametria, ko. metodi palauttaa XML-sanoman, esim.

Luo synty- ja tapahtumahistoria, parametrit:
-	Tapahtuman nimi
-	tapahtuman kohde
-	tapahtuman suorittajat
RETURN PREMIS


