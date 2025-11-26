import logging
import pprint
from typing import List

import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_printing1
# #############################################################################


class Test_printing1(hunitest.TestCase):
    def test_color_highlight1(self) -> None:
        for c in hprint._COLOR_MAP:
            _LOG.debug(hprint.color_highlight(c, c))


# #############################################################################
# Test_to_str1
# #############################################################################


class Test_to_str1(hunitest.TestCase):
    def test1(self) -> None:
        x = 1
        # To disable linter complaints.
        _ = x
        actual = hprint.to_str("x")
        expected = "x=1"
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        x = "hello world"
        # To disable linter complaints.
        _ = x
        actual = hprint.to_str("x")
        expected = "x='hello world'"
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        x = 2
        # To disable linter complaints.
        _ = x
        actual = hprint.to_str("x*2")
        expected = "x*2=4"
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test printing multiple values separated by space.
        """
        x = 1
        y = "hello"
        # To disable linter complaints.
        _ = x, y
        actual = hprint.to_str("x y")
        expected = "x=1, y='hello'"
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test printing multiple strings separated by space.
        """
        x = "1"
        y = "hello"
        # To disable linter complaints.
        _ = x, y
        actual = hprint.to_str("x y")
        expected = "x='1', y='hello'"
        self.assertEqual(actual, expected)

    def test6(self) -> None:
        """
        Test printing a list.
        """
        x = [1, "hello", "world"]
        # To disable linter complaints.
        _ = x
        actual = hprint.to_str("x")
        expected = "x=[1, 'hello', 'world']"
        self.assertEqual(actual, expected)


# #############################################################################


def example_func1(x: int, y: str) -> str:
    _ = x, y
    ret = hprint.func_signature_to_str()
    return ret  # type: ignore[no-any-return]


def example_func2() -> str:
    ret = hprint.func_signature_to_str()
    return ret  # type: ignore[no-any-return]


def example_func3(x: int, y: str) -> str:
    _ = x, y
    ret = hprint.func_signature_to_str("y")
    return ret  # type: ignore[no-any-return]


def example_func4(x: int, y: str, z: float) -> str:
    _ = x, y, z
    ret = hprint.func_signature_to_str("x z")
    return ret  # type: ignore[no-any-return]


def example_func5(x: int, y: str, z: float) -> str:
    _ = x, y, z
    ret = hprint.func_signature_to_str(["y", "z"])
    return ret  # type: ignore[no-any-return]


# #############################################################################
# Test_func_signature_to_str1
# #############################################################################


class Test_func_signature_to_str1(hunitest.TestCase):
    def test1(self) -> None:
        actual = example_func1(1, "hello")
        expected = "# example_func1: x=1, y='hello'"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        actual = example_func2()
        expected = "# example_func2:"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        actual = example_func3(1, "hello")
        expected = "# example_func3: x=1"
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        actual = example_func4(1, "hello", 3.14)
        expected = "# example_func4: y='hello'"
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        actual = example_func5(1, "hello", 3.14)
        expected = "# example_func5: x=1"
        self.assert_equal(actual, expected)


# #############################################################################
# Test_log
# #############################################################################


class Test_log(hunitest.TestCase):
    def test2(self) -> None:
        x = 1
        # To disable linter complaints.
        _ = x
        for verb in [logging.DEBUG, logging.INFO]:
            hprint.log(_LOG, verb, "x")

    def test3(self) -> None:
        x = 1
        y = "hello"
        # To disable linter complaints.
        _ = x, y
        for verb in [logging.DEBUG, logging.INFO]:
            hprint.log(_LOG, verb, "x y")

    def test4(self) -> None:
        """
        The command:

        > pytest -k Test_log::test4  -o log_cli=true --dbg_verbosity DEBUG

        should print something like:

        DEBUG    test_printing:printing.py:315 x=1, y='hello', z=['cruel', 'world']
        INFO     test_printing:printing.py:315 x=1, y='hello', z=['cruel', 'world']
        """
        x = 1
        y = "hello"
        z = ["cruel", "world"]
        # To disable linter complaints.
        _ = x, y, z
        for verb in [logging.DEBUG, logging.INFO]:
            hprint.log(_LOG, verb, "x y z")


# #############################################################################
# Test_sort_dictionary
# #############################################################################


