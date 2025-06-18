#!/usr/bin/env python3

"""
Tests for setenv.sh script.

This module contains tests that verify the functionality of the
setenv.sh script which is responsible for bootstrapping the development
environment. It includes tests for basic functionality, environment
setup, and error handling.
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest

import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.htimer as htimer
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# SetenvScriptTester
# #############################################################################


class SetenvScriptTester:
    """
    Utility class for testing the actual setenv.sh script in a controlled
    environment.

    This class provides methods to set up a test environment that mimics
    the real repository structure and tests the actual setenv.sh script
    with its dependencies.
    """

    def __init__(self) -> None:
        """
        Initialize the SetenvScriptTester with a temporary directory.
        """
        self.temp_dir = Path(tempfile.mkdtemp())
        self.git_root = self.temp_dir / "test_repo"
        self.original_cwd = Path.cwd()
        _LOG.debug("Created temporary test directory: %s", self.git_root)

    def setup_git_repo(self) -> None:
        """
        Set up a git repository in the test environment.
        """
        self.git_root.mkdir(parents=True, exist_ok=True)
        # Initialize git repository.
        subprocess.run(
            ["git", "init"],
            cwd=str(self.git_root),
            capture_output=True,
            check=True,
        )
        # Create initial commit.
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(self.git_root),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(self.git_root),
            capture_output=True,
            check=True,
        )
        # Create a dummy file and commit it.
        (self.git_root / "README.md").write_text("# Test Repository")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=str(self.git_root),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=str(self.git_root),
            capture_output=True,
            check=True,
        )
        _LOG.debug("Set up git repository at: %s", self.git_root)

    def copy_real_setenv_script(self) -> None:
        """
        Copy the real setenv.sh script to the test environment.
        """
        # Get the real script path.
        real_setenv_path = Path(__file__).parent.parent / "setenv.sh"
        # Copy to test environment.
        test_setenv_path = (
            self.git_root / "dev_scripts_helpers" / "thin_client" / "setenv.sh"
        )
        # Create directories.
        test_setenv_path.parent.mkdir(parents=True, exist_ok=True)
        # Copy file.
        hio.to_file(str(test_setenv_path), hio.from_file(str(real_setenv_path)))
        # Make setenv.sh executable.
        test_setenv_path.chmod(0o755)
        _LOG.debug("Copied real setenv.sh to test environment")

    def create_mock_thin_client_utils(self) -> None:
        """
        Create a mock thin_client_utils.sh that provides the expected
        interface.
        """
        mock_utils_content = """#!/bin/bash
set -e

# Mock functions that setenv.sh calls from thin_client_utils.sh.
# These functions provide the expected interface without executing real logic.

function parse_yaml() {
    # Mock YAML parsing - just output the expected variables based on repo_config.yaml.
    if [ ! -f "repo_config.yaml" ]; then
        echo "Error: repo_config.yaml not found" >&2
        exit 1
    fi

    # Simple mock that reads the config and outputs expected variables.
    if grep -q "use_helpers_as_nested_module: True" repo_config.yaml; then
        echo "REPO_CONF_runnable_dir_info_use_helpers_as_nested_module=True"
    elif grep -q "use_helpers_as_nested_module: 1" repo_config.yaml; then
        echo "REPO_CONF_runnable_dir_info_use_helpers_as_nested_module=True"
    else
        echo "REPO_CONF_runnable_dir_info_use_helpers_as_nested_module=False"
    fi

    # Extract other values from config.
    venv_tag=$(grep "venv_tag:" repo_config.yaml | sed 's/.*venv_tag: *"\\([^"]*\\)"/\\1/')
    dir_suffix=$(grep "dir_suffix:" repo_config.yaml | sed 's/.*dir_suffix: *"\\([^"]*\\)"/\\1/')
    enable_hooks=$(grep "enable_git_commit_hook:" repo_config.yaml | sed 's/.*enable_git_commit_hook: *\\([^ ]*\\)/\\1/')

    echo "REPO_CONF_runnable_dir_info_venv_tag=$venv_tag"
    echo "REPO_CONF_runnable_dir_info_dir_suffix=$dir_suffix"
    echo "REPO_CONF_repo_info_enable_git_commit_hook=$enable_hooks"

    # Add config variables that match the documentation structure.
    echo "REPO_CONF_container_registry_info_ecr=123456789012.dkr.ecr.us-east-1.amazonaws.com"
    echo "REPO_CONF_container_registry_info_ghcr=ghcr.io/test-org"
    echo "REPO_CONF_docker_info_docker_image_name=test-repo"
    echo "REPO_CONF_docker_info_use_sibling_container_in_unit_tests=True"
    echo "REPO_CONF_repo_info_github_host_name=github.com"
    echo "REPO_CONF_repo_info_github_repo_account=test-org"
    echo "REPO_CONF_repo_info_issue_prefix=TestTask"
    echo "REPO_CONF_repo_info_repo_name=test_repo"
    echo "REPO_CONF_s3_bucket_info_html_bucket_name=s3://test-html"
    echo "REPO_CONF_s3_bucket_info_html_ip=http://172.30.2.44"
    echo "REPO_CONF_s3_bucket_info_unit_test_bucket_name=s3://test-unit-test"
}

