import os
from typing import List

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr


# #############################################################################
# Test_build_prettier_container1
# #############################################################################


class Test_build_prettier_container1(hunitest.TestCase):
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
            file_type,
            mode="system",
            force_rebuild=True,
            use_sudo=use_sudo,
        )
        # Verify that the container was built and the command ran.
        self.assertTrue(
            os.path.exists(output_file_path),
            msg=f"Output file {output_file_path} was not created",
        )

    def test2(self) -> None:
        """
        Test that the Prettier version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        file_type = "md"
        image_name = dshdlipr.get_prettier_container_image_name(file_type)
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'prettier --version'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Freeze version output.
        self.check_string(output)

    def test3(self) -> None:
        """
        Test that the Prettier version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        file_type = "tex"
        image_name = dshdalipr.get_prettier_container_image_name(file_type)
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'prettier --version'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Freeze version output.
        self.check_string(output)

# #############################################################################
# Test_run_dockerized_prettier1
# #############################################################################


class Test_run_dockerized_prettier1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        """
        Test prettier formatting with custom options.

        :param txt: Input text to format
        :param expected: Expected formatted output
        """
        # Prepare inputs.
        in_file_path = dshddout.create_test_file(self, txt, extension="txt")
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
        cmd_opts: List[str] = [
            "--parser markdown",
            "--prose-wrap always",
            "--tab-width 2",
        ]
        file_type="md"
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlipr.run_dockerized_prettier(
            in_file_path,
            cmd_opts,
            out_file_path,
            file_type,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        actual = hio.from_file(out_file_path)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        """
        Test that Dockerized Prettier reads an input file, formats it, and
        writes the output file in the output directory.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        hio.create_dir(input_dir, incremental=True)
        input_file_path = os.path.join(input_dir, "input.md")
        hio.to_file(input_file_path, "# Test\n\nHello world")
        #
        output_dir = self.get_output_dir()
        output_file_path = os.path.join(output_dir, "output.md")
        #
        file_type="md"
        hio.create_dir(output_dir, incremental=True)
        cmd_opts = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        # Run test.
        dshdlipr.run_dockerized_prettier(
            input_file_path,
            cmd_opts,
            output_file_path,
            file_type=file_type,
            mode="system",
            force_rebuild=False,
            use_sudo=False,
        )
        # Check outputs.
        self.assertTrue(
            os.path.exists(output_file_path),
            "Output file was not created by Dockerized Prettier.",
        )

    def test2(self) -> None:
        """
        Test prettier formatting with indentation fix.
        """
        # Prepare inputs.
        txt = """
        - A
          - B
              - C
                """
        # Prepare outputs.
        expected = """
        - A
          - B
            - C
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test prettier formatting with bullet point normalization.
        """
        # Prepare inputs.
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        # Prepare outputs.
        expected = r"""
        - Good time management

        1. choose the right tasks
           - avoid non-essential tasks
        """
        # Run test.
        self.helper(txt, expected)


# TODO(ai_gp): Ad the same test but for a txt file.


# #############################################################################
# Test_prettier_on_str
# #############################################################################


class Test_prettier_on_str(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test prettier_on_str helper function.
        """
        # Prepare inputs.
        text = """
        # Title
        hello!

        ## Content
        """
        text = hprint.dedent(text)
        file_type="md"
        cmd_opts = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        # Prepare outputs.
        expected = """
        # Title

        hello!

        ## Content
        """
        # Run test.
        actual = dshdlipr.prettier_on_str(
            text,
            file_type,
            cmd_opts=cmd_opts,
            mode="system",
            force_rebuild=False,
            use_sudo=False,
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)
