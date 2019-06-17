Release notes for Pre-Ingest Tool
=================================

Changes
-------

New features added in v0.27:

    * import-description

        * ``--base_path`` option added, ``--dmdsec_target`` is now given in
          relation to ``-base_path`` if both are used
        * ``--without_uuid`` option added that allows to write the dmdSec file
          name without a UUID prefix
        * support for multiple dmdSecs refering to the same ``--dmdsec_target``

    * premis_event

        * ``--base_path`` option added, ``--event_target`` is now given in
          relation to ``-base_path`` if both are used

    * create_audiomd

        * fix bug where dataRate was given as a floating point number instead
          of as an integer

    * other bug fixes code refactoring

Backwards compatibility
-----------------------

This version of the tool is not backward-compatible with version v0.20 or older versions. The
non-compatible differences in the script arguments are following:

    * import-object

        * ``--skip_inspection`` is changed to ``--skip_wellformed_check``.
        * ``--digest_algorithm`` and ``--message_digest`` have been combined to ``--checksum``.
        * ``--format_name`` and ``--format_version`` have been combined to ``--file_format``.

    * create-addml

        * ``--no-header`` has been removed as unnecessary.

    * import-description

        * ``--desc_root`` has been changed to ``--remove_root``.

    * compile-structmap

        * ``--dmdsec_struct`` is removed and merged to ``--structmap_type``.
        * ``--type_attr`` is changed to ``--structmap_type``.

