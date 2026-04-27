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
        """
        Test parsing pandoc command with data-dir and toc options.
        """
        # Prepare inputs.
        cmd = r"""
        pandoc input.md -o output.pdf --data-dir /data --toc --toc-depth 2
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Prepare outputs.
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
        # Run test.
        actual = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test parsing pandoc command with minimal options.
        """
        # Prepare inputs.
        cmd = r"""
        pandoc input.md -o output.pdf --toc
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Prepare outputs.
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
        # Run test.
        actual = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test parsing complex pandoc command with template and formatting.
        """
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
        # Prepare outputs.
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
        # Run test.
        actual = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test round-trip conversion of pandoc command.
        """
        # Prepare inputs.
        cmd = r"""
        pandoc input.md --output output.pdf --data-dir /data --toc --toc-depth 2
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Run test.
        parsed_args = dshdlipa.convert_pandoc_cmd_to_arguments(cmd)
        converted_cmd = dshdlipa.convert_pandoc_arguments_to_cmd(parsed_args)
        actual = "pandoc " + converted_cmd
        # Check outputs.
        expected = cmd
        self.assert_equal(actual, expected)


# #############################################################################
# Test_dockerized_pandoc1
# #############################################################################


class Test_run_dockerized_pandoc1(hunitest.TestCase):
    """
    Test running the `pandoc` command inside a Docker container.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test running the `pandoc` command in a Docker container.

        :param txt: Input markdown text
        :param expected: Expected HTML output with table of contents
        """
        # Prepare inputs.
        in_file_path = dshddout.create_test_file(self, txt, extension="md")
        out_file_path = os.path.join(self.get_scratch_space(), "output.md")
        cmd_opts = [
            "pandoc",
            f"{in_file_path}",
            f"-o {out_file_path}",
            "-s --toc",
        ]
        cmd = " ".join(cmd_opts)
        container_type = "pandoc_only"
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlipa.run_dockerized_pandoc(cmd, container_type, use_sudo=use_sudo)
        # Check outputs.
        actual = hio.from_file(out_file_path)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        """
        Test running pandoc with table of contents generation.
        """
        # Prepare inputs.
        txt = """
        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        # Prepare outputs.
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
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_build_pandoc_container
# #############################################################################


# TODO(ai_gp): -> Test_build_pandoc_container1
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
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "test.md")
        output_dir = self.get_output_dir()
        output_file = os.path.join(output_dir, "test_output.html")
        hio.create_dir(output_dir, incremental=True)
        hio.to_file(input_file, "# Test\n\nHello world")
        cmd = f"pandoc {input_file} -o {output_file} --to=html"
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type="pandoc_texlive",
            force_rebuild=True,
            use_sudo=use_sudo,
        )
        # Check outputs.
        self.assertTrue(
            os.path.exists(output_file),
            msg=f"Output file {output_file} was not created",
        )


# #############################################################################
# Test_Pandoc_Cmd_Conversion
# #############################################################################


# TODO(ai_gp): -> Test_convert_pandoc_cmd_to_arguments1
class Test_Pandoc_Cmd_Conversion(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test `convert_pandoc_cmd_to_arguments` to parse a pandoc command string
        into a dictionary.
        """
        # Prepare inputs.
        cmd = (
            "pandoc sample.md -o output.md --data-dir data "
            "--template default --extract-media media -- --verbose --extra"
        )
        # Prepare outputs.
        expected = """
        {'cmd_opts': ['--verbose', '--extra'],
        'in_dir_params': {'data-dir': 'data',
                        'extract-media': 'media',
                        'template': 'default'},
        'input': 'sample.md',
        'output': 'output.md'}
        """
        # Run test.
        actual = pprint.pformat(dshdlipa.convert_pandoc_cmd_to_arguments(cmd))
        # Check outputs.
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
        # Prepare outputs.
        expected = """
        ('sample.md --output output.md --data-dir data --template default '
        '--extract-media media --verbose --extra')"""
        # Run test.
        actual = pprint.pformat(dshdlipa.convert_pandoc_arguments_to_cmd(params))
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_run_dockerized_pandoc
# #############################################################################


@pytest.mark.superslow("~457 seconds.")
# TODO(ai_gp): -> Test_run_dockerized_pandoc2
class Test_run_dockerized_pandoc(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test Dockerized Pandoc reads an externally provided input file,
        converts it, and writes the output file in the output directory.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "input.md")
        output_dir = self.get_output_dir()
        output_file = os.path.join(output_dir, "sample.html")
        hio.create_dir(output_dir, incremental=True)
        cmd = f"pandoc {input_file} -o {output_file} --to=html --toc"
        # Run test.
        dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type="pandoc_texlive",
            force_rebuild=False,
            use_sudo=False,
        )
        # Check outputs.
        self.assertTrue(
            os.path.exists(output_file),
            "Output file was not created by the Dockerized Pandoc command.",
        )
