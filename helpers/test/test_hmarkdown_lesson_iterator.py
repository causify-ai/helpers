"""
Unit tests for hmarkdown_lesson_iterator.
"""

import os
from typing import List

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
from helpers.hmarkdown_lesson_iterator import (
    _format_items_as_string,
    _iterate_slide_lines,
    SlideItem,
    read_lesson_file,
    reassemble_from_items,
)

# #############################################################################
# Test_iterate_slide_lines
# #############################################################################


class Test_iterate_slide_lines(hunitest.TestCase):
    """
    Tests for `_iterate_slide_lines()` function.
    """

    def helper(
        self,
        lines: str,
        expected_string: str,
    ) -> None:
        """
        Test helper to verify items match expected string representation.

        Converts SlideItem list into a formatted string and compares with
        expected output for golden file testing.

        :param lines: Markdown lines to parse
        :param expected_string: Expected string representation of items
        """
        split_lines = hprint.dedent(lines).splitlines()
        items = list(_iterate_slide_lines(split_lines))
        actual_string = _format_items_as_string(items)
        expected_string = hprint.dedent(expected_string)
        self.assertEqual(actual_string, expected_string)

    def test1(self) -> None:
        """
        Test behavior with empty file.
        """
        lines = ""
        expected_string = ""
        self.helper(lines, expected_string=expected_string)

    def test2(self) -> None:
        """
        Test extraction of a single slide.
        """
        lines = """
            * First Slide
            Content of the slide
            """
        expected_string = """
            type=slide, line_number=1:
              * First Slide
              Content of the slide
            """
        self.helper(lines, expected_string=expected_string)

    def test3(self) -> None:
        """
        Test extraction of multiple slides.
        """
        lines = """
            * Slide 1
            Content 1
            * Slide 2
            Content 2
            """
        expected_string = """
            type=slide, line_number=1:
              * Slide 1
              Content 1
            type=slide, line_number=3:
              * Slide 2
              Content 2
            """
        self.helper(lines, expected_string=expected_string)

    def test4(self) -> None:
        """
        Test extraction of a single header.
        """
        lines = """
            # Main Title
            Some content
            """
        expected_string = """
            type=header, line_number=1:
              # Main Title
              Some content
            """
        self.helper(lines, expected_string=expected_string)

    def test5(self) -> None:
        """
        Test extraction of multiple headers with different levels.
        """
        lines = """
            # Title 1
            Content
            ## Subtitle
            More content
            ### Sub-subtitle
            """
        expected_string = """
            type=header, line_number=1:
              # Title 1
              Content
            type=header, line_number=3:
              ## Subtitle
              More content
            type=header, line_number=5:
              ### Sub-subtitle
            """
        self.helper(lines, expected_string=expected_string)

    def test6(self) -> None:
        """
        Test extraction of HTML comment blocks.
        """
        lines = """
            Some content
            <!-- This is a comment
            spanning multiple lines
            -->
            More content
            """
        expected_string = """
            type=preamble, line_number=1:
              Some content
            type=comment, line_number=2:
              <!-- This is a comment
              spanning multiple lines
              -->
            type=preamble, line_number=5:
              More content
            """
        self.helper(lines, expected_string=expected_string)

    def test7(self) -> None:
        """
        Test extraction of CSS/JavaScript comment blocks.
        """
        lines = """
            Some content
            /* This is a comment
            spanning multiple lines
            */
            More content
            """
        expected_string = """
            type=preamble, line_number=1:
              Some content
            type=comment, line_number=2:
              /* This is a comment
              spanning multiple lines
              */
            type=preamble, line_number=5:
              More content
            """
        self.helper(lines, expected_string=expected_string)

    def test8(self) -> None:
        """
        Test handling of single-line HTML comments.
        """
        lines = """
            Content before
            <!-- Single line comment -->
            Content after
            """
        expected_string = """
            type=preamble, line_number=1:
              Content before
            type=comment, line_number=2:
              <!-- Single line comment -->
            type=preamble, line_number=3:
              Content after
            """
        self.helper(lines, expected_string=expected_string)

    def test9(self) -> None:
        """
        Test file with mixed slides, headers, and comments.
        """
        lines = """
            # Main Title
            Introduction
            * Slide 1
            Slide content
            <!-- Comment -->
            * Slide 2
            ## Subsection
            More content
            """
        expected_string = """
            type=header, line_number=1:
              # Main Title
              Introduction
            type=slide, line_number=3:
              * Slide 1
              Slide content
            type=comment, line_number=5:
              <!-- Comment -->
            type=slide, line_number=6:
              * Slide 2
            type=header, line_number=7:
              ## Subsection
              More content
            """
        self.helper(lines, expected_string=expected_string)

    def test10(self) -> None:
        """
        Test that single-line comments are grouped with surrounding slide.
        """
        lines = """
            * Slide Title
            Content line 1
            // Single line comment
            Content line 2
            """
        expected_string = """
            type=slide, line_number=1:
              * Slide Title
              Content line 1
              // Single line comment
              Content line 2
            """
        self.helper(lines, expected_string=expected_string)

    def test11(self) -> None:
        """
        Test handling of %% single-line comments.
        """
        lines = """
            * Slide Title
            %% This is a comment
            Regular content
            """
        expected_string = """
            type=slide, line_number=1:
              * Slide Title
              %% This is a comment
              Regular content
            """
        self.helper(lines, expected_string=expected_string)

    def test12(self) -> None:
        """
        Test handling of markdown line separators.
        """
        separator = "#" * 80
        lines = f"""
            * Slide 1
            Content
            {separator}
            More content
            """
        expected_string = (
            "type=slide, line_number=1:\n"
            "  * Slide 1\n"
            "  Content\n"
            "  " + separator + "\n"
            "  More content"
        )
        self.helper(lines, expected_string=expected_string)

    def test13(self) -> None:
        """
        Test that line numbers are correctly tracked.
        """
        lines = """
            * Slide 1
            Content
            * Slide 2
            Content 2
            * Slide 3
            """
        expected_string = """
            type=slide, line_number=1:
              * Slide 1
              Content
            type=slide, line_number=3:
              * Slide 2
              Content 2
            type=slide, line_number=5:
              * Slide 3
            """
        self.helper(lines, expected_string=expected_string)

    def test14(self) -> None:
        """
        Test handling of empty lines between items.
        """
        lines = """
            * Slide 1
            Content

            * Slide 2
            Content 2
            """
        expected_string = """
            type=slide, line_number=1:
              * Slide 1
              Content

            type=slide, line_number=4:
              * Slide 2
              Content 2
            """
        self.helper(lines, expected_string=expected_string)

    def test15(self) -> None:
        """
        Test parsing of complex file with mixed content.
        """
        lines = """
            # Introduction
            This is an introduction
            * What is AI?
            Artificial Intelligence overview
            <!-- Hidden notes for instructor -->
            * Machine Learning Basics
            ## Key Concepts
            // Internal comment
            Definition of ML
            """
        expected_string = """
            type=header, line_number=1:
              # Introduction
              This is an introduction
            type=slide, line_number=3:
              * What is AI?
              Artificial Intelligence overview
            type=comment, line_number=5:
              <!-- Hidden notes for instructor -->
            type=slide, line_number=6:
              * Machine Learning Basics
            type=header, line_number=7:
              ## Key Concepts
              // Internal comment
              Definition of ML
            """
        self.helper(lines, expected_string=expected_string)


