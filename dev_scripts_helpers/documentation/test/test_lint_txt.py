import logging
import os
from typing import Optional

import pytest

import dev_scripts_helpers.documentation.lint_txt as dshdlitx
import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__handle_empty_lines
# #############################################################################


class Test__handle_empty_lines(hunitest.TestCase):
    """
    Test the _handle_empty_lines function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _handle_empty_lines.

        :param txt: Input text to process
        :param expected: Expected output after handling empty lines
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._handle_empty_lines(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing single empty line after header.
        """
        # Prepare inputs.
        txt = """
        ## Front Matter (YAML)

        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Prepare outputs.
        expected = """
        ## Front Matter (YAML)
        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing multiple empty lines after header.
        """
        # Prepare inputs.
        txt = """
        # Front Matter (YAML)



        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Prepare outputs.
        expected = """
        # Front Matter (YAML)
        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing empty lines between text and code block.
        """
        # Prepare inputs.
        txt = """
        - Example:


          ```markdown
          The main advantages are:
          - **First advantage**: Description here
          - **Second advantage**: Description here
            - Sub-point with details
            - Another sub-point
          ```
        """
        # Prepare outputs.
        expected = """
        - Example:
          ```markdown
          The main advantages are:
          - **First advantage**: Description here
          - **Second advantage**: Description here
            - Sub-point with details
            - Another sub-point
          ```
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test with multiple headers and code blocks.
        """
        # Prepare inputs.
        txt = """
        # Header 1

        Some text here.

        ## Header 2


        More text here.


        ```python
        def foo():
            pass
        ```
        """
        # Prepare outputs.
        expected = """
        # Header 1
        Some text here.

        ## Header 2
        More text here.
        ```python
        def foo():
            pass
        ```
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test that text without headers or code blocks remains unchanged.
        """
        # Prepare inputs.
        txt = """
        First line

        Second line

        Third line
        """
        # Prepare outputs.
        expected = """
        First line

        Second line

        Third line
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test that empty lines between text without code blocks are preserved.
        """
        # Prepare inputs.
        txt = """
        Line 1


        Line 2
        """
        # Prepare outputs.
        expected = """
        Line 1


        Line 2
        """
        # Run test.
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test with different header levels.
        """
        # Prepare inputs.
        txt = """
        # Level 1

        ## Level 2

        ### Level 3

        #### Level 4

        Text content
        """
        # Prepare outputs.
        expected = """
        # Level 1
        ## Level 2
        ### Level 3
        #### Level 4
        Text content
        """
        # Run test.
        self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test code block with different language tags.
        """
        # Prepare inputs.
        txt = """
        Example code:


        ```javascript
        console.log("Hello");
        ```
        """
        # Prepare outputs.
        expected = """
        Example code:
        ```javascript
        console.log("Hello");
        ```
        """
        # Run test.
        self.helper(txt, expected)

    def test10(self) -> None:
        """
        Test that empty lines inside code blocks are preserved.
        """
        # Prepare inputs.
        txt = """
        Example:

        ```python
        def foo():
            pass

        def bar():
            pass
        ```
        """
        # Prepare outputs.
        expected = """
        Example:
        ```python
        def foo():
            pass

        def bar():
            pass
        ```
        """
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_remove_page_separators
# #############################################################################


