import contextlib
import io
import os
from typing import List
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.standardize_book_filename as dshdsbofi


# #############################################################################
# Test_standardize_book_filename_py
# #############################################################################


class Test_standardize_book_filename_py(hunitest.TestCase):
    """
    End-to-end tests for the `standardize_book_filename.py` executable.
    """

    def _run_main(self, argv: List[str]) -> str:
        """
        Run `dshdstbf._main()` with a mocked `sys.argv` and capture stdout.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :return: captured stdout
        """
        parser = dshdsbofi._parse()
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            with mock.patch("sys.argv", argv):
                dshdsbofi._main(parser)
        return buf.getvalue()

    def _helper_dry_run(
        self,
        input_filename: str,
    ) -> str:
        """
        Helper for dry run test.

        :param input_filename: filename to create in scratch space
        :return: captured stdout
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, input_filename)
        hio.to_file(input_file, "content")
        argv = ["standardize_book_filename.py", "--input", input_file]
        # Run test.
        actual = self._run_main(argv)
        # Check outputs: file should still exist.
        self.assertTrue(os.path.exists(input_file))
        return actual

    def test1(self) -> None:
        """
        Test dry run does not rename file on disk.
        """
        # Run test.
        actual = self._helper_dry_run("Some Book Title.pdf")
        # Check outputs: output contains expected text.
        self.assertIn("Rename", actual)
        self.assertIn("Some Book Title.pdf", actual)

    def test2(self) -> None:
        """
        Test `--mv` actually renames file on disk.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "Some Book Title.pdf")
        hio.to_file(input_file, "content")
        argv = [
            "standardize_book_filename.py",
            "--input",
            input_file,
            "--mv",
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        self.assertFalse(os.path.exists(input_file))
        renamed_files = os.listdir(scratch_dir)
        self.assertEqual(len(renamed_files), 1)
        self.assertNotEqual(renamed_files[0], "Some Book Title.pdf")

    def test3(self) -> None:
        """
        Test bare filename with no directory component.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = "Some Book Title.pdf"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            hio.to_file(input_file, "content")
            argv = ["standardize_book_filename.py", "--input", input_file]
            # Run test.
            actual = self._run_main(argv)
        finally:
            os.chdir(cwd)
        # Check outputs.
        self.assertIn("Dir   : .", actual)

    def test4(self) -> None:
        """
        Test missing input file raises assertion error.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "missing.pdf")
        argv = ["standardize_book_filename.py", "--input", input_file]
        parser = dshdsbofi._parse()
        # Run test and check output.
        with mock.patch("sys.argv", argv):
            with self.assertRaises(AssertionError):
                dshdsbofi._main(parser)
