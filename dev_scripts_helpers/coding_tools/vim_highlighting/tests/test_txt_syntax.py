import logging
import os
import subprocess

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
        # Get the directory where the test file is located
        test_dir = os.path.dirname(test_file_path)
        output_file = os.path.join(test_dir, "test_syntax_output.txt")

        # Run vim to export syntax information
        # TODO(ai_gp): Use a single string instead of an array.
        cmd = [
            "vim",
            "-u",
            vimrc_path,
            "-c",
            "ExportSyntax",
            "-c",
            "qa!",
            test_file_path,
        ]
        # Run vim with output suppressed
        subprocess.run(
            cmd, capture_output=True, check=False, timeout=10
        )

        # Read the generated output file
        # TODO(ai_gp): Use hio.from_file
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                return f.read()

        # If no output file, return empty string
        return ""

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
        self.assertGreater(
            len(actual),
            0,
            "Syntax highlighting output should not be empty",
        )
        # Verify the output contains expected syntax group markers
        self.assertIn("txtHeader1", actual)
        self.assertIn("txtHeader2", actual)

    def test2(self) -> None:
        """
        Test that syntax highlighting output matches expected golden file.

        This test uses the golden file framework to compare the actual
        syntax highlighting output with the expected output stored in
        the test outcomes directory.
        """
        # Prepare inputs.
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_file = os.path.join(current_dir, "test_syntax_examples.txt")
        vimrc_file = os.path.join(current_dir, "test_minimal.vimrc")

        # Run test.
        actual = self.helper(test_file, vimrc_file)

        # Check outputs using golden file testing.
        self.check_string(actual, tag="txt_syntax_output")
