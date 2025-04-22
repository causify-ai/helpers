import os
from typing import List, Tuple

import helpers.hio as hio
import helpers.hstring as hstring
import helpers.hunit_test as hunitest


# #############################################################################
# TestExtractVersionFromFileName
# #############################################################################


class TestExtractVersionFromFileName(hunitest.TestCase):

    def test_extract_version_from_file_name1(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("1.1", (1, 1))

    def test_extract_version_from_file_name2(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("4", (4, 0))

    def test_extract_version_from_file_name3(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("1.0", (1, 0))

    def test_extract_version_from_file_name4(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("3.11", (3, 11))

    def test_extract_version_from_file_name5(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("16.2", (16, 2))

    def test_extract_version_from_file_name6(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("25.11", (25, 11))

    def test_extract_version_from_file_name_incorrect_format1(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format("incorrect")

    def test_extract_version_from_file_name_incorrect_format2(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format(
            "universe_vxx.json"
        )

    def test_extract_version_from_file_name_incorrect_format3(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format(
            "universe_v.1.json"
        )

    def test_extract_version_from_file_name_incorrect_format4(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format(
            "universe_11.json"
        )

    def _test_extract_version_from_file_name(
        self, version: str, expected: Tuple[int, int]
    ) -> None:
        """
        Verify function provides expected output on valid inputs.

        :param version: version in string format to input, e.g. 1.0
        :param expected: expected output version in (major, minor)
            format
        """
        fn = f"/app/im_v2/ccxt/universe/download/universe_v{version}.json"
        self.assertEqual(hstring.extract_version_from_file_name(fn), expected)

    def _test_extract_version_from_file_name_incorrect_format(
        self, file_name: str
    ) -> None:
        """
        Helper function to verify function raises AssertionError on incorrect
        input format.

        :param file_name: incorrect file_name to test
        """
        expected_fail = "Can't parse file"
        with self.assertRaises(AssertionError) as fail:
            _ = hstring.extract_version_from_file_name(file_name)
        self.assertIn(expected_fail, str(fail.exception))


# #############################################################################
# TestGetDocstringLineIndices
# #############################################################################


class TestGetDocstringLineIndices(hunitest.TestCase):
    """
    Test determining which code lines are inside (doc)strings.
    """

    def helper(self, code: str, expected: List[str]) -> None:
        lines = code.split("\n")
        actual_idxs = hstring.get_docstring_line_indices(lines)
        actual = [lines[i].strip() for i in actual_idxs]
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test one type of quotes.
        """
        code = """
    def test_assert_equal1(self) -> None:
        '''
        Test one.
        '''
        actual = "hello world"
        expected = actual
        self.assert_equal(actual, expected)

    def test_check_string1(self) -> None:
        actual = "hello world"
        s = '''
        Inside a string.
        '''
        d = '''Does not count'''
        self.check_string(actual)

        """
        expected = ["'''", "Test one.", "s = '''", "Inside a string."]
        self.helper(code, expected)

    def test2(self) -> None:
        """
        Test the second type of quotes.
        """
        code = '''
    def test_assert_equal1(self) -> None:
        """
        Test one.
        """
        actual = "hello world"
        expected = actual
        self.assert_equal(actual, expected)

    def test_check_string1(self) -> None:
        actual = "hello world"
        s = """
        Inside a string.
        """
        d = """Does not count"""
        self.check_string(actual)

        '''
        expected = ['"""', "Test one.", 's = """', "Inside a string."]
        self.helper(code, expected)

    def test3(self) -> None:
        """
        Test quotes within quotes.
        """
        code = """
    def test_assert_equal1(self) -> None:
        '''
        Test one.
        """
        code += '''\
"""
        String within "Test one".
        """
        '''
        code += """\
'''
        actual = "hello world"
        expected = actual
        self.assert_equal(actual, expected)

    def test_check_string1(self) -> None:
        actual = "hello world"
        s = '''
        Inside a string.
        '''
        d = '''Does not count'''
        self.check_string(actual)

        """
        expected = [
            "'''",
            "Test one.",
            '"""',
            'String within "Test one".',
            '"""',
            "s = '''",
            "Inside a string.",
        ]
        self.helper(code, expected)


# #############################################################################
# TestGetCodeBlockLineIndices
# #############################################################################


class TestGetCodeBlockLineIndices(hunitest.TestCase):

    def helper(self, code: str, expected: List[str]) -> None:
        lines = code.split("\n")
        actual_idxs = hstring.get_code_block_line_indices(lines)
        actual = [lines[i].strip() for i in actual_idxs]
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test getting code block line indices.
        """
        code = """
    def test_assert_equal1(self) -> None:
        ```
        Test one.
        ```
        d = ```Does not count```
        actual = "hello world"
        expected = actual
        self.assert_equal(actual, expected)
        """
        expected = ["```", "Test one."]
        self.helper(code, expected)


# #############################################################################
# TestGetDocstrings
# #############################################################################


class TestGetDocstrings(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test that grouped lines within docstrings are correctly returned.
        """
        # Prepare inputs.
        test_get_docstring_lines_input_dir = self.get_input_dir()
        text_file_path = os.path.join(
            test_get_docstring_lines_input_dir, "test.txt"
        )
        text = hio.from_file(text_file_path)
        lines = text.splitlines()
        # Run.
        actual = hstring.get_docstrings(lines)
        # Check.
        expected = [
            [1, 2, 3, 4, 5, 6],
            [11, 12, 13, 14, 15, 16],
        ]
        self.assertEqual(actual, expected)
