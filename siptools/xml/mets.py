"""
METS specific values related to national specifications
"""
from __future__ import unicode_literals

import six

from xml_helpers.utils import XSI_NS

FI_NS = 'http://digitalpreservation.fi/schemas/mets/fi-extensions'

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
    'fi': 'http://digitalpreservation.fi/schemas/mets/fi-extensions',
    'xlink': 'http://www.w3.org/1999/xlink',
    'mix': 'http://www.loc.gov/mix/v20',
    'ead3': 'http://ead3.archivists.org/schema/',
    'addml': 'http://www.arkivverket.no/standarder/addml',
    'audiomd': 'http://www.loc.gov/audioMD/',
    'videomd': 'http://www.loc.gov/videoMD/'
}

METS_MDTYPES = {
    'http://purl.org/dc/elements/1.1/': {
        'mdtype': 'DC', 'version': '2008'
    },
    'http://www.loc.gov/MARC21/slim': {
        'mdtype': 'MARC', 'version': 'marcxml=1.2; marc=marc21'
    },
    'http://www.loc.gov/mods/v3': {
        'mdtype': 'MODS', 'version': '3.7'
    },
    'urn:isbn:1-931666-22-9': {
        'mdtype': 'EAD', 'version': '2002'
    },
    'http://ead3.archivists.org/schema/': {
        'mdtype': 'OTHER', 'othermdtype': 'EAD3', 'version': '1.1.1'
    },
    'urn:isbn:1-931666-33-4': {
        'mdtype': 'EAC-CPF', 'version': '2010_revised'
    },
    'https://archivists.org/ns/eac/v2': {
        'mdtype': 'EAC-CPF', 'version': '2.0'
    },
    'http://www.lido-schema.org': {
        'mdtype': 'LIDO', 'version': '1.0'
    },
    'ddi:instance:3_3': {
        'mdtype': 'DDI', 'version': '3.3'
    },
    'ddi:instance:3_2': {
        'mdtype': 'DDI', 'version': '3.2'
    },
    'ddi:instance:3_1': {
        'mdtype': 'DDI', 'version': '3.1'
    },
    'ddi:codebook:2_5': {
        'mdtype': 'DDI', 'version': '2.5.1'
    },
    'http://www.icpsr.umich.edu/DDI': {
        'mdtype': 'DDI', 'version': '2.1'
    },
    'http://www.vraweb.org/vracore4.htm': {
        'mdtype': 'VRA', 'version': '4.0'
    },
    'http://www.arkivverket.no/standarder/addml': {
        'mdtype': 'OTHER', 'othermdtype': 'ADDML', 'version': '8.3'
    },
    'http://datacite.org/schema/kernel-4': {
        'mdtype': 'OTHER', 'othermdtype': 'DATACITE', 'version': '4.1'
    },
    'http://www.loc.gov/audioMD/': {
        'mdtype': 'OTHER', 'othermdtype': 'AudioMD', 'version': '2.0'
    },
    'http://www.loc.gov/videoMD/': {
        'mdtype': 'OTHER', 'othermdtype': 'VideoMD', 'version': '2.0'
    },
    'urn:ebu:metadata-schema:ebucore': {
        'mdtype': 'OTHER', 'othermdtype': 'EBUCORE', 'version': '1.10'
    }
}

METS_PROFILE = {
    'ch': 'http://digitalpreservation.fi/mets-profiles/cultural-heritage',
    'tpas': 'http://digitalpreservation.fi/mets-profiles/research-data',
}

METS_SCHEMA = 'http://digitalpreservation.fi/schemas/mets/mets.xsd'

METS_CATALOG = "1.7.5"

METS_SPECIFICATION = "1.7.5"

RECORD_STATUS_TYPES = [
    'submission',
    'update',
    'dissemination'
]


def mets_extend(mets_root, catalog=METS_CATALOG,
                specification=METS_SPECIFICATION, contentid=None,
                contractid=None):
    """Create METS ElementTree"""

    del mets_root.attrib['{%s}schemaLocation' % XSI_NS]
    mets_root.set('{%s}schemaLocation' % XSI_NS,
                  NAMESPACES['mets'] + ' ' + METS_SCHEMA)
    mets_root.set('{%s}CATALOG' % FI_NS, catalog)
    mets_root.set('{%s}SPECIFICATION' % FI_NS, specification)
    if contentid:
        mets_root.set('{%s}CONTENTID' % FI_NS, contentid)
    if contractid:
        contractstr = six.text_type(contractid)
        mets_root.set('{%s}CONTRACTID' % FI_NS, contractstr)

    return mets_root
