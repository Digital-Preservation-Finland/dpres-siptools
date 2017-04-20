"""Functions for reading and generating MIX Data Dictionaries as
xml.etree.ElementTree data structures.

References:

    * MIX http://www.loc.gov/standards/mix/
    * Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)
    * http://www.niso.org/kst/reports/standards?step=2&gid=None&project_key=b897b0cf3e2ee526252d9f830207b3cc9f3b6c2c
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


def mix_mix(BasicDigitalObjectInformation=None, BasicImageInformation=None,
            ImageCaptureMetadata=None, ImageAssessmentMetadata=None):
    """Create MIX Data Dictionary root element.

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)
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

    if BasicDigitalObjectInformation:
        mix.append(BasicDigitalObjectInformation)
    if BasicImageInformation:
        mix.append(BasicImageInformation)
    if ImageCaptureMetadata:
        mix.append(ImageCaptureMetadata)
    if ImageAssessmentMetadata:
        mix.append(ImageAssessmentMetadata)

    return mix


def mix_BasicDigitalObjectInformation(
        byteOrder=None, Compression_elements=None):
    """Returns MIX BasicDigitalObjectInformation element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

    Returns the following ElementTree structure::

        <mix:BasicDigitalObjectInformation>
            <mix:byteOrder>big endian</mix:byteOrder>
            {{ Compression elements }}
        </mix:BasicDigitalObjectInformation>

    """

    mix_BasicDigitalObjectInformation = _element(
        'BasicDigitalObjectInformation')

    mix_byteorder = _subelement(mix_BasicDigitalObjectInformation, 'byteOrder')
    mix_byteorder.text = byteOrder
    if Compression_elements:
        for element in Compression_elements:
            mix_BasicDigitalObjectInformation.append(element)

    return mix_BasicDigitalObjectInformation


def mix_Compression(compressionScheme=None, compressionSchemeLocalList=None,
                    compressionSchemeLocalValue=None, compressionRatio=None):
    """Returns MIX Compression element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

    Returns the following ElementTree structure::

        <mix:Compression>
            <mix:compressionScheme>JPEG 2000 Lossless</mix:compressionScheme>
            <mix:compressionSchemeLocalList></mix:compressionSchemeLocalList>
            <mix:compressionSchemeLocalValue></mix:compressionSchemeLocalValue>
            <mix:compressionRatio>10</mix:compressionRatio>
        </mix:Compression>

    """
    mix_compression = _element('Compression')

    mix_compressionScheme = _subelement(mix_compression, 'compressionScheme')
    mix_compressionScheme.text = compressionScheme

    if compressionScheme == 'enumerated in local list':
        mix_compressionSchemeLocalList = _subelement(
            mix_compression, 'compressionSchemeLocalList')
        mix_compressionSchemeLocalList.text = compressionSchemeLocalList

    if compressionScheme == 'enumerated in local list':
        mix_compressionSchemeLocalValue = _subelement(
            mix_compression, 'compressionSchemeLocalValue')
        mix_compressionSchemeLocalValue.text = compressionSchemeLocalValue

    mix_compressionRatio = _subelement(mix_compression, 'compressionRatio')
    mix_compressionRatio.text = compressionRatio

    return mix_compression


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

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

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
    mix_BasicImageCharacteristics = _subelement(
        mix_BasicImageInformation, 'BasicImageCharacteristics')

    mix_imageWidth = _subelement(mix_BasicImageCharacteristics, 'imageWidth')
    mix_imageWidth.text = imageWidth

    mix_imageHeight = _subelement(mix_BasicImageCharacteristics, 'imageHeight')
    mix_imageHeight.text = imageHeight

    mix_PhotometricInterpretation = _subelement(mix_BasicImageCharacteristics,
                                                'PhotometricInterpretation')

    mix_colorSpace = _subelement(mix_PhotometricInterpretation, 'colorSpace')
    mix_colorSpace.text = colorSpace

    if iccProfileName:
        mix_ColorProfile = _subelement(
            mix_PhotometricInterpretation, 'ColorProfile')
        mix_IccProfile = _subelement(mix_ColorProfile, 'IccProfile')
        mix_iccProfileName = _subelement(mix_IccProfile, 'iccProfileName')
        mix_iccProfileName.text = iccProfileName

    if iccProfileVersion:
        mix_iccProfileVersion = _subelement(
            mix_IccProfile, 'iccProfileVersion')
        mix_iccProfileVersion.text = iccProfileVersion

    if iccProfileURI:
        mix_iccProfileURI = _subelement(mix_IccProfile, 'iccProfileURI')
        mix_iccProfileURI.text = iccProfileURI

    if localProfileName:
        mix_LocalProfile = _subelement(mix_ColorProfile, 'LocalProfile')
        mix_localProfileName = _subelement(
            mix_LocalProfile, 'localProfileName')
        mix_localProfileName.text = localProfileName

        mix_localProfileURL = _subelement(mix_LocalProfile, 'localProfileURL')
        mix_localProfileURL.text = localProfileURL

    if embeddedProfile:
        mix_embeddedProfile = _subelement(mix_ColorProfile, 'embeddedProfile')
        mix_embeddedProfile.text = embeddedProfile

    if yCbCrSubsampleHoriz:
        mix_YCbCr = _subelement(mix_PhotometricInterpretation, 'YCbCr')
        mix_YCbCrSubSampling = _subelement(mix_YCbCr, 'YCbCrSubSampling')
        mix_yCbCrSubsampleHoriz = _subelement(
            mix_YCbCrSubSampling, 'yCbCrSubsampleHoriz')
        mix_yCbCrSubsampleHoriz.text = yCbCrSubsampleHoriz

    if yCbCrSubsampleVert:
        mix_yCbCrSubsampleVert = _subelement(
            mix_YCbCrSubSampling, 'yCbCrSubsampleVert')
        mix_yCbCrSubsampleVert.text = yCbCrSubsampleVert

    if yCbCrPositioning:
        mix_yCbCrPositioning = _subelement(mix_YCbCr, 'yCbCrPositioning')
        mix_yCbCrPositioning.text = yCbCrPositioning

    if lumaRed:
        mix_YCbCrCoefficients = _subelement(mix_YCbCr, 'YCbCrCoefficients')
        mix_lumaRed = _subelement(mix_YCbCrCoefficients, 'lumaRed')
        mix_lumaRed.text = lumaRed

    if lumaGreen:
        mix_lumaGreen = _subelement(mix_YCbCrCoefficients, 'lumaGreen')
        mix_lumaGreen.text = lumaGreen

    if lumaBlue:
        mix_lumaBlue = _subelement(mix_YCbCrCoefficients, 'lumaBlue')
        mix_lumaBlue.text = lumaBlue

    if ReferenceBlackWhite_elements:
        for element in ReferenceBlackWhite_elements:
            mix_PhotometricInterpretation.append(element)

    if codec or codecVersion or codestreamProfile or complianceClass or tileWidth or tileHeight or qualityLayers or resolutionLevels or zoomLevels or djvuFormat:
        mix_SpecialFormatCharacteristics = _subelement(mix_BasicImageInformation,
                                                       'SpecialFormatCharacteristics')
    if codec or codecVersion or codestreamProfile or complianceClass or tileWidth or tileHeight or qualityLayers or resolutionLevels:
        mix_JPEG2000 = _subelement(
            mix_SpecialFormatCharacteristics, 'JPEG2000')

    if codec or codecVersion or codestreamProfile or complianceClass:
        mix_CodecCompliance = _subelement(mix_JPEG2000, 'CodecCompliance')

    if codec:
        mix_codec = _subelement(mix_CodecCompliance, 'codec')
        mix_codec.text = codec

    if codecVersion:
        mix_codecVersion = _subelement(mix_CodecCompliance, 'codecVersion')
        mix_codecVersion.text = codecVersion

    if codestreamProfile:
        mix_codestreamProfile = _subelement(
            mix_CodecCompliance, 'codestreamProfile')
        mix_codestreamProfile.text = codestreamProfile

    if complianceClass:
        mix_complianceClass = _subelement(
            mix_CodecCompliance, 'complianceClass')
        mix_complianceClass.text = complianceClass

    if tileWidth or tileHeight or qualityLayers or resolutionLevels:
        mix_EncodingOptions = _subelement(mix_JPEG2000, 'EncodingOptions')

    if tileWidth or tileHeight:
        mix_Tiles = _subelement(mix_EncodingOptions, 'Tiles')

    if tileWidth:
        mix_tileWidth = _subelement(mix_Tiles, 'tileWidth')
        mix_tileWidth.text = tileWidth

    if tileHeight:
        mix_tileHeight = _subelement(mix_Tiles, 'tileHeight')
        mix_tileHeight.text = tileHeight

    if qualityLayers:
        mix_qualityLayers = _subelement(mix_EncodingOptions, 'qualityLayers')
        mix_qualityLayers.text = qualityLayers

    if resolutionLevels:
        mix_resolutionLevels = _subelement(
            mix_EncodingOptions, 'resolutionLevels')
        mix_resolutionLevels.text = resolutionLevels

    if zoomLevels:
        mix_MrSID = _subelement(mix_SpecialFormatCharacteristics, 'MrSID')
        mix_zoomLevels = _subelement(mix_MrSID, 'zoomLevels')
        mix_zoomLevels.text = zoomLevels

    if djvuFormat:
        mix_Djvu = _subelement(mix_SpecialFormatCharacteristics, 'Djvu')
        mix_djvuFormat = _subelement(mix_Djvu, 'djvuFormat')
        mix_djvuFormat.text = djvuFormat

    return mix_BasicImageInformation


def mix_Component(
        componentPhotometricInterpretation=None, footroom=None, headroom=None):
    """Returns MIX Component element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

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

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)
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


def mix_ImageCaptureMetadata(sourceType=None, SourceID_elements=None,
                             sourceXDimensionValue=None, sourceXDimensionUnit=None,
                             sourceYDimensionValue=None, sourceYDimensionUnit=None,
                             sourceZDimensionValue=None, sourceZDimensionUnit=None,
                             dateTimeCreated=None, imageProducer_elements=None, captureDevice=None,
                             scannerManufacturer=None, scannerModelName=None,
                             scannerModelNumber=None, scannerModelSerialNo=None,
                             xOpticalResolution=None, yOpticalResolution=None,
                             opticalResolutionUnit=None, scannerSensor=None, scanningSoftwareName=None,
                             scanningSoftwareVersionNo=None, digitalCameraManufacturer=None,
                             DigitalCameraModelName=None, DigitalCameraModelNumber=None,
                             DigitalCameraModelSerialNo=None, cameraSensor=None, fNumber=None,
                             exposureTime=None, exposureProgram=None, spectralSensitivity_elements=None,
                             isoSpeedRatings=None, oECF=None, rationalType=None, exifVersion=None,
                             shutterSpeedValue=None, apertureValue=None, brightnessValue=None,
                             exposureBiasValue=None, maxApertureValue=None, distance=None,
                             minDistance=None, maxDistance=None, meteringMode=None,
                             lightSource=None, flash=None, focalLength=None, flashEnergy=None,
                             backLight=None, exposureIndex=None, sensingMethod=None,
                             cfaPattern=None, autoFocus=None, xPrintAspectRatio=None,
                             yPrintAspectRatio=None, gpsVersionID=None, gpsLatitudeRef=None,
                             GPSLatitude_element=None, gpsLongitudeRef=None,
                             GPSLongitude_element=None, gpsAltitudeRef=None, gpsAltitude=None,
                             gpsTimeStamp=None, gpsSatellites=None, gpsStatus=None,
                             gpsMeasureMode=None, gpsDOP=None, gpsSpeedRef=None, gpsSpeed=None,
                             gpsTrackRef=None, gpsTrack=None, gpsImgDirectionRef=None,
                             gpsImgDirection=None, gpsMapDatum=None, gpsDestLatitudeRef=None,
                             GPSDestLatitude_element=None, gpsDestLongitudeRef=None,
                             GPSDestLongitude_element=None, gpsDestBearingRef=None,
                             gpsDestBearing=None, gpsDestDistanceRef=None, gpsDestDistance=None,
                             gpsProcessingMethod=None, gpsAreaInformation=None, gpsDateStamp=None,
                             gpsDifferential=None, typeOfOrientationType=None, methodology=None):
    """Returns MIX ImageCaptureMetadata element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

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
            </mix:SourceInformation>
            <mix:GeneralCaptureInformation>
                <mix:dateTimeCreated></mix:dateTimeCreated>
                {{ imageProducer elements }}
                <mix:captureDevice></mix:captureDevice>
            </mix:GeneralCaptureInformation>
            <mix:ScannerCapture>
                <mix:scannerManufacturer></mix:scannerManufacturer>
                <mix:scannerModel>
                    <mix:scannerModelName></mix:scannerModelName>
                    <mix:scannerModelNumber></mix:scannerModelNumber>
                    <mix:scannerModelSerialNo></mix:scannerModelSerialNo>
                </mix:scannerModel>
                <mix:MaximumOpticalResolution>
                    <mix:xOpticalResolution></mix:xOpticalResolution>
                    <mix:yOpticalResolution></mix:yOpticalResolution>
                    <mix:opticalResolutionUnit></mix:opticalResolutionUnit>
                </mix:MaximumOpticalResolution>
                <mix:scannerSensor></mix:scannerSensor>
                <mix:ScanningSystemSoftware>
                    <mix:scanningSoftwareName></mix:scanningSoftwareName>
                    <mix:scanningSoftwareVersionNo></mix:scanningSoftwareVersionNo>
                </mix:ScanningSystemSoftware>
            </mix:ScannerCapture>
            <mix:DigitalCameraCapture>
                <mix:digitalCameraManufacturer></mix:digitalCameraManufacturer>
                <mix:DigitalCameraModel>
                    <mix:DigitalCameraModelName></mix:DigitalCameraModelName>
                    <mix:DigitalCameraModelNumber></mix:DigitalCameraModelNumber>
                    <mix:DigitalCameraModelSerialNo></mix:DigitalCameraModelSerialNo>
                </mix:DigitalCameraModel>
                <mix:cameraSensor></mix:cameraSensor>
                <mix:CameraCaptureSettings>
                    <mix:ImageData>
                        <mix:fNumber></mix:fNumber>
                        <mix:exposureTime></mix:exposureTime>
                        <mix:spectralSensitivity></mix:spectralSensitivity>
                        <mix:isoSpeedRatings></mix:isoSpeedRatings>
                        <mix:oECF></mix:oECF>
                        <mix:exifVersion></mix:exifVersion>
                        <mix:shutterSpeedValue></mix:shutterSpeedValue>
                        <mix:apertureValue></mix:apertureValue>
                        <mix:brightnessValue></mix:brightnessValue>
                        <mix:exposureBiasValue></mix:exposureBiasValue>
                        <mix:maxApertureValue></mix:maxApertureValue>
                        <mix:SubjectDistance>
                            <mix:distance></mix:distance>
                            <mix:MinMaxDistance>
                                <mix:minDistance></mix:minDistance>
                                <mix:maxDistance></mix:maxDistance>
                            </mix:MinMaxDistance>
                        </mix:SubjectDistance>
                        <mix:meteringMode></mix:meteringMode>
                        <mix:lightSource></mix:lightSource>
                        <mix:flash></mix:flash>
                        <mix:focalLength></mix:focalLength>
                        <mix:flashEnergy></mix:flashEnergy>
                        <mix:backLight></mix:backLight>
                        <mix:exposureIndex></mix:exposureIndex>
                        <mix:sensingMethod></mix:sensingMethod>
                        <mix:cfaPattern></mix:cfaPattern>
                        <mix:autoFocus></mix:autoFocus>
                        <mix:PrintAspectRatio>
                            <mix:xPrintAspectRatio></mix:xPrintAspectRatio>
                            <mix:yPrintAspectRatio></mix:yPrintAspectRatio>
                        </mix:PrintAspectRatio>
                        <mix:GPSData>
                            <mix:gpsVersionID></mix:gpsVersionID>
                            <mix:gpsLatitudeRef></mix:gpsLatitudeRef>
                            {{ GPSLatitude gpsGroup element }}
                            <mix:gpsLongitudeRef></mix:gpsLongitudeRef>
                            {{ GPSLongitude gpsGroup element }}
                            <mix:gpsAltitudeRef></mix:gpsAltitudeRef>
                            <mix:gpsAltitude></mix:gpsAltitude>
                            <mix:gpsTimeStamp></mix:gpsTimeStamp>
                            <mix:gpsSatellites></mix:gpsSatellites>
                            <mix:gpsStatus></mix:gpsStatus>
                            <mix:gpsMeasureMode></mix:gpsMeasureMode>
                            <mix:gpsDOP></mix:gpsDOP>
                            <mix:gpsSpeedRef></mix:gpsSpeedRef>
                            <mix:gpsSpeed></mix:gpsSpeed>
                            <mix:gpsTrackRef></mix:gpsTrackRef>
                            <mix:gpsTrack></mix:gpsTrack>
                            <mix:gpsImgDirectionRef></mix:gpsImgDirectionRef>
                            <mix:gpsImgDirection></mix:gpsImgDirection>
                            <mix:gpsMapDatum></mix:gpsMapDatum>
                            <mix:gpsDestLatitudeRef></mix:gpsDestLatitudeRef>
                            {{ GPSDestLatitude gpsGroup element }}
                            <mix:gpsDestLongitudeRef></mix:gpsDestLongitudeRef>
                            {{ GPSDestLongitude gpsGroup element }}
                            <mix:gpsDestBearingRef></mix:gpsDestBearingRef>
                            <mix:gpsDestBearing></mix:gpsDestBearing>
                            <mix:gpsDestDistanceRef></mix:gpsDestDistanceRef>
                            <mix:gpsDestDistance></mix:gpsDestDistance>
                            <mix:gpsProcessingMethod></mix:gpsProcessingMethod>
                            <mix:gpsAreaInformation></mix:gpsAreaInformation>
                            <mix:gpsDateStamp></mix:gpsDateStamp>
                            <mix:gpsDifferential></mix:gpsDifferential>
                        </mix:GPSData>


                        <mix:orientation></mix:orientation>
                        <mix:methodology></mix:methodology>

                    </mix:ImageData>



                </mix:CameraCaptureSettings>
            </mix:DigitalCameraCapture>
        </mix:ImageCaptureMetadata>

    """
    mix_ImageCaptureMetadata = _element('ImageCaptureMetadata')
    mix_SourceInformation = _subelement(
        mix_ImageCaptureMetadata, 'SourceInformation')
    mix_sourceType = _subelement(mix_SourceInformation, 'sourceType')
    mix_sourceType.text = sourceType

    if SourceID_elements:
        for element in SourceID_elements:
            mix_SourceInformation.append(element)

    mix_SourceSize = _subelement(mix_SourceInformation, 'SourceSize')
    mix_SourceXDimension = _subelement(
        mix_SourceInformation, 'SourceXDimension')
    mix_sourceXDimensionValue = _subelement(mix_SourceXDimension,
                                            'sourceXDimensionValue')
    mix_sourceXDimensionValue.text = sourceXDimensionValue
    mix_sourceXDimensionUnit = _subelement(mix_SourceXDimension,
                                           'sourceXDimensionUnit')
    mix_sourceXDimensionUnit.text = sourceXDimensionUnit

    mix_SourceYDimension = _subelement(
        mix_SourceInformation, 'SourceYDimension')
    mix_sourceYDimensionValue = _subelement(mix_SourceYDimension,
                                            'sourceYDimensionValue')
    mix_sourceYDimensionValue.text = sourceYDimensionValue
    mix_sourceYDimensionUnit = _subelement(mix_SourceYDimension,
                                           'sourceYDimensionUnit')
    mix_sourceYDimensionUnit.text = sourceYDimensionUnit

    mix_SourceZDimension = _subelement(
        mix_SourceInformation, 'SourceZDimension')
    mix_sourceZDimensionValue = _subelement(mix_SourceZDimension,
                                            'sourceZDimensionValue')
    mix_sourceZDimensionValue.text = sourceZDimensionValue
    mix_sourceZDimensionUnit = _subelement(mix_SourceZDimension,
                                           'sourceZDimensionUnit')
    mix_sourceZDimensionUnit.text = sourceZDimensionUnit

    mix_GeneralCaptureInformation = _subelement(mix_ImageCaptureMetadata,
                                                'GeneralCaptureInformation')
    mix_dateTimeCreated = _subelement(
        mix_GeneralCaptureInformation, 'dateTimeCreated')
    mix_dateTimeCreated.text = dateTimeCreated

    if imageProducer_elements:
        for element in imageProducer_elements:
            mix_imageProducer = _subelement(mix_GeneralCaptureInformation,
                                            'imageProducer')
            mix_imageProducer.text = element

    mix_captureDevice = _subelement(mix_GeneralCaptureInformation,
                                    'captureDevice')
    mix_captureDevice.text = captureDevice

    mix_ScannerCapture = _subelement(
        mix_ImageCaptureMetadata, 'ScannerCapture')
    mix_scannerManufacturer = _subelement(mix_ScannerCapture,
                                          'scannerManufacturer')
    mix_scannerManufacturer.text = scannerManufacturer
    mix_scannerModel = _subelement(mix_ScannerCapture, 'scannerModel')

    mix_scannerModelName = _subelement(mix_scannerModel, 'scannerModelName')
    mix_scannerModelName.text = scannerModelName

    mix_scannerModelNumber = _subelement(
        mix_scannerModel, 'scannerModelNumber')
    mix_scannerModelNumber.text = scannerModelNumber

    mix_scannerModelSerialNo = _subelement(mix_scannerModel,
                                           'scannerModelSerialNo')
    mix_scannerModelSerialNo.text = scannerModelSerialNo

    mix_MaximumOpticalResolution = _subelement(mix_ScannerCapture,
                                               'MaximumOpticalResolution')
    mix_xOpticalResolution = _subelement(
        mix_MaximumOpticalResolution, 'xOpticalResolution')
    mix_xOpticalResolution.text = xOpticalResolution

    mix_yOpticalResolution = _subelement(
        mix_MaximumOpticalResolution, 'yOpticalResolution')
    mix_yOpticalResolution.text = yOpticalResolution

    mix_opticalResolutionUnit = _subelement(mix_MaximumOpticalResolution,
                                            'opticalResolutionUnit')
    mix_opticalResolutionUnit.text = opticalResolutionUnit

    mix_scannerSensor = _subelement(mix_ScannerCapture, 'scannerSensor')
    mix_scannerSensor.text = scannerSensor

    mix_ScanningSystemSoftware = _subelement(mix_ScannerCapture,
                                             'ScanningSystemSoftware')
    mix_scanningSoftwareVersionNo = _subelement(mix_ScannerCapture,
                                                'scanningSoftwareVersionNo')

    mix_DigitalCameraCapture = _subelement(mix_ImageCaptureMetadata,
                                           'DigitalCameraCapture')
    mix_digitalCameraManufacturer = _subelement(mix_DigitalCameraCapture,
                                                'digitalCameraManufacturer')
    mix_digitalCameraManufacturer.text = digitalCameraManufacturer

    mix_DigitalCameraModel = _subelement(mix_DigitalCameraCapture,
                                         'DigitalCameraModel')
    mix_digitalCameraModelName = _subelement(mix_DigitalCameraModel,
                                             'DigitalCameraModelName')
    mix_digitalCameraModelName.text = digitalCameraModelName

    mix_digitalCameraModelNumber = _subelement(mix_DigitalCameraModel,
                                               'DigitalCameraModelNumber')
    mix_digitalCameraModelNumber.text = digitalCameraModelNumber

    mix_digitalCameraModelSerialNo = _subelement(mix_DigitalCameraModel,
                                                 'DigitalCameraModelSerialNo')
    mix_digitalCameraModelSerialNo.text = digitalCameraModelSerialNo

    mix_cameraSensor = _subelement(mix_ImageCaptureMetadata,
                                   'cameraSensor')
    mix_cameraSensor.text = cameraSensor

    mix_CameraCaptureSettings = _subelement(mix_ImageCaptureMetadata,
                                            'CameraCaptureSettings')
    mix_ImageData = _subelement(mix_CameraCaptureSettings,
                                'ImageData')

    mix_fNumber = _subelement(mix_ImageData, 'fNumber')
    mix_fNumber.text = fNumber

    mix_exposureTime = _subelement(mix_ImageData, 'exposureTime')
    mix_exposureTime.text = exposureTime

    if spectralSensitivity_elements:
        for element in spectralSensitivity_elements:
            mix_spectralSensitivity = _subelement(
                mix_ImageData, 'spectralSensitivity')
            mix_spectralSensitivity.text = element

    mix_isoSpeedRatings = _subelement(mix_ImageData, 'isoSpeedRatings')
    mix_isoSpeedRatings.text = isoSpeedRatings

    mix_oECF = _subelement(mix_ImageData, 'oECF')
    mix_oECF.text = oECF

    mix_exifVersion = _subelement(mix_ImageData, 'exifVersion')
    mix_exifVersion.text = exifVersion

    mix_shutterSpeedValue = _subelement(mix_ImageData, 'shutterSpeedValue')
    mix_shutterSpeedValue.text = shutterSpeedValue

    mix_apertureValue = _subelement(mix_ImageData, 'apertureValue')
    mix_apertureValue.text = apertureValue

    mix_brightnessValue = _subelement(mix_ImageData, 'brightnessValue')
    mix_brightnessValue.text = brightnessValue

    mix_exposureBiasValue = _subelement(mix_ImageData, 'exposureBiasValue')
    mix_exposureBiasValue.text = exposureBiasValue

    mix_maxApertureValue = _subelement(mix_ImageData, 'maxApertureValue')
    mix_maxApertureValue.text = maxApertureValue

    mix_SubjectDistance = _subelement(mix_ImageData, 'SubjectDistance')
    mix_distance = _subelement(mix_SubjectDistance, 'distance')
    mix_distance.text = distance

    mix_MinMaxDistance = _subelement(mix_SubjectDistance, 'MinMaxDistance')
    mix_minDistance = _subelement(mix_MinMaxDistance, 'minDistance')
    mix_minDistance.text = minDistance
    mix_maxDistance = _subelement(mix_MinMaxDistance, 'maxDistance')
    mix_maxDistance.text = maxDistance

    mix_meteringMode = _subelement(mix_ImageData, 'meteringMode')
    mix_meteringMode.text = meteringMode

    mix_lightSource = _subelement(mix_ImageData, 'lightSource')
    mix_lightSource.text = lightSource

    mix_flash = _subelement(mix_ImageData, 'flash')
    mix_flash.text = flash

    mix_focalLength = _subelement(mix_ImageData, 'focalLength')
    mix_focalLength.text = focalLength

    mix_flashEnergy = _subelement(mix_ImageData, 'flashEnergy')
    mix_flashEnergy.text = flashEnergy

    mix_backLight = _subelement(mix_ImageData, 'backLight')
    mix_backLight.text = backLight

    mix_exposureIndex = _subelement(mix_ImageData, 'exposureIndex')
    mix_exposureIndex.text = exposureIndex

    mix_sensingMethod = _subelement(mix_ImageData, 'sensingMethod')
    mix_sensingMethod.text = sensingMethod

    mix_cfaPattern = _subelement(mix_ImageData, 'cfaPattern')
    mix_cfaPattern.text = cfaPattern

    mix_autoFocus = _subelement(mix_ImageData, 'autoFocus')
    mix_autoFocus.text = autoFocus

    mix_PrintAspectRatio = _subelement(mix_ImageData, 'PrintAspectRatio')
    mix_xPrintAspectRatio = _subelement(mix_ImageData, 'xPrintAspectRatio')
    mix_xPrintAspectRatio.text = xPrintAspectRatio
    mix_yPrintAspectRatio = _subelement(mix_ImageData, 'yPrintAspectRatio')
    mix_yPrintAspectRatio.text = yPrintAspectRatio

    mix_GPSData = _element('GPSData')
    mix_gpsVersionID = _subelement(mix_GPSData, 'gpsVersionID')
    mix_gpsVersionID.text = gpsVersionID

    mix_gpsLatitudeRef = _subelement(mix_GPSData, 'gpsLatitudeRef')
    mix_gpsLatitudeRef.text = gpsLatitudeRef

    if GPSLatitude_element:
        mix_GPSData.append(GPSLatitude_element)

    mix_gpsLongitudeRef = _subelement(mix_GPSData, 'gpsLongitudeRef')
    mix_gpsLongitudeRef.text = gpsLongitudeRef

    if GPSLongitude_element:
        mix_GPSData.append(GPSLongitude_element)

    mix_gpsAltitudeRef = _subelement(mix_GPSData, 'gpsAltitudeRef')
    mix_gpsAltitudeRef.text = gpsAltitudeRef

    mix_gpsAltitude = _subelement(mix_GPSData, 'gpsAltitude')
    mix_gpsAltitude.text = gpsAltitude

    mix_gpsTimeStamp = _subelement(mix_GPSData, 'gpsTimeStamp')
    mix_gpsTimeStamp.text = gpsTimeStamp

    mix_gpsSatellites = _subelement(mix_GPSData, 'gpsSatellites')
    mix_gpsSatellites.text = gpsSatellites

    mix_gpsStatus = _subelement(mix_GPSData, 'gpsStatus')
    mix_gpsStatus.text = gpsStatus

    mix_gpsMeasureMode = _subelement(mix_GPSData, 'gpsMeasureMode')
    mix_gpsMeasureMode.text = gpsMeasureMode

    mix_gpsDOP = _subelement(mix_GPSData, 'gpsDOP')
    mix_gpsDOP.text = gpsDOP

    mix_gpsSpeedRef = _subelement(mix_GPSData, 'gpsSpeedRef')
    mix_gpsSpeedRef.text = gpsSpeedRef

    mix_gpsSpeed = _subelement(mix_GPSData, 'gpsSpeed')
    mix_gpsSpeed.text = gpsSpeed

    mix_gpsTrackRef = _subelement(mix_GPSData, 'gpsTrackRef')
    mix_gpsTrackRef.text = gpsTrackRef

    mix_gpsTrack = _subelement(mix_GPSData, 'gpsTrack')
    mix_gpsTrack.text = gpsTrack

    mix_gpsImgDirectionRef = _subelement(mix_GPSData, 'gpsImgDirectionRef')
    mix_gpsImgDirectionRef.text = gpsImgDirectionRef

    mix_gpsImgDirection = _subelement(mix_GPSData, 'gpsImgDirection')
    mix_gpsImgDirection.text = gpsImgDirection

    mix_gpsMapDatum = _subelement(mix_GPSData, 'gpsMapDatum')
    mix_gpsMapDatum.text = gpsMapDatum

    mix_gpsDestLatitudeRef = _subelement(mix_GPSData, 'gpsDestLatitudeRef')
    mix_gpsDestLatitudeRef.text = gpsDestLatitudeRef

    if GPSDestLatitude_element:
        mix_GPSData.append(GPSDestLatitude_element)

    mix_gpsDestLongitudeRef = _subelement(mix_GPSData, 'gpsDestLongitudeRef')
    mix_gpsDestLongitudeRef.text = gpsDestLongitudeRef

    if gpsDestLongitude_element:
        mix_GPSData.append(gpsDestLongitude_element)

    mix_gpsDestBearingRef = _subelement(mix_GPSData, 'gpsDestBearingRef')
    mix_gpsDestBearingRef.text = gpsDestBearingRef

    mix_gpsDestBearing = _subelement(mix_GPSData, 'gpsDestBearing')
    mix_gpsDestBearing.text = gpsDestBearing

    mix_gpsDestDistanceRef = _subelement(mix_GPSData, 'gpsDestDistanceRef')
    mix_gpsDestDistanceRef.text = gpsDestDistanceRef

    mix_gpsDestDistance = _subelement(mix_GPSData, 'gpsDestDistance')
    mix_gpsDestDistance.text = gpsDestDistance

    mix_gpsProcessingMethod = _subelement(mix_GPSData, 'gpsProcessingMethod')
    mix_gpsProcessingMethod.text = gpsProcessingMethod

    mix_gpsAreaInformation = _subelement(mix_GPSData, 'gpsAreaInformation')
    mix_gpsAreaInformation.text = gpsAreaInformation

    mix_gpsDateStamp = _subelement(mix_GPSData, 'gpsDateStamp')
    mix_gpsDateStamp.text = gpsDateStamp

    mix_gpsDifferential = _subelement(mix_GPSData, 'gpsDifferential')
    mix_gpsDifferential.text = gpsDifferential

    mix_orientation = _subelement(mix_ImageData, 'orientation')
    mix_orientation.text = orientation

    mix_methodology = _subelement(mix_ImageData, 'methodology')
    mix_methodology.text = methodology

    return mix_ImageCaptureMetadata


def mix_SourceID(sourceIDType=None, sourceIDValue=None):
    """Returns MIX sourceID element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

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

    return mix_sourceID


def mix_gpsGroup(degrees=None, minutes=None, seconds=None):
    """Returns MIX gpsGroup element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

    Returns the following ElementTree structure::

        <mix:gpsGroup>
            <mix:degrees></mix:degrees>
            <mix:minutes></mix:minutes>
            <mix:seconds></mix:seconds>
        </mix:sourceID>

    """
    mix_gpsGroup = _element('gpsGroup')
    mix_degrees = _subelement(mix_gpsGroup, 'degrees')
    mix_degrees.text = degrees

    mix_minutes = _subelement(mix_gpsGroup, 'minutes')
    mix_minutes.text = minutes

    mix_seconds = _subelement(mix_gpsGroup, 'seconds')
    mix_seconds.text = seconds

    return mix_gpsGroup


def mix_ImageAssessmentMetadata(samplingFrequencyPlane=None,
                                samplingFrequencyUnit=None, xSamplingFrequency=None,
                                ySamplingFrequency=None, bitsPerSampleValue_elements=None,
                                bitsPerSampleUnit=None, samplesPerPixel=None, extraSamples_elements=None,
                                colormapReference=None, embeddedColormap=None,
                                grayResponseCurve_elements=None, grayResponseUnit=None,
                                WhitePoint_elements=None,
                                PrimaryChromaticities_elements=None, targetType_elements=None,
                                TargetID_elements=None, externalTarget_elements=None,
                                performanceData_elements=None):
    """Returns MIX ImageAssessmentMetadata element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

    Returns the following ElementTree structure::

        <mix:ImageAssessmentMetadata>
            <mix:SpatialMetrics>
                <mix:samplingFrequencyPlane></mix:samplingFrequencyPlane>
                <mix:samplingFrequencyUnit></mix:samplingFrequencyUnit>
                <mix:xSamplingFrequency></mix:xSamplingFrequency>
                <mix:ySamplingFrequency></mix:ySamplingFrequency>
            </mix:SpatialMetrics>
            <mix:ImageColorEncoding>
                <mix:BitsPerSample>
                    <mix:bitsPerSampleValue></mix:bitsPerSampleValue>
                    <mix:bitsPerSampleUnit></mix:bitsPerSampleUnit>
                </mix:BitsPerSample>
                <mix:samplesPerPixel></mix:samplesPerPixel>
                <mix:extraSamples></mix:extraSamples>
                <mix:Colormap>
                    <mix:colormapReference></mix:colormapReference>
                    <mix:embeddedColormap></mix:embeddedColormap>
                </mix:Colormap>
                <mix:GrayResponse>
                    <mix:grayResponseCurve></mix:grayResponseCurve>
                    <mix:grayResponseUnit></mix:grayResponseUnit>
                </mix:GrayResponse>
                {{ WhitePoint elements }}
                {{ PrimaryChromaticities elements }}

            </mix:ImageColorEncoding>
            <mix:TargetData>
                <mix:targetType></mix:targetType>
                {{ TargetID  elements }}
                <mix:externalTarget></mix:externalTarget>
                <mix:performanceData></mix:performanceData>
            </mix:TargetData>
        </mix:ImageAssessmentMetadata>

    """
    mix_ImageAssessmentMetadata = _element('ImageAssessmentMetadata')
    mix_SpatialMetrics = _subelement(
        mix_ImageAssessmentMetadata, 'SpatialMetrics')

    if samplingFrequencyPlane:
        mix_samplingFrequencyPlane = _subelement(
            mix_SpatialMetrics, 'samplingFrequencyPlane')
        mix_samplingFrequencyPlane.text = samplingFrequencyPlane

    if samplingFrequencyUnit:
        mix_samplingFrequencyUnit = _subelement(
            mix_SpatialMetrics, 'samplingFrequencyUnit')
        mix_samplingFrequencyUnit.text = samplingFrequencyUnit

    if xSamplingFrequency:
        mix_xSamplingFrequency = _subelement(
            mix_SpatialMetrics, 'xSamplingFrequency')
        mix_xSamplingFrequency.text = xSamplingFrequency

    if ySamplingFrequency:
        mix_ySamplingFrequency = _subelement(
            mix_SpatialMetrics, 'ySamplingFrequency')
        mix_ySamplingFrequency.text = ySamplingFrequency

    mix_ImageColorEncoding = _subelement(
        mix_ImageAssessmentMetadata, 'ImageColorEncoding')
    mix_BitsPerSample = _subelement(mix_ImageColorEncoding, 'BitsPerSample')
    if bitsPerSampleValue_elements:
        for element in bitsPerSampleValue_elements:
            mix_bitsPerSampleValue = _subelement(
                mix_BitsPerSample, 'bitsPerSampleValue')
            mix_bitsPerSampleValue.text = element

    mix_bitsPerSampleUnit = _subelement(mix_BitsPerSample, 'bitsPerSampleUnit')
    mix_bitsPerSampleUnit.text = bitsPerSampleUnit

    mix_samplesPerPixel = _subelement(
        mix_ImageColorEncoding, 'samplesPerPixel')
    mix_samplesPerPixel.text = samplesPerPixel

    if extraSamples_elements:
        for element in extraSamples_elements:
            mix_extraSamples = _subelement(
                mix_ImageColorEncoding, 'extraSamples')
            mix_extraSamples.text = element

    mix_Colormap = _subelement(mix_ImageColorEncoding, 'Colormap')
    if colormapReference:
        mix_colormapReference = _subelement(mix_Colormap, 'colormapReference')
        mix_colormapReference.text = colormapReference

    if embeddedColormap:
        mix_embeddedColormap = _subelement(mix_Colormap, 'embeddedColormap')
        mix_embeddedColormap.text = embeddedColormap

    if grayResponseCurve_elements or grayResponseUnit:
        mix_GrayResponse = _subelement(mix_ImageColorEncoding, 'GrayResponse')

    if grayResponseCurve_elements:
        for element in grayResponseCurve_elements:
            mix_grayResponseCurve = _subelement(mix_GrayResponse,
                                                'grayResponseCurve')
            mix_grayResponseCurve.text = element

    if grayResponseUnit:
        mix_grayResponseUnit = _subelement(
            mix_GrayResponse, 'grayResponseUnit')
        mix_grayResponseUnit.text = grayResponseUnit

    if WhitePoint_elements:
        for element in WhitePoint_elements:
            mix_ImageColorEncoding.append(element)

    if PrimaryChromaticities_elements:
        for element in PrimaryChromaticities_elements:
            mix_ImageColorEncoding.append(element)

    if targetType_elements or TargetID_elements or externalTarget_elements or performanceData_elements:
        mix_TargetData = _subelement(mix_ImageAssessmentMetadata, 'TargetData')

    if targetType_elements:
        for element in targetType_elements:
            mix_targetType = _subelement(mix_TargetData, 'targetType')
            mix_targetType.text = element

    if TargetID_elements:
        for element in TargetID_elements:
            mix_TargetData.append(element)

    if externalTarget_elements:
        for element in externalTarget_elements:
            mix_externalTarget = _subelement(mix_TargetData, 'externalTarget')
            mix_externalTarget.text = element

    if performanceData_elements:
        for element in performanceData_elements:
            mix_performanceData = _subelement(
                mix_TargetData, 'performanceData')
            mix_performanceData.text = element

    return mix_ImageAssessmentMetadata


def mix_WhitePoint(whitePointXValue=None, whitePointYValue=None):
    """Returns MIX gpsGroup element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

    Returns the following ElementTree structure::

        <mix:WhitePoint>
            <mix:whitePointXValue></mix:whitePointXValue>
            <mix:whitePointYValue></mix:whitePointYValue>
        </mix:WhitePoint>

    """
    mix_WhitePoint = _element('WhitePoint')
    mix_whitePointXValue = _subelement(mix_WhitePoint, 'whitePointXValue')
    mix_whitePointXValue.text = whitePointXValue

    mix_whitePointYValue = _subelement(mix_WhitePoint, 'whitePointYValue')
    mix_whitePointYValue.text = whitePointYValue

    return mix_WhitePoint


def mix_PrimaryChromaticities(primaryChromaticitiesRedX=None,
                              primaryChromaticitiesRedY=None, primaryChromaticitiesGreenX=None,
                              primaryChromaticitiesGreenY=None, primaryChromaticitiesBlueX=None,
                              primaryChromaticitiesBlueY=None):
    """Returns MIX PrimaryChromaticities element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

    Returns the following ElementTree structure::

        <mix:PrimaryChromaticities>
            <mix:primaryChromaticitiesRedX></mix:primaryChromaticitiesRedX>
            <mix:primaryChromaticitiesRedY></mix:primaryChromaticitiesRedY>
            <mix:primaryChromaticitiesGreenX></mix:primaryChromaticitiesGreenX>
            <mix:primaryChromaticitiesGreenY></mix:primaryChromaticitiesGreenY>
            <mix:primaryChromaticitiesBlueX></mix:primaryChromaticitiesBlueX>
            <mix:primaryChromaticitiesBlueY></mix:primaryChromaticitiesBlueY>
        </mix:PrimaryChromaticities>

    """
    mix_PrimaryChromaticities = _element('PrimaryChromaticities')
    mix_primaryChromaticitiesRedX = _subelement(mix_PrimaryChromaticities,
                                                'primaryChromaticitiesRedX')
    mix_primaryChromaticitiesRedX.text = primaryChromaticitiesRedX

    mix_primaryChromaticitiesRedY = _subelement(mix_PrimaryChromaticities,
                                                'primaryChromaticitiesRedY')
    mix_primaryChromaticitiesRedY.text = primaryChromaticitiesRedY

    mix_primaryChromaticitiesGreenX = _subelement(
        mix_PrimaryChromaticities, 'primaryChromaticitiesGreenX')
    mix_primaryChromaticitiesGreenX.text = primaryChromaticitiesGreenX

    mix_primaryChromaticitiesGreenY = _subelement(
        mix_PrimaryChromaticities, 'primaryChromaticitiesGreenY')
    mix_primaryChromaticitiesGreenY.text = primaryChromaticitiesGreenY

    mix_primaryChromaticitiesBlueX = _subelement(mix_PrimaryChromaticities,
                                                 'primaryChromaticitiesBlueX')
    mix_primaryChromaticitiesBlueX.text = primaryChromaticitiesBlueX

    mix_primaryChromaticitiesBlueY = _subelement(mix_PrimaryChromaticities,
                                                 'primaryChromaticitiesBlueY')
    mix_primaryChromaticitiesBlueY.text = primaryChromaticitiesBlueY

    return mix_PrimaryChromaticities


def mix_TargetID(targetManufacturer=None, targetName=None, targetNo=None,
                 targetMedia=None):
    """Returns MIX TargetID element

    :Schema documentation: Data Dictionary - Technical Metadata for Digital Still Images (ANSI/NISO Z39.87-2006)

    Returns the following ElementTree structure::

        <mix:TargetID>
            <mix:targetManufacturer></mix:targetManufacturer>
            <mix:targetName></mix:targetName>
            <mix:targetNo></mix:targetNo>
            <mix:targetMedia></mix:targetMedia>
        </mix:TargetID>

    """
    mix_TargetID = _element('TargetID')
    mix_targetManufacturer = _subelement(mix_TargetID, 'targetManufacturer')
    mix_targetManufacturer.text = targetManufacturer

    mix_targetName = _subelement(mix_TargetID, 'targetName')
    mix_targetName.text = targetName

    mix_targetNo = _subelement(mix_TargetID, 'targetNo')
    mix_targetNo.text = targetNo

    mix_targetMedia = _subelement(mix_TargetID, 'targetMedia')
    mix_targetMedia.text = targetMedia

    return mix_TargetID
