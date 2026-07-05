import contextlib
import io
import os
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.standardize_book_filename as dshdstbf


# #############################################################################
# Test_standardize_book_filename_py
# #############################################################################


# TODO(ai_gp): Factor out common code in an helper and use self.assert_equal.
class Test_standardize_book_filename_py(hunitest.TestCase):
    """
    End-to-end tests for the `standardize_book_filename.py` executable.
    """

    def _run_main(self, argv: list) -> str:
        """
        Run `dshdstbf._main()` with a mocked `sys.argv` and capture stdout.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :return: captured stdout
        """
        parser = dshdstbf._parse()
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            with mock.patch("sys.argv", argv):
                dshdstbf._main(parser)
        return buf.getvalue()

    def test1(self) -> None:
        """
        Test happy path: dry run does not rename the file on disk.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "Some Book Title.pdf")
        hio.to_file(input_file, "content")
        argv = ["standardize_book_filename.py", "--input", input_file]
        # Run test.
        actual = self._run_main(argv)
        # Check outputs.
        self.assertIn("Rename", actual)
        self.assertIn("Some Book Title.pdf", actual)
        self.assertTrue(os.path.exists(input_file))

    def test2(self) -> None:
        """
        Test edge case: `--mv` actually renames the file on disk.
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
        Test edge case: bare filename with no directory component.
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
        Test edge case: missing input file raises an assertion error.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "missing.pdf")
        argv = ["standardize_book_filename.py", "--input", input_file]
        parser = dshdstbf._parse()
        # Run test and check output.
        with mock.patch("sys.argv", argv):
            with self.assertRaises(AssertionError):
                dshdstbf._main(parser)
