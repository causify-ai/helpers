import os
from typing import List, Tuple

import helpers.hio as hio
import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_select as hmarsele
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


def _build_header_list(data: List[Tuple[int, str]]) -> hmarhead.HeaderList:
    """
    Build a HeaderList from a list of (level, title) tuples.

    :param data: List of (level, title) tuples
    :return: HeaderList with line numbers assigned sequentially
    """
    res = [
        hmarhead.HeaderInfo(level, text, 5 * i + 1)
        for i, (level, text) in enumerate(data)
    ]
    return res


# #############################################################################
# Test_parse_select_arg
# #############################################################################


class Test_parse_select_arg(hunitest.TestCase):
    """
    Test --select argument parsing.
    """

    def test1(self) -> None:
        """
        Test parsing with both START and END.
        """
        # Prepare inputs.
        select_str = "## Section 1:## Section 2"
        # Run test.
        start, end = hmarsele.parse_select_arg(select_str)
        # Check outputs.
        self.assertEqual(start, "## Section 1")
        self.assertEqual(end, "## Section 2")

    def test2(self) -> None:
        """
        Test parsing with only END (colon at beginning).
        """
        # Prepare inputs.
        select_str = ":Section 2"
        # Run test.
        start, end = hmarsele.parse_select_arg(select_str)
        # Check outputs.
        self.assertIsNone(start)
        self.assertEqual(end, "Section 2")

    def test3(self) -> None:
        """
        Test parsing with only START (colon at end).
        """
        # Prepare inputs.
        select_str = "Section 1:"
        # Run test.
        start, end = hmarsele.parse_select_arg(select_str)
        # Check outputs.
        self.assertEqual(start, "Section 1")
        self.assertIsNone(end)

    def test4(self) -> None:
        """
        Test parsing with no colon (implies to EOF).
        """
        # Prepare inputs.
        select_str = "Section 1"
        # Run test.
        start, end = hmarsele.parse_select_arg(select_str)
        # Check outputs.
        self.assertEqual(start, "Section 1")
        self.assertEqual(end, "END")


# #############################################################################
# Test_parse_header_string
# #############################################################################


class Test_parse_header_string(hunitest.TestCase):
    """
    Test header string parsing.
    """

    def test1(self) -> None:
        """
        Test parsing a level-2 header.
        """
        # Prepare inputs.
        header_str = "## Section Title"
        # Run test.
        level, title = hmarsele.parse_header_string(header_str)
        # Check outputs.
        self.assertEqual(level, 2)
        self.assertEqual(title, "Section Title")

    def test2(self) -> None:
        """
        Test parsing a level-1 header.
        """
        # Prepare inputs.
        header_str = "# Chapter 1"
        # Run test.
        level, title = hmarsele.parse_header_string(header_str)
        # Check outputs.
        self.assertEqual(level, 1)
        self.assertEqual(title, "Chapter 1")

    def test3(self) -> None:
        """
        Test parsing a level-5 header.
        """
        # Prepare inputs.
        header_str = "##### Slide Title"
        # Run test.
        level, title = hmarsele.parse_header_string(header_str)
        # Check outputs.
        self.assertEqual(level, 5)
        self.assertEqual(title, "Slide Title")


# #############################################################################
# Test_find_header_by_title
# #############################################################################


class Test_find_header_by_title(hunitest.TestCase):
    """
    Test exact header title matching.
    """

    def test1(self) -> None:
        """
        Test finding a header by exact title match.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
            ]
        )
        target_title = "Section 1.1"
        # Run test.
        result = hmarsele.find_header_by_title(header_list, target_title)
        # Check outputs.
        self.assertIsNotNone(result)
        self.assertEqual(result.description, "Section 1.1")
        self.assertEqual(result.level, 2)

    def test2(self) -> None:
        """
        Test finding a header that does not exist.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        target_title = "Nonexistent"
        # Run test.
        result = hmarsele.find_header_by_title(header_list, target_title)
        # Check outputs.
        self.assertIsNone(result)


# #############################################################################
# Test_find_header_by_partial_title
# #############################################################################


