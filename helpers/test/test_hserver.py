import logging

import pytest

import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# _TestCase1
# #############################################################################


class _TestCase1:

    # def test_config_func_to_str1(self) -> None:
    #     val = hserver.config_func_to_str()
    #     _LOG.info("val=\n%s", val)
    #     if self.exp_config_func_to_str is not None:
    #         self.assert_equal(val, self.exp_config_func_to_str)

    def test_consistency1(self) -> None:
        hserver._dassert_setup_consistency()

    def test_is_host_csfy_server1(self) -> None:
        val = hserver.is_host_csfy_server()
        _LOG.info("val=\n%s", val)
        if self.exp_is_host_csfy_server is not None:
            self.assertEqual(val, self.exp_is_host_csfy_server)

    def test_is_host_mac1(self) -> None:
        val = hserver.is_host_mac()
        _LOG.info("val=\n%s", val)
        if self.exp_is_host_mac is not None:
            self.assertEqual(val, self.exp_is_host_mac)

    def test_get_docker_info1(self) -> None:
        val = hserver.get_docker_info()
        _LOG.info("val=\n%s", val)
        # Remove the docker version since it is not stable.
        val = hprint.filter_text("docker_version=", val)
        if self.exp_get_docker_info is not None:
            self.assert_equal(val, self.exp_get_docker_info)

    def test_get_setup_settings1(self) -> None:
        setups = hserver._get_setup_settings()
        val = hserver._setup_to_str(setups)
        _LOG.info("val=\n%s", val)
        if self.exp_get_setup_settings is not None:
            self.assert_equal(val, self.exp_get_setup_settings)

    # def test_get_setup_signature1(self) -> None:
    #     val = hserver._get_setup_signature()
    #     _LOG.info("val=\n%s", val)
    #     if self.exp_get_setup_signature is not None:
    #         self.assert_equal(val, self.exp_get_setup_signature)

    def test_is_inside_ci1(self) -> None:
        val = hserver.is_inside_ci()
        _LOG.info("val=\n%s", val)
        if self.exp_is_inside_ci is not None:
            self.assertEqual(val, self.exp_is_inside_ci)


# #############################################################################
# Test_hserver1
# #############################################################################


class Test_hserver1(_TestCase1, hunitest.TestCase):
    """
    Smoke test without checking anything.
    """

    def setUp(self) -> None:
        super().setUp()
        self.exp_config_func_to_str = None
        self.exp_get_docker_info = None
        self.exp_get_setup_settings = None
        self.exp_get_setup_signature = None
        self.exp_is_host_csfy_server = None
        self.exp_is_host_mac = None
        self.exp_is_inside_ci = None


# #############################################################################
# Test_hserver_inside_ci1
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_inside_ci(),
    reason="Config not matching",
)
class Test_hserver_inside_ci1(_TestCase1, hunitest.TestCase):
    """
    Run tests inside CI.
    """

    def setUp(self) -> None:
        super().setUp()
        self.exp_config_func_to_str = None
        self.exp_get_docker_info = hprint.dedent(
            r"""
            # Docker info
              has_docker=True
              docker_needs_sudo=False
              has_privileged_mode=True
              is_inside_docker=True
              has_sibling_containers_support=True
              has_docker_dind_support=True
            """
        )
        self.exp_get_setup_settings = hprint.dedent(
            r"""
            is_inside_docker_container_on_csfy_server     False
            is_outside_docker_container_on_csfy_server    False
            is_inside_docker_container_on_host_mac        False
            is_outside_docker_container_on_host_mac       False
            is_inside_docker_container_on_external_linux  False
            is_outside_docker_container_on_external_linux False
            is_dev4                                       False
            is_ig_prod                                    False
            is_prod_csfy                                  False
            is_inside_ci                                  True
            """
        )
        self.exp_get_setup_signature = None
        self.exp_is_host_csfy_server = False
        self.exp_is_host_mac = False
        self.exp_is_inside_ci = True


# #############################################################################
# Test_hserver_inside_docker_container_on_csfy_server1
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_inside_docker_container_on_csfy_server(),
    reason="Config not matching",
)
class Test_hserver_inside_docker_container_on_csfy_server1(
    _TestCase1, hunitest.TestCase
):
    """
    Run tests inside Docker container on a Causify dev server.
    """

    def setUp(self) -> None:
        super().setUp()
        self.exp_config_func_to_str = ""
        self.exp_get_docker_info = hprint.dedent(
            r"""
            # Docker info
              has_docker=True
              docker_needs_sudo=False
              has_privileged_mode=True
              is_inside_docker=True
              has_sibling_containers_support=True
              has_docker_dind_support=True
            """
        )
        self.exp_get_setup_settings = hprint.dedent(
            r"""
            is_inside_docker_container_on_csfy_server     True
            is_outside_docker_container_on_csfy_server    False
            is_inside_docker_container_on_host_mac        False
            is_outside_docker_container_on_host_mac       False
            is_inside_docker_container_on_external_linux  False
            is_outside_docker_container_on_external_linux False
            is_dev4                                       False
            is_ig_prod                                    False
            is_prod_csfy                                  False
            is_inside_ci                                  False
            """
        )
        self.exp_get_setup_signature = ""
        self.exp_is_host_csfy_server = True
        self.exp_is_host_mac = False
        self.exp_is_inside_ci = False