# #############################################################################
# Test_read_lesson_file
# #############################################################################


class Test_read_lesson_file(hunitest.TestCase):
    """
    Tests for `read_lesson_file()` function with actual files.
    """

    def _check_file_content(
        self, content: str, *, expected_count: int, expected_types: List[str]
    ) -> None:
        """
        Test helper to write content to file, read it, and verify structure.

        :param content: Content to write to file
        :param expected_count: Expected number of items
        :param expected_types: Expected list of item types
        """
        input_dir = self.get_input_dir()
        lesson_file = os.path.join(input_dir, "test_lesson.txt")
        hio.to_file(lesson_file, content)
        items = list(read_lesson_file(lesson_file))
        self.assertEqual(len(items), expected_count)
        actual_types = [item["type"] for item in items]
        self.assertEqual(actual_types, expected_types)

    def test1(self) -> None:
        """
        Test reading a simple lesson file from disk.
        """
        content = hprint.dedent("""
            * Slide 1
            Content
            * Slide 2
            More content
            """)
        expected_types = ["slide", "slide"]
        self._check_file_content(
            content, expected_count=2, expected_types=expected_types
        )

    def test2(self) -> None:
        """
        Test reading a lesson file with headers.
        """
        content = hprint.dedent("""
            # Title
            ## Subtitle
            * Slide
            Content
            """)
        expected_types = ["header", "header", "slide"]
        self._check_file_content(
            content, expected_count=3, expected_types=expected_types
        )


# #############################################################################
# TestReassembleFromItems
# #############################################################################


