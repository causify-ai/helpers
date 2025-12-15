import logging

import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_format_compressed_markdown1
# #############################################################################


class Test_format_compressed_markdown1(hunitest.TestCase):
    def helper(self, actual: str, expected: str) -> None:
        # Prepare inputs.
        actual = hprint.dedent(actual)
        actual = [line for line in actual.split("\n") if line != ""]
        actual = "\n".join(actual)
        # Prepare outputs.
        expected = hprint.dedent(expected)
        # Check output.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        # Prepare inputs.
        # ...
        # Evaluate the function.
        # ...
        # Check output.
        # ...
        pass

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
        # Check.
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
        expected = """
        - First bullet
        - Second bullet
        - Third bullet"""
        # Check.
        self.helper(text, expected)
