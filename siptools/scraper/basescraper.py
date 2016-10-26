import hashlib
import os.path
from cached_property import cached_property


class BaseScraper(object):

    filename = None

    def __init__(self, filename):
	if not os.path.isfile(filename):
	    raise IOError("File not found %s" % filename)

        self.filename = filename

    @cached_property
    def md5(self):
        """Calculate md5 checksum for given file."""
        hash_md5 = hashlib.md5()
        with open(self.filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
            return hash_md5.hexdigest()
