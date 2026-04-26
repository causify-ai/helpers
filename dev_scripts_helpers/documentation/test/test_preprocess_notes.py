import glob
import logging
import os
from collections.abc import Sequence
from typing import cast

import pytest

import dev_scripts_helpers.documentation.preprocess_notes as dshdprno
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_colorize_backticks
# #############################################################################


class Test_colorize_backticks(hunitest.TestCase):
    """
    Test the `_colorize_backticks()` function.
    """

    def helper(self, txt_in: str, expected: str) -> None:
        """
        Helper method to test the _colorize_backticks function.

        :param txt_in: input text
        :param expected: expected output text
        """
        actual = dshdprno._colorize_backticks(txt_in)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test single backtick-wrapped word.
        """
        # Prepare inputs.
        txt_in = "The `store` variable is used."
        expected = r"The \textcolor{blue}{\texttt{store}} variable is used."
        # Run test.
        self.helper(txt_in, expected)

    def test2(self) -> None:
        """
        Test multiple backtick-wrapped words in one line.
        """
        # Prepare inputs.
        txt_in = "Use `function1` and `function2` to process data."
        expected = r"Use \textcolor{blue}{\texttt{function1}} and \textcolor{blue}{\texttt{function2}} to process data."
        # Run test.
        self.helper(txt_in, expected)

    def test3(self) -> None:
        """
        Test backtick-wrapped multi-word phrase.
        """
        # Prepare inputs.
        txt_in = "The `main function` is important."
        expected = r"The \textcolor{blue}{\texttt{main function}} is important."
        # Run test.
        self.helper(txt_in, expected)

    def test4(self) -> None:
        """
        Test line with no backticks should remain unchanged.
        """
        # Prepare inputs.
        txt_in = "This line has no special formatting."
        expected = txt_in
        # Run test.
        self.helper(txt_in, expected)

    def test5(self) -> None:
        """
        Test triple backticks (code block) should not be processed.
        """
        # Prepare inputs.
        txt_in = "```python\nprint('hello')\n```"
        expected = txt_in
        # Run test.
        self.helper(txt_in, expected)

    def test6(self) -> None:
        """
        Test backticks at the beginning of the line.
        """
        # Prepare inputs.
        txt_in = "`config` is a parameter"
        expected = r"\textcolor{blue}{\texttt{config}} is a parameter"
        # Run test.
        self.helper(txt_in, expected)

    def test7(self) -> None:
        """
        Test backticks at the end of the line.
        """
        # Prepare inputs.
        txt_in = "Import the module called `helpers`"
        expected = r"Import the module called \textcolor{blue}{\texttt{helpers}}"
        # Run test.
        self.helper(txt_in, expected)

    def test8(self) -> None:
        """
        Test backticks containing special characters (underscores).
        """
        # Prepare inputs.
        txt_in = "Use the `_private_func` or `__dunder__` naming."
        expected = r"Use the \textcolor{blue}{\texttt{\_private\_func}} or \textcolor{blue}{\texttt{\_\_dunder\_\_}} naming."
        # Run test.
        self.helper(txt_in, expected)

    def test9(self) -> None:
        """
        Test backticks containing numbers.
        """
        # Prepare inputs.
        txt_in = "Call `func42` to compute result."
        expected = r"Call \textcolor{blue}{\texttt{func42}} to compute result."
        # Run test.
        self.helper(txt_in, expected)

    def test10(self) -> None:
        """
        Test empty backticks should not match.
        """
        # Prepare inputs.
        txt_in = "Text with `` empty backticks here."
        # Empty backticks should not match due to pattern requiring at least one character.
        expected = txt_in
        # Run test.
        self.helper(txt_in, expected)

    def test11(self) -> None:
        """
        Test backticks inside a line with multiple sentences.
        """
        # Prepare inputs.
        txt_in = "First sentence with `var1`. Second sentence with `var2`. Third sentence."
        expected = r"First sentence with \textcolor{blue}{\texttt{var1}}. Second sentence with \textcolor{blue}{\texttt{var2}}. Third sentence."
        # Run test.
        self.helper(txt_in, expected)

    def test12(self) -> None:
        """
        Test backticks containing dots (like package names).
        """
        # Prepare inputs.
        txt_in = "Import `numpy.array` for matrix operations."
        expected = r"Import \textcolor{blue}{\texttt{numpy.array}} for matrix operations."
        # Run test.
        self.helper(txt_in, expected)

    def test13(self) -> None:
        """
        Test backticks containing underscores (escaped in LaTeX).
        """
        # Prepare inputs.
        txt_in = "The `weeks_to_xmas` variable stores the countdown."
        expected = r"The \textcolor{blue}{\texttt{weeks\_to\_xmas}} variable stores the countdown."
        # Run test.
        self.helper(txt_in, expected)

    def test14(self) -> None:
        """
        Test multiple backtick-wrapped words with underscores.
        """
        # Prepare inputs.
        txt_in = (
            "Use `_private_func` or `public_var` for different access levels."
        )
        expected = r"Use \textcolor{blue}{\texttt{\_private\_func}} or \textcolor{blue}{\texttt{public\_var}} for different access levels."
        # Run test.
        self.helper(txt_in, expected)

    def test15(self) -> None:
        """
        Test backticks with leading and trailing underscores.
        """
        # Prepare inputs.
        txt_in = "Call `__init__` or `__dunder__` methods in Python."
        expected = r"Call \textcolor{blue}{\texttt{\_\_init\_\_}} or \textcolor{blue}{\texttt{\_\_dunder\_\_}} methods in Python."
        # Run test.
        self.helper(txt_in, expected)


# #############################################################################
# Test_colorize_backticks_integration
# #############################################################################


class Test_colorize_backticks_integration(hunitest.TestCase):
    """
    Test backtick colorization as part of the full preprocessing pipeline.
    """

    def helper(
        self, txt_in: str, type_: str, expected: str
    ) -> None:
        """
        Test helper for _transform_lines with backtick colorization.

        :param txt_in: input text
        :param type_: output type ("pdf" or "slides")
        :param expected: expected output text
        """
        # Prepare inputs.
        txt_in_lines = txt_in.split("\n")
        txt_in_lines = hprint.dedent(txt_in_lines, remove_lead_trail_empty_lines_=True)
        # Execute function.
        actual = dshdprno._transform_lines(txt_in_lines, type_, is_qa=False)
        actual = "\n".join(actual)
        # Check.
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test backtick colorization in full pipeline with type="pdf".
        """
        # Prepare inputs.
        txt_in = r"""
        # Chapter 1
        The `variable` is used here.
        And `function_name` is called next.
        """
        expected = r"""
        ---
        fontsize: 10pt
        ---
        \let\emph\textit
        \let\uline\underline
        \let\ul\underline
        # Chapter 1
        The \textcolor{blue}{\texttt{variable}} is used here.
        And \textcolor{blue}{\texttt{function\_name}} is called next.
        """
        # Run test.
        self.helper(txt_in, "pdf", expected)

    def test2(self) -> None:
        """
        Test backtick colorization with type="slides".
        """
        # Prepare inputs.
        txt_in = r"""
        # Slide Title
        Use `method1` and `method2` for processing.
        """
        expected = r"""
        ---
        fontsize: 10pt
        ---
        \let\emph\textit
        \let\uline\underline
        \let\ul\underline
        # Slide Title
        Use \textcolor{blue}{\texttt{method1}} and \textcolor{blue}{\texttt{method2}} for processing.
        """
        # Run test.
        self.helper(txt_in, "slides", expected)

    def test3(self) -> None:
        """
        Test backtick colorization doesn't affect code blocks.
        """
        # Prepare inputs.
        txt_in = r"""
        Example code:
        ```python
        variable = `store`
        ```
        The `variable` name is important.
        """
        expected = r"""
        ---
        fontsize: 10pt
        ---
        \let\emph\textit
        \let\uline\underline
        \let\ul\underline
        Example code:
        ```python
        variable = `store`
        ```
        The \textcolor{blue}{\texttt{variable}} name is important.
        """
        # Run test.
        self.helper(txt_in, "pdf", expected)


