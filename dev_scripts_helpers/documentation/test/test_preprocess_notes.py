import logging
import os

import pytest

import dev_scripts_helpers.documentation.preprocess_notes as dshdprno
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# TODO(gp): Pass through the function and not only executable.
def _run_preprocess_notes(in_file: str, out_file: str) -> str:
    """
    Execute the end-to-end flow for `preprocess_notes.py` returning the output
    as string.
    """
    exec_path = hgit.find_file_in_git_tree("preprocess_notes.py")
    hdbg.dassert_path_exists(exec_path)
    #
    hdbg.dassert_path_exists(in_file)
    #
    cmd = []
    cmd.append(exec_path)
    cmd.append(f"--input {in_file}")
    cmd.append(f"--output {out_file}")
    cmd.append("--type pdf")
    cmd_as_str = " ".join(cmd)
    hsystem.system(cmd_as_str)
    # Check.
    actual = hio.from_file(out_file)
    return actual  # type: ignore


# #############################################################################
# Test_process_color_commands1
# #############################################################################


class Test_process_color_commands1(hunitest.TestCase):
    def test_text_content1(self) -> None:
        """
        Test with plain text content.
        """
        txt_in = r"\red{Hello world}"
        expected = r"\textcolor{red}{\text{Hello world}}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_math_content1(self) -> None:
        """
        Test color command with mathematical content.
        """
        txt_in = r"\blue{x + y = z}"
        expected = r"\textcolor{blue}{x + y = z}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_multiple_colors1(self) -> None:
        """
        Test multiple color commands in the same line.
        """
        txt_in = r"The \red{quick} \blue{fox} \green{jumps}"
        expected = r"The \textcolor{red}{\text{quick}} \textcolor{blue}{\text{fox}} \textcolor{darkgreen}{\text{jumps}}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_mixed_content1(self) -> None:
        """
        Test color commands with both text and math content.
        """
        txt_in = r"\red{Result: x^2 + y^2}"
        expected = r"\textcolor{red}{Result: x^2 + y^2}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_nested_braces1(self) -> None:
        """
        Test color command with nested braces.
        """
        txt_in = r"\blue{f(x) = {x + 1}}"
        expected = r"\textcolor{blue}{f(x) = {x + 1}}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_colorize_bullet_points1
# #############################################################################


@pytest.mark.skip(reason="Broken for now")
class Test_colorize_bullet_points1(hunitest.TestCase):
    def helper(self, txt_in: str, expected: str) -> None:
        """
        Test colorize bullet points.
        """
        txt_in = hprint.dedent(txt_in)
        actual = hmarkdo.colorize_bullet_points(txt_in)
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test colorize bullet points.
        """
        txt_in = r"""
        - **VC Theory**
            - Measures model

        - **Bias-Variance Decomposition**
            - Prediction error
                - **Bias**
                - **Variance**

        - **Computation Complexity**
            - Balances model
            - Related to
            - E.g., Minimum

        - **Bayesian Approach**
            - Treats ML as probability
            - Combines prior knowledge with observed data to update belief about a model

        - **Problem in ML Theory:**
            - Assumptions may not align with practical problems
        """
        expected = r"""
        - **\red{VC Theory}**
            - Measures model

        - **\orange{Bias-Variance Decomposition}**
            - Prediction error
                - **\yellow{Bias}**
                - **\lime{Variance}**

        - **\green{Computation Complexity}**
            - Balances model
            - Related to
            - E.g., Minimum

        - **\teal{Bayesian Approach}**
            - Treats ML as probability
            - Combines prior knowledge with observed data to update belief about a model

        - **\cyan{Problem in ML Theory:}**
            - Assumptions may not align with practical problems
        """
        self.helper(txt_in, expected)


# #############################################################################
# Test_preprocess_notes1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_preprocess_notes1(hunitest.TestCase):
    """
    Test `preprocess_notes.py` using the executable and checked in files.
    """

    def test1(self) -> None:
        self._helper()

    def _helper(self) -> None:
        # Set up.
        in_file = os.path.join(self.get_input_dir(), "input1.txt")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        # Run.
        actual = _run_preprocess_notes(in_file, out_file)
        # Check.
        self.check_string(actual)


# #############################################################################
# Test_process_question1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_process_question1(hunitest.TestCase):
    """
    Check that the output of `preprocess_notes.py` is the expected one calling
    the library function directly.
    """

    def test_process_question1(self) -> None:
        txt_in = "* Hope is not a strategy"
        do_continue_exp = True
        expected = "- **Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, expected)

    def test_process_question2(self) -> None:
        txt_in = "** Hope is not a strategy"
        do_continue_exp = True
        expected = "- **Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, expected)

    def test_process_question3(self) -> None:
        txt_in = "*: Hope is not a strategy"
        do_continue_exp = True
        expected = "- **Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, expected)

    def test_process_question4(self) -> None:
        txt_in = "- Systems don't run themselves, they need to be run"
        do_continue_exp = False
        expected = txt_in
        self._helper_process_question(txt_in, do_continue_exp, expected)

    def test_process_question5(self) -> None:
        space = "   "
        txt_in = "*" + space + "Hope is not a strategy"
        do_continue_exp = True
        expected = "-" + space + "**Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, expected)

    def test_process_question6(self) -> None:
        space = "   "
        txt_in = "**" + space + "Hope is not a strategy"
        do_continue_exp = True
        expected = "-" + " " * len(space) + "**Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, expected)

    def _helper_process_question(
        self, txt_in: str, do_continue_exp: bool, expected: str
    ) -> None:
        do_continue, actual = dshdprno._process_question_to_markdown(txt_in)
        self.assertEqual(do_continue, do_continue_exp)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_preprocess_notes3
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_preprocess_notes3(hunitest.TestCase):
    """
    Check that the output of `preprocess_notes.py` is the expected one calling
    the library function directly.
    """

    def test_run_all1(self) -> None:
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
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        # Execute function.
        type_ = "pdf"
        actual = dshdprno._transform_lines(txt_in, type_, is_qa=False)
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
