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

    def _helper_check_version(self, file_type: str) -> None:
        """
        Check that Prettier version command works in container.

        :param file_type: File type for container image
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        image_name = dshdlipr.get_prettier_container_image_name(file_type)
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'prettier --version'"
        )
        # Run test.
        _, output = hsystem.system_to_string(cmd)
        # Check outputs.
        self.check_string(output)

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Test that the Prettier Docker container is built correctly.
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        file_type = "md"
        input_dir = self.get_input_dir()
        output_dir = self.get_output_dir()
        input_file_path = os.path.join(input_dir, "test.md")
        hio.to_file(input_file_path, "# Test\n\nHello world")
        # Prepare outputs.
        hio.create_dir(output_dir, incremental=True)
        output_file_path = os.path.join(output_dir, "test_output.md")
        cmd_opts = ["--parser", "markdown", "--prose-wrap", "always"]
        # Run test.
        dshdlipr.run_dockerized_prettier(
            input_file_path,
            cmd_opts,
            output_file_path,
            file_type,
            mode="system",
            force_rebuild=True,
            use_sudo=use_sudo,
        )
        # Check outputs.
        self.assertTrue(
            os.path.exists(output_file_path),
            msg=f"Output file {output_file_path} was not created",
        )

    def test2(self) -> None:
        """
        Test that the Prettier version matches expected output for md file type.
        """
        self._helper_check_version("md")

    def test3(self) -> None:
        """
        Test that the Prettier version matches expected output for tex file type.
        """
        self._helper_check_version("tex")


# #############################################################################
# Test_run_dockerized_prettier_md1
# #############################################################################


class Test_run_dockerized_prettier_md1(hunitest.TestCase):
    def _helper(self, txt: str, expected: str) -> None:
        """
        Test prettier formatting with custom options.

        :param txt: Input text to format
        :param expected: Expected formatted output
        """
        # Prepare inputs.
        in_file_path = dshddout.create_test_file(self, txt, extension="txt")
        file_type = "md"
        cmd_opts: List[str] = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Prepare outputs.
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
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
        Test that Dockerized Prettier reads an input file and writes output.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        hio.create_dir(input_dir, incremental=True)
        input_file_path = os.path.join(input_dir, "input.md")
        hio.to_file(input_file_path, "# Test\n\nHello world")
        file_type = "md"
        cmd_opts = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        # Prepare outputs.
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        output_file_path = os.path.join(output_dir, "output.md")
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
        # Expected: indentation normalized.
        expected = """
        - A
          - B
            - C
        """
        # Run test.
        self._helper(txt, expected)

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
        # Expected: bullet format and indentation normalized.
        expected = r"""
        - Good time management

        1. choose the right tasks
           - avoid non-essential tasks
        """
        # Run test.
        self._helper(txt, expected)


# #############################################################################
# Test_run_dockerized_prettier_txt1
# #############################################################################


class Test_run_dockerized_prettier_txt1(hunitest.TestCase):
    def _helper(self, txt: str, expected: str) -> None:
        """
        Test prettier formatting with custom options.

        :param txt: Input text to format
        :param expected: Expected formatted output
        """
        # Prepare inputs.
        in_file_path = dshddout.create_test_file(self, txt, extension="txt")
        file_type = "txt"
        cmd_opts: List[str] = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Prepare outputs.
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
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
        Test that Dockerized Prettier reads an input file and writes output.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        hio.create_dir(input_dir, incremental=True)
        input_file_path = os.path.join(input_dir, "input.txt")
        hio.to_file(input_file_path, "# Test\n\nHello world")
        file_type = "txt"
        cmd_opts = [
            "--parser",
            "markdown",
            "--prose-wrap",
            "always",
            "--tab-width",
            "2",
        ]
        # Prepare outputs.
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        output_file_path = os.path.join(output_dir, "output.txt")
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
        # Expected: indentation normalized.
        expected = """
        - A
          - B
            - C
        """
        # Run test.
        self._helper(txt, expected)

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
        # Expected: bullet format and indentation normalized.
        expected = r"""
        - Good time management

        1. choose the right tasks
           - avoid non-essential tasks
        """
        # Run test.
        self._helper(txt, expected)


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
        file_type = "md"
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
        expected = hprint.dedent(expected)
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
        self.assert_equal(actual, expected)
