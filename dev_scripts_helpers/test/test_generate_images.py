import base64
import logging
import os

import pytest

pytest.importorskip("openai")

import dev_scripts_helpers.generate_images as dscgenima
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_descriptions_with_names
# #############################################################################


class Test_parse_descriptions_with_names(hunitest.TestCase):
    """
    Test the _parse_descriptions_with_names() function for extracting prompts with names.
    """

    def helper(self, content: str, expected: list) -> None:
        """
        Test helper for _parse_descriptions_with_names().

        :param content: input text content with prompts
        :param expected: expected list of tuples (prompt_name, prompt_text)
        """
        # Prepare inputs.
        content = hprint.dedent(content)
        # Run test.
        actual = dscgenima._parse_descriptions_with_names(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """Test parsing single prompt with name extraction."""
        # Prepare inputs.
        content = """
        # Prompt_A
        This is the first prompt text.
        """
        # Prepare outputs.
        expected = [("Prompt_A", "This is the first prompt text.")]
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """Test parsing multiple prompts with names."""
        # Prepare inputs.
        content = """
        # Urban_Landscape
        A futuristic cityscape at sunset.

        # Nature_Scene
        A serene forest with a waterfall.

        # Abstract_Art
        Geometric shapes in vibrant colors.
        """
        # Prepare outputs.
        expected = [
            ("Urban_Landscape", "A futuristic cityscape at sunset."),
            ("Nature_Scene", "A serene forest with a waterfall."),
            ("Abstract_Art", "Geometric shapes in vibrant colors."),
        ]
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """Test parsing prompts with multi-line text."""
        # Prepare inputs.
        content = """
        # Prompt_A
        Line 1 of prompt A.
        Line 2 of prompt A.

        # Prompt_B
        Line 1 of prompt B.
        """
        # Prepare outputs.
        expected = [
            ("Prompt_A", "Line 1 of prompt A.\nLine 2 of prompt A."),
            ("Prompt_B", "Line 1 of prompt B."),
        ]
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """Test parsing prompts with underscores and numbers in names."""
        # Prepare inputs.
        content = """
        # Prompt_Name_123
        This is the prompt text.
        # Another_Prompt_456
        Another prompt.
        """
        # Prepare outputs.
        expected = [
            ("Prompt_Name_123", "This is the prompt text."),
            ("Another_Prompt_456", "Another prompt."),
        ]
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """Test parsing empty content."""
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """Test that content without prompt headers raises assertion error."""
        # Prepare inputs.
        content = """
        Just some random text
        without any headers.
        """
        content = hprint.dedent(content)
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dscgenima._parse_descriptions_with_names(content)
        # Verify error message contains information about unprocessed lines.
        error_message = str(cm.exception)
        self.assertIn("Found lines that were not processed", error_message)
        self.assertIn("Just some random text", error_message)

    def test7(self) -> None:
        """Test parsing prompts with blank lines within text."""
        # Prepare inputs.
        content = """
        # Prompt_A
        First paragraph.

        Second paragraph after blank line.

        # Prompt_B
        Another prompt.
        """
        # Prepare outputs.
        expected = [
            ("Prompt_A", "First paragraph.\n\nSecond paragraph after blank line."),
            ("Prompt_B", "Another prompt."),
        ]
        # Run test.
        self.helper(content, expected)
