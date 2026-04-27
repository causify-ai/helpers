import logging
import os
from typing import List

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dsddut
import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_pandoc_arguments1
# #############################################################################


class Test_parse_pandoc_arguments1(hunitest.TestCase):
    def test1(self) -> None:
        # Prepare inputs.
        cmd = r"""
        pandoc input.md -o output.pdf --data-dir /data --toc --toc-depth 2
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Call tested function.
        actual = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        # Check output.
        expected = {
            "input": "input.md",
            "output": "output.pdf",
            "in_dir_params": {
                "data-dir": "/data",
                "template": None,
                "extract-media": None,
            },
            "cmd_opts": ["--toc", "--toc-depth", "2"],
        }
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        # Prepare inputs.
        cmd = r"""
        pandoc input.md -o output.pdf --toc
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Call tested function.
        actual = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        # Check output.
        expected = {
            "input": "input.md",
            "output": "output.pdf",
            "in_dir_params": {
                "data-dir": None,
                "template": None,
                "extract-media": None,
            },
            "cmd_opts": ["--toc"],
        }
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        # Prepare inputs.
        cmd = r"""
        pandoc test/outcomes/tmp.pandoc.preprocess_notes.txt \
            -V geometry:margin=1in -f markdown --number-sections \
            --highlight-style=tango -s -t latex \
            --template documentation/pandoc.latex \
            -o test/outcomes/tmp.pandoc.tex \
            --toc --toc-depth 2
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Call tested function.
        actual = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        # Check output.
        expected = {
            "input": "test/outcomes/tmp.pandoc.preprocess_notes.txt",
            "output": "test/outcomes/tmp.pandoc.tex",
            "in_dir_params": {
                "data-dir": None,
                "template": "documentation/pandoc.latex",
                "extract-media": None,
            },
            "cmd_opts": [
                "-V",
                "geometry:margin=1in",
                "-f",
                "markdown",
                "--number-sections",
                "--highlight-style=tango",
                "-s",
                "-t",
                "latex",
                "--toc",
                "--toc-depth",
                "2",
            ],
        }
        self.assert_equal(str(actual), str(expected))

    def test_parse_and_convert1(self) -> None:
        # Prepare inputs.
        cmd = r"""
        pandoc input.md --output output.pdf --data-dir /data --toc --toc-depth 2
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Parse the command.
        parsed_args = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        # Convert back to command.
        converted_cmd = dshdlipa.convert_pandoc_arguments_to_cmd(parsed_args)
        # Check that the converted command matches the original command.
        actual = "pandoc " + converted_cmd
        expected = cmd
        self.assert_equal(actual, expected)


# #############################################################################
# Test_dockerized_pandoc1
# #############################################################################


class Test_dockerized_pandoc1(hunitest.TestCase):
    """
    Test running the `pandoc` command inside a Docker container.
    """

    def run_pandoc(self, txt: str, expected: str) -> None:
        """
        Test running the `pandoc` command in a Docker container.

        This test creates a test file, runs the command inside a Docker
        container with specified command options, and checks if the
        output matches the expected result.
        """
        cmd_opts = ["pandoc"]
        in_file_path = dsddut.create_test_file(self, txt, extension="md")
        cmd_opts.append(f"{in_file_path}")
        out_file_path = os.path.join(self.get_scratch_space(), "output.md")
        cmd_opts.append(f"-o {out_file_path}")
        # Generate the table of contents.
        cmd_opts.append("-s --toc")
        cmd = " ".join(cmd_opts)
        container_type = "pandoc_only"
        use_sudo = hdocker.get_use_sudo()
        dshdlipa.run_dockerized_pandoc(cmd, container_type, use_sudo=use_sudo)
        # Check.
        actual = hio.from_file(out_file_path)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        txt = """
        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        expected = r"""
        - [Good](#good){#toc-good}
          - [Bad](#bad){#toc-bad}

        # Good

        - Good time management
          1.  choose the right tasks

          - Avoid non-essential tasks

        ## Bad

        - Hello
          - World
        """
        self.run_pandoc(txt, expected)