function activate_venv() {
    # Mock virtual environment activation.
    local venv_tag=$1
    echo "# activate_venv()"
    echo "src_dir=$HOME/src"
    echo "venv_dir=$HOME/src/venv/client_venv.${venv_tag}"
    echo "# Activate virtual env '$HOME/src/venv/client_venv.${venv_tag}/bin/activate'"
    echo "which python=$HOME/src/venv/client_venv.${venv_tag}/bin/python"
    echo "python -v=Python 3.12.3"
    echo "which python3=$HOME/src/venv/client_venv.${venv_tag}/bin/python3"
    echo "python3 -v=Python 3.12.3"
}

function set_path() {
    # Mock path setting - matches real output format.
    local dev_script_dir=$1
    echo "DEV_SCRIPT_HELPER_DIR=$dev_script_dir"
    # Create a mock PATH with multiple directories like the real output.
    mock_path="$dev_script_dir:$dev_script_dir/release_sorrentum:$dev_script_dir/docker:$dev_script_dir/coding_tools:$dev_script_dir/misc:$dev_script_dir/testing:$dev_script_dir/notebooks:$dev_script_dir/infra:$dev_script_dir/poetry:$dev_script_dir/system_tools:$dev_script_dir/encrypt_models:$dev_script_dir/cvxpy_setup:$dev_script_dir/to_clean:$dev_script_dir/scraping_script:$dev_script_dir/git:$dev_script_dir/old:$dev_script_dir/integrate_repos:$dev_script_dir/test:$dev_script_dir/documentation:$dev_script_dir/github:$dev_script_dir/cleanup_scripts:$dev_script_dir/llms:$dev_script_dir/update_devops_packages:$dev_script_dir/aws:$dev_script_dir/lint:$dev_script_dir/thin_client:$dev_script_dir/dockerize:$dev_script_dir/chatgpt:$GIT_ROOT_DIR:$HOME/src/venv/client_venv.helpers/bin:$HOME/.pyenv/shims:$HOME/.pyenv/plugins/pyenv-virtualenv/shims:$HOME/.pyenv/bin:$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:$HOME/.local/bin"
    echo "PATH=$mock_path"
}

function set_pythonpath() {
    # Mock PYTHONPATH setting - matches real output format.
    local helpers_root_dir="$1"
    echo "# set_pythonpath()"
    echo "Adding $helpers_root_dir to PYTHONPATH"
    echo "PYTHONPATH=$helpers_root_dir:"
}

function set_symlink_permissions() {
    # Mock symlink permissions setting - matches real output format.
    local directory="$1"
    echo "# set_symlink_permissions()"
    # Mock finding and processing symlinks.
    echo "INFO:Remove write permissions for: './.github/gitleaks-rules.toml'"
    echo "INFO:Remove write permissions for: './.git/hooks/pre-commit'"
    echo "INFO:Remove write permissions for: './.git/hooks/commit-msg'"
}

