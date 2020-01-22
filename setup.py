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
        include_package_data=True,
        version=get_version(),
        install_requires=[
            "lxml",
            "scandir",
            "file-magic",
            "pymediainfo",
            "wand>=0.5.1",
            "Pillow",
            "six",
            "olefile",
            "opf-fido==1.4.0",
            "click",
            "ffmpeg-python",
            "M2Crypto",
            "python-mimeparse",
            'xml_helpers@git+https://gitlab.csc.fi/dpres/xml-helpers.git@develop',
            'mets@git+https://gitlab.csc.fi/dpres/mets.git@develop',
            'premis@git+https://gitlab.csc.fi/dpres/premis.git@develop',
            'dpres_signature@git+https://gitlab.csc.fi/dpres/dpres-signature.git@develop',
            'nisomix@git+https://gitlab.csc.fi/dpres/nisomix.git@develop',
            'addml@git+https://gitlab.csc.fi/dpres/addml.git@develop',
            'audiomd@git+https://gitlab.csc.fi/dpres/audiomd.git@develop',
            'videomd@git+https://gitlab.csc.fi/dpres/videomd.git@develop',
            'file_scraper@git+https://gitlab.csc.fi/dpres/file-scraper.git@develop'
        ],
        entry_points={'console_scripts': scripts_list()}

    )


if __name__ == '__main__':
    main()
