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


# #############################################################################
# Test_process_question1
# #############################################################################


# @pytest.mark.skipif(
#     hserver.is_inside_ci() or hserver.is_dev_csfy(),
#     reason="Disabled because of CmampTask10710",
# )
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

    def helper(
        self, txt_in: str, do_continue_exp: bool, exp: str
    ) -> None:
        do_continue, act = dshdprno._process_question_to_markdown(txt_in)
        self.assertEqual(do_continue, do_continue_exp)
        self.assert_equal(act, exp)


# #############################################################################
# Test_preprocess_notes3
# #############################################################################


# @pytest.mark.skipif(
#     hserver.is_inside_ci() or hserver.is_dev_csfy(),
#     reason="Disabled because of CmampTask10710",
# )
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

    def test_run_all2(self) -> None:
        """
        Test type_="slides".
        """
        # Prepare inputs.
        txt_in = os.path.join(self.get_input_dir(), "input.txt")
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        # Run function.
        type_ = "slides"
        act = dshdprno._transform_lines(txt_in, type_, is_qa=False)
        # Check.
        self.check_string(act)


# #############################################################################
# Test_preprocess_notes1
# #############################################################################

@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_preprocess_notes_executable1(hunitest.TestCase):
    """
    Test `preprocess_notes.py` using the executable and checked in files.
    """

    @staticmethod
    def helper(in_file: str, out_file: str, type_: str) -> str:
        """
        Execute the end-to-end flow for `preprocess_notes.py` returning the output
        as string.
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