"""Functions for reading and generating MIX Data Dictionaries as
xml.etree.ElementTree data structures.

References:

    * PREMIS http://www.loc.gov/standards/mix/
    * ElementTree
    https://docs.python.org/2.6/library/xml.etree.elementtree.html

"""


import json

import xml.etree.ElementTree as ET

import siptools.xml.xmlutil

MIX_NS = 'http://www.loc.gov/mix/v20'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'


def serialize(root_element):
    """Serialize ElementTree structure with MIX namespace mapping.

    This modifies the default "ns0:tag" style prefixes to "mix:tag"
    prefixes.

    :element: Starting element to serialize
    :returns: Serialized XML as string

    """

    def register_namespace(prefix, uri):
        """foo"""
        ns_map = getattr(ET, '_namespace_map')
        ns_map[uri] = prefix

    register_namespace('mix', MIX_NS)
    register_namespace('xsi', XSI_NS)

    siptools.xml.xmlutil.indent(root_element)

    return ET.tostring(root_element)


def mix_ns(tag, prefix=""):
    """Prefix ElementTree tags with MIX namespace.

    object -> {http://www.loc.gov/mix/v20}object

    :tag: Tag name as string
    :returns: Prefixed tag

    """
    if prefix:
        tag = tag[0].upper() + tag[1:]
        return '{%s}%s%s' % (MIX_NS, prefix, tag)
    return '{%s}%s' % (MIX_NS, tag)


def xsi_ns(tag):
    """Prefix ElementTree tags with XSI namespace.

    object -> {http://www.loc.gov/mix/v20}object

    :tag: Tag name as string
    :returns: Prefixed tag

    """
    return '{%s}%s' % (XSI_NS, tag)


def _element(tag, prefix=""):
    """Return _ElementInterface with MIX namespace.

    Prefix parameter is useful for adding prefixed to lower case tags. It just
    uppercases first letter of tag and appends it to prefix::

        element = _element('objectIdentifier', 'linking')
        element.tag
        'linkingObjectIdentifier'

    :tag: Tagname
    :prefix: Prefix for the tag (default="")
    :returns: ElementTree element object

    """
    return ET.Element(mix_ns(tag, prefix))


def _subelement(parent, tag, prefix=""):
    """Return subelement for the given parent element. Created element is
    appelded to parent element.

    :parent: Parent element
    :tag: Element tagname
    :prefix: Prefix for the tag
    :returns: Created subelement

    """
    return ET.SubElement(parent, mix_ns(tag, prefix))


def mix_mix(child_elements=None):
    """Create MIX Data Dictionary root element.

    :child_elements: Any elements appended to the MIX dictionary

    Returns the following ElementTree structure::


        <mix:mix
            xmlns:mix="http://www.loc.gov/mix/v20"
            xmlns:xsi="http://www.w3.org/2001/xmlschema-instance"
            xsi:schemalocation="http://www.loc.gov/mix/v20
                                http://www.loc.gov/mix/mix.xsd"

    """
    mix = _element('mix')
    mix.set(
        xsi_ns('schemaLocation'),
        'http://www.loc.gov/mix/v20 '
        'http://www.loc.gov/mix/mix.xsd')

    if child_elements:
        for element in child_elements:
            _mix.append(element)

    return _mix


def mix_BasicDigitalObjectInformation(
        byteOrder=None, compressionScheme=None, compressionRatio=None):
    """Returns MIX BasicDigitalObjectInformation element

    :byteOrder: byte order in which multi-byte numbers are stored 
    :compressionScheme: compression scheme used to store the image data
    :compressionRatio: Agent type

    Returns the following ElementTree structure::

        <mix:BasicDigitalObjectInformation>
            <mix:byteOrder>big endian</mix:byteOrder>
            <mix:Compression>
                <mix:compressionScheme>JPEG 2000 Lossless</mix:compressionScheme>
                <mix:compressionRatio>10</mix:compressionRatio>
            </mix:Compression>
        </mix:BasicDigitalObjectInformation>

    """

    mix_BasicDigitalObjectInformation = _element('BasicDigitalObjectInformation')

    mix_byteorder = _subelement(mix_BasicDigitalObjectInformation, 'byteOrder')
    mix_byteorder.text = byteOrder

    mix_compression = _subelement(mix_BasicDigitalObjectInformation, 'Compression')

    mix_compressionScheme = _subelement(mix_compression, 'compressionScheme')
    mix_compressionScheme.text = compressionScheme

    mix_compressionRatio = _subelement(mix_compression, 'compressionRatio')
    mix_compressionRatio.text = compressionRatio

    return mix_BasicDigitalObjectInformation

