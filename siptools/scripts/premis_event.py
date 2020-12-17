"""Command line tool for creating premis events"""
from __future__ import print_function, unicode_literals

import glob
import json
import os
import sys
from uuid import uuid4

import click
import lxml.etree
import six

import premis
from siptools.mdcreator import MetsSectionCreator
from siptools.xml.mets import NAMESPACES
from siptools.xml.premis import PREMIS_EVENT_OUTCOME_TYPES
from siptools.utils import list2str, read_object_id

click.disable_unicode_literals_warning = True


@click.command()
@click.argument('event_type', required=True, type=str)
@click.argument('event_datetime', required=True, type=str)
@click.option('--workspace',
              type=click.Path(exists=True),
              default='./workspace',
              metavar='<WORKSPACE PATH>',
              help=("Directory where files are created. Defaults "
                    "to ./workspace/"))
@click.option('--base_path', type=click.Path(exists=True), default='.',
              metavar='<BASE PATH>',
              help=("Source base path of event_target or linking_object. If "
                    "used, give event_target/linking_object in relation to "
                    "this base path."))
@click.option('--linking_object', 'linking_objects',
              nargs=2, type=str, multiple=True,
              metavar='<EVENT PATH ROLE> <EVENT PATH>',
              help=('Role and path for the event.'
                    'For example: source path/to/source_file '
                    'May be used multiple times. Given role is stored only '
                    'if --add_object_links is also used.'))
@click.option('--event_target',
              type=str, multiple=True,
              metavar='<EVENT TARGET PATH>',
              help=('Target for the event. Default is the root of '
                    'digital objects. May be used multiple times. '
                    'Same as: --linking_object target path/to/target_file'))
@click.option('--event_detail',
              type=str, required=True,
              metavar='<EVENT DETAIL>',
              help='Short information about the event')
@click.option('--event_outcome',
              type=click.Choice(PREMIS_EVENT_OUTCOME_TYPES),
              required=True,
              metavar='<EVENT OUTCOME>',
              help=('Event outcome type. Possible values are: ' +
                    list2str(PREMIS_EVENT_OUTCOME_TYPES)))
@click.option('--event_outcome_detail',
              type=str, required=True,
              metavar='<EVENT OUTCOME DETAIL>',
              help='Detailed information about the event outcome.')
@click.option('--agent_name',
              required='--agent_type' in sys.argv,
              type=str,
              metavar='<AGENT NAME>',
              help='Agent name')
@click.option('--agent_identifier', nargs=2,
              type=str,
              metavar='<AGENT IDENTIFIER TYPE> <AGENT IDENTIFIER VALUE>',
              help='Agent identifier type and value. Does not have effect if '
                   '--agent_name and --agent_type are missing.')
@click.option('--agent_type',
              required='--agent_name' in sys.argv,
              type=str,
              metavar='<AGENT TYPE>',
              help='Agent type.')
@click.option('--create_agent_file',
              type=str,
              metavar='<CREATE AGENTS FILE>',
              help='The file containing (multiple) created agents '
                   'relating to the current event. Will override the '
                   'other given agent options if used.')
@click.option('--add_object_links',
              is_flag=True,
              help='Add PREMIS linking objects to event. Requires that'
                   'import_object has been run already.')
@click.option('--stdout',
              is_flag=True,
              help='Print output to stdout')
# pylint: disable=too-many-arguments
def main(**kwargs):
    """The script creates provenance metadata for the package. The metadata
    contains event and, if given, also agent of the event.

    \b
    EVENT_TYPE: Type of the event.
    EVENT_DATETIME: Timestamp of the event.
    """
    premis_event(**kwargs)
    return 0


