import lxml.etree as ET

FI_NS = 'http://www.kdk.fi/standards/mets/kdk-extensions'

DIV_TYPES = ['Documentation files',
    'Configuration files',
    'Other files',
    'Method files',
    'Notebook',
    'Publication files',
    'Access and use rights files',
    'Software files',
    'Machine-readable metadata']

NAMESPACES = {
    'mets': 'http://www.loc.gov/METS/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'premis': 'info:lc/xmlns/premis-v2',
    'fi': 'http://www.kdk.fi/standards/mets/kdk-extensions',
    'xlink': 'http://www.w3.org/1999/xlink',
    'mix': 'http://www.loc.gov/mix/v20',
    'ead3': 'http://ead3.archivists.org/schema/',
    'addml': 'http://www.arkivverket.no/standarder/addml'
}

METS_MDTYPES = {
    'http://purl.org/dc/elements/1.1/' : {'mdtype' : 'DC', 'version' :'1.1'},
    'http://www.loc.gov/MARC21/slim' : {'mdtype' : 'MARC', 'version' : ''},
    'http://www.loc.gov/mods/v3' : {'mdtype' : 'MODS', 'version' : ''},
    'urn:isbn:1-931666-22-9': {'mdtype' : 'EAD', 'version' : ''},
    'http://ead3.archivists.org/schema/': {'mdtype' : 'OTHER', 'othermdtype' : 'EAD3',
        'version' : '1.0.0'},
    'urn:isbn:1-931666-33-4' : {'mdtype' : 'EAC', 'version' : ''},
    'http://www.lido-schema.org' : {'mdtype' : 'LIDO', 'version' : ''},
    'ddi:instance:3_2' : {'mdtype' : 'DDI', 'version' : '3.2'},
    'ddi:instance:3_1' : {'mdtype' : 'DDI', 'version' : '3.1'},
    'ddi:codebook:2_5' : {'mdtype' : 'DDI', 'version' : '2.5'},
    'http://www.icpsr.umich.edu/DDI' : {'mdtype' : 'DDI', 'version' : '2.1'},
    'http://www.vraweb.org/vracore4.htm' : {'mdtype' : 'VRA', 'version' : '4.0'},
    'http://www.arkivverket.no/standarder/addml' : {'mdtype' : 'OTHER',
        'othermdtype' : 'ADDML', 'version' : '8.3'}}

METS_PROFILE = {'kdk': 'http://www.kdk.fi/kdk-mets-profile', 'tpas': 'http://www.avointiede.fi/att-mets-profile', 'tpas-midterm': 'http://www.avointiede.fi/att-midterm-mets-profile?dissemination_service=no', 'tpas-dissemination': 'http://www.avointiede.fi/att-midterm-mets-profile?dissemination_service=yes' }

METS_CATALOG = "1.6.0"

METS_SPECIFICATION = "1.6.1"

RECORD_STATUS_TYPES = [
    'submission',
    'update',
    'dissemination'
]

def mets_extend(mets_root, catalog=METS_CATALOG,
                specification=METS_SPECIFICATION, contentid=None):
    """Create METS ElementTree"""

    mets_root.set('{%s}CATALOG' % FI_NS, catalog)
    mets_root.set('{%s}SPECIFICATION' % FI_NS, specification)
    if contentid:
        mets_root.set('{%s}CONTENTID' % FI_NS, contentid)

    return mets_root

