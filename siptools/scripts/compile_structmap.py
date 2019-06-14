""""Command line tool for creating the structural map and file section
metadata for a METS document."""

import sys
import os
from uuid import uuid4
import pickle
import click
import lxml.etree as ET
import mets
import xml_helpers.utils as h
from siptools.xml.mets import NAMESPACES
from siptools.utils import encode_path, tree, add, get_objectlist


ALLOWED_C_SUBS = ['c', 'c01', 'c02', 'c03', 'c04', 'c05', 'c06', 'c07',
                  'c08', 'c09', 'c10', 'c11', 'c12']


def ead3_ns(tag):
    """Get tag with EAD3 namespace
    """
    path = '{%s}%s' % ('http://ead3.archivists.org/schema/', tag)
    return path


@click.command()
@click.option('--workspace',
              type=click.Path(exists=True), default='./workspace/',
              metavar='<WORKSPACE PATH>',
              help="Workspace directory. Defaults to ./workspace/")
@click.option('--structmap_type',
              type=str,
              metavar='<STRUCTMAP TYPE>',
              help="Type of structmap e.g. 'Fairdata-physical', "
                   "'EAD3-logical', or 'Directory-physical'")
@click.option('--root_type',
              metavar='<ROOT TYPE>',
              type=str, help="Type of root div")
@click.option('--dmdsec_loc',
              type=str,
              metavar='<DMD LOCATION>',
              help="Location of structured descriptive metadata, "
                   "if applicable.")
@click.option('--stdout',
              is_flag=True,
              help='Print output also to stdout.')
def main(workspace, structmap_type, root_type, dmdsec_loc, stdout):
    """Tool for generating METS file section and structural map based on
    created/imported administrative metada and descriptive metadata.
    The script will also add order of the file to the structural map
    (via pickle file), if --order argument was used in import_object script.
    """
    compile_structmap(workspace, structmap_type, root_type, dmdsec_loc, stdout)

    return 0


def compile_structmap(workspace="./workspace/", structmap_type=None,
                      root_type=None, dmdsec_loc=None, stdout=False):
    """Generate METS file section and structural map based on
    created/imported administrative metada and descriptive metadata.
    """
    filelist = get_objectlist(workspace)

    if structmap_type == 'EAD3-logical':
        # If structured descriptive metadata for structMap divs is used, also
        # the fileSec element (apparently?) is different. The
        # create_ead3_structmap function populates the fileGrp element.
        filegrp = mets.filegrp()
        filesec_element = mets.filesec(child_elements=[filegrp])
        filesec = mets.mets(child_elements=[filesec_element])

        structmap = create_ead3_structmap(dmdsec_loc, workspace,
                                          filegrp, filelist, structmap_type)
    else:
        filesec = create_filesec(workspace, filelist)
        structmap = create_structmap(workspace, filesec.getroot(),
                                     filelist, structmap_type, root_type)

    if stdout:
        print h.serialize(filesec)
        print h.serialize(structmap)

    output_sm_file = os.path.join(workspace, 'structmap.xml')
    output_fs_file = os.path.join(workspace, 'filesec.xml')

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


def create_filesec(workspace, filelist):
    """Creates METS document element tree that contains fileSec element.
    """
    filegrp = mets.filegrp()
    filesec = mets.filesec(child_elements=[filegrp])

    create_filegrp(workspace, filegrp, filelist)

    mets_element = mets.mets(child_elements=[filesec])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def create_structmap(workspace, filesec, filelist, type_attr=None,
                     root_type=None):
    """Creates METS document element tree that contains structural map.

    :param workspace: directory from which some files are searhed
    :param filesec: fileSec element
    :param filelist: Sorted list of digital objects (file paths)
    :param type_attr: TYPE attribute of structMap element
    :param root_type: TYPE attribute of root div element
    :returns: structural map element
    """

    amdids = get_md_references(workspace, directory='.')
    dmdids = get_md_references(workspace, directory='.', ref_type='dmd')

    if type_attr == 'Directory-physical':
        container_div = mets.div(type_attr='directory', label='.',
                                 dmdid=dmdids, admid=amdids)
    else:
        root_type = root_type if root_type else 'directory'
        container_div = mets.div(type_attr=root_type, dmdid=dmdids,
                                 admid=amdids)

    structmap = mets.structmap(type_attr=type_attr)
    structmap.append(container_div)
    divs = div_structure(filelist)
    create_div(workspace, divs, container_div, filesec,
               filelist, type_attr=type_attr)

    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def div_structure(filelist):
    """Create div structure for directory-based structmap

    :filelist: Sorted list of digital objects (file paths)
    :returns: Directory tree as a dict like object
    """
    divs = tree()
    for amd_file in filelist:
        add(divs, amd_file.split('/'))
    return divs