# #############################################################################
# Test_process_question1
# #############################################################################


class Test_process_question1(hunitest.TestCase):
    """
    Check that the output of `preprocess_notes.py` is the expected one calling
    the library function directly.
    """

    def test_process_question1(self) -> None:
        txt_in = "* Hope is not a strategy"
        do_continue_exp = True
        exp = "- **Hope is not a strategy**"
        self.helper(txt_in, do_continue_exp, exp)

    def test_process_question2(self) -> None:
        txt_in = "** Hope is not a strategy"
        do_continue_exp = True
        exp = "- **Hope is not a strategy**"
        self.helper(txt_in, do_continue_exp, exp)

    def test_process_question3(self) -> None:
        txt_in = "*: Hope is not a strategy"
        do_continue_exp = True
        exp = "- **Hope is not a strategy**"
        self.helper(txt_in, do_continue_exp, exp)

    def test_process_question4(self) -> None:
        txt_in = "- Systems don't run themselves, they need to be run"
        do_continue_exp = False
        exp = txt_in
        self.helper(txt_in, do_continue_exp, exp)

    def test_process_question5(self) -> None:
        space = "   "
        txt_in = "*" + space + "Hope is not a strategy"
        do_continue_exp = True
        exp = "-" + space + "**Hope is not a strategy**"
        self.helper(txt_in, do_continue_exp, exp)

    def test_process_question6(self) -> None:
        space = "   "
        txt_in = "**" + space + "Hope is not a strategy"
        do_continue_exp = True
        exp = "-" + " " * len(space) + "**Hope is not a strategy**"
        self.helper(txt_in, do_continue_exp, exp)

    def helper(self, txt_in: str, do_continue_exp: bool, expected: str) -> None:
        do_continue, actual = dshdprno._process_question_to_markdown(txt_in)
        self.assertEqual(do_continue, do_continue_exp)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_remove_headers1
