"""
Unit tests for hlatex module.

This module tests LaTeX text processing utilities including:
- Removing LaTeX formatting commands
- Detecting LaTeX line separators
- Framing sections with separator lines
- Detecting LaTeX comments
- Extracting section headers and their hierarchy
"""

import logging

import helpers.hlatex as hlatex
import helpers.hmarkdown_headers as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


class Test_remove_latex_formatting1(hunitest.TestCase):
    """
    Test the remove_latex_formatting function.
    """

    def test1(self) -> None:
        """
        Test removal of textcolor commands from LaTeX text.
        """
        # Prepare inputs.
        txt = r"""
        - If there is \textcolor{red}{no pattern}, we can try learning:
          - Measure if \textcolor{blue}{learning works}.
          - In the \textcolor{orange}{worst case}, conclude that it
            \textcolor{green}{does not work}.
        - If we can find the \textcolor{purple}{solution in one step} or
          \textcolor{cyan}{program the solution}:
          - \textcolor{brown}{Machine learning} is not the \textcolor{teal}{recommended
            technique}, but it still works.
        - Without \textcolor{magenta}{data}, we cannot do anything:
          \textcolor{violet}{data is all that matters}.
        """
        txt = hprint.dedent(txt)
        # Prepare outputs.
        expected = r"""
        - If there is no pattern, we can try learning:
          - Measure if learning works.
          - In the worst case, conclude that it
            does not work.
        - If we can find the solution in one step or
          program the solution:
          - Machine learning is not the recommended
            technique, but it still works.
        - Without data, we cannot do anything:
          data is all that matters."""
        expected = hprint.dedent(expected)
        # Run test.
        actual = hlatex.remove_latex_formatting(txt)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_is_latex_line_separator1
# #############################################################################


class Test_is_latex_line_separator1(hunitest.TestCase):
    """
    Test the _is_latex_line_separator function.
    """

    # TODO(ai_gp): -> test1, test2, ...
    def test_hash_separator(self) -> None:
        """
        Test that a line with repeated # characters is recognized as separator.
        """
        # Prepare inputs.
        line = "% ##########"
        # Run test.
        actual = hlatex._is_latex_line_separator(line)
        # Check outputs.
        self.assertTrue(actual)

    def test_equals_separator(self) -> None:
        """
        Test that a line with repeated = characters is recognized as separator.
        """
        # Prepare inputs.
        line = "% =========="
        # Run test.
        actual = hlatex._is_latex_line_separator(line)
        # Check outputs.
        self.assertTrue(actual)

    def test_dash_separator(self) -> None:
        """
        Test that a line with repeated - characters is recognized as separator.
        """
        # Prepare inputs.
        line = "% ----------"
        # Run test.
        actual = hlatex._is_latex_line_separator(line)
        # Check outputs.
        self.assertTrue(actual)

    def test_not_enough_repeats(self) -> None:
        """
        Test that a line with too few repeated characters is not a separator.
        """
        # Prepare inputs.
        line = "% ####"
        # Run test.
        actual = hlatex._is_latex_line_separator(line)
        # Check outputs.
        self.assertFalse(actual)

    def test_regular_comment(self) -> None:
        """
        Test that a regular comment is not recognized as separator.
        """
        # Prepare inputs.
        line = "% This is a regular comment"
        # Run test.
        actual = hlatex._is_latex_line_separator(line)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_frame_sections1
# #############################################################################


