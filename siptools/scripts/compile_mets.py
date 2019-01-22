"""Command line tool for creating METS document and copying files to workspace
directory.
"""

import os
import sys
import argparse
import datetime
import uuid
from shutil import copyfile
from scandir import scandir
import lxml.etree
import mets
import xml_helpers.utils as h
from siptools.xml.mets import NAMESPACES, METS_PROFILE, METS_CATALOG, \
    METS_SPECIFICATION, RECORD_STATUS_TYPES, mets_extend
from siptools.utils import get_files


def _dict2str(dictionary):
    """Create a human readable list of words and their explanations from
    dictionary.

    :param dictionary: list of strings
    :returns: dictionary formatted as single string
    """
    items = ['"%s" (%s)' % (item, dictionary[item]) for item in dictionary]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def parse_arguments(arguments):
    """Parse arguments"""
    parser = argparse.ArgumentParser(
        description="Merge partial METS documents in workspace directory into "
                    "one METS document."
    )
    parser.add_argument('mets_profile',
                        metavar='mets_profile',
                        type=str,
                        choices=METS_PROFILE,
                        help='METS profile. Allowed values are: ' +
                        _dict2str(METS_PROFILE) + '.')
    parser.add_argument('organization_name',
                        type=str,
                        help='Creator name (organization)')
    parser.add_argument('contractid',
                        type=str,
                        help='Digital Preservation Contract identifier')
    parser.add_argument('--objid',
                        type=str,
                        default=str(uuid.uuid4()),
                        help='Organizations unique identifier for the package')
    parser.add_argument('--label',
                        type=str,
                        help='Short description of the information package')
    parser.add_argument('--contentid',
                        type=str,
                        help='Identifier for SIP Content')
    parser.add_argument('--create_date',
                        type=str,
                        default=datetime.datetime.utcnow().isoformat(),
                        help='SIP create datetime formatted as '
                             'yyyy-mm-ddThh:mm:ss. Defaults to current time.')
    parser.add_argument('--last_moddate',
                        type=str,
                        help='Last modification datetime formatted as '
                             'yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--record_status',
                        choices=RECORD_STATUS_TYPES,
                        type=str,
                        default='submission',
                        help='Record status. Defaults to "submission".')
    parser.add_argument('--workspace',
                        type=str,
                        default='./workspace',
                        help='Workspace directory. Defaults to "./workspace".')
    parser.add_argument('--clean',
                        action='store_true',
                        help='Remove partial METS documents from workspace '
                             'directory')
    parser.add_argument('--copy_files',
                        action='store_true',
                        help='Copy digital objects from base path to '
                             'workspace')
    parser.add_argument('--base_path',
                        type=str,
                        default='./',
                        help='Base path of the digital objects')
    parser.add_argument('--stdout',
                        action='store_true',
                        help='Print output to stdout.')
    parser.add_argument('--packagingservice',
                        type=str,
                        help='If defined, add packaging service as CREATOR '
                             'agent to METS Header.')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method
    """
    args = parse_arguments(arguments)

    mets_document = create_mets(
        args.workspace,
        mets_attributes={'PROFILE': args.mets_profile,
                         'OBJID': args.objid,
                         'LABEL': args.label,
                         "CONTENTID": args.contentid,
                         "CONTRACTID": args.contractid},
        metshdr_attributes={"CREATEDATE": args.create_date,
                            "LASTMODDATE": args.last_moddate,
                            "RECORDSTATUS": args.record_status},
        organization=args.organization_name,
        packagingservice=args.packagingservice
    )

    if args.stdout:
        print h.serialize(mets_document.getroot())

    output_file = os.path.join(args.workspace, 'mets.xml')

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as outfile:
        outfile.write(h.serialize(mets_document.getroot()))

    print "compile_mets created file: %s" % output_file

    if args.copy_files:
        copy_files(args.workspace, args.base_path)
        print "compile_mets copied objects from %s to workspace" % \
            args.base_path

    if args.clean:
        clean_metsparts(args.workspace)
        print "compile_mets cleaned work files from workspace"

    return 0


def create_mets(workspace, mets_attributes, metshdr_attributes,
                organization, packagingservice=None):
    """Creates METS document element tree. Looks for files with prefix
    "-techmd.xml", "-agent.xml", "-event.xml", "dmdsec.xml", "structmap.xml",
    "filesec.xml", and "rightsmd.xml" from workspace and merges the dmdSec,
    amdSec, fileSec, and structMap elements (one element from each file) into
    one METS document. Also metsHdr element is created and included in
    document.

    :param workspace: path to directory where files are searched
    :param dict mets_attributes: attributes of mets element: "PROFILE",
                                 "OBJID", "LABEL", "CONTENTID", and
                                 "CONTRACTID"
    :param dict metshdr_attributes: attributes of metsHdr element:
                                    "CREATEDATE", "LASTMODDATE" and
                                    "RECORDSTATUS"
    :param organization: name of CREATOR agent
    :param packagingservice: Add ``packagingservice`` as CREATOR agent.
                             ``organization`` is used as ARCHIVIST agent.
    :returns: METS document ElementTree object
    """
    # Create list of agent elements
    if packagingservice:
        agents = [mets.agent(organization, agent_role='ARCHIVIST')]
        agents.append(mets.agent(packagingservice,
                                 agent_type='OTHER',
                                 agent_role='CREATOR',
                                 othertype='SOFTWARE'))
    else:
        agents = [mets.agent(organization, agent_role='CREATOR')]

    # Create mets header
    metshdr = mets.metshdr(metshdr_attributes["CREATEDATE"],
                           metshdr_attributes["LASTMODDATE"],
                           metshdr_attributes["RECORDSTATUS"],
                           agents)

    # Collect elements from workspace XML files
    elements = []
    for entry in scandir(workspace):
        if entry.name.endswith(('-amd.xml', 'dmdsec.xml',
                                'structmap.xml', 'filesec.xml',
                                'rightsmd.xml')) and entry.is_file():
            element = lxml.etree.parse(entry.path).getroot()[0]
            elements.append(element)

    elements = mets.merge_elements('{%s}amdSec' % NAMESPACES['mets'], elements)
    elements.sort(key=mets.order)

    # Create METS element
    mets_element = mets.mets(METS_PROFILE[mets_attributes["PROFILE"]],
                             objid=mets_attributes["OBJID"],
                             label=mets_attributes["LABEL"],
                             namespaces=NAMESPACES)
    mets_element = mets_extend(mets_element,
                               METS_CATALOG,
                               METS_SPECIFICATION,
                               mets_attributes["CONTENTID"],
                               mets_attributes["CONTRACTID"])
    mets_element.append(metshdr)
    for element in elements:
        mets_element.append(element)
    lxml.etree.cleanup_namespaces(mets_element)

    return lxml.etree.ElementTree(mets_element)


def clean_metsparts(path):
    """Clean mets parts from workspace
    """
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            if (name.endswith(('-amd.xml', 'dmdsec.xml', 'structmap.xml',
                               'filesec.xml', 'rightsmd.xml',
                               'amd-references.xml',
                               'siptools-file-properties.json'))):
                os.remove(os.path.join(root, name))


def copy_files(workspace, data_dir):
    """Copy digital objects to workspace
    """
    files = get_files(workspace)
    for source in files:
        target = os.path.join(workspace, source)
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        copyfile(os.path.join(data_dir, source), target)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