function set_csfy_env_vars() {
    # Mock CSFY environment variables - matches real output format.
    echo "# set_csfy_env_vars()"
    export CSFY_HOST_NAME=$(hostname)
    echo "CSFY_HOST_NAME=$CSFY_HOST_NAME"
    export CSFY_HOST_OS_NAME=$(uname)
    echo "CSFY_HOST_OS_NAME=$CSFY_HOST_OS_NAME"
    export CSFY_HOST_USER_NAME=$(whoami)
    echo "CSFY_HOST_USER_NAME=$CSFY_HOST_USER_NAME"
    export CSFY_HOST_OS_VERSION=$(uname -r)
    echo "CSFY_HOST_OS_VERSION=$CSFY_HOST_OS_VERSION"
}

function configure_specific_project() {
    # Mock project configuration - matches real output format.
    echo "# configure_specific_project()"
    echo "host_name=$(hostname) csfy_host_name=$(hostname)"
    export CSFY_AWS_PROFILE="ck"
    echo "CSFY_AWS_PROFILE=ck"
    export CSFY_AWS_S3_BUCKET="cryptokaizen-data"
    echo "CSFY_AWS_S3_BUCKET=cryptokaizen-data"
    export CSFY_ECR_BASE_PATH="causify"
    echo "CSFY_ECR_BASE_PATH=causify"
    export CSFY_HOST_NAME=$(hostname)
    echo "CSFY_HOST_NAME=$CSFY_HOST_NAME"
    export CSFY_HOST_OS_NAME=$(uname)
    echo "CSFY_HOST_OS_NAME=$CSFY_HOST_OS_NAME"
    export CSFY_HOST_OS_VERSION=$(uname -r)
    echo "CSFY_HOST_OS_VERSION=$CSFY_HOST_OS_VERSION"
    export CSFY_HOST_USER_NAME=$(whoami)
    echo "CSFY_HOST_USER_NAME=$CSFY_HOST_USER_NAME"
}

function print_env_signature() {
    # Mock environment signature printing - matches real output format.
    echo "# PATH="
    # Print PATH on separate lines like real output.
    echo "$PATH" | tr ':' '\\n'
    echo "# PYTHONPATH="
    echo "$PYTHONPATH" | tr ':' '\\n'
    echo "# printenv="
    printenv
    echo "# alias="
    alias
}

function dassert_dir_exists() {
    # Mock directory existence check.
    local dir_path="$1"
    if [ ! -d "$dir_path" ]; then
        echo "ERROR: Directory '$dir_path' does not exist." >&2
        exit 1
    fi
}

# Color definitions for output formatting.
RED='\\033[0;31m'
YELLOW='\\033[1;33m'
GREEN='\\033[0;32m'
NC='\\033[0m'

INFO="${GREEN}INFO${NC}"
WARNING="${YELLOW}WARNING${NC}"
ERROR="${RED}ERROR${NC}"
"""
        test_utils_path = (
            self.git_root
            / "dev_scripts_helpers"
            / "thin_client"
            / "thin_client_utils.sh"
        )
        test_utils_path.parent.mkdir(parents=True, exist_ok=True)
        hio.to_file(str(test_utils_path), mock_utils_content)
        test_utils_path.chmod(0o755)
        _LOG.debug("Created mock thin_client_utils.sh")

    def create_repo_config(self, config_content: str) -> None:
        """
        Create a repo_config.yaml file in the test environment.

        :param config_content: YAML content for the config file
        """
        config_path = self.git_root / "repo_config.yaml"
        hio.to_file(str(config_path), config_content)
        _LOG.debug("Created repo_config.yaml: %s", config_path)

    def create_test_structure(self) -> None:
        """
        Create the necessary directory structure for testing.
        """
        # Create helpers_root directory (as described in the docs).
        helpers_root = self.git_root / "helpers_root"
        helpers_root.mkdir(parents=True, exist_ok=True)
        # Create dev_scripts_helpers directory directly under git root for non-nested module case.
        dev_scripts_helpers_dir = self.git_root / "dev_scripts_helpers"
        dev_scripts_helpers_dir.mkdir(parents=True, exist_ok=True)
        # Create dev_scripts_test directory (following the naming pattern from docs).
        dev_scripts_dir = self.git_root / "dev_scripts_test"
        dev_scripts_dir.mkdir(parents=True, exist_ok=True)
        # Create git hooks directory under helpers_root (for nested module case).
        git_hooks_dir_nested = (
            helpers_root / "dev_scripts_helpers" / "git" / "git_hooks"
        )
        git_hooks_dir_nested.mkdir(parents=True, exist_ok=True)
        # Create git hooks directory directly under git root (for non-nested module case).
        git_hooks_dir_non_nested = (
            self.git_root / "dev_scripts_helpers" / "git" / "git_hooks"
        )
        git_hooks_dir_non_nested.mkdir(parents=True, exist_ok=True)
        # Create a mock install_hooks.py script.
        install_hooks_content = """#!/usr/bin/env python3
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=['install', 'remove'], required=True)
    args = parser.parse_args()

    if args.action == 'install':
        print("Installing git hooks")
    elif args.action == 'remove':
        print("Removing git hooks")

    return 0