class Test_sort_dictionary(hunitest.TestCase):
    def test1(self) -> None:
        dict_ = {
            "tool": {
                "poetry": {
                    "name": "lm",
                    "version": "0.1.0",
                    "description": "",
                    "authors": [""],
                    "dependencies": {
                        "awscli": "*",
                        "boto3": "*",
                        "flaky": "*",
                        "fsspec": "*",
                        "gluonts": "*",
                        "invoke": "*",
                        "jupyter": "*",
                        "matplotlib": "*",
                        "mxnet": "*",
                        "networkx": "*",
                        "pandas": "^1.1.0",
                        "psycopg2": "*",
                        "pyarrow": "*",
                        "pytest": "^6.0.0",
                        "pytest-cov": "*",
                        "pytest-instafail": "*",
                        "pytest-xdist": "*",
                        "python": "^3.7",
                        "pywavelets": "*",
                        "s3fs": "*",
                        "seaborn": "*",
                        "sklearn": "*",
                        "statsmodels": "*",
                        "bs4": "*",
                        "jsonpickle": "*",
                        "lxml": "*",
                        "tqdm": "*",
                        "requests": "*",
                    },
                    "dev-dependencies": {},
                }
            },
            "build-system": {
                "requires": ["poetry>=0.12"],
                "build-backend": "poetry.masonry.api",
            },
        }
        actual = hprint.sort_dictionary(dict_)
        self.check_string(pprint.pformat(actual))


# #############################################################################
# Test_indent1
# #############################################################################


class Test_indent1(hunitest.TestCase):
    def test1(self) -> None:
        txt = """foo

klass TestHelloWorld(hunitest.TestCase):
    bar
"""
        num_spaces = 2
        actual = hprint.indent(txt, num_spaces=num_spaces)
        expected = """  foo

  klass TestHelloWorld(hunitest.TestCase):
      bar
"""
        self.assert_equal(actual, expected, fuzzy_match=False)


# #############################################################################
# Test_dedent1
# #############################################################################


class Test_dedent1(hunitest.TestCase):
    def test1(self) -> None:
        txt = """
        foo

        klass TestHelloWorld(hunitest.TestCase):
            bar
"""
        actual = hprint.dedent(txt)
        expected = """foo

klass TestHelloWorld(hunitest.TestCase):
    bar"""
        self.assert_equal(actual, expected, fuzzy_match=False)

    def test2(self) -> None:
        txt = r"""
        read_data:
          file_name: foo_bar.txt
          nrows: 999
        single_val: hello
        zscore:
          style: gaz
          com: 28"""
        actual = hprint.dedent(txt)
        expected = """read_data:
  file_name: foo_bar.txt
  nrows: 999
single_val: hello
zscore:
  style: gaz
  com: 28"""
        self.assert_equal(actual, expected, fuzzy_match=False)

    def test_roundtrip1(self) -> None:
        """
        Verify that `indent` and `dedent` are inverse of each other.
        """
        txt1 = """foo

# #############################################################################
# TestHelloWorld
# #############################################################################

class TestHelloWorld(hunitest.TestCase):
    bar"""
        num_spaces = 3
        txt2 = hprint.indent(txt1, num_spaces=num_spaces)
        txt3 = hprint.dedent(txt2)
        self.assert_equal(txt1, txt3, fuzzy_match=False)


# #############################################################################
# Test_align_on_left1
# #############################################################################


class Test_align_on_left1(hunitest.TestCase):
    def test1(self) -> None:
        txt = """foo

klass TestHelloWorld(hunitest.TestCase):
    bar
"""
        actual = hprint.align_on_left(txt)
        expected = """foo

klass TestHelloWorld(hunitest.TestCase):
bar
"""
        self.assert_equal(actual, expected, fuzzy_match=False)


# #############################################################################
# Test_logging1
# #############################################################################


class Test_logging1(hunitest.TestCase):
    def test_log_frame1(self) -> None:
        hprint.log_frame(_LOG, "%s %s", "hello", "world")

    def test_log_frame2(self) -> None:
        hprint.log_frame(_LOG, "%s", "hello", level=1)

    def test_log_frame3(self) -> None:
        hprint.log_frame(_LOG, "%s", "hello", level=2, verbosity=logging.INFO)


# #############################################################################
# Test_remove_lead_trail_empty_lines1
# #############################################################################


