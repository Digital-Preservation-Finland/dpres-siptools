""""Command line tool for creating structure map and file metadata for a METS
document."""

import sys
import argparse
import os
import json
from uuid import uuid4
import scandir
import lxml.etree as ET
import mets
import xml_helpers.utils as h
from siptools.xml.mets import NAMESPACES
from siptools.utils import encode_id, encode_path, tree, add, get_files


def ead3_ns(tag):
    """Get tag with EAD3 namespace
    """
    path = '{%s}%s' % ('http://ead3.archivists.org/schema/', tag)
    return path


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line argumets"""

    parser = argparse.ArgumentParser(
        description="Tool for generating METS fileSec and structMap based on "
                    "administrative metada files (-premis-amd.xml -suffix) "
                    "and descriptive metadata files (-dmdsec.xml -suffix) "
                    "found in the workspace directory. Outputs two XML files: "
                    "filesec.xml and structmap.xml"
    )
    parser.add_argument('--dmdsec_struct',
                        type=str,
                        help="Use structured descriptive metadata for "
                             "creating structMap divs")
    parser.add_argument('--dmdsec_loc',
                        type=str,
                        help="Location of structured descriptive metadata")
    parser.add_argument('--type_attr',
                        type=str,
                        help="Type of structmap e.g. 'Fairdata-physical'"
                             " or 'Directory-physical'")
    parser.add_argument('--root_type',
                        type=str,
                        help="Type of root div")
    parser.add_argument('--workspace',
                        type=str,
                        default='./workspace/',
                        help="Destination directory for output files. "
                             "Defaults to ./workspace/")
    parser.add_argument('--stdout',
                        action='store_true',
                        help='Print output also to stdout.')
    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for compile_structmap"""
    args = parse_arguments(arguments)

    fileset = get_files(args.workspace)

    if args.dmdsec_struct == 'ead3':
        # If structured descriptive metadata for structMap divs is used, also
        # the fileSec element (apparently?) is different. The
        # create_ead3_structmap function populates the fileGrp element.
        filegrp = mets.filegrp()
        filesec_element = mets.filesec(child_elements=[filegrp])
        filesec = mets.mets(child_elements=[filesec_element])

        structmap = create_ead3_structmap(args.dmdsec_loc, args.workspace,
                                          filegrp, fileset, args.type_attr)
    else:
        filesec = create_filesec(args.workspace, fileset)
        structmap = create_structmap(args.workspace, filesec.getroot(),
                                     fileset, args.type_attr, args.root_type)

    if args.stdout:
        print h.serialize(filesec)
        print h.serialize(structmap)

    output_sm_file = os.path.join(args.workspace, 'structmap.xml')
    output_fs_file = os.path.join(args.workspace, 'filesec.xml')

    if not os.path.exists(os.path.dirname(output_sm_file)):
        os.makedirs(os.path.dirname(output_sm_file))

    if not os.path.exists(os.path.dirname(output_fs_file)):
        os.makedirs(os.path.dirname(output_fs_file))

    with open(output_sm_file, 'w+') as outfile:
        outfile.write(h.serialize(structmap))

    with open(output_fs_file, 'w+') as outfile:
        outfile.write(h.serialize(filesec))

    print "compile_structmap created files: %s %s" % (output_sm_file,
                                                      output_fs_file)

    return 0


