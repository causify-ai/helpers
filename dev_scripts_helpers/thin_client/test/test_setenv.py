import logging
import os
import pathlib
from typing import Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# _SetenvTestHelper
# #############################################################################


class _SetenvTestHelper(hunitest.TestCase):
    """
    Helper test class to perform common setup and provide utility methods for
    testing setenv.sh script.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> None:
        self.set_up_test()

    def set_up_test(self) -> None:
        """
        Set up test environment.
        """
        # Get the path to the `setenv.sh` script.
        git_root = hgit.find_git_root()
        setenv_files = hsystem.find_file_with_dir(
            "thin_client/setenv.sh",
            root_dir=git_root,
            dir_depth=1,
            mode="assert_unless_one_result",
        )
        self.setenv_path = pathlib.Path(setenv_files[0])
        _LOG.debug("setenv_path=%s", self.setenv_path)
        # Get the path to the `thin_client_utils.sh` and `repo_config.yaml`
        # files that are used by `setenv.sh`.
        utils_files = hsystem.find_file_with_dir(
            "thin_client/thin_client_utils.sh",
            root_dir=git_root,
            dir_depth=1,
            mode="assert_unless_one_result",
        )
        self.thin_client_utils_path = pathlib.Path(utils_files[0])
        _LOG.debug("thin_client_utils_path=%s", self.thin_client_utils_path)
        self.repo_config_path = pathlib.Path(
            hsystem.find_file_in_repo("repo_config.yaml", root_dir=git_root)
        )
        _LOG.debug("repo_config_path=%s", self.repo_config_path)
        # Exit if files do not exist.
        if not self.setenv_path.exists():
            hdbg.dfatal(f"setenv.sh not found at {self.setenv_path}")
        if not self.thin_client_utils_path.exists():
            hdbg.dfatal(
                f"thin_client_utils.sh not found at {self.thin_client_utils_path}"
            )
        if not self.repo_config_path.exists():
            hdbg.dfatal(f"repo_config.yaml not found at {self.repo_config_path}")
        _LOG.debug(
            "Initialized _SetenvScriptTestHelper with setenv.sh, thin_client_utils.sh, and repo_config.yaml"
        )

    def run_setenv_in_clean_bash(self) -> Tuple[int, str]:
        """
        Run setenv.sh in a clean isolated bash environment, capturing both
        output and environment variables.

        :return: tuple of (return_code, output)
        """
        wrapper_script = self._create_wrapper_script()
        # Create a temporary executable file.
        wrapper_path = self._create_tmp_executable_file(wrapper_script)
        _LOG.debug("Running setenv.sh in clean bash environment")
        result = hsystem.system_to_string(
            f"bash {wrapper_path}",
            abort_on_error=False,
            log_level=logging.DEBUG,
        )
        return result

    def _create_wrapper_script(self) -> str:
        """
        Create a wrapper script to run setenv.sh in a clean isolated bash
        environment.

        :return: wrapper script content
        """
        wrapper_script = f"""#!/bin/bash
set -e

# Clear environment variables that might interfere with testing.
unset PYTHONPATH
unset PATH
unset GIT_ROOT_DIR
unset HELPERS_ROOT_DIR
unset DEV_SCRIPT_DIR
unset CSFY_*

# Set minimal PATH for basic commands.
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Change to the directory containing setenv.sh.
cd "{self.setenv_path.parent}"

# Source the setenv.sh script and capture output.
set +e  # Allow the script to fail gracefully.
tmp_out=$(mktemp)
source "{self.setenv_path}" >"$tmp_out" 2>&1
source_status=$?
set -e

# Print the captured output.
echo "=== SETENV.SH OUTPUT ==="
cat "$tmp_out"
echo "=== END SETENV.SH OUTPUT ==="
rm -f "$tmp_out"

# Print environment variables after sourcing.
echo "=== ENVIRONMENT VARIABLES AFTER SETENV ==="
env | sort
echo "=== END ENVIRONMENT VARIABLES ==="

