""" dmdsec"""

from siptools.xml.namespaces import METS_NAMESPACE, METS_NS

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

#METS_NS="http://www.loc.gov/METS/"
#METS = "{%s}" % METS_NS
#METS_SCHEMALOCATION = "http://www.loc.gov/METS/ http://kdk.fi/standards/mets/mets.xsd"

#XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

#XSI = "{%s}" % XSI_NS
#NAMESPACES = {'mets': METS_NS, 'xsi': XSI_NS}

def import_description():
    """ kuvaus """

    dmd_source_path = 'workspace/metadata/'
    dmd_result_path = 'workspace/mets-parts/'

    source_path = os.path.abspath(dmd_source_path)
    result_path = os.path.abspath(dmd_result_path) 

    for root, dirs, files in os.walk(source_path, topdown=False):
        for name in files:
            s_path = os.path.join(root, name)
            t_path = os.path.join(result_path, name) 
            print "copying %s to %s" % (s_path, result_path)
            with open(s_path, 'r') as content_file:
                content = content_file.read()

            with open(t_path, 'w') as target_file:
                target_file.write(serialize(content))


def serialize(content):
    """
    Serialize encapsulated objects to XML.

    Returns:
        content of this class as serialized XML (string).
    """

    ID = str(uuid.uuid4())

    el_root = Element("mets", nsmap=METS_NAMESPACE)
    #el_root.set(XSI + 'schemaLocation', METS_SCHEMALOCATION)

    el_dmdsec = Element("dmdSec", nsmap=METS_NAMESPACE) 
    el_dmdsec.set("ID", ID)
    el_dmdsec.set("CREATED", get_edtf_time())
    el_root.append(el_dmdsec)

    el_mdwrap = Element("mdWrap", nsmap=METS_NAMESPACE) 
    el_dmdsec.append(el_mdwrap)

    el_xmldata = Element("xmlData", nsmap=METS_NAMESPACE) 

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

    except lxml.etree.XMLSyntaxError as exception:
        el_xmldata.text = content.decode("utf-8")

    el_mdwrap.append(el_xmldata)

    return tostring(el_root, pretty_print=True, xml_declaration=True,
                                    encoding='UTF-8')

def get_edtf_time():
    time_now = datetime.datetime.now()
    localtz = dateutil.tz.tzlocal()
    timezone_offset = localtz.utcoffset(time_now)
    timezone_offset = (timezone_offset.days * 86400 +
            timezone_offset.seconds) / 3600
    return time_now.strftime('%Y-%m-%dT%H:%M:%S')

def namespace(element): 
    m = re.match('\{.*\}', element.tag)
    return m.group(0) if m else ''

def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="A short description of this "
            "program")
    parser.add_argument('message', help="Positional argument which "
            "is needed for program to start.")
    parser.add_argument('-n', dest='print_count', type=int, default=3,
            help='Optional integer argument which defaults to 3.')

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