class Test_find_header_by_substring_title(hunitest.TestCase):
    """
    Test substring header title matching.
    """

    def test1(self) -> None:
        """
        Test finding a header by substring anywhere in title.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "My Chapter 2"),
                (2, "Chapter 2 Intro"),
            ]
        )
        substring = "Chapter 2"
        # Run test and check output (multiple matches).
        with self.assertRaises(AssertionError) as cm:
            hmarsele.find_header_by_substring_title(header_list, substring)
        self.assertIn("multiple headers", str(cm.exception))

    def test2(self) -> None:
        """
        Test finding header with unique substring.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "My Section 1"),
                (2, "My Section 2"),
            ]
        )
        substring = "My Section 2"
        # Run test.
        result = hmarsele.find_header_by_substring_title(
            header_list, substring
        )
        # Check outputs.
        self.assertIsNotNone(result)
        self.assertEqual(result.description, "My Section 2")

    def test3(self) -> None:
        """
        Test substring not found.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1"),
            ]
        )
        substring = "Nonexistent"
        # Run test.
        result = hmarsele.find_header_by_substring_title(
            header_list, substring
        )
        # Check outputs.
        self.assertIsNone(result)


# TODO(ai_gp): Run skill /coding.factor_common_code
class Test_find_header_by_level_and_prefix(hunitest.TestCase):
    """
    Test level-exact and prefix matching.
    """

    def test1(self) -> None:
        """
        Test finding header by exact level and prefix match.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
            ]
        )
        # Run test.
        result = hmarsele.find_header_by_level_and_prefix(
            header_list, 2, "Section 1.1"
        )
        # Check outputs.
        self.assertIsNotNone(result)
        self.assertEqual(result.description, "Section 1.1")

    def test2(self) -> None:
        """
        Test level mismatch returns None.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        # Run test (level 1 doesn't match level 2 header).
        result = hmarsele.find_header_by_level_and_prefix(
            header_list, 1, "Section"
        )
        # Check outputs.
        self.assertIsNone(result)

    def test3(self) -> None:
        """
        Test multiple level-exact prefix matches raises error.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
            ]
        )
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hmarsele.find_header_by_level_and_prefix(
                header_list, 2, "Section"
            )
        self.assertIn("multiple headers", str(cm.exception))


class Test_find_header_by_partial_title(hunitest.TestCase):
    """
    Test partial header title matching.
    """

    def test1(self) -> None:
        """
        Test finding a header by unique partial title match.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
            ]
        )
        partial_title = "Section 1.1"
        # Run test.
        result = hmarsele.find_header_by_partial_title(
            header_list, partial_title
        )
        # Check outputs.
        self.assertIsNotNone(result)
        self.assertEqual(result.description, "Section 1.1")

    def test2(self) -> None:
        """
        Test finding a header by partial prefix match.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
            ]
        )
        partial_title = "Section"
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hmarsele.find_header_by_partial_title(header_list, partial_title)
        self.assertIn("multiple headers", str(cm.exception))

    def test3(self) -> None:
        """
        Test finding a header that does not match.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        partial_title = "Nonexistent"
        # Run test.
        result = hmarsele.find_header_by_partial_title(
            header_list, partial_title
        )
        # Check outputs.
        self.assertIsNone(result)

    def test4(self) -> None:
        """
        Test finding a header by unique partial match that is a prefix.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
            ]
        )
        partial_title = "Chapter"
        # Run test.
        result = hmarsele.find_header_by_partial_title(
            header_list, partial_title
        )
        # Check outputs.
        self.assertIsNotNone(result)
        self.assertEqual(result.description, "Chapter 1")


# #############################################################################
# Test_find_header_from_input
# #############################################################################


