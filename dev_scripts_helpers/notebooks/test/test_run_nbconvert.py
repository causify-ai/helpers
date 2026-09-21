import logging
import os
from typing import List, Tuple
from unittest import mock

import dev_scripts_helpers.notebooks.run_nbconvert as dshnrunb
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_to_container_path
# #############################################################################


class Test_to_container_path(hunitest.TestCase):
    """
    Test `run_nbconvert._to_container_path()`.
    """

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
        actual = dshnrunb._to_container_path(path, git_root)
        # Check outputs.
        self.assert_equal(actual, expected)

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
        actual = dshnrunb._to_container_path(path, git_root)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that a path outside the git root is rejected.
        """
        # Prepare inputs.
        path = "/home/user/other_repo/tutorials"
        git_root = "/home/user/repo"
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dshnrunb._to_container_path(path, git_root)


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
            "--to html --ExecutePreprocessor.timeout=-1 "
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


# #############################################################################
# Test_run_nbconvert_py
# #############################################################################


class Test_run_nbconvert_py(hunitest.TestCase):
    """
    End-to-end tests for the `run_nbconvert.py` executable.

    A stub `docker_cmd.sh` records the command it receives, so no Docker is
    needed.
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
            "--to html --ExecutePreprocessor.timeout=-1 "
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
