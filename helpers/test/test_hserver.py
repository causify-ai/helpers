import logging

import pytest

import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_hserver1
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_inside_docker(),
    reason="This test should be run inside a Docker container",
)
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
        hserver._dassert_setup_consistency()

    def test_get_setup_signature1(self) -> None:
        val = hserver._get_setup_signature()
        _LOG.info("val=\n%s", val)

    def test_get_setup_settings1(self) -> None:
        setups = hserver._get_setup_settings()
        val = hserver._setup_to_str(setups)
        _LOG.info("val=\n%s", val)

    def test_config_func_to_str1(self) -> None:
        val = hserver.config_func_to_str()
        _LOG.info("val=\n%s", val)


# #############################################################################
# Test_hserver2
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_docker(),
    reason="This test should be run outside a Docker container",
)
class Test_hserver2(hunitest.TestCase):

    def test_consistency1(self) -> None:
        hserver._dassert_setup_consistency()

    def test_get_setup_signature1(self) -> None:
        val = hserver._get_setup_signature()
        _LOG.info("val=\n%s", val)

    def test_get_setup_settings1(self) -> None:
        setups = hserver._get_setup_settings()
        val = hserver._setup_to_str(setups)
        _LOG.info("val=\n%s", val)

    def test_config_func_to_str1(self) -> None:
        val = hserver.config_func_to_str()
        _LOG.info("val=\n%s", val)


# #############################################################################
# Test_hserver_dev_csfy1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_docker() or not hserver.is_dev_csfy(),
    reason="This test should be run on one of Causify dev machines",
)
class Test_hserver3(hunitest.TestCase):

    def test_consistency1(self) -> None:
        hserver._dassert_setup_consistency()

    def test_get_setup_signature1(self) -> None:
        act = hserver._get_setup_signature()
        exp = ""
        self.assert_equal(act, dev)

    def test_get_setup_settings1(self) -> None:
        setups = hserver._get_setup_settings()
        act = hserver._setup_to_str(setups)
        exp = ""
        self.assert_equal(act, exp)

    def test_config_func_to_str1(self) -> None:
        act = hserver.config_func_to_str()
        exp = ""
        self.assert_equal(act, exp)


# #############################################################################
# Test_hserver_gp_mac1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_docker() or not hserver.is_dev_csfy(),
    reason="This test should be run on one of Causify dev machines",
)
class Test_hserver_gp_mac1(hunitest.TestCase):

    def test_consistency1(self) -> None:
        hserver._dassert_setup_consistency()

    def test_get_setup_signature1(self) -> None:
        act = hserver._get_setup_signature()
        exp = ""
        self.assert_equal(act, dev)

    def test_get_setup_settings1(self) -> None:
        setups = hserver._get_setup_settings()
        act = hserver._setup_to_str(setups)
        exp = ""
        self.assert_equal(act, exp)

    def test_config_func_to_str1(self) -> None:
        act = hserver.config_func_to_str()
        exp = ""
        self.assert_equal(act, exp)


# #############################################################################


# TODO(gp): Add test mocking the environment variables in _get_setup_signature.
# We should have one class for each set up (e.g., outside Mac, outside Linux,
# inside Docker, inside CI, etc.)