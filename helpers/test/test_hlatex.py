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
        actual = hlatex.remove_latex_formatting(txt)
        self.assert_equal(actual, expected)


# #############################################################################


class Test_is_latex_line_separator1(hunitest.TestCase):
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
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(True))

    def test_dash_separator(self) -> None:
        """
        Test that a line with repeated - characters is recognized as separator.
        """
        # Prepare inputs.
        line = "% ----------"
        # Run test.
        actual = hlatex._is_latex_line_separator(line)
        # Check outputs.
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(True))

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
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(False))


# #############################################################################


class Test_frame_sections1(hunitest.TestCase):
    def helper(self, input_txt: str, expected: str) -> None:
        """
        Helper method to test frame_sections function.

        :param input_txt: input LaTeX text
        :param expected: expected output after processing
        """
        # Prepare inputs.
        lines = hprint.dedent(input_txt)
        lines = lines.split("\n")
        # Run test.
        actual = hlatex.frame_sections(lines)
        actual = "\n".join(actual)
        # Prepare expected.
        expected = hprint.dedent(expected)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test_basic_section(self) -> None:
        """
        Test adding separator before a single section command.
        """
        # Prepare inputs.
        input_txt = r"""
        \section{Introduction}
        This is the introduction.
        """
        # Prepare expected outputs.
        expected = r"""
        % ##############################################################################
        \section{Introduction}
        This is the introduction.
        """
        # Check.
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
        # Prepare expected outputs.
        expected = r"""
        % ##############################################################################
        \section{Proposed framework}

        % ==============================================================================
        \subsection{Combining Physics-Informed and Data-Driven Approaches}

        % ------------------------------------------------------------------------------
        \subsubsection{Detailed Analysis}
        """
        # Check.
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
        # Prepare expected outputs.
        expected = r"""
        % ##############################################################################
        \section{Introduction}

        % ==============================================================================
        \subsection{Background}
        """
        # Check.
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
        # Prepare expected outputs.
        expected = r"""
        % ##############################################################################
        \section{Introduction}

        This is text after multiple empty lines.
        """
        # Check.
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
        # Prepare expected outputs.
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
        # Check.
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
        # Prepare expected outputs.
        expected = r"""
        This is regular text.
        No sections here.
        Just content.
        """
        # Check.
        self.helper(input_txt, expected)


# #############################################################################
# Test_is_latex_comment
# #############################################################################


class Test_is_latex_comment(hunitest.TestCase):
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
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(True))

    def test_not_a_comment(self) -> None:
        """
        Test that a regular line is not recognized as a comment.
        """
        # Prepare inputs.
        line = "This is regular text"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(False))

    def test_escaped_percent(self) -> None:
        """
        Test that a line with escaped % character is not a comment.
        """
        # Prepare inputs.
        line = r"The value is \% of the total"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(False))

    def test_percent_in_middle(self) -> None:
        """
        Test that a line with % in the middle is not a comment.
        """
        # Prepare inputs.
        line = r"Text before \% and after"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(False))

    def test_empty_comment(self) -> None:
        """
        Test that a line with only % is a comment.
        """
        # Prepare inputs.
        line = "%"
        # Run test.
        actual = hlatex._is_latex_comment(line)
        # Check outputs.
        # TODO(ai_gp): Use assertTrue / assertFalse instead of this.
        self.assert_equal(str(actual), str(True))


# #############################################################################
# Test_extract_latex_section
# #############################################################################


