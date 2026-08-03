"""
Import as:

import helpers.test.test_hunit_test_purification as thuntepur
"""

import datetime
import logging
import os
import unittest.mock as umock
from typing import Any, Dict, List, Optional, Tuple

import pytest

import helpers.hgit as hgit
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_purification as huntepur
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_purify_txt_from_client
# #############################################################################


class Test_purify_txt_from_client(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_txt_from_client()` function.
    """

    def helper(self, txt: str, expected: str, **kwargs: Any) -> None:
        """
        Helper for testing purify_txt_from_client.

        :param txt: Input text to purify
        :param expected: Expected output
        :param kwargs: Additional arguments to pass to assert_equal
        """
        # Run test.
        actual = huntepur.purify_txt_from_client(txt)
        # Check outputs.
        self.assert_equal(actual, expected, **kwargs)

    def helper_with_git_root_mocking(self, relative_path: str) -> None:
        """
        Helper for tests that need git root mocking.

        Build `txt` by joining the real git root with `relative_path` and
        check that it purifies to `$GIT_ROOT/<relative_path>`.

        :param relative_path: path relative to the git root to test
        """
        # Prepare inputs.
        git_root: str = hgit.get_client_root(super_module=False)
        pwd: str = os.path.dirname(git_root)
        txt = os.path.join(git_root, relative_path)
        expected = f"$GIT_ROOT/{relative_path}"
        with umock.patch("os.getcwd", return_value=pwd):
            self.helper(txt, expected)

    def test1(self) -> None:
        """
        Test removing 'amp/' prefix from file paths.
        """
        # Prepare inputs.
        txt = "amp/helpers/test/test_system_interaction.py"
        # Prepare outputs.
        expected = "helpers/test/test_system_interaction.py"
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing 'amp/' prefix from multiple paths in one string.
        """
        # Prepare inputs.
        txt = """
        amp/helpers/test/test_file1.py
        amp/helpers/test/test_file2.py
        amp/helpers/test/test_file3.py
        """
        txt = hprint.dedent(txt)
        # Prepare outputs.
        expected = """
        helpers/test/test_file1.py
        helpers/test/test_file2.py
        helpers/test/test_file3.py
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing 'amp/' prefix from list of file paths.
        """
        # Prepare inputs.
        txt = "['amp/helpers/test/test_system_interaction.py']"
        # Prepare outputs.
        expected = "['helpers/test/test_system_interaction.py']"
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test removing 'app.' prefix from dotted module paths.
        """
        # Prepare inputs.
        txt = "app.helpers.test.test_system_interaction.py"
        # Prepare outputs.
        expected = "helpers.test.test_system_interaction.py"
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test that longer paths are processed before shorter ones using real paths.
        """
        self.helper_with_git_root_mocking("src/file.py")

    def test6(self) -> None:
        """
        Test that paths with multiple occurrences of the same pattern are
        processed correctly using real paths.
        """
        self.helper_with_git_root_mocking("src/project/file.py")

    def test7(self) -> None:
        """
        Test that paths with multiple patterns are processed in the correct
        order using real pwd.
        """
        self.helper_with_git_root_mocking("src/project/file.py")

    def test8(self) -> None:
        """
        Test that paths with no matching patterns are left unchanged.
        """
        other_path = "/var/tmp/other/file.py"
        txt = other_path
        expected = other_path
        # Get pwd for mocking context (hgit call happens inside helper).
        git_root = hgit.get_client_root(super_module=False)
        pwd = os.path.dirname(git_root)
        with umock.patch("os.getcwd", return_value=pwd):
            self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test purification of pylint/flake8/mypy output with $SUPER_MODULE paths.
        """
        # Prepare inputs.
        super_module_path = hgit.get_client_root(super_module=True)
        # pylint: disable=line-too-long
        txt = r"""
        ************* Module input [pylint]
        $SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py: Your code has been rated at -10.00/10 (previous run: -10.00/10, +0.00) [pylint]
        $SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:20: W605 invalid escape sequence '\s' [flake8]
        $SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:9: F821 undefined name 're' [flake8]
        cmd line='$SUPER_MODULE/dev_scripts/linter.py -f $SUPER_MODULE/amp/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py --linter_log $SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/linter.log'
        dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [E0602(undefined-variable), ] Undefined variable 're' [pylint]
        dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [W1401(anomalous-backslash-in-string), ] Anomalous backslash in string: '\s'. String constant might be missing an r prefix. [pylint]
        dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: error: Name 're' is not defined [mypy]
        """
        txt = hprint.dedent(txt)
        txt = txt.replace("$SUPER_MODULE", super_module_path)
        # pylint: enable=line-too-long
        # Prepare outputs.
        expected = r"""
        ************* Module input [pylint]
        $GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py: Your code has been rated at -10.00/10 (previous run: -10.00/10, +0.00) [pylint]
        $GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:20: W605 invalid escape sequence '\s' [flake8]
        $GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:9: F821 undefined name 're' [flake8]
        cmd line='$GIT_ROOT/dev_scripts/linter.py -f $GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py --linter_log $GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/linter.log'
        dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [E0602(undefined-variable), ] Undefined variable 're' [pylint]
        dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [W1401(anomalous-backslash-in-string), ] Anomalous backslash in string: '\s'. String constant might be missing an r prefix. [pylint]
        dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: error: Name 're' is not defined [mypy]
        """
        # Run test.
        self.helper(txt, expected, dedent=True)

    def test10(self) -> None:
        """
        Test case when client root path is equal to `/`
        """
        # Prepare inputs.
        txt = "/tmp/subdir1"
        # Prepare outputs.
        expected = txt
        # Run test.
        with umock.patch("helpers.hgit.get_client_root", return_value="/"):
            self.helper(txt, expected)

    def test11(self) -> None:
        """
        Test the correct order of `app` -> `amp` purification with multiple
        import statements.
        """
        txt = """
        import app.amp.helpers_root.helpers.test.test_file
        from app.amp.helpers_root.helpers.hprint import dedent
        import app.amp.helpers.config
        from amp.app.helpers.config import get_config
        import amp.app.helpers_root.config
        """
        expected = """
        import helpers.test.test_file
        from helpers.hprint import dedent
        import helpers.config
        from helpers.config import get_config
        import helpers.config
        """
        self.helper(txt, expected)

    def test12(self) -> None:
        """
        Test amp and app purification in file path strings.
        """
        txt = """
        app/amp/helpers_root/helpers/test/test_file.py
        amp/app/helpers_root/helpers/test/test_file.py
        """
        expected = """
        helpers/test/test_file.py
        helpers/test/test_file.py
        """
        self.helper(txt, expected)

    def test13(self) -> None:
        """
        Test purification of a full docker run command with API keys,
        paths, and docker image name.
        """
        # Prepare inputs.
        txt = (
            "docker run --rm --user $(id -u):$(id -g)"
            " -e AM_CONTAINER_VERSION"
            " -e ARTIFICIAL_ANALYSIS_API_KEY"
            " -e CSFY_AWS_ACCESS_KEY_ID"
            " -e CSFY_AWS_DEFAULT_REGION"
            " -e CSFY_AWS_PROFILE"
            " -e CSFY_AWS_S3_BUCKET"
            " -e CSFY_AWS_SECRET_ACCESS_KEY"
            " -e CSFY_AWS_SESSION_TOKEN"
            " -e CSFY_CI -e CSFY_ECR_BASE_PATH"
            " -e CSFY_ENABLE_DIND"
            " -e CSFY_FORCE_TEST_FAIL"
            " -e CSFY_GIT_ROOT_PATH"
            " -e CSFY_HELPERS_ROOT_PATH"
            " -e CSFY_HOST_GIT_ROOT_PATH"
            " -e CSFY_HOST_NAME"
            " -e CSFY_HOST_OS_NAME"
            " -e CSFY_HOST_OS_VERSION"
            " -e CSFY_HOST_USER_NAME"
            " -e CSFY_REPO_CONFIG_CHECK"
            " -e CSFY_REPO_CONFIG_PATH"
            " -e CSFY_TELEGRAM_TOKEN"
            " -e CSFY_USE_HELPERS_AS_NESTED_MODULE"
            " -e OPENAI_API_KEY"
            " -e OPENROUTER_API_KEY"
            " -e QUANDL_API_KEY"
            " --workdir /app"
            " tmp.latex.aarch64.417056b0"
            " pdflatex -output-directory"
            " /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch"
            " --interaction=nonstopmode --halt-on-error --shell-escape"
            " /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.tex"
        )
        # Prepare outputs.
        expected = (
            "$DOCKER_EXECUTABLE run --rm --user $(id -u):$(id -g)"
            " -e ..."
            " --workdir $GIT_ROOT"
            " tmp.latex.$ARCH.$CONTAINER_ID"
            " pdflatex -output-directory"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch"
            " --interaction=nonstopmode --halt-on-error --shell-escape"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.tex"
        )
        # Run test.
        self.helper(txt, expected)

    def test14(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test15(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_directory_paths
# #############################################################################


class Test_purify_directory_paths(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_directory_paths()` function.
    """

    def helper(self, input_: str, expected: str) -> None:
        """
        Helper for testing purify_directory_paths.

        :param input_: Input path to test
        :param expected: Expected output path
        """
        # Run test.
        actual = huntepur.purify_directory_paths(input_)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def helper_with_env_and_pwd_mocking(
        self,
        input_: str,
        expected: str,
        env_vars: Optional[Dict[str, str]] = None,
        git_root: Optional[str] = None,
    ) -> None:
        """
        Helper for tests that need env and pwd mocking.

        :param input_: Input path to test
        :param expected: Expected output path
        :param env_vars: Optional dict of env vars to patch
        :param git_root: Optional git root (if None, uses actual git root)
        """
        # Prepare inputs.
        if git_root is None:
            git_root = hgit.get_client_root(super_module=False)
        pwd: str = os.path.dirname(git_root)
        if env_vars is None:
            env_vars = {}
        # Run test.
        with (
            umock.patch.dict("os.environ", env_vars, clear=True),
            umock.patch("os.getcwd", return_value=pwd),
        ):
            self.helper(input_, expected)

    def _get_git_root_and_fake_csfy_env_vars(
        self,
    ) -> Tuple[str, str, Dict[str, str]]:
        """
        Return the real git root together with a fake
        `CSFY_HOST_GIT_ROOT_PATH` and the corresponding `env_vars` dict.

        :return: real git root, fake `CSFY_HOST_GIT_ROOT_PATH`, and
            `env_vars` dict patching `CSFY_HOST_GIT_ROOT_PATH` to the fake
            value
        """
        git_root = hgit.get_client_root(super_module=False)
        csfy_host_git_root = "/tmp/csfy_host_git_root"
        env_vars = {"CSFY_HOST_GIT_ROOT_PATH": csfy_host_git_root}
        return git_root, csfy_host_git_root, env_vars

    def test1(self) -> None:
        """
        Test the replacement of `GIT_ROOT` using real git root.
        """
        git_root, _, env_vars = self._get_git_root_and_fake_csfy_env_vars()
        input_ = os.path.join(git_root, "src/subdir/file.py")
        expected = "$GIT_ROOT/src/subdir/file.py"
        self.helper_with_env_and_pwd_mocking(
            input_, expected, env_vars, git_root
        )

    def test2(self) -> None:
        """
        Test the replacement of `CSFY_HOST_GIT_ROOT_PATH` using real git root.
        """
        git_root, csfy_host_git_root, env_vars = (
            self._get_git_root_and_fake_csfy_env_vars()
        )
        input_ = f"{csfy_host_git_root}/other/file.py"
        expected = "$CSFY_HOST_GIT_ROOT_PATH/other/file.py"
        self.helper_with_env_and_pwd_mocking(
            input_, expected, env_vars, git_root
        )

    def test3(self) -> None:
        """
        Test the replacement of `PWD` using real git root and pwd.
        """
        git_root, _, env_vars = self._get_git_root_and_fake_csfy_env_vars()
        git_root = git_root.rstrip("/")
        pwd = os.path.dirname(git_root)
        # TODO(gp): Skip test if pwd is "/": the purification function
        # explicitly skips replacing "/" to avoid corrupting all paths. This
        # edge case occurs when git_root has no parent as in the CI (e.g.,
        # git_root="/app" gives pwd="/").
        if pwd == "/":
            pytest.skip("Cannot test PWD replacement when parent directory is /")
        input_ = f"{pwd}/documents/file.py"
        expected = "$PWD/documents/file.py"
        with umock.patch("helpers.hgit.get_client_root", return_value=git_root):
            self.helper_with_env_and_pwd_mocking(
                input_, expected, env_vars, git_root
            )

    def test4(self) -> None:
        """
        Test when `GIT_ROOT`, `CSFY_HOST_GIT_ROOT_PATH` and pwd are the same.
        """
        git_root = hgit.get_client_root(super_module=False)
        input_ = os.path.join(git_root, "file.py")
        expected = "$GIT_ROOT/file.py"
        env_vars = {"CSFY_HOST_GIT_ROOT_PATH": git_root}
        self.helper_with_env_and_pwd_mocking(
            input_, expected, env_vars, git_root
        )

    def test5(self) -> None:
        """
        Test with empty string input.
        """
        input_ = ""
        expected = ""
        self.helper(input_, expected)

    def test6(self) -> None:
        """
        Test with single character input.
        """
        input_ = "a"
        expected = "a"
        self.helper(input_, expected)


# #############################################################################
# Test_purify_from_environment
# #############################################################################


class Test_purify_from_environment(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_from_environment()` function.
    """

    def helper(self, input_: str, expected: str) -> None:
        """
        Helper for testing purify_from_environment.

        :param input_: Input string to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        hsystem.set_user_name("root")
        try:
            # Run test.
            actual = huntepur.purify_from_environment(input_)
            # Check outputs.
            self.assert_equal(actual, expected, fuzzy_match=True)
        finally:
            # Reset the global user name variable regardless of a test results.
            hsystem.set_user_name("")

    def test1(self) -> None:
        input_ = "IMAGE=$CSFY_ECR_BASE_PATH/amp_test:local-root-1.0.0"
        expected = "IMAGE=$CSFY_ECR_BASE_PATH/amp_test:local-$USER_NAME-1.0.0"
        self.helper(input_, expected)

    def test2(self) -> None:
        input_ = "--name root.amp_test.app.app"
        expected = "--name $USER_NAME.amp_test.app.app"
        self.helper(input_, expected)

    def test3(self) -> None:
        input_ = "run --rm -l user=root"
        expected = "run --rm -l user=$USER_NAME"
        self.helper(input_, expected)

    def test4(self) -> None:
        input_ = "run_docker_as_root='True'"
        expected = "run_docker_as_root='True'"
        self.helper(input_, expected)

    def test5(self) -> None:
        input_ = "out_col_groups: [('root_q_mv',), ('root_q_mv_adj',), ('root_q_mv_os',)]"
        expected = "out_col_groups: [('root_q_mv',), ('root_q_mv_adj',), ('root_q_mv_os',)]"
        self.helper(input_, expected)

    def test6(self) -> None:
        input_ = ""
        expected = ""
        self.helper(input_, expected)

    def test7(self) -> None:
        input_ = "a"
        expected = "a"
        self.helper(input_, expected)


# #############################################################################
# Test_purify_amp_references
# #############################################################################


class Test_purify_amp_references(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_amp_references()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_amp_references.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        txt = hprint.dedent(txt)
        # Prepare outputs.
        expected = hprint.dedent(expected)
        # Run test.
        actual = huntepur.purify_amp_references(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Remove the reference to `amp.`.
        """
        txt = """
        * Failed assertion *
        Instance '<amp.helpers.test.test_dbg._Man object at 0x123456>'
            of class '_Man' is not a subclass of '<class 'int'>'
        """
        expected = r"""
        * Failed assertion *
        Instance '<helpers.test.test_dbg._Man object at 0x123456>'
            of class '_Man' is not a subclass of '<class 'int'>'
        """
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing multiple amp references in a single string.
        """
        txt = """
        ImportError: No module named 'amp.helpers.test.test_file'
        """
        expected = r"""
        ImportError: No module named 'helpers.test.test_file'
        """
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing amp references in file paths.
        """
        txt = """
        File "/home/user/amp/helpers/test/test_dbg.py", line 10
        File "/home/user/amp/helpers/test/test_file.py", line 20
        """
        expected = r"""
        File "/home/user/helpers/test/test_dbg.py", line 10
        File "/home/user/helpers/test/test_file.py", line 20
        """
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test removing amp references in import statements.
        """
        txt = """
        from amp.helpers.test import test_dbg
        import amp.helpers.test.test_file
        from amp.helpers.test.test_dbg import _Man
        """
        expected = r"""
        from helpers.test import test_dbg
        import helpers.test.test_file
        from helpers.test.test_dbg import _Man
        """
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test removing amp references in docstrings and comments.
        """
        txt = """
        # This is a test for amp.helpers.test.test_dbg
        """
        expected = r"""
        # This is a test for helpers.test.test_dbg
        """
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test removing amp references in error messages with multiple
        occurrences.
        """
        txt = """
        Error in amp.helpers.test.test_dbg: Invalid input
        Error in amp.helpers.test.test_file: File not found
        Error in amp.helpers.test.test_dbg: Permission denied
        """
        expected = r"""
        Error in helpers.test.test_dbg: Invalid input
        Error in helpers.test.test_file: File not found
        Error in helpers.test.test_dbg: Permission denied
        """
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test that longer amp paths are processed before shorter ones.
        """
        txt = "amp/helpers/amp/test/test_file.py"
        expected = "helpers/test/test_file.py"
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test that nested amp references are processed correctly.
        """
        txt = "amp.helpers.test.amp.TestClass"
        expected = "helpers.test.amp.TestClass"
        self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test removing amp references from test creation comments with various
        module paths.
        """
        txt = """
        # Test created for amp.helpers.test.test_file
        # Test created for amp.core.dataflow.model
        # Test created for amp.helpers.test.test_dbg._Man
        """
        expected = r"""
        # Test created for helpers.test.test_file
        # Test created for core.dataflow.model
        # Test created for helpers.test.test_dbg._Man
        """
        self.helper(txt, expected)

    def test10(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test11(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_app_references
# #############################################################################


class Test_purify_app_references(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_app_references()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_app_references.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        # Run test.
        actual = huntepur.purify_app_references(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test app.helpers reference removal.
        """
        txt = "app.helpers.test.test_file"
        expected = "helpers.test.test_file"
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test app.amp.helpers reference removal.
        """
        txt = "app.amp.helpers.test.test_file"
        expected = "amp.helpers.test.test_file"
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test app.amp.helpers_root.helpers reference removal.
        """
        txt = "app.amp.helpers_root.helpers.test.test_file"
        expected = "amp.helpers.test.test_file"
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test multiple app references in the same string.
        """
        txt = """
        app.helpers.test.test_file
        app.amp.helpers.test.test_file
        app.amp.helpers_root.helpers.test.test_file
        """
        expected = """
        helpers.test.test_file
        amp.helpers.test.test_file
        amp.helpers.test.test_file
        """
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test that longer app paths are processed before shorter ones.
        """
        txt = "app/helpers/app/test/test_file.py"
        expected = "helpers/test/test_file.py"
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test that app.amp.helpers_root references are processed before app.amp.
        """
        txt = "app.amp.helpers_root.helpers.test.TestClass"
        expected = "amp.helpers.test.TestClass"
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test string with no app references.
        """
        txt = "path/to/file.txt"
        expected = "path/to/file.txt"
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test removing app references from test creation comments with various
        module paths.
        """
        txt = """
        # Test created for app.helpers.test.test_file
        # Test created for app.core.dataflow.model
        # Test created for app.helpers.test.test_dbg._Man
        """
        expected = r"""
        # Test created for helpers.test.test_file
        # Test created for core.dataflow.model
        # Test created for helpers.test.test_dbg._Man
        """
        self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test10(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_super_module_references
# #############################################################################


class Test_purify_super_module_references(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_super_module_references()` function.
    """

    def helper(self, super_module_root: str, txt: str, expected: str) -> None:
        """
        Helper for testing purify_super_module_references.

        :param super_module_root: Super module root path to mock
        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Run test.
        with umock.patch(
            "helpers.hgit.get_client_root", return_value=super_module_root
        ):
            actual = huntepur.purify_super_module_references(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test stripping an arbitrary super-module checkout dir name (e.g.,
        `csfy1`, as opposed to the hardcoded `amp`/`app` names) from a plain
        dotted qualname.
        """
        # Prepare inputs.
        super_module_root = "/Users/user/src/csfy1"
        txt = "csfy1.helpers_root.helpers.test.test_hobject._Object1"
        # Prepare outputs.
        expected = "helpers_root.helpers.test.test_hobject._Object1"
        # Run test.
        self.helper(super_module_root, txt, expected)

    def test2(self) -> None:
        """
        Test stripping the super-module prefix from a `<module.Class object
        at 0x...>`-style repr.
        """
        # Prepare inputs.
        super_module_root = "/Users/user/src/csfy1"
        txt = (
            "<csfy1.helpers_root.helpers.test.test_hobject._Object1 at 0x123456>"
        )
        # Prepare outputs.
        expected = (
            "<helpers_root.helpers.test.test_hobject._Object1 at 0x123456>"
        )
        # Run test.
        self.helper(super_module_root, txt, expected)

    def test3(self) -> None:
        """
        Test stripping the super-module prefix from a `class '...'`-style
        reference.
        """
        # Prepare inputs.
        super_module_root = "/Users/user/src/csfy1"
        txt = "class 'csfy1.helpers_root.helpers.test.test_hdbg._Man'"
        # Prepare outputs.
        expected = "class 'helpers_root.helpers.test.test_hdbg._Man'"
        # Run test.
        self.helper(super_module_root, txt, expected)

    def test4(self) -> None:
        """
        Test that a super-module name other than `csfy1` is also handled,
        since the prefix is derived dynamically instead of hardcoded.
        """
        # Prepare inputs.
        super_module_root = "/Users/user/src/cmamp1"
        txt = "cmamp1.helpers_root.helpers.test.test_hobject._Object1"
        # Prepare outputs.
        expected = "helpers_root.helpers.test.test_hobject._Object1"
        # Run test.
        self.helper(super_module_root, txt, expected)

    def test5(self) -> None:
        """
        Test that `amp`/`app` are left untouched, since those are already
        handled by `purify_amp_references()`/`purify_app_references()`.
        """
        # Prepare inputs.
        super_module_root = "/Users/user/src/amp"
        txt = "amp.helpers.test.test_hobject._Object1"
        # Prepare outputs.
        expected = "amp.helpers.test.test_hobject._Object1"
        # Run test.
        self.helper(super_module_root, txt, expected)

    def test6(self) -> None:
        """
        Test that text with no super-module reference is left unchanged.
        """
        # Prepare inputs.
        super_module_root = "/Users/user/src/csfy1"
        txt = "helpers.test.test_hobject._Object1"
        # Prepare outputs.
        expected = "helpers.test.test_hobject._Object1"
        # Run test.
        self.helper(super_module_root, txt, expected)

    def test7(self) -> None:
        """
        Test that a `/` super-module root (no nesting detected) is a no-op.
        """
        # Prepare inputs.
        super_module_root = "/"
        txt = "csfy1.helpers_root.helpers.test.test_hobject._Object1"
        # Prepare outputs.
        expected = "csfy1.helpers_root.helpers.test.test_hobject._Object1"
        # Run test.
        self.helper(super_module_root, txt, expected)

    def test8(self) -> None:
        """
        Test with empty string input.
        """
        super_module_root = "/Users/user/src/csfy1"
        txt = ""
        expected = ""
        self.helper(super_module_root, txt, expected)

    def test9(self) -> None:
        """
        Test with single character input.
        """
        super_module_root = "/Users/user/src/csfy1"
        txt = "a"
        expected = "a"
        self.helper(super_module_root, txt, expected)


# #############################################################################
# Test_purify_from_env_vars
# #############################################################################


# TODO(ShaopengZ): numerical issue. (arm vs x86)
@pytest.mark.requires_ck_infra
class Test_purify_from_env_vars(hunitest.TestCase):
    """
    Test purification from env vars.
    """

    def helper(self, env_var: str) -> None:
        """
        Helper for testing purify_from_env_vars.

        :param env_var: Environment variable to test
        """
        # Prepare inputs.
        env_var_value = os.environ[env_var]
        input_ = f"s3://{env_var_value}/"
        # Prepare outputs.
        expected = f"s3://${env_var}/"
        # Run test.
        actual = huntepur.purify_from_env_vars(input_)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    @pytest.mark.skipif(
        not hrecouti.get_repo_config().get_name() == "//cmamp",
        reason="Run only in //cmamp",
    )
    def test1(self) -> None:
        """
        - $CSFY_AWS_S3_BUCKET
        """
        env_var = "CSFY_AWS_S3_BUCKET"
        self.helper(env_var)


# #############################################################################
# Test_purify_object_representation
# #############################################################################


class Test_purify_object_representation(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_object_representation()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_object_representation.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        txt = hprint.dedent(txt)
        # Prepare outputs.
        expected = hprint.dedent(expected)
        # Run test.
        actual = huntepur.purify_object_representation(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        txt = """
        load_prices: {'source_node_name': 'RealTimeDataSource object
        at 0x7f571c329b50
        """
        expected = r"""
        load_prices: {'source_node_name': 'RealTimeDataSource object
        at 0x"""
        self.helper(txt, expected)

    def test2(self) -> None:
        txt = """
        load_prices: {'source_node_name at 0x7f571c329b51':
        'RealTimeDataSource object at 0x7f571c329b50
        """
        expected = r"""
        load_prices: {'source_node_name at 0x':
        'RealTimeDataSource object at 0x"""
        self.helper(txt, expected)

    def test3(self) -> None:
        txt = """
        load_prices: {'source_node_name': 'RealTimeDataSource',
        'source_node_kwargs': {'market_data':
        <market_data.market_data.ReplayedMarketData
        object>, 'period': 'last_5mins', 'asset_id_col': 'asset_id',
        'multiindex_output': True}} process_forecasts: {'prediction_col': 'close',
        'execution_mode': 'real_time', 'process_forecasts_config':
        {'market_data':
        <market_data.market_data.ReplayedMarketData
        object at 0x7faff4c3faf0>,'portfolio  ': <oms.portfolio.SimulatedPortfolio
        object>, 'order_type': 'price@twap', 'ath_start_time':
        datetime.time(9, 30), 'trading_start_time': datetime.time(9, 30),
        'ath_end_time': datetime.time(16, 40), 'trading_end_time':
        datetime.time(16, 4  0)}}
        """
        expected = r"""
        load_prices: {'source_node_name': 'RealTimeDataSource',
        'source_node_kwargs': {'market_data':
        <market_data.market_data.ReplayedMarketData
        object>, 'period': 'last_5mins', 'asset_id_col': 'asset_id',
        'multiindex_output': True}} process_forecasts: {'prediction_col': 'close',
        'execution_mode': 'real_time', 'process_forecasts_config':
        {'market_data':
        <market_data.market_data.ReplayedMarketData
        object at 0x>,'portfolio  ': <oms.portfolio.SimulatedPortfolio
        object>, 'order_type': 'price@twap', 'ath_start_time':
        datetime.time(9, 30), 'trading_start_time': datetime.time(9, 30),
        'ath_end_time': datetime.time(16, 40), 'trading_end_time':
        datetime.time(16, 4  0)}}"""
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test replacing wall_clock_time=Timestamp('..., tz='America/New_York'))
        """
        txt = """
        _knowledge_datetime_col_name='timestamp_db' <str> _delay_in_secs='0'
        <int>>, 'bar_duration_in_secs': 300, 'rt_timeout_in_secs_or_time': 900} <dict>,
        _dst_dir=None <NoneType>, _fit_at_beginning=False <bool>,
        _wake_up_timestamp=None <NoneType>, _bar_duration_in_secs=300 <int>,
        _events=[Event(num_it=1, current_time=Timestamp('2000-01-01
        10:05:00-0500', tz='America/New_York'),
        wall_clock_time=Timestamp('2022-08-04 09:29:13.441715-0400',
        tz='America/New_York')), Event(num_it=2,
        current_time=Timestamp('2000-01-01 10:10:00-0500',
        tz='America/New_York'), wall_clock_time=Timestamp('2022-08-04
        09:29:13.892793-0400', tz='America/New_York')), Event(num_it=3,
        current_time=Timestamp('2000-01-01 10:15:00-0500',
        tz='America/New_York'), wall_clock_time=Timestamp('2022-08-04
        09:29:14.131619-0400', tz='America/New_York'))] <list>)
        """
        expected = """
        _knowledge_datetime_col_name='timestamp_db' <str> _delay_in_secs='0'
        <int>>, 'bar_duration_in_secs': 300, 'rt_timeout_in_secs_or_time': 900} <dict>,
        _dst_dir=None <NoneType>, _fit_at_beginning=False <bool>,
        _wake_up_timestamp=None <NoneType>, _bar_duration_in_secs=300 <int>,
        _events=[Event(num_it=1, current_time=Timestamp('2000-01-01
        10:05:00-0500', tz='America/New_York'),
        wall_clock_time=Timestamp('xxx', tz='America/New_York')),
        Event(num_it=2, current_time=Timestamp('2000-01-01 10:10:00-0500',
        tz='America/New_York'), wall_clock_time=Timestamp('xxx',
        tz='America/New_York')), Event(num_it=3,
        current_time=Timestamp('2000-01-01 10:15:00-0500',
        tz='America/New_York'), wall_clock_time=Timestamp('xxx',
        tz='America/New_York'))] <list>)
        """
        txt = " ".join(hprint.dedent(txt).split("\n"))
        expected = " ".join(hprint.dedent(expected).split("\n"))
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_today_date
# #############################################################################


class Test_purify_today_date(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_today_date()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_today_date.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        # Run test.
        actual = huntepur.purify_today_date(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test replacing today's date and time with placeholders.
        """
        today = datetime.date.today()
        today_str = today.strftime("%Y%m%d")
        txt = f"""
        Report generated on {today_str}_103045.
        Next run scheduled at {today_str}_235959.
        """
        expected = """
        Report generated on YYYYMMDD_HHMMSS.
        Next run scheduled at YYYYMMDD_HHMMSS.
        """
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test replacing today's date only with placeholder.
        """
        today = datetime.date.today()
        today_str = today.strftime("%Y%m%d")
        txt = f"""
        Backup completed: {today_str}.
        Last modified: {today_str}.
            """
        expected = """
        Backup completed: YYYYMMDD.
        Last modified: YYYYMMDD.
        """
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test to check that non-date-like numbers are not replaced.
        """
        txt = """
        ID: 20000319_123456
        Code: 20000321
        Reference: 20000320_999999
        """
        expected = """
        ID: 20000319_123456
        Code: 20000321
        Reference: 20000320_999999
        """
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_white_spaces
# #############################################################################


class Test_purify_white_spaces(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_white_spaces()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_white_spaces.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        # Run test.
        actual = huntepur.purify_white_spaces(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing trailing spaces and tabs.
        """
        txt = "Line 1    \nLine 2\t\nLine 3  \t  \n"
        expected = "Line 1\nLine 2\nLine 3\n"
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing trailing spaces and preserving empty lines.
        """
        txt = "Line 1\n\n\nLine 2\n\n\n\nLine 3  "
        expected = "Line 1\n\n\nLine 2\n\n\n\nLine 3"
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing trailing whitespace and preserving leading whitespace.
        """
        txt = "   \n  Line 1\nLine 2\n  Line 3  \n  "
        expected = "   \n  Line 1\nLine 2\n  Line 3\n"
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test preserving intentional whitespace within lines.
        """
        txt = "Line 1    with    spaces\nLine 2\twith\ttabs"
        expected = "Line 1    with    spaces\nLine 2\twith\ttabs\n"
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with single line no trailing spaces.
        """
        txt = "Line with no trailing spaces"
        expected = "Line with no trailing spaces\n"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_parquet_file_names
# #############################################################################


class Test_purify_parquet_file_names(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_parquet_file_names()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_parquet_file_names.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        # Run test.
        actual = huntepur.purify_parquet_file_names(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test purification of Parquet file names with the path.

        The Parquet file names with the
        GUID have to be replaced with the `data.parquet` string.
        """
        txt = """
        s3://some_bucket/root/currency_pair=BTC_USDT/year=2024/month=1/ea5e3faed73941a2901a2128abeac4ca-0.parquet
        s3://some_bucket/root/currency_pair=BTC_USDT/year=2024/month=2/f7a39fefb69b40e0987cec39569df8ed-0.parquet
        """
        expected = """
        s3://some_bucket/root/currency_pair=BTC_USDT/year=2024/month=1/data.parquet
        s3://some_bucket/root/currency_pair=BTC_USDT/year=2024/month=2/data.parquet
        """
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test purification of Parquet file name without the path.
        """
        txt = """
        ffa39fffb69b40e0987cec39569df8ed-0.parquet
        """
        expected = """
        data.parquet
        """
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test with string containing no parquet files.
        """
        txt = "some random text"
        expected = "some random text"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_helpers
# #############################################################################


class Test_purify_helpers(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_helpers()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_helpers.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        # Run test.
        actual = huntepur.purify_helpers(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test replacing helpers references in import statements.
        """
        txt = """
        import helpers_root.helpers.hdbg as hdbg
        from helpers_root.helpers.hprint import dedent
        import helpers_root.config_root.config as config
        """
        expected = """
        import helpers.hdbg as hdbg
        from helpers.hprint import dedent
        import config_root.config as config
        """
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test replacing helpers references in file paths.
        """
        txt = """
        /path/to/helpers/hdbg.py
        /path/to/helpers/hprint.py
        /path/to/config_root/config.py
        """
        expected = """
        /path/to/helpers/hdbg.py
        /path/to/helpers/hprint.py
        /path/to/config_root/config.py
        """
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test replacing helpers references in docstrings and comments.
        """
        txt = """
        import helpers_root.helpers.hdbg
        from /path/to/helpers_root/helpers/hprint import dedent
        import helpers_root.config_root.config
        from /path/to/helpers_root/config_root/config import settings
        """
        expected = """
        import helpers.hdbg
        from /path/to/helpers/hprint import dedent
        import config_root.config
        from /path/to/config_root/config import settings
        """
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test that non-matching patterns are not replaced.
        """
        txt = """
        import other_module
        from other_package import helpers
        import helpers_utils
        path/to/other/helpers/file.py
        """
        expected = """
        import other_module
        from other_package import helpers
        import helpers_utils
        path/to/other/helpers/file.py
        """
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_docker_image_name
# #############################################################################


class Test_purify_docker_image_name(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_docker_image_name()` function.
    """

    def test1(self) -> None:
        """
        Test replacing hex container ID with $CONTAINER_ID placeholder.
        """
        # Prepare inputs.
        txt = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.edb567be pdflatex -output-directory
        """
        # Prepare outputs.
        expected = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.$CONTAINER_ID pdflatex -output-directory
        """
        # Run test.
        actual = huntepur.purify_docker_image_name(txt)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test patterns like `tmp.latex.aarch64.2f590c86.2f590c86`.
        """
        # Prepare inputs.
        txt = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.aarch64.2f590c86.2f590c86 pdflatex -output-directory
        """
        # Prepare outputs.
        expected = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.$ARCH.$CONTAINER_ID pdflatex -output-directory
        """
        # Run test.
        actual = huntepur.purify_docker_image_name(txt)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test the Apple `container` engine executable (instead of `docker`).
        """
        # Prepare inputs.
        txt = r"""
        container run --rm --user $(id -u):$(id -g) --workdir /app --mount type=bind,source=/Users/saggese/src/helpers1,target=/app tmp.latex.arm64.417056b0 pdflatex -output-directory
        """
        # Prepare outputs.
        expected = r"""
        container run --rm --user $(id -u):$(id -g) --workdir /app --mount type=bind,source=/Users/saggese/src/helpers1,target=/app tmp.latex.$ARCH.$CONTAINER_ID pdflatex -output-directory
        """
        # Run test.
        actual = huntepur.purify_docker_image_name(txt)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test4(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        actual = huntepur.purify_docker_image_name(txt)
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        actual = huntepur.purify_docker_image_name(txt)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_purify_docker_cmd
# #############################################################################


class Test_purify_docker_cmd(hunitest.TestCase):
    """
    Test normalization of `docker run` / `container run` commands.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_docker_cmd.

        :param txt: Input docker command to normalize
        :param expected: Expected output
        """
        # Prepare inputs.
        # Run test.
        actual = huntepur.purify_docker_cmd(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Normalize a `docker` command with many `-e` flags on a single line.
        """
        txt = (
            "docker run --rm --user $(id -u):$(id -g) -e AM_CONTAINER_VERSION "
            "-e CSFY_AWS_ACCESS_KEY_ID -e CSFY_AWS_DEFAULT_REGION --workdir "
            "$GIT_ROOT tmp.pandoc_texlive.aarch64.xxxxxxxx foo"
        )
        expected = (
            "$DOCKER_EXECUTABLE run --rm --user $(id -u):$(id -g) -e ... "
            "--workdir $GIT_ROOT tmp.pandoc_texlive.aarch64.xxxxxxxx foo"
        )
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Normalize the Apple `container` engine with `-e` flags wrapped
        across multiple lines, as observed on macOS.
        """
        txt = (
            "container run --rm --user $(id -u):$(id -g)\n"
            "-e AM_GDRIVE_PATH\n"
            "-e AM_TELEGRAM_TOKEN\n"
            "-e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET --workdir /app "
            "tmp.pandoc_texlive.arm64.9a4bae9a foo"
        )
        expected = (
            "$DOCKER_EXECUTABLE run --rm --user $(id -u):$(id -g) -e ... "
            "--workdir /app tmp.pandoc_texlive.arm64.9a4bae9a foo"
        )
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        `docker` and `container` commands with different `-e` var lists
        normalize to the identical string.
        """
        txt_docker = (
            "docker run --rm --user $(id -u):$(id -g) -e AM_CONTAINER_VERSION "
            "-e CSFY_AWS_ACCESS_KEY_ID -e CSFY_AWS_DEFAULT_REGION -e "
            "CSFY_AWS_PROFILE --workdir $GIT_ROOT tmp.foo.xxxxxxxx bar"
        )
        txt_container = (
            "container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH "
            "-e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE --workdir $GIT_ROOT "
            "tmp.foo.xxxxxxxx bar"
        )
        actual_docker = huntepur.purify_docker_cmd(txt_docker)
        actual_container = huntepur.purify_docker_cmd(txt_container)
        self.assert_equal(actual_docker, actual_container)

    def test4(self) -> None:
        """
        Run command without `-e` flags should only get the executable
        normalized.
        """
        txt = (
            "docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT "
            "tmp.foo.xxxxxxxx bar"
        )
        expected = (
            "$DOCKER_EXECUTABLE run --rm --user $(id -u):$(id -g) --workdir "
            "$GIT_ROOT tmp.foo.xxxxxxxx bar"
        )
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Text without a docker/container run command should be unchanged.
        """
        txt = "import helpers.hunit_test as hunitest"
        expected = txt
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        self.helper(txt, expected)


# #############################################################################
# Test_purify_line_number
# #############################################################################


class Test_purify_line_number(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_line_number()` function.
    """

    def test1(self) -> None:
        """
        Test replacing line numbers in file paths with $LINE_NUMBER placeholder.
        """
        # Prepare inputs.
        txt = """
        dag_config (marked_as_used=False, writer=None, val_type=config_root.config.config_.Config):
        in_col_groups (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::286::apply_history_lookback, val_type=list): [('close',), ('volume',)]
        out_col_group (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::286::apply_history_lookback, val_type=tuple): ()
        """
        # Prepare outputs.
        expected = r"""
        dag_config (marked_as_used=False, writer=None, val_type=config_root.config.config_.Config):
        in_col_groups (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::$LINE_NUMBER::apply_history_lookback, val_type=list): [('close',), ('volume',)]
        out_col_group (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::$LINE_NUMBER::apply_history_lookback, val_type=tuple): ()
        """
        # Run test.
        actual = huntepur.purify_line_number(txt)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test with empty string input.
        """
        txt = ""
        expected = ""
        actual = huntepur.purify_line_number(txt)
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test with single character input.
        """
        txt = "a"
        expected = "a"
        actual = huntepur.purify_line_number(txt)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_purify_file_names
# #############################################################################


class Test_purify_file_names(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_file_names()` function.
    """

    def helper(
        self,
        file_names: List[str],
        expected: List[str],
        git_root: str = "/home/user/gitroot",
    ) -> None:
        """
        Helper for testing purify_file_names.

        :param file_names: Input file names to purify
        :param expected: Expected output file names
        :param git_root: Git root to mock
        """
        # Prepare inputs.
        # Run test.
        with umock.patch("helpers.hgit.get_client_root", return_value=git_root):
            actual = huntepur.purify_file_names(file_names)
        # Prepare outputs.
        actual_str = "\n".join(str(path) for path in actual)
        expected_str = "\n".join(str(path) for path in expected)
        # Check outputs.
        self.assert_equal(actual_str, expected_str)

    def test1(self) -> None:
        """
        Test basic file name purification with relative paths.
        """
        # Prepare inputs.
        file_names = [
            "/home/user/gitroot/helpers/test/test_file.py",
            "/home/user/gitroot/amp/helpers/test/test_dbg.py",
        ]
        # Prepare outputs.
        expected = [
            "helpers/test/test_file.py",
            "helpers/test/test_dbg.py",
        ]
        # Run test.
        self.helper(file_names, expected)

    def test2(self) -> None:
        """
        Test file name purification with nested amp references.
        """
        # Prepare inputs.
        file_names = [
            "/home/user/gitroot/amp/helpers/amp/test/test_file.py",
            "/home/user/gitroot/amp/helpers/test/amp/test_dbg.py",
        ]
        # Prepare outputs.
        expected = [
            "helpers/test/test_file.py",
            "helpers/test/test_dbg.py",
        ]
        # Run test.
        self.helper(file_names, expected)

    def test3(self) -> None:
        """
        Test file name purification with app references to ensure that they are
        not replaced.
        """
        # Prepare inputs.
        file_names = [
            "/home/user/gitroot/app/helpers/test/test_file.py",
            "/home/user/gitroot/app/amp/helpers/test/test_dbg.py",
        ]
        # Prepare outputs.
        expected = [
            "app/helpers/test/test_file.py",
            "app/helpers/test/test_dbg.py",
        ]
        # Run test.
        self.helper(file_names, expected)

    def test4(self) -> None:
        """
        Test file name purification with empty list.
        """
        # Prepare inputs.
        file_names = []
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(file_names, expected)


# #############################################################################
# Test_purify_apple_container_output
# #############################################################################


class Test_purify_apple_container_output(hunitest.TestCase):
    """
    Test `hunit_test_purification.purify_apple_container_output()` function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Helper for testing purify_apple_container_output.

        :param txt: Input text to purify
        :param expected: Expected output
        """
        # Prepare inputs.
        # Run test.
        actual = huntepur.purify_apple_container_output(txt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing single container startup line.
        """
        txt = """
        [0/6] [0s]
        dot - graphviz version 12.2.1 (20241206.2353)
        """
        txt = hprint.dedent(txt)
        expected = """
        dot - graphviz version 12.2.1 (20241206.2353)
        """
        expected = hprint.dedent(expected)
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing multiple container startup lines.
        """
        txt = hprint.dedent(r"""
        [0/6] [0s]
        [1/6] Fetching image [0s]
        [2/6] Unpacking image [0s]
        [3/6] Fetching kernel [0s]
        [4/6] Fetching init image [0s]
        [5/6] Unpacking init image [0s]
        [6/6] Starting container [0s]
        [6/6] Starting container [1s]
        dot - graphviz version 12.2.1 (20241206.2353)
        """)
        expected = "dot - graphviz version 12.2.1 (20241206.2353)\n\n"
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test with output that has no container lines.
        """
        txt = "dot - graphviz version 12.2.1 (20241206.2353)\n"
        expected = "dot - graphviz version 12.2.1 (20241206.2353)\n"
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test with empty string.
        """
        txt = ""
        expected = ""
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test with only container startup lines.
        """
        txt = hprint.dedent(r"""
        [0/6] [0s]
        [1/6] Fetching image [0s]
        [2/6] Unpacking image [0s]
        """)
        expected = "\n\n"
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test that lines with brackets but not starting/ending with them are
        kept.
        """
        txt = hprint.dedent(r"""
        [0/6] [0s]
        Some output with [brackets] in the middle
        dot - graphviz version 12.2.1 (20241206.2353)
        """)
        expected = hprint.dedent(r"""
        Some output with [brackets] in the middle
        dot - graphviz version 12.2.1 (20241206.2353)
        """)
        self.helper(txt, expected)
