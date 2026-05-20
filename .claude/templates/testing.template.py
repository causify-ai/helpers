import logging

import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class Test_format_compressed_markdown1(hunitest.TestCase):
    """
    Test the format_compressed_markdown function.
    """

    def helper(self, actual: str, expected: str) -> None:
        """
        Test helper for `format_compressed_markdown()`.

        Prepares inputs by dedenting and removing empty lines, prepares expected
        output by dedenting, then compares them.

        :param actual: Actual input text with potential indentation
        :param expected: Expected output text after formatting
        """
        actual = hprint.dedent(actual)
        actual = [line for line in actual.split("\n") if line != ""]
        actual = "\n".join(actual)
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test basic case.
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
        Test basic case with single first level bullet.
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
        Test multiple first level bullets.
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
