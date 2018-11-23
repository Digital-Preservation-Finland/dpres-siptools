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

    if args.agent_name:

        _mets = mets.mets()
        amdsec = mets.amdsec()
        _mets.append(amdsec)

        if args.event_target:
            agent_id = encode_id(
                encode_path(
                    '%s-%s-agent.xml' % (args.event_target, args.event_type)
                )
            )
            output_file = os.path.join(
                args.workspace, encode_path(
                    '%s-%s-agent.xml' % (args.event_target, args.event_type)
                )
            )

        else:
            agent_id = encode_id(
                encode_path('%s-agent.xml' % (args.event_type))
            )
            output_file = os.path.join(
                args.workspace, encode_path(
                    '%s-agent.xml' % (args.event_type)
                )
            )

        linking_agent_identifier = create_premis_agent(
            amdsec, agent_id, args.agent_name, args.agent_type
        )

        if args.stdout:
            print h.serialize(_mets)

        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))

        with open(output_file, 'w+') as outfile:
            outfile.write(h.serialize(_mets))

        print "premis_event created file: %s" % output_file

    else:
        linking_agent_identifier = None

    # Create event
    _mets = mets.mets()
    amdsec = mets.amdsec()
    _mets.append(amdsec)

    if args.event_target:
        event_id = encode_id(
            encode_path(
                '%s-%s-event.xml' % (args.event_target, args.event_type)
            )
        )
        output_file = os.path.join(
            args.workspace, encode_path(
                '%s-%s-event.xml' % (args.event_target, args.event_type)
            )
        )
    else:
        event_id = encode_id(encode_path('%s-event.xml' % (args.event_type)))
        output_file = os.path.join(
            args.workspace, encode_path('%s-event.xml' % (args.event_type))
        )

    create_premis_event(
        amdsec, args.event_type, args.event_datetime, args.event_detail,
        args.event_outcome, args.event_outcome_detail,
        linking_agent_identifier, event_id
    )

    if args.stdout:
        print h.serialize(_mets)

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(h.serialize(_mets))

    print "premis_event created file: %s" % output_file

    return 0


def create_premis_agent(tree, agent_id, agent_name, agent_type):
    """Creates METS digiprovMD element that contains PREMIS agent element with
    unique identifier and appends it to XML element tree.

    :param tree: XML ElementTree to which the PREMIS agent is added
    :param agent_id: ID attribute of digiprovMD element
    :param agent_name: content of PREMIS agentName element
    :param agent_type: content of PREMIS agentType element
    :returns: unique identifier of agent
    """
    uuid = str(uuid4())
    agent_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=uuid, prefix='agent'
    )
    premis_agent = premis.agent(agent_identifier, agent_name, agent_type)

    linking_agent_identifier = premis.identifier(
        identifier_type='UUID', identifier_value=uuid, prefix='linkingAgent'
    )

    xmldata = mets.xmldata(child_elements=[premis_agent])
    mdwrap = mets.mdwrap('PREMIS:AGENT', '2.3', child_elements=[xmldata])
    digiprovmd = mets.digiprovmd(agent_id, child_elements=[mdwrap])
    tree.append(digiprovmd)

    return linking_agent_identifier


def create_premis_event(tree, event_type, event_datetime, event_detail,
                        event_outcome, event_outcome_detail,
                        linking_agent_identifier, event_id):
    """Creates METS digiprovMD element that contains PREMIS event element and
    adds it to XML element tree. Also linking agent identifier element is added
    to PREMIS event element, if such element is provided as parameter.

    :param tree: XML ElementTree to which the PREMIS event is added
    :param event_type: Event type
    :param event_datetime: Event time
    :param event_detail: Event details
    :param event_outcome: Event outcome ("success" or "failure")
    :param event_outcome_detail: Event outcome description
    :param linking_agent_identifier: PREMIS agent identifier element or
                                     ``None``
    :param event_id:
    :returns: ``None``
    """
    event_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=str(uuid4()),
        prefix='event'
    )

    premis_event_outcome = premis.outcome(event_outcome,
                                          event_outcome_detail)

    if linking_agent_identifier is not None:
        child_elements = [premis_event_outcome, linking_agent_identifier]
    else:
        child_elements = [premis_event_outcome]

    premis_event = premis.event(event_identifier, event_type,
                                event_datetime, event_detail,
                                child_elements=child_elements)

    xmldata = mets.xmldata(child_elements=[premis_event])
    mdwrap = mets.mdwrap('PREMIS:EVENT', '2.3', child_elements=[xmldata])
    digiprovmd = mets.digiprovmd(event_id, child_elements=[mdwrap])
    tree.append(digiprovmd)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
