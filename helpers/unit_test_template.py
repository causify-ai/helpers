"""
Import as:

import helpers.unit_test_template as hunteske
"""

import logging

import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_Example
# #############################################################################


class Test_Example(hunitest.TestCase):
    def test_example1(self) -> None:
        pass
