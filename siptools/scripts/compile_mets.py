"""Command line tool for creating mets"""

import os
import sys
import argparse
from scandir import scandir
import lxml.etree
import siptools.xml.mets as m
from siptools.xml.namespaces import NAMESPACES, METS_PROFILE
from siptools.xml.mets_record_status_types import RECORD_STATUS_TYPES
import datetime
import uuid


def parse_arguments(arguments):
    parser = argparse.ArgumentParser(description="Tool for "
                                     "creating mets")
    parser.add_argument('mets_profile', type=str, choices=METS_PROFILE,
            help='list of METS-profiles:%s' % METS_PROFILE)

    parser.add_argument('organization_name', type=str,
                        help='Creator name (organization)')
    parser.add_argument('--objid', dest='objid',
                        type=str, default= str(uuid.uuid4()),
                        help='Organizations unique identifier for the package')
    parser.add_argument('--label', dest='label',
                        type=str, help='Short description of the information package')
    parser.add_argument('--catalog', dest='catalog',
                        type=str, help='Version number of the NDL schema catalog used')
    parser.add_argument('--specification', dest='specification',
            type=str,
                        help='Version number of packaging specification used in creation of data package')
    parser.add_argument('--contentid', dest='contentid',
                        type=str, help='Identifier for SIP Content')
    parser.add_argument('--create_date', dest='create_date',
                        type=str, default=datetime.datetime.utcnow().isoformat(),
                        help='SIP create datetime yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--last_moddate', dest='last_moddate',
                        type=str, default=datetime.datetime.utcnow().isoformat(),
                        help='Last modification datetime yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--record_status', dest='record_status',
                        choices=RECORD_STATUS_TYPES,
                        type=str, default='submission', help='list of record status types:%s' % RECORD_STATUS_TYPES)
    parser.add_argument('--workspace', dest='workspace', type=str,
                        default='./',
                        help="Workspace directory")
    parser.add_argument('--stdout', help='Print output to stdout')

    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    # Create mets header
    mets = m.mets_mets(METS_PROFILE[args.mets_profile], args.objid, args.label,
            args.catalog, args.specification, args.contentid)
    metshdr = m.metshdr(args.organization_name, args.create_date,
                        args.last_moddate, args.record_status)
    mets.append(metshdr)

    # Create mets amdSec
    amdsec = m.amdsec()

    # Append parts
    trees = []
    for entry in scandir(args.workspace):
        if not entry.name.startswith('mets.xml') and entry.is_file():
            element = lxml.etree.parse(entry.path).getroot()[0]

            if element.tag == '{%s}dmdSec' % NAMESPACES['mets']:
                mets.append(element)

            if element.tag == '{%s}techMD' % NAMESPACES['mets']:
                amdsec.append(element)

            if element.tag == '{%s}amdSec' % NAMESPACES['mets']:
                amdsec.append(element[0])

            if element.tag == '{%s}digiprovMD' % NAMESPACES['mets']:
                amdsec.append(element)

            if element.tag == '{%s}fileSec' % NAMESPACES['mets']:
                mets.append(element)

    mets.append(amdsec)

    if args.stdout:
        print m.serialize(mets)

    output_file = os.path.join(args.workspace, 'mets.xml')

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(m.serialize(mets))

    return 0

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