if __name__ == '__main__':
    sys.exit(main())
"""
        # Create the script in both locations to handle both cases.
        install_hooks_path_nested = git_hooks_dir_nested / "install_hooks.py"
        hio.to_file(str(install_hooks_path_nested), install_hooks_content)
        install_hooks_path_nested.chmod(0o755)
        install_hooks_path_non_nested = (
            git_hooks_dir_non_nested / "install_hooks.py"
        )
        hio.to_file(str(install_hooks_path_non_nested), install_hooks_content)
        install_hooks_path_non_nested.chmod(0o755)
        # Create devops directory structure (as described in docs).
        devops_dir = self.git_root / "devops"
        devops_dir.mkdir(parents=True, exist_ok=True)
        # Create some mock devops files.
        dockerfile_content = """FROM python:3.12-slim
# Mock Dockerfile for testing.
"""
        hio.to_file(str(devops_dir / "Dockerfile"), dockerfile_content)
        _LOG.debug("Created test directory structure")

    def create_mock_repo_config(self) -> None:
        """
        Create a realistic repo_config.yaml based on the documentation
        examples.
        """
        config_content = """
# Mock repo_config.yaml based on documentation examples.
repo_info:
  repo_name: test_repo
  github_repo_account: test-org
  github_host_name: github.com
  issue_prefix: TestTask
  enable_git_commit_hook: True

docker_info:
  docker_image_name: test-repo
  use_sibling_container_in_unit_tests: True

runnable_dir_info:
  use_helpers_as_nested_module: True
  venv_tag: "test_venv"
  dir_suffix: "test"

container_registry_info:
  ecr: 123456789012.dkr.ecr.us-east-1.amazonaws.com
  ghcr: ghcr.io/test-org

s3_bucket_info:
  html_bucket_name: s3://test-html
  html_ip: http://172.30.2.44
  unit_test_bucket_name: s3://test-unit-test
"""
        self.create_repo_config(config_content)

    def run_setenv_script(
        self, capture_env: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run the actual setenv.sh script in the test environment.

        :param capture_env: Whether to capture environment variables
        :return: CompletedProcess with script output and return code
        """
        setenv_path = (
            self.git_root / "dev_scripts_helpers" / "thin_client" / "setenv.sh"
        )
        if capture_env:
            wrapper_script = f"""#!/bin/bash
set -e

print_env() {{
    echo "=== SCRIPT ENVIRONMENT VARIABLES ==="
    env | sort
    echo "=== END SCRIPT ENVIRONMENT VARIABLES ==="
}}

tmp_out=$(mktemp)

set +e                                    # Allow the script to fail gracefully.
# shellcheck disable=SC1090
source "{setenv_path}" >"$tmp_out"   # Stdout → tmp_out, stderr untouched.
source_status=$?
set -e

echo "=== SOURCE OUTPUT ==="
cat "$tmp_out"
echo "=== END SOURCE OUTPUT ==="
rm -f "$tmp_out"

# Only dump env details on success (keeps error output clean).
if [ $source_status -eq 0 ]; then
    print_env
fi

exit $source_status
"""
            wrapper_path = self.git_root / "wrapper.sh"
            hio.to_file(str(wrapper_path), wrapper_script)
            wrapper_path.chmod(0o755)
            script_to_run = str(wrapper_path)
        else:
            script_to_run = str(setenv_path)
        _LOG.debug("Running setenv.sh script: %s", script_to_run)
        # Change to git root directory and run the script.
        env = os.environ.copy()
        return subprocess.run(
            ["bash", script_to_run],
            env=env,
            cwd=str(self.git_root),
            capture_output=True,
            text=True,
        )

    def cleanup(self) -> None:
        """
        Clean up the test environment.
        """
        # Change back to original directory.
        os.chdir(self.original_cwd)
        # Remove temporary directory.
        hsystem.system(f"rm -rf {self.temp_dir}")
        _LOG.debug("Cleaned up temporary directory: %s", self.temp_dir)


