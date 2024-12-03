import logging
import os
import unittest.mock as umock
from typing import Any, List

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_replace_shared_root_path1
# #############################################################################


class Test_replace_shared_root_path1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test replacing shared root path.
        """
        # Mock `henv.execute_repo_config_code()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared1": "/shared_folder1",
            "/data/shared2": "/shared_folder2",
        }
        with umock.patch.object(
            hdocker.henv, "execute_repo_config_code", return_value=mock_mapping
        ):
            # Test replacing shared root path.
            path1 = "/data/shared1/asset1"
            act1 = hdocker.replace_shared_root_path(path1)
            exp1 = "/shared_folder1/asset1"
            self.assertEqual(act1, exp1)
            #
            path2 = "/data/shared2/asset2"
            act2 = hdocker.replace_shared_root_path(path2)
            exp2 = "/shared_folder2/asset2"
            self.assertEqual(act2, exp2)
            #
            path3 = 'object("/data/shared2/asset2/item")'
            act3 = hdocker.replace_shared_root_path(path3)
            exp3 = 'object("/shared_folder2/asset2/item")'
            self.assertEqual(act3, exp3)

    def test2(self) -> None:
        """
        Test replacing shared root path with the `replace_ecs_tokyo` parameter.
        """
        # Mock `henv.execute_repo_config_code()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared": "/shared_folder",
        }
        with umock.patch.object(
            hdocker.henv, "execute_repo_config_code", return_value=mock_mapping
        ):
            # Test if `ecs_tokyo` is replaced if `replace_ecs_tokyo = True`.
            path1 = 'object("/data/shared/ecs_tokyo/asset2/item")'
            replace_ecs_tokyo = True
            act1 = hdocker.replace_shared_root_path(
                path1, replace_ecs_tokyo=replace_ecs_tokyo
            )
            exp1 = 'object("/shared_folder/ecs/asset2/item")'
            self.assertEqual(act1, exp1)
            # Test if `ecs_tokyo` is not replaced if `replace_ecs_tokyo` is not
            # defined.
            path2 = 'object("/data/shared/ecs_tokyo/asset2/item")'
            act2 = hdocker.replace_shared_root_path(path2)
            exp2 = 'object("/shared_folder/ecs_tokyo/asset2/item")'
            self.assertEqual(act2, exp2)


# #############################################################################
# Test_convert_file_names_to_docker1
# #############################################################################

# class Test_convert_file_names_to_docker1(hunitest.TestCase):
#     def test1(self) -> None:
#         dir_name = self.get_input_dir()
#         # Prepare inputs.
#         in_file_path = os.path.join(dir_name, "input.md")
#         hio.to_file(in_file_path, "empty")
#         out_file_path = os.path.join(dir_name, "output.md")
#         # Call tested function.
#         act_in_file_path, act_out_file_path, act_mount = hdocker.convert_file_names_to_docker(in_file_path, out_file_path)
#         # Check output.
#         exp_in_file_path = r"""helpers/test/outcomes/Test_convert_file_names_to_docker1.test1/input/input.md"""
#         exp_out_file_path = r"src/helpers1/test2.md"
#         exp_mount = r"""
#         type=bind,source=/Users/saggese/src/helpers1,target=/src
#         """
#         self.assert_equal(act_in_file_path, exp_in_file_path, dedent=True)
#         self.assert_equal(act_out_file_path, exp_out_file_path, dedent=True)
#         self.assert_equal(act_mount, exp_mount, dedent=True)

# #############################################################################
# Test_run_dockerized_prettier1
# #############################################################################


