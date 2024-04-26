"""Functions and classes for importing PREMIS representation objects."""
import premis
from siptools.mdcreator import MetsSectionCreator


def import_representation_object(workspace, object_id, alt_id, original_name,
                                 target_filepath):
    """
    Import premis representation objects.
    :workspace: Workspace path
    :object_id: PREMIS representation object's identifier value
    :alt_id: PREMIS representation object's alternative identifier value
    :original_name: PREMIS representation object's original name
    :target_filepath: Filepath of the outcome file
    """
    creator = PremisRepresentationCreator(workspace)
    creator.add_premis_md(object_id, alt_id, original_name, target_filepath)
    creator.write()


class PremisRepresentationCreator(MetsSectionCreator):
    """
    Subclass of MetsSectionCreator. Generates PREMIS metadata for
    representation objects.
    """
    def add_premis_md(self, object_id, alt_id, original_name,
                      target_filepath):
        """
        Create PREMIS metadata. This method creates PREMIS metadata with
        given arguments as a representation type object. It also adds a
        linking between the representation object and the target file.
        :object_id: PREMIS representation object's identifier value
        :alt_id: PREMIS representation object's alternative identifier value
        :original_name: PREMIS representation object's original name
        :target_filepath: Filepath of the outcome file
        """
        el_premis_object = create_premis_representation(object_id,
                                                        alt_id,
                                                        original_name)
        self.add_md(el_premis_object,
                    filename=target_filepath)

    def write(self, mdtype="PREMIS:OBJECT", mdtypeversion="2.3",
              othermdtype=None, section="digiprovmd", stdout=False,
              file_metadata_dict=None,
              ref_file="import-object-md-references.jsonl"):
        """Write PREMIS metadata."""
        super().write(
            mdtype=mdtype, mdtypeversion=mdtypeversion, section=section,
            file_metadata_dict=file_metadata_dict, ref_file=ref_file
        )


def create_premis_representation(object_id,
                                 alt_id,
                                 original_name):
    """
    Create premis representation object with given arguments.
    :object_id: PREMIS representation object's identifier value
    :alt_id: PREMIS representation object's alternative identifier value
    :original_name: PREMIS representation object's original name
    :returns: PREMIS object element
    """
    object_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=object_id)

    object_alt_id = premis.identifier(
        identifier_type='local',
        identifier_value=alt_id)

    el_premis_object = premis.object(
        object_identifier,
        alt_ids=[object_alt_id],
        original_name=original_name,
        representation=True)

    return el_premis_object
