import lxml.etree
from cached_property import cached_property
from siptools.scraper.shell import Shell

from siptools.scraper.basescraper import BaseScraper

NAMESPACES = {'j': 'http://hul.harvard.edu/ois/xml/ns/jhove'}


class JhovePDF(BaseScraper):

    report = None

    @cached_property
    def report(self):
        shell = Shell(['/usr/bin/jhove', '-h', 'XML', self.filename])

        if shell.returncode != 0:
            raise Exception()

        return lxml.etree.fromstring(shell.stdout)

    def _report_field(self, field):
        query = '//j:%s/text()' % field
        results = self.report.xpath(query, namespaces=NAMESPACES)
        return '\n'.join(results)

    @property
    def mimetype(self):
        return self._report_field("mimeType")

    @property
    def file_version(self):
        return self._report_field("version")