def _attribute_values(given_params):
    """
    Give attribute values as a dict for the script.

    :given_params: Arguments as dict.
    :returns: Attribute value dict
    """
    attributes = {
        "event_type": given_params["event_type"],
        "event_datetime": given_params["event_datetime"],
        "workspace": "./workspace/",
        "base_path": ".",
        "event_detail": given_params["event_detail"],
        "event_outcome": given_params["event_outcome"],
        "event_outcome_detail": given_params["event_outcome_detail"],
        "agent_name": None,
        "agent_type": None,
        "agent_identifier": None,
        "create_agent_file": "",
        "stdout": False,
        "add_object_links": False,
        "linking_agents": set(),
        "linking_objects": (),
        "linking_object_ids": set()
    }
    for key in given_params:
        if given_params[key] and key not in ["event_target"]:
            attributes[key] = given_params[key]

    if "event_target" in given_params and given_params["event_target"]:
        for target in given_params["event_target"]:
            attributes["linking_objects"] = \
                attributes["linking_objects"] + (("target", target), )

    if not attributes["agent_name"] and not attributes["agent_type"]:
        attributes["agent_identifier"] = None

    return attributes


def premis_event(**kwargs):
    """
    The script creates provenance metadata for the package. The metadata
    contains event and, if given, also agent of the event.

    :kwargs: Given arguments
             event_type: PREMIS event type
             event_datetime: Timestamp of the event
             workspace: Workspace path
             base_path: Base path of digital objects
             linking_objects: Roled paths of the event
             event_target: Target paths of the event
             event_detail: Short information about the event
             event_outcome: Event outcome
             event_outcome_detail: Deteiled information about the event
             agent_name: Agent name
             agent_type: PREMIS agent type
             agent_identifier: Agent identifier type and value (tuple)
             create_agent_file: External file containing agents created
                                by the create-agents script
             stdout: True prints output to stdout
             add_object_links: True for adding linking objects. Requires
                               that import-object script has already been
                               used.
    """
    attributes = _attribute_values(kwargs)
    creator = PremisCreator(attributes["workspace"])

    agents = _resolve_agents(**attributes)

    for agent in agents:

        attributes["linking_agents"].add(
            (agent["agent_identifier"][0],
             agent["agent_identifier"][1],
             agent["agent_role"]))

        agent = create_premis_agent(**agent)

        agent_creator = PremisCreator(attributes["workspace"])
        for (directory, event_file, role) in iterate_linking_objects(
                attributes["base_path"], attributes["linking_objects"]):
            agent_creator.add_md(agent, event_file, directory=directory)
        agent_creator.write(mdtype="PREMIS:AGENT",
                            stdout=attributes["stdout"])

    if attributes["add_object_links"]:
        for (directory, event_file, role) in iterate_linking_objects(
                attributes["base_path"], attributes["linking_objects"]):
            if event_file is not None:
                linking_object = read_object_id(
                    event_file, attributes["workspace"])
                attributes["linking_object_ids"].add(
                    (linking_object[0], linking_object[1], role))

    event = create_premis_event(**attributes)

    for (directory, event_file, role) in iterate_linking_objects(
            attributes["base_path"], attributes["linking_objects"]):
        creator.add_md(event, event_file, directory=directory)

    creator.write(mdtype="PREMIS:EVENT", stdout=attributes["stdout"])


def iterate_linking_objects(base_path, linking_objects):
    """
    Iterate event paths given by the user.
    :base_path: Base path of digital objects
    :linking_objects: Roled paths of the event
    :returns: Tuple of directory, file and role. Directory is given if
              path to yield is a directory, file is given if path to
              yield is a file. Role is the given role or "target" by
              default.
    """
    for link in linking_objects:
        yield normalized_linking_object(base_path, link[1]) + (link[0],)
    if not linking_objects:
        yield (".", None, "target")