def _create_test_file(self_: Any, txt: str, extension: str) -> str:
    file_path = os.path.join(self_.get_scratch_space(), f"input.{extension}")
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    _LOG.debug("txt=\n%s", txt)
    hio.to_file(file_path, txt)
    return file_path


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_run_dockerized_prettier1(hunitest.TestCase):
    """
    Test running the `prettier` command inside a Docker container.
    """

    def test1(self) -> None:
        txt = """
        - A
          - B
              - C
                """
        exp = """
        - A
          - B
            - C
        """
        self.run_prettier(txt, exp)

    def test2(self) -> None:
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        exp = r"""
        - Good time management

        1. choose the right tasks
           - avoid non-essential tasks
        """
        self.run_prettier(txt, exp)

    def run_prettier(self, txt: str, exp: str) -> None:
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
        in_file_path = _create_test_file(self, txt, extension="txt")
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        hdocker.run_dockerized_prettier(
            in_file_path, out_file_path, cmd_opts, force_rebuild, use_sudo
        )
        # Check.
        act = hio.from_file(out_file_path)
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )


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
        act = hdocker.parse_pandoc_arguments(cmd)
        # Check output.
        exp = {
            "in_file_path": "input.md",
            "out_file_path": "output.pdf",
            "data_dir": "/data",
            "cmd_opts": ["--toc", "--toc-depth", "2"],
        }
        self.assert_equal(str(act), str(exp))

    def test2(self) -> None:
        # Prepare inputs.
        cmd = r"""
        pandoc input.md -o output.pdf --toc
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Call tested function.
        act = hdocker.parse_pandoc_arguments(cmd)
        # Check output.
        exp = {
            "in_file_path": "input.md",
            "out_file_path": "output.pdf",
            "data_dir": None,
            "cmd_opts": ["--toc"],
        }
        self.assert_equal(str(act), str(exp))

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
        act = hdocker.parse_pandoc_arguments(cmd)
        # Check output.
        exp = {
            "in_file_path": "test/outcomes/tmp.pandoc.preprocess_notes.txt",
            "out_file_path": "test/outcomes/tmp.pandoc.tex",
            "data_dir": None,
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
                "--template",
                "documentation/pandoc.latex",
                "--toc",
                "--toc-depth",
                "2",
            ],
        }
        self.assert_equal(str(act), str(exp))

    def test_parse_and_convert1(self) -> None:
        # Prepare inputs.
        cmd = r"""
        pandoc input.md --output output.pdf --data-dir /data --toc --toc-depth 2
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Parse the command.
        parsed_args = hdocker.parse_pandoc_arguments(cmd)
        # Convert back to command.
        converted_cmd = hdocker.convert_pandoc_arguments_to_cmd(
            parsed_args["in_file_path"],
            parsed_args["out_file_path"],
            parsed_args["cmd_opts"],
            parsed_args["data_dir"],
        )
        # Check that the converted command matches the original command.
        act = "pandoc " + converted_cmd
        exp = cmd
        self.assert_equal(act, exp)


# #############################################################################
# Test_run_dockerized_pandoc1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_run_dockerized_pandoc1(hunitest.TestCase):
    """
    Test running the `pandoc` command inside a Docker container.
    """

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
        exp = r"""
        -   [Good](#good){#toc-good}
            -   [Bad](#bad){#toc-bad}

        # Good

        -   Good time management
            1.  choose the right tasks

            -   Avoid non-essential tasks

        ## Bad

        -   Hello
            -   World
        """
        self.run_pandoc(txt, exp)

    def run_pandoc(self, txt: str, exp: str) -> None:
        """
        Test running the `pandoc` command in a Docker container.

        This test creates a test file, runs the command inside a Docker
        container with specified command options, and checks if the
        output matches the expected result.
        """
        cmd_opts: List[str] = []
        # Generate the table of contents.
        cmd_opts.append("-s --toc")
        # Run `pandoc` in a Docker container.
        in_file_path = _create_test_file(self, txt, extension="md")
        out_file_path = os.path.join(self.get_scratch_space(), "output.md")
        data_dir = None
        use_sudo = hdocker.get_use_sudo()
        hdocker.run_dockerized_pandoc(
            in_file_path, out_file_path, cmd_opts, data_dir, use_sudo
        )
        # Check.
        act = hio.from_file(out_file_path)
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )


# #############################################################################
# Test_run_markdown_toc1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_run_markdown_toc1(hunitest.TestCase):
    """
    Test running the `markdown-toc` command inside a Docker container.
    """

    def test1(self) -> None:
        txt = """
        <!-- toc -->

        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        exp = r"""
        <!-- toc -->

        - [Good](#good)
          * [Bad](#bad)

        <!-- tocstop -->

        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        self.run_markdown_toc(txt, exp)

    def run_markdown_toc(self, txt: str, exp: str) -> None:
        """
        Test running the `markdown-toc` command in a Docker container.
        """
        cmd_opts: List[str] = []
        # Run `markdown-toc` in a Docker container.
        in_file_path = _create_test_file(self, txt, extension="md")
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        hdocker.run_dockerized_markdown_toc(
            in_file_path, force_rebuild, cmd_opts, use_sudo
        )
        # Check.
        act = hio.from_file(in_file_path)
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )
