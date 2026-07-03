"""
Import as:

import helpers.test.test_hunit_test_purification as thuntepur
"""

import datetime
import logging
import os
import unittest.mock as umock
from typing import Any, List

import pytest

import helpers.hgit as hgit
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_purification as huntepur
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_purify_text1
# #############################################################################


class Test_purify_text1(hunitest.TestCase):
    def helper(self, txt: str, expected: str, **kwargs: Any) -> None:
        actual = huntepur.purify_txt_from_client(txt)
        self.assert_equal(actual, expected, **kwargs)

    def test1(self) -> None:
        txt = "amp/helpers/test/test_system_interaction.py"
        expected = "helpers/test/test_system_interaction.py"
        self.helper(txt, expected)

    def test2(self) -> None:
        txt = "amp/helpers/test/test_system_interaction.py"
        expected = "helpers/test/test_system_interaction.py"
        self.helper(txt, expected)

    def test3(self) -> None:
        txt = "['amp/helpers/test/test_system_interaction.py']"
        expected = "['helpers/test/test_system_interaction.py']"
        self.helper(txt, expected)

    def test4(self) -> None:
        txt = "app.helpers.test.test_system_interaction.py"
        expected = "helpers.test.test_system_interaction.py"
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test that longer paths are processed before shorter ones.
        """
        txt = "/home/user/project/src/file.py"
        with (
            umock.patch("helpers.hgit.get_client_root") as mock_git_root,
            umock.patch("os.getcwd") as mock_pwd,
        ):
            mock_git_root.return_value = "/home/user/project"
            mock_pwd.return_value = "/home/user"
            expected = "$GIT_ROOT/src/file.py"
            self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test that paths with multiple occurrences of the same pattern are
        processed correctly.
        """
        txt = "/home/user/project/src/project/file.py"
        with (
            umock.patch("helpers.hgit.get_client_root") as mock_git_root,
            umock.patch("os.getcwd") as mock_pwd,
        ):
            mock_git_root.return_value = "/home/user/project"
            mock_pwd.return_value = "/home/user"
            expected = "$GIT_ROOT/src/project/file.py"
            self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test that paths with multiple patterns are processed in the correct
        order.
        """
        txt = "/home/user/project/src/project/file.py"
        with (
            umock.patch("helpers.hgit.get_client_root") as mock_git_root,
            umock.patch("os.getcwd") as mock_pwd,
        ):
            mock_git_root.return_value = "/home/user/project"
            mock_pwd.return_value = "/home/user/project/src"
            expected = "$GIT_ROOT/src/project/file.py"
            self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test that paths with no matching patterns are left unchanged.
        """
        txt = "/home/user/other/file.py"
        with (
            umock.patch("helpers.hgit.get_client_root") as mock_git_root,
            umock.patch("os.getcwd") as mock_pwd,
        ):
            mock_git_root.return_value = "/home/user/project"
            mock_pwd.return_value = "/home/user/project/src"
            expected = "/home/user/other/file.py"
            self.helper(txt, expected)

    def test9(self) -> None:
        super_module_path = hgit.get_client_root(super_module=True)
        # TODO(gp): We should remove the current path.
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
        # pylint: enable=line-too-long
        self.helper(txt, expected, dedent=True)

    def test10(self) -> None:
        """
        Test case when client root path is equal to `/`
        """
        # pylint: disable=redefined-outer-name
        hgit = umock.Mock()
        hgit.get_client_root.return_value = "/"
        txt = "/tmp/subdir1"
        expected = txt
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
            " tmp.latex.aarch64.xxxxxxxx"
            " pdflatex -output-directory"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch"
            " --interaction=nonstopmode --halt-on-error --shell-escape"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.tex"
        )
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_purify_directory_paths1
# #############################################################################


