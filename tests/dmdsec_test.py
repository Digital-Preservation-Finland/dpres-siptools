""" Test"""
from siptools.scripts.dmdsec import import_description


def test_dmdsec():
    """ test """
    # Testi oikealle datalle: Tutki syntyneen dmdsec-oikeellisuus
    # lukemalla lxml.etree.fromstring -funktiolla
    # Tee testit myos epaonnistuneille tapauksille: Jos tiedostoa ei
    # loydy, tiedosto ei ole xml:aa, metadata ei ole luettelossa (vaara
    # nimiavaruus


    import_description()

    assert True