class Test_extract_latex_section(hunitest.TestCase):
    def helper(self, line, expected) -> None:
        """
        Test extraction of basic section command.
        """
        # Prepare inputs.
        line = r"\section{Introduction}"
        # Run test.
        header_info = hlatex._extract_latex_section(line)
        # Check outputs.
        actual = header_info_to_str(header_info)
        self.assert_equal(actual, expected)

    # TODO(ai_gp): Use self.helper()
    def test_section_basic(self) -> None:
        """
        Test extraction of basic section command.
        """
        # Prepare inputs.
        line = r"\section{Introduction}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(1))
        self.assert_equal(title, "Introduction")

    # TODO(ai_gp): Use self.helper()
    def test_subsection_basic(self) -> None:
        """
        Test extraction of basic subsection command.
        """
        # Prepare inputs.
        line = r"\subsection{Background}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(2))
        self.assert_equal(title, "Background")

    # TODO(ai_gp): Use self.helper()
    def test_subsubsection_basic(self) -> None:
        """
        Test extraction of basic subsubsection command.
        """
        # Prepare inputs.
        line = r"\subsubsection{Details}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(3))
        self.assert_equal(title, "Details")

    # TODO(ai_gp): Use self.helper()
    def test_section_with_nested_braces(self) -> None:
        """
        Test extraction of section with nested LaTeX commands.
        """
        # Prepare inputs.
        line = r"\section{Introduction to \textbf{Machine Learning}}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(1))
        self.assert_equal(title, r"Introduction to \textbf{Machine Learning}")

    # TODO(ai_gp): Use self.helper()
    def test_section_with_optional_argument(self) -> None:
        """
        Test extraction of section with optional short title.
        """
        # Prepare inputs.
        line = r"\section[Short Title]{Long Title for Table of Contents}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(1))
        # Should extract the long title (in curly braces)
        self.assert_equal(title, "Long Title for Table of Contents")

    # TODO(ai_gp): Use self.helper()
    def test_section_with_escaped_characters(self) -> None:
        """
        Test extraction of section with escaped special characters.
        """
        # Prepare inputs.
        line = r"\section{Cost Analysis: \$100 \& More}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(1))
        self.assert_equal(title, r"Cost Analysis: \$100 \& More")

    # TODO(ai_gp): Use self.helper()
    def test_section_with_leading_whitespace(self) -> None:
        """
        Test extraction of section with leading whitespace.
        """
        # Prepare inputs.
        line = r"   \section{Methods}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(1))
        self.assert_equal(title, "Methods")

    # TODO(ai_gp): Use self.helper()
    def test_not_a_section(self) -> None:
        """
        Test that a regular line is not recognized as a section.
        """
        # Prepare inputs.
        line = "This is regular text"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(False))
        self.assert_equal(str(level), str(0))
        self.assert_equal(title, "")

    # TODO(ai_gp): Use self.helper()
    def test_section_empty_title(self) -> None:
        """
        Test extraction of section with empty title.
        """
        # Prepare inputs.
        line = r"\section{}"
        # Run test.
        is_section, level, title = hlatex._extract_latex_section(line)
        # Check outputs.
        self.assert_equal(str(is_section), str(True))
        self.assert_equal(str(level), str(1))
        self.assert_equal(title, "")


# #############################################################################
# Test_extract_headers_from_latex
# #############################################################################


class Test_extract_headers_from_latex(hunitest.TestCase):
    def helper(self, lines, expected) -> None:
        """
        Test extraction from a basic LaTeX document with multiple section levels.
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 3
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        actual_str = str(actual)
        # Check outputs.
        self.assert_equal(actual_str, expected)

    # TODO(ai_gp): Use self.helper()
    def test_basic_document(self, lines, expected) -> None:
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
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 3
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        actual_str = str(actual)
        # Check outputs.
        self.assert_equal(actual_str, expected)

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
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 3
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        # Check outputs.
        self.assert_equal(str(len(actual)), str(2))
        self.assert_equal(actual[0].description, "Introduction")
        self.assert_equal(actual[1].description, "Current Subsection")

    # TODO(ai_gp): Use self.helper()
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
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 2
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        # Check outputs.
        # Should only get section and subsection, not subsubsection
        self.assert_equal(str(len(actual)), str(2))
        self.assert_equal(actual[0].description, "Chapter 1")
        self.assert_equal(actual[1].description, "Section 1.1")

    # TODO(ai_gp): Use self.helper()
    def test_with_nested_braces(self) -> None:
        """
        Test extraction with nested LaTeX commands in titles.
        """
        # Prepare inputs.
        lines = r"""
        \section{Introduction to \textbf{ML}}
        \subsection{Using \emph{Neural Networks}}
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 3
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        # Check outputs.
        self.assert_equal(str(len(actual)), str(2))
        self.assert_equal(actual[0].description, r"Introduction to \textbf{ML}")
        self.assert_equal(actual[1].description, r"Using \emph{Neural Networks}")

    # TODO(ai_gp): Use self.helper()
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
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 3
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        # Check outputs.
        # Line numbers should be 3 and 6 (1-indexed)
        self.assert_equal(str(actual[0].line_number), str(3))
        self.assert_equal(str(actual[1].line_number), str(6))

    # TODO(ai_gp): Use self.helper()
    def test_empty_document(self) -> None:
        """
        Test extraction from document with no sections.
        """
        # Prepare inputs.
        lines = """
        This is just regular text.
        No sections here.
        """
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 3
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        # Check outputs.
        self.assert_equal(str(len(actual)), str(0))

    # TODO(ai_gp): Use self.helper()
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
        lines = hprint.dedent(lines)
        lines = lines.split("\n")
        max_level = 3
        # Run test.
        actual = hlatex.extract_headers_from_latex(
            lines, max_level, sanity_check=False
        )
        # Check outputs.
        self.assert_equal(str(len(actual)), str(5))
        # Check structure
        self.assert_equal(str(actual[0].level), str(1))
        self.assert_equal(actual[0].description, "Chapter 1")
        self.assert_equal(str(actual[1].level), str(2))
        self.assert_equal(actual[1].description, "Section 1.1")
        self.assert_equal(str(actual[2].level), str(3))
        self.assert_equal(actual[2].description, "Subsection 1.1.1")
        self.assert_equal(str(actual[3].level), str(2))
        self.assert_equal(actual[3].description, "Section 1.2")
        self.assert_equal(str(actual[4].level), str(1))
        self.assert_equal(actual[4].description, "Chapter 2")
