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
    def test1(self) -> None:
        """
        Test the defaults when no argument is passed.
        """
        # Prepare inputs.
        parser = dshstseut.add_search_args(argparse.ArgumentParser())
        # Run test.
        parsed = parser.parse_args([])
        # Check outputs.
        self.assertEqual(parsed.positional, [])
        self.assertEqual(parsed.dir, "")
        self.assertFalse(parsed.dry_run)

    def test2(self) -> None:
        """
        Test all the arguments are parsed.
        """
        # Prepare inputs.
        parser = dshstseut.add_search_args(argparse.ArgumentParser())
        # Run test.
        parsed = parser.parse_args(
            ["notebook", ".", "py", "--dir", "src", "--dry_run"]
        )
        # Check outputs.
        self.assertEqual(parsed.positional, ["notebook", ".", "py"])
        self.assertEqual(parsed.dir, "src")
        self.assertTrue(parsed.dry_run)


# #############################################################################
# Test_parse_extensions
# #############################################################################


class Test_parse_extensions(hunitest.TestCase):
    def helper(self, ext_str: str, expected: List[str]) -> None:
        # Run test.
        actual = dshstseut.parse_extensions(ext_str)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test a single extension.
        """
        self.helper("py", ["py"])

    def test2(self) -> None:
        """
        Test a comma-separated list, stripping whitespace.
        """
        self.helper("py, ipynb ,md", ["py", "ipynb", "md"])

    def test3(self) -> None:
        """
        Test that an extension starting with dot raises an assertion error.
        """
        with self.assertRaises(AssertionError):
            dshstseut.parse_extensions(".py")

    def test4(self) -> None:
        """
        Test that an empty extension in the list raises an assertion error.
        """
        with self.assertRaises(AssertionError):
            dshstseut.parse_extensions("py,")


# #############################################################################
# Test_parse_positional
# #############################################################################


class Test_parse_positional(hunitest.TestCase):
    def helper(
        self,
        positional: List[str],
        dir_flag: str,
        expected: Tuple[str, str, List[str]],
        *,
        has_pattern: bool = True,
    ) -> None:
        # Run test.
        actual = dshstseut.parse_positional(
            positional, dir_flag, has_pattern=has_pattern
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that only the pattern is passed.
        """
        self.helper(["notebook"], "", ("notebook", ".", []))

    def test2(self) -> None:
        """
        Test that pattern and directory are passed.
        """
        self.helper(["notebook", "src"], "", ("notebook", "src", []))

    def test3(self) -> None:
        """
        Test that pattern, directory, and extensions are passed.
        """
        self.helper(
            ["notebook", ".", "py,md"], "", ("notebook", ".", ["py", "md"])
        )

    def test4(self) -> None:
        """
        Test that the directory is passed with `--dir`.
        """
        self.helper(["notebook"], "src", ("notebook", "src", []))

    def test5(self) -> None:
        """
        Test that no argument is passed.
        """
        self.helper([], "", ("", ".", []))

    def test6(self) -> None:
        """
        Test the mode without pattern, where arguments start from `<dir>`.
        """
        self.helper(["src", "py"], "", ("", "src", ["py"]), has_pattern=False)

    def test7(self) -> None:
        """
        Test that the directory in both positional arg and `--dir` fails.
        """
        with self.assertRaises(AssertionError):
            dshstseut.parse_positional(["notebook", "."], "src")

    def test8(self) -> None:
        """
        Test that too many positional arguments raise an assertion error.
        """
        with self.assertRaises(AssertionError):
            dshstseut.parse_positional(["notebook", ".", "py", "extra"], "")