# #############################################################################


class Test_remove_headers1(hunitest.TestCase):
    """
    Test the `_remove_headers()` function.
    """

    def helper(
        self, lines_in: Sequence[str], expected: Sequence[str], max_level: int = 999
    ) -> None:
        """
        Helper method to test the _remove_headers function.

        :param lines_in: input lines
        :param expected: expected output lines
        :param max_level: maximum level of headers to consider (default:
            999 to remove all headers)
        """
        actual = dshdprno._remove_headers(list(lines_in), max_level)
        # Convert lists to strings for comparison.
        actual_str = "\n".join(actual)
        expected_str = "\n".join(expected)
        self.assert_equal(actual_str, expected_str)

    def test1(self) -> None:
        """
        Test removing a single level 1 header.
        """
        lines_in = """
        # Chapter 1
        Some content here
        """
        lines_in = lines_in.split("\n")
        lines_in = hprint.dedent(lines_in, remove_lead_trail_empty_lines_=True)
        expected = """
        Some content here
        """
        expected = expected.split("\n")
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.helper(lines_in, expected)

    def test2(self) -> None:
        """
        Test removing headers of various levels.
        """
        lines_in = """
        # Chapter 1
        Content line 1
        ## Section 1.1
        Content line 2
        ### Subsection
        Content line 3
        #### Sub-subsection
        Content line 4
        """
        lines_in = lines_in.split("\n")
        lines_in = hprint.dedent(lines_in, remove_lead_trail_empty_lines_=True)
        expected = """
        Content line 1
        Content line 2
        Content line 3
        Content line 4
        """
        expected = expected.split("\n")
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.helper(lines_in, expected)

    def test3(self) -> None:
        """
        Test headers mixed with regular text and bullet points.
        """
        lines_in = """
        # Header
        - Bullet point 1
        - Bullet point 2
        ## Subheader
        Regular text
        """
        lines_in = lines_in.split("\n")
        lines_in = hprint.dedent(lines_in, remove_lead_trail_empty_lines_=True)
        expected = """
        - Bullet point 1
        - Bullet point 2
        Regular text
        """
        expected = expected.split("\n")
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.helper(lines_in, expected)

    def test4(self) -> None:
        """
        Test input with no headers (should return unchanged).
        """
        lines_in = """
        This is some text
        - Bullet point
        More text
        """
        lines_in = lines_in.split("\n")
        lines_in = hprint.dedent(lines_in, remove_lead_trail_empty_lines_=True)
        expected = lines_in
        self.helper(lines_in, expected)

    def test5(self) -> None:
        """
        Test input with only headers (should return empty list).
        """
        lines_in = """
        # Header 1
        ## Header 2
        ### Header 3
        """
        lines_in = lines_in.split("\n")
        lines_in = hprint.dedent(lines_in, remove_lead_trail_empty_lines_=True)
        expected = []
        self.helper(lines_in, expected)

    def test6(self) -> None:
        """
        Test that empty lines around headers are preserved.
        """
        lines_in = ["", "# Header", "", "Content", ""]
        expected = ["", "", "Content", ""]
        self.helper(lines_in, expected)