# #############################################################################
# Test_hserver_outside_docker_container_on_csfy_server1
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_outside_docker_container_on_csfy_server(),
    reason="Config not matching",
)
class Test_hserver_outside_docker_container_on_csfy_server1(
    _TestCase1, hunitest.TestCase
):
    """
    Run tests outside Docker container on a Causify dev server.
    """

    def setUp(self) -> None:
        super().setUp()
        self.exp_config_func_to_str = ""
        self.exp_get_docker_info = hprint.dedent(
            r"""
            # Docker info
              has_docker=True
              docker_needs_sudo=False
              has_privileged_mode=True
              is_inside_docker=False
              has_sibling_containers_support=*undef*
              has_docker_dind_support=*undef*
            """
        )
        self.exp_get_setup_settings = hprint.dedent(
            r"""
            is_inside_docker_container_on_csfy_server     False
            is_outside_docker_container_on_csfy_server    True
            is_inside_docker_container_on_host_mac        False
            is_outside_docker_container_on_host_mac       False
            is_inside_docker_container_on_external_linux  False
            is_outside_docker_container_on_external_linux False
            is_dev4                                       False
            is_ig_prod                                    False
            is_prod_csfy                                  False
            is_inside_ci                                  False
            """
        )
        self.exp_get_setup_signature = ""
        self.exp_is_host_csfy_server = True
        self.exp_is_host_mac = False
        self.exp_is_inside_ci = False


# #############################################################################
# Test_hserver_inside_docker_container_on_gp_mac1
# #############################################################################


@pytest.mark.skipif(
    not (hserver.is_inside_docker() and hserver.is_host_gp_mac()),
    reason="Config not matching",
)
class Test_hserver_inside_docker_container_on_gp_mac1(
    _TestCase1, hunitest.TestCase
):
    """
    Run tests inside Docker container on GP's Mac.
    """

    def setUp(self) -> None:
        super().setUp()
        self.exp_config_func_to_str = ""
        self.exp_get_docker_info = hprint.dedent(
            r"""
            # Docker info
              has_docker=True
              docker_needs_sudo=False
              has_privileged_mode=True
              is_inside_docker=True
              has_sibling_containers_support=True
              has_docker_dind_support=True
            """
        )
        self.exp_get_setup_settings = hprint.dedent(
            r"""
            is_inside_docker_container_on_csfy_server     False
            is_outside_docker_container_on_csfy_server    False
            is_inside_docker_container_on_host_mac        True
            is_outside_docker_container_on_host_mac       False
            is_inside_docker_container_on_external_linux  False
            is_outside_docker_container_on_external_linux False
            is_dev4                                       False
            is_ig_prod                                    False
            is_prod_csfy                                  False
            is_inside_ci                                  False
            """
        )
        self.exp_get_setup_signature = ""
        self.exp_is_host_csfy_server = False
        self.exp_is_host_mac = True
        self.exp_is_inside_ci = False


# #############################################################################
# Test_hserver_outside_docker_container_on_gp_mac1
# #############################################################################


@pytest.mark.skipif(
    not (not hserver.is_inside_docker() and hserver.is_host_gp_mac()),
    reason="Config not matching",
)
class Test_hserver_outside_docker_container_on_gp_mac1(
    _TestCase1, hunitest.TestCase
):
    """
    Run tests outside Docker container on GP's Mac.
    """

    def setUp(self) -> None:
        super().setUp()
        self.exp_config_func_to_str = ""
        self.exp_get_docker_info = hprint.dedent(
            r"""
            # Docker info
              has_docker=True
              docker_needs_sudo=False
              has_privileged_mode=True
              is_inside_docker=False
              has_sibling_containers_support=*undef*
              has_docker_dind_support=*undef*
            """
        )
        self.exp_get_setup_settings = hprint.dedent(
            r"""
            is_inside_docker_container_on_csfy_server     False
            is_outside_docker_container_on_csfy_server    False
            is_inside_docker_container_on_host_mac        False
            is_outside_docker_container_on_host_mac       True
            is_inside_docker_container_on_external_linux  False
            is_outside_docker_container_on_external_linux False
            is_dev4                                       False
            is_ig_prod                                    False
            is_prod_csfy                                  False
            is_inside_ci                                  False
            """
        )
        self.exp_get_setup_signature = ""
        self.exp_is_host_csfy_server = False
        self.exp_is_host_mac = True
        self.exp_is_inside_ci = False


# #############################################################################


# TODO(gp): Add test mocking the environment variables in _get_setup_signature.
# We should have one class for each set up (e.g., outside Mac, outside Linux,
# inside Docker, inside CI, etc.)