class Test_remove_page_separators(hunitest.TestCase):
    """
    Test the _remove_page_separators function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _remove_page_separators.

        :param txt: Input text to process
        :param expected: Expected output after removing page separators
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._remove_page_separators(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing a single page separator line.
        """
        # Prepare inputs.
        txt = """
        First section
        ---
        Second section
        """
        # Prepare outputs.
        expected = """
        First section

        Second section
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing multiple page separator lines.
        """
        # Prepare inputs.
        txt = """
        Section 1
        ---
        Section 2
        ---
        Section 3
        """
        # Prepare outputs.
        expected = """
        Section 1

        Section 2

        Section 3
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing page separators with trailing spaces.
        """
        # Prepare inputs.
        txt = """
        Content before
        ---
        Content after
        """
        # Prepare outputs.
        expected = """
        Content before

        Content after
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test that text without separators remains unchanged.
        """
        # Prepare inputs.
        txt = """
        First line
        Second line
        Third line
        """
        # Prepare outputs.
        expected = """
        First line
        Second line
        Third line
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test that separators within text content are preserved.
        """
        # Prepare inputs.
        txt = """
        Example:
        This is a --- dash in text
        And another line
        """
        # Prepare outputs.
        expected = """
        Example:
        This is a --- dash in text
        And another line
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_add_blank_lines_between_headers
# #############################################################################


class Test_add_blank_lines_between_headers(hunitest.TestCase):
    """
    Test the _add_blank_lines_between_headers function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _add_blank_lines_between_headers.

        :param txt: Input text to process
        :param expected: Expected output after adding blank lines
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._add_blank_lines_between_headers(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test adding blank line between two consecutive headers.
        """
        # Prepare inputs.
        txt = """
        # Conversational Diagram Designer (CDD)
        ## 1. Overview
        Conversational Diagram Designer (CDD) is a browser-based diagramming tool.
        """
        # Prepare outputs.
        expected = """
        # Conversational Diagram Designer (CDD)

        ## 1. Overview
        Conversational Diagram Designer (CDD) is a browser-based diagramming tool.
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test adding blank lines between multiple consecutive headers.
        """
        # Prepare inputs.
        txt = """
        # Title
        ## Subtitle
        ### Subsubtitle
        #### Deep subtitle
        Content here
        """
        # Prepare outputs.
        expected = """
        # Title

        ## Subtitle

        ### Subsubtitle

        #### Deep subtitle
        Content here
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test that non-consecutive headers are not affected.
        """
        # Prepare inputs.
        txt = """
        # Header 1

        Some text here.

        ## Header 2

        More text here.
        """
        # Prepare outputs.
        expected = """
        # Header 1

        Some text here.

        ## Header 2

        More text here.
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test mixed consecutive and non-consecutive headers.
        """
        # Prepare inputs.
        txt = """
        # Main Title
        ## Section 1
        Content for section 1.

        ## Section 2
        ### Subsection 2.1
        More content.
        """
        # Prepare outputs.
        expected = """
        # Main Title

        ## Section 1
        Content for section 1.

        ## Section 2

        ### Subsection 2.1
        More content.
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with text without headers.
        """
        # Prepare inputs.
        txt = """
        First line
        Second line
        Third line
        """
        # Prepare outputs.
        expected = """
        First line
        Second line
        Third line
        """
        # Run test.
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test with only one header.
        """
        # Prepare inputs.
        txt = """
        # Single Header
        Some content below.
        """
        # Prepare outputs.
        expected = """
        # Single Header
        Some content below.
        """
        # Run test.
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test headers at beginning and end of file.
        """
        # Prepare inputs.
        txt = """
        # First Header
        ## Second Header
        """
        # Prepare outputs.
        expected = """
        # First Header

        ## Second Header
        """
        # Run test.
        self.helper(txt, expected)


def _get_text1() -> str:
    """
    Get sample text containing mathematical equations in LaTeX format.
    """
    txt = r"""
    * Gradient descent for logistic regression
    - The typical implementations of gradient descent (basic or advanced) need
      two inputs:
        - The cost function $E_{in}(\vw)$ (to monitor convergence)
        - The gradient of the cost function
          $\frac{\partial E}{w_j} \text{ for all } j$ (to optimize)
    - The cost function is:
        $$E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)$$

    - In case of general probabilistic model $h(\vx)$ in \{0, 1\}):
        $$
        E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)
        $$

    - In case of logistic regression in \{+1, -1\}:
        $$E_{in}(\vw) = \frac{1}{N} \sum_i \log(1 + \exp(-y_i \vw^T \vx_i))$$

    - It can be proven that the function $E_{in}(\vw)$ to minimize is convex in
      $\vw$ (sum of exponentials and flipped exponentials is convex and log is
      monotone)"""
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    return txt


# #############################################################################
# Test_lint_txt1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_lint_txt1(hunitest.TestCase):
    """
    Test the text preprocessing functionality.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Process text with `_preprocess_txt()` and compare with expected output.

        :param txt: Input text to preprocess
        :param expected: Expected output after preprocessing
        """
        # Prepare inputs.
        txt = txt.split("\n")
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        # Run.
        actual = dshdlitx._preprocess_txt(txt)
        # Check.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    # //////////////////////////////////////////////////////////////////////////

    def test_preprocess1(self) -> None:
        txt = r"""$$E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)$$"""
        expected = r"""
        $$
        E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)
        $$"""
        self.helper(txt, expected)

    def test_preprocess2(self) -> None:
        txt = r"""
        $$E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)$$"""
        expected = r"""
        $$
        E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)
        $$"""
        self.helper(txt, expected)

    def test_preprocess3(self) -> None:
        txt = _get_text1()
        expected = r"""
        - STARGradient descent for logistic regression
        - The typical implementations of gradient descent (basic or advanced) need
          two inputs:
            - The cost function $E_{in}(\vw)$ (to monitor convergence)
            - The gradient of the cost function
              $\frac{\partial E}{w_j} \text{ for all } j$ (to optimize)
        - The cost function is:
            $$
            E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)
            $$

        - In case of general probabilistic model $h(\vx)$ in \{0, 1\}):
            $$
            E_{in}(\vw) = \frac{1}{N} \sum_i \big(
            -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
            \big)
            $$

        - In case of logistic regression in \{+1, -1\}:
            $$
            E_{in}(\vw) = \frac{1}{N} \sum_i \log(1 + \exp(-y_i \vw^T \vx_i))
            $$

        - It can be proven that the function $E_{in}(\vw)$ to minimize is convex in
          $\vw$ (sum of exponentials and flipped exponentials is convex and log is
          monotone)"""
        self.helper(txt, expected)

    def test_preprocess4(self) -> None:
        txt = r"""
        # #########################
        # test
        # #############################################################################"""
        expected = r"""# test"""
        self.helper(txt, expected)

    def test_preprocess5(self) -> None:
        txt = r"""
        ## ////////////////
        # test
        # ////////////////"""
        expected = r"""# test"""
        self.helper(txt, expected)


