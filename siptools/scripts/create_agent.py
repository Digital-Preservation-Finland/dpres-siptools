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
@click.option('--agent_identifier', nargs=2,
              type=str,
              metavar='<IDENTIFIER TYPE> <IDENTIFIER VALUE>',
              help=('Agent identifier type and value'))
@click.option('--output_file',
              type=str, required=True,
              metavar='<OUTPUT FILE>',
              help=('The name of the JSON file that collects all agents '
                    'related to the event in question'))
# pylint: disable=too-many-arguments
def main(**kwargs):
    """The script collects provenance metadata for the package. The
    metadata contains the agent and linking information for the event
    that the agent relates to. If used, this script must be run prior
    to the premis-event script, since no actual XML data is written
    in this script.

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
        "agent_identifier": (),
        "output_file": given_params["output_file"],
    }
    for key in given_params:
        if given_params[key]:
            attributes[key] = given_params[key]

    if not any((attributes["agent_type"] == 'software',
                attributes["agent_type"] == 'hardware')):
        attributes["agent_version"] = None

    if not attributes["agent_identifier"]:
        if attributes["agent_version"]:
            message_string = attributes["agent_name"] + \
                attributes["agent_version"] + attributes["agent_type"]
        else:
            message_string = attributes["agent_name"] + \
                             attributes["agent_type"]

        message = hashlib.md5()
        message.update(message_string)
        attributes["agent_identifier"] = ("local", message.hexdigest())

    return attributes


def create_agent(**kwargs):
    """
    The script creates provenance metadata for the package. The metadata
    contains the agent and linking information to the event. The result
    is a JSON file containing metadata about the agent and its role in
    relation to the event.

    :kwargs: Given arguments
             agent_name: agent name
             workspace: Workspace path
             agent_type: agent type
             agent_version: Agent version if agent type is "software"
             agent_role: agent role in relation to the event
             agent_identifier: Agent identifier type and value (tuple)
             output_file: The name of the JSON file that collects agent
                          information in relation to the event

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

    output_path = os.path.join(
        attributes["workspace"],
        attributes["output_file"] + '-AGENTS-amd.json')

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
