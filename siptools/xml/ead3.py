"""Functions for reading and generating Encoded Archival Description, EAD3, as
xml.etree.ElementTree data structures.

References:

    * EAD3 http;//www.loc.gov/ead
    * ElementTree
    https://docs.python.org/2.6/library/xml.etree.elementtree.html

"""


import json

import xml.etree.ElementTree as ET
import lxml.etree

import siptools.xml.xmlutil

EAD3_NS = 'http://ead3.archivists.org/schema/'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'


def serialize(root_element):
    """Serialize ElementTree structure with EAD3 namespace mapping.

    This modifies the default "ns0:tag" style prefixes to "ead3:tag"
    prefixes.

    :element: Starting element to serialize
    :returns: Serialized XML as string

    """

    def register_namespace(prefix, uri):
        """foo"""
        ns_map = getattr(ET, '_namespace_map')
        ns_map[uri] = prefix

    register_namespace('ead3', EAD3_NS)
    register_namespace('xsi', XSI_NS)

    siptools.xml.xmlutil.indent(root_element)

    return ET.tostring(root_element)


def ead3_ns(tag, prefix=""):
    """Prefix ElementTree tags with EAD3 namespace.

    object -> {info:lc...ead3}object

    :tag: Tag name as string
    :returns: Prefixed tag

    """
    if prefix:
        tag = tag[0].upper() + tag[1:]
        return '{%s}%s%s' % (EAD3_NS, prefix, tag)
    return '{%s}%s' % (EAD3_NS, tag)


def xsi_ns(tag):
    """Prefix ElementTree tags with XSI namespace.

    object -> {info:lc...ead}object

    :tag: Tag name as string
    :returns: Prefixed tag

    """
    return '{%s}%s' % (XSI_NS, tag)


def _element(tag, prefix=""):
    """Return _ElementInterface with EAD3 namespace.

    Prefix parameter is useful for adding prefixed to lower case tags. It just
    uppercases first letter of tag and appends it to prefix::

        element = _element('objectIdentifier', 'linking')
        element.tag
        'linkingObjectIdentifier'

    :tag: Tagname
    :prefix: Prefix for the tag (default="")
    :returns: ElementTree element object

    """
    return ET.Element(ead3_ns(tag, prefix))


def _subelement(parent, tag, prefix=""):
    """Return subelement for the given parent element. Created element is
    appended to parent element.

    :parent: Parent element
    :tag: Element tagname
    :prefix: Prefix for the tag
    :returns: Created subelement

    """
    return ET.SubElement(parent, ead3_ns(tag, prefix))


def ead_ead(archdesc=None, control=None, **attributes):
    """Create Encoded Archival Description root element."""

    allowed_attributes = ['altrender', 'audience', 'base', 'id', 'lang',
            'relatedencoding','script']

    _ead = _element('ead')

    _ead.set(
        xsi_ns('schemaLocation'),
		'http://ead3.archivists.org/schema '
		'http://www.loc.gov/ead/ead3.xsd')

    if attributes is not None:
        for attr in attributes:
            if attr in allowed_attributes:
                _ead.set(attr, attributes[attr])

    _ead.append(control)

    _ead.append(archdesc)

    return _ead

def ead_control(recordid, title, otherrecordids=None, representations=None,
        manstatus=None, pubstatus=None, managencys=None,
        lang=None, convention=None, loctype=None, locctrl=None,
        manevents=None, sources=None, **attributes):
    """Creates the EAD3 control element.

    The control element is a mandatory element that includes several
    subelements in a defined order. The subelements contents are
    included in the arguments and created in this function.

    """
    allowed_attributes = ['altrender', 'audience', 'base', 'countryencoding'
            'dateencoding', 'encodinganalog', 'id', 'lang', 'langencoding',
            'relatedencoding', 'repositoryencoding', 'script',
            'scriptencoding']

    _control = _element('control')

    if attributes is not None:
        for attr in attributes:
            if attr in allowed_attributes:
                _control.set(attr, attributes[attr])

    _recordid = _subelement(_control, 'recordid')
    _recordid.text = recordid

    if otherrecordids:
        for otherrecordid in otherrecordids:
            _otherrecordid = _subelement(_control, 'otherrecordid')
            _otherrecordid.text = otherrecordid

    if representations:
        for representation in representations:
            _representation = _subelement(_control, 'representation')
            _representation.text = representation

    _filedesc = _subelement(_control, 'filedesc')
    _titlestmt = _subelement(_filedesc, 'titlestmt')
    _titleproper = _subelement(_titlestmt, 'titleproper')
    _titleproper.text = title

    if manstatus:
        _maintenancestatus = _subelement(_control, 'maintenancestatus')
        _maintenancestatus.set('value', manstatus)

    if pubstatus:
        _publicationstatus = _subelement(_control, 'publicationstatus')
        _publicationstatus.text = pubstatus

    if managencys:
        _maintenanceagency = _subelement(_control, 'maintenanceagency')
        for managency in managencys:
            _agencyname = _subelement(_maintenanceagency, 'agencyname')
            _agencyname.text = managency

    _maintenancehistory = _subelement(_control, 'maintenancehistory')
    if len(manevents):
        for manevent in manevents:
            _maintenancehistory.append(manevent)

    if sources:
        _sources = _subelement(_control, 'sources')
        for source in sources:
            _source = _subelement(_sources, 'source')
            _source.text = source

    return _control

