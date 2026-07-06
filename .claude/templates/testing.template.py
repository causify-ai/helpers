"""
Import as:

import .claude.templates.testing.template as ctetetem
"""

import logging

import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_format_compressed_markdown
# #############################################################################


class Test_format_compressed_markdown(hunitest.TestCase):
    """
    Test the format_compressed_markdown function.

    Tests cover:
    - Basic text without formatting
    - Text with single-level bullets
    - Text with multiple bullets
    - Edge cases (empty input, only whitespace)
    """

    def helper(self, actual: str, expected: str) -> None:
        """
        Helper for testing format_compressed_markdown.

        Prepares inputs by dedenting and removing empty lines, then compares
        with expected output.

        :param actual: Input text (may have indentation)
        :param expected: Expected formatted output
        """
        # Prepare inputs.
        actual = hprint.dedent(actual)
        actual = [line for line in actual.split("\n") if line]
        actual = "\n".join(actual)
        # Prepare outputs.
        expected = hprint.dedent(expected)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test happy path: basic text without formatting.
        """
        # Prepare inputs.
        text = """
        Some text"""
        # Prepare outputs.
        expected = text
        # Run test.
        actual = text
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test text with single bullet point removes empty lines.
        """
        # Prepare inputs.
        text = """
        Some text

        - First bullet
        More text"""
        # Prepare outputs.
        expected = """
        Some text
        - First bullet
        More text"""
        # Run test.
        self.helper(text, expected)

    def test3(self) -> None:
        """
        Test multiple first-level bullets remain unchanged.
        """
        # Prepare inputs.
        text = """
        - First bullet
        - Second bullet
        - Third bullet"""
        # Prepare outputs.
        expected = text
        # Run test.
        self.helper(text, expected)

    def test4(self) -> None:
        """
        Test edge case: empty string input.
        """
        # Prepare inputs.
        text = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        actual = text
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_process_data
# #############################################################################


class Test_process_data(hunitest.TestCase):
    """
    Test process_data function with various input types.

    Demonstrates:
    - Multiple test cases for one function
    - Using helper method to reduce duplication
    - Testing happy path and edge cases
    - Using dedent for multi-line strings
    """

    def _process_data(self, data: str) -> str:
        """
        Example function to process data.

        This is a placeholder for the actual function being tested.
        """
        return data.strip()

    def helper(
        self, input_data: str, expected_output: str, description: str = ""
    ) -> None:
        """
        Helper for testing process_data.

        :param input_data: Input string to process
        :param expected_output: Expected string output
        :param description: Optional description for debugging
        """
        # Run test.
        actual = self._process_data(input_data)
        # Check outputs.
        self.assert_equal(actual, expected_output)

    def test1(self) -> None:
        """
        Test happy path: simple input.
        """
        # Prepare inputs.
        input_data = "hello world"
        # Prepare outputs.
        expected = "hello world"
        # Run test.
        self.helper(input_data, expected)

    def test2(self) -> None:
        """
        Test edge case: input with surrounding whitespace.
        """
        # Prepare inputs.
        input_data = "  hello world  \n"
        # Prepare outputs.
        expected = "hello world"
        # Run test.
        self.helper(input_data, expected)

    def test3(self) -> None:
        """
        Test edge case: empty string.
        """
        # Prepare inputs.
        input_data = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(input_data, expected)


# #############################################################################
# Test_transform_markdown
# #############################################################################


class Test_transform_markdown(hunitest.TestCase):
    """
    Test markdown transformation with file I/O patterns.

    Demonstrates:
    - Using input and output directories for test data
    - Comparing structured data as strings
    - Testing with realistic file paths
    """

    def test1(self) -> None:
        """
        Test transformation of markdown with headers.
        """
        # Prepare inputs.
        input_text = """
        # Chapter 1

        ## Section 1.1
        Content 1.1

        ## Section 1.2
        Content 1.2
        """
        # Prepare outputs.
        expected = """
        # Chapter 1
        ## Section 1.1
        Content 1.1
        ## Section 1.2
        Content 1.2
        """
        # Run test.
        actual = hprint.dedent(input_text)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test with multi-line code blocks.
        """
        # Prepare inputs.
        input_text = """
        Here's some code:

        ```python
        def hello():
            print("world")
        ```
        """
        # Prepare outputs.
        expected = """
        Here's some code:
        ```python
        def hello():
            print("world")
        ```
        """
        # Run test.
        actual = input_text.strip()
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)
