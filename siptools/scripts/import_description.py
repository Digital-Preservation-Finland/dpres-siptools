""" import_description"""

from siptools.xml.namespaces import NAMESPACES, METS_NS

import re
import sys
import argparse
import os
import shutil
import lxml.etree
from lxml.etree import Element, SubElement, tostring
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

    el_root = Element("{%s}mets" % NAMESPACES['mets'], nsmap=NAMESPACES)
    #el_root.set(XSI + 'schemaLocation', METS_SCHEMALOCATION)

    el_dmdsec = Element("{%s}dmdSec" % NAMESPACES['mets'], nsmap=NAMESPACES)
    el_dmdsec.set("ID", ID)
    el_dmdsec.set("CREATED", get_edtf_time())
    el_root.append(el_dmdsec)

    el_mdwrap = Element("{%s}mdWrap" % NAMESPACES['mets'], nsmap=NAMESPACES)
    el_dmdsec.append(el_mdwrap)

    el_xmldata = Element("{%s}xmlData" % NAMESPACES['mets'], nsmap=NAMESPACES)

    try:
        parser = lxml.etree.XMLParser(
            dtd_validation=False, no_network=True)
        tree = lxml.etree.fromstring(content)

        childNodeList = tree.findall('*')

        for node in childNodeList:
            el_xmldata.append(node)
            ns = namespace(node)[1:-1]
            if ns in METS_NS.keys():
                el_mdwrap.set("MDTYPE", METS_NS[ns]['mdtype'])
            else:
                raise TypeError("Invalid namespace: %s" % ns)

    except lxml.etree.XMLSyntaxError as exception:
        el_xmldata.text = content.decode("utf-8")

    el_mdwrap.append(el_xmldata)

    return tostring(el_root, pretty_print=True, xml_declaration=True,
                    encoding='UTF-8')


def get_edtf_time():
    """return current time in format yyy-mm-ddThh:mm:ss"""
    time_now = datetime.datetime.now()
    localtz = dateutil.tz.tzlocal()
    timezone_offset = localtz.utcoffset(time_now)
    timezone_offset = (timezone_offset.days * 86400 +
                       timezone_offset.seconds) / 3600
    return time_now.strftime('%Y-%m-%dT%H:%M:%S')


def namespace(element):
    """return xml element's namespace"""
    m = re.match('\{.*\}', element.tag)
    return m.group(0) if m else ''


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
    parser.add_argument('dmdsec_location')
    argparse._StoreAction(option_strings=[], dest='dmdsec_location', nargs=None,
                          const=None, default=None, type=None, choices=None, help=None, metavar=None)
    parser.add_argument('--workspace', default='./')
    argparse._StoreAction(option_strings=['--workspace'], dest='workspace',
                          nargs=None, const=None, default='./', type=None, choices=None, help=None, metavar=None)

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
