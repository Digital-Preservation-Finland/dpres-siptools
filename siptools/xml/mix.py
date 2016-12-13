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
        componentPhotometricInterpretation=None,
        ReferenceBlackWhite_elements=None,
        codec=None, codecVersion=None, codestreamProfile=None,
        complianceClass=None, tileWidth=None, tileHeight=None,
        qualityLayers=None, resolutionLevels=None, zoomLevels=None, 
        djvuFormat=None):

    """Returns MIX BasicImageInformation element

    :byteOrder: byte order in which multi-byte numbers are stored 
    :compressionScheme: compression scheme used to store the image data
    :compressionRatio: Agent type
    :ReferenceBlackWhite_elements: ReferenceBlackWhite elements appended to the
    PhotometricInterpretation (default=None)

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
            <mix:SpecialFormatCharacteristics>
                <mix:JPEG2000>
                    <mix:CodecCompliance>
                        <mix:codec>Kakadu</mix:codec>
                        <mix:codecVersion>5.2</mix:codecVersion>
                        <mix:codestreamProfile>P1</mix:codestreamProfile>
                        <mix:complianceClass>C1</mix:complianceClass>
                    </mix:CodecCompliance>
                    <mix:EncodingOptions>
                        <mix:Tiles>
                            <mix:tileWidth>256</mix:tileWidth>
                            <mix:tileHeight>256</mix:tileHeight>
                        </mix:Tiles>
                        <mix:qualityLayers></mix:qualityLayers>
                        <mix:resolutionLevels></mix:resolutionLevels>
                    </mix:EncodingOptions>
                </mix:JPEG2000>
                <mix:MrSID>
                    <mix:zoomLevels></mix:zoomLevels>
                </mix:MrSID>
                <mix:Djvu>
                    <mix:djvuFormat></mix:djvuFormat>
                </mix:Djvu>
            </mix:SpecialFormatCharacteristics>

        </mix:BasicImageInformation>

    """

    mix_BasicImageInformation = _element('BasicImageInformation')
    mix_BasicImageCharacteristics = _subelement(mix_BasicImageInformation, 'BasicImageCharacteristics')

    mix_imageWidth = _subelement(mix_BasicImageCharacteristics, 'imageWidth')
    mix_imageWidth.text = imageWidth

    mix_imageHeight = _subelement(mix_BasicImageCharacteristics, 'imageHeight')

    mix_PhotometricInterpretation = _subelement(mix_BasicImageCharacteristics,
            'PhotometricInterpretation')

    mix_colorSpace = _subelement(mix_PhotometricInterpretation, 'colorSpace')
    mix_colorSpace.text = colorSpace

    mix_ColorProfile = _subelement(mix_PhotometricInterpretation, 'ColorProfile')
    mix_IccProfile = _subelement(mix_ColorProfile, 'IccProfile')
    mix_iccProfileName = _subelement(mix_IccProfile, 'iccProfileName')
    mix_iccProfileName.text = iccProfileName

    mix_iccProfileVersion = _subelement(mix_IccProfile, 'iccProfileVersion')
    mix_iccProfileVersion.text = iccProfileVersion

    mix_iccProfileURI = _subelement(mix_IccProfile, 'iccProfileURI')
    mix_iccProfileURI.text = iccProfileURI

    mix_LocalProfile = _subelement(mix_ColorProfile, 'LocalProfile')
    mix_localProfileName = _subelement(mix_LocalProfile, 'localProfileName')
    mix_localProfileName.text = localProfileName

    mix_localProfileURL = _subelement(mix_LocalProfile, 'localProfileURL')
    mix_localProfileURL.text = localProfileURL

    mix_embeddedProfile = _subelement(mix_ColorProfile, 'embeddedProfile')
    mix_embeddedProfile.text = embeddedProfile

    mix_YCbCr = _subelement(mix_PhotometricInterpretation, 'YCbCr')
    mix_YCbCrSubSampling = _subelement(mix_YCbCr, 'YCbCrSubSampling')
    mix_yCbCrSubsampleHoriz = _subelement(mix_YCbCrSubSampling, 'yCbCrSubsampleHoriz')
    mix_yCbCrSubsampleHoriz.text = yCbCrSubsampleHoriz

    mix_yCbCrSubsampleVert = _subelement(mix_YCbCrSubSampling,
            'yCbCrSubsampleVert')
    mix_yCbCrSubsampleVert.text = yCbCrSubsampleVert

    mix_yCbCrPositioning = _subelement(mix_YCbCr, 'yCbCrPositioning')
    mix_yCbCrPositioning.text = yCbCrPositioning

    mix_YCbCrCoefficients = _subelement(mix_YCbCr, 'YCbCrCoefficients')
    mix_lumaRed = _subelement(mix_YCbCrCoefficients, 'lumaRed')
    mix_lumaRed.text = lumaRed

    mix_lumaGreen = _subelement(mix_YCbCrCoefficients, 'lumaGreen')
    mix_lumaGreen.text = lumaGreen

    mix_lumaBlue = _subelement(mix_YCbCrCoefficients, 'lumaBlue')
    mix_lumaBlue.text = lumaBlue

    if ReferenceBlackWhite_elements:
        for element in ReferenceBlackWhite_elements:
            mix_PhotometricInterpretation.append(element)

    mix_SpecialFormatCharacteristics = _subelement(mix_BasicImageInformation,
            'SpecialFormatCharacteristics')
    mix_JPEG2000 = _subelement(mix_SpecialFormatCharacteristics, 'JPEG2000')
    mix_CodecCompliance = _subelement(mix_JPEG20, 'CodecCompliance')
    mix_codec = _subelement(mix_CodecCompliance, 'codec')
    mix_codec.text = codec

    mix_codecVersion = _subelement(mix_CodecCompliance, 'codecVersion')
    mix_codecVersion.text = codecVersion

    mix_codestreamProfile = _subelement(mix_CodecCompliance, 'codestreamProfile')
    mix_codestreamProfile.text = codestreamProfile

    mix_complianceClass = _subelement(mix_CodecCompliance, 'complianceClass')
    mix_complianceClass.text = complianceClass

    mix_EncodingOptions = _subelement(mix_JPEG20, 'EncodingOptions')
    mix_Tiles = _subelement(mix_EncodingOptions, 'Tiles')
    mix_tileWidth = _subelement(mix_Tiles, 'tileWidth')
    mix_tileWidth.text = tileWidth

    mix_tileHeight = _subelement(mix_Tiles, 'tileHeight')
    mix_tileHeight.text = tileHeight

    mix_qualityLayers = _subelement(mix_EncodingOptions, 'qualityLayers')
    mix_qualityLayers.text = qualityLayers

    mix_resolutionLevels = _subelement(mix_EncodingOptions, 'resolutionLevels')
    mix_resolutionLevels.text = resolutionLevels

    mix_MrSID = _subelement(mix_SpecialFormatCharacteristics, 'MrSID')
    mix_zoomLevels = _subelement(mix_MrSID, 'zoomLevels')
    mix_zoomLevels.text = mix_zoomLevels

    mix_Djvu = _subelement(mix_SpecialFormatCharacteristics, 'Djvu')
    mix_djvuFormat = _subelement(mix_Djvu, 'djvuFormat')
    mix_djvuFormat.text = mix_djvuFormat

    return agent