class Test_frame_sections1(hunitest.TestCase):
    """
    Test the frame_sections function.
    """

    def helper(self, input_txt: str, expected: str) -> None:
        """
        Helper method to test frame_sections function.

        :param input_txt: Input LaTeX text
        :param expected: Expected output after processing
        """
        # Prepare inputs.
        lines = hprint.dedent(input_txt)
        lines = lines.split("\n")
        # Run test.
        actual = hlatex.frame_sections(lines)
        actual = "\n".join(actual)
        # Prepare outputs.
        expected = hprint.dedent(expected)
        # Check outputs.
        self.assert_equal(actual, expected)

    # TODO(ai_gp): -> test1, test2, ...
    def test_basic_section(self) -> None:
        """
        Test adding separator before a single section command.
        """
        # Prepare inputs.
        input_txt = r"""
        \section{Introduction}
        This is the introduction.
        """
        # Prepare outputs.
        expected = r"""
        % ##############################################################################
        \section{Introduction}
        This is the introduction.
        """
        # Run test.
        self.helper(input_txt, expected)

    def test_all_section_types(self) -> None:
        """
        Test adding separators before section, subsection, and subsubsection.
        """
        # Prepare inputs.
        input_txt = r"""
        \section{Proposed framework}

        \subsection{Combining Physics-Informed and Data-Driven Approaches}

        \subsubsection{Detailed Analysis}
        """
        # Prepare outputs.
        expected = r"""
        % ##############################################################################
        \section{Proposed framework}

        % ==============================================================================
        \subsection{Combining Physics-Informed and Data-Driven Approaches}

        % ------------------------------------------------------------------------------
        \subsubsection{Detailed Analysis}
        """
        # Run test.
        self.helper(input_txt, expected)

    def test_existing_separators_removed(self) -> None:
        """
        Test that existing separators are removed and replaced with correct ones.
        """
        # Prepare inputs.
        input_txt = r"""
        % ==============
        \section{Introduction}

        % ##############
        \subsection{Background}
        """
        # Prepare outputs.
        expected = r"""
        % ##############################################################################
        \section{Introduction}

        % ==============================================================================
        \subsection{Background}
        """
        # Run test.
        self.helper(input_txt, expected)

    def test_consecutive_empty_lines_reduced(self) -> None:
        """
        Test that multiple consecutive empty lines are reduced to one.
        """
        # Prepare inputs.
        input_txt = r"""
        \section{Introduction}



        This is text after multiple empty lines.
        """
        # Prepare outputs.
        expected = r"""
        % ##############################################################################
        \section{Introduction}

        This is text after multiple empty lines.
        """
        # Run test.
        self.helper(input_txt, expected)

    def test_mixed_content(self) -> None:
        """
        Test with mixed content including text, sections, and empty lines.
        """
        # Prepare inputs.
        input_txt = r"""
        This is some introductory text.

        \section{Methods}

        We describe the methods here.


        \subsection{Data Collection}

        Details about data collection.

        \subsubsection{Sampling Strategy}

        Sampling details here.
        """
        # Prepare outputs.
        expected = r"""
        This is some introductory text.

        % ##############################################################################
        \section{Methods}

        We describe the methods here.

        % ==============================================================================
        \subsection{Data Collection}

        Details about data collection.

        % ------------------------------------------------------------------------------
        \subsubsection{Sampling Strategy}

        Sampling details here.
        """
        # Run test.
        self.helper(input_txt, expected)

    def test_no_sections(self) -> None:
        """
        Test that lines without section commands are left unchanged.
        """
        # Prepare inputs.
        input_txt = r"""
        This is regular text.
        No sections here.
        Just content.
        """
        # Prepare outputs.
        expected = r"""
        This is regular text.
        No sections here.
        Just content.
        """
        # Run test.
        self.helper(input_txt, expected)


# #############################################################################
# Test_is_latex_comment
# #############################################################################


class Test_is_latex_comment(hunitest.TestCase):
    """
    Test the _is_latex_comment function.
    """

    # TODO(ai_gp): -> test1, test2, ...
    def test_basic_comment(self) -> None:
        """
        Test that a line starting with % is recognized as a comment.
        """
        # Prepare inputs.
        line = "% This is a comment"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        self.assertTrue(actual)

    def test_comment_with_leading_whitespace(self) -> None:
        """
        Test that a line with leading whitespace and % is a comment.
        """
        # Prepare inputs.
        line = "   % This is a comment"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        self.assertTrue(actual)

    def test_not_a_comment(self) -> None:
        """
        Test that a regular line is not recognized as a comment.
        """
        # Prepare inputs.
        line = "This is regular text"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        self.assertFalse(actual)

    def test_escaped_percent(self) -> None:
        """
        Test that a line with escaped % character is not a comment.
        """
        # Prepare inputs.
        line = r"The value is \% of the total"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        self.assertFalse(actual)

    def test_percent_in_middle(self) -> None:
        """
        Test that a line with % in the middle is not a comment.
        """
        # Prepare inputs.
        line = r"Text before \% and after"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        self.assertFalse(actual)

    def test_empty_comment(self) -> None:
        """
        Test that a line with only % is a comment.
        """
        # Prepare inputs.
        line = "%"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# Test_extract_latex_section
