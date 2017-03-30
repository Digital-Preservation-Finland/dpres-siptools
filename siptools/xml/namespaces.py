METS_SCHEMALOCATION = "http://www.loc.gov/METS/ http://kdk.fi/standards/mets/mets.xsd"

NAMESPACES = {
    'mets': 'http://www.loc.gov/METS/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'premis': 'info:lc/xmlns/premis-v2',
    'fi': 'http://www.kdk.fi/standards/mets/kdk-extensions',
    'w3_xlink': 'http://www.w3.org/1999/xlink',
    'mix': 'http://www.loc.gov/mix/v20',
    'ead3': 'http://ead3.archivists.org/schema/'
}

METS_NS = {'http://purl.org/dc/elements/1.1/' : {'mdtype' : 'DC', 'version' :
'1.1'}, 'http://www.loc.gov/MARC21/slim' : {'mdtype' : 'MARC', 'version' : ''},
'http://www.loc.gov/mods/v3' : {'mdtype' : 'MODS', 'version' : ''},
'urn:isbn:1-931666-22-9': {'mdtype' : 'EAD', 'version' : ''},
'http://ead3.archivists.org/schema/': {'mdtype' : 'EAD3', 'version' : ''},
'urn:isbn:1-931666-33-4' : {'mdtype' : 'EAC', 'version' : ''},
'http://www.lido-schema.org' : {'mdtype' : 'LIDO', 'version' : ''},
'ddi:instance:3_2' : {'mdtype' : 'DDI', 'version' : '3.2'},
'ddi:instance:3_1' : {'mdtype' : 'DDI', 'version' : '3.1'},
'ddi:codebook:2_5' : {'mdtype' : 'DDI', 'version' : '2.5'},
'http://www.icpsr.umich.edu/DDI' : {'mdtype' : 'DDI', 'version' : '2.1'},
'http://www.vraweb.org/vracore4.htm' : {'mdtype' : 'VRA', 'version' : ''}}

METS_PROFILE = {'kdk': 'http://www.kdk.fi/kdk-mets-profile', 'tpas': 'http://www.avointiede.fi/att-mets-profile', 'tpas-midterm': 'http://www.avointiede.fi/att-midterm-mets-profile?dissemination_service=no', 'tpas-dissemination': 'http://www.avointiede.fi/att-midterm-mets-profile?dissemination_service=yes' }

METS_CATALOG = "1.5.0"

METS_SPECIFICATION = "1.5.0"

