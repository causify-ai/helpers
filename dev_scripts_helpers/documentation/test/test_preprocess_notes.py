import logging
import os
from collections.abc import Sequence
from typing import Dict, List, Optional


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
        txt_in = "Use `_private_func` or `public_var` for different access levels."
        expected = r"Use \textcolor{blue}{\texttt{\_private\_func}} or \textcolor{blue}{\texttt{public\_var}} for different access levels."
        self.helper(txt_in, expected)

    def test15(self) -> None:
        """
        Test backticks with leading and trailing underscores.
        """
        txt_in = "Call `__init__` or `__dunder__` methods in Python."
        expected = r"Call \textcolor{blue}{\texttt{\_\_init\_\_}} or \textcolor{blue}{\texttt{\_\_dunder\_\_}} methods in Python."
        self.helper(txt_in, expected)


# #############################################################################
# Test_colorize_backticks_integration
# #############################################################################


class Test_colorize_backticks_integration(hunitest.TestCase):
    """
    Test backtick colorization as part of the full preprocessing pipeline.
    """

    def helper(self, txt_in: str, type_: str, expected: str) -> None:
        """
        Test helper for _transform_lines with backtick colorization.

        :param txt_in: input text
        :param type_: output type ("pdf" or "slides")
        :param expected: expected output text
        """
        # Prepare inputs.
        txt_in_lines = txt_in.split("\n")
        txt_in_lines = hprint.dedent(
            txt_in_lines, remove_lead_trail_empty_lines_=True
        )
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

    def helper(self, txt_in: str, do_continue_exp: bool, expected: str) -> None:
        """
        Helper method to test _process_question_to_markdown function.

        :param txt_in: input text
        :param do_continue_exp: expected do_continue flag
        :param expected: expected output text
        """
        # Run test.
        do_continue, actual = dshdprno._process_question_to_markdown(txt_in)
        # Check outputs.
        self.assertEqual(do_continue, do_continue_exp)
        self.assert_equal(actual, expected)

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


# #############################################################################
# Test_remove_headers1
# #############################################################################


class Test_remove_headers1(hunitest.TestCase):
    """
    Test the `_remove_headers()` function.
    """

    def helper(
        self,
        lines_in_str: str,
        expected_str: str,
        *,
        max_level: int = 999,
    ) -> None:
        """
        Helper method to test the _remove_headers function.

        :param lines_in_str: input text with dedent applied
        :param expected_str: expected output text with dedent applied
        :param max_level: maximum level of headers to consider (default:
            999 to remove all headers)
        """
        # Prepare inputs.
        lines_in = lines_in_str.split("\n")
        lines_in = hprint.dedent(lines_in, remove_lead_trail_empty_lines_=True)
        expected = expected_str.split("\n")
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdprno._remove_headers(lines_in, max_level)
        # Check outputs.
        actual_str = "\n".join(actual)
        expected_str_final = "\n".join(expected)
        self.assert_equal(actual_str, expected_str_final)

    def test1(self) -> None:
        """
        Test removing a single level 1 header.
        """
        # Prepare inputs.
        lines_in = """
        # Chapter 1
        Some content here
        """
        expected = """
        Some content here
        """
        # Run test.
        self.helper(lines_in, expected)

    def test2(self) -> None:
        """
        Test removing headers of various levels.
        """
        # Prepare inputs.
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
        expected = """
        Content line 1
        Content line 2
        Content line 3
        Content line 4
        """
        # Run test.
        self.helper(lines_in, expected)

    def test3(self) -> None:
        """
        Test headers mixed with regular text and bullet points.
        """
        # Prepare inputs.
        lines_in = """
        # Header
        - Bullet point 1
        - Bullet point 2
        ## Subheader
        Regular text
        """
        expected = """
        - Bullet point 1
        - Bullet point 2
        Regular text
        """
        # Run test.
        self.helper(lines_in, expected)

    def test4(self) -> None:
        """
        Test input with no headers (should return unchanged).
        """
        # Prepare inputs.
        lines_in = """
        This is some text
        - Bullet point
        More text
        """
        expected = lines_in
        # Run test.
        self.helper(lines_in, expected)

    def test5(self) -> None:
        """
        Test input with only headers (should return empty list).
        """
        # Prepare inputs.
        lines_in = """
        # Header 1
        ## Header 2
        ### Header 3
        """
        expected = ""
        # Run test.
        self.helper(lines_in, expected)

    def test6(self) -> None:
        """
        Test that empty lines around headers are preserved.
        """
        # Prepare inputs.
        lines_in = ["", "# Header", "", "Content", ""]
        lines_in = hprint.dedent(lines_in, remove_lead_trail_empty_lines_=False)
        expected = ["", "", "Content", ""]
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=False)
        # Run test.
        actual = dshdprno._remove_headers(lines_in, 999)
        # Check outputs.
        actual_str = "\n".join(actual)
        expected_str = "\n".join(expected)
        self.assert_equal(actual_str, expected_str)


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
        self,
        lines_str: str,
        section_name: str,
        expected_str: Optional[str],
    ) -> None:
        """
        Test helper for _extract_section.

        :param lines_str: input text with dedent applied
        :param section_name: section name to extract
        :param expected_str: expected extracted text or None
        """
        # Prepare inputs.
        lines_str_dedented = hprint.dedent(lines_str)
        lines = lines_str_dedented.strip().split("\n") if lines_str_dedented.strip() else []
        # Run test.
        actual = dshdprno._extract_section(lines, section_name)
        # Check outputs.
        if expected_str is None:
            self.assertEqual(actual, None)
        else:
            expected_str_dedented = hprint.dedent(expected_str)
            expected = expected_str_dedented.strip().split("\n") if expected_str_dedented.strip() else []
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
        expected = """
        Line 1 of section A
        Line 2 of section A
        """
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
        expected = """
        Line 1 of B
        Line 2 of B
        """
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
        expected = ""
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
        expected = """
        Intro text
        ## Subsection 1
        Subsection content
        ### Deep subsection
        Deep content
        """
        # Run test.
        self.helper(lines, "Main Section", expected)


# #############################################################################
# Test_expand_includes
# #############################################################################


# TODO(gp): Can we simplify this without using the temp dir?
class Test_expand_includes(hunitest.TestCase):
    """
    Test the `_expand_includes()` function.
    """

    def _create_temp_files(
        self, files_to_create: Dict[str, str], temp_dir: str
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

    def _run_in_temp_dir(self, func, temp_dir: str) -> None:
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
        files_to_create: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Test helper for _expand_includes.

        :param lines: input lines with include directives
        :param expected: expected expanded lines
        :param files_to_create: dict of {filename: content} to create in temp dir
        """
        # Prepare inputs.
        temp_dir = self.get_scratch_space()
        if files_to_create:
            self._create_temp_files(files_to_create, temp_dir)

        def run_test() -> None:
            # Run test.
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
            "Text between",
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

    def test8(self) -> None:
        """
        Test include directive with absolute file path.
        """
        # Prepare inputs.
        temp_dir = self.get_scratch_space()
        files_to_create = {
            "include.md": """
                # Section
                Included content
                """,
        }
        self._create_temp_files(files_to_create, temp_dir)
        # Use absolute path in include directive.
        abs_path = os.path.join(temp_dir, "include.md")
        lines = [
            f'// include:{abs_path} "Section"',
        ]
        expected = ["Included content"]

        def run_test() -> None:
            actual = dshdprno._expand_includes(lines)
            self.assertEqual(actual, expected)

        self._run_in_temp_dir(run_test, temp_dir)


# #############################################################################
# Test_process_question_to_slides
# #############################################################################


class Test_process_question_to_slides(hunitest.TestCase):
    """
    Test the `_process_question_to_slides()` function.
    """

    def helper(
        self,
        txt_in: str,
        expected_continue: bool,
        expected_output: str,
        *,
        level: int = 4,
    ) -> None:
        """
        Helper method to test _process_question_to_slides function.

        :param txt_in: input text
        :param expected_continue: expected should_continue flag
        :param expected_output: expected output text
        :param level: header level
        """
        # Run test.
        actual_continue, actual_output = dshdprno._process_question_to_slides(
            txt_in, level=level
        )
        # Check outputs.
        self.assertEqual(actual_continue, expected_continue)
        self.assert_equal(actual_output, expected_output)

    def test1(self) -> None:
        """
        Test single-star question converted to level-4 header.
        """
        txt_in = "* What is this?"
        expected_continue = True
        expected_output = "#### What is this?"
        self.helper(txt_in, expected_continue, expected_output)

    def test2(self) -> None:
        """
        Test double-star question converted to level-4 header.
        """
        txt_in = "** What is this?"
        expected_continue = True
        expected_output = "#### What is this?"
        self.helper(txt_in, expected_continue, expected_output)

    def test3(self) -> None:
        """
        Test colon-question converted to level-4 header.
        """
        txt_in = "*: What is this?"
        expected_continue = True
        expected_output = "#### What is this?"
        self.helper(txt_in, expected_continue, expected_output)

    def test4(self) -> None:
        """
        Test line without question marker returns False.
        """
        txt_in = "This is regular text"
        expected_continue = False
        expected_output = txt_in
        self.helper(txt_in, expected_continue, expected_output)

    def test5(self) -> None:
        """
        Test custom header level parameter.
        """
        txt_in = "* Question text"
        expected_continue = True
        expected_output = "## Question text"
        self.helper(txt_in, expected_continue, expected_output, level=2)

    def test6(self) -> None:
        """
        Test question with trailing spaces.
        """
        txt_in = "* Question text   "
        expected_continue = True
        expected_output = "#### Question text   "
        self.helper(txt_in, expected_continue, expected_output)


# #############################################################################
# Test_process_abbreviations
# #############################################################################


class Test_process_abbreviations(hunitest.TestCase):
    """
    Test the `_process_abbreviations()` function.
    """

    def helper(self, txt_in: str, expected: str) -> None:
        """
        Helper method to test _process_abbreviations function.

        :param txt_in: input text
        :param expected: expected output text
        """
        # Run test.
        actual = dshdprno._process_abbreviations(txt_in)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test => replacement with spaces.
        """
        txt_in = r"A => B"
        expected = r"A $\implies$ B"
        self.helper(txt_in, expected)

    def test2(self) -> None:
        """
        Test no replacement without spaces around operator.
        """
        txt_in = "A=>B"
        expected = "A=>B"
        self.helper(txt_in, expected)

    def test3(self) -> None:
        """
        Test multiple replacements in one line.
        """
        txt_in = r"X => Y => Z"
        expected = r"X $\implies$ Y $\implies$ Z"
        self.helper(txt_in, expected)

    def test4(self) -> None:
        """
        Test line without abbreviations remains unchanged.
        """
        txt_in = "This line has no abbreviations"
        expected = txt_in
        self.helper(txt_in, expected)


# #############################################################################
# Test_process_enumerated_list
# #############################################################################


class Test_process_enumerated_list(hunitest.TestCase):
    """
    Test the `_process_enumerated_list()` function.
    """

    def helper(self, txt_in: str, expected: str) -> None:
        """
        Helper method to test _process_enumerated_list function.

        :param txt_in: input text
        :param expected: expected output text
        """
        # Run test.
        actual = dshdprno._process_enumerated_list(txt_in)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test basic enumerated list with parenthesis.
        """
        txt_in = "1) Item one"
        expected = "1. Item one"
        self.helper(txt_in, expected)

    def test2(self) -> None:
        """
        Test enumerated list with indentation.
        """
        txt_in = "  2) Item two"
        expected = "  2. Item two"
        self.helper(txt_in, expected)

    def test3(self) -> None:
        """
        Test line without enumeration remains unchanged.
        """
        txt_in = "Regular text without numbering"
        expected = txt_in
        self.helper(txt_in, expected)

    def test4(self) -> None:
        """
        Test numbered line without parenthesis remains unchanged.
        """
        txt_in = "1. Already formatted"
        expected = txt_in
        self.helper(txt_in, expected)


# #############################################################################
# Test_transform_lines_slides
# #############################################################################


class Test_transform_lines_slides(hunitest.TestCase):
    """
    Test the `_transform_lines()` function with type_='slides'.
    """

    def helper(
        self,
        lines: List[str],
        type_: str,
        is_qa: bool,
        expected: List[str],
        *,
        actions: Optional[List[str]] = None,
    ) -> None:
        """
        Helper method to test _transform_lines function.

        :param lines: input lines
        :param type_: output type
        :param is_qa: whether input is QA format
        :param expected: expected output lines
        :param actions: optional actions to perform
        """
        # Run test.
        actual = dshdprno._transform_lines(lines, type_, is_qa, actions=actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test slides processing converts questions to headers.
        """
        lines = [
            "---",
            "# Main Slide",
            "* What is this?",
            "Some content",
        ]
        expected = [
            "---",
            "# Main Slide",
            "#### What is this?",
            "Some content",
        ]
        self.helper(lines, "slides", False, expected)

    def test2(self) -> None:
        """
        Test slides with backticks colorized properly.
        """
        lines = [
            "---",
            "Content with `code` inline",
        ]
        expected = [
            "---",
            r"Content with \textcolor{blue}{\texttt{code}} inline",
        ]
        self.helper(lines, "slides", False, expected)

    def test3(self) -> None:
        """
        Test slides processing with abbreviations.
        """
        lines = [
            "---",
            r"A => B is implied",
        ]
        expected = [
            "---",
            r"A $\implies$ B is implied",
        ]
        self.helper(lines, "slides", False, expected)


# #############################################################################
# Test_preprocess_lines_toc
# #############################################################################


class Test_preprocess_lines_toc(hunitest.TestCase):
    """
    Test the `_preprocess_lines()` function with different toc_type values.
    """

    def helper(
        self,
        lines: List[str],
        type_: str,
        toc_type: str,
        is_qa: bool,
        expected_contains: str,
    ) -> None:
        """
        Helper method to test _preprocess_lines function.

        :param lines: input lines
        :param type_: output type
        :param toc_type: type of TOC
        :param is_qa: whether input is QA format
        :param expected_contains: string that output should contain
        """
        # Run test.
        actual = dshdprno._preprocess_lines(lines, type_, toc_type, is_qa)
        # Check outputs.
        self.assertIn(expected_contains, "\n".join(actual))

    def test1(self) -> None:
        """
        Test toc_type='none' with basic processing.
        """
        lines = [
            "---",
            "# Header",
            "Content",
        ]
        self.helper(lines, "pdf", "none", False, "# Header")

    def test2(self) -> None:
        """
        Test toc_type='remove_headers' removes appropriate headers.
        """
        # Prepare inputs.
        lines = [
            "---",
            "# Header 1",
            "## Header 2",
            "#### Header 4",
            "Content",
        ]
        # Run test.
        actual = dshdprno._preprocess_lines(
            lines, "pdf", "remove_headers", False
        )
        actual_str = "\n".join(actual)
        # Check outputs.
        expected_dict = {
            "# Header 1": False,
            "## Header 2": False,
            "#### Header 4": True,
        }
        for text, should_be_present in expected_dict.items():
            is_present = text in actual_str
            self.assertEqual(is_present, should_be_present)


# #############################################################################
# Test_transform_lines_qa
# #############################################################################


class Test_transform_lines_qa(hunitest.TestCase):
    """
    Test the `_transform_lines()` function with is_qa=True.
    """

    def helper(
        self,
        lines: List[str],
        type_: str,
        is_qa: bool,
        expected: List[str],
    ) -> None:
        """
        Helper method to test _transform_lines function for QA.

        :param lines: input lines
        :param type_: output type
        :param is_qa: whether input is QA format
        :param expected: expected output lines
        """
        # Run test.
        actual = dshdprno._transform_lines(lines, type_, is_qa)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test QA file processing adds indentation to non-header lines.
        """
        # Prepare inputs.
        lines = [
            "---",
            "# Chapter Title",
            "Question text",
            "Answer text",
        ]
        # Prepare outputs.
        expected = [
            "  ---",
            "# Chapter Title",
            "  Question text",
            "  Answer text",
        ]
        # Run test.
        self.helper(lines, "pdf", True, expected)

    def test2(self) -> None:
        """
        Test QA file removes empty lines unless adjacent to special content.
        """
        # Prepare inputs.
        lines = [
            "---",
            "# Chapter",
            "Line 1",
            "",
            "Line 2",
        ]
        # Prepare outputs.
        expected = [
            "  ---",
            "# Chapter",
            "  Line 1",
            "  Line 2",
        ]
        # Run test.
        self.helper(lines, "pdf", True, expected)

    def test3(self) -> None:
        """
        Test QA file preserves empty lines before code blocks.
        """
        # Prepare inputs.
        lines = [
            "---",
            "# Chapter",
            "Text",
            "",
            "```python",
            "code",
            "```",
        ]
        # Prepare outputs.
        expected = [
            "  ---",
            "# Chapter",
            "  Text",
            "",
            "  ```python",
            "  code",
            "  ```",
        ]
        # Run test.
        self.helper(lines, "pdf", True, expected)


# #############################################################################
# Test_transform_lines_actions
# #############################################################################


class Test_transform_lines_actions(hunitest.TestCase):
    """
    Test the `_transform_lines()` function with various actions.
    """

    def helper(
        self,
        lines: List[str],
        type_: str,
        is_qa: bool,
        expected: List[str],
        *,
        actions: Optional[List[str]] = None,
    ) -> None:
        """
        Helper method to test _transform_lines function with actions.

        :param lines: input lines
        :param type_: output type
        :param is_qa: whether input is QA format
        :param expected: expected output lines
        :param actions: optional actions to perform
        """
        actual = dshdprno._transform_lines(lines, type_, is_qa, actions=actions)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test slides processing with process_links action.
        """
        # Prepare inputs.
        lines = [
            "---",
            "# Title",
            "[Link text](https://example.com)",
        ]
        # Prepare outputs.
        expected = [
            "---",
            "# Title",
            r"[\textcolor{blue}{\underline{Link text}}](https://example.com)",
        ]
        # Run test.
        self.helper(lines, "slides", False, expected, actions=["process_links"])

    def test2(self) -> None:
        """
        Test slides processing with colorize_bullets action.
        """
        # Prepare inputs.
        lines = [
            "---",
            "#### Slide Title",
            "- Bullet point 1",
            "- Bullet point 2",
        ]
        # Prepare outputs.
        expected = [
            "---",
            "#### Slide Title",
            "- Bullet point 1",
            "- Bullet point 2",
        ]
        # Run test.
        self.helper(lines, "slides", False, expected, actions=["colorize_bullets"])


# #############################################################################
# Test_preprocess_lines_navigation
# #############################################################################


class Test_preprocess_lines_navigation(hunitest.TestCase):
    """
    Test the `_preprocess_lines()` function with toc_type='navigation'.
    """

    def test1(self) -> None:
        """
        Test toc_type='navigation' with type_='slides'.
        """
        lines = [
            "---",
            "# Part 1",
            "## Section 1.1",
            "Content here",
        ]
        actual = dshdprno._preprocess_lines(lines, "slides", "navigation", False)
        # Navigation processing should add slides
        self.assertGreaterEqual(len(actual), len(lines))


# #############################################################################
# Test_validate_slide_names
# #############################################################################


class Test_validate_slide_names(hunitest.TestCase):
    """
    Test the `_validate_slide_names()` function.
    """

    def helper_valid(self, lines: List[str]) -> None:
        """
        Helper method to test valid slide names.

        :param lines: list of lines to validate
        """
        # Run test.
        dshdprno._validate_slide_names(lines)

    def helper_invalid(self, lines: List[str], expected_line_num: int) -> None:
        """
        Helper method to test invalid slide names.

        :param lines: list of lines to validate
        :param expected_line_num: expected line number of the invalid slide
        """
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshdprno._validate_slide_names(lines)
        # Check outputs.
        expected_substr = f"line {expected_line_num}"
        self.assertIn(expected_substr, str(cm.exception))

    def test1(self) -> None:
        """
        Test slides with valid titles.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1 Title",
            "Some content",
            "* Slide 2 Title",
            "More content",
        ]
        # Run test.
        self.helper_valid(lines)

    def test2(self) -> None:
        """
        Test slide with whitespace-only title.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1 Title",
            "*   ",
            "Some content",
        ]
        expected_line_num = 2
        # Run test.
        self.helper_invalid(lines, expected_line_num)

    def test3(self) -> None:
        """
        Test multiple invalid slides.
        """
        # Prepare inputs.
        lines = [
            "* Valid Slide",
            "*   ",
            "Content",
            "*    ",
            "More content",
        ]
        expected_line_num = 2
        # Run test.
        self.helper_invalid(lines, expected_line_num)

    def test4(self) -> None:
        """
        Test multiple slides with first one invalid.
        """
        # Prepare inputs.
        lines = [
            "*   ",
            "Content",
            "* Valid Slide",
            "More content",
        ]
        expected_line_num = 1
        # Run test.
        self.helper_invalid(lines, expected_line_num)

    def test5(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        lines: List[str] = []
        # Run test.
        self.helper_valid(lines)

    def test6(self) -> None:
        """
        Test no slides in input.
        """
        # Prepare inputs.
        lines = [
            "Some content",
            "More content",
            "No slides here",
        ]
        # Run test.
        self.helper_valid(lines)


# #############################################################################
# Test_assert_no_existing_counters
# #############################################################################


class Test_assert_no_existing_counters(hunitest.TestCase):
    """
    Test the `_assert_no_existing_counters()` function.
    """

    def helper_valid(self, lines: List[str]) -> None:
        """
        Helper method to test valid slides without counters.

        :param lines: list of lines to validate
        """
        # Run test.
        dshdprno._assert_no_existing_counters(lines)

    def helper_invalid(self, lines: List[str]) -> None:
        """
        Helper method to test slides with existing counters.

        :param lines: list of lines to validate
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdprno._assert_no_existing_counters(lines)

    def test1(self) -> None:
        """
        Test slides without counter format.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1",
            "* Slide 2",
        ]
        # Run test.
        self.helper_valid(lines)

    def test2(self) -> None:
        """
        Test slide with existing counter format.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1",
            "* Slide 2 (1/2)",
        ]
        # Run test.
        self.helper_invalid(lines)


# #############################################################################
# Test_add_duplicate_slide_counters
# #############################################################################


class Test_add_duplicate_slide_counters(hunitest.TestCase):
    """
    Test the `_add_duplicate_slide_counters()` function.
    """

    def helper(self, lines: List[str], expected: List[str]) -> None:
        """
        Helper method to test counter addition.

        :param lines: input lines
        :param expected: expected output lines
        """
        # Run test.
        actual = dshdprno._add_duplicate_slide_counters(lines)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test no duplicates.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1",
            "Content",
            "* Slide 2",
            "Content",
        ]
        # Expected: no changes.
        expected = lines
        # Run test.
        self.helper(lines, expected)

    def test2(self) -> None:
        """
        Test two slides with same name.
        """
        # Prepare inputs.
        lines = [
            "* Demo",
            "Content 1",
            "* Demo",
            "Content 2",
        ]
        # Expected: counters added.
        expected = [
            "* Demo (1/2)",
            "Content 1",
            "* Demo (2/2)",
            "Content 2",
        ]
        # Run test.
        self.helper(lines, expected)

    def test3(self) -> None:
        """
        Test three slides with same name (non-consecutive).
        """
        # Prepare inputs.
        lines = [
            "* Example",
            "Content 1",
            "* Other",
            "Content",
            "* Example",
            "Content 2",
            "* Example",
            "Content 3",
        ]
        # Expected: all Example slides get counters.
        expected = [
            "* Example (1/3)",
            "Content 1",
            "* Other",
            "Content",
            "* Example (2/3)",
            "Content 2",
            "* Example (3/3)",
            "Content 3",
        ]
        # Run test.
        self.helper(lines, expected)

    def test4(self) -> None:
        """
        Test mixed duplicates and unique.
        """
        # Prepare inputs.
        lines = [
            "* Unique",
            "* Dup",
            "* Other",
            "* Dup",
        ]
        # Expected: only Dup gets counters.
        expected = [
            "* Unique",
            "* Dup (1/2)",
            "* Other",
            "* Dup (2/2)",
        ]
        # Run test.
        self.helper(lines, expected)

    def test5(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        lines: List[str] = []
        # Expected: no changes.
        expected = lines
        # Run test.
        self.helper(lines, expected)


# #############################################################################
# Test_validate_unique_slide_names
# #############################################################################


class Test_validate_unique_slide_names(hunitest.TestCase):
    """
    Test the `_validate_unique_slide_names()` function.
    """

    def helper_valid(self, lines: List[str]) -> None:
        """
        Helper method to test valid unique names.

        :param lines: list of lines to validate
        """
        # Run test.
        dshdprno._validate_unique_slide_names(lines)

    def helper_invalid(self, lines: List[str]) -> None:
        """
        Helper method to test invalid duplicate names.

        :param lines: list of lines to validate
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdprno._validate_unique_slide_names(lines)

    def test1(self) -> None:
        """
        Test all unique slide names.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1",
            "* Slide 2",
            "* Slide 3 (1/2)",
        ]
        # Run test.
        self.helper_valid(lines)

    def test2(self) -> None:
        """
        Test duplicate slide names.
        """
        # Prepare inputs.
        lines = [
            "* Slide 1",
            "* Slide 1",
        ]
        # Run test.
        self.helper_invalid(lines)

    def test3(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        lines: list = []
        # Run test.
        self.helper_valid(lines)