# #############################################################################


class Test_extract_latex_section(hunitest.TestCase):
    """
    Test the _extract_latex_section function.
    """

    def helper(
        self, line: str, expected_level: int, expected_title: str
    ) -> None:
        """
        Helper method to test extraction of LaTeX section commands.

        :param line: LaTeX line to parse
        :param expected_level: Expected section level (0 if no section)
        :param expected_title: Expected title (empty string if no section)
        """
        # Prepare inputs - line_number is arbitrary for testing.
        line_number = 1
        # Run test.
        header_info = hlatex._extract_latex_section(line, line_number)
        # Check outputs.
        if expected_level == 0:
            # No section expected.
            self.assertIsNone(header_info)
        else:
            # Section expected.
            self.assertIsNotNone(header_info)
            self.assert_equal(str(header_info.level), str(expected_level))
            self.assert_equal(header_info.description, expected_title)

    # TODO(ai_gp): -> test1, test2, ...
    def test_section_basic(self) -> None:
        """
        Test extraction of basic section command.
        """
        line = r"\section{Introduction}"
        self.helper(line, 1, "Introduction")

    def test_subsection_basic(self) -> None:
        """
        Test extraction of basic subsection command.
        """
        line = r"\subsection{Background}"
        self.helper(line, 2, "Background")

    def test_subsubsection_basic(self) -> None:
        """
        Test extraction of basic subsubsection command.
        """
        line = r"\subsubsection{Details}"
        self.helper(line, 3, "Details")

    def test_section_with_nested_braces(self) -> None:
        """
        Test extraction of section with nested LaTeX commands.
        """
        line = r"\section{Introduction to \textbf{Machine Learning}}"
        self.helper(line, 1, r"Introduction to \textbf{Machine Learning}")

    def test_section_with_optional_argument(self) -> None:
        """
        Test extraction of section with optional short title.
        """
        line = r"\section[Short Title]{Long Title for Table of Contents}"
        # Should extract the long title (in curly braces).
        self.helper(line, 1, "Long Title for Table of Contents")

    def test_section_with_escaped_characters(self) -> None:
        """
        Test extraction of section with escaped special characters.
        """
        line = r"\section{Cost Analysis: \$100 \& More}"
        self.helper(line, 1, r"Cost Analysis: \$100 \& More")

    def test_section_with_leading_whitespace(self) -> None:
        """
        Test extraction of section with leading whitespace.
        """
        line = r"   \section{Methods}"
        self.helper(line, 1, "Methods")

    def test_not_a_section(self) -> None:
        """
        Test that a regular line is not recognized as a section.
        """
        line = "This is regular text"
        self.helper(line, 0, "")

    def test_section_empty_title(self) -> None:
        """
        Test that section with empty title is not extracted.
        """
        line = r"\section{}"
        # Sections with empty titles should not be extracted.
        self.helper(line, 0, "")


# #############################################################################
# Test_extract_headers_from_latex
# #############################################################################