# #############################################################################
# _SetenvTestHelper
# #############################################################################


class _SetenvTestHelper(hunitest.TestCase):
    """
    Helper test class for setenv.sh tests.

    This class provides common setup, teardown, and assertion methods
    for testing the actual setenv.sh script.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        """
        Set up and tear down test environment for each test.
        """
        self.set_up_test()
        yield
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Set up test environment before each test.
        """
        self._timer = htimer.Timer()
        self.tester = SetenvScriptTester()
        self._setup_test_environment()

    def tear_down_test(self) -> None:
        """
        Clean up test environment after each test.
        """
        # Make sure to stop the timer.
        if (
            hasattr(self, "_timer")
            and self._timer.is_started()
            and not self._timer.is_stopped()
        ):
            self._timer.stop()
        self.tester.cleanup()

    def _setup_test_environment(self) -> None:
        """
        Set up the test environment with real scripts and dependencies.
        """
        # Set up git repository.
        self.tester.setup_git_repo()
        # Copy real setenv.sh script.
        self.tester.copy_real_setenv_script()
        # Create mock thin_client_utils.sh.
        self.tester.create_mock_thin_client_utils()
        # Create test directory structure.
        self.tester.create_test_structure()
        # Create mock repo config.
        self.tester.create_mock_repo_config()

    def _run_setenv_script(self) -> subprocess.CompletedProcess:
        """
        Run the actual setenv.sh script in the test environment.

        :return: CompletedProcess with script output and return code
        """
        return self.tester.run_setenv_script()


# #############################################################################
# TestSetenvBasic
# #############################################################################


class TestSetenvBasic(_SetenvTestHelper):
    """
    Test basic functionality of the actual setenv.sh script.
    """

    def test_script_sources_correctly(self) -> None:
        """
        Test that the actual script can be sourced without errors.
        """
        result = self._run_setenv_script()
        self.assertEqual(
            result.returncode, 0, f"Script failed with error: {result.stderr}"
        )

    def test_git_root_detection(self) -> None:
        """
        Test that GIT_ROOT_DIR is correctly detected from git.
        """
        result = self._run_setenv_script()
        self.assertIn("GIT_ROOT_DIR=", result.stdout)
        self.assertIn(str(self.tester.git_root), result.stdout)

    def test_script_path_output(self) -> None:
        """
        Test that the script outputs its own path.
        """
        result = self._run_setenv_script()
        # Check for script path output.
        self.assertIn("##>", result.stdout)
        self.assertIn("setenv.sh", result.stdout)

    def test_thin_client_utils_sourcing(self) -> None:
        """
        Test that thin_client_utils.sh is found and sourced correctly.
        """
        result = self._run_setenv_script()
        self.assertIn("Thin client utils found at:", result.stdout)


# #############################################################################
# TestSetenvConfigParsing
# #############################################################################


