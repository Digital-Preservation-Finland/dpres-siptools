""" import_description"""

from siptools.xml.namespaces import NAMESPACES, METS_NS

import re
import sys
import argparse
import os
import shutil
import lxml.etree
from lxml.etree import Element, SubElement, tostring
import siptools.xml.mets as m
import uuid
import datetime
import dateutil.tz
import urllib
from urllib import quote_plus


def import_description(workspace_path, dmdsec_location):
    """ Read xml-file(s) into METS-files. """

    source_path = os.path.abspath(dmdsec_location)
    target_path = os.path.abspath(workspace_path)

    filecount = 0
    if os.path.isdir(source_path):
        for root, dirs, files in os.walk(source_path, topdown=False):
            for name in files:
                filecount += 1
                url_t_path = quote_plus(dmdsec_location, safe='') + name
                s_path = os.path.join(root, name)
                t_path = os.path.join(target_path, url_t_path)
                # print "copying %s to %s" % (s_path, t_path)
                with open(s_path, 'r') as content_file:
                    content = content_file.read()

                mets_dmdsec = serialize(content)
                if not os.path.exists(target_path):
                    os.makedirs(target_path)

                with open(t_path, 'w') as target_file:
                    target_file.write(mets_dmdsec)
    else:
        with open(source_path, 'r') as content_file:
            content = content_file.read()
        url_t_path = quote_plus(dmdsec_location, safe='')
        t_path = os.path.join(target_path, url_t_path)

        mets_dmdsec = serialize(content)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        with open(t_path, 'w') as target_file:
            target_file.write(mets_dmdsec)
        filecount = 1

    # print "Filecount: %s" % filecount
    if filecount == 0:
        raise IOError("Invalid descriptive metadata location: %s" %
                      source_path)


def serialize(content):
    """
    Serialize encapsulated objects to XML.

    Returns:
        content of this class as serialized XML (string).
    """

    ID = str(uuid.uuid4())

    mets = m.mets_mets()

    parser = lxml.etree.XMLParser(
        dtd_validation=False, no_network=True)
    tree = lxml.etree.fromstring(content)

    childNodeList = tree.findall('*')
    dmdsec = m.dmdSec(ID, child_elements=childNodeList)
    mets.append(dmdsec)

    return m.serialize(mets)

def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    # print "args.workspace: %s" % args.workspace
    # print "args.dmdsec_location: %s" % args.dmdsec_location
    import_description(args.workspace, args.dmdsec_location)


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="A short description of this "
                                     "program")
    parser.add_argument('dmdsec_location', type=str,
            help='Location of descriptive metadata')
    parser.add_argument('--workspace', dest='workspace', type=str,
            default='./', help="Workspace directory")
    parser.add_argument('--stdout', help='Print output to stdout')

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
