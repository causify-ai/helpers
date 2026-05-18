"""
Unit tests for hmarkdown_lesson_iterator.
"""

import os
from typing import List, Optional

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
from helpers.hmarkdown_lesson_iterator import (
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

    def _check_slide_items(
        self,
        items: List[SlideItem],
        *,
        expected_string: str,
    ) -> None:
        """
        Test helper to verify items match expected string representation.

        Converts SlideItem list into a formatted string and compares with
        expected output for golden file testing.

        :param items: List of items to check
        :param expected_string: Expected string representation of items
        """
        actual_string = self._format_items_as_string(items)
        self.assertEqual(actual_string, expected_string)

    def _format_items_as_string(self, items: List[SlideItem]) -> str:
        """
        Format SlideItem list as a human-readable string.

        :param items: List of SlideItem dicts to format
        :return: Formatted string representation
        """
        lines = []
        for item in items:
            item_type = item["type"]
            line_number = item["line_number"]
            content = item["content"]
            lines.append(f"type={item_type}, line_number={line_number}:")
            for content_line in content:
                lines.append(f"  {content_line}")
        return "\n".join(lines)

    # TODO(ai_gp): Delete this function and replace the calls to this function with calls to
    # _check_slide_items
    def _check_single_item_type(
        self,
        items: List[SlideItem],
        expected_type: str,
        *,
        expected_line_number: int = 1,
        expected_content: Optional[List[str]] = None,
    ) -> None:
        """
        Test helper to verify a single item's type, line number, and optionally content.

        :param items: List of items to check
        :param expected_type: Expected item type (e.g., 'slide', 'header', 'comment')
        :param expected_line_number: Expected line number (default: 1)
        :param expected_content: Expected content lines (optional)
        """
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["type"], expected_type)
        self.assertEqual(items[0]["line_number"], expected_line_number)
        if expected_content is not None:
            self.assertEqual(items[0]["content"], expected_content)

    # TODO(ai_gp): Delete this function and replace the calls to this function with calls to
    # _check_slide_items
    def _check_items_with_line_numbers(
        self, items: List[SlideItem], *, expected_specs: List[tuple]
    ) -> None:
        """
        Test helper to verify items have expected types and line numbers.

        :param items: List of items to check
        :param expected_specs: List of (expected_type, expected_line_number) tuples
        """
        self.assertEqual(len(items), len(expected_specs))
        for i, (expected_type, expected_line_num) in enumerate(expected_specs):
            self.assertEqual(items[i]["type"], expected_type)
            self.assertEqual(items[i]["line_number"], expected_line_num)

    # TODO(ai_gp): Delete this function and replace the calls to this function with calls to
    # _check_slide_items
    def _check_types_list(
        self, items: List[SlideItem], *, expected_types: List[str]
    ) -> None:
        """
        Test helper to verify items' types match expected list.

        :param items: List of items to check
        :param expected_types: Expected list of item types
        """
        actual_types = [item["type"] for item in items]
        self.assertEqual(actual_types, expected_types)

    def test1(self) -> None:
        """
        Test behavior with empty file.
        """
        # Prepare inputs.
        lines: List[str] = []
        # Run test.
        items = list(_iterate_slide_lines(lines))
        # Check outputs.
        self.assertEqual(items, [])

    def test2(self) -> None:
        """
        Test extraction of a single slide.
        """
        lines = hprint.dedent("""
            * First Slide
            Content of the slide
            """).splitlines()
        expected_content = hprint.dedent("""
            * First Slide
            Content of the slide
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self._check_single_item_type(
            items, expected_type="slide", expected_content=expected_content
        )

    def test3(self) -> None:
        """
        Test extraction of multiple slides.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1",
            "Content 1",
            "* Slide 2",
            "Content 2",
        ]
        expected_specs = [("slide", 1), ("slide", 3)]
        # Run test.
        items = list(_iterate_slide_lines(lines))
        # Check outputs.
        self._check_items_with_line_numbers(items, expected_specs=expected_specs)

    def test4(self) -> None:
        """
        Test extraction of a single header.
        """
        lines = hprint.dedent("""
            # Main Title
            Some content
            """).splitlines()
        expected_content = hprint.dedent("""
            # Main Title
            Some content
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self._check_single_item_type(
            items, expected_type="header", expected_content=expected_content
        )

    def test5(self) -> None:
        """
        Test extraction of multiple headers with different levels.
        """
        lines = hprint.dedent("""
            # Title 1
            Content
            ## Subtitle
            More content
            ### Sub-subtitle
            """).splitlines()
        expected_specs = [("header", 1), ("header", 3), ("header", 5)]
        items = list(_iterate_slide_lines(lines))
        self._check_items_with_line_numbers(items, expected_specs=expected_specs)

    def test6(self) -> None:
        """
        Test extraction of HTML comment blocks.
        """
        lines = hprint.dedent("""
            Some content
            <!-- This is a comment
            spanning multiple lines
            -->
            More content
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self._check_single_item_type(
            items, expected_type="comment", expected_line_number=2
        )
        self.assertIn("This is a comment", items[0]["content"][0])

    def test7(self) -> None:
        """
        Test extraction of CSS/JavaScript comment blocks.
        """
        lines = hprint.dedent("""
            Some content
            /* This is a comment
            spanning multiple lines
            */
            More content
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self._check_single_item_type(
            items, expected_type="comment", expected_line_number=2
        )

    def test8(self) -> None:
        """
        Test handling of single-line HTML comments.
        """
        lines = hprint.dedent("""
            Content before
            <!-- Single line comment -->
            Content after
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self._check_single_item_type(
            items, expected_type="comment", expected_line_number=2
        )

    def test9(self) -> None:
        """
        Test file with mixed slides, headers, and comments.
        """
        lines = hprint.dedent("""
            # Main Title
            Introduction
            * Slide 1
            Slide content
            <!-- Comment -->
            * Slide 2
            ## Subsection
            More content
            """).splitlines()
        expected_types = ["header", "slide", "comment", "slide", "header"]
        items = list(_iterate_slide_lines(lines))
        self._check_types_list(items, expected_types=expected_types)

    def test10(self) -> None:
        """
        Test that single-line comments are grouped with surrounding slide.
        """
        lines = hprint.dedent("""
            * Slide Title
            Content line 1
            // Single line comment
            Content line 2
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self._check_single_item_type(items, expected_type="slide")
        self.assertIn("// Single line comment", items[0]["content"])

    def test11(self) -> None:
        """
        Test handling of %% single-line comments.
        """
        lines = hprint.dedent("""
            * Slide Title
            %% This is a comment
            Regular content
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self._check_single_item_type(items, expected_type="slide")

    def test12(self) -> None:
        """
        Test handling of markdown line separators.
        """
        lines = (
            hprint.dedent("""
            * Slide 1
            Content
            """).splitlines()
            + ["#" * 80]
            + hprint.dedent("""
            More content
            """).splitlines()
        )
        items = list(_iterate_slide_lines(lines))
        self.assertEqual(len(items), 1)
        self.assertIn("#" * 80, items[0]["content"])

    def test13(self) -> None:
        """
        Test that line numbers are correctly tracked.
        """
        lines = hprint.dedent("""
            * Slide 1
            Content
            * Slide 2
            Content 2
            * Slide 3
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        line_numbers = [item["line_number"] for item in items]
        self.assertEqual(line_numbers, [1, 3, 5])

    def test14(self) -> None:
        """
        Test handling of empty lines between items.
        """
        lines = hprint.dedent("""
            * Slide 1
            Content

            * Slide 2
            Content 2
            """).splitlines()
        items = list(_iterate_slide_lines(lines))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["type"], "slide")
        self.assertEqual(items[1]["type"], "slide")

    def test15(self) -> None:
        """
        Test parsing of complex file with mixed content.
        """
        lines = hprint.dedent("""
            # Introduction
            This is an introduction
            * What is AI?
            Artificial Intelligence overview
            <!-- Hidden notes for instructor -->
            * Machine Learning Basics
            ## Key Concepts
            // Internal comment
            Definition of ML
            """).splitlines()
        expected_types = ["header", "slide", "comment", "slide", "header"]
        items = list(_iterate_slide_lines(lines))
        self._check_types_list(items, expected_types=expected_types)


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


class TestReassembleFromItems(hunitest.TestCase):
    """
    Tests for `reassemble_from_items()` function.
    """

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
        items = [
            {
                "type": "slide",
                "content": ["* Slide 1", "Content"],
                "line_number": 1,
            }
        ]
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        self.assertEqual(result, "* Slide 1\nContent")

    def test_multiple_items(self) -> None:
        """
        Test reassembly of multiple items.
        """
        # Prepare inputs.
        items = [
            {
                "type": "header",
                "content": ["# Title", "Introduction"],
                "line_number": 1,
            },
            {
                "type": "slide",
                "content": ["* Slide 1", "Content"],
                "line_number": 3,
            },
        ]
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        expected = "# Title\nIntroduction\n* Slide 1\nContent"
        self.assertEqual(result, expected)

    def test_preserve_empty_lines(self) -> None:
        """
        Test that empty lines are preserved.
        """
        # Prepare inputs.
        items = [
            {
                "type": "slide",
                "content": ["* Slide 1", "Content.", ""],
                "line_number": 1,
            },
            {
                "type": "slide",
                "content": ["* Slide 2", "More"],
                "line_number": 4,
            },
        ]
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        expected = "* Slide 1\nContent.\n\n* Slide 2\nMore"
        self.assertEqual(result, expected)

    def test_single_trailing_newline(self) -> None:
        """
        Test preservation of single trailing newline.
        """
        # Prepare inputs.
        items = [
            {
                "type": "slide",
                "content": ["* Slide", "Content"],
                "line_number": 1,
            }
        ]
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
        items = [
            {
                "type": "slide",
                "content": ["* Slide", "Content"],
                "line_number": 1,
            }
        ]
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
        items = [
            {
                "type": "slide",
                "content": ["* Slide", "Content"],
                "line_number": 1,
            }
        ]
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
            {
                "type": "slide",
                "content": ["* Slide 1", "Content"],
                "line_number": 1,
            },
            {
                "type": "comment",
                "content": ["<!-- Comment", "spanning lines", "-->"],
                "line_number": 3,
            },
            {
                "type": "slide",
                "content": ["* Slide 2", "More"],
                "line_number": 6,
            },
        ]
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        expected = (
            "* Slide 1\nContent\n<!-- Comment\nspanning lines\n-->\n"
            "* Slide 2\nMore"
        )
        self.assertEqual(result, expected)

    def test_with_preamble(self) -> None:
        """
        Test reassembly with preamble content.
        """
        # Prepare inputs.
        items = [
            {
                "type": "preamble",
                "content": ["::: columns", ":::: {.column}", "Text"],
                "line_number": 1,
            },
            {
                "type": "slide",
                "content": ["* Slide 1", "Content"],
                "line_number": 4,
            },
        ]
        # Run test.
        result = reassemble_from_items(items)
        # Check outputs.
        expected = "::: columns\n:::: {.column}\nText\n* Slide 1\nContent"
        self.assertEqual(result, expected)

    def test_round_trip_simple(self) -> None:
        """
        Test round-trip: content -> items -> reassembled content.
        """
        # Prepare inputs.
        original_content = (
            "# Title\nIntro\n* Slide 1\nContent\n* Slide 2\nMore\n"
        )
        # Simulate parsed items from the content.
        items = [
            {
                "type": "header",
                "content": ["# Title", "Intro"],
                "line_number": 1,
            },
            {
                "type": "slide",
                "content": ["* Slide 1", "Content"],
                "line_number": 3,
            },
            {
                "type": "slide",
                "content": ["* Slide 2", "More"],
                "line_number": 5,
            },
        ]
        # Run test.
        result = reassemble_from_items(items, original_content=original_content)
        # Check outputs.
        self.assertEqual(result, original_content)