class Test_find_header_from_input(hunitest.TestCase):
    """
    Test unified header finding from user input.
    """

    def test1(self) -> None:
        """
        Test finding header from full format input.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
            ]
        )
        header_input = "## Section 1.1"
        # Run test.
        result, level = hmarsele.find_header_from_input(
            header_list, header_input
        )
        # Check outputs.
        self.assertEqual(result.description, "Section 1.1")
        self.assertEqual(level, 2)

    def test2(self) -> None:
        """
        Test finding header from partial title input.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        header_input = "Chapter"
        # Run test.
        result, level = hmarsele.find_header_from_input(
            header_list, header_input
        )
        # Check outputs.
        self.assertEqual(result.description, "Chapter 1")
        self.assertEqual(level, 1)

    def test3(self) -> None:
        """
        Test header not found raises error.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        header_input = "Nonexistent"
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hmarsele.find_header_from_input(header_list, header_input)

    def test4(self) -> None:
        """
        Test finding header with full format (level must match exactly).
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        header_input = "## Section 1.1"
        # Run test (level must match exactly).
        result, level = hmarsele.find_header_from_input(
            header_list, header_input
        )
        # Check outputs.
        self.assertEqual(result.description, "Section 1.1")
        self.assertEqual(level, 2)

    def test5(self) -> None:
        """
        Test finding header with line number.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        header_input = "6"
        # Run test (6 is the line number for second header: 5*1+1=6).
        result, level = hmarsele.find_header_from_input(
            header_list, header_input
        )
        # Check outputs.
        self.assertEqual(result.description, "Section 1.1")
        self.assertEqual(level, 2)

    def test6(self) -> None:
        """
        Test finding header with substring (no # prefix).
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "My Section 1"),
                (2, "My Other"),
            ]
        )
        header_input = "Section"
        # Run test.
        result, level = hmarsele.find_header_from_input(
            header_list, header_input
        )
        # Check outputs.
        self.assertEqual(result.description, "My Section 1")
        self.assertEqual(level, 2)


# #############################################################################
# Test_find_end_line
# #############################################################################


class Test_find_end_line(hunitest.TestCase):
    """
    Test end-line boundary detection.
    """

    def test1(self) -> None:
        """
        Test finding end line with explicit end header.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
                (1, "Chapter 2"),
            ]
        )
        start_header = header_list[1]
        end_header_input = "## Section 1.2"
        # Run test.
        end_line = hmarsele.find_end_line(
            header_list, start_header, end_header_input
        )
        # Check outputs.
        self.assertEqual(end_line, header_list[2].line_number - 1)

    def test2(self) -> None:
        """
        Test auto-detecting end line at next same-level header.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (2, "Section 1.2"),
                (1, "Chapter 2"),
            ]
        )
        start_header = header_list[1]
        end_header_input = None
        # Run test.
        end_line = hmarsele.find_end_line(
            header_list, start_header, end_header_input
        )
        # Check outputs.
        self.assertEqual(end_line, header_list[2].line_number - 1)

    def test3(self) -> None:
        """
        Test end line is None when no next same-level header.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (3, "Subsection 1.1.1"),
            ]
        )
        start_header = header_list[1]
        end_header_input = None
        # Run test.
        end_line = hmarsele.find_end_line(
            header_list, start_header, end_header_input
        )
        # Check outputs.
        self.assertIsNone(end_line)

    def test4(self) -> None:
        """
        Test end line stops at higher-level header.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
                (3, "Subsection 1.1.1"),
                (1, "Chapter 2"),
            ]
        )
        start_header = header_list[1]
        end_header_input = None
        # Run test.
        end_line = hmarsele.find_end_line(
            header_list, start_header, end_header_input
        )
        # Check outputs.
        self.assertEqual(end_line, header_list[3].line_number - 1)


# #############################################################################
# Test_extract_text_from_markdown_lines
# #############################################################################


