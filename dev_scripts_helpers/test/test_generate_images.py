import logging

import dev_scripts_helpers.generate_images as dscgenima
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_descriptions
# #############################################################################


class Test_parse_descriptions(hunitest.TestCase):
    """
    Test the _parse_descriptions() function for extracting prompts from text.
    """

    def helper(self, content: str, expected: list) -> None:
        """
        Test helper for _parse_descriptions().

        :param content: input text content with prompts
        :param expected: expected list of extracted prompts
        """
        # Prepare inputs.
        content = hprint.dedent(content)
        # Run test.
        actual = dscgenima._parse_descriptions(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """Test parsing single prompt with single-line text."""
        # Prepare inputs.
        content = """
            # Prompt_A
            This is the first prompt text.
            """
        # Prepare outputs.
        expected = ["This is the first prompt text."]
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """Test parsing single prompt with multi-line text."""
        # Prepare inputs.
        content = """
            # Prompt_A
            This is the first line.
            This is the second line.
            This is the third line.
            """
        # Prepare outputs.
        expected = [
            "This is the first line.\nThis is the second line.\nThis is the third line."
        ]
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """Test parsing multiple prompts without blank lines between them."""
        # Prepare inputs.
        content = """
            # Prompt_A
            Text for prompt A.
            # Prompt_B
            Text for prompt B.
            # Prompt_C
            Text for prompt C.
            """
        # Prepare outputs.
        expected = [
            "Text for prompt A.",
            "Text for prompt B.",
            "Text for prompt C.",
        ]
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """Test parsing multiple prompts with blank lines between them."""
        # Prepare inputs.
        content = """
            # Prompt_A
            Text for prompt A.

            # Prompt_B
            Text for prompt B.


            # Prompt_C
            Text for prompt C.
            """
        # Prepare outputs.
        expected = [
            "Text for prompt A.",
            "Text for prompt B.",
            "Text for prompt C.",
        ]
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """Test parsing multiple prompts with multi-line text and blank lines."""
        # Prepare inputs.
        content = """
            # Prompt_A
            Line 1 of prompt A.
            Line 2 of prompt A.

            # Prompt_B
            Line 1 of prompt B.
            Line 2 of prompt B.
            Line 3 of prompt B.

            # Prompt_C
            Single line for prompt C.
            """
        # Prepare outputs.
        expected = [
            "Line 1 of prompt A.\nLine 2 of prompt A.",
            "Line 1 of prompt B.\nLine 2 of prompt B.\nLine 3 of prompt B.",
            "Single line for prompt C.",
        ]
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """Test parsing prompts with blank lines within the text."""
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
            "First paragraph.\n\nSecond paragraph after blank line.",
            "Another prompt.",
        ]
        # Run test.
        self.helper(content, expected)

    def test7(self) -> None:
        """Test parsing empty content."""
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(content, expected)

    def test8(self) -> None:
        """Test parsing content without any prompt headers."""
        # Prepare inputs.
        content = """
            Just some random text
            without any headers
            that should be ignored.
            """
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(content, expected)

    def test9(self) -> None:
        """Test parsing prompts with underscores in the name."""
        # Prepare inputs.
        content = """
            # Prompt_Name_With_Underscores
            This is the prompt text.
            """
        # Prepare outputs.
        expected = ["This is the prompt text."]
        # Run test.
        self.helper(content, expected)

    def test10(self) -> None:
        """Test parsing prompts with numbers in the name."""
        # Prepare inputs.
        content = """
            # Prompt123
            This is the prompt text.
            # Prompt456
            Another prompt.
            """
        # Prepare outputs.
        expected = ["This is the prompt text.", "Another prompt."]
        # Run test.
        self.helper(content, expected)

    def test11(self) -> None:
        """Test that leading and trailing whitespace is stripped from prompts."""
        # Prepare inputs.
        content = """
            # Prompt_A

              Text with leading spaces.
              More text.

            """
        # Prepare outputs.
        expected = ["Text with leading spaces.\n  More text."]
        # Run test.
        self.helper(content, expected)

    def test12(self) -> None:
        """Test parsing prompt headers with multiple spaces after hash."""
        # Prepare inputs.
        content = """
            #   Prompt_A
            Text for prompt A.
            #    Prompt_B
            Text for prompt B.
            """
        # Prepare outputs.
        expected = ["Text for prompt A.", "Text for prompt B."]
        # Run test.
        self.helper(content, expected)

    def test13(self) -> None:
        """Test complex realistic example with multiple prompts."""
        # Prepare inputs.
        content = """
            # Urban_Landscape
            A futuristic cityscape at sunset with flying cars and neon lights.
            The buildings are tall glass structures reflecting the orange sky.
            Include people walking on elevated sidewalks.

            # Nature_Scene
            A serene forest with a waterfall cascading into a crystal-clear pool.
            Morning mist hovers over the water.


            Rays of sunlight break through the canopy.

            # Abstract_Art
            Geometric shapes in vibrant colors.
            Circles, triangles, and squares overlapping.
            Use bold primary colors: red, blue, yellow.
            """
        # Prepare outputs.
        expected = [
            "A futuristic cityscape at sunset with flying cars and neon lights.\nThe buildings are tall glass structures reflecting the orange sky.\nInclude people walking on elevated sidewalks.",
            "A serene forest with a waterfall cascading into a crystal-clear pool.\nMorning mist hovers over the water.\n\n\nRays of sunlight break through the canopy.",
            "Geometric shapes in vibrant colors.\nCircles, triangles, and squares overlapping.\nUse bold primary colors: red, blue, yellow.",
        ]
        # Run test.
        self.helper(content, expected)