# #############################################################################
# Test_lint_txt2
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_lint_txt2(hunitest.TestCase):
    @staticmethod
    def get_text_problematic_for_prettier1() -> str:
        txt = r"""
        * Python formatting
        - Python has several built-in ways of formatting strings
          1) `%` format operator
          2) `format` and `str.format`


        * `%` format operator
        - Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        return txt

    def helper(self, txt: str, expected: Optional[str], file_name: str) -> str:
        """
        Helper function to process the given text and compare the result with
        the expected output.

        :param txt: The text to be processed.
        :param expected: The expected output after processing the text. If
            None, no comparison is made.
        :param file_name: The name of the file to be used for
            processing.
        :return: The processed text.
        """
        # Prepare inputs.
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        txt = txt.split("\n")
        file_name = os.path.join(self.get_scratch_space(), file_name)
        # Run function.
        actual = dshdlitx._perform_actions(txt, file_name)
        # Check.
        actual = "\n".join(actual)
        if expected:
            expected = hprint.dedent(
                expected, remove_lead_trail_empty_lines_=True
            )
            self.assert_equal(actual, expected)
        return actual

    # //////////////////////////////////////////////////////////////////////////

    def test_process1(self) -> None:
        txt = _get_text1()
        expected = None
        file_name = "test.txt"
        actual = self.helper(txt, expected, file_name)
        self.check_string(actual)

    def test_process2(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        expected = r"""
        * Good Time Management

        1. Choose the right tasks
           - Avoid non-essential tasks
        """
        file_name = "test.txt"
        self.helper(txt, expected, file_name)

    def test_process3(self) -> None:
        """
        Run the text linter on a md file.
        """
        txt = r"""
        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        expected = r"""
        <!-- toc -->

        - [Good](#good)
          * [Bad](#bad)

        <!-- tocstop -->

        # Good
        - Good time management
          1. Choose the right tasks
          - Avoid non-essential tasks

        ## Bad
        - Hello
          - World
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)

    def test_process4(self) -> None:
        """
        Check that no replacement happens inside a ``` block.
        """
        txt = r"""
        <!-- toc -->
        <!-- tocstop -->

        - Good
        - Hello

        ```test
        - hello
            - world
        1) oh no!
        ```
        """
        expected = r"""
        <!-- toc -->



        <!-- tocstop -->

        - Good
        - Hello
        ```test
        - hello
            - world
        1) oh no!
        ```
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)

    def test_process_prettier_bug1(self) -> None:
        """
        For some reason prettier replaces - with * when there are 2 empty lines.
        """
        txt = self.get_text_problematic_for_prettier1()
        actual = hdocexec.prettier_on_str(txt, file_type="txt")
        expected = r"""
        - Python formatting

        * Python has several built-in ways of formatting strings
          1. `%` format operator
          2. `format` and `str.format`

        - `%` format operator

        * Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test_process5(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = self.get_text_problematic_for_prettier1()
        expected = r"""
        * Python Formatting
        - Python has several built-in ways of formatting strings
          1. `%` format operator
          2. `format` and `str.format`

        * `%` Format Operator
        - Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        file_name = "test.txt"
        self.helper(txt, expected, file_name)

    def test_process6(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = r"""
        * `str.format`
        - Python 3 allows to format multiple values, e.g.,
           ```python
           key = 'my_var'
           value = 1.234
           ```
        """
        expected = r"""
        * `str.format`
        - Python 3 allows to format multiple values, e.g.,
          ```python
             key = 'my_var'
           value = 1.234
          ```
        """
        file_name = "test.txt"
        self.helper(txt, expected, file_name)

    def test7(self) -> None:
        """
        Test that YAML front matter is preserved in markdown files.
        """
        txt = r"""
        ---
        title: My Document
        date: 2024-01-01
        author: Test Author
        ---

        # Main Content

        - This is a list
          - With nested items
        """
        expected = r"""
        ---
        title: My Document
        date: 2024-01-01
        author: Test Author
        ---

        <!-- toc -->

        - [Main Content](#main-content)

        <!-- tocstop -->

        # Main Content
        - This is a list
          - With nested items
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)

    def test8(self) -> None:
        """
        Test that page separators are removed but YAML front matter is preserved.
        """
        txt = r"""
        ---
        title: Test
        ---

        # Section 1

        Content here.

        ---

        # Section 2

        More content.
        """
        expected = r"""
        ---
        title: Test
        ---

        <!-- toc -->

        - [Section 1](#section-1)
        - [Section 2](#section-2)

        <!-- tocstop -->

        # Section 1
        Content here.

        # Section 2
        More content.
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)


# #############################################################################
# Test_lint_txt_cmd_line1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_lint_txt_cmd_line1(hunitest.TestCase):
    """
    Test the lint_txt.py command-line script with different file types.
    """

    def run_lint_txt(
        self,
        in_file: str,
        type_: str,
        use_script: bool,
        cmd_opts: str,
    ) -> Optional[str]:
        """
        Run lint_txt processing directly by calling the code.

        :param in_file: Path to the input file containing the notes.
        :param type_: The output format, either 'md' or 'tex'.
        :param use_script
        :param cmd_opts: Additional command-line options to pass to the
            script.
        :return: The processed text content.
        """
        if use_script:
            # lint_txt.py \
            #  -i papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex \
            #  --use_dockerized_prettier \
            cmd = []
            exec_path = hgit.find_file_in_git_tree("lint_txt.py")
            hdbg.dassert_path_exists(exec_path)
            cmd.append(exec_path)
            cmd.append(f"--input {in_file}")
            cmd.append("--use_dockerized_prettier")
            # Save a script file to store the commands.
            hdbg.dassert_in(type_, ["md", "tex"])
            out_dir = self.get_scratch_space()
            out_file = os.path.join(out_dir, f"output.{type_}")
            cmd.append(f"--output {out_file}")
            cmd.append(cmd_opts)
            cmd = " ".join(cmd)
            hsystem.system(cmd)
            # Check the content of the file, if needed.
            output_txt: Optional[str] = None
            if os.path.exists(out_file):
                output_txt = hio.from_file(out_file)
        else:
            hdbg.dassert_in(type_, ["md", "tex"])
            # Read input file.
            txt = hio.from_file(in_file)
            lines = txt.split("\n")
            # Process the content directly.
            out_lines = dshdlitx._perform_actions(
                lines,
                in_file,
                actions=None,
                print_width=80,
                use_dockerized_prettier=True,
                use_dockerized_markdown_toc=True,
            )
            # Return the processed text.
            output_txt = "\n".join(out_lines)
        return output_txt

    # ///////////////////////////////////////////////////////////////////////////

    def test_md1(self) -> None:
        """
        Run lint_to_txt.py on a markdown file by calling the function directly.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "text.md")
        type_ = "md"
        use_script = False
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check.
        self.check_string(output_txt)

    def test_md2(self) -> None:
        """
        Run lint_to_txt.py on a markdown file using the command-line script.

        This test uses the same input file as test_md1 and should produce
        the same output. It uses test_method_name to reuse the golden
        outcome from test_md1.
        """
        # Prepare inputs.
        in_file = os.path.join(
            self.get_input_dir(test_method_name="test_md1"), "text.md"
        )
        type_ = "md"
        use_script = True
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check using the same golden outcome as test_md1.
        self.check_string(output_txt, test_method_name="test_md1")

    def test_tex1(self) -> None:
        """
        Run lint_to_txt.py on a latex file by calling the function directly.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "text.tex")
        type_ = "tex"
        use_script = False
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check.
        self.check_string(output_txt)

    def test_tex2(self) -> None:
        """
        Run lint_to_txt.py on a latex file using the command-line script.

        This test uses the same input file as test_tex1 and should produce
        the same output. It uses test_method_name to reuse the golden
        outcome from test_tex1.
        """
        # Prepare inputs.
        in_file = os.path.join(
            self.get_input_dir(test_method_name="test_tex1"), "text.tex"
        )
        type_ = "tex"
        use_script = True
        cmd_opts = "--print-width 80"
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check using the same golden outcome as test_tex1.
        self.check_string(output_txt, test_method_name="test_tex1")