class Test_reassemble_from_items(hunitest.TestCase):
    """
    Tests for `reassemble_from_items()` function.
    """

    def _make_item(
        self,
        item_type: str,
        content: List[str],
        *,
        line_number: int = 1,
    ) -> SlideItem:
        """
        Test helper to create a SlideItem dict.

        :param item_type: Item type (e.g., 'slide', 'header', 'comment')
        :param content: Content lines for the item
        :param line_number: Line number where item starts
        :return: SlideItem dict
        """
        return {
            "type": item_type,
            "content": content,
            "line_number": line_number,
        }

    def test_empty_items(self) -> None:
        """
        Test reassembly of empty item list.
        """
        # Prepare inputs.
        items: List[SlideItem] = []
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        self.assertEqual(result, "")

    def test_single_slide(self) -> None:
        """
        Test reassembly of a single slide.
        """
        # Prepare inputs.
        items = [self._make_item("slide", ["* Slide 1", "Content"])]
        expected = "* Slide 1\nContent"
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        self.assertEqual(result, expected)

    def test_multiple_items(self) -> None:
        """
        Test reassembly of multiple items.
        """
        # Prepare inputs.
        items = [
            self._make_item("header", ["# Title", "Introduction"], line_number=1),
            self._make_item("slide", ["* Slide 1", "Content"], line_number=3),
        ]
        expected = "# Title\nIntroduction\n* Slide 1\nContent"
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        self.assertEqual(result, expected)

    def test_preserve_empty_lines(self) -> None:
        """
        Test that empty lines are preserved.
        """
        # Prepare inputs.
        items = [
            self._make_item("slide", ["* Slide 1", "Content.", ""], line_number=1),
            self._make_item("slide", ["* Slide 2", "More"], line_number=4),
        ]
        expected = "* Slide 1\nContent.\n\n* Slide 2\nMore"
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        self.assertEqual(result, expected)

    def test_single_trailing_newline(self) -> None:
        """
        Test preservation of single trailing newline.
        """
        # Prepare inputs.
        items = [self._make_item("slide", ["* Slide", "Content"])]
        original_content = "* Slide\nContent\n"
        # Run test.
        result = reassemble_from_items(items, original_content=original_content)
        # Check outputs.
        self.assertEqual(result, original_content)
        self.assertTrue(result.endswith("\n"))

    def test_multiple_trailing_newlines(self) -> None:
        """
        Test preservation of multiple trailing newlines.
        """
        # Prepare inputs.
        items = [self._make_item("slide", ["* Slide", "Content"])]
        original_content = "* Slide\nContent\n\n"
        # Run test.
        result = reassemble_from_items(items, original_content=original_content)
        # Check outputs.
        self.assertEqual(result, original_content)
        self.assertTrue(result.endswith("\n\n"))

    def test_no_trailing_newline(self) -> None:
        """
        Test handling of content without trailing newline.
        """
        # Prepare inputs.
        items = [self._make_item("slide", ["* Slide", "Content"])]
        original_content = "* Slide\nContent"
        # Run test.
        result = reassemble_from_items(items, original_content=original_content)
        # Check outputs.
        self.assertEqual(result, original_content)
        self.assertFalse(result.endswith("\n"))

    def test_with_comments(self) -> None:
        """
        Test reassembly with comment blocks.
        """
        # Prepare inputs.
        items = [
            self._make_item("slide", ["* Slide 1", "Content"], line_number=1),
            self._make_item(
                "comment",
                ["<!-- Comment", "spanning lines", "-->"],
                line_number=3,
            ),
            self._make_item("slide", ["* Slide 2", "More"], line_number=6),
        ]
        expected = (
            "* Slide 1\nContent\n<!-- Comment\nspanning lines\n-->\n"
            "* Slide 2\nMore"
        )
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        self.assertEqual(result, expected)

    def test_with_preamble(self) -> None:
        """
        Test reassembly with preamble content.
        """
        # Prepare inputs.
        items = [
            self._make_item(
                "preamble",
                ["::: columns", ":::: {.column}", "Text"],
                line_number=1,
            ),
            self._make_item("slide", ["* Slide 1", "Content"], line_number=4),
        ]
        expected = "::: columns\n:::: {.column}\nText\n* Slide 1\nContent"
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        self.assertEqual(result, expected)

    def test_round_trip_simple(self) -> None:
        """
        Test round-trip: content -> items -> reassembled content.
        """
        # Prepare inputs.
        original_content = (
            "# Title\nIntro\n* Slide 1\nContent\n* Slide 2\nMore\n"
        )
        items = [
            self._make_item("header", ["# Title", "Intro"], line_number=1),
            self._make_item("slide", ["* Slide 1", "Content"], line_number=3),
            self._make_item("slide", ["* Slide 2", "More"], line_number=5),
        ]
        # Run test.
        result = reassemble_from_items(items, original_content=original_content)
        # Check outputs.
        self.assertEqual(result, original_content)
