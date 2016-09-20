"""Configure py.test default values and functionality"""

import os
import sys

from tests.fixtures import *
import pytest

# Prefer modules from source directory rather than from site-python
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                '..'))