def normalized_linking_object(base_path, linking_object=None):
    """
    Return the path to the event target (or other role) based on the
    base_path and linking_objects. If linking_objects is None, the event
    concerns the whole package.

    :base_path: Base path
    :linking_object: Roled directory or file of the event
    :returns: a tuple of directory and event_file.
    """
    event_file = None
    directory = None

    # If the given link path is an absolute path and base_path is
    # current path (i.e. not given), relpath will return ../../..
    # sequences, if current path is not part of the absolute path. In
    # such case we will use the absolute path for eventpath and omit
    # base_path relation.
    if linking_object:
        if base_path not in ['.']:
            eventpath = os.path.normpath(
                os.path.join(base_path, linking_object))
        else:
            eventpath = os.path.normpath(linking_object)

        if os.path.isdir(eventpath):
            directory = os.path.normpath(linking_object)
        elif os.path.isfile(eventpath):
            event_file = os.path.normpath(linking_object)
        else:
            raise IOError
    else:
        directory = '.'

    return (directory, event_file)


class PremisCreator(MetsSectionCreator):
    """
    Subclass of MetsSectionCreator, which generates PREMIS event or agent
    metadata.
    """
    # pylint: disable=too-many-arguments
    def write(self, mdtype="PREMIS", mdtypeversion="2.3", othermdtype=None,
              section="digiprovmd", stdout=False, file_metadata_dict=None,
              ref_file="premis-event-md-references.jsonl"):
        super(PremisCreator, self).write(
            mdtype=mdtype,
            mdtypeversion=mdtypeversion,
            othermdtype=othermdtype,
            section=section,
            stdout=stdout,
            file_metadata_dict=file_metadata_dict,
            ref_file=ref_file
        )


def get_premis_agent_identifiers(workspace):
    """
    Get a dictionary of PREMIS agent name and type pairs and their
    corresponding agent identifiers

    :param workspace: Path to the workspace

    :returns: A dictionary with the following tuple-to-tuple mapping
              {(agent_type, agent_name): (agent_ident_type, agent_ident_value)}
    """
    result = {}

    search_path = os.path.join(workspace, "*AGENT-amd.xml")

    for path in glob.glob(search_path):
        element = lxml.etree.parse(path).getroot()[0]
        agent = element.find(
            "mets:digiprovMD/mets:mdWrap/mets:xmlData/premis:agent",
            namespaces=NAMESPACES
        )

        agent_type = agent.find(
            "premis:agentType", namespaces=NAMESPACES
        ).text
        agent_name = agent.find(
            "premis:agentName", namespaces=NAMESPACES
        ).text

        id_type = agent.find(
            "premis:agentIdentifier/premis:agentIdentifierType",
            namespaces=NAMESPACES
        ).text
        id_value = agent.find(
            "premis:agentIdentifier/premis:agentIdentifierValue",
            namespaces=NAMESPACES
        ).text

        result[(agent_type, agent_name)] = (id_type, id_value)

    return result


def create_premis_agent(**attributes):
    """Creates METS digiprovMD element that contains PREMIS agent element with
    unique identifier.

    :attributes: The following keys:
                 agent_name: content of PREMIS agentName element
                 agent_type: content of PREMIS agentType element
                 agent_identifier: PREMIS agent identifier
    :returns: PREMIS event XML element
    """
    agent_identifier = premis.identifier(
        identifier_type=attributes["agent_identifier"][0],
        identifier_value=attributes["agent_identifier"][1], prefix='agent'
    )
    premis_agent = premis.agent(agent_identifier,
                                attributes["agent_name"],
                                attributes["agent_type"],
                                note=attributes["agent_note"])

    return premis_agent


