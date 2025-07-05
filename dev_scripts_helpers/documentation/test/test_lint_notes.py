import logging
import os
from typing import Optional

import pytest

import dev_scripts_helpers.documentation.lint_notes as dshdlino
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _get_text1() -> str:
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
# Test_lint_notes1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_lint_notes1(hunitest.TestCase):
    def test_preprocess1(self) -> None:
        txt = r"""$$E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)$$"""
        exp = r"""
        $$
        E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)
        $$"""
        self._helper_preprocess(txt, exp)

    def test_preprocess2(self) -> None:
        txt = r"""
        $$E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)$$"""
        exp = r"""
        $$
        E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)
        $$"""
        self._helper_preprocess(txt, exp)

    def test_preprocess3(self) -> None:
        txt = _get_text1()
        exp = r"""
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
        self._helper_preprocess(txt, exp)

    def test_preprocess4(self) -> None:
        txt = r"""
        # #########################
        # test
        # #############################################################################"""
        exp = r"""# test"""
        self._helper_preprocess(txt, exp)

    def test_preprocess5(self) -> None:
        txt = r"""
        ## ////////////////
        # test
        # ////////////////"""
        exp = r"""# test"""
        self._helper_preprocess(txt, exp)

    def _helper_preprocess(self, txt: str, exp: str) -> None:
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        act = dshdlino._preprocess(txt)
        exp = hprint.dedent(exp, remove_lead_trail_empty_lines_=True)
        self.assert_equal(act, exp)


# #############################################################################
# Test_lint_notes2
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_lint_notes2(hunitest.TestCase):
    def test_process1(self) -> None:
        txt = _get_text1()
        exp = None
        file_name = "test.txt"
        act = self._helper_process(txt, exp, file_name)
        self.check_string(act)

    def test_process2(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        exp = r"""
        * Good time management

        1. Choose the right tasks
           - Avoid non-essential tasks
        """
        file_name = "test.txt"
        self._helper_process(txt, exp, file_name)

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
        exp = r"""
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
        self._helper_process(txt, exp, file_name)

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
        exp = r"""
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
        self._helper_process(txt, exp, file_name)

    def test_process_prettier_bug1(self) -> None:
        """
        For some reason prettier replaces - with * when there are 2 empty lines.
        """
        txt = self._get_text_problematic_for_prettier1()
        act = dshdlino.prettier_on_str(txt, file_type="txt")
        exp = r"""
        - Python formatting

        * Python has several built-in ways of formatting strings
          1. `%` format operator
          2. `format` and `str.format`

        - `%` format operator

        * Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        exp = hprint.dedent(exp, remove_lead_trail_empty_lines_=True)
        self.assert_equal(act, exp)

    def test_process5(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = self._get_text_problematic_for_prettier1()
        exp = r"""
        * Python formatting
        - Python has several built-in ways of formatting strings

          1. `%` format operator
          2. `format` and `str.format`

        * `%` format operator
        - Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        file_name = "test.txt"
        self._helper_process(txt, exp, file_name)

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
        exp = r"""
        * `str.format`
        - Python 3 allows to format multiple values, e.g.,
          ```python
          key = 'my_var'
          value = 1.234
          ```
        """
        file_name = "test.txt"
        self._helper_process(txt, exp, file_name)

    # //////////////////////////////////////////////////////////////////////////

    @staticmethod
    def _get_text_problematic_for_prettier1() -> str:
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

    def _helper_process(
        self, txt: str, exp: Optional[str], file_name: str
    ) -> str:
        """
        Helper function to process the given text and compare the result with
        the expected output.

        :param txt: The text to be processed.
        :param exp: The expected output after processing the text. If
            None, no comparison is made.
        :param file_name: The name of the file to be used for
            processing.
        :return: The processed text.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        file_name = os.path.join(self.get_scratch_space(), file_name)
        act = dshdlino._process(txt, file_name)
        if exp:
            exp = hprint.dedent(exp, remove_lead_trail_empty_lines_=True)
            self.assert_equal(act, exp)
        return act


# #############################################################################
# Test_lint_notes_cmd_line1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_lint_notes_cmd_line1(hunitest.TestCase):
    def create_md_input_file(self) -> str:
        txt = """
        # Header1
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        return in_file

    def create_tex_input_file(self) -> str:
        txt = r"""
            \documentclass{article}

        \title{Simple \LaTeX{} Example}
        \author{Your Name}
                \date{\today}

        \begin{document}

        \maketitle

        \section{Introduction}
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

        \section{Math Example}
        Here is an inline equation: \( E = mc^2 \).\\
        And a displayed equation:
                \[
        \int_{0}^{\infty} e^{-x^2} \, dx = \frac{\sqrt{\pi}}{2}
        \]

            \section{Lists}
        \begin{itemize}
        \item Item 1
                \item Item 2
            \item Item 3
        \end{itemize}

        \end{document}
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "input.tex")
        hio.to_file(in_file, txt)
        return in_file

    # TODO(gp): Run this calling directly the code and not executing the script.
    def run_lint_notes(
        self, in_file: str, type_: str, cmd_opts: str
    ) -> Optional[str]:
        """
        Run the `lint_notes.py` script with the specified options.

        :param in_file: Path to the input file containing the notes.
        :param type_: The output format, either 'md' or 'tex'.
        :param cmd_opts: Additional command-line options to pass to the
            script.
        :return: A tuple containing the script content and the output
            content.
        """
        # lint_notes.py \
        #  -i papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex \
        #  --use_dockerized_prettier \
        cmd = []
        exec_path = hgit.find_file_in_git_tree("lint_notes.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--in_file_name {in_file}")
        cmd.append("--use_dockerized_prettier")
        # Save a script file to store the commands.
        hdbg.dassert_in(type_, ["md", "tex"])
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, f"output.{type_}")
        cmd.append(f"--out_file_name {out_file}")
        cmd.append(cmd_opts)
        cmd = " ".join(cmd)
        hsystem.system(cmd)
        # Check the content of the file, if needed.
        output_txt: Optional[str] = None
        if os.path.exists(out_file):
            output_txt = hio.from_file(out_file)
        return output_txt

    # ///////////////////////////////////////////////////////////////////////////

    def test1(self) -> None:
        """
        Run lint_to_notes.py on a markdown file.
        """
        # Prepare inputs.
        in_file = self.create_md_input_file()
        type_ = "md"
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_notes(in_file, type_, cmd_opts)
        # Check.
        self.check_string(output_txt)

    def test2(self) -> None:
        """
        Run lint_to_notes.py on a latex file.
        """
        # Prepare inputs.
        in_file = self.create_tex_input_file()
        type_ = "tex"
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_notes(in_file, type_, cmd_opts)
        # Check.
        self.check_string(output_txt)


class Test_improve_header_and_slide_titles1(hunitest.TestCase):
    """
    Test the function `_improve_header_and_slide_titles`.
    """

    def helper(self, txt: str, exp: str) -> None:
        txt = hprint.dedent(txt)
        exp = hprint.dedent(exp)
        act = dshdlino._improve_header_and_slide_titles(txt)
        self.assert_equal(act, exp)

    def test1(self) -> None:
        txt = r"""
        * ML theory
        """
        exp = r"""
        * ML Theory
        """
        self.helper(txt, exp)

    def test2(self) -> None:
        """
        Test the function `_improve_header_and_slide_titles`.
        """
        txt = r"""
        * A map of machine learning
        """
        exp = r"""
        * A Map of Machine Learning
        """
        self.helper(txt, exp)