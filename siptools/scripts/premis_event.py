"""Command line tool for creating premis events"""

import sys
import os
from uuid import uuid4
import argparse

import premis
import mets
import xml_helpers.utils as h

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

        _mets = mets.mets()
        amdsec = mets.amdsec()
        _mets.append(amdsec)

        output_filename = '%s-agent.xml' % (args.event_type)
        if args.event_target:
            output_filename = '%s-%s' % (args.event_target, output_filename)

        agent_id = encode_id(encode_path(output_filename))
        output_file_path = os.path.join(args.workspace,
                                        encode_path(output_filename))

        agent_identifier = str(uuid4())
        amdsec.append(create_premis_agent(agent_id,
                                          args.agent_name,
                                          args.agent_type,
                                          agent_identifier))

        if args.stdout:
            print h.serialize(_mets)

        if not os.path.exists(os.path.dirname(output_file_path)):
            os.makedirs(os.path.dirname(output_file_path))

        with open(output_file_path, 'w+') as output_file:
            output_file.write(h.serialize(_mets))

        print "premis_event created file: %s" % output_file_path

    else:
        agent_identifier = None

    # Create event
    _mets = mets.mets()
    amdsec = mets.amdsec()
    _mets.append(amdsec)

    output_filename = '%s-event.xml' % args.event_type
    if args.event_target:
        output_filename = '%s-%s' % (args.event_target, output_filename)
    event_id = encode_id(encode_path(output_filename))
    output_file_path = os.path.join(args.workspace,
                                    encode_path(output_filename))

    amdsec.append(
        create_premis_event(
            args.event_type, args.event_datetime, args.event_detail,
            args.event_outcome, args.event_outcome_detail,
            agent_identifier, event_id
        )
    )

    if args.stdout:
        print h.serialize(_mets)

    if not os.path.exists(os.path.dirname(output_file_path)):
        os.makedirs(os.path.dirname(output_file_path))

    with open(output_file_path, 'w+') as output_file:
        output_file.write(h.serialize(_mets))

    print "premis_event created file: %s" % output_file_path

    return 0


def create_premis_agent(agent_id, agent_name, agent_type, agent_identifier):
    """Creates METS digiprovMD element that contains PREMIS agent element with
    unique identifier.

    :param agent_id: ID attribute of digiprovMD element
    :param agent_name: content of PREMIS agentName element
    :param agent_type: content of PREMIS agentType element
    :param agent_identifier: content of PREMIS agentIdentifierValue element
    :returns: METS digiprovMD element
    """
    agent_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=agent_identifier, prefix='agent'
    )
    premis_agent = premis.agent(agent_identifier, agent_name, agent_type)

    xmldata = mets.xmldata(child_elements=[premis_agent])
    mdwrap = mets.mdwrap('PREMIS:AGENT', '2.3', child_elements=[xmldata])
    digiprovmd = mets.digiprovmd(agent_id, child_elements=[mdwrap])

    return digiprovmd


def create_premis_event(event_type, event_datetime, event_detail,
                        event_outcome, event_outcome_detail,
                        agent_identifier, event_id):
    """Creates METS digiprovMD element that contains PREMIS event element.
    Linking agent identifier element is added to PREMIS event element, if agent
    identifier is provided as parameter.

    :param event_type: Event type
    :param event_datetime: Event time
    :param event_detail: Event details
    :param event_outcome: Event outcome ("success" or "failure")
    :param event_outcome_detail: Event outcome description
    :param linking_agent_identifier: PREMIS agent identifier or ``None``
    :param event_id: ID attribute of digiprovMD element
    :returns: ``None``
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

    xmldata = mets.xmldata(child_elements=[premis_event])
    mdwrap = mets.mdwrap('PREMIS:EVENT', '2.3', child_elements=[xmldata])
    digiprovmd = mets.digiprovmd(event_id, child_elements=[mdwrap])

    return digiprovmd


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
