"""Command line tool for creating premis events"""

import sys
import argparse
import siptools.xml.premis as p
import siptools.xml.mets as m
import os
from uuid import uuid4
from siptools.xml.premis_event_types import PREMIS_EVENT_TYPES
from siptools.xml.premis_event_types import PREMIS_EVENT_OUTCOME_TYPES
from siptools.utils import encode_path, encode_id

def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="Tool for "
                                     "creating premis events")

    parser.add_argument('event_type', type=str, choices=PREMIS_EVENT_TYPES,
                        help='list of event types:%s' % PREMIS_EVENT_TYPES)
    parser.add_argument('event_datetime', type=str,
                        help='Event datetime yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--event_detail', dest='event_detail',
                        type=str, help='Event detail')
    parser.add_argument('--event_outcome', choices=PREMIS_EVENT_OUTCOME_TYPES,
                        dest='event_outcome', type=str, help='Event outcome types: %s' %
                        PREMIS_EVENT_OUTCOME_TYPES)
    parser.add_argument('--event_outcome_detail', dest='event_outcome_detail',
                        type=str, help='Event outcome_detail')
    parser.add_argument('--workspace', dest='workspace', type=str,
                        default='./workspace',
                        help="Workspace directory")
    parser.add_argument('--agent_name', dest='agent_name',
                        type=str, help='Agent name')
    parser.add_argument('--agent_type', dest='agent_type',
                        type=str, help='Agent type')
    parser.add_argument('--stdout', help='Print output to stdout')
    parser.add_argument('--event_target', dest='event_target',
                        type=str, help='Target for the event. Default '
                        'is the root of digital objects')

    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)
    
    if args.agent_name:

        mets = m.mets_mets()
        amdsec = m.amdsec()
        mets.append(amdsec)

        if args.event_target:
            agent_id = encode_id(encode_path('%s-%s-agent.xml' % (args.event_target,
                args.event_type)))
            output_file = os.path.join(args.workspace, encode_path('%s-%s-agent.xml' %
                (args.event_target, args.event_type)))
        else:
            agent_id = encode_id(encode_path('%s-agent.xml' % (args.event_type)))
            output_file = os.path.join(args.workspace, encode_path('%s-agent.xml' %
                (args.event_type)))
        linking_agent_identifier = create_premis_agent(
            amdsec, agent_id, args.agent_name, args.agent_type)

        if args.stdout:
            print m.serialize(mets)

        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))

        with open(output_file, 'w+') as outfile:
            outfile.write(m.serialize(mets))

        print "premis_event created file: %s" % output_file
    
    else:
        linking_agent_identifier = None

    # Create event
    mets = m.mets_mets()
    amdsec = m.amdsec()
    mets.append(amdsec)


    if args.event_target:
        event_id = encode_id(encode_path('%s-%s-event.xml' % (args.event_target,
            args.event_type)))
        output_file = os.path.join(args.workspace, encode_path('%s-%s-event.xml' %
            (args.event_target, args.event_type)))
    else:
        event_id = encode_id(encode_path('%s-event.xml' % (args.event_type)))
        output_file = os.path.join(args.workspace, encode_path('%s-event.xml' %
            (args.event_type)))

    create_premis_event(amdsec, args.event_type, args.event_datetime,
                        args.event_detail, args.event_outcome, args.event_outcome_detail,
                        linking_agent_identifier, event_id)

    if args.stdout:
        print m.serialize(mets)

    output_file = os.path.join(args.workspace, encode_path('%s-%s-event.xml' %
        (args.digital_object, args.event_type)))

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(m.serialize(mets))

    print "premis_event created file: %s" % output_file

    return 0


def create_premis_agent(tree, agent_id, agent_name, agent_type):
    digiprovmd = m.digiprovmd(agent_id)
    mdwrap = m.mdwrap(mdtype='PREMIS:AGENT')
    xmldata = m.xmldata()

    agent_identifier = p.premis_identifier(
        identifier_type='local',
        identifier_value=agent_name, prefix='agent')
    premis_agent = p.premis_agent(agent_identifier, agent_name,
                                  agent_type)

    linking_agent_identifier = p.premis_identifier(
        identifier_type='local',
        identifier_value=agent_name, prefix='linkingAgent')

    xmldata.append(premis_agent)
    mdwrap.append(xmldata)
    digiprovmd.append(mdwrap)
    tree.append(digiprovmd)

    return linking_agent_identifier


def create_premis_event(tree, event_type, event_datetime, event_detail,
                        event_outcome, event_outcome_detail,
                        linking_agent_identifier, event_id):
    digiprovmd = m.digiprovmd(event_id)
    mdwrap = m.mdwrap(mdtype='PREMIS:EVENT')
    xmldata = m.xmldata()

    unique = str(uuid4())
    event_identifier = p.premis_identifier(
            identifier_type='UUID',
            identifier_value=unique,
            prefix='event')

    premis_event_outcome = p.premis_event_outcome(event_outcome,
                                                  event_outcome_detail)

    if linking_agent_identifier:
        child_elements=[premis_event_outcome, linking_agent_identifier]
    else:
        child_elements=[premis_event_outcome]    
    premisevent = p.premis_event(event_identifier, event_type,
                                 event_datetime, event_detail,
                                 child_elements=child_elements)

    xmldata.append(premisevent)
    mdwrap.append(xmldata)
    digiprovmd.append(mdwrap)
    tree.append(digiprovmd)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