class Test_purify_directory_paths1(hunitest.TestCase):
    def helper(self, input_: str, expected: str) -> None:
        actual = huntepur.purify_directory_paths(input_)
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test the replacement of `GIT_ROOT`.
        """
        with (
            umock.patch(
                "helpers.hgit.get_client_root", return_value="/home/user/gitroot"
            ),
            umock.patch.dict(
                "os.environ",
                {"CSFY_HOST_GIT_ROOT_PATH": "/home/user/csfy_host_git_root"},
                clear=True,
            ),
            umock.patch("os.getcwd", return_value="/home/user"),
        ):
            input_ = "/home/user/gitroot/src/subdir/file.py"
            expected = "$GIT_ROOT/src/subdir/file.py"
            self.helper(input_, expected)

    def test2(self) -> None:
        """
        Test the replacement of `CSFY_HOST_GIT_ROOT_PATH`.
        """
        with (
            umock.patch(
                "helpers.hgit.get_client_root", return_value="/home/user/gitroot"
            ),
            umock.patch.dict(
                "os.environ",
                {"CSFY_HOST_GIT_ROOT_PATH": "/home/user/csfy_host_git_root"},
                clear=True,
            ),
            umock.patch("os.getcwd", return_value="/home/user"),
        ):
            input_ = "/home/user/csfy_host_git_root/other/file.py"
            expected = "$CSFY_HOST_GIT_ROOT_PATH/other/file.py"
            self.helper(input_, expected)

    def test3(self) -> None:
        """
        Test the replacement of `PWD`.
        """
        with (
            umock.patch(
                "helpers.hgit.get_client_root", return_value="/home/user/gitroot"
            ),
            umock.patch.dict(
                "os.environ",
                {"CSFY_HOST_GIT_ROOT_PATH": "/home/user/csfy_host_git_root"},
                clear=True,
            ),
            umock.patch("os.getcwd", return_value="/home/user"),
        ):
            input_ = "/home/user/documents/file.py"
            expected = "$PWD/documents/file.py"
            self.helper(input_, expected)

    def test4(self) -> None:
        """
        Test the replacement when `GIT_ROOT`, `CSFY_HOST_GIT_ROOT_PATH` and
        current working directory are the same.
        """
        with (
            umock.patch(
                "helpers.hgit.get_client_root", return_value="/home/user"
            ),
            umock.patch.dict(
                "os.environ",
                {"CSFY_HOST_GIT_ROOT_PATH": "/home/user"},
                clear=True,
            ),
            umock.patch("os.getcwd", return_value="/home/user"),
        ):
            input_ = "/home/user/file.py"
            expected = "$GIT_ROOT/file.py"
            self.helper(input_, expected)


# #############################################################################
# Test_purify_from_environment1
# #############################################################################


class Test_purify_from_environment1(hunitest.TestCase):
    def helper(self, input_: str, expected: str) -> None:
        try:
            # Manually set a user name to test the behaviour.
            hsystem.set_user_name("root")
            # Run.
            actual = huntepur.purify_from_environment(input_)
            self.assert_equal(actual, expected, fuzzy_match=True)
        finally:
            # Reset the global user name variable regardless of a test results.
            hsystem.set_user_name(None)

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


# #############################################################################
# Test_purify_amp_reference1
# #############################################################################


class Test_purify_amp_reference1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        txt = hprint.dedent(txt)
        actual = huntepur.purify_amp_references(txt)
        expected = hprint.dedent(expected)
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


# #############################################################################
# Test_purify_app_references1
# #############################################################################


class Test_purify_app_references1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        actual = huntepur.purify_app_references(txt)
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
        env_var_value = os.environ[env_var]
        input_ = f"s3://{env_var_value}/"
        actual = huntepur.purify_from_env_vars(input_)
        expected = f"s3://${env_var}/"
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


# TODO(gp): HelpersTask1
#    @pytest.mark.skipif(
#        not hrecouti.get_repo_config().get_name() == "//cmamp",
#        reason="Run only in //cmamp",
#    )
#    def test_end_to_end(self) -> None:
#        """
#        - Multiple env vars.
#        """
#        #am_aws_s3_bucket = os.environ["AM_AWS_S3_BUCKET"]
#        csfy_aws_s3_bucket = os.environ["CSFY_AWS_S3_BUCKET"]
#        #
#        text = f"""
#        $AM_AWS_S3_BUCKET = {am_aws_s3_bucket}
#        $CSFY_AWS_S3_BUCKET = {csfy_aws_s3_bucket}
#        """
#        #
#        actual = huntepur.purify_from_env_vars(text)
#        self.check_string(actual, fuzzy_match=True)


