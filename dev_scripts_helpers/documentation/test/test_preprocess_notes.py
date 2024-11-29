import logging
import os

import pytest

import dev_scripts_helpers.documentation.preprocess_notes as dshdcttpa
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _run_preprocess(in_file: str, out_file: str) -> str:
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
    cmd_as_str = " ".join(cmd)
    hsystem.system(cmd_as_str)
    # Check.
    act = hio.from_file(out_file)
    return act  # type: ignore


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_preprocess_notes1(hunitest.TestCase):
    """
    Check that the output of `preprocess_notes.py` is the expected one.

    using:
    - an end-to-end flow;
    - checked in files.
    """

    @pytest.mark.skip
    def test1(self) -> None:
        self._helper()

    @pytest.mark.skip
    def test2(self) -> None:
        self._helper()

    def _helper(self) -> None:
        # Set up.
        in_file = os.path.join(self.get_input_dir(), "input1.txt")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        # Run.
        act = _run_preprocess(in_file, out_file)
        # Check.
        self.check_string(act)


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_preprocess_notes2(hunitest.TestCase):
    """
    Check that the output of `preprocess_notes.py` is the expected one
    calling the library function directly.
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

    def test_transform1(self) -> None:
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
        txt_in = hprint.dedent(txt_in, remove_empty_leading_trailing_lines=True)
        exp = r"""
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
        exp = hprint.dedent(exp, remove_empty_leading_trailing_lines=True)
        self._helper_transform(txt_in, exp)

    def _helper_process_question(
        self, txt_in: str, do_continue_exp: bool, exp: str
    ) -> None:
        do_continue, act = dshdcttpa._process_question(txt_in)
        self.assertEqual(do_continue, do_continue_exp)
        self.assert_equal(act, exp)

    # #########################################################################

    def _helper_transform(self, txt_in: str, exp: str) -> None:
        act_as_arr = dshdcttpa._transform(txt_in.split("\n"))
        act = "\n".join(act_as_arr)
        self.assert_equal(act, exp)
