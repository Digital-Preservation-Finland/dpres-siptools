"""Command line tool for creating premis events"""
import sys
import os
from uuid import uuid4
import argparse

import premis
import xml_helpers.utils

from siptools.xml.premis import PREMIS_EVENT_TYPES, PREMIS_EVENT_OUTCOME_TYPES
from siptools.utils import AmdCreator


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line argumets"""

    def _list2str(lst):
        """Create a human readable list of words from list of strings.

        :param lst: list of strings
        :returns: list formatted as single string
        """
        first_words = ['"' + string + '"' for string in lst[:-1]]
        last_word = '"' + lst[-1] + '"'
        return ', '.join(first_words) + ', and ' + last_word

    parser = argparse.ArgumentParser(
        description=(
            "Create METS document that contains PREMIS event element. Another "
            "METS document that contains PREMIS agent element is created if "
            "optional parameters \"agent_type\" and \"agent_name\" are used. "
            "The PREMIS agent element is linked to PREMIS event element by "
            "unique identifier. The digiprovMD elements get identifiers based "
            "on the METS document filename. "
        )
    )
    parser.add_argument('event_type',
                        type=str,
                        metavar='event_type',
                        choices=PREMIS_EVENT_TYPES,
                        help=('Event type. Possible values are: ' +
                              _list2str(PREMIS_EVENT_TYPES)))
    parser.add_argument('event_datetime',
                        type=str,
                        help='Event datetime formatted as yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--event_detail',
                        dest='event_detail',
                        type=str,
                        required=True,
                        help='Event detail')
    parser.add_argument('--event_outcome',
                        metavar='EVENT_OUTCOME',
                        choices=PREMIS_EVENT_OUTCOME_TYPES,
                        dest='event_outcome',
                        type=str,
                        required=True,
                        help=('Event outcome type. Possible values are: ' +
                              _list2str(PREMIS_EVENT_OUTCOME_TYPES)))
    parser.add_argument('--event_outcome_detail',
                        dest='event_outcome_detail',
                        type=str,
                        help='Event outcome detail')
    parser.add_argument('--workspace',
                        dest='workspace',
                        type=str,
                        default='./workspace',
                        help=("Directory where files are created. Default "
                              "is ./workspace"))
    parser.add_argument('--agent_name',
                        dest='agent_name',
                        required='--agent_type' in sys.argv,
                        type=str,
                        help='Agent name')
    parser.add_argument('--agent_type',
                        dest='agent_type',
                        required='--agent_name' in sys.argv,
                        type=str,
                        help='Agent type')
    parser.add_argument('--stdout',
                        action='store_true',
                        help='Print output to stdout')
    parser.add_argument('--event_target',
                        dest='event_target',
                        type=str,
                        help=('Target for the event. Default is the root of '
                              'digital objects.'))

    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for premis_event.

    :arguments: list of commandline arguments
    :returns: 0
    """

    args = parse_arguments(arguments)

    event_target = None
    directory = None

    if args.event_target and os.path.isdir(args.event_target):
        directory = os.path.normpath(args.event_target)
    elif args.event_target and os.path.isfile(args.event_target):
        event_target = args.event_target
    elif not args.event_target:
        directory = '.'

    if args.agent_name or args.agent_type:
        agent_identifier = str(uuid4())
        agent = create_premis_agent(args.agent_name,
                                    args.agent_type, agent_identifier)

        agent_creator = PremisCreator(args.workspace)
        agent_creator.add_md(agent, event_target, directory=directory)
        agent_creator.write(mdtype="PREMIS:AGENT", stdout=args.stdout)

        if args.stdout:
            print xml_helpers.utils.serialize(agent)
    else:
        agent_identifier = None

    event = create_premis_event(
        args.event_type,
        args.event_datetime,
        args.event_detail,
        args.event_outcome,
        args.event_outcome_detail,
        agent_identifier
    )

    creator = PremisCreator(args.workspace)
    creator.add_md(event, event_target, directory=directory)
    creator.write(mdtype="PREMIS:EVENT", stdout=args.stdout)

    if args.stdout:
        print xml_helpers.utils.serialize(event)

    return 0


class PremisCreator(AmdCreator):
    """Subclass of AmdCreator, which generates PREMIS event
    or agent metadata.
    """

    def write(self, mdtype="PREMIS", mdtypeversion="2.3",
              section="digiprovmd", stdout=False):
        super(PremisCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion, section=section)


def create_premis_agent(agent_name, agent_type, agent_identifier):
    """Creates METS digiprovMD element that contains PREMIS agent element with
    unique identifier.

    :param agent_name: content of PREMIS agentName element
    :param agent_type: content of PREMIS agentType element
    :param agent_identifier: content of PREMIS agentIdentifierValue element
    :returns: PREMIS event XML element
    """
    agent_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=agent_identifier, prefix='agent'
    )
    premis_agent = premis.agent(agent_identifier, agent_name, agent_type)

    return premis_agent


def create_premis_event(event_type, event_datetime, event_detail,
                        event_outcome, event_outcome_detail, agent_identifier):
    """Creates METS digiprovMD element that contains PREMIS event element.
    Linking agent identifier element is added to PREMIS event element, if agent
    identifier is provided as parameter.

    :param event_type: Event type
    :param event_datetime: Event time
    :param event_detail: Event details
    :param event_outcome: Event outcome ("success" or "failure")
    :param event_outcome_detail: Event outcome description
    :param agent_identifier: PREMIS agent identifier or ``None``
    :returns: PREMIS event XML element
    """
    event_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=str(uuid4()),
        prefix='event'
    )

    premis_event_outcome = premis.outcome(event_outcome,
                                          event_outcome_detail)

    child_elements = [premis_event_outcome]

    # Create linkingAgentIdentifier element if agent identifier is provided
    if agent_identifier is not None:
        linking_agent_identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=agent_identifier,
            prefix='linkingAgent'
        )
        child_elements.append(linking_agent_identifier)

    premis_event = premis.event(event_identifier, event_type,
                                event_datetime, event_detail,
                                child_elements=child_elements)

    return premis_event


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
