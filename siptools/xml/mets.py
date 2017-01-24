import datetime
import xml.etree.ElementTree as ET
import siptools.xml.xmlutil
import siptools.xml.namespaces
import uuid
import re

METS_NS = 'http://www.loc.gov/METS/'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
FI_NS = 'http://www.kdk.fi/standards/mets/kdk-extensions'
XLINK = 'http://www.w3.org/1999/xlink'

def serialize(root_element):
    """Serialize ElementTree structure with PREMIS namespace mapping.

    This modifies the default "ns0:tag" style prefixes to "premis:tag"
    prefixes.

    :element: Starting element to serialize
    :returns: Serialized XML as string

    """

    siptools.xml.xmlutil.indent(root_element)

    return ET.tostring(root_element)


def mets_mets(profile=siptools.xml.namespaces.METS_PROFILE['kdk'],
        objid=str(uuid.uuid4()), label=None,
        catalog=siptools.xml.namespaces.METS_CATALOG,
        specification=siptools.xml.namespaces.METS_SPECIFICATION, contentid=None):
    """Create METS ElementTree"""

    def register_namespace(prefix, uri):
        """foo"""
        ns_map = getattr(ET, '_namespace_map')
        ns_map[uri] = prefix

    for prefix, uri in siptools.xml.namespaces.NAMESPACES.iteritems():
        register_namespace(prefix, uri)


    mets = _element('mets')
    mets.set('xmlns:' + 'fi', FI_NS)
    mets.set('xmlns:' + 'xlink', XLINK)
    mets.set('PROFILE', profile)
    mets.set('OBJID', objid)
    mets.set('fi:CATALOG', catalog)
    mets.set('fi:SPECIFICATION', specification)
    if label:
        mets.set('LABEL', label)
    if contentid:
        mets.set('fi:CONTENTID', contentid)

    return mets



def order(element):
    """Return order number for given element in METS schema. This can be
    use for example with sort(). """
    return  ['{%s}dmdSec' % METS_NS,
            '{%s}amdSec' % METS_NS,
            '{%s}techMD' % METS_NS,
            '{%s}digiprovMD' % METS_NS,
            '{%s}fileSec' % METS_NS,
            '{%s}structMap' % METS_NS].index(element.tag)


def children_order(element):
    return ['{%s}techMD' % METS_NS,
            '{%s}digiprovMD' % METS_NS,].index(element.getchildren()[0].tag)

def merge_elements(tag, elements):
    """Merge elements with given tag in elements list"""
    elements_to_merge = filter(lambda x: x.tag == tag, elements)

    elements_to_merge.sort(key=children_order)
    for element in elements_to_merge[1:]:
        elements_to_merge[0].extend(element.getchildren())

    elements = list(set(elements) - set(elements_to_merge))
    return elements + [elements_to_merge[0]]


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

def dmdSec(child_elements=None, element_id=str(uuid.uuid4()),
        created_date=datetime.datetime.utcnow().isoformat()):
    """Return the dmdSec element"""

    dmdSec = _element('dmdSec')
    dmdSec.set('ID', element_id)
    dmdSec.set('CREATED', created_date)
    mdWrap = _element('mdWrap')
    xmlData = _element('xmlData')
    if child_elements:
        for element in child_elements:
            xmlData.append(element)
            ns = namespace(element)[1:-1]
            if ns in siptools.xml.namespaces.METS_NS.keys():
                mdWrap.set("MDTYPE", siptools.xml.namespaces.METS_NS[ns]['mdtype'])
                mdWrap.set('MDTYPEVERSION',
                        siptools.xml.namespaces.METS_NS[ns]['version'])
            else:
                raise TypeError("Invalid namespace: %s" % ns)
    mdWrap.append(xmlData)
    dmdSec.append(mdWrap)

    return dmdSec


def techmd(element_id, created_date=datetime.datetime.utcnow().isoformat(),
           child_elements=None):
    """Return the techMD element"""

    techmd = _element('techMD')
    techmd.set('ID', element_id)
    techmd.set('CREATED', created_date)

    if child_elements:
        for element in child_elements:
            techmd.append(element)

    return techmd


def mdwrap(mdtype='PREMIS:OBJECT', mdtypeversion="2.3"):
    element = _element('mdWrap')
    element.set('MDTYPE', mdtype)
    element.set('MDTYPEVERSION', mdtypeversion)
    return element

def xmldata():
    return _element('xmlData')


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


def mets_agent(organisation_name, agent_role='CREATOR',
        agent_type='ORGANIZATION'):
    """Returns METS agent element"""
    metsagent = _element('agent')
    metsagent.set('ROLE', agent_role)
    metsagent.set('TYPE', agent_type)
    _orgname = _element('name')
    _orgname.text = organisation_name
    metsagent.append(_orgname)

    return metsagent


def metshdr(organisation_name, create_date=datetime.datetime.utcnow().isoformat(),
        last_mod_date=None, record_status=None):
    """Return the metsHdr element"""

    _metshdr = _element('metsHdr')
    _metshdr.set('CREATEDATE', create_date)
    _metshdr.set('LASTMODDATE', last_mod_date)
    _metshdr.set('RECORDSTATUS', record_status)

    _metsagent = mets_agent(organisation_name)

    _metshdr.append(_metsagent)

    return _metshdr


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
    _fptr.set('FILEID', fileid)

    return _fptr


def div(type=None, order=None, contentids=None, label=None, orderlabel=None,
        dmdid=None, admid=None,
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
        _div.set('DMDID', ' '.join(dmdid))
    if admid:
        _div.set('ADMID', ' '.join(admid))

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


def structmap(type=None, label=None, pid=None,
              pidtype=None):
    """Return the structmap element"""

    _structmap = _element('structMap')
    #_structMap.append(div_element)
    if type:
        _structmap.set('TYPE', type)
    if label:
        _structmap.set('LABEL', label)
    if pid:
        _structmap.set('PID', pid)
    if pidtype:
        _structmap.set('PIDTYPE', pidtype)

    return _structmap


def filegrp(use=None, file_elements=None):
    """Return the fileGrp element"""

    _filegrp = _element('fileGrp')
    if use:
        _filegrp.set('USE', use)
    if file_elements:
        for element in file_elements:
            _filegroup.append(elements)

    return _filegrp


def filesec(filegroup_elements=None):
    """Return the fileSec element"""

    _filesec = _element('fileSec')
    if filegroup_elements:
        for element in filegroup_elements:
            _filesec.append(element)

    return _filesec


def file(id=None, admid_elements=None, loctype=None, xlink_href=None, xlink_type=None,
         groupid=None):
    """Return the file element"""

    _file = _element('file')
    _file.set('ID', id)
    admids = ' '.join(admid_elements)
    _file.set('ADMID', admids)
    if groupid:
        _file.set('GROUPID', groupid)

    _flocat = _element('FLocat')
    _flocat.set('LOCTYPE', loctype)
    _flocat.set('xlink:href', xlink_href)
    _flocat.set('xlink:type', xlink_type)
    _file.append(_flocat)

    return _file

def namespace(element):
    """return xml element's namespace"""
    m = re.match('\{.*\}', element.tag)
    return m.group(0) if m else ''
