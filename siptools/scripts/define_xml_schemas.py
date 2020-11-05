"""Command line tool for defining XML schemas"""
from __future__ import unicode_literals

import os
import sys
from uuid import uuid4

import click
import six

import lxml.etree as ET

import premis
from siptools.mdcreator import MetsSectionCreator
from siptools.xml.mets import NAMESPACES


click.disable_unicode_literals_warning = True


@click.command()
@click.option(
    '--uri_pairs', nargs=2, type=str, multiple=True, required=True,
    metavar='<SCHEMA URI> <RELATIVE SCHEMA PATH>',
    help="A pair of schema URIs. The first URI is the schema location "
    "URI as defined in the XML file(s). The second URI is the relative "
    "path to the local schema file, given in relation to the current "
    "directory or to --base_path.")
@click.option(
    '--base_path', type=click.Path(exists=True), default='.',
    metavar='<BASE PATH>',
    help="Source base path of local schemas. If used, give schemas in "
         "relation to this base path.")
@click.option(
    '--workspace', type=click.Path(exists=True), default='./workspace/',
    metavar='<WORKSPACE PATH>',
    help="Workspace directory for the metadata files. "
         "Defaults to ./workspace")
@click.option(
    '--stdout', is_flag=True, help='Print result also to stdout.')
# pylint: disable=too-many-arguments
def main(**kwargs):
    """Import a set of XML schema URIs and local schema paths. These
    paths are used to create a premis representation object containing
    the mapping between schemaLocations and the relative locations of
    the schema files that are included in the package.

    """
    define_schemas(**kwargs)
    return 0


def define_schemas(uri_pairs,
                   base_path='.',
                   workspace='./workspace/',
                   stdout=False):
    """Define local schema as a pair of schema URI and path to local
    schema file. The local schemas are collected into a premis
    representation type object.

    :uri_pairs: Tuples of (URI reference and local schema path)
    :workspace: Workspace path
    :base_path: Base path of digital objects
    :stdout: True prints output to stdout
    """
    schemas = {}
    for uri_pair in uri_pairs:
        schemas[uri_pair[0]] = uri_pair[1]

    _check_filepaths(schemas=schemas, base=base_path)

    creator = PremisCreator(workspace)
    creator.add_premis_md(schemas)

    creator.write(stdout=stdout)


class PremisCreator(MetsSectionCreator):
    """Subclass of MetsSectionCreator, which generates PREMIS metadata
    for schema references.
    """

    def add_premis_md(self, schemas):
        """

        Create PREMIS metadata. This method creates PREMIS metadata with
        schema references as a representation type object. The
        representation object is linked to the package root as a
        directory type link.

        :schemas: A dictionary of URI references and local schema paths
        """

        premis_elem = create_premis_representation(schemas)
        self.add_md(premis_elem, directory='.')

    # pylint: disable=too-many-arguments
    def write(self, mdtype="PREMIS:OBJECT", mdtypeversion="2.3",
              othermdtype=None, section=None, stdout=False,
              file_metadata_dict=None,
              ref_file="define-xml-schemas-references.jsonl"):
        """
        Write PREMIS metadata.
        """
        super(PremisCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion,
            ref_file=ref_file, stdout=stdout
        )


def create_premis_representation(schemas):
    """
    Create Premis representation object for given schemas. Each
    schema reference is defined as <premis:dependency> metadata
    within the <premis:environment> section of the representation
    object.

    :schemas: A dictionary of URI references and local schema paths
    :returns: PREMIS object as etree
    """
    object_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=six.text_type(uuid4())
    )
    child_elements = []

    purpose = ET.Element(
        '{%s}environmentPurpose' % NAMESPACES['premis'],
        nsmap=NAMESPACES)
    purpose.text = 'xml-schemas'
    child_elements.append(purpose)

    for schema_ref in schemas:
        dependency_identifier = premis.identifier(
            identifier_type='URI',
            identifier_value=schema_ref,
            prefix='dependency'
        )
        child_elements.append(premis.dependency(
            names=[schemas[schema_ref]],
            identifiers=[dependency_identifier]))

    premis_environment = premis.environment(child_elements=child_elements)

    # Create object element
    el_premis_object = premis.object(
        object_identifier,
        representation=True,
        child_elements=[premis_environment])

    return el_premis_object


def _check_filepaths(schemas=None, base='.'):
    """
    Check the file paths recursively from given directory. Raises error
    if given local schema file path doesn't exist.

    :schemas: A dictionary of URI references and local schema paths
    :base: Base path (see --base_path)

    :raises: IOError if given schema path does not exist.
    """
    for given_path in schemas:
        schema_path = os.path.normpath(os.path.join(base, schemas[given_path]))
        if not os.path.isfile(schema_path):
            raise IOError


if __name__ == "__main__":
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