def ead_maintenanceevent(eventtype=None, eventdatetime=None, agenttype=None,
        agent=None, eventdescriptions=None):
    """Creates the EAD3 maintenanceevent element.

    The element maintenancevent is a mandatory element within control.
    It consists of several subelements of which some are empty elements,
    like the eventtype and agenttype. All included subelements contents
    are included as arguments and created in this function.

    """
    _maintenanceevent = _element('maintenanceevent')

    if eventtype:
        _eventtype = _subelement(_maintenanceevent, 'eventtype')
        _eventtype.set('value', eventtype)

    if eventdatetime:
        _eventdatetime = _subelement(_maintenanceevent, 'eventdatetime')
        _eventdatetime.text = eventdatetime

    if agenttype:
        _agenttype = _subelement(_maintenanceevent, 'agenttype')
        _agenttype.set('value', agenttype)

    if agent:
        _agent = _subelement(_maintenanceevent, 'agent')
        _agent.text = agent

    if eventdescriptions:
        for eventdescription in eventdescriptions:
            _eventdescription = _subelement(_maintenanceevent, 'eventdescription')
            _eventdescription.text = eventdescription

    return _maintenanceevent

def ead_archdesc(level, did, desc_elements=None, dsc=None, **attributes):
    """Creates the EAD3 archdesc element.

    The subelements of the archdesc element are defined in the list
    allowed_desc_elements and included in the argument desc_elements.
    If the EAD finding aid file contains c elements they are included
    within the dsc element defined here.

    """
    allowed_attributes = ['altrender', 'audience', 'base', 'encodinganalog',
            'id', 'lang', 'localtype', 'otherlevel', 'relatedencoding',
            'script']

    allowed_desc_elements = ['accessrestrict', 'accruals', 'acqinfo',
            'altformavail', 'appraisal', 'arrangement', 'bibliography',
            'bioghist', 'controlaccess', 'custodhist', 'fileplan', 'index',
            'legalstatus', 'odd', 'originalsloc', 'otherfindaid', 'phystech',
            'prefercite', 'processinfo', 'relatedmaterial', 'relations',
            'scopecontent', 'separatedmaterial', 'userestrict']

    _archdesc = _element('archdesc')

    _archdesc.set('level', level)

    if attributes is not None:
        for attr in attributes:
            if attr in allowed_attributes:
                _archdesc.set(attr, attributes[attr])

    _archdesc.append(did)

    if desc_elements:
        for element in desc_elements:
            if lxml.etree.QName(element.tag).localname in allowed_desc_elements:
                _archdesc.append(element)

    if dsc is not None:
        _archdesc.append(dsc)

    return _archdesc

def ead_did(head=None, desc_elements=None, **attributes):
    """Creates the EAD3 did element.

    The did element is a mandatory element containing basic descriptive
    metadata within archdesc and all c elements. Its subelements are
    defined in the list allowed_desc_elements and included in the
    argument desc_elements.

    """
    allowed_attributes = ['altrender', 'audience', 'encodinganalog', 'id',
            'lang', 'script']

    allowed_desc_elements = ['abstract', 'container', 'dao', 'daoset',
            'langmaterial', 'materialspec', 'origination', 'physdescset',
            'physdesc', 'physdescstructured', 'physloc', 'repository',
            'unitdate', 'unitdatestructured', 'unitid', 'unittitle']

    _did = _element('did')

    if attributes is not None:
        for attr in attributes:
            if attr in allowed_attributes:
                _did.set(attr, attributes[attr])

    if head:
        _did.append(head)

    if desc_elements:
        for element in desc_elements:
            if lxml.etree.QName(element.tag).localname in allowed_desc_elements:
                _did.append(element)

    return _did

def ead_c(did, cnum=None, csubs=None, head=None, desc_elements=None,
        thead=None, **attributes):
    """Creates the EAD3 c element.

    The c element created can either be unnumbered, c, or
    numbered, c01, c02 etc. defined by the argument cnum. Other
    hierarchically lower c elements that are part of this c element
    are included as a list in the csubs argument.

    """
    allowed_attributes = ['altrender', 'audience', 'base', 'encodinganalog',
            'id', 'lang', 'level', 'otherlevel', 'script']

    allowed_desc_elements = ['accessrestrict', 'accruals', 'acqinfo',
            'altformavail', 'appraisal', 'arrangement', 'bibliography',
            'bioghist', 'controlaccess', 'custodhist', 'fileplan', 'index',
            'legalstatus', 'odd', 'originalsloc', 'otherfindaid', 'phystech',
            'prefercite', 'processinfo', 'relatedmaterial', 'relations',
            'scopecontent', 'separatedmaterial', 'userestrict']

    if cnum:
        _c = _element(cnum)
    else:
        _c = _element('c')

    if attributes is not None:
        for attr in attributes:
            if attr in allowed_attributes:
                _c.set(attr, attributes[attr])

    if head:
        _c.append(head)

    _c.append(did)

    if desc_elements:
        for element in desc_elements:
            if lxml.etree.QName(element.tag).localname in allowed_desc_elements:
                _c.append(element)

    if thead:
        _c.append(thead)

    if csubs:
        for csub in csubs:
            _c.append(csub)

    return _c

def ead_element(tag, contents, **attributes):
    """Creates EAD3 element.

    Creates an EAD3 element that contains text. 

    """
    _new_element = _element(tag)

    if attributes is not None:
        for attr in attributes:
            _new_element.set(attr, attributes[attr])

    _new_element.text = contents

    return _new_element

def ead_wrapper(tag=None, contents=None, head=None, **attributes):
    """Creates EAD3 element that wraps other elements.

    Creates an EAD3 wrapper element that contains other elements, but no
    text. The elements contents is a list of other elements. 

    """
    _wrapper = _element(tag)

    if attributes is not None:
        for attr in attributes:
            _wrapper.set(attr, attributes[attr])

    if head:
        _wrapper.append(head)

    for content in contents:
        _wrapper.append(content)

    return _wrapper