# #############################################################################
# Test_purify_object_representation1
# #############################################################################


class Test_purify_object_representation1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        txt = hprint.dedent(txt)
        actual = huntepur.purify_object_representation(txt)
        expected = hprint.dedent(expected)
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


# #############################################################################
# Test_purify_today_date1
# #############################################################################


class Test_purify_today_date1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        actual = huntepur.purify_today_date(txt)
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


# #############################################################################
# Test_purify_white_spaces1
# #############################################################################


class Test_purify_white_spaces1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        actual = huntepur.purify_white_spaces(txt)
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


# #############################################################################
# Test_purify_parquet_file_names1
# #############################################################################


class Test_purify_parquet_file_names1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        actual = huntepur.purify_parquet_file_names(txt)
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


# #############################################################################
# Test_purify_helpers1
# #############################################################################


class Test_purify_helpers1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        actual = huntepur.purify_helpers(txt)
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


# #############################################################################
# Test_purify_docker_image_name1
# #############################################################################


class Test_purify_docker_image_name1(hunitest.TestCase):
    def test1(self) -> None:
        txt = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.edb567be pdflatex -output-directory
        """
        expected = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.xxxxxxxx pdflatex -output-directory
        """
        actual = huntepur.purify_docker_image_name(txt)
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test patterns like `tmp.latex.aarch64.2f590c86.2f590c86`.
        """
        txt = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.aarch64.2f590c86.2f590c86 pdflatex -output-directory
        """
        expected = r"""
        docker run --rm --user $(id -u):$(id -g) --workdir $GIT_ROOT --mount type=bind,source=/Users/saggese/src/helpers1,target=$GIT_ROOT tmp.latex.aarch64.xxxxxxxx pdflatex -output-directory
        """
        actual = huntepur.purify_docker_image_name(txt)
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test the Apple `container` engine executable (instead of `docker`).
        """
        txt = r"""
        container run --rm --user $(id -u):$(id -g) --workdir /app --mount type=bind,source=/Users/saggese/src/helpers1,target=/app tmp.latex.arm64.417056b0 pdflatex -output-directory
        """
        expected = r"""
        container run --rm --user $(id -u):$(id -g) --workdir /app --mount type=bind,source=/Users/saggese/src/helpers1,target=/app tmp.latex.arm64.xxxxxxxx pdflatex -output-directory
        """
        actual = huntepur.purify_docker_image_name(txt)
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_purify_docker_cmd1
# #############################################################################


class Test_purify_docker_cmd1(hunitest.TestCase):
    """
    Test normalization of `docker run` / `container run` commands.
    """

    def helper(self, txt: str, expected: str) -> None:
        actual = huntepur.purify_docker_cmd(txt)
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


# #############################################################################
# Test_purify_line_number1
# #############################################################################


class Test_purify_line_number1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check that the text is purified from line numbers correctly.
        """
        txt = """
        dag_config (marked_as_used=False, writer=None, val_type=config_root.config.config_.Config):
        in_col_groups (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::286::apply_history_lookback, val_type=list): [('close',), ('volume',)]
        out_col_group (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::286::apply_history_lookback, val_type=tuple): ()
        """
        expected = r"""
        dag_config (marked_as_used=False, writer=None, val_type=config_root.config.config_.Config):
        in_col_groups (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::$LINE_NUMBER::apply_history_lookback, val_type=list): [('close',), ('volume',)]
        out_col_group (marked_as_used=True, writer=$GIT_ROOT/dataflow/system/system_builder_utils.py::$LINE_NUMBER::apply_history_lookback, val_type=tuple): ()
        """
        actual = huntepur.purify_line_number(txt)
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_purify_file_names1
# #############################################################################


