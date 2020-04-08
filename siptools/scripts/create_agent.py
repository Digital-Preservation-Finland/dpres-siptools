"""Command line tool for collecting agent metadata"""
from __future__ import unicode_literals, print_function

import os
import sys
import json
import hashlib

import click

from siptools.xml.premis import PREMIS_AGENT_TYPES

click.disable_unicode_literals_warning = True


def _list2str(lst):
    """Create a human readable list of words from list of strings.

    :param lst: list of strings
    :returns: list formatted as single string
    """
    first_words = ['"{}"'.format(string) for string in lst[:-1]]
    last_word = '"{}"'.format(lst[-1])
    return ', '.join(first_words) + ', and ' + last_word


@click.command()
@click.argument('agent_name', required=True, type=str)
@click.option('--workspace',
              type=click.Path(exists=True),
              default='./workspace',
              metavar='<WORKSPACE PATH>',
              help=("Directory where files are created. Defaults "
                    "to ./workspace/"))
@click.option('--agent_type', required=True,
              type=click.Choice(PREMIS_AGENT_TYPES),
              help=('The type of the agent. Possible values are: ' +
                    _list2str(PREMIS_AGENT_TYPES)))
@click.option('--agent_version',
              type=str,
              metavar='<AGENT VERSION>',
              help='The version of the agent. Does not have effect if '
                   'agent_type is not "software" or "hardware"')
@click.option('--agent_role',
              type=str,
              metavar='<AGENT ROLE>',
              help=('The role of the agent in relation to the event in '
                    'question'))
@click.option('--agent_note',
              type=str,
              metavar='<AGENT NOTE>',
              help=('The agent note'))
@click.option('--agent_identifier', nargs=2,
              type=str,
              metavar='<IDENTIFIER TYPE> <IDENTIFIER VALUE>',
              help=('Agent identifier type and value'))
@click.option('--create_agent_file',
              type=str, required=True,
              metavar='<CREATE AGENT FILE>',
              help=('The name of the JSON file that collects all agents '
                    'related to the event in question'))
# pylint: disable=too-many-arguments
def main(**kwargs):
    """The script collects provenance metadata for the package. The
    metadata consist of an agent and its relation to an event.  The
    script collects the metadata and the linking information for the
    event to a JSON file, that is read by the subsequent premis-event
    script.

    If used, this script must be run prior to the premis-event script,
    since no actual XML data is written in this script and the agent
    is given only in relation an event. The create-agent file created
    in this script must also be passed to the premis-event script,
    allowing it to collect the metadata created by this script.

    When multiple agents relate to the same event, this script needs
    to be run for each agent using the same --create_agent_file value.

    \b
    AGENT_NAME: The name of the agent.
    """
    create_agent(**kwargs)
    return 0


def _attribute_values(given_params):
    """
    Give attribute values as a dict for the script.

    :given_params: Arguments as dict.
    :returns: Attribute value dict
    """
    attributes = {
        "agent_name": given_params["agent_name"],
        "workspace": "./workspace/",
        "agent_type":  given_params["agent_type"],
        "agent_version": None,
        "agent_role": None,
        "agent_note": None,
        "agent_identifier": (),
        "create_agent_file": given_params["create_agent_file"],
    }
    for key in given_params:
        if given_params[key]:
            attributes[key] = given_params[key]

    if not any((attributes["agent_type"] == 'software',
                attributes["agent_type"] == 'hardware')):
        attributes["agent_version"] = None

    if not attributes["agent_identifier"]:
        message_string = '{name}{version}{agent_type}'.format(
            name=attributes['agent_name'],
            version=attributes.get('agent_version', ''),
            agent_type=attributes['agent_type'])
        message = hashlib.md5()
        message.update(message_string)
        attributes["agent_identifier"] = ("local", message.hexdigest())

    return attributes


def create_agent(**kwargs):
    """
    The script collects provenance metadata for the package. The metadata
    consists of information about the agent and linking information to
    the event that the agent relates to. The result of this function is
    a JSON file containing metadata about the agent and its role in
    relation to the event.
    If the given JSON file exists, the new agent metadata is appended
    to the existing data, allowing for multiple agents to be related to
    the same event.

    :kwargs: Given arguments
             agent_name: agent name
             workspace: Workspace path
             agent_type: agent type
             agent_version: Agent version if agent type is "software"
             agent_role: agent role in relation to the event
             agent_note: Agent note as a string
             agent_identifier: Agent identifier type and value (tuple)
             create_agent_file: The name of the JSON file that collects
                                agent information in relation to the
                                event

    :returns: The agent identifier value as a string
    """
    attributes = _attribute_values(kwargs)

    agent_dict = {
        "identifier_type": attributes["agent_identifier"][0],
        "identifier_value": attributes["agent_identifier"][1],
        "agent_name": attributes["agent_name"],
        "agent_type": attributes["agent_type"],
    }
    if attributes["agent_version"]:
        agent_dict["agent_version"] = attributes["agent_version"]
    if attributes["agent_role"]:
        agent_dict["agent_role"] = attributes["agent_role"]
    if attributes["agent_note"]:
        agent_dict["agent_note"] = attributes["agent_note"]

    output_path = os.path.join(
        attributes["workspace"],
        attributes["create_agent_file"] + '-AGENTS-amd.json')

    agents_list = []
    if os.path.exists(output_path):
        with open(output_path) as in_file:
            agents_list = json.load(in_file)

    agents_list.append(agent_dict)

    with open(output_path, 'wt') as outfile:
        json.dump(agents_list, outfile, indent=4)

    print(
        "Collected agent metadata with identifier %s" %
        attributes["agent_identifier"][1])

    return attributes["agent_identifier"][1]


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