def create_filesec(workspace, fileset):
    """Creates METS document element tree that contains fileSec element.
    """
    filegrp = mets.filegrp()
    filesec = mets.filesec(child_elements=[filegrp])

    directories = div_structure(fileset)
    create_filegrp(workspace, filegrp, fileset)

    mets_element = mets.mets(child_elements=[filesec])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def create_structmap(workspace, filesec, fileset, type_attr=None,
                     root_type=None):
    """Creates METS document element tree that contains structural map.

    :param workspace: directory from which some files are searhed
    :param filesec: fileSec element
    :param fileset: Sorted list of digital objects (file paths)
    :param type_attr: TYPE attribute of div element
    :param root_type: TYPE attribute of div element
    :returns: structural map element
    """

    if os.path.isfile(os.path.join(workspace, 'dmdsec.xml')):
        dmdids = [encode_id('dmdsec.xml')]
    else:
        dmdids = None
    amdids = get_amd_references(workspace, directory='.')

    if type_attr == 'Directory-physical':
        container_div = mets.div(type_attr='directory', label='.',
                                 dmdid=dmdids, admid=amdids)
    else:
        root_type = root_type if root_type else 'directory'
        container_div = mets.div(type_attr=root_type, dmdid=dmdids,
                                 admid=amdids)

    properties = {}
    property_path = os.path.join(workspace, 'siptools-file-properties.json')
    if os.path.isfile(property_path):
        with open(property_path) as infile:
            properties = json.load(infile)

    structmap = mets.structmap(type_attr=type_attr)
    structmap.append(container_div)
    divs = div_structure(fileset)
    create_div(workspace, divs, container_div, filesec,
               fileset, properties=properties, type_attr=type_attr)

    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def get_streams(workspace, path):
    """Get stream indexes of a file

    :workspace: Workspace path
    :path: Path of a digital object in amd-references.xml

    :returns: Sorted set of stream indexes of a file
    """
    reference_file = os.path.join(workspace, 'amd-references.xml')
    xml = ET.parse(reference_file)
    streamset = set()
    streams = xml.xpath(
        '/amdReferences/amdReference[@file="%s"]/@stream' % path)
    for stream in streams:
        streamset.add(stream)
    return sorted(streamset)


def div_structure(fileset):
    """Create div structure for directory-based structmap

    :fileset: Sorted list of digital objects (file paths)
    :returns: Directory tree as a dict like object
    """
    divs = tree()
    for amd_file in fileset:
        add(divs, amd_file.split('/'))
    return divs


def create_ead3_structmap(descfile, workspace, filegrp, fileset, type_attr):
    """Create structmap based on ead3 descriptive metadata structure.

    :desc_file: EAD3 descriptive metadata file
    :workspace: Workspace path
    :structmap: Structmap element
    :filegrp: fileGrp element
    :fileset: Sorted list of digital objects (file paths)
    :dmdsec_id: ID of dmdSec section
    """
    structmap = mets.structmap(type_attr=type_attr)
    container_div = mets.div(type_attr='logical')
    structmap.append(container_div)

    import_xml = ET.parse(descfile)
    root = import_xml.getroot()

    if root.xpath("//ead3:archdesc/@otherlevel", namespaces=NAMESPACES):
        level = root.xpath("//ead3:archdesc/@otherlevel",
                           namespaces=NAMESPACES)[0]
    else:
        level = root.xpath("//ead3:archdesc/@level",
                           namespaces=NAMESPACES)[0]

    if os.path.isfile(os.path.join(workspace, 'dmdsec.xml')):
        dmdids = [encode_id('dmdsec.xml')]
    else:
        dmdids = None
    amdids = get_amd_references(workspace, directory='.')

    div_ead = mets.div(type_attr='archdesc', label=level, dmdid=dmdids,
                       admid=amdids)

    if len(root.xpath("//ead3:archdesc/ead3:dsc", namespaces=NAMESPACES)) > 0:
        for ead3_c in root.xpath("//ead3:dsc/*", namespaces=NAMESPACES):
            if len(ET.QName(ead3_c.tag).localname) > 1:
                cnum = str(ET.QName(ead3_c.tag).localname)[-2:]
            else:
                cnum = None
            ead3_c_div(ead3_c, div_ead, filegrp, workspace, fileset, cnum=cnum)

    structmap.append(div_ead)
    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def ead3_c_div(parent, structmap, filegrp, workspace, fileset, cnum=None):
    """Create div elements based on ead3 c elements. Fptr elements are
    created based on ead dao elements. The Ead3 elements tags are put
    into @type and the @level or @otherlevel attributes from ead3 will
    be put into @label.

    :parent: Element to follow in EAD3
    :div: Div element in structmap
    :filegrp: fileGrp element
    :workspace: Workspace path
    :fileset: Sorted list of digital objects (file paths)
    :cnum: EAD3 c level
    """
    allowed_c_subs = ['c', 'c01', 'c02', 'c03', 'c04', 'c05', 'c06', 'c07',
                      'c08', 'c09', 'c10', 'c11', 'c12']

    if parent.xpath("./@otherlevel"):
        level = parent.xpath("./@otherlevel")[0]
    else:
        level = parent.xpath("./@level")[0]

    if cnum:
        c_div = mets.div(type_attr=('c' + str(cnum)), label=level)
        cnum_sub = str('0') + str(int(cnum) + 1)
    else:
        c_div = mets.div(type_attr='c', label=level)
        cnum_sub = None

    for elem in parent.findall("./*"):
        if ET.QName(elem.tag).localname in allowed_c_subs:
            ead3_c_div(elem, c_div, filegrp, workspace, fileset, cnum=cnum_sub)

    for files in parent.xpath("./ead3:did/*", namespaces=NAMESPACES):
        if ET.QName(files.tag).localname in ['dao', 'daoset']:
            if ET.QName(files.tag).localname == 'daoset':
                ead3_file = files.xpath(
                    "./ead3:dao/@href", namespaces=NAMESPACES)[0]
            else:
                ead3_file = files.xpath("./@href")[0]
            if ead3_file.startswith('/'):
                ead3_file = ead3_file[1:]
            amd_file = [x for x in fileset if ead3_file in x][0]
            fileid = add_file_to_filesec(workspace, amd_file, filegrp)
            dao = mets.fptr(fileid=fileid)
            c_div.append(dao)

    structmap.append(c_div)


