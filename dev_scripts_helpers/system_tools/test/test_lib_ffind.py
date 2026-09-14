# TODO(ai_gp): Add 'import logging' before other imports per template
# (testing.rules.md:## Unit Test Code Structure)
from typing import Any, Dict, List, Optional, Type

import dev_scripts_helpers.system_tools.lib_ffind as dshstliff
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

# TODO(ai_gp): Add '_LOG = logging.getLogger(__name__)' after imports
# per template (testing.rules.md:## Unit Test Code Structure)
_FIND_PRUNE = (
    r"\( -path './.git' -o -path './.ipynb_checkpoints' -o -path "
    r"./.mypy_cache \) -prune -o"
)


# #############################################################################
# TestFfindScript
# #############################################################################


# TODO(ai_gp): Rename test class to Test_main to match function being
# tested (testing.rules.md:## Naming Conventions for a Function)
class TestFfindScript(hunitest.TestCase):
    # TODO(ai_gp): Update docstring to reference 'lib_ffind.main()'
    # function being tested per naming conventions
    # (testing.rules.md:## Test Class Documentation)
    """
    Test `ffind` script functionality through `lib_ffind` module integration.
    """

    def _assert_cmd_invocation(
        self,
        sys_calls: List[Dict[str, Any]],
        expected_cmd: str,
    ) -> None:
        """
        Assert that the captured system calls match the expected command.

        :param sys_calls: captured system calls
        :param expected_cmd: expected command string
        """
        self.assertEqual(len(sys_calls), 1, "Expected exactly one call")
        # TODO(ai_gp): Use self.assert_equal() when comparing strings instead of
        # self.assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(
            sys_calls[0]["function"],
            "hsystem.system",
            "Expected hsystem.system call",
        )
        actual_cmd = sys_calls[0]["args"][0]
        # TODO(ai_gp): Use self.assert_equal() when comparing strings instead of
        # self.assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual_cmd, expected_cmd)

    def helper(
        self,
        args: List[str],
        expected_cmd: str,
        expected_exit_code: Optional[int],
        *,
        side_effect: Optional[Type[Exception]] = None,
    ) -> None:
        """
        Test helper for `ffind` main function.

        :param args: arguments to pass to `lib_ffind.main()`
        :param expected_cmd: expected command string or "" to skip command
            verification
        :param expected_exit_code: expected exit code or None to skip exit
            code verification
        :param side_effect: exception to raise from `hsystem.system()`
        """
        # Run test.
        with hunteuti.capture_sys_calls(side_effect=side_effect) as sys_calls:
            try:
                exit_code = dshstliff.main(args)
            except SystemExit as e:
                exit_code = e.code
        # TODO(ai_gp): Use assert_sys_calls extending it if needed to also
        # check exit code
        # Check command output.
        if expected_cmd != "":
            self._assert_cmd_invocation(sys_calls, expected_cmd)
        # Check exit code.
        if expected_exit_code is not None:
            self.assertEqual(exit_code, expected_exit_code)

    def test1(self) -> None:
        """
        Test search for a pattern in the current directory.
        """
        # Prepare inputs.
        args = ["Task243"]
        # Prepare outputs.
        expected_cmd = (
            f'find . {_FIND_PRUNE} -iname "*Task243*" -print '
            "| grep -v __pycache__ | sort"
        )
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test2(self) -> None:
        """
        Test search for a pattern in a directory selected with `--dir`.
        """
        # Prepare inputs: `helpers` is a real dir relative to cwd.
        args = ["stocktwits", "--dir", "helpers"]
        # Prepare outputs.
        expected_cmd = (
            f'find helpers {_FIND_PRUNE} -iname "*stocktwits*" -print '
            "| grep -v __pycache__ | sort"
        )
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test3(self) -> None:
        """
        Test filter by file extension using the second positional argument.
        """
        # Prepare inputs: `helpers` is a real dir relative to cwd.
        args = ["stocktwits", ".py", "--dir", "helpers"]
        # Prepare outputs.
        expected_cmd = (
            f'find helpers {_FIND_PRUNE} -iname "*stocktwits*.py" -print '
            "| grep -v __pycache__ | sort"
        )
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test4(self) -> None:
        """
        Test the `--only_files` flag.
        """
        # Prepare inputs.
        args = ["stocktwits", "--only_files"]
        # Prepare outputs.
        expected_cmd = (
            f'find . {_FIND_PRUNE} -type f -iname "*stocktwits*" -print '
            "| grep -v __pycache__ | sort"
        )
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test5(self) -> None:
        """
        Test no arguments returns a usage error.
        """
        # Prepare inputs.
        args: List[str] = []
        expected_cmd = ""
        expected_exit_code = -1
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test6(self) -> None:
        """
        Test too many positional arguments returns a usage error.
        """
        # Prepare inputs.
        args = ["stocktwits", ".py", "extra"]
        expected_cmd = ""
        expected_exit_code = -1
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test7(self) -> None:
        """
        Test --help flag.
        """
        # Prepare inputs.
        args = ["--help"]
        expected_cmd = ""
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test8(self) -> None:
        """
        Test that a non-existent `--dir` raises an assertion error.
        """
        # Prepare inputs.
        args = ["stocktwits", "--dir", "/nonexistent_dir_xyz"]
        # Run test and expect assertion error.
        with self.assertRaises(AssertionError):
            dshstliff.main(args)