# #############################################################################
# Test_preprocess_notes_end_to_end1
# #############################################################################


class Test_preprocess_notes_end_to_end1(hunitest.TestCase):
    """
    Test `preprocess_notes.py` by calling the library function directly.
    """

    def test_run_all1(self) -> None:
        """
        Test type_="pdf".
        """
        # Prepare inputs.
        txt_in = r"""
        # #############################################################################
        # Python: nested functions
        # #############################################################################
        - Functions can be declared in the body of another function
        - E.g., to hide utility functions in the scope of the function that uses them
            ```python
            def print_integers(values):

                def _is_integer(value):
                    try:
                        return value == int(value)
                    except:
                        return False
                for v in values:
                    if _is_integer(v):
                        print(v)
            ```
        """
        txt_in = txt_in.split("\n")
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        # Execute function.
        type_ = "pdf"
        actual = dshdprno._transform_lines(txt_in, type_, is_qa=False)
        actual = "\n".join(actual)
        # Check.
        expected = r"""
        ---
        fontsize: 10pt
        ---
        \let\emph\textit
        \let\uline\underline
        \let\ul\underline
        # Python: nested functions
        - Functions can be declared in the body of another function
        - E.g., to hide utility functions in the scope of the function that uses them
            ```python
            def print_integers(values):

                def _is_integer(value):
                    try:
                        return value == int(value)
                    except:
                        return False
                for v in values:
                    if _is_integer(v):
                        print(v)
            ```
        """
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_preprocess_notes_end_to_end2
# #############################################################################


class Test_preprocess_notes_end_to_end2(hunitest.TestCase):
    """
    Test `preprocess_notes.py` by calling the library function directly.

    # To update the outcomes:
    > cd /Users/saggese/src/umd_msml6101
    > cp -r lectures_source/Lesson*.txt ./helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2/input/

    # To compare inputs and outputs:
    > vimdiff dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2.test_run_all1/{input,output}/Lesson01-Intro.txt
    """

    @pytest.mark.skip(
        reason="Requires external input files to be manually copied"
    )
    def test_run_all1(self) -> None:
        input_dir = self.get_input_dir()
        _LOG.debug("input_dir=%s", input_dir)
        # Find all the files in the `test/input` directory.
        files = glob.glob(os.path.join(input_dir, "*.txt"))
        _LOG.debug("Found %s files", len(files))
        hdbg.dassert_lt(0, len(files))
        for file in files:
            # Read the file.
            text = hio.from_file(file)
            # Run the function.
            # > preprocess_notes.py \
            #     --input lectures_source/Lesson02-Techniques.txt \
            #     --output tmp.notes_to_pdf.preprocess_notes.txt \
            #     --type slides \
            #     --toc_type navigation
            lines = text.split("\n")
            type_ = "slides"
            toc_type = "navigation"
            is_qa = False
            actual = dshdprno._preprocess_lines(lines, type_, toc_type, is_qa)
            # Check.
            actual = "\n".join(actual)
            tag = os.path.basename(file)
            tag = hio.remove_extension(tag, ".txt", check_file_exists=False)
            hdbg.dassert_is_not(tag, None)
            self.check_string(actual, tag=cast(str, tag))


