import logging
import os
import unittest.mock as umock
from typing import Any, List, Tuple

import pytest

import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
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
        # Mock `hserver.get_shared_data_dirs()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared1": "/shared_folder1",
            "/data/shared2": "/shared_folder2",
        }
        with umock.patch.object(
            hserver, "get_shared_data_dirs", return_value=mock_mapping
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
        # Mock `hserver.get_shared_data_dirs()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared": "/shared_folder",
        }
        with umock.patch.object(
            hserver, "get_shared_data_dirs", return_value=mock_mapping
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
# Test_convert_to_docker_path1
# #############################################################################


class Test_convert_to_docker_path1(hunitest.TestCase):
    @staticmethod
    def convert_caller_to_callee_docker_path(
        in_file_path: str,
        is_caller_host: bool,
        use_sibling_container_for_callee: bool,
        check_if_exists: bool,
    ) -> Tuple[str, str]:
        """
        Prepare inputs and call the function to convert a file name to Docker
        paths.

        :return: A tuple containing
            - docker_file_path: the Docker file path
            - mount: the Docker mount string
        """
        (
            source_host_path,
            callee_mount_path,
            mount,
        ) = hdocker.get_docker_mount_info(
            is_caller_host, use_sibling_container_for_callee
        )
        docker_file_path = hdocker.convert_caller_to_callee_docker_path(
            in_file_path,
            source_host_path,
            callee_mount_path,
            check_if_exists=check_if_exists,
            is_input=True,
            is_caller_host=is_caller_host,
            use_sibling_container_for_callee=use_sibling_container_for_callee,
        )
        return docker_file_path, mount

    def helper(
        self,
        in_file_path: str,
        is_caller_host: bool,
        use_sibling_container_for_callee: bool,
        check_if_exists: bool,
        exp_docker_file_path: str,
        exp_mount: str,
    ) -> None:
        """
        Test converting a file name to Docker paths.
        """
        # Run test.
        docker_file_path, mount = self.convert_caller_to_callee_docker_path(
            in_file_path,
            is_caller_host,
            use_sibling_container_for_callee,
            check_if_exists,
        )
        # Check output.
        self.assert_equal(docker_file_path, exp_docker_file_path)
        self.assert_equal(mount, exp_mount)

    def test1(self) -> None:
        """
        Test converting a file name to Docker paths.
        """
        # - Prepare inputs.
        dir_name = self.get_input_dir()
        in_file_path = os.path.join(dir_name, "tmp.llm_transform.in.txt")
        is_caller_host = True
        use_sibling_container_for_callee = True
        check_if_exists = False
        # - Prepare outputs.
        helpers_root_path = hgit.find_helpers_root()
        exp_docker_file_path = os.path.join(
            helpers_root_path,
            "helpers/test/outcomes",
            "Test_convert_to_docker_path1.test1/input",
            "tmp.llm_transform.in.txt",
        )
        exp_mount = "type=bind,source=/app,target=/app"
        self.helper(
            in_file_path,
            is_caller_host,
            use_sibling_container_for_callee,
            check_if_exists,
            exp_docker_file_path,
            exp_mount,
        )

    def test2(self) -> None:
        """
        Test converting a file name of an existing file to a Docker path.
        """
        # - Prepare inputs.
        dir_name = self.get_input_dir()
        # Create a file.
        # E.g., in_file_path='/app/helpers/test/outcomes/Test_convert_to_docker_path1.test2/input/input.md'
        in_file_path = os.path.join(dir_name, "tmp.input.md")
        hio.to_file(in_file_path, "empty")
        _LOG.debug(hprint.to_str("in_file_path"))
        is_caller_host = True
        use_sibling_container_for_callee = True
        check_if_exists = True
        # - Prepare outputs.
        helpers_root_path = hgit.find_helpers_root()
        exp_docker_file_path = os.path.join(
            helpers_root_path,
            "helpers/test/outcomes",
            "Test_convert_to_docker_path1.test2/input",
            "tmp.input.md",
        )
        exp_mount = "type=bind,source=/app,target=/app"
        self.helper(
            in_file_path,
            is_caller_host,
            use_sibling_container_for_callee,
            check_if_exists,
            exp_docker_file_path,
            exp_mount,
        )


def _create_test_file(self_: Any, txt: str, extension: str) -> str:
    file_path = os.path.join(self_.get_scratch_space(), f"input.{extension}")
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    _LOG.debug("txt=\n%s", txt)
    hio.to_file(file_path, txt)
    return file_path


# #############################################################################
# Test_run_dockerized_prettier1
# #############################################################################


# TODO(gp): -> Test_dockerized_prettier1
@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_run_dockerized_prettier1(hunitest.TestCase):
    """
    Test running the `prettier` command inside a Docker container.
    """

    def helper(self, txt: str, exp: str) -> None:
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
            in_file_path,
            cmd_opts,
            out_file_path,
            file_type="md",
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check.
        act = hio.from_file(out_file_path)
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )

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
        self.helper(txt, exp)

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
        self.helper(txt, exp)


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
        act = hdocker.convert_pandoc_cmd_to_arguments(cmd)
        # Check output.
        exp = {
            "input": "input.md",
            "output": "output.pdf",
            "in_dir_params": {
                "data-dir": "/data",
                "template": None,
                "extract-media": None,
            },
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
        act = hdocker.convert_pandoc_cmd_to_arguments(cmd)
        # Check output.
        exp = {
            "input": "input.md",
            "output": "output.pdf",
            "in_dir_params": {
                "data-dir": None,
                "template": None,
                "extract-media": None,
            },
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
        act = hdocker.convert_pandoc_cmd_to_arguments(cmd)
        # Check output.
        exp = {
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
        self.assert_equal(str(act), str(exp))

    def test_parse_and_convert1(self) -> None:
        # Prepare inputs.
        cmd = r"""
        pandoc input.md --output output.pdf --data-dir /data --toc --toc-depth 2
        """
        cmd = hprint.dedent(cmd, remove_lead_trail_empty_lines_=True)
        # Parse the command.
        parsed_args = hdocker.convert_pandoc_cmd_to_arguments(cmd)
        # Convert back to command.
        converted_cmd = hdocker.convert_pandoc_arguments_to_cmd(parsed_args)
        # Check that the converted command matches the original command.
        act = "pandoc " + converted_cmd
        exp = cmd
        self.assert_equal(act, exp)


# #############################################################################
# Test_run_dockerized_pandoc1
# #############################################################################


# TODO(gp): -> Test_dockerized_pandoc1
@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_run_dockerized_pandoc1(hunitest.TestCase):
    """
    Test running the `pandoc` command inside a Docker container.
    """

    def run_pandoc(self, txt: str, exp: str) -> None:
        """
        Test running the `pandoc` command in a Docker container.

        This test creates a test file, runs the command inside a Docker
        container with specified command options, and checks if the
        output matches the expected result.
        """
        cmd_opts = ["pandoc"]
        in_file_path = _create_test_file(self, txt, extension="md")
        cmd_opts.append(f"{in_file_path}")
        out_file_path = os.path.join(self.get_scratch_space(), "output.md")
        cmd_opts.append(f"-o {out_file_path}")
        # Generate the table of contents.
        cmd_opts.append("-s --toc")
        cmd = " ".join(cmd_opts)
        container_type = "pandoc_only"
        use_sudo = hdocker.get_use_sudo()
        hdocker.run_dockerized_pandoc(cmd, container_type, use_sudo=use_sudo)
        # Check.
        act = hio.from_file(out_file_path)
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
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
        exp = r"""
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
        self.run_pandoc(txt, exp)


# #############################################################################
# Test_run_markdown_toc1
# #############################################################################


# TODO(gp): -> Test_dockerized_markdown_toc1
@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_run_markdown_toc1(hunitest.TestCase):
    def run_markdown_toc(self, txt: str, exp: str) -> None:
        """
        Test running the `markdown-toc` command in a Docker container.
        """
        cmd_opts: List[str] = []
        # Run `markdown-toc` in a Docker container.
        in_file_path = _create_test_file(self, txt, extension="md")
        use_sudo = hdocker.get_use_sudo()
        force_rebuild = False
        hdocker.run_dockerized_markdown_toc(
            in_file_path,
            cmd_opts,
            use_sudo=use_sudo,
            force_rebuild=force_rebuild,
        )
        # Check.
        act = hio.from_file(in_file_path)
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        """
        Test running the `markdown-toc` command inside a Docker container.
        """
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


# #############################################################################
# Test_dockerized_latex1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_dockerized_latex1(hunitest.TestCase):
    def create_input_file(self) -> Tuple[str, str]:
        txt = r"""
        \documentclass{article}

        \begin{document}

        Hello, World!

        \end{document}
        """
        in_file_path = _create_test_file(self, txt, extension="tex")
        out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
        return in_file_path, out_file_path

    def test_dockerized1(self) -> None:
        """
        Run `latex` inside a Docker container.
        """
        # Prepare inputs.
        in_file_path, out_file_path = self.create_input_file()
        cmd_opts: List[str] = []
        run_latex_again = True
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run function.
        hdocker.run_basic_latex(
            in_file_path,
            cmd_opts,
            run_latex_again,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )

    # TODO(gp): In theory this should go in test_dockerized_latex.py
    def test_cmd_line1(self) -> None:
        """
        Run `latex` using the command line.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("dockerized_latex.py")
        in_file_path, out_file_path = self.create_input_file()
        out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
        # Run function.
        cmd = f"{exec_path} -i {in_file_path} -o {out_file_path}"
        hsystem.system(cmd)
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )

    # TODO(gp): This doesn't work since:
    # 1) `convert_latex_cmd_to_arguments()` is monkey patching with parsing the
    # arguments. Maybe we need to pass multiple arguments to the mocking since
    # it's called multiple times.
    # 2) we re-execute `hdbg.init_logger()` which messes up the global state.
    # def test3(self) -> None:
    #     """
    #     Test the code to run `latex` using the parser.
    #     """
    #     from unittest.mock import patch
    #     import argparse
    #     # Prepare inputs.
    #     in_file_path = self.create_input_file()
    #     out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
    #     # Run function.
    #     mock_args = argparse.Namespace(
    #             input=in_file_path,
    #             output=out_file_path,
    #             run_latex_again=False,
    #             dockerized_force_rebuild=False,
    #             dockerized_use_sudo=hdocker.get_use_sudo(),
    #             log_level=logging.INFO
    #     )
    #     with patch("argparse.ArgumentParser.parse_known_args", return_value=(mock_args, [])):
    #         hdl._main(hdl._parse())
    #     # Check output.
    #     self.assertTrue(os.path.exists(out_file_path), msg=f"Output file {out_file_path} not found")


# #############################################################################
# Test_dockerized_tikz_to_bitmap1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_dockerized_tikz_to_bitmap1(hunitest.TestCase):
    def create_input_file(self) -> Tuple[str, str]:
        txt = r"""
        \documentclass[tikz, border=10pt]{standalone}
        \usepackage{tikz}

        \begin{document}

        \begin{tikzpicture}[scale=0.8]
            % Define the sets as circles with transparency
            \draw[thick, fill=blue!20, opacity=0.6] (0,0) circle (1.5cm);
            \node at (0,0) {$A$};

            \draw[thick, fill=red!20, opacity=0.6] (4,0) circle (1.5cm);
            \node at (4,0) {$B$};

            \draw[thick, fill=green!20, opacity=0.6] (2,3.5) circle (1.5cm);
            \node at (2,3.5) {$C$};
            % Add a title
            \node[font=\bfseries] at (2,-2.5) {Pairwise Exclusive Sets};
            \node[align=center] at (2,-3.3) {No overlap between any pair of sets};
        \end{tikzpicture}

        \end{document}
        """
        in_file_path = _create_test_file(self, txt, extension="tex")
        out_file_path = os.path.join(self.get_scratch_space(), "output.png")
        return in_file_path, out_file_path

    def test_dockerized1(self) -> None:
        """
        Run `tikz_to_bitmap` inside a Docker container.
        """
        # Prepare inputs.
        in_file_path, out_file_path = self.create_input_file()
        cmd_opts = ["-density 300", "-quality 10"]
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run function.
        hdocker.run_dockerized_tikz_to_bitmap(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )

    # TODO(gp): In theory this should go in test_tikz_to_png.py
    def test_command_line1(self) -> None:
        """
        Run `dockerized_tikz_to_bitmap` through the command line.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("dockerized_tikz_to_bitmap.py")
        in_file_path, out_file_path = self.create_input_file()
        # Run function.
        cmd = f"{exec_path} -i {in_file_path} -o {out_file_path} -density 300 -quality 10"
        hsystem.system(cmd)
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )


# #############################################################################
# Test_dockerized_graphviz1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_dockerized_graphviz1(hunitest.TestCase):
    def create_input_file(self) -> Tuple[str, str]:
        txt = r"""
        digraph {
            a -> b[label="0.2",weight="0.2"];
            a -> c[label="0.4",weight="0.4"];
            c -> b[label="0.6",weight="0.6"];
            c -> e[label="0.6",weight="0.6"];
            e -> e[label="0.1",weight="0.1"];
            e -> b[label="0.7",weight="0.7"];
        }
        """
        in_file_path = _create_test_file(self, txt, extension="dot")
        out_file_path = os.path.join(self.get_scratch_space(), "output.png")
        return in_file_path, out_file_path

    def test_dockerized1(self) -> None:
        """
        Run `graphviz` inside a Docker container.
        """
        # Prepare inputs.
        in_file_path, out_file_path = self.create_input_file()
        cmd_opts = []
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run function.
        hdocker.run_dockerized_graphviz(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )

    # TODO(gp): In theory this should go in test_dockerized_graphviz.py
    def test_command_line1(self) -> None:
        """
        Run `dockerized_graphviz` through the command line.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("dockerized_graphviz.py")
        in_file_path, out_file_path = self.create_input_file()
        # Run function.
        cmd = f"{exec_path} -i {in_file_path} -o {out_file_path}"
        hsystem.system(cmd)
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )
