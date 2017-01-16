"""Functions for reading and generating PREMIS Data Dictionaries as
xml.etree.ElementTree data structures.

References:

    * PREMIS http://www.loc.gov/standards/premis/
    * ElementTree
    https://docs.python.org/2.6/library/xml.etree.elementtree.html

"""


import json

import xml.etree.ElementTree as ET

import siptools.xml.xmlutil

PREMIS_NS = 'info:lc/xmlns/premis-v2'
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

    register_namespace('premis', PREMIS_NS)
    register_namespace('xsi', XSI_NS)

    siptools.xml.xmlutil.indent(root_element)

    return ET.tostring(root_element)


def premis_ns(tag, prefix=""):
    """Prefix ElementTree tags with PREMIS namespace.

    object -> {info:lc...premis}object

    :tag: Tag name as string
    :returns: Prefixed tag

    """
    if prefix:
        tag = tag[0].upper() + tag[1:]
        return '{%s}%s%s' % (PREMIS_NS, prefix, tag)
    return '{%s}%s' % (PREMIS_NS, tag)


def xsi_ns(tag):
    """Prefix ElementTree tags with XSI namespace.

    object -> {info:lc...premis}object

    :tag: Tag name as string
    :returns: Prefixed tag

    """
    return '{%s}%s' % (XSI_NS, tag)


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
    return ET.Element(premis_ns(tag, prefix))


def _subelement(parent, tag, prefix=""):
    """Return subelement for the given parent element. Created element is
    appelded to parent element.

    :parent: Parent element
    :tag: Element tagname
    :prefix: Prefix for the tag
    :returns: Created subelement

    """
    return ET.SubElement(parent, premis_ns(tag, prefix))


def premis_identifier(identifier_type, identifier_value, prefix=""):
    """Return PREMIS identifier segments.

    Produces without prefix the following PREMIS segment::


          <premis:objectIdentifier>
              <premis:objectIdentifierType>
                  preservation-sig-id
              </premis:objectIdentifierType>
              <premis:objectIdentifierValue>
                  c8b978b6-e160-4497-8027-e19fa0297766
              </premis:objectIdentifierValue>
          </premis:objectIdentifier>

    With prefix='relatedObject' the following PREMIS segment::

          <premis:relatedObjectIdentification>
              <premis:relatedObjectIdentifierType>
                  preservation-sip-id
              </premis:relatedObjectIdentifierType>
              <premis:relatedObjectIdentifierValue>
                  1ac641ec-223f-42f4-86c2-9402451d63bf
              </premis:relatedObjectIdentifierValue>
          </premis:relatedObjectIdentification>

    With prefix='dependency' the following PREMIS segment::

        <premis:dependencyIdentifier>
            <premis:dependencyIdentifierType>
                local</premis:dependencyIdentifierType>
            <premis:dependencyIdentifierValue>
                kdk-sip-premis-object001</premis:dependencyIdentifierValue>
        </premis:dependencyIdentifier>

    With prefix='linking' the following PREMIS segment::

        <premis:linkingObjectIdentifier>
            <premis:linkingObjectIdentifierType>
                preservation-sip-id</premis:linkingObjectIdentifierType>
            <premis:linkingObjectIdentifierValue>
                1ac641ec</premis:linkingObjectIdentifierValue>
        </premis:linkingObjectIdentifier>

    """

    if not prefix:
        prefix = 'object'

    if prefix == 'relatedObject':
        _identifier = _element('Identification', prefix)
    else:
        _identifier = _element('Identifier', prefix)

    _value = _subelement(_identifier, 'IdentifierType', prefix)
    _value.text = identifier_type

    _type = _subelement(_identifier, 'IdentifierValue', prefix)
    _type.text = identifier_value

    return _identifier


def get_identifier_type_value(object_or_identifier):
    """Return identifierType and IdentifierValue from given PREMIS identifier
    or object. If segment contains multiple identifiers, returns first
    occurrence.

    :object_or_identifier: Premis object or identifier
    :returns: (identifier_type, identifier_value)

    """

    identifier = object_or_identifier

    if identifier.find(premis_ns('objectIdentifier')) is not None:
        identifier = identifier.find(premis_ns('objectIdentifier'))

    if identifier.find(premis_ns('relatedObjectIdentification')) is not None:
        identifier = identifier.find(premis_ns('relatedObjectIdentification'))

    return (
        identifier.find(premis_ns('objectIdentifierType')).text,
        identifier.find(premis_ns('objectIdentifierValue')).text)


def premis_relationship(
        relationship_type, relationship_subtype,
        related_object):

    """Create PREMIS relationship DOM segment.

    :relationship_type: Relationship type from PREMIS vocabulary
    :relationship_subtype: Relationship subtype from PREMIS vocabulary
    :related_object: Related object linked to relationship
    :returns: ElementTree DOM tree

    Produces the following PREMIS segment::

      <premis:relationship>

          <premis:relationshipType>structural</premis:relationshipType>
          <premis:relationshipSubType>
              is included in
          </premis:relationshipSubType>

          {{ premis_identifier(prefix=related) }}

      </premis:relationship>

    """

    relationship = _element('relationship')

    _type = _subelement(relationship, 'relationshipType')
    _type.text = relationship_type

    _subtype = _subelement(relationship, 'relationshipSubType')
    _subtype.text = relationship_subtype

    (related_type, related_value) = get_identifier_type_value(
        related_object)

    related_identifier = premis_identifier(
        related_type, related_value, prefix='relatedObject')

    relationship.append(related_identifier)

    return relationship


def premis_environment(object_or_identifier=None):
    """Return the PREMIS environment structure.

    :dependency_identifier: PREMIS identifier structure
    :returns: None

    Returns the following ElementTree structure::

        <premis:environment>
            <premis:dependency>

                {{ dependency_identifier }}

            </premis:dependency>
        </premis:environment>

    """

    environment = _element('environment')

    if object_or_identifier is None:
        return environment

    object_identifier = object_or_identifier.find(
        premis_ns('objectIdentifier'))

    if object_identifier is None:
        object_identifier = object_or_identifier

    dependency_identifier_type = object_identifier.find(
        premis_ns('dependencyIdentifierType'))

    if dependency_identifier_type is None:
        (identifier_type, identifier_value) = get_identifier_type_value(
            object_identifier)

        dependency_identifier = premis_identifier(
            identifier_type, identifier_value, 'dependency')
    else:
        dependency_identifier = object_identifier

    dependency = _subelement(environment, 'dependency')
    dependency.append(dependency_identifier)

    return environment


def premis_object(
        identifier,
        original_name=None,
        child_elements=None,
        representation=False):

    """Return the PREMIS object.

        :identifier: PREMIS identifier
        :original_name: Original name field
        :child_elements=None: Any other element appended
        :representation=False:

    Returns the following ElementTree structure::

        <premis:object xsi:type="premis:representation">

            {{ premis_identifier() }}

            <premis:originalName>varmiste.sig</premis:originalName>

            {{ premis_relationship() }}

        </premis:object>

    """

    _object = _element('object')

    _object.append(identifier)

    if representation:
        _object.set(xsi_ns('type'), 'premis:representation')
    else:
        _object.set(xsi_ns('type'), 'premis:file')

    if original_name:
        _original_name = _subelement(_object, 'originalName')
        _original_name.text = original_name

    if child_elements:
        for element in child_elements:
            _object.append(element)

    return _object


def premis_agent(
        identifier, agent_name, agent_type):
    """Returns PREMIS agent element

    :identifier: PREMIS identifier for the agent
    :agent_name: Agent name
    :agent_type: Agent type

    Returns the following ElementTree structure::

        <premis:agent>
            <premis:agentIdentifier>
                <premis:agentIdentifierType>
                    preservation-agent-id</premis:agentIdentifierType>
                <premis:agentIdentifierValue>
                    preservation-agent-check_virus_clamscan.py-0.63-1422
                </premis:agentIdentifierValue>
            </premis:agentIdentifier>
            <premis:agentName>check_virus_clamscan.py</premis:agentName>
            <premis:agentType>software</premis:agentType>
        </premis:agent>

    """

    agent = _element('agent')

    agent.append(identifier)

    _agent_name = _subelement(agent, 'agentName')
    _agent_name.text = agent_name

    _agent_type = _subelement(agent, 'agentType')
    _agent_type.text = agent_type

    return agent


def premis_premis(child_elements=None):
    """Create PREMIS Data Dictionary root element.

    :child_elements: Any elements appended to the PREMIS dictionary

    Returns the following ElementTree structure::


        <premis:premis
            xmlns:premis="info:lc/xmlns/premis-v2"
            xmlns:xsi="http://www.w3.org/2001/xmlschema-instance"
            xsi:schemalocation="info:lc/xmlns/premis-v2
                                http://www.loc.gov/standards/premis/premis.xsd"
            version="2.2">

    """
    _premis = _element('premis')
    _premis.set(
        xsi_ns('schemaLocation'),
        'info:lc/xmlns/premis-v2 '
        'http://www.loc.gov/standards/premis/premis.xsd')

    _premis.set('version', '2.2')

    if child_elements:
        for element in child_elements:
            _premis.append(element)

    return _premis


def premis_event_outcome(outcome, detail_note=None, detail_extension=None):
    """Create PREMIS event outcome DOM structure.

    :outcome: Event outcome (success, failure)
    :detail_note: Description for the event outcome

    Returns the following ElementTree structure::

        <premis:eventOutcomeInformation>
            <premis:eventOutcome>success</premis:eventOutcome>
            <premis:eventOutcomeDetail>
                <premis:eventOutcomeDetailNote>
                    mets.xml sha1 4d0c38dedcb5e5fc93586cfa2b7ebedbd63 OK
                </premis:eventOutcomeDetailNote>
            </premis:eventOutcomeDetail>
        </premis:eventOutcomeInformation>


    """

    outcome_information = _element('eventOutcomeInformation')

    _outcome = _subelement(outcome_information, 'eventOutcome')
    _outcome.text = outcome

    detail = _subelement(outcome_information, 'eventOutcomeDetail')

    if detail_note:
        _detail_note = _subelement(detail, 'eventOutcomeDetailNote')
        _detail_note.text = detail_note

    if detail_extension:
        _detail_extension = _subelement(detail, 'eventOutcomeDetailExtension')
        _detail_extension.text = detail_extension

    return outcome_information


def premis_event(
        identifier, event_type, event_date_time, event_detail,
        child_elements=None, linking_objects=None):
    """Create PREMIS event element.

    :identifier: PREMIS event identifier
    :event_type: Type for the event
    :event_date_time: Event time
    :event_detail: Event details
    :child_elements: Any child elements appended to the event (default=None)
    :linking_objects: Any linking objects appended to the event (default=None)

    Returns the following ElementTree structure::

        <premis:event>

            <premis:eventType>digital signature validation</premis:eventType>
            <premis:eventDateTime>2015-02-03T13:04:25</premis:eventDateTime>
            <premis:eventDetail>
                Submission information package digital signature validation
            </premis:eventDetail>

            {{ child elements }}

        </premis:event>


    """

    event = _element('event')

    event.append(identifier)

    _event_type = _subelement(event, 'eventType')
    _event_type.text = event_type

    _event_date_time = _subelement(event, 'eventDateTime')
    _event_date_time.text = event_date_time

    _event_detail = _subelement(event, 'eventDetail')
    _event_detail.text = event_detail

    if child_elements:
        for element in child_elements:
            event.append(element)

    if linking_objects:
        for _object in linking_objects:
            linking_object = premis_identifier(
                _object.findtext('.//' + premis_ns('objectIdentifierType')),
                _object.findtext('.//' + premis_ns('objectIdentifierValue')),
                'linkingObject')
            event.append(linking_object)

    return event


def iter_elements(starting_element, tag):
    """Iterate all element from starting element that match the `tag`
    parameter. Tag is always prefixed to PREMIS namespace before matching.

    :starting_element: Element where matching elements are searched
    :returns: Generator object for iterating all elements

    """
    for element in starting_element.findall('.//' + premis_ns(tag)):
        yield element


def iter_agents(premis):
    """Iterate all PREMIS agents from starting element.

    :starting_element: Element where matching elements are searched
    :returns: Generator object for iterating all elements

    """
    for element in iter_elements(premis, 'agent'):
        yield element


def iter_events(premis):
    """Iterate all PREMIS events from starting element.

    :starting_element: Element where matching elements are searched
    :returns: Generator object for iterating all elements

    """
    for element in iter_elements(premis, 'event'):
        yield element


def iter_objects(premis):
    """Iterate all PREMIS objects from starting element.

    :starting_element: Element where matching elements are searched
    :returns: Generator object for iterating all elements

    """

    for element in iter_elements(premis, 'object'):
        yield element


def filter_objects(premis_objects, filtered_objects):
    """Return PREMIS objects from `premis_objects` which are not listed in
    `filtered_objects`

    :premis_objects: Objects to filter
    :filtered_objects: Objects which are removed from `premis_objects`
    :returns: Generator object for iterating all objects

    """
    for element in premis_objects:
        found = False
        for filter_element in iter_objects(filtered_objects):
            if contains_object(filter_element, element):
                found = True
        if not found:
            yield element


def contains_object(object_element, search_from_element):
    """Return True if `search_from_element` contains the `object_element`
    object or objectIdentifier.

    :object_element: PREMIS object or identifier
    :search_from_element: PREMIS object to search from
    :returns: Boolean

    """

    key_identifier_value = iter_elements(
        object_element, 'objectIdentifierValue').next()

    # Unfortunately Python 2.6 ElementTree does not support xpath search by
    # element value so we have to search with for-loop

    identifiers = iter_elements(search_from_element, 'objectIdentifierValue')

    for identifier_value in identifiers:
        if identifier_value.text == key_identifier_value.text:
            return True

    return False


def event_count(premis):
    """Return number of events in PREMIS data dictionary.

    :premis: ElementTree element
    :returns: Integer

    """
    return len([x for x in iter_events(premis)])


def object_count(premis):
    """Return number of objects in PREMIS data dictionary.

    :premis: ElementTree element
    :returns: Integer

    """
    return len([x for x in iter_objects(premis)])


def agent_count(premis):
    """Return number of agents in PREMIS data dictionary.

    :premis: ElementTree element
    :returns: Integer

    """
    return len([x for x in iter_agents(premis)])


#
# TODO: Remove JSON Event class after refactoring Premis generation to
# ElementTree factories
#

class Event(object):

    """Premis event serializer.

    TODO: this is only development stub.
    TODO: Replace this with proper Premis event serialization!

    """

    def __init__(self, event_record=None):
        """TODO: Docstring for __init__.

        :event_type: TODO
        :event_detail: TODO
        :returns: TODO

        """
        if type(event_record) == str:
            self.from_json(event_record)
        else:
            self.fields = event_record

    def from_json(self, json_fields):
        """TODO: Docstring for serialize.
        :returns: TODO

        """
        self.fields = json.loads(json_fields)

    def to_json(self):
        """TODO: Docstring for serialize.
        :returns: TODO

        """
        return json.dumps(self.fields)

    def __str__(self):
        """TODO: Docstring for __str__.
        :returns: TODO

        """
        return self.to_json()

    def __iter__(self):
        """TODO: Docstring for __next__.
        :returns: TODO

        """
        for line in self.to_json():
            yield line


def agents_with_type(agents, agent_type='organization'):
    """Return all agents from list of `agents` with given `agent_type`.

    :task_report: Report to search from
    :returns: Generator object which iterates all (agent_type, agent_name)

    """

    for agent in agents:
        agent_name = agent.findtext(premis_ns('agentName'))
        _agent_type = agent.findtext(premis_ns('agentType'))

        if _agent_type == agent_type:
            yield (agent_type, agent_name)


def objects_with_type(objects, object_identifier_type):
    """Return all objects from list of `objects` with given
    `object_identifier_type` matching the PREMIS objectIdentifierType field.

    :objects: Iterable of objects
    :object_identifier_type: Identifier type as string
    :returns: Iterator with all matching objects

    """
    for _object in objects:

        _object_identifier = _object.find(premis_ns('objectIdentifier'))
        _object_identifier_type = _object_identifier.findtext(
            premis_ns('objectIdentifierType'))

        if _object_identifier_type == object_identifier_type:
            yield _object


def event_with_type_and_detail(events, event_type, event_detail):
    """Return all events from list of `events` with given
    `event_identifier_type` matching the PREMIS eventIdentifierType field.

    :events: Iterable of events
    :event_identifier_type: Identifier type as string
    :returns: Iterator with all matching events

    """

    for _event in events:
        _event_type = _event.findtext(premis_ns('eventType'))
        _event_detail = _event.findtext(premis_ns('eventDetail'))

        if _event_type == event_type and _event_detail == event_detail:
            yield _event