def create_ead3_structmap(descfile, workspace, filegrp, filelist, type_attr):
    """Create structmap based on ead3 descriptive metadata structure.

    :desc_file: EAD3 descriptive metadata file
    :workspace: Workspace path
    :structmap: Structmap element
    :filegrp: fileGrp element
    :filelist: Sorted list of digital objects (file paths)
    :type_attr: TYPE attribute of structMap element
    """
    structmap = mets.structmap(type_attr=type_attr)
    container_div = mets.div(type_attr='logical')

    root = ET.parse(descfile).getroot()

    try:
        label = root.xpath(("//ead3:archdesc/@otherlevel | "
                            "//ead3:archdesc/@level"),
                           namespaces=NAMESPACES)[0]
    except IndexError:
        label = 'archdesc'

    amdids = get_md_references(workspace, directory='.')
    dmdids = get_md_references(workspace, directory='.', ref_type='dmd')

    div_ead = mets.div(type_attr='archdesc', label=label, dmdid=dmdids,
                       admid=amdids)

    if len(root.xpath("//ead3:archdesc/ead3:dsc", namespaces=NAMESPACES)) > 0:
        for elem in root.xpath("//ead3:dsc/*", namespaces=NAMESPACES):
            if ET.QName(elem.tag).localname in ALLOWED_C_SUBS:
                ead3_c_div(elem, div_ead, filegrp, workspace, filelist)

    container_div.append(div_ead)
    structmap.append(container_div)
    mets_element = mets.mets(child_elements=[structmap])
    ET.cleanup_namespaces(mets_element)
    return ET.ElementTree(mets_element)


