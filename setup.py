"""
Install siptools
"""

import os
from setuptools import setup, find_packages
from version import get_version


def scripts_list():
    """Return list of command line tools from package pas.scripts"""
    scripts = []
    for modulename in os.listdir('siptools/scripts'):
        if modulename == '__init__.py':
            continue
        if not modulename.endswith('.py'):
            continue
        modulename = modulename.replace('.py', '')
        scriptname = modulename.replace('_', '-')
        scripts.append(
            '%s = siptools.scripts.%s:main' % (scriptname, modulename)
        )
    print(scripts)
    return scripts


def main():
    """Install siptools"""
    setup(
        name='siptools',
        packages=find_packages(exclude=['tests', 'tests.*']),
        version=get_version(),
        install_requires=[
            "lxml",
            "scandir",
            "file-magic",
            "wand",
            "Pillow",
            "ffmpeg-python",
            "xml_helpers",
            "mets",
            "premis",
            "dpres_signature",
            "nisomix",
            "addml",
            "audiomd"
            "videomd"
        ],
        dependency_links=[
            'git+https://gitlab.csc.fi/dpres/xml-helpers.git'
            '@develop#egg=xml_helpers-0.0',
            'git+https://gitlab.csc.fi/dpres/mets.git@develop#egg=mets-0.0',
            'git+https://gitlab.csc.fi/dpres/premis.git'
            '@develop#egg=premis-0.0',
            'git+https://gitlab.csc.fi/dpres/dpres-signature.git'
            '@develop#egg=dpres_signature-0.0',
            'git+https://gitlab.csc.fi/dpres/nisomix.git'
            '@develop#egg=nisomix-0.0',
            'git+https://gitlab.csc.fi/dpres/addml.git@develop#egg=addml-0.0',
            'git+https://gitlab.csc.fi/dpres/audiomd.git@develop#egg=audiomd-0.0'
            'git+https://gitlab.csc.fi/dpres/videomd.git@develop#egg=videomd-0.0'
        ],
        entry_points={'console_scripts': scripts_list()}

    )


if __name__ == '__main__':
    main()
