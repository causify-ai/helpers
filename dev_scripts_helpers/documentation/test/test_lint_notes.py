import logging
import os
from typing import Optional

import pytest

import dev_scripts_helpers.documentation.lint_notes as dshdlino
import helpers.hprint as hprint
import helpers.hserver as hserver
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
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
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
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
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
        act = dshdlino.prettier_on_str(txt)
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