def create_premis_event(**attributes):
    """Creates METS digiprovMD element that contains PREMIS event element.
    Linking agent identifier element is added to PREMIS event element, if agent
    identifier is provided as parameter.

    :attributes: The following keys:
                  event_type: PREMIS event type
                  event_datetime: Timestamp of the event
                  event_detail: Short information about the event
                  event_outcome: Event outcome
                  event_outcome_detail: Deteiled information about the event
                  linking_agents: Linking agent identifier type,
                                  identifier value and role (tuple)
                  linking_object_ids: Set where each element contains linking
                                      object identifier type, value and role
                                      as tuple
    :returns: PREMIS event XML element
    """
    attributes = _attribute_values(attributes)
    event_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=six.text_type(uuid4()),
        prefix='event'
    )

    premis_event_outcome = premis.outcome(attributes["event_outcome"],
                                          attributes["event_outcome_detail"])

    child_elements = [premis_event_outcome]

    # Create linkingAgentIdentifier element if agent identifiers are provided
    for linking_agent in attributes["linking_agents"]:
        linking_agent_identifier = premis.identifier(
            identifier_type=linking_agent[0],
            identifier_value=linking_agent[1],
            prefix='linkingAgent',
            role=linking_agent[2]
        )
        child_elements.append(linking_agent_identifier)

    # Create linkingObjectIdentifier element if object identifiers are given
    for link in attributes["linking_object_ids"]:
        linking_object_identifier = premis.identifier(
            identifier_type=link[0],
            identifier_value=link[1],
            prefix='linkingObject',
            role=link[2]
        )
        child_elements.append(linking_object_identifier)

    premis_event_elem = premis.event(
        event_identifier,
        attributes["event_type"],
        attributes["event_datetime"],
        attributes["event_detail"],
        child_elements=child_elements
    )

    return premis_event_elem


def _resolve_agents(**attributes):
    """Resolves linked agents that can be added to the event in a few
    different ways and outputs the agent information as json.

    First, if the create_agent_file option is provided, the linked
    agent information is read from the file.
    If the list was not provided, the agent provided in the agent_name
    and agent_type options are used.
    If the agent_identifier is provided, that identifier is used,
    otherwise a UUID identifier is created.
    """
    agent_list = []

    agents_filepath = os.path.join(
        attributes["workspace"],
        attributes["create_agent_file"] + '-AGENTS-amd.json')

    # Get existing agent identifiers for reuse
    premis_agent_identifiers = get_premis_agent_identifiers(
        attributes["workspace"]
    )

    if attributes["create_agent_file"] and os.path.exists(agents_filepath):

        with open(agents_filepath) as in_file:
            agents = json.load(in_file)

        for agent in agents:
            attributes["agent_name"] = agent["agent_name"]
            if 'agent_version' in agent:
                attributes["agent_name"] = agent["agent_name"] + \
                    '-v' + agent["agent_version"]
            attributes["agent_identifier"] = premis_agent_identifiers.get(
                (attributes["agent_type"], attributes["agent_name"]), None
            )

            if not attributes["agent_identifier"]:
                attributes["agent_identifier"] = (agent["identifier_type"],
                                                  agent["identifier_value"])
            attributes["agent_type"] = agent["agent_type"]

            agent_dict = {
                "agent_identifier": attributes["agent_identifier"],
                "agent_name": attributes["agent_name"],
                "agent_type": attributes["agent_type"],
                "agent_note": None,
                "agent_role": None
            }
            if 'agent_note' in agent:
                agent_dict["agent_note"] = agent["agent_note"]
            if 'agent_role' in agent:
                agent_dict["agent_role"] = agent["agent_role"]

            agent_list.append(agent_dict)

    elif attributes["agent_name"] or attributes["agent_type"]:
        if not attributes["agent_identifier"]:
            attributes["agent_identifier"] = premis_agent_identifiers.get(
                (attributes["agent_type"], attributes["agent_name"]), None
            )

        if not attributes["agent_identifier"]:
            attributes["agent_identifier"] = ("UUID", six.text_type(uuid4()))

        agent_dict = {
            "agent_identifier": attributes["agent_identifier"],
            "agent_name": attributes["agent_name"],
            "agent_type": attributes["agent_type"],
            "agent_note": None,
            "agent_role": None
        }
        agent_list.append(agent_dict)

    return agent_list


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
