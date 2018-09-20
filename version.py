"""
Gets the current version number.
If in a git repository, it is the current git tag.
Otherwise it is the one contained in the PKG-INFO file.
 
To use this script, simply import it in your setup.py file
and use the results of get_version() as your package version:
 
    from version import *
 
    setup(
        ...
        version=get_version(),
        ...
    )
"""

__all__ = ('get_version')

import os.path
import re
from subprocess import CalledProcessError, Popen, PIPE


version_re = re.compile('^Version: (.+)$', re.M)


def call_git_describe():
    cmd = 'git describe --abbrev --tags --match v[0-9]*'.split()
    print ' '.join(cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = p.communicate()
    return stdout.strip()


def write_pkg_info():

    if os.path.isfile('PKG-INFO'):
        return

    d = os.path.abspath(os.path.dirname(__file__))
    try:
        version = re.match(r".*-v([\d\.]+-[^-]+-g[^/]+)", d).group(1)
    except:
        version = '0.0'

    print "%s: Writing version info to '%s'..." % (__file__, os.path.abspath('PKG-INFO'))
    f = open(os.path.join(d, 'PKG-INFO'), 'w')
    f.write("Metadata-Version: 1.0\n")
    f.write("Name: information-package-tools\n")
    f.write("Version: %s\n" % version)
    f.write("Summary: UNKNOWN\n")
    f.write("Home-page: UNKNOWN\n")
    f.write("Author: UNKNOWN\n")
    f.write("Author-email: UNKNOWN\n")
    f.write("License: UNKNOWN\n")
    f.write("Description: UNKNOWN\n")
    f.write("Platform: UNKNOWN\n")
    f.close()


def get_version():
    d = os.path.dirname(__file__)

    if os.path.isdir(os.path.join(d, '../../.git')):
        # Get the version using "git describe".
        version_git = call_git_describe()

        # PEP 386 compatibility
        if version_git:
            version = "%s-%s" % (
                '.post'.join(version_git.split('-')[:2]),
                '-'.join(version_git.split('-')[2:])
            )

        print "Version number from GIT repository: " + version
    else:
        write_pkg_info()
        # Extract the version from the PKG-INFO file.
        with open(os.path.join(d, 'PKG-INFO')) as f:
            version = version_re.search(f.read()).group(1)
        print "Version number from PKG-INFO: " + version

    return version


if __name__ == '__main__':
    print(get_version())