# #############################################################################
# Test_preprocess_notes_end_to_end3
# #############################################################################


class Test_preprocess_notes_end_to_end3(hunitest.TestCase):
    """
    Test `preprocess_notes.py` by calling the library function directly.

    # To update the outcomes:
    > cd /Users/saggese/src/umd_msml6101
    > cp -r lectures_source/Lesson*.txt ./helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2/input/

    # To compare inputs and outputs:
    > vimdiff dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2.test_run_all1/{input,output}/Lesson01-Intro.txt
    """

    @pytest.mark.skip(
        reason="Requires external input files to be manually copied"
    )
    def test_run_all1(self) -> None:
        input_dir = self.get_input_dir()
        _LOG.debug("input_dir=%s", input_dir)
        # Find all the files in the `test/input` directory.
        files = glob.glob(os.path.join(input_dir, "*.txt"))
        _LOG.debug("Found %s files", len(files))
        hdbg.dassert_lt(0, len(files))
        for file in files:
            # Read the file.
            text = hio.from_file(file)
            # Run the function.
            # > preprocess_notes.py \
            #     --input lectures_source/Lesson02-Techniques.txt \
            #     --output tmp.notes_to_pdf.preprocess_notes.txt \
            #     --type slides \
            #     --toc_type navigation
            lines = text.split("\n")
            type_ = "slides"
            toc_type = "navigation"
            is_qa = False
            actual = dshdprno._preprocess_lines(lines, type_, toc_type, is_qa)
            # Check.
            actual = "\n".join(actual)
            tag = os.path.basename(file)
            tag = hio.remove_extension(tag, ".txt", check_file_exists=False)
            hdbg.dassert_is_not(tag, None)
            self.check_string(actual, tag=cast(str, tag))


# #############################################################################
# Test_preprocess_notes_executable1
# #############################################################################


class Test_preprocess_notes_executable1(hunitest.TestCase):
    """
    Test `preprocess_notes.py` using the executable and checked in files.
    """

    @staticmethod
    def helper(in_file: str, out_file: str, type_: str) -> str:
        """
        Execute the end-to-end flow for `preprocess_notes.py` returning the
        output as string.
        """
        hdbg.dassert_path_exists(in_file)
        # Find executable.
        exec_path = hgit.find_file_in_git_tree("preprocess_notes.py")
        hdbg.dassert_path_exists(exec_path)
        # Prepare command.
        cmd = []
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--type {type_}")
        cmd_as_str = " ".join(cmd)
        # Run.
        hsystem.system(cmd_as_str)
        # Check.
        act = hio.from_file(out_file)
        return act  # type: ignore

    def test1(self) -> None:
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "input1.txt")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        type_ = "pdf"
        # Run.
        act = self.helper(in_file, out_file, type_)
        # Check.
        self.check_string(act)

    def test2(self) -> None:
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "input1.txt")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        type_ = "pdf"
        # Run.
        act = self.helper(in_file, out_file, type_)
        # Check.
        self.check_string(act)

    def test3(self) -> None:
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "input1.txt")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        type_ = "pdf"
        # Run.
        act = self.helper(in_file, out_file, type_)
        # Check.
        self.check_string(act)


# #############################################################################
# Test_preprocess_notes_remove_headers1
# #############################################################################


class Test_preprocess_notes_remove_headers1(hunitest.TestCase):
    """
    Test `preprocess_notes.py` with `--toc_type remove_headers`.
    """

    def test1(self) -> None:
        """
        Test the full preprocessing flow with header removal.
        """
        # Prepare inputs.
        txt_in = r"""
        # Chapter 1: Introduction
        This is some introductory content.

        ## Section 1.1: Background
        More content here with some details.

        * What is the main concept?
        The main concept is to understand how preprocessing works.

        ### Subsection 1.1.1
        - Bullet point 1
        - Bullet point 2
        - Bullet point 3

        Some regular text after bullets.

        ## Section 1.2: Examples

        Here is a code block:
        ```python
        def foo():
            # This is a comment with # symbol
            pass
        ```

        # Chapter 2: Advanced Topics

        More advanced content goes here.

        * Another question?
        Answer to the question.
        """
        txt_in = txt_in.split("\n")
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        # Execute function.
        type_ = "pdf"
        toc_type = "remove_headers"
        actual = dshdprno._preprocess_lines(txt_in, type_, toc_type, is_qa=False)
        actual = "\n".join(actual)
        # Check.
        self.check_string(actual)


