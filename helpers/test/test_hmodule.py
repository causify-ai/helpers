import logging

import helpers.hmodule as hmodule
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_hmodule1
# #############################################################################


class Test_hmodule1(hunitest.TestCase):
    def test_has_module1(self) -> None:
        """
        Check that the function returns true for the existing package.
        """
        self.assertTrue(hmodule.has_module("numpy"))

    def test_has_not_module1(self) -> None:
        """
        Check that the function returns false for the non-existing package.
        """
        self.assertFalse(hmodule.has_module("no_such_module"))
