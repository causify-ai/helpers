import glob
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



# #############################################################################
# Test_process_question1
# #############################################################################

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

    def helper(self, txt_in: str, do_continue_exp: bool, expected: str) -> None:
        do_continue, actual = dshdprno._process_question_to_markdown(txt_in)
        self.assertEqual(do_continue, do_continue_exp)
        self.assert_equal(actual, expected)



# #############################################################################
# Test_remove_headers1
# #############################################################################

class Test_remove_headers1(hunitest.TestCase):
    """
    Test the `_remove_headers()` function.
    """

    def helper(self, lines_in: list, expected: list, max_level: int = 999) -> None:
        """
        Helper method to test the _remove_headers function.

        :param lines_in: input lines
        :param expected: expected output lines
        :param max_level: maximum level of headers to consider (default: 999 to remove all headers)
        """
        actual = dshdprno._remove_headers(lines_in, max_level)
        # Convert lists to strings for comparison.
        actual_str = "\n".join(actual)
        expected_str = "\n".join(expected)
        self.assert_equal(actual_str, expected_str)

    def test1(self) -> None:
        """
        Test removing a single level 1 header.
        """
        lines_in = ["# Chapter 1", "Some content here"]
        expected = ["Some content here"]
        self.helper(lines_in, expected)

    def test2(self) -> None:
        """
        Test removing headers of various levels.
        """
        lines_in = [
            "# Chapter 1",
            "Content line 1",
            "## Section 1.1",
            "Content line 2",
            "### Subsection",
            "Content line 3",
            "#### Sub-subsection",
            "Content line 4",
        ]
        expected = [
            "Content line 1",
            "Content line 2",
            "Content line 3",
            "Content line 4",
        ]
        self.helper(lines_in, expected)

    def test3(self) -> None:
        """
        Test headers mixed with regular text and bullet points.
        """
        lines_in = [
            "# Header",
            "- Bullet point 1",
            "- Bullet point 2",
            "## Subheader",
            "Regular text",
        ]
        expected = [
            "- Bullet point 1",
            "- Bullet point 2",
            "Regular text",
        ]
        self.helper(lines_in, expected)

    def test4(self) -> None:
        """
        Test input with no headers (should return unchanged).
        """
        lines_in = [
            "This is some text",
            "- Bullet point",
            "More text",
        ]
        expected = lines_in
        self.helper(lines_in, expected)

    def test5(self) -> None:
        """
        Test input with only headers (should return empty list).
        """
        lines_in = [
            "# Header 1",
            "## Header 2",
            "### Header 3",
        ]
        expected = []
        self.helper(lines_in, expected)

    def test6(self) -> None:
        """
        Test that empty lines around headers are preserved.
        """
        lines_in = [
            "",
            "# Header",
            "",
            "Content",
            "",
        ]
        expected = [
            "",
            "",
            "Content",
            "",
        ]
        self.helper(lines_in, expected)


# #############################################################################
# Test_preprocess_notes_end_to_end1
# #############################################################################

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
        txt_in = txt_in.split("\n")
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        # Execute function.
        type_ = "pdf"
        actual = dshdprno._transform_lines(txt_in, type_, is_qa=False)
        actual = "\n".join(actual)
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



# #############################################################################
# Test_preprocess_notes_end_to_end2
# #############################################################################

