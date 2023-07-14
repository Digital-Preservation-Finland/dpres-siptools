"""Configure py.test default values and functionality"""
from __future__ import unicode_literals

import os
import sys
import tempfile
import shutil

from click.testing import CliRunner

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
        help="Also run end-to-end tests"
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
        "e2e: End-to-end tests"
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


@pytest.fixture(scope="function")
def run_cli():
    """Executes given Click interface with given arguments
    """
    def _run_cli(cli_func, args, success=True):
        """
        Execute Click command with given arguments and check the exit code

        :param cli_func: Click command function
        :param list args: List of parameters
        :param bool success: If True, expect the command to succeed, otherwise
                             expect the command to fail.

        :returns: Command result
        :rtype: click.testing.Result
        """
        runner = CliRunner()
        result = runner.invoke(
            cli_func, args,
            # If the command is meant to succeed, let pytest catch the
            # exceptions instead of Click
            catch_exceptions=not success
        )
        if success:
            assert result.exit_code == 0, result
        else:
            assert result.exit_code != 0, \
                "Expected command to fail but it succeeded instead"

        return result

    return _run_cli