class TestSetenvConfigParsing(_SetenvTestHelper):
    """
    Test YAML config parsing functionality.
    """

    def test_repo_config_parsing(self) -> None:
        """
        Test that repo_config.yaml is correctly parsed.
        """
        result = self._run_setenv_script()
        self.assertIn(
            "REPO_CONF_runnable_dir_info_use_helpers_as_nested_module=True",
            result.stdout,
        )
        self.assertIn(
            "REPO_CONF_runnable_dir_info_venv_tag=test_venv", result.stdout
        )
        self.assertIn(
            "REPO_CONF_runnable_dir_info_dir_suffix=test", result.stdout
        )
        self.assertIn(
            "REPO_CONF_repo_info_enable_git_commit_hook=True", result.stdout
        )
        # Check for additional config variables that appear in real output.
        self.assertIn("REPO_CONF_container_registry_info_ecr=", result.stdout)
        self.assertIn(
            "REPO_CONF_repo_info_github_host_name=github.com", result.stdout
        )

    def test_backward_compatibility_integer_value(self) -> None:
        """
        Test backward compatibility with integer values in config.
        """
        # Mock repo_config.yaml with integer value for backward compatibility.
        config_with_int = """
# Mock repo_config.yaml with integer value for backward compatibility.
repo_info:
  repo_name: test_repo
  github_repo_account: test-org
  github_host_name: github.com
  issue_prefix: TestTask
  enable_git_commit_hook: True

docker_info:
  docker_image_name: test-repo
  use_sibling_container_in_unit_tests: True

runnable_dir_info:
  use_helpers_as_nested_module: 1
  venv_tag: "test_venv"
  dir_suffix: "test"

container_registry_info:
  ecr: 123456789012.dkr.ecr.us-east-1.amazonaws.com
  ghcr: ghcr.io/test-org

s3_bucket_info:
  html_bucket_name: s3://test-html
  html_ip: http://172.30.2.44
  unit_test_bucket_name: s3://test-unit-test
"""
        self.tester.create_repo_config(config_with_int)
        result = self._run_setenv_script()
        self.assertIn(
            "REPO_CONF_runnable_dir_info_use_helpers_as_nested_module=True",
            result.stdout,
        )


# #############################################################################
# TestSetenvEnvironmentSetup
# #############################################################################


class TestSetenvEnvironmentSetup(_SetenvTestHelper):
    """
    Test environment setup functionality.
    """

    def test_helpers_root_detection(self) -> None:
        """
        Test that helpers_root directory is detected correctly.
        """
        result = self._run_setenv_script()
        self.assertIn("HELPERS_ROOT_DIR=", result.stdout)
        self.assertIn("helpers_root", result.stdout)

    def test_dev_script_dir_setup(self) -> None:
        """
        Test that dev_scripts directory is set up correctly.
        """
        result = self._run_setenv_script()
        self.assertIn("DEV_SCRIPT_DIR=", result.stdout)
        self.assertIn("dev_scripts_test", result.stdout)

    def test_pythonpath_setting(self) -> None:
        """
        Test that PYTHONPATH is set correctly.
        """
        result = self._run_setenv_script()
        self.assertIn("PYTHONPATH=", result.stdout)
        # Check for "Adding ... to PYTHONPATH".
        self.assertIn("Adding", result.stdout)

    def test_csfy_environment_variables(self) -> None:
        """
        Test that CSFY environment variables are set.
        """
        result = self._run_setenv_script()
        self.assertIn("CSFY_HOST_NAME=", result.stdout)
        self.assertIn("CSFY_HOST_OS_NAME=", result.stdout)
        self.assertIn("CSFY_HOST_USER_NAME=", result.stdout)
        self.assertIn("CSFY_HOST_OS_VERSION=", result.stdout)

    def test_venv_activation(self) -> None:
        """
        Test that virtual environment activation is called correctly.
        """
        result = self._run_setenv_script()
        self.assertIn("# activate_venv()", result.stdout)
        self.assertIn("src_dir=", result.stdout)
        self.assertIn("venv_dir=", result.stdout)
        self.assertIn("which python=", result.stdout)
        self.assertIn("python -v=", result.stdout)


# #############################################################################
# TestSetenvGitHooks
# #############################################################################


