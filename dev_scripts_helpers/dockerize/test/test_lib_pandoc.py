import os
import pprint

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa


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

    def test4(self) -> None:
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
        in_file_path = dshddout.create_test_file(self, txt, extension="md")
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


# #############################################################################
# Test_build_pandoc_container
# #############################################################################


class Test_build_pandoc_container(hunitest.TestCase):
    """
    Test building the `pandoc` container.
    """

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Test that the Pandoc Docker container is built correctly.
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        # We'll create a minimal markdown file and run pandoc on it.
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "test.md")
        #
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        output_file = os.path.join(output_dir, "test_output.html")
        # Create a simple markdown file.
        hio.to_file(input_file, "# Test\n\nHello world")
        # Call the function to trigger container build.
        cmd = f"pandoc {input_file} -o {output_file} --to=html"
        dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type="pandoc_texlive",
            force_rebuild=True,
            use_sudo=use_sudo,
        )
        # Verify that the container was built and the command ran.
        self.assertTrue(
            os.path.exists(output_file),
            msg=f"Output file {output_file} was not created",
        )


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
        actual = pprint.pformat(dshdlipa.convert_pandoc_cmd_to_arguments(cmd))
        expected = """
        {'cmd_opts': ['--verbose', '--extra'],
        'in_dir_params': {'data-dir': 'data',
                        'extract-media': 'media',
                        'template': 'default'},
        'input': 'sample.md',
        'output': 'output.md'}
        """
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

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
        actual = pprint.pformat(dshdlipa.convert_pandoc_arguments_to_cmd(params))
        expected = """
        ('sample.md --output output.md --data-dir data --template default '
        '--extract-media media --verbose --extra')"""
        print("Actual...", actual)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_run_dockerized_pandoc
# #############################################################################


@pytest.mark.superslow("~457 seconds.")
class Test_run_dockerized_pandoc(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test Dockerized Pandoc reads an externally provided input file,
        converts it, and writes the output file in the output directory.
        """
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "input.md")
        #
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        output_file = os.path.join(output_dir, "sample.html")
        # Build the pandoc command string.
        cmd = f"pandoc {input_file} -o {output_file} --to=html --toc"
        # Call the function.
        dshdlipa.run_dockerized_pandoc(
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