class Test_get_chunk_bounds(hunitest.TestCase):
    """
    Test chunk boundary computation.
    """

    def test1(self) -> None:
        """
        Test getting bounds for explicit START and END.
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",
            "Intro",
            "",
            "## Section 1.1",
            "Content",
            "",
            "## Section 1.2",
            "More",
        ]
        # Run test.
        start_idx, end_idx = hmarsele.get_chunk_bounds(
            lines, "Section 1.1", "Section 1.2"
        )
        # Check outputs.
        self.assertEqual(start_idx, 3)
        self.assertEqual(end_idx, 6)

    def test2(self) -> None:
        """
        Test getting bounds with no end (next same-level).
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",
            "Intro",
            "",
            "## Section 1.1",
            "Content",
            "",
            "## Section 1.2",
            "More",
        ]
        # Run test.
        start_idx, end_idx = hmarsele.get_chunk_bounds(
            lines, "Section 1.1", None
        )
        # Check outputs: should stop before Section 1.2.
        self.assertEqual(start_idx, 3)
        self.assertEqual(end_idx, 6)

    def test3(self) -> None:
        """
        Test getting bounds with None start (from beginning).
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",
            "Intro",
            "",
            "## Section 1.1",
            "Content",
        ]
        # Run test.
        start_idx, end_idx = hmarsele.get_chunk_bounds(
            lines, None, "Section 1.1"
        )
        # Check outputs: should start from line 0.
        self.assertEqual(start_idx, 0)
        self.assertEqual(end_idx, 3)


class Test_extract_text_from_markdown_lines(hunitest.TestCase):
    """
    Test text extraction with "END" special value and new features.
    """

    def test1(self) -> None:
        """
        Test extracting from header to end of file with "END" special value.
        """
        # Prepare inputs - simulate markdown lines with headers.
        lines = [
            "# Introduction",
            "Some intro text",
            "",
            "## Background",
            "Background content",
            "",
            "# Methods",
            "Method details",
            "",
            "# Results",
            "Our findings",
            "",
            "# Conclusion",
            "Final thoughts",
        ]
        # Run test: extract from "Methods" to end of file.
        result = hmarsele.extract_text_from_markdown_lines(
            lines, "Methods", "END"
        )
        # Check outputs: should include everything from "# Methods" to end.
        self.assertIn("# Methods", result[0])
        self.assertIn("# Results", "\n".join(result))
        self.assertIn("# Conclusion", "\n".join(result))
        self.assertNotIn("# Introduction", "\n".join(result))

    def test2(self) -> None:
        """
        Test extracting from nested header to end of file with "END".
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",
            "Introduction",
            "",
            "## Section 1.1",
            "Content",
            "",
            "## Section 1.2",
            "More content",
            "",
            "# Chapter 2",
            "New chapter",
        ]
        # Run test: extract from "Section 1.2" to end.
        result = hmarsele.extract_text_from_markdown_lines(
            lines, "Section 1.2", "END"
        )
        # Check outputs.
        result_text = "\n".join(result)
        self.assertIn("## Section 1.2", result_text)
        self.assertIn("# Chapter 2", result_text)
        self.assertNotIn("Section 1.1", result_text)

    def test3(self) -> None:
        """
        Test that None end_header still auto-detects next same-level header.
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",
            "Intro",
            "",
            "## Section 1.1",
            "Content",
            "",
            "## Section 1.2",
            "More",
            "",
            "# Chapter 2",
            "New",
        ]
        # Run test: extract with None (should stop at "## Section 1.2").
        result = hmarsele.extract_text_from_markdown_lines(
            lines, "Section 1.1", None
        )
        # Check outputs: should NOT include Section 1.2 or Chapter 2.
        result_text = "\n".join(result)
        self.assertIn("## Section 1.1", result_text)
        self.assertNotIn("## Section 1.2", result_text)
        self.assertNotIn("# Chapter 2", result_text)

    def test4(self) -> None:
        """
        Test extracting from beginning of file (start_header_str=None).
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",
            "Intro",
            "",
            "## Section 1.1",
            "Content",
            "",
            "## Section 1.2",
            "More",
        ]
        # Run test: extract from beginning to "Section 1.1" (excluding it).
        result = hmarsele.extract_text_from_markdown_lines(
            lines, None, "Section 1.1"
        )
        # Check outputs: should start from first line but stop before Section 1.1.
        # TODO(ai_gp): Apply .claude/skills/testing.rules.md:663:## Replace Checking Invariants with `assert_equal`
        # to all functions in the file
        result_text = "\n".join(result)
        self.assertIn("# Chapter 1", result_text)
        self.assertIn("Intro", result_text)
        self.assertNotIn("## Section 1.1", result_text)
        self.assertNotIn("## Section 1.2", result_text)


