"""End to end test for the siptools package."""

import sys
import os
import subprocess
import pytest


@pytest.mark.skipif('ipt' not in sys.modules, reason='Requires ipt')
def test_end_to_end(testpath):
    """Test creation of SIP and asserting the validity
    of the created mets document with validation tools.
    """

    objects = 'tests/data/single/text-file.txt'
    dmd_file = 'tests/data/import_description/metadata/dc_description.xml'
    dmd_target = 'tests/data/single'
    file_to_sign = 'mets.xml'
    private_key = 'tests/data/rsa-keys.crt'

    environment = os.environ.copy()
    environment['PYTHONPATH'] = '.'

    command = ['python', 'siptools/scripts/import_object.py',
               '--workspace', testpath, objects, '--skip_inspection',
               '--format_name', 'text/plain', '--format_version', '1.0',
               '--digest_algorithm', 'MD5', '--message_digest',
               '1qw87geiewgwe9', '--date_created', '2017-01-11T10:14:13',
               '--charset', 'ISO-8859-15']
    child = subprocess.Popen(command, env=environment)
    child.communicate()
    assert child.returncode == 0

    command = ['python', 'siptools/scripts/premis_event.py', 'creation',
               '2017-01-11T10:14:13', '--event_detail', 'Testing',
               '--event_outcome', 'success', '--event_outcome_detail',
               'Outcome detail', '--workspace', testpath, '--agent_name',
               'Demo Application', '--agent_type', 'software',
               '--event_target', objects]
    child = subprocess.Popen(command, env=environment)
    child.communicate()
    assert child.returncode == 0

    command = ['python', 'siptools/scripts/import_description.py', dmd_file,
               '--workspace', testpath, '--dmdsec_target', dmd_target,
               '--desc_root']
    child = subprocess.Popen(command, env=environment)
    child.communicate()
    assert child.returncode == 0

    command = ['python', 'siptools/scripts/compile_structmap.py',
               '--workspace', testpath]
    child = subprocess.Popen(command, env=environment)
    child.communicate()
    assert child.returncode == 0

    command = ['python', 'siptools/scripts/compile_mets.py',
               '--workspace', testpath, 'ch', 'CSC',
               'contract-id-1234', '--create_date', '2017-01-11T10:14:13',
               '--copy_files', '--clean']
    child = subprocess.Popen(command, env=environment)
    child.communicate()
    assert child.returncode == 0

    command = ['python', 'siptools/scripts/sign_mets.py',
               '--workspace', testpath, private_key]
    child = subprocess.Popen(command, env=environment)
    child.communicate()
    assert child.returncode == 0

    command = ['python', 'siptools/scripts/compress.py',
               '--tar_filename', os.path.join(testpath, 'sip.tar'), testpath]
    child = subprocess.Popen(command, env=environment)
    child.communicate()
    assert child.returncode == 0

    schematron_path = '/usr/share/dpres-xml-schemas/schematron/'
    schematron_rules = [
        'mets_addml.sch',
        'mets_amdsec.sch',
        'mets_audiomd.sch',
        'mets_digiprovmd.sch',
        'mets_dmdsec.sch',
        'mets_ead3.sch',
        'mets_filesec.sch',
        'mets_mdwrap.sch',
        'mets_metshdr.sch',
        'mets_mix.sch',
        'mets_mods.sch',
        'mets_premis_digiprovmd.sch',
        'mets_premis_rightsmd.sch',
        'mets_premis.sch',
        'mets_premis_techmd.sch',
        'mets_rightsmd.sch',
        'mets_root.sch',
        'mets_sourcemd.sch',
        'mets_structmap.sch',
        'mets_techmd.sch',
        'mets_videomd.sch'
    ]
    for rule in schematron_rules:
        rule_path = os.path.join(schematron_path, rule)
        command = ['check-xml-schematron-features', '-s',
                   rule_path, os.path.join(testpath, file_to_sign)]
        child = subprocess.Popen(command, env=environment)
        child.communicate()
        assert child.returncode == 0