class Test_preprocess_notes_end_to_end2(hunitest.TestCase):
    """
    Test `preprocess_notes.py` by calling the library function directly.

    # To update the outcomes:
    > cd /Users/saggese/src/umd_msml6101
    > cp -r lectures_source/Lesson*.txt ./helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2/input/

    # To compare inputs and outputs:
    > vimdiff dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2.test_run_all1/{input,output}/Lesson01-Intro.txt
    """

    @pytest.mark.skip(
        reason="Requires external input files to be manually copied"
    )
    def test_run_all1(self) -> None:
        input_dir = self.get_input_dir()
        _LOG.debug("input_dir=%s", input_dir)
        # Find all the files in the `test/input` directory.
        files = glob.glob(os.path.join(input_dir, "*.txt"))
        _LOG.debug("Found %s files", len(files))
        hdbg.dassert_lt(0, len(files))
        for file in files:
            # Read the file.
            text = hio.from_file(file)
            # Run the function.
            # > preprocess_notes.py \
            #     --input lectures_source/Lesson02-Techniques.txt \
            #     --output tmp.notes_to_pdf.preprocess_notes.txt \
            #     --type slides \
            #     --toc_type navigation
            lines = text.split("\n")
            type_ = "slides"
            toc_type = "navigation"
            is_qa = False
            actual = dshdprno._preprocess_lines(lines, type_, toc_type, is_qa)
            # Check.
            actual = "\n".join(actual)
            tag = os.path.basename(file)
            tag = hio.remove_extension(tag, ".txt", check_file_exists=False)
            self.check_string(actual, tag=tag)



# #############################################################################
# Test_preprocess_notes_end_to_end3
# #############################################################################

class Test_preprocess_notes_end_to_end3(hunitest.TestCase):
    """
    Test `preprocess_notes.py` by calling the library function directly.

    # To update the outcomes:
    > cd /Users/saggese/src/umd_msml6101
    > cp -r lectures_source/Lesson*.txt ./helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2/input/

    # To compare inputs and outputs:
    > vimdiff dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end2.test_run_all1/{input,output}/Lesson01-Intro.txt
    """

    @pytest.mark.skip(
        reason="Requires external input files to be manually copied"
    )
    def test_run_all1(self) -> None:
        input_dir = self.get_input_dir()
        _LOG.debug("input_dir=%s", input_dir)
        # Find all the files in the `test/input` directory.
        files = glob.glob(os.path.join(input_dir, "*.txt"))
        _LOG.debug("Found %s files", len(files))
        hdbg.dassert_lt(0, len(files))
        for file in files:
            # Read the file.
            text = hio.from_file(file)
            # Run the function.
            # > preprocess_notes.py \
            #     --input lectures_source/Lesson02-Techniques.txt \
            #     --output tmp.notes_to_pdf.preprocess_notes.txt \
            #     --type slides \
            #     --toc_type navigation
            lines = text.split("\n")
            type_ = "slides"
            toc_type = "navigation"
            is_qa = False
            actual = dshdprno._preprocess_lines(lines, type_, toc_type, is_qa)
            # Check.
            actual = "\n".join(actual)
            tag = os.path.basename(file)
            tag = hio.remove_extension(tag, ".txt", check_file_exists=False)
            self.check_string(actual, tag=tag)



# #############################################################################
# Test_preprocess_notes_executable1
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
        Execute the end-to-end flow for `preprocess_notes.py` returning the
        output as string.
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



# #############################################################################
# Test_preprocess_notes_remove_headers1
# #############################################################################

class Test_preprocess_notes_remove_headers1(hunitest.TestCase):
    """
    Test `preprocess_notes.py` with `--toc_type remove_headers`.
    """

    def test1(self) -> None:
        """
        Test the full preprocessing flow with header removal.
        """
        # Prepare inputs.
        txt_in = r"""
        # Chapter 1: Introduction
        This is some introductory content.

        ## Section 1.1: Background
        More content here with some details.

        * What is the main concept?
        The main concept is to understand how preprocessing works.

        ### Subsection 1.1.1
        - Bullet point 1
        - Bullet point 2
        - Bullet point 3

        Some regular text after bullets.

        ## Section 1.2: Examples

        Here is a code block:
        ```python
        def foo():
            # This is a comment with # symbol
            pass
        ```

        # Chapter 2: Advanced Topics

        More advanced content goes here.

        * Another question?
        Answer to the question.
        """
        txt_in = txt_in.split("\n")
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        # Execute function.
        type_ = "pdf"
        toc_type = "remove_headers"
        actual = dshdprno._preprocess_lines(
            txt_in, type_, toc_type, is_qa=False
        )
        actual = "\n".join(actual)
        # Check.
        self.check_string(actual)