class Test_extract_headers_from_latex(hunitest.TestCase):
    """
    Test the extract_headers_from_latex function.
    """

    def helper(self, lines: str, expected: str, *, max_level: int = 3) -> None:
        """
        Helper method to test header extraction from LaTeX documents.

        :param lines: LaTeX document content as a string
        :param expected: Expected string representation of header list
        :param max_level: Maximum header level to extract (default: 3)
        """
        # Prepare inputs.
        lines_list = hprint.dedent(lines).split("\n")
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines_list, max_level, sanity_check=False
        )
        actual_str = hmarkdo.header_list_to_str(actual)
        # Prepare outputs.
        expected = hprint.dedent(expected)
        # Check outputs.
        self.assert_equal(actual_str, expected)

    # TODO(ai_gp): -> test1, test2, ...
    def test_basic_document(self) -> None:
        """
        Test extraction from a basic LaTeX document with multiple section levels.
        """
        # Prepare inputs.
        lines = r"""
        \section{Introduction}
        This is the introduction.

        \subsection{Background}
        Background information here.

        \section{Methods}
        Methods description.
        """
        # Prepare outputs.
        expected = """
        HeaderInfo(1, 'Introduction', 1)
        HeaderInfo(2, 'Background', 4)
        HeaderInfo(1, 'Methods', 7)"""
        # Run test.
        self.helper(lines, expected)

    def test_with_comments(self) -> None:
        """
        Test that commented-out sections are skipped.
        """
        # Prepare inputs.
        lines = r"""
        \section{Introduction}
        % \section{Old Section}
        \subsection{Current Subsection}
        % \subsection{Old Subsection}
        """
        # Prepare outputs.
        expected = """
        HeaderInfo(1, 'Introduction', 1)
        HeaderInfo(2, 'Current Subsection', 3)"""
        # Run test.
        self.helper(lines, expected)

    def test_max_level_filtering(self) -> None:
        """
        Test that only headers up to max_level are extracted.
        """
        # Prepare inputs.
        lines = r"""
        \section{Chapter 1}
        \subsection{Section 1.1}
        \subsubsection{Section 1.1.1}
        """
        # Prepare outputs.
        # Should only get section and subsection, not subsubsection.
        expected = """
        HeaderInfo(1, 'Chapter 1', 1)
        HeaderInfo(2, 'Section 1.1', 2)"""
        # Run test.
        self.helper(lines, expected, max_level=2)

    def test_with_nested_braces(self) -> None:
        """
        Test extraction with nested LaTeX commands in titles.
        """
        # Prepare inputs.
        lines = r"""
        \section{Introduction to \textbf{ML}}
        \subsection{Using \emph{Neural Networks}}
        """
        # Prepare outputs.
        expected = r"""
        HeaderInfo(1, 'Introduction to \textbf{ML}', 1)
        HeaderInfo(2, 'Using \emph{Neural Networks}', 2)"""
        # Run test.
        self.helper(lines, expected)

    def test_line_numbers(self) -> None:
        """
        Test that line numbers are correctly recorded.
        """
        # Prepare inputs.
        lines = r"""
        Some text here.

        \section{First Section}
        More text.

        \subsection{First Subsection}
        Even more text.
        """
        # Prepare outputs.
        # Line numbers should be 3 and 6 (1-indexed).
        expected = """
        HeaderInfo(1, 'First Section', 3)
        HeaderInfo(2, 'First Subsection', 6)"""
        # Run test.
        self.helper(lines, expected)

    def test_empty_document(self) -> None:
        """
        Test extraction from document with no sections.
        """
        # Prepare inputs.
        lines = """
        This is just regular text.
        No sections here.
        """
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(lines, expected)

    def test_all_levels(self) -> None:
        """
        Test extraction with all three section levels.
        """
        # Prepare inputs.
        lines = r"""
        \section{Chapter 1}
        Introduction to chapter.

        \subsection{Section 1.1}
        Section content.

        \subsubsection{Subsection 1.1.1}
        Detailed content.

        \subsection{Section 1.2}
        More content.

        \section{Chapter 2}
        Second chapter.
        """
        # Prepare outputs.
        expected = """
        HeaderInfo(1, 'Chapter 1', 1)
        HeaderInfo(2, 'Section 1.1', 4)
        HeaderInfo(3, 'Subsection 1.1.1', 7)
        HeaderInfo(2, 'Section 1.2', 10)
        HeaderInfo(1, 'Chapter 2', 13)"""
        # Run test.
        self.helper(lines, expected)