class Test_remove_lead_trail_empty_lines1(hunitest.TestCase):
    def helper(self, input_str: str, expected_output: List[str]) -> None:
        """
        Test the `remove_lead_trail_empty_lines` function.

        :param input_str: The input string to be processed.
        :param expected_output: The expected output list of strings.

        Example:
            input_str = "line1\n\n\nline2"
            expected_output = ["line1", "", "", "line2"]
        """
        # Test as string.
        actual = hprint.remove_lead_trail_empty_lines(input_str)
        expected = "\n".join(expected_output)
        self.assertEqual(actual, expected)
        # Test as list of strings.
        input_str = input_str.splitlines()
        actual = hprint.remove_lead_trail_empty_lines(input_str)
        self.assertEqual(actual, expected_output)

    def test_empty_string_returns_empty_list(self) -> None:
        input_str: str = ""
        expected_output: List[str] = []
        self.helper(input_str, expected_output)

    def test_single_line_string_returns_single_line_list(self) -> None:
        input_str: str = "line"
        expected_output = ["line"]
        self.helper(input_str, expected_output)

    def test_multiple_lines_with_no_empty_lines_returns_same_lines(
        self,
    ) -> None:
        input_str: str = "line1\nline2\nline3"
        expected_output = ["line1", "line2", "line3"]
        self.helper(input_str, expected_output)

    def test_leading_empty_lines_are_removed(self) -> None:
        input_str: str = "\n\nline1\nline2"
        expected_output = ["line1", "line2"]
        self.helper(input_str, expected_output)

    def test_trailing_empty_lines_are_removed(self) -> None:
        input_str: str = "line1\nline2\n\n"
        expected_output = ["line1", "line2"]
        self.helper(input_str, expected_output)

    def test_leading_and_trailing_empty_lines_are_removed(self) -> None:
        input_str: str = "\n\nline1\nline2\n\n"
        expected_output = ["line1", "line2"]
        self.helper(input_str, expected_output)

    def test_consecutive_empty_lines_in_middle_are_not_removed(self) -> None:
        input_str: str = "line1\n\n\nline2"
        expected_output = ["line1", "", "", "line2"]
        self.helper(input_str, expected_output)

    def test_only_empty_lines_returns_empty_list(self) -> None:
        input_str: str = "\n\n\n"
        expected_output: List[str] = []
        self.helper(input_str, expected_output)

    def test_mixed_content_with_leading_trailing_and_middle_empty_lines(
        self,
    ) -> None:
        input_str: str = "\n\nline1\n\nline2\n\n"
        expected_output = ["line1", "", "line2"]
        self.helper(input_str, expected_output)

    def test_single_empty_line_returns_empty_list(self) -> None:
        input_str: str = "\n"
        expected_output: List[str] = []
        self.helper(input_str, expected_output)

    def test_multiple_consecutive_empty_lines_at_beginning_and_end(
        self,
    ) -> None:
        input_str: str = "\n\n\nline1\nline2\n\n\n"
        expected_output = ["line1", "line2"]
        self.helper(input_str, expected_output)

    def test_input_with_only_spaces_and_tabs_as_empty_lines(self) -> None:
        input_str: str = " \n\t\nline1\nline2\n \n\t"
        expected_output = ["line1", "line2"]
        self.helper(input_str, expected_output)

    def test_input_with_mixed_line_endings_unix_and_windows(self) -> None:
        input_str: str = "line1\n\nline2\r\n\r\nline3"
        expected_output = ["line1", "", "line2", "", "line3"]
        self.helper(input_str, expected_output)

    def test_input_with_special_characters(self) -> None:
        input_str: str = "line1\n\n!@#$%^&*()\n\nline2"
        expected_output = ["line1", "", "!@#$%^&*()", "", "line2"]
        self.helper(input_str, expected_output)


# #############################################################################
# Test_remove_empty_lines
# #############################################################################