# #############################################################################
# Test_extract_rule_from_file
# #############################################################################


class Test_extract_rule_from_file(hunitest.TestCase):
    """
    Test extracting rules from markdown rule files.
    """

    def helper_create_rule_file(self) -> str:
        """
        Create a test rule file with multiple sections at different levels.

        :return: path to the created rule file
        """
        out_dir = self.get_scratch_space()
        file_path = os.path.join(out_dir, "rules.md")
        content = """
            - Document intro

            # Level 1 Section

            - Level 1 content line 1
            - Level 1 content line 2

            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2

            ## Level 1.2 Subsection

            - Level 1.2 content

            # Another Level 1 Section

            - Another level 1 content
            """
        content = hprint.dedent(content)
        hio.to_file(file_path, content)
        return file_path

    def test1(self) -> None:
        """
        Test extracting entire file when no line number is provided.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = file_path
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # The content should be the full file.
        expected = hio.from_file(file_path)
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test extracting level-1 header section (line 3).
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3"
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # Should extract from line 3 until the next level-1 header (line 13).
        expected = """
            # Level 1 Section

            - Level 1 content line 1
            - Level 1 content line 2

            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2

            ## Level 1.2 Subsection

            - Level 1.2 content"""
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test extracting level-2 header section stops at next level-2 or level-1.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:8"
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # Should extract from line 8 (level-2 header) to next level-2 header
        # (line 13).
        expected = """
            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2"""
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test extracting with section name validation (matching).
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3:# Level 1 Section"
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # Same as test2 since the name matches.
        expected = """
            # Level 1 Section

            - Level 1 content line 1
            - Level 1 content line 2

            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2

            ## Level 1.2 Subsection

            - Level 1.2 content"""
        self.assert_equal(actual, expected, dedent=True)

    def test5(self) -> None:
        """
        Test that section name mismatch raises ValueError.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3:# Different Name"
        with self.assertRaises(ValueError):
            hmarsele.extract_rule_from_file(rule_spec)

    def test6(self) -> None:
        """
        Test that non-header line raises ValueError.
        """
        file_path = self.helper_create_rule_file()
        # This is "- Level 1 content line 1", not a header.
        rule_spec = f"{file_path}:4"
        with self.assertRaises(ValueError):
            hmarsele.extract_rule_from_file(rule_spec)

    def test7(self) -> None:
        """
        Test that invalid line number raises error.
        """
        file_path = self.helper_create_rule_file()
        # Out of range.
        rule_spec = f"{file_path}:999"
        with self.assertRaises(AssertionError):
            hmarsele.extract_rule_from_file(rule_spec)

    def test8(self) -> None:
        """
        Test that non-existent file raises error.
        """
        rule_spec = "/nonexistent/path/to/file.md"
        with self.assertRaises(AssertionError):
            hmarsele.extract_rule_from_file(rule_spec)


# #############################################################################
# Test_extract_text_from_markdown
# #############################################################################


