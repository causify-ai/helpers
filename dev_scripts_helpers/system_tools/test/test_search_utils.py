import argparse
import logging
from typing import List, Tuple

import dev_scripts_helpers.system_tools.search_utils as dshstseut
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_add_search_args
# #############################################################################


class Test_add_search_args(hunitest.TestCase):
    """
    Test `dev_scripts_helpers.system_tools.search_utils.add_search_args()` function.
    """

    def helper(
        self,
        args: List[str],
        expected_positional: List[str],
        expected_dir: str,
        expected_dry_run: bool,
    ) -> None:
        """
        Test helper for add_search_args.

        :param args: Command-line arguments to parse
        :param expected_positional: Expected positional arguments
        :param expected_dir: Expected directory flag value
        :param expected_dry_run: Expected dry_run flag value
        """
        # Run test.
        parser = dshstseut.add_search_args(argparse.ArgumentParser())
        parsed = parser.parse_args(args)
        # Check outputs.
        # TODO(ai_gp): Create a string and then compare it with assert_equal.
        self.assert_equal(str(parsed.positional), str(expected_positional))
        self.assert_equal(parsed.dir, expected_dir)
        self.assertEqual(parsed.dry_run, expected_dry_run)

    def test1(self) -> None:
        """
        Test the defaults when no argument is passed.
        """
        # Prepare inputs.
        args = []
        # Prepare outputs.
        expected_positional = []
        expected_dir = ""
        expected_dry_run = False
        # Run test.
        self.helper(args, expected_positional, expected_dir, expected_dry_run)

    def test2(self) -> None:
        """
        Test all the arguments are parsed.
        """
        # Prepare inputs.
        args = ["notebook", ".", "py", "--dir", "src", "--dry_run"]
        # Prepare outputs.
        expected_positional = ["notebook", ".", "py"]
        expected_dir = "src"
        expected_dry_run = True
        # Run test.
        self.helper(args, expected_positional, expected_dir, expected_dry_run)


# #############################################################################
# Test_parse_extensions
# #############################################################################


class Test_parse_extensions(hunitest.TestCase):
    """
    Test `dev_scripts_helpers.system_tools.search_utils.parse_extensions()` function.
    """

    def helper(self, ext_str: str, expected: List[str]) -> None:
        """
        Test helper for parse_extensions.

        :param ext_str: Extension string to parse
        :param expected: Expected list of extensions
        """
        # Run test.
        actual = dshstseut.parse_extensions(ext_str)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test a single extension.
        """
        # Prepare inputs.
        ext_str = "py"
        # Prepare outputs.
        expected = ["py"]
        # Run test.
        self.helper(ext_str, expected)

    def test2(self) -> None:
        """
        Test a comma-separated list, stripping whitespace.
        """
        # Prepare inputs.
        ext_str = "py, ipynb ,md"
        # Prepare outputs.
        expected = ["py", "ipynb", "md"]
        # Run test.
        self.helper(ext_str, expected)



# #############################################################################
# Test_parse_positional
# #############################################################################


class Test_parse_positional(hunitest.TestCase):
    """
    Test `dev_scripts_helpers.system_tools.search_utils.parse_positional()` function.
    """

    def helper(
        self,
        positional: List[str],
        dir_flag: str,
        expected: Tuple[str, str, List[str]],
        *,
        has_pattern: bool = True,
    ) -> None:
        """
        Test helper for parse_positional.

        :param positional: Positional arguments to parse
        :param dir_flag: Directory flag value
        :param expected: Expected output tuple (pattern, directory, extensions)
        :param has_pattern: Whether the positional args include a pattern
        """
        # Run test.
        actual = dshstseut.parse_positional(
            positional, dir_flag, has_pattern=has_pattern
        )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that only the pattern is passed.
        """
        # Prepare inputs.
        positional = ["notebook"]
        dir_flag = ""
        # Prepare outputs.
        expected = ("notebook", ".", [])
        # Run test.
        self.helper(positional, dir_flag, expected)

    def test2(self) -> None:
        """
        Test that pattern and directory are passed.
        """
        # Prepare inputs.
        positional = ["notebook", "src"]
        dir_flag = ""
        # Prepare outputs.
        expected = ("notebook", "src", [])
        # Run test.
        self.helper(positional, dir_flag, expected)

    def test3(self) -> None:
        """
        Test that pattern, directory, and extensions are passed.
        """
        # Prepare inputs.
        positional = ["notebook", ".", "py,md"]
        dir_flag = ""
        # Prepare outputs.
        expected = ("notebook", ".", ["py", "md"])
        # Run test.
        self.helper(positional, dir_flag, expected)

    def test4(self) -> None:
        """
        Test that the directory is passed with `--dir`.
        """
        # Prepare inputs.
        positional = ["notebook"]
        dir_flag = "src"
        # Prepare outputs.
        expected = ("notebook", "src", [])
        # Run test.
        self.helper(positional, dir_flag, expected)

    def test5(self) -> None:
        """
        Test that no argument is passed.
        """
        # Prepare inputs.
        positional = []
        dir_flag = ""
        # Prepare outputs.
        expected = ("", ".", [])
        # Run test.
        self.helper(positional, dir_flag, expected)

    def test6(self) -> None:
        """
        Test the mode without pattern, where arguments start from `<dir>`.
        """
        # Prepare inputs.
        positional = ["src", "py"]
        dir_flag = ""
        has_pattern = False
        # Prepare outputs.
        expected = ("", "src", ["py"])
        # Run test.
        self.helper(positional, dir_flag, expected, has_pattern=has_pattern)

