import logging
import os
import shlex
import subprocess

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)  # noqa: F841


class TestTxtSyntaxHighlighting(hunitest.TestCase):
    """
    Test Vim syntax highlighting for txt files.
    """

    def helper(self, test_file_path: str, vimrc_path: str) -> str:
        """
        Helper method to run Vim and extract syntax highlighting info.

        :param test_file_path: Path to the test file to analyze
        :param vimrc_path: Path to the Vim configuration file
        :return: Syntax highlighting output from Vim
        """
        # Get the directory where the test file is located.
        test_dir = os.path.dirname(test_file_path)
        output_file = os.path.join(test_dir, "test_syntax_output.txt")
        hdbg.dassert_file_exists(test_file_path)
        hdbg.dassert_file_exists(vimrc_path)
        # Run vim to export syntax information.
        cmd = f"vim -u {shlex.quote(vimrc_path)} -c ExportSyntax -c qa! {shlex.quote(test_file_path)}"
        # Run vim with output suppressed.
        subprocess.run(
            cmd, shell=True, capture_output=True, check=False, timeout=10
        )
        # Read the generated output file.
        hdbg.dassert_file_exists(output_file)
        return hio.from_file(output_file)

    def test1(self) -> None:
        """
        Test that Vim successfully exports syntax highlighting information.
        """
        # Prepare inputs.
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_file = os.path.join(current_dir, "test_syntax_examples.txt")
        vimrc_file = os.path.join(current_dir, "test_minimal.vimrc")
        # Run test.
        actual = self.helper(test_file, vimrc_file)
        # Check outputs.
        hdbg.dassert_lt(0, len(actual), "Syntax highlighting output should not be empty")
        # Verify the output contains expected syntax group markers.
        self.assertIn("txtHeader1", actual)
        self.assertIn("txtHeader2", actual)

    def test2(self) -> None:
        """
        Test that syntax highlighting output matches expected golden file.
        """
        # Prepare inputs.
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_file = os.path.join(current_dir, "test_syntax_examples.txt")
        vimrc_file = os.path.join(current_dir, "test_minimal.vimrc")
        # Run test.
        actual = self.helper(test_file, vimrc_file)
        # Check outputs using golden file testing.
        # TODO(ai_gp): Remove tag
        self.check_string(actual, tag="txt_syntax_output")
