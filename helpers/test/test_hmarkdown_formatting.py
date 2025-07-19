import logging
import os

import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_remove_end_of_line_periods1
# #############################################################################


class Test_remove_end_of_line_periods1(hunitest.TestCase):
    def test_standard_case(self) -> None:
        txt = "Hello.\nWorld.\nThis is a test."
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = "Hello\nWorld\nThis is a test"
        self.assertEqual(act, exp)

    def test_no_periods(self) -> None:
        txt = "Hello\nWorld\nThis is a test"
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = "Hello\nWorld\nThis is a test"
        self.assertEqual(act, exp)

    def test_multiple_periods(self) -> None:
        txt = "Line 1.....\nLine 2.....\nEnd."
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = "Line 1\nLine 2\nEnd"
        self.assertEqual(act, exp)

    def test_empty_string(self) -> None:
        txt = ""
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = ""
        self.assertEqual(act, exp)

    def test_leading_and_trailing_periods(self) -> None:
        txt = ".Line 1.\n.Line 2.\n..End.."
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = ".Line 1\n.Line 2\n..End"
        self.assertEqual(act, exp)


# #############################################################################
# Test_md_clean_up1
# #############################################################################


class Test_md_clean_up1(hunitest.TestCase):
    def test1(self) -> None:
        # Prepare inputs.
        txt = r"""
        **States**:
        - \( S = \{\text{Sunny}, \text{Rainy}\} \)
        **Observations**:
        - \( O = \{\text{Yes}, \text{No}\} \) (umbrella)

        ### Initial Probabilities:
        \[
        P(\text{Sunny}) = 0.6, \quad P(\text{Rainy}) = 0.4
        \]

        ### Transition Probabilities:
        \[
        \begin{aligned}
        P(\text{Sunny} \to \text{Sunny}) &= 0.7, \quad P(\text{Sunny} \to \text{Rainy}) = 0.3 \\
        P(\text{Rainy} \to \text{Sunny}) &= 0.4, \quad P(\text{Rainy} \to \text{Rainy}) = 0.6
        \end{aligned}
        \]

        ### Observation (Emission) Probabilities:
        \[
        \begin{aligned}
        P(\text{Yes} \mid \text{Sunny}) &= 0.1, \quad P(\text{No} \mid \text{Sunny}) = 0.9 \\
        P(\text{Yes} \mid \text{Rainy}) &= 0.8, \quad P(\text{No} \mid \text{Rainy}) = 0.2
        \end{aligned}
        \]
        """
        txt = hprint.dedent(txt)
        act = hmarkdo.md_clean_up(txt)
        act = hprint.dedent(act)
        exp = r"""
        **States**:
        - $S = \{\text{Sunny}, \text{Rainy}\}$
        **Observations**:
        - $O = \{\text{Yes}, \text{No}\}$ (umbrella)

        ### Initial Probabilities:
        $$
        \Pr(\text{Sunny}) = 0.6, \quad \Pr(\text{Rainy}) = 0.4
        $$

        ### Transition Probabilities:
        $$
        \begin{aligned}
        \Pr(\text{Sunny} \to \text{Sunny}) &= 0.7, \quad \Pr(\text{Sunny} \to \text{Rainy}) = 0.3 \\
        \Pr(\text{Rainy} \to \text{Sunny}) &= 0.4, \quad \Pr(\text{Rainy} \to \text{Rainy}) = 0.6
        \end{aligned}
        $$

        ### Observation (Emission) Probabilities:
        $$
        \begin{aligned}
        \Pr(\text{Yes} | \text{Sunny}) &= 0.1, \quad \Pr(\text{No} | \text{Sunny}) = 0.9 \\
        \Pr(\text{Yes} | \text{Rainy}) &= 0.8, \quad \Pr(\text{No} | \text{Rainy}) = 0.2
        \end{aligned}
        $$"""
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_remove_code_delimiters1
# #############################################################################


class Test_remove_code_delimiters1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test a basic example.
        """
        # Prepare inputs.
        content = r"""
        ```python
        def hello_world():
            print("Hello, World!")
        ```
        """
        content = hprint.dedent(content)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        def hello_world():
            print("Hello, World!")
        """
        self.assert_equal(str(act), exp, dedent=True)

    def test2(self) -> None:
        """
        Test an example with empty lines at the start and end.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        def check_empty_lines():
            print("Check empty lines are present!")
        """
        self.assert_equal(str(act), exp, dedent=True)

    def test3(self) -> None:
        """
        Test a markdown with headings, Python and yaml blocks.
        """
        # Prepare inputs.
        content = r"""
        # Section 1

        This section contains comment and python code.

        > "Knowledge is like a tree, growing stronger with each branch of understanding."

        ```python
        def greet(name):
            return f"Hello, {name}!"
        print(greet("World"))
        ```

        # Section 2

        Key points below.

        - Case Study 1: Implementation in modern industry
        - Case Study 2: Comparative analysis of traditional vs. modern methods

        ```yaml
        future:
        - AI integration
        - Process optimization
        - Sustainable solutions
        ```
        """
        content = hprint.dedent(content)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        # Section 1

        This section contains comment and python code.

        > "Knowledge is like a tree, growing stronger with each branch of understanding."


        def greet(name):
            return f"Hello, {name}!"
        print(greet("World"))


        # Section 2

        Key points below.

        - Case Study 1: Implementation in modern industry
        - Case Study 2: Comparative analysis of traditional vs. modern methods

        yaml
        future:
        - AI integration
        - Process optimization
        - Sustainable solutions

        """
        self.assert_equal(str(act), exp, dedent=True)

    def test4(self) -> None:
        """
        Test another markdown with headings and multiple indent Python blocks.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        content = hprint.dedent(content)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        self.check_string(act, dedent=True)

    def test5(self) -> None:
        """
        Test an empty string.
        """
        # Prepare inputs.
        content = ""
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = ""
        self.assert_equal(str(act), exp, dedent=True)

    def test6(self) -> None:
        """
        Test a Python and immediate markdown code block.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        def no_start_python():
            print("No mention of python at the start")



            A markdown paragraph contains
            delimiters that needs to be removed.
        """
        self.assert_equal(str(act), exp, dedent=True)