class Test_remove_empty_lines(hunitest.TestCase):
    # TODO(ai_gp): Use helper in all the test methods, without changing the
    # interface of helper.
    def helper(self, lines: str, max_consecutive_empty_lines: int, expected: str) -> None:
        """
        Test with an empty list.
        """
        hdbg.dassert_isinstance(lines, list)
        # Prepare inputs.
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = hprint.dedent(expected)
        expected = expected.split("\n")
        self.assert_equal(str(actual), str(expected))

    def test_empty_list(self) -> None:
        """
        Test with an empty list.
        """
        # Prepare inputs.
        lines = []
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = []
        self.assert_equal(str(actual), str(expected))

    def test_no_empty_lines(self) -> None:
        """
        Test with no empty lines in the input.
        """
        # Prepare inputs.
        lines = """
        line1
        line2
        line3
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = ["line1", "line2", "line3"]
        self.assert_equal(str(actual), str(expected))

    def test_all_empty_lines(self) -> None:
        """
        Test with all lines being empty.
        """
        # Prepare inputs.
        lines = ["", "", ""]
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = []
        self.assert_equal(str(actual), str(expected))

    def test_single_empty_line_between_content(self) -> None:
        """
        Test with a single empty line between content lines.
        """
        # Prepare inputs.
        lines = """
        line1

        line2
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = ["line1", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_multiple_consecutive_empty_lines(self) -> None:
        """
        Test with multiple consecutive empty lines.
        """
        # Prepare inputs.
        lines = """
        line1


        line2
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = ["line1", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_empty_lines_with_whitespace(self) -> None:
        """
        Test with lines containing only whitespace (spaces/tabs).
        """
        # Prepare inputs.
        lines = ["line1", "   ", "\t", "line2"]
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = ["line1", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_leading_and_trailing_empty_lines(self) -> None:
        """
        Test with leading and trailing empty lines.
        """
        # Prepare inputs.
        lines = ["", "", "line1", "line2", "", ""]
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = ["line1", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_param_2(self) -> None:
        """
        Test with max_consecutive_empty_lines=2 and 3 consecutive empty lines.
        """
        # Prepare inputs.
        lines = """
        line1



        line2
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=2)
        # Check outputs.
        # With max_consecutive_empty_lines=2, only empty lines exceeding count of 2 are kept.
        # So 3 consecutive empty lines result in 1 empty line kept (the 3rd one).
        expected = ["line1", "", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_param_3(self) -> None:
        """
        Test with max_consecutive_empty_lines=3 and 6 consecutive empty lines.
        """
        # Prepare inputs.
        lines = """
        line1






        line2
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=3)
        # Check outputs.
        # With max_consecutive_empty_lines=3, only empty lines exceeding count of 3 are kept.
        # So 6 consecutive empty lines result in 3 empty lines kept (the 4th, 5th, and 6th ones).
        expected = ["line1", "", "", "", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_with_single_empty(self) -> None:
        """
        Test with max_consecutive_empty_lines=2 but only single empty lines.
        """
        # Prepare inputs.
        lines = """
        line1

        line2

        line3
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=2)
        # Check outputs.
        expected = ["line1", "line2", "line3"]
        self.assert_equal(str(actual), str(expected))

    def test_mixed_content_with_whitespace_lines(self) -> None:
        """
        Test with mixed content including lines with only whitespace.
        """
        # Prepare inputs.
        lines = ["line1", "  ", "", "line2", "\t\t", "line3"]
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = ["line1", "line2", "line3"]
        self.assert_equal(str(actual), str(expected))

    def test_single_line_no_empty(self) -> None:
        """
        Test with a single non-empty line.
        """
        # Prepare inputs.
        lines = ["single line"]
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        expected = ["single line"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_param_1(self) -> None:
        """
        Test with max_consecutive_empty_lines=1 and 2 consecutive empty lines.
        """
        # Prepare inputs.
        lines = """
        line1


        line2
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=1)
        # Check outputs.
        # With max_consecutive_empty_lines=1, only empty lines exceeding count of 1 are kept.
        # So 2 consecutive empty lines result in 1 empty line kept (the 2nd one).
        expected = ["line1", "", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_boundary_equal(self) -> None:
        """
        Test boundary case where consecutive empty lines equals max_consecutive_empty_lines.
        """
        # Prepare inputs.
        lines = """
        line1


        line2
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=2)
        # Check outputs.
        # With exactly 2 consecutive empty lines and max_consecutive_empty_lines=2,
        # no empty lines should be kept (2 > 2 is False).
        expected = ["line1", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_multiple_groups(self) -> None:
        """
        Test multiple groups of consecutive empty lines with max_consecutive_empty_lines.
        """
        # Prepare inputs.
        lines = """
        line1



        line2


        line3
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=2)
        # Check outputs.
        # First group: 3 consecutive empty lines -> 1 kept (the 3rd one).
        # Second group: 2 consecutive empty lines -> 0 kept (2 > 2 is False).
        expected = ["line1", "", "line2", "line3"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_zero_default(self) -> None:
        """
        Test that default max_consecutive_empty_lines=0 removes all empty lines.
        """
        # Prepare inputs.
        lines = """
        line1


        line2


        line3
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        # Run test.
        actual = hprint.remove_empty_lines(lines)
        # Check outputs.
        # With max_consecutive_empty_lines=0 (default), all empty lines are removed.
        expected = ["line1", "line2", "line3"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_with_whitespace_only_lines(self) -> None:
        """
        Test max_consecutive_empty_lines with lines containing only whitespace.
        """
        # Prepare inputs.
        lines = ["line1", "  ", "\t", "   ", "line2"]
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=1)
        # Check outputs.
        # With max_consecutive_empty_lines=1, 3 consecutive whitespace-only lines
        # should result in 2 being kept (the 2nd and 3rd ones).
        expected = ["line1", "\t", "   ", "line2"]
        self.assert_equal(str(actual), str(expected))

    def test_max_consecutive_empty_lines_at_start_and_end(self) -> None:
        """
        Test max_consecutive_empty_lines with empty lines at start and end.
        """
        # Prepare inputs.
        lines = ["", "", "", "line1", "line2", "", "", ""]
        # Run test.
        actual = hprint.remove_empty_lines(lines, max_consecutive_empty_lines=1)
        # Check outputs.
        # Leading 3 empty lines -> 2 kept (the 2nd and 3rd).
        # Trailing 3 empty lines -> 2 kept (the 2nd and 3rd).
        expected = ["", "", "line1", "line2", "", ""]
        self.assert_equal(str(actual), str(expected))
