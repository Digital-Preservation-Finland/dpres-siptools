"""Command line tool for creating premis events"""

import argparse
import siptools.xml.premis as p
import siptools.xml.mets as m
import os
from uuid import uuid4
from siptools.xml.premis_event_types import PREMIS_EVENT_TYPES
from siptools.xml.premis_event_types import PREMIS_EVENT_OUTCOME_TYPES

def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="Tool for "
            "creating premis events")

    parser.add_argument('event_type', type=str, choices=PREMIS_EVENT_TYPES,
            help='list of event types:%s' % PREMIS_EVENT_TYPES)
    parser.add_argument('event_datetime', type=str, help='Event datetime yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--event_detail', dest='event_detail', type=str, help='Event detail')
    parser.add_argument('--event_outcome', choices=PREMIS_EVENT_OUTCOME_TYPES,
            dest='event_outcome', type=str, help='Event outcome types: %s' %
            PREMIS_EVENT_OUTCOME_TYPES)
    parser.add_argument('--event_outcome_detail', dest='event_outcome_detail',
            type=str, help='Event outcome_detail')
    parser.add_argument('--workspace', dest='workspace', type=str,
            default='./',
            help="Workspace directory")
    parser.add_argument('--agent_name', dest='agent_name',
            type=str, help='Agent name')
    parser.add_argument('--agent_type', dest='agent_type',
            type=str, help='Agent type')
    parser.add_argument('--stdout', help='Print output to stdout')

    return parser.parse_args(arguments)

def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    mets = m._element('mets')
    amdsec = m.amdsec()
    mets.append(amdsec)
    digiprovmd = m.digiprovmd('digiprovmd-%s' % str(uuid4()))
    amdsec.append(digiprovmd)

    digiprovmd_agent = m.digiprovmd('digiprovmd-%s' % str(uuid4()))
    amdsec.append(digiprovmd_agent)

    unique = str(uuid4())
    event_identifier = p.premis_identifier(
            identifier_type='premis-event-id',
            identifier_value=unique)

    agent_identifier = p.premis_identifier(
            identifier_type='local',
            identifier_value=args.agent_name, prefix='agent')
    premis_agent = p.premis_agent(agent_identifier, args.agent_name,
            args.agent_type)
    digiprovmd_agent.append(premis_agent)

    linking_agent_identifier = p.premis_identifier(
            identifier_type='local',
            identifier_value=args.agent_name, prefix='linkingAgent')

    premis_event_outcome = p.premis_event_outcome(args.event_outcome,
            args.event_outcome_detail)

    premisevent = p.premis_event(event_identifier, args.event_type,
            args.event_datetime,args.event_detail,
            child_elements=[premis_event_outcome, linking_agent_identifier])
    digiprovmd.append(premisevent)

    #print "mets:%s " % m.serialize(mets)
    if args.stdout:
        print m.serialize(mets)

    output_file = os.path.join(args.workspace, args.event_type + '.xml')

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(m.serialize(mets))

    return 0

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)


