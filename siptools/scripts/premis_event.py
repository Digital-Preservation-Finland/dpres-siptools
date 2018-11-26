"""Command line tool for creating premis events"""

import sys
import os
from uuid import uuid4
import argparse

import premis
import mets
import xml_helpers.utils

from siptools.xml.premis import PREMIS_EVENT_TYPES, PREMIS_EVENT_OUTCOME_TYPES
from siptools.utils import encode_path, encode_id


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Tool for creating premis events")

    parser.add_argument('event_type',
                        type=str,
                        help='list of event types:%s' % PREMIS_EVENT_TYPES)
    parser.add_argument('event_datetime',
                        type=str,
                        help='Event datetime yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--event_detail',
                        dest='event_detail',
                        type=str,
                        help='Event detail')
    parser.add_argument('--event_outcome',
                        choices=PREMIS_EVENT_OUTCOME_TYPES,
                        dest='event_outcome',
                        type=str,
                        help=('Event outcome types: %s'
                              % PREMIS_EVENT_OUTCOME_TYPES))
    parser.add_argument('--event_outcome_detail',
                        dest='event_outcome_detail',
                        type=str,
                        help='Event outcome_detail')
    parser.add_argument('--workspace',
                        dest='workspace',
                        type=str,
                        default='./workspace',
                        help="Workspace directory")
    parser.add_argument('--agent_name',
                        dest='agent_name',
                        type=str,
                        help='Agent name')
    parser.add_argument('--agent_type',
                        dest='agent_type',
                        type=str,
                        help='Agent type')
    parser.add_argument('--stdout',
                        help='Print output to stdout')
    parser.add_argument('--event_target',
                        dest='event_target',
                        type=str,
                        help=('Target for the event. Default is the root of '
                              'digital objects.'))

    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for premis_event"""
    args = parse_arguments(arguments)

    # Create agent
    if args.agent_name:

        output_filename = '%s-agent.xml' % (args.event_type)
        if args.event_target:
            output_filename = '%s-%s' % (args.event_target, output_filename)
        output_filename = encode_path(output_filename)

        agent_id = encode_id(output_filename)

        agent_identifier = str(uuid4())
        premis_agent = create_premis_agent(args.agent_name,
                                           args.agent_type,
                                           agent_identifier)

        _mets = create_mets(premis_agent, agent_id, 'PREMIS:AGENT')

        if args.stdout:
            print xml_helpers.utils.serialize(_mets)

        write_mets(_mets, os.path.join(args.workspace, output_filename))

    else:
        agent_identifier = None

    # Create event
    output_filename = '%s-event.xml' % args.event_type
    if args.event_target:
        output_filename = '%s-%s' % (args.event_target, output_filename)
    output_filename = encode_path(output_filename)

    event_id = encode_id(output_filename)

    premis_event = create_premis_event(
        args.event_type, args.event_datetime, args.event_detail,
        args.event_outcome, args.event_outcome_detail, agent_identifier
    )

    _mets = create_mets(premis_event, event_id, 'PREMIS:EVENT')

    write_mets(_mets, os.path.join(args.workspace, output_filename))

    if args.stdout:
        print xml_helpers.utils.serialize(_mets)

    return 0


def write_mets(mets_element, output_file):
    """Write METS XML elemnt to file.

    :param mets_element: METS XML element
    :param output: output file path
    :returns: ``None``
    """

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as output:
        output.write(xml_helpers.utils.serialize(mets_element))

    print "premis_event created file: %s" % output_file


def create_mets(premis_element, digiprovmd_id, mdtype):
    """Creates a METS XML element that contains PREMIS element

    :param premis_element: PREMIS element
    :param digiprovmd_id: ID attribute of digiprovMD element
    :param mdtype: MDTYPE of mdWrap element
    :returns: METS XML element
    """
    xmldata = mets.xmldata(child_elements=[premis_element])
    mdwrap = mets.mdwrap(mdtype, '2.3', child_elements=[xmldata])
    digiprovmd = mets.digiprovmd(digiprovmd_id, child_elements=[mdwrap])
    amdsec = mets.amdsec(child_elements=[digiprovmd])
    _mets = mets.mets(child_elements=[amdsec])

    return _mets


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
