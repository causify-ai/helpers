import os

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_run_dockerized_prettier
# #############################################################################


class Test_run_dockerized_prettier(hunitest.TestCase):

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Test that Dockerized Prettier reads an input file, formats it, and
        writes the output file in the output directory.
        """
        input_dir = self.get_input_dir()
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        input_file_path = os.path.join(input_dir, "input.md")
        output_file_path = os.path.join(output_dir, "output.md")
        # Prepare input command options.
        cmd_opts = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        # Call function to test.
        hdocker.run_dockerized_prettier(
            input_file_path,
            cmd_opts,
            output_file_path,
            return_cmd=False,
            force_rebuild=False,
            use_sudo=False,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(output_file_path),
            "Output file was not created by Dockerized Prettier.",
        )
