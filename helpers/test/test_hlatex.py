import logging

import helpers.hlatex as hlatex
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


class Test_remove_latex_formatting1(hunitest.TestCase):
    def test1(self) -> None:
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
        actual = hlatex.is_latex_line_separator(line)
        # Check outputs.
        self.assert_equal(str(actual), str(True))

    def test_equals_separator(self) -> None:
        """
        Test that a line with repeated = characters is recognized as separator.
        """
        # Prepare inputs.
        line = "% =========="
        # Run test.
        actual = hlatex.is_latex_line_separator(line)
        # Check outputs.
        self.assert_equal(str(actual), str(True))

    def test_dash_separator(self) -> None:
        """
        Test that a line with repeated - characters is recognized as separator.
        """
        # Prepare inputs.
        line = "% ----------"
        # Run test.
        actual = hlatex.is_latex_line_separator(line)
        # Check outputs.
        self.assert_equal(str(actual), str(True))

    def test_not_enough_repeats(self) -> None:
        """
        Test that a line with too few repeated characters is not a separator.
        """
        # Prepare inputs.
        line = "% ####"
        # Run test.
        actual = hlatex.is_latex_line_separator(line)
        # Check outputs.
        self.assert_equal(str(actual), str(False))

    def test_regular_comment(self) -> None:
        """
        Test that a regular comment is not recognized as separator.
        """
        # Prepare inputs.
        line = "% This is a regular comment"
        # Run test.
        actual = hlatex.is_latex_line_separator(line)
        # Check outputs.
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
