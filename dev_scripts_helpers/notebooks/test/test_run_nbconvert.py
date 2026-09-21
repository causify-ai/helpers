import logging
import os
from typing import Any, List, Tuple
from unittest import mock

import dev_scripts_helpers.notebooks.run_nbconvert as dshnrunb
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__main
# #############################################################################


class Test__main(hunitest.TestCase):
    """
    Test `run_nbconvert._main()` function.
    """

    def _create_notebook_dir(self) -> Tuple[str, str]:
        """
        Create a notebook with a stub `docker_cmd.sh` in the scratch space.

        :return: path of the notebook and path of the file where the stub
            `docker_cmd.sh` writes the command it receives
        """
        scratch_dir = os.path.realpath(self.get_scratch_space())
        # Create the notebook.
        notebook_file = os.path.join(scratch_dir, "nb.ipynb")
        hio.to_file(notebook_file, "{}")
        # Create the stub that records its first argument.
        record_file = os.path.join(scratch_dir, "docker_cmd.record.txt")
        docker_cmd = f"""
        echo "$1" > {record_file}
        """
        docker_cmd = hprint.dedent(docker_cmd)
        hio.to_file(os.path.join(scratch_dir, "docker_cmd.sh"), docker_cmd)
        return notebook_file, record_file

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `run_nbconvert._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshnrunb._parse()
        with mock.patch("sys.argv", argv):
            dshnrunb._main(parser)

    def test1(self) -> None:
        """
        Test that `--dry_run` does not call `docker_cmd.sh`.
        """
        # Prepare inputs.
        notebook_file, record_file = self._create_notebook_dir()
        argv = ["run_nbconvert.py", "-i", notebook_file, "--dry_run"]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        self.assertFalse(os.path.exists(record_file))

    def test2(self) -> None:
        """
        Test that `docker_cmd.sh` receives the `nbconvert` command for the
        notebook.
        """
        # Prepare inputs.
        notebook_file, record_file = self._create_notebook_dir()
        argv = ["run_nbconvert.py", "-i", notebook_file]
        # Prepare outputs.
        notebook_dir = os.path.dirname(notebook_file)
        # `docker_cmd.sh` mounts the git root of the notebook dir.
        cmd = f"cd {notebook_dir} && git rev-parse --show-toplevel"
        _, git_root = hsystem.system_to_one_line(cmd)
        git_root = os.path.realpath(git_root)
        template_dir = hgit.find_file_in_git_tree("html_anchorfix")
        template_base_dir = os.path.dirname(template_dir)
        rel_notebook_dir = os.path.relpath(notebook_dir, git_root)
        rel_template_dir = os.path.relpath(template_base_dir, git_root)
        expected = (
            f"cd /git_root/{rel_notebook_dir} && jupyter nbconvert --execute "
            "--to html --ExecutePreprocessor.timeout=300 "
            "--template html_anchorfix "
            "--TemplateExporter.extra_template_basedirs="
            f"/git_root/{rel_template_dir} nb.ipynb"
        )
        # Run test.
        self._run_main(argv)
        # Check outputs.
        # The stub writes the command followed by a newline.
        actual = hio.from_file(record_file).strip()
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that `--cell_timeout` and `--progress` reach the `nbconvert`
        command.
        """
        # Prepare inputs.
        notebook_file, record_file = self._create_notebook_dir()
        argv = [
            "run_nbconvert.py",
            "-i",
            notebook_file,
            "--cell_timeout",
            "60",
            "--progress",
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = hio.from_file(record_file).strip()
        self.assertIn("--log-level=DEBUG", actual)
        self.assertIn("--ExecutePreprocessor.timeout=60", actual)


# #############################################################################
# Test_to_container_path
# #############################################################################


class Test_to_container_path(hunitest.TestCase):
    """
    Test `run_nbconvert._to_container_path()`.
    """

    def helper(self, path: str, git_root: str, expected: str) -> None:
        """
        Helper for _to_container_path.

        :param path: Path to convert
        :param git_root: Git root directory
        :param expected: Expected container path
        """
        # Run test.
        actual = dshnrunb._to_container_path(path, git_root)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a path nested inside the git root.
        """
        # Prepare inputs.
        path = "/home/user/repo/tutorials/L01"
        git_root = "/home/user/repo"
        # Prepare outputs.
        expected = "/git_root/tutorials/L01"
        # Run test.
        self.helper(path, git_root, expected)

    def test2(self) -> None:
        """
        Test that the git root itself maps to `/git_root`.
        """
        # Prepare inputs.
        path = "/home/user/repo"
        git_root = "/home/user/repo"
        # Prepare outputs.
        expected = "/git_root"
        # Run test.
        self.helper(path, git_root, expected)


# #############################################################################
# Test_build_nbconvert_cmd
# #############################################################################


class Test_build_nbconvert_cmd(hunitest.TestCase):
    """
    Test `run_nbconvert._build_nbconvert_cmd()`.
    """

    def test1(self) -> None:
        """
        Test the command for a notebook nested inside the git root.
        """
        # Prepare inputs.
        git_root = "/home/user/repo"
        notebook_file = "/home/user/repo/tutorials/L01/nb.ipynb"
        template_base_dir = (
            "/home/user/repo/helpers_root/dev_scripts_helpers/notebooks/"
            "nbconvert_templates"
        )
        # Prepare outputs.
        expected = (
            "cd /git_root/tutorials/L01 && jupyter nbconvert --execute "
            "--to html --ExecutePreprocessor.timeout=300 "
            "--template html_anchorfix "
            "--TemplateExporter.extra_template_basedirs="
            "/git_root/helpers_root/dev_scripts_helpers/notebooks/"
            "nbconvert_templates nb.ipynb"
        )
        # Run test.
        actual = dshnrunb._build_nbconvert_cmd(
            notebook_file, template_base_dir=template_base_dir, git_root=git_root
        )
        # Check outputs.
        self.assert_equal(actual, expected)


    def test2(self) -> None:
        """
        Test that `cell_timeout` sets the per-cell timeout.
        """
        # Run test.
        actual = self._build(cell_timeout=600)
        # Check outputs.
        self.assertIn("--ExecutePreprocessor.timeout=600 ", actual)
        self.assertNotIn("--log-level", actual)

    def test3(self) -> None:
        """
        Test that `cell_timeout=-1` disables the per-cell timeout.
        """
        # Run test.
        actual = self._build(cell_timeout=-1)
        # Check outputs.
        self.assertIn("--ExecutePreprocessor.timeout=-1 ", actual)

    def test4(self) -> None:
        """
        Test that `progress` turns on the DEBUG log level of `nbconvert`.
        """
        # Run test.
        actual = self._build(progress=True)
        # Check outputs.
        self.assertIn("--to html --log-level=DEBUG --ExecutePreprocessor", actual)

    def test5(self) -> None:
        """
        Test that a `cell_timeout` that is not positive or -1 is rejected.
        """
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            self._build(cell_timeout=0)
        # Check outputs.
        self.assertIn("cell_timeout", str(cm.exception))

    def _build(self, **kwargs: Any) -> str:
        """
        Build the command for a notebook nested inside the git root.

        :param kwargs: args to pass to `_build_nbconvert_cmd()`
        :return: the command
        """
        git_root = "/home/user/repo"
        notebook_file = "/home/user/repo/tutorials/L01/nb.ipynb"
        template_base_dir = (
            "/home/user/repo/helpers_root/dev_scripts_helpers/notebooks/"
            "nbconvert_templates"
        )
        actual = dshnrunb._build_nbconvert_cmd(
            notebook_file,
            template_base_dir=template_base_dir,
            git_root=git_root,
            **kwargs,
        )
        return actual


# #############################################################################
# Test_count_executed_cells
# #############################################################################


class Test_count_executed_cells(hunitest.TestCase):
    """
    Test `run_nbconvert._count_executed_cells()`.
    """

    def test1(self) -> None:
        """
        Test that markdown cells and empty code cells are not counted.
        """
        # Prepare inputs.
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Title"]},
                {"cell_type": "code", "source": ["import os\n", "x = 1"]},
                {"cell_type": "code", "source": []},
                {"cell_type": "code", "source": ["  \n"]},
                {"cell_type": "code", "source": ["y = 2"]},
            ]
        }
        notebook_file = os.path.join(self.get_scratch_space(), "nb.ipynb")
        hio.to_json(notebook_file, notebook)
        # Run test.
        actual = dshnrunb._count_executed_cells(notebook_file)
        # Check outputs.
        self.assertEqual(actual, 2)

    def test2(self) -> None:
        """
        Test a notebook without cells.
        """
        # Prepare inputs.
        notebook_file = os.path.join(self.get_scratch_space(), "nb.ipynb")
        hio.to_file(notebook_file, "{}")
        # Run test.
        actual = dshnrunb._count_executed_cells(notebook_file)
        # Check outputs.
        self.assertEqual(actual, 0)


# #############################################################################
# Test_build_progress_filter
# #############################################################################


class Test_build_progress_filter(hunitest.TestCase):
    """
    Test `run_nbconvert._build_progress_filter()`.
    """

    def test1(self) -> None:
        """
        Test that the filter keeps one line per cell and the important lines.
        """
        # Prepare inputs.
        log = """
        Executing: 'jupyter nbconvert'
        [NbConvertApp] Converting notebook nb.ipynb to html
        [NbConvertApp] Executing cell:
        %load_ext autoreload
        import logging
        [NbConvertApp] msg_type: status
        [NbConvertApp] content: {'text': 'Writing 5 bytes ERROR'}
        [NbConvertApp] Skipping non-executing cell 1
        [NbConvertApp] Executing cell:
        # Display N samples.
        utils.cell()
        [NbConvertApp] msg_type: status
        Traceback (most recent call last):
        CellTimeoutError: timed out
        [NbConvertApp] Writing 1234 bytes to nb.html
        """
        log = hprint.dedent(log)
        log_file = os.path.join(self.get_scratch_space(), "nbconvert.log")
        hio.to_file(log_file, log)
        # Prepare outputs.
        expected = """
        Executing: 'jupyter nbconvert'
        [NbConvertApp] Converting notebook nb.ipynb to html
        [NbConvertApp] cell 1/3: %load_ext autoreload
        [NbConvertApp] cell 2/3: # Display N samples.
        Traceback (most recent call last):
        CellTimeoutError: timed out
        [NbConvertApp] Writing 1234 bytes to nb.html
        """
        # Run test.
        cmd = f"cat {log_file} | {dshnrunb._build_progress_filter(3)}"
        _, actual = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)
