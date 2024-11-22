"""
Import as:

import helpers.repo_config_utils as hrecouti
"""

import logging
import os
from typing import Any

import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): -> get_repo_name
def get_name() -> str:
    return f"//{_REPO_NAME}"


def get_repo_map() -> Dict[str, str]:
    """
    Return a mapping of short repo name -> long repo name.
    """
repo_map: Dict[str, str] = {_REPO_NAME: f"{_GITHUB_REPO_ACCOUNT}/{_REPO_NAME}"}
return repo_map


def get_extra_amp_repo_sym_name() -> str:
    return f"{_GITHUB_REPO_ACCOUNT}/{_REPO_NAME}"


# TODO(gp): -> get_github_host_name
def get_host_name() -> str:
    return "github.com"


def get_invalid_words() -> List[str]:
    return []


def get_docker_base_image_name() -> str:
    """
    Return a base name for docker image.
    """
return _DOCKER_IMAGE_NAME


# TODO(gp): Convert in variables.

def get_unit_test_bucket_path() -> str:
    """
    Return the path to the unit test bucket.
    """

assert 0, f"Not supported by '{_REPO_NAME}'"
unit_test_bucket = "cryptokaizen-unit-test"
# We do not use `os.path.join` since it converts `s3://` to `s3:/`.
unit_test_bucket_path = "s3://" + unit_test_bucket
return unit_test_bucket_path


def get_html_bucket_path() -> str:
    """
    Return the path to the bucket where published HTMLs are stored.
    """
assert 0, f"Not supported by '{_REPO_NAME}'"
html_bucket = "cryptokaizen-html"
# We do not use `os.path.join` since it converts `s3://` to `s3:/`.
html_bucket_path = "s3://" + html_bucket
return html_bucket_path


def get_html_dir_to_url_mapping() -> Dict[str, str]:
    """
    Return a mapping between directories mapped on URLs.

    This is used when we have web servers serving files from specific
    directories.
    """
assert 0, f"Not supported by '{_REPO_NAME}'"
dir_to_url = {"s3://cryptokaizen-html": "http://172.30.2.44"}
return dir_to_url

def assert_setup(
    self_: Any, exp_enable_privileged_mode: bool, exp_has_dind_support: bool
) -> None:
    signature = henv.env_to_str(add_system_signature=False)
    _LOG.debug("env_to_str=%s", signature)
    #
    act_enable_privileged_mode = henv.execute_repo_config_code(
        "enable_privileged_mode()"
    )
    self_.assertEqual(act_enable_privileged_mode, exp_enable_privileged_mode)
    #
    act_has_dind_support = henv.execute_repo_config_code("has_dind_support()")
    self_.assertEqual(act_has_dind_support, exp_has_dind_support)


def _dassert_setup_consistency() -> None:
    """
    Check that one and only one set up config should be true.
    """
    # Use the settings from the `repo_config` corresponding to this container.
    enable_privileged_mode = henv.execute_repo_config_code(
        "enable_privileged_mode()"
    )
    use_docker_sibling_containers = henv.execute_repo_config_code(
        "use_docker_sibling_containers()"
    )
    use_docker_network_mode_host = henv.execute_repo_config_code(
        "use_docker_network_mode_host()"
    )
    use_main_network = henv.execute_repo_config_code("use_main_network()")
    _LOG.debug(
        hprint.to_str(
            "enable_privileged_mode use_docker_sibling_containers "
            "use_docker_network_mode_host use_main_network"
        )
    )
    # It's not possible to have dind and sibling containers together.
    hdbg.dassert(
        not (use_docker_sibling_containers and enable_privileged_mode),
        "use_docker_sibling_containers=%s enable_privileged_mode=%s",
        use_docker_sibling_containers,
        enable_privileged_mode,
    )
    # To run sibling containers they need to be in the same main network.
    if use_docker_sibling_containers:
        hdbg.dassert(use_main_network, "use_main_network=%s", use_main_network)
    # It's not possible to have both host and main network (which implies
    # bridge mode).
    hdbg.dassert(
        not (use_docker_network_mode_host and use_main_network),
        "use_docker_network_mode_host=%s use_main_network=%s",
        use_docker_network_mode_host,
        use_main_network,
    )


# If the env var is not defined then we want to check. The only reason to skip
# it's if the env var is defined and equal to False.
check_repo = os.environ.get("AM_REPO_CONFIG_CHECK", "True") != "False"
_is_called = False
if check_repo:
    if not _is_called:
        _dassert_setup_consistency()
        _is_called = True
else:
    _LOG.warning(f"Skipping repo check in {__file__}")