def add_file_to_filesec(workspace, path, filegrp):
    """Add file element to fileGrp element given as parameter.

    :param workspace: Workspace directorye from which administrative MD
                      files and amd reference files searched.
    :param path: url encoded path of the file
    :param lxml.etree.Element filegrp: fileGrp element
    :param str returns: id of file added to fileGrp
    :returns: unique identifier of file element
    """
    fileid = '_' + str(uuid4())

    # Create list of IDs of amdID elements
    amdids = get_amd_references(workspace, path=path)

    # Create XML element and add it to fileGrp
    file_el = mets.file_elem(
        fileid,
        admid_elements=set(amdids),
        loctype='URL',
        xlink_href='file://%s' % encode_path(path, safe='/'),
        xlink_type='simple',
        groupid=None
    )

    streams = get_streams(workspace, path)
    if streams:
        for stream in streams:
            stream_ids = get_amd_references(workspace, path=path,
                                            stream=stream)
            stream_el = mets.stream(admid_elements=stream_ids)
            file_el.append(stream_el)

    filegrp.append(file_el)

    return fileid


def get_fileid(filesec, path):
    """Find a file with `path` from fileSec. Returns the ID attribute of
    matching file element.

    :param path: path of the file
    :param lxml.etree Element filesec: fileSec element
    :returns: file element identifier
    """
    encoded_path = encode_path(path, safe='/')
    element = filesec.xpath(
        '//mets:fileGrp/mets:file/mets:FLocat[@xlink:href="file://%s"]/..'
        % encoded_path,
        namespaces=NAMESPACES
    )[0]

    return element.attrib['ID']


def get_amd_references(workspace, path=None, stream=None, directory=None):
    """If administrative MD reference file exists in workspace, read
    the MD IDs that should be referenced for the file, stream or
    directory in question.

    :workspace: path to workspace directory
    :path: path of the file for which MD IDs are read
    :stream: stream index for which MD IDs are read
    :directory: path of the directory for which MD IDs are read
    :returns: a set of administrative MD IDs
    """
    reference_file = os.path.join(workspace, 'amd-references.xml')
    amd_ids = []

    if os.path.isfile(reference_file):
        element_tree = ET.parse(reference_file)
        if directory:
            directory = os.path.normpath(directory)
            reference_elements = element_tree.xpath(
                '/amdReferences/amdReference[@directory="%s"]' % directory
            )
        elif stream is None:
            reference_elements = element_tree.xpath(
                '/amdReferences/amdReference[@file="%s" '
                'and not(@stream)]' % path
            )
        else:
            reference_elements = element_tree.xpath(
                '/amdReferences/amdReference[@file="%s" '
                'and @stream="%s"]' % (path, stream)
            )
        amd_ids = [element.text for element in reference_elements]

    return set(amd_ids)


