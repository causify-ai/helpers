import logging

import helpers.henv as henv
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_env1
# #############################################################################


class Test_env1(hunitest.TestCase):

    def test_get_system_signature1(self) -> None:
        txt = henv.get_system_signature()
        _LOG.debug(txt)

    def test_has_module1(self) -> None:
        """
        Check that the function returns true for the existing package.
        """
        self.assertTrue(henv.has_module("numpy"))

    def test_has_not_module1(self) -> None:
        """
        Check that the function returns false for the non-existing package.
        """
        self.assertFalse(henv.has_module("no_such_module"))