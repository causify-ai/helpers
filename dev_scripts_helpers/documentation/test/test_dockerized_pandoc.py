import os
import pprint

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
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
        act = pprint.pformat(hdocker.convert_pandoc_cmd_to_arguments(cmd))
        exp = """
        {'cmd_opts': ['--verbose', '--extra'],
        'in_dir_params': {'data-dir': 'data',
                        'extract-media': 'media',
                        'template': 'default'},
        'input': 'sample.md',
        'output': 'output.md'}
        """
        # Check output.
        self.assert_equal(act, exp, fuzzy_match=True)

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
        act = pprint.pformat(hdocker.convert_pandoc_arguments_to_cmd(params))
        exp = """
        ('sample.md --output output.md --data-dir data --template default '
        '--extract-media media --verbose --extra')"""
        print("Actual...", act)
        # Check output.
        self.assert_equal(act, exp, fuzzy_match=True)


# #############################################################################
# Test_run_dockerized_pandoc
# #############################################################################


class Test_run_dockerized_pandoc(hunitest.TestCase):

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Test Dockerized Pandoc reads an externally provided input file,
        converts it, and writes the output file in the output directory.
        """
        input_dir = self.get_input_dir()
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        input_file = os.path.join(input_dir, "input.md")
        output_file = os.path.join(output_dir, "sample.html")
        # Build the pandoc command string.
        cmd = f"pandoc {input_file} -o {output_file} --to=html --toc"
        # Call the function.
        hdocker.run_dockerized_pandoc(
            cmd,
            container_type="pandoc_texlive",
            force_rebuild=False,
            use_sudo=False,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(output_file),
            "Output file was not created by the Dockerized Pandoc command.",
        )
