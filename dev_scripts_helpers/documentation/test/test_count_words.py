import contextlib
import io
import os
from unittest import mock

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.count_words as dshdcowo


# #############################################################################
# Test_count_words_in_file
# #############################################################################


class Test_count_words_in_file(hunitest.TestCase):
    """
    Test the `_count_words_in_file()` function.
    """

    def helper(self, content: str, expected: int) -> None:
        """
        Test helper for `_count_words_in_file()`.

        :param content: content to write to the test file
        :param expected: expected word count
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "test.txt")
        hio.to_file(file_path, content)
        # Run test.
        actual = dshdcowo._count_words_in_file(file_path=file_path)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test happy path: normal text with several words.
        """
        # Prepare inputs.
        content = "This is a simple sentence with seven words."
        # Prepare outputs.
        expected = 8
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test edge case: empty file has zero words.
        """
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected = 0
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test edge case: multi-line text with extra whitespace.
        """
        # Prepare inputs.
        content = "line one\n\n   line   two  \nline three"
        # Prepare outputs.
        expected = 6
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_count_words
# #############################################################################


# TODO(ai_gp): Factor out common code.
class Test_count_words(hunitest.TestCase):
    """
    Test the `_count_words()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: word counts across multiple files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "file1.txt")
        file2 = os.path.join(scratch_dir, "file2.txt")
        hio.to_file(file1, "one two three")
        hio.to_file(file2, "four five")
        file_paths = [file1, file2]
        # Prepare outputs.
        expected_total = 5
        expected_counts = {file1: 3, file2: 2}
        # Run test.
        actual_total, actual_counts = dshdcowo._count_words(
            file_paths=file_paths
        )
        # Check outputs.
        self.assertEqual(actual_total, expected_total)
        self.assertEqual(str(actual_counts), str(expected_counts))

    def test2(self) -> None:
        """
        Test edge case: single file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "file1.txt")
        hio.to_file(file1, "only one file here")
        file_paths = [file1]
        # Prepare outputs.
        expected_total = 4
        expected_counts = {file1: 4}
        # Run test.
        actual_total, actual_counts = dshdcowo._count_words(
            file_paths=file_paths
        )
        # Check outputs.
        self.assertEqual(actual_total, expected_total)
        self.assertEqual(str(actual_counts), str(expected_counts))


# #############################################################################
# Test_format_reading_time
# #############################################################################


class Test_format_reading_time(hunitest.TestCase):
    """
    Test the `_format_reading_time()` function.
    """

    def helper(self, words: int, expected: str) -> None:
        """
        Test helper for `_format_reading_time()`.

        :param words: number of words
        :param expected: expected formatted reading time
        """
        # Run test.
        actual = dshdcowo._format_reading_time(words=words)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test happy path: word count under an hour of reading time.
        """
        # Prepare inputs.
        words = 300
        # Prepare outputs.
        expected = "2.0m"
        # Run test.
        self.helper(words, expected)

    def test2(self) -> None:
        """
        Test edge case: word count above an hour of reading time.
        """
        # Prepare inputs.
        words = 15000
        # Prepare outputs.
        expected = "1.67h"
        # Run test.
        self.helper(words, expected)

    def test3(self) -> None:
        """
        Test edge case: zero words.
        """
        # Prepare inputs.
        words = 0
        # Prepare outputs.
        expected = "0.0m"
        # Run test.
        self.helper(words, expected)


# #############################################################################
# Test_build_table_data
# #############################################################################


# TODO(ai_gp): Factor out common code.
class Test_build_table_data(hunitest.TestCase):
    """
    Test the `_build_table_data()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: rows are sorted by file path with a total row.
        """
        # Prepare inputs.
        file_counts = {"b.txt": 100, "a.txt": 200}
        total_words = 300
        # Prepare outputs.
        expected = """
        ([['a.txt', '200', '1.3m'], ['b.txt', '100', '0.7m'], ['TOTAL', '300', '2.0m']], ['File', 'Words', 'Reading Time'])
        """.strip()
        # Run test.
        actual = dshdcowo._build_table_data(
            file_counts=file_counts, total_words=total_words
        )
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test2(self) -> None:
        """
        Test edge case: single file.
        """
        # Prepare inputs.
        file_counts = {"only.txt": 150}
        total_words = 150
        # Prepare outputs.
        expected = """
        ([['only.txt', '150', '1.0m'], ['TOTAL', '150', '1.0m']], ['File', 'Words', 'Reading Time'])
        """.strip()
        # Run test.
        actual = dshdcowo._build_table_data(
            file_counts=file_counts, total_words=total_words
        )
        # Check outputs.
        self.assert_equal(str(actual), expected)


# #############################################################################
# Test_print_table
# #############################################################################


class Test_print_table(hunitest.TestCase):
    """
    Test the `_print_table()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: printed table contains file names and totals.
        """
        # Prepare inputs.
        file_counts = {"a.txt": 10}
        total_words = 10
        # Prepare outputs.
        expected = """
        File      Words  Reading Time
        ------  -------  --------------
        a.txt        10  0.1m
        TOTAL        10  0.1m
        """
        expected = hprint.dedent(expected)
        # Run test.
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            dshdcowo._print_table(
                file_counts=file_counts, total_words=total_words
            )
        actual = buf.getvalue()
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_count_words_py
# #############################################################################


# TODO(ai_gp): Factor out common code
# TODO(ai_gp): Use self.assert_equal instead of self.assert_in
class Test_count_words_py(hunitest.TestCase):
    """
    End-to-end tests for the `count_words.py` executable.
    """

    def _run_main(self, argv: list) -> str:
        """
        Run `dshdcowo._main()` with a mocked `sys.argv` and capture stdout.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :return: captured stdout
        """
        parser = dshdcowo._parse()
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            with mock.patch("sys.argv", argv):
                dshdcowo._main(parser)
        return buf.getvalue()

    def test1(self) -> None:
        """
        Test happy path: single `--input_file` argument.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "doc.txt")
        hio.to_file(input_file, "one two three four five")
        argv = ["count_words.py", "--input_file", input_file]
        # Run test.
        actual = self._run_main(argv)
        # Check outputs.
        self.assertIn("5", actual)
        self.assertIn("TOTAL", actual)

    def test2(self) -> None:
        """
        Test happy path: multiple `--input_files` arguments.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "doc1.txt")
        file2 = os.path.join(scratch_dir, "doc2.txt")
        hio.to_file(file1, "one two")
        hio.to_file(file2, "three four five")
        argv = ["count_words.py", "--input_files", file1, file2]
        # Run test.
        actual = self._run_main(argv)
        # Check outputs.
        self.assertIn("TOTAL", actual)
        self.assertIn("5", actual)
