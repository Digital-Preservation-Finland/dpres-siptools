"""Configure py.test default values and functionality"""
from __future__ import unicode_literals

import os
import sys
import tempfile
import shutil

import pytest

# Prefer modules from source directory rather than from site-python
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                '..'))


def pytest_addoption(parser):
    """Add additional options to pytest."""
    parser.addoption(
        "--e2e",
        action="store_true",
        default=False,
        help="Also run end-to-end tests (requires ipt package)"
    )
    parser.addoption(
        "--validation",
        action="store_true",
        default=False,
        help="Also run validation tests (requires file-scraper-full package)"
    )


def pytest_configure(config):
    """Add additional configuration to pytest."""
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests intended to be run with ipt package"
    )
    config.addinivalue_line(
        "markers",
        "validation: Tests intended to be run with file-scraper-full package"
    )


def pytest_runtest_setup(item):
    """Setting up to skip the tests with specific markers if
    appropriate option has not been evoked.
    """

    skip_tests = ['validation', 'e2e']

    for keyword in skip_tests:
        if keyword in item.keywords:
            if not item.config.getoption("--%s" % keyword):
                pytest.skip(
                    "Use option --%s to run additional tests" % keyword)


@pytest.fixture(scope="function")
def testpath(request):
    """Creates temporary directory and clean up after testing.

    :request: Pytest request fixture
    :returns: Path to temporary directory

    """
    temp_path = tempfile.mkdtemp(prefix="tests.testpath.")

    def fin():
        """remove temporary path"""
        shutil.rmtree(temp_path)

    request.addfinalizer(fin)
    return temp_path