class Test_extract_text_from_markdown(hunitest.TestCase):
    """
    Test _extract_text_from_markdown function.
    """

    @staticmethod
    def _to_lines(text: str) -> List[str]:
        return hprint.dedent(text).strip().split("\n")

    def helper(
        self,
        document_text: str,
        start_header: str,
        end_header: str | None,
        expected_text: str,
    ) -> None:
        """
        Test helper for extract_text_from_markdown_lines.

        :param document_text: Full document text to extract from
        :param start_header: Starting header (full or partial)
        :param end_header: Ending header (full or partial) or None
        :param expected_text: Expected extracted text
        """
        # Prepare inputs.
        lines = self._to_lines(document_text)
        # Prepare outputs.
        expected = self._to_lines(expected_text)
        # Run test.
        actual = hmarsele.extract_text_from_markdown_lines(
            lines, start_header, end_header, is_slide_format=False
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            This is the introduction.

            # Methods

            This is the methods section.

            # Results

            Our findings.
            """
        start_header = "# Methods"
        end_header = "# Results"
        expected_text = """
            # Methods

            This is the methods section.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level header (implicit end).
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            Intro text.

            # Methods

            Methods text.

            # Results

            Results text.
            """
        start_header = "# Methods"
        end_header = None
        expected_text = """
            # Methods

            Methods text.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test3(self) -> None:
        """
        Test extracting with nested headers (## under #).
        """
        # Prepare inputs.
        document_text = """
            # Chapter 1

            ## Section 1.1

            Content 1.1

            ## Section 1.2

            Content 1.2

            # Chapter 2
            """
        start_header = "## Section 1.1"
        end_header = None
        expected_text = """
            ## Section 1.1

            Content 1.1
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test4(self) -> None:
        """
        Test extracting until end of file when no next same-level header.
        """
        # Prepare inputs.
        document_text = """
            # Chapter 1

            ## Section 1.1

            Content 1.1

            # Chapter 2

            Content of chapter 2
            """
        start_header = "## Section 1.1"
        end_header = None
        expected_text = """
            ## Section 1.1

            Content 1.1
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def helper_error(
        self, document_text: str, start_header: str, end_header: str | None
    ) -> None:
        """
        Test helper for extract_text_from_markdown_lines error cases.

        :param document_text: Full document text to extract from
        :param start_header: Starting header (full or partial)
        :param end_header: Ending header (full or partial) or None
        """
        # Prepare inputs.
        lines = self._to_lines(document_text)
        # Run test and check output.
        with self.assertRaises(Exception):
            hmarsele.extract_text_from_markdown_lines(
                lines, start_header, end_header, is_slide_format=False
            )

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            Text
            """
        start_header = "# Nonexistent"
        end_header = None
        # Run test.
        self.helper_error(document_text, start_header, end_header)

    def test6(self) -> None:
        """
        Test error when end header not found.
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            Text
            """
        start_header = "# Introduction"
        end_header = "# Nonexistent"
        # Run test.
        self.helper_error(document_text, start_header, end_header)


# #############################################################################
# Test_extract_text_from_markdown_lines
# #############################################################################


class Test_extract_text_from_markdown_lines(hunitest.TestCase):
    """
    Test _extract_from_md_slides function with slide notation.
    """

    @staticmethod
    def _to_lines(text: str) -> List[str]:
        return hprint.dedent(text).strip().split("\n")

    def helper(
        self,
        document_text: str,
        start_header: str,
        end_header: str | None,
        expected_text: str,
    ) -> None:
        """
        Test helper for extract_text_from_markdown_lines with slide format.

        :param document_text: Full document text with slide notation
        :param start_header: Starting header/slide (e.g., "* Title" or "##### Title")
        :param end_header: Ending header/slide (optional)
        :param expected_text: Expected extracted text
        """
        # Prepare inputs.
        lines = self._to_lines(document_text)
        # Prepare outputs.
        expected = self._to_lines(expected_text)
        # Run test.
        actual = hmarsele.extract_text_from_markdown_lines(
            lines, start_header, end_header, is_slide_format=True
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting from slide using * notation, no explicit end.
        """
        # Prepare inputs.
        document_text = """
            * Introduction

            This is the introduction slide.

            * Methods

            This is the methods slide.

            * Results

            Our findings.
            """
        start_header = "* Methods"
        end_header = None
        expected_text = """
            ##### Methods

            This is the methods slide.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test2(self) -> None:
        """
        Test extracting between two slides using * notation.
        """
        # Prepare inputs.
        document_text = """
            * Introduction

            Intro text.

            * Methods

            Methods text.

            * Results

            Results text.
            """
        start_header = "* Methods"
        end_header = "* Results"
        expected_text = """
            ##### Methods

            Methods text.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test3(self) -> None:
        """
        Test extracting from slide using * notation to header using # notation.
        """
        # Prepare inputs.
        document_text = """
            * Slide 1

            Content of slide 1.

            ##### Subsection 1.1

            Content 1.1

            * Slide 2

            Content of slide 2.
            """
        start_header = "* Slide 1"
        end_header = "##### Subsection 1.1"
        expected_text = """
            ##### Slide 1

            Content of slide 1.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)
