import logging

import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_hserver1
# #############################################################################


class Test_hserver1(hunitest.TestCase):

    def test_is_inside_ci1(self) -> None:
        is_inside_ci_ = hserver.is_inside_ci()
        if is_inside_ci_:
            # Inside CI we expect to run inside Docker.
            self.assertTrue(hserver.is_inside_docker())

    def test_is_inside_docker1(self) -> None:
        # We always run tests inside Docker.
        self.assertTrue(hserver.is_inside_docker())

    def test_is_dev_csfy1(self) -> None:
        _ = hserver.is_dev_csfy()

    def test_is_prod_csfy1(self) -> None:
        is_prod_csfy = hserver.is_prod_csfy()
        if is_prod_csfy:
            # Prod runs inside Docker.
            self.assertTrue(hserver.is_inside_docker())

    def test_consistency1(self) -> None:
        """
        One and only one set up config should be true.
        """
        hserver._dassert_setup_consistency()