class Test_purify_file_names1(hunitest.TestCase):
    def helper(self, file_names: List[str], expected: List[str]) -> None:
        actual = huntepur.purify_file_names(file_names)
        actual = "\n".join(str(path) for path in actual)
        expected = "\n".join(str(path) for path in expected)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test basic file name purification with relative paths.
        """
        with umock.patch(
            "helpers.hgit.get_client_root", return_value="/home/user/gitroot"
        ):
            txt = [
                "/home/user/gitroot/helpers/test/test_file.py",
                "/home/user/gitroot/amp/helpers/test/test_dbg.py",
            ]
            expected = [
                "helpers/test/test_file.py",
                "helpers/test/test_dbg.py",
            ]
            self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test file name purification with nested amp references.
        """
        with umock.patch(
            "helpers.hgit.get_client_root", return_value="/home/user/gitroot"
        ):
            txt = [
                "/home/user/gitroot/amp/helpers/amp/test/test_file.py",
                "/home/user/gitroot/amp/helpers/test/amp/test_dbg.py",
            ]
            expected = [
                "helpers/test/test_file.py",
                "helpers/test/test_dbg.py",
            ]
            self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test file name purification with app references to ensure that they are
        not replaced.
        """
        with umock.patch(
            "helpers.hgit.get_client_root", return_value="/home/user/gitroot"
        ):
            txt = [
                "/home/user/gitroot/app/helpers/test/test_file.py",
                "/home/user/gitroot/app/amp/helpers/test/test_dbg.py",
            ]
            expected = [
                "app/helpers/test/test_file.py",
                "app/helpers/test/test_dbg.py",
            ]
            self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test file name purification with empty list.
        """
        with umock.patch(
            "helpers.hgit.get_client_root", return_value="/home/user/gitroot"
        ):
            txt = []
            expected = []
            self.helper(txt, expected)


# #############################################################################
# Test_purify_apple_container_output1
# #############################################################################


class Test_purify_apple_container_output1(hunitest.TestCase):

    def helper(self, txt: str, expected: str) -> None:
        actual = huntepur.purify_apple_container_output(txt)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing single container startup line.
        """
        # TODO(ai_gp): Use variables like
        # txt = """
        # ...
        # txt = hprint.dedent(txt)
        txt = "[0/6] [0s]\ndot - graphviz version 12.2.1 (20241206.2353)\n"
        expected = "dot - graphviz version 12.2.1 (20241206.2353)\n\n"
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing multiple container startup lines.
        """
        txt = (
            "[0/6] [0s]\n"
            "[1/6] Fetching image [0s]\n"
            "[2/6] Unpacking image [0s]\n"
            "[3/6] Fetching kernel [0s]\n"
            "[4/6] Fetching init image [0s]\n"
            "[5/6] Unpacking init image [0s]\n"
            "[6/6] Starting container [0s]\n"
            "[6/6] Starting container [1s]\n"
            "dot - graphviz version 12.2.1 (20241206.2353)\n"
        )
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
        txt = (
            "[0/6] [0s]\n"
            "[1/6] Fetching image [0s]\n"
            "[2/6] Unpacking image [0s]\n"
        )
        expected = "\n\n"
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test that lines with brackets but not starting/ending with them are
        kept.
        """
        txt = (
            "[0/6] [0s]\n"
            "Some output with [brackets] in the middle\n"
            "dot - graphviz version 12.2.1 (20241206.2353)\n"
        )
        expected = (
            "Some output with [brackets] in the middle\n"
            "dot - graphviz version 12.2.1 (20241206.2353)\n"
        )
        self.helper(txt, expected)
