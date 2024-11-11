import logging
import os

import pytest

import dev_scripts_helpers.documentation.convert_txt_to_pandoc as dshdcttpa
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _run_preprocess(in_file: str, out_file: str) -> str:
    """
    Execute the end-to-end flow for convert_txt_to_pandoc.py returning the
    output as string.
    """
    exec_path = hgit.find_file_in_git_tree("convert_txt_to_pandoc.py")
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


# TODO(gp): -> Test_convert_txt_to_pandoc*
class Test_preprocess1(hunitest.TestCase):
    """
    Check that the output of convert_txt_to_pandoc.py is the expected one.

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


class Test_preprocess2(hunitest.TestCase):
    """
    Check that the output of convert_txt_to_pandoc.py is the expected one
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
        txt_in = """
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
        exp = """
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