def ead3_c_div(parent, structmap, filegrp, workspace, filelist):
    """Create div elements based on ead3 c elements. Fptr elements are
    created based on ead dao elements. The Ead3 elements tags are put
    into @type and the @level or @otherlevel attributes from ead3 will
    be put into @label.

    :parent: Element to follow in EAD3
    :div: Div element in structmap
    :filegrp: fileGrp element
    :workspace: Workspace path
    :filelist: Sorted list of digital objects (file paths)
    """

    try:
        label = parent.xpath(("./@otherlevel | ./@level"),
                             namespaces=NAMESPACES)[0]
    except IndexError:
        label = ET.QName(parent.tag).localname

    c_div = mets.div(type_attr=(ET.QName(parent.tag).localname), label=label)

    for elem in parent.findall("./*"):
        if ET.QName(elem.tag).localname in ALLOWED_C_SUBS:
            ead3_c_div(elem, c_div, filegrp, workspace, filelist)

    for elem in parent.xpath("./ead3:did/*", namespaces=NAMESPACES):
        if ET.QName(elem.tag).localname in ['dao', 'daoset']:
            if ET.QName(elem.tag).localname == 'daoset':
                ead3_file = elem.xpath(
                    "./ead3:dao/@href", namespaces=NAMESPACES)[0]
            else:
                ead3_file = elem.xpath("./@href")[0]
            if ead3_file.startswith('/'):
                ead3_file = ead3_file[1:]
            amd_file = [x for x in filelist if ead3_file in x][0]
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
    amdids = get_md_references(workspace, path=path)

    # Create XML element and add it to fileGrp
    file_el = mets.file_elem(
        fileid,
        admid_elements=set(amdids),
        loctype='URL',
        xlink_href='file://%s' % encode_path(path, safe='/'),
        xlink_type='simple',
        groupid=None
    )

    streams = get_objectlist(workspace, path)
    if streams:
        for stream in streams:
            stream_ids = get_md_references(workspace, path=path,
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


def get_md_references(workspace, path=None, stream=None, directory=None,
                      ref_type='amd'):
    """If MD reference file exists in workspace, read
    the MD IDs that should be referenced for the file, stream or
    directory in question. MD reference references to either an
    administrative metadata section or a descriptove metadata section.

    :workspace: path to workspace directory
    :path: path of the file for which MD IDs are read
    :stream: stream index for which MD IDs are read
    :directory: path of the directory for which MD IDs are read
    :ref_type: type of metadata section, e.g. amd or dmd
    :returns: a set of administrative MD IDs
    """
    reference_file = os.path.join(workspace, 'amd-references.xml')
    amd_ids = []

    if os.path.isfile(reference_file):
        element_tree = ET.parse(reference_file)
        if directory:
            directory = os.path.normpath(directory)
            reference_elements = element_tree.xpath(
                '/amdReferences/amdReference'
                '[@directory="%s" and @ref_type="%s"]' % (
                    directory, ref_type)
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


def create_div(workspace, divs, parent, filesec, filelist, path='',
               type_attr=None):
    """Recursively create fileSec and structmap divs based on directory
    structure.

    :param workspace: Workspace path
    :param divs: Current directory or file in directory structure walkthrough
    :param parent: Parent element in structMap
    :param filesec: filesec element
    :param filelist: Sorted list of digital objects (file paths)
    :param path: Current path in directory structure walkthrough
    :param type_attr: Structmap type
    :returns: ``None``
    """
    fptr_list = []
    property_list = []
    div_list = []
    for div in divs.keys():
        div_path = os.path.join(path, div)
        # It's a file, lets create file+fptr elements
        if div_path in filelist:
            fileid = get_fileid(filesec, div_path)
            fptr = mets.fptr(fileid)
            div_el = add_file_properties(workspace, div_path, fptr)
            if div_el is not None:
                property_list.append(div_el)
            else:
                fptr_list.append(fptr)

        # It's not a file, lets create a div element
        else:
            div_path = os.path.join(path, div)
            amdids = get_md_references(workspace, directory=div_path)
            dmdsec_id = get_md_references(workspace, directory=div_path,
                                          ref_type='dmd')
            if type_attr == 'Directory-physical':
                div_el = mets.div(type_attr='directory', label=div,
                                  dmdid=dmdsec_id, admid=amdids)
            else:
                div_el = mets.div(type_attr=div, dmdid=dmdsec_id,
                                  admid=amdids)
            div_list.append(div_el)
            create_div(workspace, divs[div], div_el, filesec, filelist,
                       div_path, type_attr)

    # Add fptr list first, then div list
    for fptr_elem in fptr_list:
        parent.append(fptr_elem)
    for div_elem in property_list:
        parent.append(div_elem)
    for div_elem in div_list:
        parent.append(div_elem)


def create_filegrp(workspace, filegrp, filelist):
    """Add files to fileSec under fileGrp element.

    :param workspace: Workspace path
    :param filegrp: filegrp element in fileSec
    :param filelist: Set of digital objects (file paths)
    :returns: ``None``
    """
    for path in filelist:
        add_file_to_filesec(workspace, path, filegrp)


def add_file_properties(workspace, path, fptr):
    """Create a div element with file properties

    :param properties: File properties
    :param path: File path
    :param fptr: Element fptr for file

    :returns: Div element with properties or None
    """

    amdref = next(iter(get_md_references(workspace, path=path)))
    pkl_name = os.path.join(
        workspace, '{}-scraper.pkl'.format(amdref[1:]))

    if not os.path.isfile(pkl_name):
        return None

    with open(pkl_name, 'r') as pkl_file:
        file_metadata_dict = pickle.load(pkl_file)

    properties = {}
    if 'properties' not in file_metadata_dict[0]:
        return None
    else:
        properties = file_metadata_dict[0]['properties']

    if 'order' in properties:
        div_el = mets.div(type_attr='file',
                          order=properties['order'])
        div_el.append(fptr)
        return div_el

    return None


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
