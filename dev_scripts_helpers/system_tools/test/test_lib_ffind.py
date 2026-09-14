import logging
# Trivial edit.
from typing import List, Optional, Type

import dev_scripts_helpers.system_tools.lib_ffind as dshstliff
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

_LOG = logging.getLogger(__name__)

# `find` expression to prune dirs that should not be searched.
_FIND_PRUNE = (
    r"\( -path './.git' -o -path './.ipynb_checkpoints' -o -path "
    r"./.mypy_cache \) -prune -o"
)


# #############################################################################
# Test_main
# #############################################################################


class Test_main(hunitest.TestCase):
    """
    Test `lib_ffind.main()` function.
    """

    # pylint: disable=too-many-public-methods

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
        # Check command output.
        if expected_cmd != "":
            expected_sys_calls = [
                {
                    "function": "hsystem.system",
                    "args": (expected_cmd,),
                    "kwargs": {"suppress_output": False, "abort_on_error": False},
                }
            ]
            expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)
            hunteuti.assert_sys_calls(self, sys_calls, expected_str)
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
