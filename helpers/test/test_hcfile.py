import logging
import os
from typing import Any, List

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hcfile as hcfile

_LOG = logging.getLogger(__name__)


def _create_test_file(self_: Any, filename: str, content: str) -> str:
    """
    Create a test file with given content in the scratch directory.

    :param scratch_dir: Directory to create file in
    :param filename: Name of file to create
    :param content: Content to write to file
    :return: Full path to created file
    """
    scratch_dir = self_.get_scratch_space()
    file_path = os.path.join(scratch_dir, filename)
    content = hprint.dedent(content)
    hio.to_file(file_path, content)
    return file_path


def _create_cfile(self_: Any, cfile_content: List[str]) -> str:
    """
    Create a cfile with TODOs in the scratch directory.

    :param scratch_dir: Directory to create file in
    :param cfile_content: List of TODO lines to write
    :return: Full path to created cfile
    """
    content = "\n".join(cfile_content)
    return _create_test_file(self_, "cfile.txt", content)


# #############################################################################
# Test_parse_cfile1
# #############################################################################


class Test_parse_cfile1(hunitest.TestCase):
    def helper(self, cfile_content: str, expected: str) -> None:
        """
        Helper function to test parsing a cfile.

        :param cfile_content: Content to write to the test cfile
        :param expected: Expected output from parse_cfile
        """
        # Prepare inputs.
        cfile_path = _create_test_file(self, "cfile.txt", cfile_content)
        # Run function under test.
        actual = hcfile.parse_cfile(cfile_path)
        actual = "\n".join(map(str, actual))
        # Check output.
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test parsing a cfile with valid entries.
        """
        cfile_content = r"""
        file1.py:10: Add docstring
        file2.py:20: Add type hints
        file3.py:30: Fix formatting
        """
        expected = r"""
        ('file1.py', '10', ' Add docstring')
        ('file2.py', '20', ' Add type hints')
        ('file3.py', '30', ' Fix formatting')
        """
        self.helper(cfile_content, expected)

    def test2(self) -> None:
        """
        Test parsing a cfile with valid entries.
        """
        cfile_content = r"""
        dev_scripts_helpers/llms/dockerized_llm_review.py:63:33: F821 undefined name '_extract_bullet_points' [flake8]
        dev_scripts_helpers/llms/llm_transform.py:23: [C0301(line-too-long), ] Line too long (109/100) [pylint]
        helpers/hio.py: 'pandas' is imported multiple times [normalize_imports]
        helpers/hmarkdown.py:770:38: W605 invalid escape sequence '\S' [flake8]
        """
        expected = r"""
        ('dev_scripts_helpers/llms/dockerized_llm_review.py', '63', "33: F821 undefined name '_extract_bullet_points' [flake8]")
        ('dev_scripts_helpers/llms/llm_transform.py', '23', ' [C0301(line-too-long), ] Line too long (109/100) [pylint]')
        ('helpers/hmarkdown.py', '770', "38: W605 invalid escape sequence '\\S' [flake8]")
        """
        self.helper(cfile_content, expected)

    def test_empty_file(self) -> None:
        """
        Test parsing an empty cfile.
        """
        self.helper("", "")

    def test_invalid_entries(self) -> None:
        """
        Test parsing a cfile with invalid entries that should be skipped.
        """
        cfile_content = r"""
        file1.py:10: Valid entry
        Invalid line without proper format
        file2.py:20: Another valid entry
           :30: Missing filename
        file3.py:: Missing line number
        """
        expected = r"""
        ('file1.py', '10', ' Valid entry')
        ('file2.py', '20', ' Another valid entry')
        ('   ', '30', ' Missing filename')
        """
        self.helper(cfile_content, expected)


# #############################################################################
# Test_inject_todos_from_cfile1
# #############################################################################


class Test_inject_todos_from_cfile1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test injecting TODOs from a cfile into a Python file.
        """
        # Create a test file.
        test_file_content = """
        def hello(msg):
            print(msg)

        def world():
            print("world")
        """
        file_path = _create_test_file(self, "test.py", test_file_content)
        # Create cfile with TODOs.
        cfile_content = [
            f"{file_path}:1: Add type hints.",
            f"{file_path}:4: Add docstring.",
        ]
        _create_cfile(self, cfile_content)
        # Run the function under test.
        self._inject_todos("\n".join(cfile_content))
        # Check output.
        actual = hio.from_file(file_path)
        expected = """
        # TODO(user): Add type hints.
        def hello(msg):
            print(msg)

        # TODO(user): Add docstring.
        def world():
            print("world")
        """
        self.assert_equal(actual, expected, dedent=True)

    def test_one_line_file(self) -> None:
        """
        Test injecting TODOs into an empty file.
        """
        # Create an empty test file
        test_file_content = """
        print("hello")
        """
        file_path = _create_test_file(self, "empty.py", test_file_content)
        # Create cfile with TODOs
        cfile_content = [f"{file_path}:1: Add content to empty file."]
        _create_cfile(self, cfile_content)
        # Run the function under test
        self._inject_todos("\n".join(cfile_content))
        # Check output
        actual = hio.from_file(file_path)
        expected = """
        # TODO(user): Add content to empty file.
        print("hello")
        """
        self.assert_equal(actual, expected, dedent=True)

    def test_invalid_line_numbers(self) -> None:
        """
        Test handling of TODOs with invalid line numbers.
        """
        # Create a test file
        test_file_content = """
        line1
        line2
        """
        file_path = _create_test_file(self, "test.py", test_file_content)
        # Create cfile with invalid line numbers
        cfile_content = [
            f"{file_path}:999: This line number doesn't exist.",
        ]
        _create_cfile(self, cfile_content)
        # This should raise an assertion error due to invalid line numbers
        with self.assertRaises(AssertionError) as err:
            self._inject_todos("\n".join(cfile_content))
        # Check output.
        expected = """
        ################################################################################
        * Failed assertion *
        998 < 2
        ################################################################################
        """
        self.assert_equal(
            str(err.exception), expected, dedent=True, fuzzy_match=True
        )

    def test2(self) -> None:
        """
        Test injecting TODOs from a cfile into a Python file with a complex
        class.
        """
        # Create a test file.
        test_file_content = """
        import logging
        from typing import List, Optional

        class DataProcessor:
            def __init__(self):
                self.logger = logging.getLogger(__name__)
                self.data = []

            def process_batch(self, items):
                for item in items:
                    self.data.append(self._transform(item))

            def _transform(self, item):
                return item.upper()

            def get_results(self):
                return self.data

            def clear(self):
                self.data = []
        """
        file_path = _create_test_file(self, "test.py", test_file_content)
        # Create cfile with TODOs.
        cfile_content = [
            f"{file_path}:4: Add class docstring explaining purpose and usage",
            f"{file_path}:5: Add type hints for instance variables",
            f"{file_path}:9: Add type hints for items parameter",
            f"{file_path}:10: Consider adding batch size validation",
            f"{file_path}:13: Add error handling for non-string inputs",
            f"{file_path}:16: Add return type hint and docstring",
            f"{file_path}:19: Add docstring explaining clear behavior",
        ]
        _create_cfile(self, cfile_content)
        # Run function under test.
        self._inject_todos("\n".join(cfile_content))
        # Check output.
        actual = hio.from_file(file_path)
        expected = """
        import logging
        from typing import List, Optional

        # TODO(user): Add class docstring explaining purpose and usage
        class DataProcessor:
            # TODO(user): Add type hints for instance variables
            def __init__(self):
                self.logger = logging.getLogger(__name__)
                self.data = []

            # TODO(user): Add type hints for items parameter
            def process_batch(self, items):
                # TODO(user): Consider adding batch size validation
                for item in items:
                    self.data.append(self._transform(item))

            # TODO(user): Add error handling for non-string inputs
            def _transform(self, item):
                return item.upper()

            # TODO(user): Add return type hint and docstring
            def get_results(self):
                return self.data

            # TODO(user): Add docstring explaining clear behavior
            def clear(self):
                self.data = []
        """
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test injecting TODOs from a cfile into multiple Python files.
        """
        # Create first test file.
        test_file1_content = """
        def foo():
            pass
        """
        file_path1 = _create_test_file(self, "test1.py", test_file1_content)
        # Create second test file.
        test_file2_content = """
        def bar():
            return None
        """
        file_path2 = _create_test_file(self, "test2.py", test_file2_content)
        # Create cfile.
        cfile_content = [
            f"{file_path1}:1: Add docstring for foo.",
            f"{file_path2}:1: Add docstring for bar.",
            f"{file_path2}:2: Add type hint for return.",
        ]
        _create_cfile(self, cfile_content)
        # Run function under test.
        self._inject_todos("\n".join(cfile_content))
        # Check output.
        actual1 = hio.from_file(file_path1)
        expected1 = """
        # TODO(user): Add docstring for foo.
        def foo():
            pass
        """
        self.assert_equal(actual1, expected1, dedent=True)
        #
        actual2 = hio.from_file(file_path2)
        expected2 = """
        # TODO(user): Add docstring for bar.
        def bar():
            # TODO(user): Add type hint for return.
            return None
        """
        self.assert_equal(actual2, expected2, dedent=True)

    def _inject_todos(self, cfile_content: str) -> None:
        """
        Helper to inject TODOs with standard parameters.
        """
        todo_user = "user"
        comment_prefix = "#"
        hcfile.inject_todos_from_cfile(cfile_content, todo_user, comment_prefix)
