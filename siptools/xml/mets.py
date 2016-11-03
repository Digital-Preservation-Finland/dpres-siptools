import datetime
import xml.etree.ElementTree as ET

import siptools.xml.xmlutil
import siptools.xml.namespaces

METS_NS = 'http://www.loc.gov/METS/'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'


def serialize(root_element):
    """Serialize ElementTree structure with PREMIS namespace mapping.

    This modifies the default "ns0:tag" style prefixes to "premis:tag"
    prefixes.

    :element: Starting element to serialize
    :returns: Serialized XML as string

    """

    def register_namespace(prefix, uri):
        """foo"""
        ns_map = getattr(ET, '_namespace_map')
        ns_map[uri] = prefix

    for ns in siptools.xml.namespaces.NAMESPACES:
        register_namespace(ns[0], ns[1])

    siptools.xml.xmlutil.indent(root_element)

    return ET.tostring(root_element)


def mets_ns(tag, prefix=""):
    """Prefix ElementTree tags with METS namespace.

    object -> {info:lc...premis}object

    :tag: Tag name as string
    :returns: Prefixed tag

    """
    if prefix:
        tag = tag[0].upper() + tag[1:]
        return '{%s}%s%s' % (METS_NS, prefix, tag)
    return '{%s}%s' % (METS_NS, tag)


def _element(tag, prefix=""):
    """Return _ElementInterface with PREMIS namespace.

    Prefix parameter is useful for adding prefixed to lower case tags. It just
    uppercases first letter of tag and appends it to prefix::

        element = _element('objectIdentifier', 'linking')
        element.tag
        'linkingObjectIdentifier'

    :tag: Tagname
    :prefix: Prefix for the tag (default="")
    :returns: ElementTree element object

    """
    return ET.Element(mets_ns(tag, prefix))


def _subelement(parent, tag, prefix=""):
    """Return subelement for the given parent element. Created element is
    appelded to parent element.

    :parent: Parent element
    :tag: Element tagname
    :prefix: Prefix for the tag
    :returns: Created subelement

    """
    return ET.SubElement(parent, mets_ns(tag, prefix))


def techmd(element_id, created_date=datetime.datetime.utcnow().isoformat(),
           child_elements=None):

    """Return the techMD element"""

    _techmd = _element('techMD')
    _techmd.set('ID', element_id)
    _techmd.set('CREATED', created_date)

    if child_elements:
        for element in child_elements:
            _techmd.append(element)

    return _techmd

def digiprovmd(element_id, created_date=datetime.datetime.utcnow().isoformat(),
        child_elements=None):
    """Return the digiprovMD element"""

    _digiprovmd = _element('digiprovMD')
    _digiprovmd.set('ID', element_id)
    _digiprovmd.set('CREATED', created_date)

    if child_elements:
        for element in child_elements:
            _techmd.append(element)

    return _digiprovmd

def amdsec(child_elements=None):
    """Return the amdSec element"""

    _amdsec = _element('amdSec')

    if child_elements:
        for element in child_elements:
            _amdsec.append(element)

    return _amdsec

def mptr(loctype=None, xlink_href=None, xlink_type=None):
    """Return the fptr element"""

    _mptr = _element('mptr')
    _mptr.set('LOCTYPE', loctype)
    _mptr.set('xlink:href', xlink_href)
    _mptr.set('xlink:type', xlink_type)

    return _fptr

def fptr(fileid=None):
    """Return the fptr element"""

    _fptr = _element('fptr')
    _fptr.set('FILEID', filed)

    return _fptr


def div(type=None, order=None, contentids=None, label=None, orderlabel=None, dmdid=None, amdid=None,
        div_elements=None, fptr_elements=None, mptr_elements=None):
    """Return the div element"""

    _div = _element('div')
    _div.set('TYPE', type)
    if order:
        _div.set('ORDER', order)
    if contentids:
        _div.set('CONTENTIDS', contentids)
    if label:
        _div.set('LABEL', label)
    if orderlabel:
        _div.set('ORDERLABEL', orderlabel)
    if dmdid:
        _div.set('DMDID', dmdid)
    if amdid:
        _div.set('AMDID', amdid)

    if div_elements:
        for element in div_elements:
            _div.append(element)
    if fptr_elements:
        for element in fprt_elements:
            _div.append(element)
    if mptr_elements:
        for element in mprt_elements:
            _div.append(element)

    return _div

def structmap(div_element=None, type=None, label=None, pid=None,
        pidtype=None):
    """Return the structmap element"""

    _structMap = _element('structMap')
    _structMap.append(div_element)
    if type:
        _structMap.set('TYPE', type)
    if label:
        _structMap.set('LABEL', label)
    if pid:
        _structMap.set('PID', pid)
    if pidtype:
        _structMap.set('PIDTYPE', pidtype)

    return _structMap