def mix_Component(
        componentPhotometricInterpretation=None, footroom=None, headroom=None):
    """Returns MIX Component element

    :componentPhotometricInterpretation: byte order in which multi-byte numbers are stored 
    :compressionScheme: compression scheme used to store the image data
    :compressionRatio: Agent type

    Returns the following ElementTree structure::

        <mix:Component>
            <mix:componentPhotometricInterpretation></mix:componentPhotometricInterpretation>
            <mix:footroom></mix:footroom>
            <mix:headroom></mix:headroom>
        </mix:Component>

    """

    mix_Component = _element('Component')

    mix_componentPhotometricInterpretation = _subelement(mix_Component,
            'componentPhotometricInterpretation')
    mix_componentPhotometricInterpretation.text = componentPhotometricInterpretation

    mix_footroom = _subelement(mix_Component, 'footroom')
    mix_footroom.text = footroom

    mix_headroom = _subelement(mix_Component, 'headroom')
    mix_headroom.text = headroom

    return mix_Component

def mix_ReferenceBlackWhite(child_elements=None):
    """Returns MIX ReferenceBlackWhite element

    :child_elements: Any child elements appended to the ReferenceBlackWhite (default=None) 

    Returns the following ElementTree structure::

        <mix:ReferenceBlackWhite>
            {{ child elements }}
        </mix:ReferenceBlackWhite>

    """
    mix_ReferenceBlackWhite = _element('ReferenceBlackWhite')

    if child_elements:
        for element in child_elements:
            mix_ReferenceBlackWhite.append(element)

    return mix_ReferenceBlackWhite

