import logging
import os
import pathlib
from typing import Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# _SetenvTestCase
# #############################################################################


class _SetenvTestCase(hunitest.TestCase):
    """
    Helper test class to perform common setup and provide utility methods for
    testing `setenv.sh` script.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> None:
        self.set_up_test()

    def set_up_test(self) -> None:
        """
        Set up test environment.
        """
        # TODO(sandeep): Factor out general utilities like `get setenv_path`,
        # `get thin_client_utils_path`, and `get repo_config_path` into
        # `helpers/henv.py`.
        # Get the path to the `setenv.sh` script.
        helpers_root = hgit.find_helpers_root()
        setenv_files = hsystem.find_file_with_dir(
            "thin_client/setenv.sh",
            root_dir=helpers_root,
            dir_depth=1,
            mode="assert_unless_one_result",
        )
        self.setenv_path = pathlib.Path(setenv_files[0])
        _LOG.debug("setenv_path=%s", self.setenv_path)
        # Get the path to the `thin_client_utils.sh` and `repo_config.yaml`
        # files that are used by `setenv.sh`.
        utils_files = hsystem.find_file_with_dir(
            "thin_client/thin_client_utils.sh",
            root_dir=helpers_root,
            dir_depth=1,
            mode="assert_unless_one_result",
        )
        self.thin_client_utils_path = pathlib.Path(utils_files[0])
        _LOG.debug("thin_client_utils_path=%s", self.thin_client_utils_path)
        self.repo_config_path = pathlib.Path(
            hsystem.find_file_in_repo("repo_config.yaml", root_dir=helpers_root)
        )
        _LOG.debug("repo_config_path=%s", self.repo_config_path)
        # Exit if files do not exist.
        hdbg.dassert_file_exists(str(self.setenv_path))
        hdbg.dassert_file_exists(str(self.thin_client_utils_path))
        hdbg.dassert_file_exists(str(self.repo_config_path))
        _LOG.debug(
            "Initialized _SetenvTestCase with `setenv.sh`, `thin_client_utils.sh`, \
                and `repo_config.yaml`"
        )

    def run_setenv_in_clean_bash(self) -> Tuple[int, str]:
        """
        Run `setenv.sh` in a clean isolated bash environment, capturing both
        output and environment variables.

        :return: tuple of (return_code, output)
        """
        wrapper_script = self._create_wrapper_script()
        # Create a temporary executable file.
        tmp_dir = self.get_scratch_space()
        wrapper_path = os.path.join(tmp_dir, "tmp_wrapper.sh")
        hio.create_executable_script(wrapper_path, wrapper_script)
        _LOG.debug("Running `setenv.sh` in clean bash environment")
        # Use `env -i` to reset the environment.
        result = hsystem.system_to_string(
            f"env -i bash {wrapper_path}",
            abort_on_error=False,
            log_level=logging.DEBUG,
        )
        # Write all test outputs to files for debugging.
        # `result` is a tuple of (return_code, output).
        self._write_test_outputs(result[1])
        return result

    def _write_output_to_file(self, output: str, filename: str) -> None:
        """
        Write the output to a file in the test output directory.

        :param output: output to write
        :param filename: filename to write to
        """
        output_dir = self.get_output_dir(test_class_name=self.__class__.__name__)
        hio.create_dir(output_dir, incremental=True)
        output_file = os.path.join(output_dir, filename)
        hio.to_file(output_file, output)
        _LOG.debug("Test output written to: %s", output_file)

    def _write_test_outputs(self, output: str) -> None:
        """
        Write `setenv.sh` test output and environment variables to files.

        :param output: complete output from the setenv script
        """
        # Extract and write environment variables separately.
        env_start = output.find("=== ENVIRONMENT VARIABLES AFTER setenv.sh ===")
        env_end = output.find("=== END ENVIRONMENT VARIABLES AFTER setenv.sh ===")
        if env_start != -1 and env_end != -1:
            env_section = output[env_start:env_end]
            self._write_output_to_file(env_section, "environment_variables.txt")
        # Extract and write setenv.sh output separately.
        setenv_start = output.find("=== setenv.sh output ===")
        setenv_end = output.find("=== END setenv.sh output ===")
        if setenv_start != -1 and setenv_end != -1:
            setenv_section = output[setenv_start:setenv_end]
            self._write_output_to_file(setenv_section, "setenv_script_output.txt")

    def _create_wrapper_script(self) -> str:
        """
        Create a wrapper script to run `setenv.sh` in a clean isolated bash
        environment.

        :return: wrapper script content
        """
        wrapper_script = f"""#!/bin/bash
        set -e

        # Set minimal PATH for basic commands.
        export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

        # Change to the directory containing `setenv.sh`.
        cd "{self.setenv_path.parent}"

        # Source the `setenv.sh` script and capture output.
        # Allow the script to fail gracefully.
        set +e
        tmp_out=$(mktemp)
        source "{self.setenv_path}" >"$tmp_out" 2>&1
        source_status=$?
        set -e

        # Print the captured output.
        echo "=== setenv.sh output ==="
        cat "$tmp_out"
        echo "=== END setenv.sh output ==="
        rm -f "$tmp_out"

        # Print environment variables after sourcing.
        echo "=== ENVIRONMENT VARIABLES AFTER setenv.sh ==="
        env | sort
        echo "=== END ENVIRONMENT VARIABLES AFTER setenv.sh ==="

        exit $source_status
        """
        wrapper_script = hprint.dedent(wrapper_script)
        return wrapper_script

    def _parse_environment_variables(self, env_section: str) -> dict:
        """
        Extract environment variable values by using `=` as the delimiter.

        :param env_section: environment variables section from the
            output
        :return: dictionary mapping variable names to their values
        """
        env_vars = {}
        lines = env_section.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("==="):
                continue
            # Parse lines in format `VAR_NAME=value`.
            if "=" in line:
                var_name, value = line.split("=", 1)
                env_vars[var_name] = value
        _LOG.debug("Environment variables: %s", env_vars)
        return env_vars


# #############################################################################
# TestSetenvOutput
# #############################################################################


class TestSetenvOutput(_SetenvTestCase):
    """
    Test the output and environment effects of `setenv.sh` script.
    """

    def test_setenv_output(self) -> None:
        """
        Test that `setenv.sh` produces expected output and no errors.
        """
        # Run `setenv.sh` and capture output.
        return_code, output = self.run_setenv_in_clean_bash()
        # Check that the script ran successfully.
        self.assertEqual(
            return_code,
            0,
            f"setenv.sh failed with return code {return_code}. Output: {output}",
        )
        # Check for expected output patterns.
        expected_patterns = [
            ("##>", "Script should show its path with ##>"),
            ("setenv.sh", "Script should mention setenv.sh"),
            ("GIT_ROOT_DIR=", "Script should set GIT_ROOT_DIR"),
            (
                "Thin client utils found at:",
                "Script should find thin_client_utils.sh",
            ),
            ("##> Parsing repo config", "Script should parse repo config"),
            ("# activate_venv()", "Script should activate virtual environment"),
            ("HELPERS_ROOT_DIR=", "Script should set HELPERS_ROOT_DIR"),
            ("DEV_SCRIPT_DIR=", "Script should set DEV_SCRIPT_DIR"),
            ("PATH=", "Script should set PATH"),
            ("# set_pythonpath()", "Script should set PYTHONPATH"),
            (
                "# set_symlink_permissions()",
                "Script should handle symlink permissions",
            ),
            ("Installing git hooks", "Script should install git hooks"),
            (
                "# set_csfy_env_vars()",
                "Script should set CSFY environment variables",
            ),
            ("# configure_specific_project()", "Script should configure project"),
            ("# PATH=", "Script should print environment signature"),
            ("# PYTHONPATH=", "Script should print PYTHONPATH in signature"),
            ("successful", "Script should show success message"),
        ]
        for pattern, description in expected_patterns:
            self.assertIn(pattern, output, description)
        # Check for absence of error patterns.
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
        Test that `setenv.sh` sets up environment variables correctly.
        """
        # Run `setenv.sh` and capture environment.
        return_code, output = self.run_setenv_in_clean_bash()
        self.assertEqual(
            return_code,
            0,
            f"setenv.sh failed with return code {return_code}. Output: {output}",
        )
        # Extract environment variables section.
        env_start = output.find("=== ENVIRONMENT VARIABLES AFTER setenv.sh ===")
        env_end = output.find("=== END ENVIRONMENT VARIABLES AFTER setenv.sh ===")
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
        # Extract environment variables from the environment variables section.
        env_vars = self._parse_environment_variables(env_section)
        # Check that environment variables are not empty or None.
        for var in expected_vars:
            # Remove the trailing `=` from the variable name.
            var_name = var[:-1]
            if var_name in env_vars:
                value = env_vars[var_name]
                self.assertIsNotNone(
                    value, f"Environment variable {var_name} should not be None"
                )
                self.assertNotEqual(
                    value.strip(),
                    "",
                    f"Environment variable {var_name} should not be empty",
                )
                _LOG.debug("Environment variable %s=%s", var_name, value)