exit $source_status
"""
        return wrapper_script

    def _create_tmp_executable_file(
        self, content: str, suffix: str = ".sh"
    ) -> str:
        """
        Create a temporary executable file.

        :param content: content to write to the file
        :param suffix: file suffix (default: .sh)
        :return: path to the created temporary file
        """
        tmp_dir = self.get_scratch_space()
        tmp_file_name = f"tmp_wrapper_{suffix}"
        tmp_path = os.path.join(tmp_dir, tmp_file_name)
        # Save the content to file.
        hio.to_file(tmp_path, content)
        # Make file executable.
        os.chmod(tmp_path, 0o755)
        return tmp_path


# #############################################################################
# TestSetenvOutput
# #############################################################################


class TestSetenvOutput(_SetenvTestHelper):
    """
    Test the output and environment effects of setenv.sh script.
    """

    def test_setenv_output(self) -> None:
        """
        Test that setenv.sh produces expected output and no errors.
        """
        # Run setenv.sh and capture output.
        return_code, output = self.run_setenv_in_clean_bash()
        # Check that the script ran successfully.
        self.assertEqual(
            return_code,
            0,
            f"setenv.sh failed with return code {return_code}. Output: {output}",
        )
        # Check for expected output.
        self.assertIn("##>", output, "Script should show its path with ##>")
        self.assertIn("setenv.sh", output, "Script should mention setenv.sh")
        self.assertIn("GIT_ROOT_DIR=", output, "Script should set GIT_ROOT_DIR")
        self.assertIn(
            "Thin client utils found at:",
            output,
            "Script should find thin_client_utils.sh",
        )
        self.assertIn(
            "##> Parsing repo config", output, "Script should parse repo config"
        )
        self.assertIn(
            "# activate_venv()",
            output,
            "Script should activate virtual environment",
        )
        self.assertIn(
            "HELPERS_ROOT_DIR=", output, "Script should set HELPERS_ROOT_DIR"
        )
        self.assertIn(
            "DEV_SCRIPT_DIR=", output, "Script should set DEV_SCRIPT_DIR"
        )
        self.assertIn("PATH=", output, "Script should set PATH")
        self.assertIn(
            "# set_pythonpath()", output, "Script should set PYTHONPATH"
        )
        self.assertIn(
            "# set_symlink_permissions()",
            output,
            "Script should handle symlink permissions",
        )
        self.assertIn(
            "Installing git hooks", output, "Script should install git hooks"
        )
        self.assertIn(
            "# set_csfy_env_vars()",
            output,
            "Script should set CSFY environment variables",
        )
        self.assertIn(
            "# configure_specific_project()",
            output,
            "Script should configure project",
        )
        self.assertIn(
            "# PATH=", output, "Script should print environment signature"
        )
        self.assertIn(
            "# PYTHONPATH=", output, "Script should print PYTHONPATH in signature"
        )
        self.assertIn("successful", output, "Script should show success message")
        error_patterns = [
            "ERROR:",
            "FATAL:",
            "CRITICAL:",
            "Exception:",
            "Traceback:",
        ]
        for pattern in error_patterns:
            self.assertNotIn(
                pattern,
                output,
                f"Output should not contain error pattern: {pattern}",
            )

    def test_setenv_environment_variables(self) -> None:
        """
        Test that setenv.sh sets up environment variables correctly.
        """
        # Run setenv.sh and capture environment.
        return_code, output = self.run_setenv_in_clean_bash()
        self.assertEqual(
            return_code,
            0,
            f"setenv.sh failed with return code {return_code}. Output: {output}",
        )
        # Extract environment variables section.
        env_start = output.find("=== ENVIRONMENT VARIABLES AFTER SETENV ===")
        env_end = output.find("=== END ENVIRONMENT VARIABLES ===")
        self.assertNotEqual(
            env_start, -1, "Environment variables section should be present"
        )
        self.assertNotEqual(
            env_end, -1, "Environment variables section should be present"
        )
        env_section = output[env_start:env_end]
        expected_vars = [
            "PATH=",
            "PYTHONPATH=",
            "CSFY_HOST_NAME=",
            "CSFY_HOST_OS_NAME=",
            "CSFY_HOST_USER_NAME=",
            "CSFY_HOST_OS_VERSION=",
            "CSFY_AWS_PROFILE=",
            "CSFY_AWS_S3_BUCKET=",
            "CSFY_ECR_BASE_PATH=",
        ]
        # Check for expected environment variables.
        for var in expected_vars:
            self.assertIn(
                var, env_section, f"Environment should contain variable: {var}"
            )
