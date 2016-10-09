"""Command line tool for creating premis events"""

import argparse
import siptools.xml.premis as p
import siptools.xml.mets as m
import os
from uuid import uuid4

def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="Tool for "
            "creating premis events")

    parser.add_argument('event_type', type=str, help='list of event types here')
    parser.add_argument('event_datetime', type=str, help='Event datetime yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--event_detail', dest='event_detail', type=str, help='Event detail')
    parser.add_argument('--event_outcome', dest='event_outcome', type=str, help='Event outcome')
    # Event outcome on lista
    parser.add_argument('--workspace', dest='workspace', type=str,
            default='./',
            help="Destination file")
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
    unique = str(uuid4())
    event_identifier = p.premis_identifier(
            identifier_type='premis-event-id',
            identifier_value=unique)

    premisevent = p.premis_event(event_identifier, args.event_type,
            args.event_datetime,args.event_detail)
    digiprovmd.append(premisevent)

    print "mets:%s " % m.serialize(mets)
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