def create_div(workspace, divs, parent, filesec, fileset, path='',
               properties={}, type_attr=None):
    """Recursively create fileSec and structmap divs based on directory
    structure.

    :param workspace: Workspace path
    :param divs: Current directory or file in directory structure walkthrough
    :param parent: Parent element in structMap
    :param filesec: filesec element
    :param fileset: Sorted list of digital objects (file paths)
    :param path: Current path in directory structure walkthrough
    :param properties: Properties of files created in import_object.py
    :param type_attr: Structmap type
    :returns: ``None``
    """
    fptr_list = []
    property_list = []
    div_list = []
    for div in divs.keys():
        div_path = os.path.join(path, div)
        # It's a file, lets create file+fptr elements
        if div_path in fileset:
            fileid = get_fileid(filesec, div_path)
            fptr = mets.fptr(fileid)
            div_el = add_file_properties(properties, div_path, fptr)
            if div_el is not None:
                property_list.append(div_el)
            else:
                fptr_list.append(fptr)

        # It's not a file, lets create a div element
        else:
            div_path = os.path.join(path, div)
            amdids = get_amd_references(workspace, directory=div_path)
            dmdsec_id = ids_for_files(workspace, div_path, 'dmdsec.xml')
            if type_attr == 'Directory-physical':
                div_el = mets.div(type_attr='directory', label=div,
                                  dmdid=dmdsec_id, admid=amdids)
            else:
                div_el = mets.div(type_attr=div, dmdid=dmdsec_id,
                                  admid=amdids)
            div_list.append(div_el)
            create_div(workspace, divs[div], div_el, filesec, fileset,
                       div_path, properties, type_attr)

    # Add fptr list first, then div list
    for fptr_elem in fptr_list:
        parent.append(fptr_elem)
    for div_elem in property_list:
        parent.append(div_elem)
    for div_elem in div_list:
        parent.append(div_elem)


def create_filegrp(workspace, filegrp, fileset):
    """Add files to fileSec under fileGrp element.

    :param workspace: Workspace path
    :param filegrp: filegrp element in fileSec
    :param fileset: Set of digital objects (file paths)
    :returns: ``None``
    """
    for path in fileset:
        add_file_to_filesec(workspace, path, filegrp)


def add_file_properties(properties, path, fptr):
    """Create a div element with file properties

    :param properties: File properties
    :param path: File path
    :param fptr: Element fptr for file

    :returns: Div element with properties or None
    """
    if properties is None:
        return None
    if encode_path(path) in properties:
        file_properties = properties[encode_path(path)]
        if 'order' in file_properties:
            div_el = mets.div(type_attr='file',
                              order=file_properties['order'])
            div_el.append(fptr)
            return div_el
    return None


def ids_for_files(workspace, path, idtype, dash_count=0):
    """Search files in workspace based on keywords or number of dashes in
    filename, and create ID for each found file.

    :param str workspace: Path to directory from which the files are searched
    :param str path: If not None, False, or 0, only return filenames that
                     contain this word
    :param str idtype: Only return filenames that contain this word
    :param int dash_count: If path is None, False, or 0, return filenames that
                           have this many dashes
    :returns (list): List of ids of found files
    """
    # Find all files from workspace directory and filter out filenames that do
    # not contain idtype
    workspace_filenames = [fname.name for fname in scandir.scandir(workspace)]
    md_files = [x for x in workspace_filenames if idtype in x]

    if path:
        # Filter filenames based on path
        files_result = [x for x in md_files
                        if encode_path(path) in x and (path+'%2F') not in x]
    else:
        # Filter filenames based on number of '-'-characters in filename
        files_result = [x for x in md_files if x.count('-') == dash_count]

    # Create IDs for files
    id_result = [encode_id(x) for x in files_result]

    return id_result


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
