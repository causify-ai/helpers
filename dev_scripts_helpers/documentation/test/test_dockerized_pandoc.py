import os

import pytest

import helpers.hdocker as hdocker
import helpers.hunit_test as hunitest


# #############################################################################
# Test_Pandoc_Cmd_Conversion
# #############################################################################


class Test_Pandoc_Cmd_Conversion(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test `convert_pandoc_cmd_to_arguments` to parse a pandoc command string
        into a dictionary.
        """
        # Create a sample pandoc command string.
        cmd = (
            "pandoc sample.md -o output.md --data-dir data "
            "--template default --extract-media media -- --verbose --extra"
        )
        # Call function to test.
        result = hdocker.convert_pandoc_cmd_to_arguments(cmd)
        expected = {
            "input": "sample.md",
            "output": "output.md",
            "in_dir_params": {
                "data-dir": "data",
                "template": "default",
                "extract-media": "media",
            },
            "cmd_opts": ["--verbose", "--extra"],
        }
        # Check output.
        self.assertEqual(result, expected)

    def test2(self) -> None:
        """
        Test `convert_pandoc_arguments_to_cmd` to build a command string from a
        dictionary of parameters.
        """
        # Prepare inputs.
        params = {
            "input": "sample.md",
            "output": "output.md",
            "in_dir_params": {
                "data-dir": "data",
                "template": "default",
                "extract-media": "media",
            },
            "cmd_opts": ["--verbose", "--extra"],
        }
        # Call function to test.
        cmd = hdocker.convert_pandoc_arguments_to_cmd(params)
        expected_cmd = (
            "sample.md --output output.md --data-dir data --template default "
            "--extract-media media --verbose --extra"
        )
        # Check output.
        self.assertEqual(cmd, expected_cmd)


# #############################################################################
# Test_run_dockerized_pandoc
# #############################################################################


class Test_run_dockerized_pandoc(hunitest.TestCase):

    @pytest.mark.timeout(30)
    def test1(self) -> None:
        """
        Test Dockerized Pandoc reads an externally provided input file,
        converts it, and writes the output file in the output directory.
        """
        input_dir = self.get_input_dir()
        output_dir = self.get_output_dir()
        input_file = os.path.join(input_dir, "input.md")
        output_file = os.path.join(output_dir, "sample.pdf")
        # Build the pandoc command string.
        cmd = f"pandoc {input_file} -o {output_file} --toc"
        # Call the function.
        hdocker.run_dockerized_pandoc(
            cmd,
            container_type="pandoc_texlive",
            force_rebuild=True,
            use_sudo=False,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(output_file),
            "Output file was not created by the Dockerized Pandoc command.",
        )
