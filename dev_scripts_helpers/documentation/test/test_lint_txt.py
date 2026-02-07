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
# Test_extract_yaml_frontmatter
# #############################################################################


class Test_extract_yaml_frontmatter(hunitest.TestCase):
    """
    Test the _extract_yaml_frontmatter function.
    """

    def helper(
        self,
        txt: str,
        expected_frontmatter: list,
        expected_remaining: list,
    ) -> None:
        """
        Test helper for _extract_yaml_frontmatter.

        :param txt: Input text to process
        :param expected_frontmatter: Expected front matter lines
        :param expected_remaining: Expected remaining lines
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        frontmatter, remaining = dshdlitx._extract_yaml_frontmatter(lines)
        # Check outputs.
        self.assertEqual(frontmatter, expected_frontmatter)
        self.assertEqual(remaining, expected_remaining)

    def test1(self) -> None:
        """
        Test extracting YAML front matter from a file.
        """
        # Prepare inputs.
        txt = """
        ---
        title: My Document
        date: 2024-01-01
        ---
        # Content
        This is the main content.
        """
        # Prepare outputs.
        expected_frontmatter = ["---", "title: My Document", "date: 2024-01-01", "---"]
        expected_remaining = ["# Content", "This is the main content."]
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test2(self) -> None:
        """
        Test processing a file without YAML front matter.
        """
        # Prepare inputs.
        txt = """
        # Content
        This is the main content.
        """
        # Prepare outputs.
        expected_frontmatter = []
        expected_remaining = ["# Content", "This is the main content."]
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test3(self) -> None:
        """
        Test handling incomplete YAML front matter (missing closing delimiter).
        """
        # Prepare inputs.
        txt = """
        ---
        title: My Document
        # Content without closing delimiter
        """
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Prepare outputs.
        expected_frontmatter = []
        expected_remaining = lines
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test4(self) -> None:
        """
        Test extracting empty YAML front matter.
        """
        # Prepare inputs.
        txt = """
        ---
        ---
        # Content
        """
        # Prepare outputs.
        expected_frontmatter = ["---", "---"]
        expected_remaining = ["# Content"]
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test5(self) -> None:
        """
        Test that separators not at the beginning are not treated as front matter.
        """
        # Prepare inputs.
        txt = """
        # Content
        ---
        More content
        """
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Prepare outputs.
        expected_frontmatter = []
        expected_remaining = lines
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)


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

    def test_remove_single_separator(self) -> None:
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

    def test_remove_multiple_separators(self) -> None:
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

    def test_remove_separator_with_spaces(self) -> None:
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

    def test_no_separator(self) -> None:
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

    def test_separator_in_code_block_preserved(self) -> None:
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

    def test_empty_input(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
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
