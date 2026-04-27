import os
from typing import List

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr


# #############################################################################
# Test_build_prettier_container
# #############################################################################


class Test_build_prettier_container(hunitest.TestCase):
    """
    Test building the `prettier` container.
    """

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Test that the Prettier Docker container is built correctly.
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        file_type = "md"
        # Build the container by calling run_dockerized_prettier.
        # We'll create a minimal markdown file and run prettier on it.
        input_dir = self.get_input_dir()
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        input_file_path = os.path.join(input_dir, "test.md")
        output_file_path = os.path.join(output_dir, "test_output.md")
        # Create a simple markdown file.
        hio.to_file(input_file_path, "# Test\n\nHello world")
        # Call the function to trigger container build.
        cmd_opts = ["--parser", "markdown", "--prose-wrap", "always"]
        dshdlipr.run_dockerized_prettier(
            input_file_path,
            cmd_opts,
            output_file_path,
            file_type=file_type,
            mode="system",
            force_rebuild=True,
            use_sudo=use_sudo,
        )
        # Verify that the container was built and the command ran.
        self.assertTrue(
            os.path.exists(output_file_path),
            msg=f"Output file {output_file_path} was not created",
        )


# #############################################################################
# Test_run_dockerized_prettier
# #############################################################################


# TODO(ai_gp): -> Test_run_dockerized_prettier1
class Test_run_dockerized_prettier(hunitest.TestCase):
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
        dshdlipr.run_dockerized_prettier(
            input_file_path,
            cmd_opts,
            output_file_path,
            file_type="md",
            mode="system",
            force_rebuild=False,
            use_sudo=False,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(output_file_path),
            "Output file was not created by Dockerized Prettier.",
        )

    def test_prettier_on_str1(self) -> None:
        """
        Test that Dockerized Prettier reads an input file, formats it, and
        writes the output file in the output directory.
        """
        text = """
        # Title
        hello!

        ## Content
        """
        text = hprint.dedent(text)
        cmd_opts = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        # Call function to test.
        actual = dshdlipr.prettier_on_str(
            text,
            file_type="md",
            cmd_opts=cmd_opts,
            mode="system",
            force_rebuild=False,
            use_sudo=False,
        )
        # Check output.
        expected = """
        # Title

        hello!

        ## Content
        """
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_dockerized_prettier1
# #############################################################################


class Test_dockerized_prettier1(hunitest.TestCase):
    """
    Test running the `prettier` command inside a Docker container.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test running the `prettier` command in a Docker container.

        This test creates a test file, runs the command inside a Docker
        container with specified command options, and checks if the
        output matches the expected result.
        """
        cmd_opts: List[str] = []
        cmd_opts.append("--parser markdown")
        cmd_opts.append("--prose-wrap always")
        tab_width = 2
        cmd_opts.append(f"--tab-width {tab_width}")
        # Run `prettier` in a Docker container.
        in_file_path = dshddout.create_test_file(self, txt, extension="txt")
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        dshdlipr.run_dockerized_prettier(
            in_file_path,
            cmd_opts,
            out_file_path,
            file_type="md",
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check.
        actual = hio.from_file(out_file_path)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        txt = """
        - A
          - B
              - C
                """
        expected = """
        - A
          - B
            - C
        """
        self.helper(txt, expected)

    def test2(self) -> None:
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        expected = r"""
        - Good time management

        1. choose the right tasks
           - avoid non-essential tasks
        """
        self.helper(txt, expected)
