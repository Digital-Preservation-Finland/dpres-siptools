import subprocess

from siptools.scraper import jhove


def scraper(fname):

    mimetype = subprocess.Popen('/usr/bin/file --mime-type %s' % fname,
                                shell=True, stdout=subprocess.PIPE).communicate()[0]
    mimetype = mimetype.split(' ')[1]

    return jhove.JhovePDF(fname)
