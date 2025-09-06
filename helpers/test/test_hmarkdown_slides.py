import logging
from typing import List

import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_process_slides
# #############################################################################


class Test_process_slides(hunitest.TestCase):
    @staticmethod
    def transform(slide_text: List[str]) -> str:
        """
        Example adding a `@` to the beginning of each line of the slide.
        """
        _LOG.debug("input=\n%s", "\n".join(slide_text))
        # Transform.
        text_out = [f"@{line}" for line in slide_text]
        _LOG.debug("output=\n%s", "\n".join(text_out))
        return text_out

    def helper(self, text: str, expected: str) -> None:
        # Prepare inputs.
        text = hprint.dedent(text, remove_lead_trail_empty_lines_=False)
        # Process.
        actual = hmarkdo.process_slides(text, self.transform)
        # Check output.
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=False)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test multiple slides.
        """
        text = """
        * Slide 1
            - Point 1
            - Point 2

        * Slide 2
            - Point A
            - Point B
        """
        expected = """
        @* Slide 1
        @    - Point 1
        @    - Point 2
        @
        @* Slide 2
        @    - Point A
        @    - Point B
        """
        self.helper(text, expected)

    def test2(self) -> None:
        """
        Test single line slide.
        """
        text = """
        * Single line slide
        """
        expected = """
        @* Single line slide
        """
        self.helper(text, expected)

    def test3(self) -> None:
        """
        Test slide with inline comment.
        """
        text = """
        * Slide with comment
            # This is a comment
            - Point 1
        """
        expected = """
        @* Slide with comment
        @    # This is a comment
        @    - Point 1
        """
        self.helper(text, expected)

    def test4(self) -> None:
        """
        Test slide with comment block.
        """
        text = """
        * Slide with block
            <!--
            This is a comment block
            spanning multiple lines
            -->
            - Point 1
        """
        expected = """
        @* Slide with block
        @    <!--
        @    This is a comment block
        @    spanning multiple lines
        @    -->
        @    - Point 1
        """
        self.helper(text, expected)

    def test5(self) -> None:
        text = """
        * Slide 1
        * Slide 2
        """
        expected = """
        @* Slide 1
        @* Slide 2
        """
        self.helper(text, expected)

    def test6(self) -> None:
        text = """

        * Slide 1
        * Slide 2
        """
        expected = """

        @* Slide 1
        @* Slide 2
        """
        self.helper(text, expected)

    def test7(self) -> None:
        text = """

        * Slide 1
        * Slide 2

        """
        expected = """

        @* Slide 1
        @* Slide 2
        @
        """
        self.helper(text, expected)

    def test8(self) -> None:
        text = """
        //* Slide 1
        * Slide 2

        """
        expected = """
        //* Slide 1
        @* Slide 2
        @
        """
        self.helper(text, expected)


# #############################################################################
# Test_convert_slide_to_markdown
# #############################################################################


class Test_convert_slide_to_markdown(hunitest.TestCase):
    def helper(self, input_text, expected_text) -> None:
        """
        Test converting multiple slide bullets.
        """
        # Prepare inputs.
        input_text = hprint.dedent(input_text).strip().split("\n")
        # Run test.
        actual = hmarkdo.convert_slide_to_markdown(lines)
        # Check outputs.
        expected = hprint.dedent(expected_text).strip().split("\n")
        self.assert_equal(str(actual), str(expected))

    # TODO(ai): Use helper
    def test_convert_simple_slide(self) -> None:
        """
        Test converting a simple slide bullet to markdown header.
        """
        # Prepare inputs.
        text = "* This is a slide title"
        lines = [text]
        # Run test.
        actual = hmarkdo.convert_slide_to_markdown(lines)
        # Check outputs.
        expected = ["##### This is a slide title"]
        self.assert_equal(str(actual), str(expected))

    def test_convert_multiple_slides(self) -> None:
        """
        Test converting multiple slide bullets.
        """
        # Prepare inputs.
        text = """
        * First slide
          - Some content
        * Second slide
          - More content
        """
        lines = hprint.dedent(text).strip().split("\n")
        # Run test.
        actual = hmarkdo.convert_slide_to_markdown(lines)
        # Check outputs.
        expected_text = """
        ##### First slide
          - Some content
        ##### Second slide
          - More content
        """
        expected = hprint.dedent(expected_text).strip().split("\n")
        self.assert_equal(str(actual), str(expected))

    def test_convert_mixed_content(self) -> None:
        """
        Test converting slides mixed with other content.
        """
        # Prepare inputs.
        text = """
        Some intro text
        * Slide title
          - Point 1
          - Point 2
        Regular markdown text
        * Another slide
        """
        lines = hprint.dedent(text).strip().split("\n")
        # Run test.
        actual = hmarkdo.convert_slide_to_markdown(lines)
        # Check outputs.
        expected_text = """
        Some intro text
        ##### Slide title
          - Point 1
          - Point 2
        Regular markdown text
        ##### Another slide
        """
        expected = hprint.dedent(expected_text).strip().split("\n")
        self.assert_equal(str(actual), str(expected))

    def test_convert_no_slides(self) -> None:
        """
        Test converting text with no slide bullets.
        """
        # Prepare inputs.
        text = """
        Regular text
        More text
        - Regular bullet point
        """
        lines = hprint.dedent(text).strip().split("\n")
        # Run test.
        actual = hmarkdo.convert_slide_to_markdown(lines)
        # Check outputs.
        expected_text = """
        Regular text
        More text
        - Regular bullet point
        """
        expected = hprint.dedent(expected_text).strip().split("\n")
        self.assert_equal(str(actual), str(expected))

    def test_convert_empty_input(self) -> None:
        """
        Test converting empty input.
        """
        # Prepare inputs.
        lines = []
        # Run test.
        actual = hmarkdo.convert_slide_to_markdown(lines)
        # Check outputs.
        expected = []
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_markdown_to_slide
# #############################################################################


class Test_markdown_to_slide(hunitest.TestCase):
    # TODO(ai): Use helper
    def test_convert_simple_header(self) -> None:
        """
        Test converting a simple h5 header to slide bullet.
        """
        lines = ["##### This is a slide title"]
        expected = ["* This is a slide title"]
        actual = hmarkdo.markdown_to_slide(lines)
        self.assert_equal(str(actual), str(expected))

    # TODO(ai): Use helper
    def test_convert_multiple_headers(self) -> None:
        """
        Test converting multiple h5 headers.
        """
        lines = [
            "##### First slide",
            "  - Some content",
            "##### Second slide", 
            "  - More content"
        ]
        expected = [
            "* First slide",
            "  - Some content",
            "* Second slide",
            "  - More content"
        ]
        actual = hmarkdo.markdown_to_slide(lines)
        self.assertEqual(actual, expected)

    def test_convert_mixed_content(self) -> None:
        """
        Test converting headers mixed with other content.
        """
        lines = [
            "Some intro text",
            "##### Slide title",
            "  - Point 1",
            "  - Point 2",
            "Regular markdown text",
            "##### Another slide"
        ]
        expected = [
            "Some intro text",
            "* Slide title", 
            "  - Point 1",
            "  - Point 2",
            "Regular markdown text",
            "* Another slide"
        ]
        actual = hmarkdo.markdown_to_slide(lines)
        self.assert_equal(str(actual), str(expected))

    def test_convert_no_h5_headers(self) -> None:
        """
        Test converting text with no h5 headers.
        """
        lines = [
            "Regular text",
            "# H1 header",
            "## H2 header",
            "#### H4 header"
        ]
        expected = [
            "Regular text",
            "# H1 header", 
            "## H2 header",
            "#### H4 header"
        ]
        actual = hmarkdo.markdown_to_slide(lines)
        self.assertEqual(actual, expected)

    def test_convert_empty_input(self) -> None:
        """
        Test converting empty input.
        """
        lines = []
        expected = []
        actual = hmarkdo.markdown_to_slide(lines)
        self.assertEqual(actual, expected)

    def test_roundtrip_conversion(self) -> None:
        """
        Test that converting slide to markdown and back gives original result.
        """
        original_lines = [
            "* First slide",
            "  - Some content",
            "* Second slide",
            "Regular text"
        ]
        # Convert to markdown and back
        markdown_lines = hmarkdo.convert_slide_to_markdown(original_lines)
        roundtrip_lines = hmarkdo.markdown_to_slide(markdown_lines)
        self.assert_equal(str(roundtrip_lines), str(original_lines))