def mix_ImageCaptureMetadata(sourceType=None, SourceID_elements=None):
    """Returns MIX ImageCaptureMetadata element

    :sourceType: specifies the medium of the analog source material scanned to
    create a digital still image
    :SourceID_elements: SourceID elements appended to the SourceInformation (default=None) 

    Returns the following ElementTree structure::

        <mix:ImageCaptureMetadata>
            <mix:SourceInformation>
                <mix:sourceType></mix:sourceType>
                {{ SourceID elements }}
                <mix:SourceSize>
                    <mix:SourceXDimension>
                        <mix:sourceXDimensionValue></mix:sourceXDimensionValue>
                        <mix:sourceXDimensionUnit></mix:sourceXDimensionUnit>
                    </mix:SourceXDimension>
                    <mix:SourceYDimension>
                        <mix:sourceYDimensionValue></mix:sourceYDimensionValue>
                        <mix:sourceYDimensionUnit></mix:sourceYDimensionUnit>
                    </mix:SourceYDimension>
                    <mix:SourceZDimension>
                        <mix:sourceZDimensionValue></mix:sourceZDimensionValue>
                        <mix:sourceZDimensionUnit></mix:sourceZDimensionUnit>
                    </mix:SourceZDimension>
                </mix:SourceSize>
            <mix:SourceInformation>
        </mix:ImageCaptureMetadata>

    """
    mix_ImageCaptureMetadata = _element('ImageCaptureMetadata')
    mix_SourceInformation = _subelement(mix_ImageCaptureMetadata, 'SourceInformation')
    mix_sourceType = _subelement(mix_SourceInformation, 'sourceType')
    mix_sourceType.text = sourceType

    if SourceID_elements:
        for element in SourceID_elements:
            mix_SourceInformation.append(element)

    mix_SourceSize = _subelement(mix_SourceInformation, 'SourceSize')
    mix_SourceXDimension = _subelement(mix_SourceInformation, 'SourceXDimension')
    mix_sourceXDimensionValue = _subelement(mix_SourceXDimension,
            'sourceXDimensionValue')
    mix_sourceXDimensionValue.text = sourceXDimensionValue
    mix_sourceXDimensionUnit = _subelement(mix_SourceXDimension,
            'sourceXDimensionUnit')
    mix_sourceXDimensionUnit.text = sourceXDimensionUnit


    return mix_ImageCaptureMetadata

def mix_SourceID(sourceIDType=None, sourceIDValue=None):
    """Returns MIX sourceID element

    :sourceIDType: designates the system or domain in which the identifier is
    unque
    :sourceIDValue: the value of the SourceID

    Returns the following ElementTree structure::

        <mix:sourceID>
            <mix:sourceIDType></mix:sourceIDType>
            <mix:sourceIDValue></mix:sourceIDValue>
        </mix:sourceID>

    """
    mix_sourceID = _element('sourceID')
    mix_sourceIDType = _subelement(mix_sourceID, 'sourceIDType')
    mix_sourceIDType.text = sourceIDType

    mix_sourceIDValue = _subelement(mix_sourceID, 'sourceIDValue')
    mix_sourceIDValue.text = sourceIDValue


    return mix_ReferenceBlackWhite