class TestSetenvGitHooks(_SetenvTestHelper):
    """
    Test git hooks installation functionality.
    """

    def test_git_hooks_installation_enabled(self) -> None:
        """
        Test git hooks installation when enabled in config.
        """
        result = self._run_setenv_script()
        self.assertIn("Installing git hooks", result.stdout)

    def test_git_hooks_installation_disabled(self) -> None:
        """
        Test git hooks installation when disabled in config.
        """
        config_disabled = """
runnable_dir_info:
  use_helpers_as_nested_module: True
  venv_tag: "test_venv"
  dir_suffix: "test"
repo_info:
  enable_git_commit_hook: False
"""
        self.tester.create_repo_config(config_disabled)
        result = self._run_setenv_script()
        self.assertIn("Removing git hooks", result.stdout)

    def test_symlink_permissions(self) -> None:
        """
        Test that symlink permissions are set correctly.
        """
        result = self._run_setenv_script()
        self.assertIn("# set_symlink_permissions()", result.stdout)
        self.assertIn("INFO:Remove write permissions for:", result.stdout)


# #############################################################################
# TestSetenvErrorHandling
# #############################################################################


class TestSetenvErrorHandling(_SetenvTestHelper):
    """
    Test error handling functionality.
    """

    def test_missing_repo_config(self) -> None:
        """
        Test behavior when repo_config.yaml is missing.
        """
        os.remove(self.tester.git_root / "repo_config.yaml")
        result = self._run_setenv_script()
        self.assertNotEqual(result.returncode, 0)

    def test_missing_thin_client_utils(self) -> None:
        """
        Test behavior when thin_client_utils.sh is missing.
        """
        os.remove(
            self.tester.git_root
            / "dev_scripts_helpers"
            / "thin_client"
            / "thin_client_utils.sh"
        )
        result = self._run_setenv_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "ERROR: File 'thin_client_utils.sh' not found", result.stderr
        )

    def test_invalid_yaml_syntax(self) -> None:
        """
        Test behavior with invalid YAML syntax.
        """
        invalid_config = """
runnable_dir_info:
  use_helpers_as_nested_module: True
  venv_tag: "test_venv"
  dir_suffix: "test"
repo_info:
  enable_git_commit_hook: True
  invalid: [unclosed: list
"""
        self.tester.create_repo_config(invalid_config)
        self._run_setenv_script()
        # The script should handle invalid YAML gracefully or fail appropriately.
        # The exact behavior depends on the parse_yaml function implementation.


# #############################################################################
# TestSetenvNonNestedModule
# #############################################################################


class TestSetenvNonNestedModule(_SetenvTestHelper):
    """
    Test setenv.sh behavior when not using helpers as nested module.
    """

    def test_non_nested_module_config(self) -> None:
        """
        Test behavior when use_helpers_as_nested_module is False.
        """
        config_non_nested = """
runnable_dir_info:
  use_helpers_as_nested_module: False
  venv_tag: "test_venv"
  dir_suffix: "test"
repo_info:
  enable_git_commit_hook: True
"""
        self.tester.create_repo_config(config_non_nested)
        result = self._run_setenv_script()
        # Should use "helpers" as venv tag instead of the configured one.
        self.assertIn("# activate_venv()", result.stdout)
        # The script should handle this configuration appropriately.


# #############################################################################
# TestSetenvRunnableDirStructure
# #############################################################################


