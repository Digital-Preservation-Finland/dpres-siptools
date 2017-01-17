from tempfile import NamedTemporaryFile
import os
import pytest
import subprocess

def test_end_to_end(testpath):

    testpath = './workspace'
    objects = 'tests/data/single/text-file.txt'
    dmd_file = 'tests/data/import_description/metadata/dc_description.xml'
    dmd_target = 'tests/data/single'
    structmap_dir = 'tests/data/single'
    file_to_sign = os.path.join(testpath, 'mets.xml')
    signature_filename = '/home/vagrant/siptools/workspace/signature.sig'
    private_key = 'tests/data/rsa-keys.crt'
    dir_to_tar = 'tests/data/single'



    command = ['python', 'siptools/scripts/import_object.py',
        '--output', testpath, objects, '--skip_inspection' , '1', '--format_name',
        'image/dpx', '--format_version', '1.0', '--digest_algorithm', 'MD5',
        '--message_digest', '1qw87geiewgwe9', '--date_created', '2017-01-11T10:14:13']
    subprocess.Popen(command)

    command = ['python', 'siptools/scripts/premis_event.py', 'creation',
            '2017-01-11T10:14:13', '--event_detail', 'Testing',
            '--event_outcome', 'success', '--event_outcome_detail', 
            'Outcome detail', '--workspace', testpath, '--agent_name', 
            'Demo Application', '--agent_type', 'software']
    subprocess.Popen(command)

    command = ['python', 'siptools/scripts/import_description.py', dmd_file,
            '--dmdsec_target', dmd_target, '--workspace', testpath]
    subprocess.Popen(command)

    command = ['python', 'siptools/scripts/compile_structmap.py',
            structmap_dir, '--workspace', testpath]
    subprocess.Popen(command)

    command = ['python', 'siptools/scripts/compile_mets.py',
            '--workspace', testpath, 'kdk', 'CSC']
    subprocess.Popen(command)

    command = ['python', 'siptools/scripts/sign_mets.py',
            file_to_sign, signature_filename, private_key]
    subprocess.Popen(command)

    #command = ['python', 'siptools/scripts/compress.py',
    #        dir_to_tar]
    #subprocess.Popen(command)

    command = ['check-xml-schematron-features', '-s',
            '/usr/share/information-package-tools/kdk-schematron/mets_internal.sch',
            file_to_sign]
    subprocess.Popen(command)
