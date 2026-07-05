import os
from typing import List
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.documentation.replace_latex as dshdrela


# #############################################################################
# Test_standard_cleanup
# #############################################################################


class Test_standard_cleanup(hunitest.TestCase):
    """
    Test the `_standard_cleanup()` function.
    """

    def helper(self, content: str, aggressive: bool, expected: str) -> None:
        """
        Test helper for `_standard_cleanup()`.

        :param content: input file content
        :param aggressive: value of the `aggressive` flag
        :param expected: expected file content after cleanup
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "test.txt")
        hio.to_file(file_path, content)
        # Run test.
        dshdrela._standard_cleanup(file_path, aggressive)
        # Check outputs.
        actual = hio.from_file(file_path)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test word substitutions and terse rewording.
        """
        # Prepare inputs.
        content = "we know that gaussian iid variables doesn't change"
        # Prepare outputs.
        expected = (
            "you know that Gaussian IID variables does not change"
        )
        # Run test.
        self.helper(content, False, expected)

    def test2(self) -> None:
        """
        Test `iff` is converted to the math symbol.
        """
        # Prepare inputs.
        content = "this holds iff that holds"
        # Prepare outputs.
        expected = r"this holds $\iff$ that holds"
        # Run test.
        self.helper(content, False, expected)

    def test3(self) -> None:
        """
        Test `\\textit{}` is converted to markdown italics.
        """
        # Prepare inputs.
        content = r"\textit{Answer}: some \textit{term} here"
        # Prepare outputs.
        expected = "- ___Answer___: some _term_ here"
        # Run test.
        self.helper(content, False, expected)

    def test4(self) -> None:
        """
        Test aggressive mode capitalizes the first bullet letter.
        """
        # Prepare inputs.
        content = "- hello world"
        # Prepare outputs.
        expected = "- Hello world"
        # Run test.
        self.helper(content, True, expected)

    def test5(self) -> None:
        """
        Test trailing whitespace is stripped.
        """
        # Prepare inputs.
        content = "some line with trailing spaces   "
        # Prepare outputs.
        expected = "some line with trailing spaces"
        # Run test.
        self.helper(content, False, expected)


# #############################################################################
# Test_replace_latex_py
# #############################################################################


class Test_replace_latex_py(hunitest.TestCase):
    """
    End-to-end tests for the `replace_latex.py` executable.
    """

    def _run_main(self, argv: List[str]) -> List:
        """
        Run `dshdrela._main()` with a mocked `sys.argv` and capture system
        calls.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :return: list of captured system call invocations
        """
        parser = dshdrela._parse()
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch("sys.argv", argv):
                dshdrela._main(parser)
        return invocations

    def test1(self) -> None:
        """
        Test `checkout` action runs `git checkout`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "test.txt")
        hio.to_file(file_path, "content")
        argv = [
            "replace_latex.py",
            "-a",
            "checkout",
            "--file",
            file_path,
        ]
        # Prepare outputs.
        expected_invocations = [
            {
                "function": "hsystem.system",
                "args": (f"git checkout -- {file_path}",),
                "kwargs": {},
            }
        ]
        expected = hunteuti.invocations_to_str(expected_invocations)
        # Run test.
        actual = self._run_main(argv)
        actual = hunteuti.invocations_to_str(actual)
        # Check outputs.
        self.assert_equal(
            actual, expected, purify_text=True, purify_expected_text=True
        )

    def test2(self) -> None:
        """
        Test `pandoc_before` and `pandoc_after` actions invoke
        `notes_to_pdf.py`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "test.txt")
        hio.to_file(file_path, "content")
        argv = [
            "replace_latex.py",
            "-a",
            "pandoc_before",
            "-a",
            "pandoc_after",
            "--file",
            file_path,
        ]
        # Prepare outputs.
        cmd = (
            f"notes_to_pdf.py -a pdf --no_toc --no_open_pdf --input {file_path}"
        )
        expected_invocations = [
            {"function": "hsystem.system", "args": (cmd,), "kwargs": {}},
            {"function": "hsystem.system", "args": (cmd,), "kwargs": {}},
        ]
        expected = hunteuti.invocations_to_str(expected_invocations)
        # Run test.
        actual = self._run_main(argv)
        actual = hunteuti.invocations_to_str(actual)
        # Check outputs.
        self.assert_equal(
            actual, expected, purify_text=True, purify_expected_text=True
        )

    def test3(self) -> None:
        """
        Test `replace` action cleans up the file in place.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "test.txt")
        hio.to_file(file_path, "we know that gaussian variables")
        argv = [
            "replace_latex.py",
            "-a",
            "replace",
            "--file",
            file_path,
        ]
        # Prepare outputs.
        expected = "you know that Gaussian variables"
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = hio.from_file(file_path)
        self.assert_equal(actual, expected)