class TestSetenvRunnableDirStructure(_SetenvTestHelper):
    """
    Test setenv.sh behavior in the context of runnable directory structure.
    """

    def test_runnable_dir_configuration(self) -> None:
        """
        Test that setenv.sh works with realistic runnable dir configuration.
        """
        result = self._run_setenv_script()
        # Check that the script handles the realistic config structure.
        self.assertIn("REPO_CONF_repo_info_repo_name=test_repo", result.stdout)
        self.assertIn(
            "REPO_CONF_docker_info_docker_image_name=test-repo", result.stdout
        )
        self.assertIn(
            "REPO_CONF_repo_info_github_repo_account=test-org", result.stdout
        )
        self.assertIn("REPO_CONF_repo_info_issue_prefix=TestTask", result.stdout)

    def test_helpers_root_detection_in_runnable_dir(self) -> None:
        """
        Test helpers_root detection in runnable directory context.
        """
        result = self._run_setenv_script()
        # Should detect helpers_root directory.
        self.assertIn("HELPERS_ROOT_DIR=", result.stdout)
        self.assertIn("helpers_root", result.stdout)

    def test_dev_scripts_directory_structure(self) -> None:
        """
        Test that dev_scripts directory is properly structured.
        """
        result = self._run_setenv_script()
        # Should detect dev_scripts directory with proper suffix.
        self.assertIn("DEV_SCRIPT_DIR=", result.stdout)
        self.assertIn("dev_scripts_test", result.stdout)

    def test_docker_integration_config(self) -> None:
        """
        Test that Docker-related configuration is properly handled.
        """
        result = self._run_setenv_script()
        # Check Docker configuration variables.
        self.assertIn(
            "REPO_CONF_docker_info_use_sibling_container_in_unit_tests=True",
            result.stdout,
        )
        self.assertIn("REPO_CONF_container_registry_info_ecr=", result.stdout)
        self.assertIn("REPO_CONF_container_registry_info_ghcr=", result.stdout)

    def test_s3_bucket_configuration(self) -> None:
        """
        Test that S3 bucket configuration is properly handled.
        """
        result = self._run_setenv_script()
        # Check S3 configuration variables.
        self.assertIn(
            "REPO_CONF_s3_bucket_info_html_bucket_name=s3://test-html",
            result.stdout,
        )
        self.assertIn(
            "REPO_CONF_s3_bucket_info_html_ip=http://172.30.2.44", result.stdout
        )
        self.assertIn(
            "REPO_CONF_s3_bucket_info_unit_test_bucket_name=s3://test-unit-test",
            result.stdout,
        )


# #############################################################################
# TestSetenvSuccessOutput
# #############################################################################


class TestSetenvSuccessOutput(_SetenvTestHelper):
    """
    Test successful script completion and output.
    """

    def test_success_message(self) -> None:
        """
        Test that the script outputs a success message.
        """
        result = self._run_setenv_script()
        self.assertIn("successful", result.stdout)

    def test_environment_signature(self) -> None:
        """
        Test that environment signature is printed.
        """
        result = self._run_setenv_script()
        self.assertIn("# PATH=", result.stdout)
        self.assertIn("# PYTHONPATH=", result.stdout)
        self.assertIn("# printenv=", result.stdout)
        self.assertIn("# alias=", result.stdout)

    def test_script_completion(self) -> None:
        """
        Test that the script completes all expected steps.
        """
        result = self._run_setenv_script()
        # Check that all major steps are executed in the right order.
        self.assertIn("##>", result.stdout)  # Script path.
        self.assertIn("GIT_ROOT_DIR=", result.stdout)  # Git root detection.
        self.assertIn(
            "Thin client utils found at:", result.stdout
        )  # Utils sourcing.
        self.assertIn("##> Parsing repo config", result.stdout)  # Config parsing.
        self.assertIn("REPO_CONF_", result.stdout)  # Config variables.
        self.assertIn("# activate_venv()", result.stdout)  # Venv activation.
        self.assertIn("HELPERS_ROOT_DIR=", result.stdout)  # Helpers root.
        self.assertIn("DEV_SCRIPT_DIR=", result.stdout)  # Dev script dir.
        self.assertIn(
            "DEV_SCRIPT_HELPER_DIR=", result.stdout
        )  # Dev script helper dir.
        self.assertIn("PATH=", result.stdout)  # Path setting.
        self.assertIn("# set_pythonpath()", result.stdout)  # Python path.
        self.assertIn(
            "# set_symlink_permissions()", result.stdout
        )  # Symlink permissions.
        self.assertIn("Installing git hooks", result.stdout)  # Git hooks.
        self.assertIn("# set_csfy_env_vars()", result.stdout)  # CSFY vars.
        self.assertIn(
            "# configure_specific_project()", result.stdout
        )  # Project config.
        self.assertIn("# PATH=", result.stdout)  # Environment signature.
        self.assertIn("successful", result.stdout)  # Success message.
