Release notes for Pre-Ingest Tool
=================================

Changes
-------

Version v0.48:

    * Minor fix in README file.

New features added in v0.47:

    * Add support for native files.
    * Add support for ICC color profile name.
    * Fix character encoding issues in error messages.

New features added in v0.46:

    * Add support for national specifications 1.7.2.

New features added in v0.45:

    * import-description

        * ``--dmd_source`` option added, used to document the source of
          the descriptive metadata
        * ``--dmd_agent`` option added, used to document the agent exporting
          the descriptive metadata from the source

    * import-object

        * ``--event_datetime`` option added, used to give a timestamp for
          for the event(s) created by the script, otherwise the current execution
          time of the script is used
        * ``--event_target`` option added, used to give the target for the event(s)
          created by the script, otherwise the FILEPATHS argument value is used

    * premis-event

        * ``--create_agent_file`` option added, used when agent metadata has been
          created by the create-agent script

    * create-agent

        New helper script to create detailed agent metadata for the premis-event
        script and to allow for multiple agents to link to the same event

    The temporary linking files created by the scripts are now jsonl instead of
    XML.

    The temporary pickle files created when importing digital objects have been
    replaced with json files.
    
    The tool has been optimized for improved running time for large packages with
    several files.

Bugfix in v0.28:

    * ``--order`` attribute value (given in import-object) was handled
      inadequately compile-structmap.

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

