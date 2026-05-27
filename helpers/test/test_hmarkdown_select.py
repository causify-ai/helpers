from typing import List, Tuple

import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_select as hmarsele
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
        Test finding header with full format (level prefix is ignored, uses partial match).
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        header_input = "# Section 1.1"
        # Run test (level prefix is ignored, partial match is used).
        result, level = hmarsele.find_header_from_input(
            header_list, header_input
        )
        # Check outputs.
        self.assertEqual(result.description, "Section 1.1")
        self.assertEqual(level, 2)

    def test5(self) -> None:
        """
        Test partial match with # prefix.
        """
        # Prepare inputs.
        header_list = _build_header_list(
            [
                (1, "Chapter 1"),
                (2, "Section 1.1"),
            ]
        )
        header_input = "## Chapter"
        # Run test.
        result, level = hmarsele.find_header_from_input(
            header_list, header_input
        )
        # Check outputs.
        self.assertEqual(result.description, "Chapter 1")
        self.assertEqual(level, 1)


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


class Test_extract_text_from_markdown_lines(hunitest.TestCase):
    """
    Test text extraction with "END" special value.
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