# #############################################################################
# Test_extract_section
# #############################################################################


class Test_extract_section(hunitest.TestCase):
    """
    Test the `_extract_section()` function.
    """

    def helper(
        self, lines: Sequence[str], section_name: str, expected: Sequence[str] | None
    ) -> None:
        """
        Test helper for _extract_section.

        :param lines: input lines list
        :param section_name: section name to extract
        :param expected: expected extracted lines or None
        """
        # Execute function.
        actual = dshdprno._extract_section(list(lines), section_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting a basic section from a header.
        """
        # Prepare inputs.
        lines = """
        # Section A
        Line 1 of section A
        Line 2 of section A
        # Section B
        Line 1 of section B
        """
        lines = lines.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        expected = """
        Line 1 of section A
        Line 2 of section A
        """
        expected = expected.split("\n")
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        # Run test.
        self.helper(lines, "Section A", expected)

    def test2(self) -> None:
        """
        Test extracting a section that extends to end of file.
        """
        # Prepare inputs.
        lines = """
        # Section A
        Line 1 of A
        # Section B
        Line 1 of B
        Line 2 of B
        """
        lines = lines.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        expected = """
        Line 1 of B
        Line 2 of B
        """
        expected = expected.split("\n")
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        # Run test.
        self.helper(lines, "Section B", expected)

    def test3(self) -> None:
        """
        Test when section is not found returns None.
        """
        # Prepare inputs.
        lines = """
        # Section A
        Content A
        # Section B
        Content B
        """
        lines = lines.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        expected = None
        # Run test.
        self.helper(lines, "Section C", expected)

    def test4(self) -> None:
        """
        Test extracting a section with no content (next header immediately after).
        """
        # Prepare inputs.
        lines = """
        # Section A
        # Section B
        Content B
        """
        lines = lines.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        expected = []
        # Run test.
        self.helper(lines, "Section A", expected)

    def test5(self) -> None:
        """
        Test extracting a section that contains subsections (level 2+ headers).
        """
        # Prepare inputs.
        lines = """
        # Main Section
        Intro text
        ## Subsection 1
        Subsection content
        ### Deep subsection
        Deep content
        # Next Section
        Next content
        """
        lines = lines.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        expected = """
        Intro text
        ## Subsection 1
        Subsection content
        ### Deep subsection
        Deep content
        """
        expected = expected.split("\n")
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        # Run test.
        self.helper(lines, "Main Section", expected)


# #############################################################################
# Test_expand_includes
# #############################################################################


class Test_expand_includes(hunitest.TestCase):
    """
    Test the `_expand_includes()` function.
    """

    def _create_temp_files(
        self, files_to_create: dict[str, str], temp_dir: str
    ) -> None:
        """
        Create temporary files in a directory.

        :param files_to_create: dict of {filename: content} to create
        :param temp_dir: directory to create files in
        """
        for filename, content in files_to_create.items():
            file_path = os.path.join(temp_dir, filename)
            content_dedented = hprint.dedent(
                content.split("\n"), remove_lead_trail_empty_lines_=True
            )
            content_str = "\n".join(content_dedented)
            hio.to_file(file_path, content_str)

    def _run_in_temp_dir(
        self, func, temp_dir: str
    ) -> None:
        """
        Run a function in a temporary directory.

        :param func: callable to run in temp directory
        :param temp_dir: directory to change to
        """
        saved_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            func()
        finally:
            os.chdir(saved_cwd)

    def helper(
        self,
        lines: Sequence[str],
        expected: Sequence[str],
        *,
        files_to_create: dict[str, str] | None = None,
    ) -> None:
        """
        Test helper for _expand_includes.

        :param lines: input lines with include directives
        :param expected: expected expanded lines
        :param files_to_create: dict of {filename: content} to create in temp dir
        """
        # Create temporary files in scratch space.
        temp_dir = self.get_scratch_space()
        if files_to_create:
            self._create_temp_files(files_to_create, temp_dir)
        # Change to temp directory for include path resolution.

        def run_test() -> None:
            # Execute function.
            actual = dshdprno._expand_includes(list(lines))
            # Check outputs.
            self.assertEqual(actual, list(expected))

        self._run_in_temp_dir(run_test, temp_dir)

    def test1(self) -> None:
        """
        Test basic include directive expansion.
        """
        # Prepare inputs.
        lines = [
            "# Main Document",
            '// include:include.md "Included Content"',
            "End of document",
        ]
        expected = [
            "# Main Document",
            "This is included.",
            "More content.",
            "End of document",
        ]
        files_to_create = {
            "include.md": """
                # Included Content
                This is included.
                More content.
                # Another Section
                Not included.
                """,
        }
        # Run test.
        self.helper(lines, expected, files_to_create=files_to_create)

    def test2(self) -> None:
        """
        Test multiple include directives in same file.
        """
        # Prepare inputs.
        lines = [
            '// include:file1.md "Section A"',
            'Text between',
            '// include:file2.md "Section Y"',
        ]
        expected = ["Content A", "Text between", "Content Y"]
        files_to_create = {
            "file1.md": """
                # Section A
                Content A
                # Section B
                Content B
                """,
            "file2.md": """
                # Section X
                Content X
                # Section Y
                Content Y
                """,
        }
        # Run test.
        self.helper(lines, expected, files_to_create=files_to_create)

    def test3(self) -> None:
        """
        Test include directive with spaces in title.
        """
        # Prepare inputs.
        lines = [
            '// include:include.md "Multi Word Title"',
        ]
        expected = ["Included text"]
        files_to_create = {
            "include.md": """
                # Multi Word Title
                Included text
                # Another
                Other
                """,
        }
        # Run test.
        self.helper(lines, expected, files_to_create=files_to_create)

    def test4(self) -> None:
        """
        Test that nested includes raise an error.
        """
        # Prepare inputs.
        lines = [
            '// include:include.md "Section"',
        ]
        files_to_create = {
            "include.md": """
                # Section
                // include:other.md "Nested"
                Content
                """,
        }
        # Create temporary files in scratch space.
        temp_dir = self.get_scratch_space()
        self._create_temp_files(files_to_create, temp_dir)
        # Change to temp directory for include path resolution.

        def run_test() -> None:
            # Execute function and check it raises.
            with self.assertRaises(AssertionError):
                dshdprno._expand_includes(lines)

        self._run_in_temp_dir(run_test, temp_dir)

    def test5(self) -> None:
        """
        Test that missing include file raises error.
        """
        # Prepare inputs.
        lines = [
            '// include:nonexistent.md "Title"',
        ]
        # Run test and expect exception.
        temp_dir = self.get_scratch_space()

        def run_test() -> None:
            with self.assertRaises(AssertionError):
                dshdprno._expand_includes(lines)

        self._run_in_temp_dir(run_test, temp_dir)

    def test6(self) -> None:
        """
        Test that missing section in include file raises error.
        """
        # Prepare inputs.
        lines = [
            '// include:include.md "Missing Section"',
        ]
        files_to_create = {
            "include.md": """
                # Section A
                Content A
                """,
        }
        # Create temporary files in scratch space.
        temp_dir = self.get_scratch_space()
        self._create_temp_files(files_to_create, temp_dir)
        # Change to temp directory for include path resolution.

        def run_test() -> None:
            # Execute function and check it raises.
            with self.assertRaises(AssertionError):
                dshdprno._expand_includes(lines)

        self._run_in_temp_dir(run_test, temp_dir)

    def test7(self) -> None:
        """
        Test that lines without includes pass through unchanged.
        """
        # Prepare inputs.
        lines = [
            "# Header",
            "Some content",
            "// This is a comment, not an include",
            "More content",
        ]
        expected = lines
        # Run test.
        self.helper(lines, expected)
