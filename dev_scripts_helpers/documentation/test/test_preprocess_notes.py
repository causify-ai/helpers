import logging
import os

import pytest

import dev_scripts_helpers.documentation.preprocess_notes as dshdprno
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
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
    act = hio.from_file(out_file)
    return act  # type: ignore


# #############################################################################
# Test_process_color_commands1
# #############################################################################


class Test_process_color_commands1(hunitest.TestCase):

    def test_text_content1(self) -> None:
        """
        Test with plain text content.
        """
        txt_in = r"\red{Hello world}"
        exp = r"\textcolor{red}{\text{Hello world}}"
        act = dshdprno._process_color_commands(txt_in)
        self.assert_equal(act, exp)

    def test_math_content1(self) -> None:
        """
        Test color command with mathematical content.
        """
        txt_in = r"\blue{x + y = z}"
        exp = r"\textcolor{blue}{x + y = z}"
        act = dshdprno._process_color_commands(txt_in)
        self.assert_equal(act, exp)

    def test_multiple_colors1(self) -> None:
        """
        Test multiple color commands in the same line.
        """
        txt_in = r"The \red{quick} \blue{fox} \green{jumps}"
        exp = r"The \textcolor{red}{\text{quick}} \textcolor{blue}{\text{fox}} \textcolor{darkgreen}{\text{jumps}}"
        act = dshdprno._process_color_commands(txt_in)
        self.assert_equal(act, exp)

    def test_mixed_content1(self) -> None:
        """
        Test color commands with both text and math content.
        """
        txt_in = r"\red{Result: x^2 + y^2}"
        exp = r"\textcolor{red}{Result: x^2 + y^2}"
        act = dshdprno._process_color_commands(txt_in)
        self.assert_equal(act, exp)

    def test_nested_braces1(self) -> None:
        """
        Test color command with nested braces.
        """
        txt_in = r"\blue{f(x) = {x + 1}}"
        exp = r"\textcolor{blue}{f(x) = {x + 1}}"
        act = dshdprno._process_color_commands(txt_in)
        self.assert_equal(act, exp)


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
        act = _run_preprocess_notes(in_file, out_file)
        # Check.
        self.check_string(act)


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
        exp = "- **Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, exp)

    def test_process_question2(self) -> None:
        txt_in = "** Hope is not a strategy"
        do_continue_exp = True
        exp = "- **Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, exp)

    def test_process_question3(self) -> None:
        txt_in = "*: Hope is not a strategy"
        do_continue_exp = True
        exp = "- **Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, exp)

    def test_process_question4(self) -> None:
        txt_in = "- Systems don't run themselves, they need to be run"
        do_continue_exp = False
        exp = txt_in
        self._helper_process_question(txt_in, do_continue_exp, exp)

    def test_process_question5(self) -> None:
        space = "   "
        txt_in = "*" + space + "Hope is not a strategy"
        do_continue_exp = True
        exp = "-" + space + "**Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, exp)

    def test_process_question6(self) -> None:
        space = "   "
        txt_in = "**" + space + "Hope is not a strategy"
        do_continue_exp = True
        exp = "-" + " " * len(space) + "**Hope is not a strategy**"
        self._helper_process_question(txt_in, do_continue_exp, exp)

    def _helper_process_question(
        self, txt_in: str, do_continue_exp: bool, exp: str
    ) -> None:
        do_continue, act = dshdprno._process_question_to_markdown(txt_in)
        self.assertEqual(do_continue, do_continue_exp)
        self.assert_equal(act, exp)


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
        act = dshdprno._transform_lines(txt_in, type_, is_qa=False)
        # Check.
        exp = r"""
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
        exp = hprint.dedent(exp, remove_lead_trail_empty_lines_=True)
        self.assert_equal(act, exp)
