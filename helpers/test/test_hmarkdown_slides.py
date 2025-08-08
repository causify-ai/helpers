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
