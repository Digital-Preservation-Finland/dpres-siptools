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
        entry_points={'console_scripts': scripts_list()}

    )


if __name__ == '__main__':
    main()