def mix_BasicImageInformation(
        imageWidth=None, imageHeight=None, colorSpace=None,
        iccProfileName=None, iccProfileVersion=None, iccProfileURI=None,
        localProfileName=None, localProfileURL=None, embeddedProfile=None,
        yCbCrSubsampleHoriz=None, yCbCrSubsampleVert=None,
        yCbCrPositioning=None, lumaRed=None, lumaGreen=None, lumaBlue=None,
        componentPhotometricInterpretation=None, footroom=None, headroom=None):
    """Returns MIX BasicDigitalObjectInformation element

    :byteOrder: byte order in which multi-byte numbers are stored 
    :compressionScheme: compression scheme used to store the image data
    :compressionRatio: Agent type

    Returns the following ElementTree structure::

        <mix:BasicImageInformation>
            <mix:BasicImageCharacteristics>
                <mix:imageWidth>869</mix:imageWidth>
                <mix:imageHeight>1271</mix:imageHeight>
                <mix:PhotometricInterpretation>
                    <mix:colorSpace>ICCBased</<mix:colorSpace>
                    <mix:ColorProfile>
                        <mix:IccProfile>
                            <mix:iccProfileName>Adobe RGB</mix:iccProfileName>
                            <mix:iccProfileVersion>1998</mix:iccProfileVersion>
                            <mix:iccProfileURI>http://www.adobe.com/digitalimag/adobergb.html</mix:iccProfileURI>
                        <mix:IccProfile>
                        <mix:LocalProfile>
                            <mix:localProfileName>xyz</mix:localProfileName>
                            <mix:localProfileURL>http://www.myprofile.com/digitalimag/myrgb.html</mix:localProfileURL>
                        <mix:LocalProfile>
                        <mix:embeddedProfile></mix:embeddedProfile>
                    </mix:ColorProfile>
                    <mix:YCbCr>
                        <mix:YCbCrSubSampling>
                            <mix:yCbCrSubsampleHoriz></mix:yCbCrSubsampleHoriz>
                            <mix:yCbCrSubsampleVert></mix:yCbCrSubsampleVert>
                        </mix:YCbCrSubSampling>
                        <mix:yCbCrPositioning></mix:yCbCrPositioning>
                        <mix:YCbCrCoefficients>
                            <mix:lumaRed></mix:lumaRed>
                            <mix:lumaGreen></mix:lumaGreen>
                            <mix:lumaBlue></mix:lumaBlue>
                        </mix:YCbCrCoefficients>
                    </mix:YCbCr>
                    <mix:ReferenceBlackWhite>
                        <mix:Component>
                            <mix:componentPhotometricInterpretation></mix:componentPhotometricInterpretation>
                            <mix:footroom></mix:footroom>
                            <mix:headroom></mix:headroom>
                        </mix:Component>
                    </mix:ReferenceBlackWhite>
                </mix:PhotometricInterpretation>
            </mix:BasicImageCharacteristics>
        </mix:BasicImageInformation>

    """
        #imageWidth=None, imageHeight=None, colorSpace=None,
        #iccProfileName=None, iccProfileVersion=None, iccProfileURI=None,
        #localProfileName=None, localProfileURL=None, embeddedProfile=None,
        #yCbCrSubsampleHoriz=None, yCbCrSubsampleVert=None,
        #yCbCrPositioning=None, lumaRed=None, lumaGreen=None, lumaBlue=None,
        #componentPhotometricInterpretation=None, footroom=None, headroom=None):

    mix_BasicDigitalObjectInformation = _element('BasicDigitalObjectInformation')

    mix_byteorder = _subelement(mix_BasicDigitalObjectInformation, 'byteOrder')
    mix_byteorder.text = byteOrder

    mix_compression = _subelement(mix_BasicDigitalObjectInformation, 'Compression')

    mix_compressionScheme = _subelement(mix_compression, 'compressionScheme')
    mix_compressionScheme.text = compressionScheme

    mix_compressionRatio = _subelement(mix_compression, 'compressionRatio')
    mix_compressionRatio.text = compressionRatio

    return agent

