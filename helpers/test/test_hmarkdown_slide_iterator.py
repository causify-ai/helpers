"""
Unit tests for hmarkdown_slide_iterator.
"""

import os
from typing import List

import helpers.hio as hio
import helpers.hmarkdown_slide_iterator as hmaslite
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# Test_iterate_slide_lines
# #############################################################################


class Test_iterate_slide_lines(hunitest.TestCase):
    """
    Tests for `hmarkdown_slide_iterator.iterate_slide_lines()` function.
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
        items = list(hmaslite.iterate_slide_lines(split_lines))
        actual_string = hmaslite.format_items_as_string(items)
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
    Tests for `hmarkdown_slide_iterator.read_lesson_file()` function with actual files.
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
        items = list(hmaslite.read_lesson_file(lesson_file))
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
# Test_reassemble_from_items
# #############################################################################


class Test_reassemble_from_items(hunitest.TestCase):
    """
    Tests for `hmarkdown_slide_iterator.reassemble_from_items()` function.
    """

    def helper(
        self,
        lines: str,
    ) -> None:
        """
        Test helper to verify items match expected string representation.

        Converts SlideItem list into a formatted string and compares with
        expected output for golden file testing.

        :param lines: Markdown lines to parse
        :param expected_string: Expected string representation of items
        """
        split_lines = hprint.dedent(lines).splitlines()
        items = list(hmaslite.iterate_slide_lines(split_lines))
        actual_string = hmaslite.reassemble_from_items(items)
        self.assertEqual(actual_string, lines)

    def test1(self) -> None:
        """
        Test reassembly of empty item list.
        """
        lines = ""
        self.helper(lines)

    def test2(self) -> None:
        """
        Test reassembly of a single slide.
        """
        lines = hprint.dedent("""
            * Slide 1
            Content
            """)
        self.helper(lines)

    def test3(self) -> None:
        """
        Test reassembly of multiple items.
        """
        lines = hprint.dedent("""
            # Title
            Introduction
            * Slide 1
            Content
            """)
        self.helper(lines)

    def test4(self) -> None:
        """
        Test that empty lines are preserved.
        """
        lines = hprint.dedent("""
            * Slide 1
            Content.

            * Slide 2
            More
            """)
        self.helper(lines)

    def test5(self) -> None:
        """
        Test reassembly with comment blocks.
        """
        lines = hprint.dedent("""
            * Slide 1
            Content
            <!-- Comment
            spanning lines
            -->
            * Slide 2
            More
            """)
        self.helper(lines)

    def test6(self) -> None:
        """
        Test reassembly with preamble content.
        """
        lines = hprint.dedent("""
            ::: columns
            :::: {.column}
            Text
            * Slide 1
            Content
            """)
        self.helper(lines)

    def test7(self) -> None:
        """
        Test round-trip: content -> items -> reassembled content.
        """
        lines = hprint.dedent("""
            # Title
            Intro
            * Slide 1
            Content
            * Slide 2
            More
            """)
        self.helper(lines)

    def test8(self) -> None:
        """
        Test reassembly with lines containing only spaces.
        """
        # Prepare inputs.
        split_lines = [
            "* Slide 1",
            "Content",
            "   ",
            "* Slide 2",
            "More",
        ]
        # Run test.
        items = list(hmaslite.iterate_slide_lines(split_lines))
        actual_string = hmaslite.reassemble_from_items(items)
        # Check outputs.
        expected = "* Slide 1\nContent\n   \n* Slide 2\nMore"
        self.assertEqual(actual_string, expected)

    def test9(self) -> None:
        """
        Test reassembly with trailing spaces on lines.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
            Content with trailing spaces
            * Slide 2
            """)
        # Run test.
        self.helper(lines)

    def test10(self) -> None:
        """
        Test reassembly with leading spaces in content.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
               Indented content
                  More indented
            * Slide 2
            """)
        # Run test.
        self.helper(lines)

    def test11(self) -> None:
        """
        Test reassembly with multiple consecutive empty lines.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
            Content



            * Slide 2
            More
            """)
        # Run test.
        self.helper(lines)

    def test12(self) -> None:
        """
        Test reassembly with tabs and spaces mixed.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
            \tTabbed content
              Spaced content
            \t  Mixed indent
            * Slide 2
            """)
        # Run test.
        self.helper(lines)

    def test13(self) -> None:
        """
        Test reassembly with header lines containing multiple spaces.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            # Title   with    multiple    spaces
            Content
            ## Subtitle  with  spaces
            """)
        # Run test.
        self.helper(lines)

    def test14(self) -> None:
        """
        Test reassembly with lines containing varying spaces.
        """
        # Prepare inputs.
        split_lines = [
            "* Slide 1",
            " ",
            "Content",
            "  ",
            "More content",
            "   ",
            "* Slide 2",
        ]
        # Run test.
        items = list(hmaslite.iterate_slide_lines(split_lines))
        actual_string = hmaslite.reassemble_from_items(items)
        # Check outputs.
        expected = "* Slide 1\n \nContent\n  \nMore content\n   \n* Slide 2"
        self.assertEqual(actual_string, expected)

    def test15(self) -> None:
        """
        Test reassembly with code block indentation.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
            Code example:
                def hello():
                    return 'world'
            * Slide 2
            """)
        # Run test.
        self.helper(lines)

    def test16(self) -> None:
        """
        Test reassembly with trailing spaces at end of lines.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
            Text line
            Another line
            * Slide 2
            """)
        # Run test.
        self.helper(lines)

    def test17(self) -> None:
        """
        Test reassembly with special characters and spacing.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
            Content with special chars: !@#$%^&*()
              Spaced special: {a: 1, b: 2}
            * Slide 2
            """)
        # Run test.
        self.helper(lines)

    def test18(self) -> None:
        """
        Test reassembly with nested bullet points.
        """
        # Prepare inputs.
        lines = hprint.dedent("""
            * Slide 1
              - Item 1
              - Item 2
                - Nested item
            * Slide 2
            """)
        # Run test.
        self.helper(lines)
