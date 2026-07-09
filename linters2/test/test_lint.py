import logging
import os
import unittest.mock as umock
from typing import Dict, List

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters2.lint as lilint

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_filter_files_by_type
# #############################################################################


class Test_filter_files_by_type(hunitest.TestCase):
    """
    Test _filter_files_by_type file categorization logic.
    """

    def _create_files(self, names: List[str]) -> Dict[str, str]:
        """
        Create empty files in scratch dir.

        - Return: {name: abs_path}
        """
        scratch_dir = self.get_scratch_space()
        paths = {}
        for name in names:
            path = os.path.join(scratch_dir, name)
            hio.to_file(path, "")
            paths[name] = path
        return paths

    def test1(self) -> None:
        """
        Default filters — py,ipynb extensions.
        """
        # Prepare inputs.
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md", "qux.txt"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
            paths["qux.txt"],
        ]
        file_types = ["py", "ipynb"]
        # Prepare outputs.
        expected_py_files = [paths["foo.py"]]
        expected_ipynb_files = [paths["bar.ipynb"]]
        expected_md_files = []
        # Run test.
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            file_types,
            skip_dassert_exists=True,
        )
        # Check outputs.
        self.assertEqual(py_files, expected_py_files)
        self.assertEqual(ipynb_files, expected_ipynb_files)
        self.assertEqual(md_files, expected_md_files)

    def test2(self) -> None:
        """
        py extension only — only .py files included.
        """
        # Prepare inputs.
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        file_types = ["py"]
        # Prepare outputs.
        expected_py_files = [paths["foo.py"]]
        expected_ipynb_files = []
        expected_md_files = []
        # Run test.
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            file_types,
            skip_dassert_exists=True,
        )
        # Check outputs.
        self.assertEqual(py_files, expected_py_files)
        self.assertEqual(ipynb_files, expected_ipynb_files)
        self.assertEqual(md_files, expected_md_files)

    def test3(self) -> None:
        """
        ipynb extension only — only .ipynb files included.
        """
        # Prepare inputs.
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        file_types = ["ipynb"]
        # Prepare outputs.
        expected_py_files = []
        expected_ipynb_files = [paths["bar.ipynb"]]
        expected_md_files = []
        # Run test.
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            file_types,
            skip_dassert_exists=True,
        )
        # Check outputs.
        self.assertEqual(py_files, expected_py_files)
        self.assertEqual(ipynb_files, expected_ipynb_files)
        self.assertEqual(md_files, expected_md_files)

    def test4(self) -> None:
        """
        md extension only — only .md files included.
        """
        # Prepare inputs.
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        file_types = ["md"]
        # Prepare outputs.
        expected_py_files = []
        expected_ipynb_files = []
        expected_md_files = [paths["baz.md"]]
        # Run test.
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            file_types,
            skip_dassert_exists=True,
        )
        # Check outputs.
        self.assertEqual(py_files, expected_py_files)
        self.assertEqual(ipynb_files, expected_ipynb_files)
        self.assertEqual(md_files, expected_md_files)

    def test5(self) -> None:
        """
        Paired jupytext .py files excluded by default.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        standalone_py = os.path.join(scratch_dir, "standalone.py")
        paired_py = os.path.join(scratch_dir, "paired.py")
        paired_ipynb = os.path.join(scratch_dir, "paired.ipynb")
        notebook_ipynb = os.path.join(scratch_dir, "notebook.ipynb")
        hio.to_file(standalone_py, "")
        hio.to_file(paired_py, "")
        hio.to_file(paired_ipynb, "")
        hio.to_file(notebook_ipynb, "")
        file_paths = [standalone_py, paired_py, notebook_ipynb]
        file_types = ["py", "ipynb"]
        exclude_paired_jupytext = True
        # Prepare outputs.
        expected_py_files = [standalone_py]
        expected_ipynb_files = [notebook_ipynb]
        expected_md_files = []
        # Run test.
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            file_types,
            skip_dassert_exists=True,
            exclude_paired_jupytext=exclude_paired_jupytext,
        )
        # Check outputs.
        self.assertEqual(py_files, expected_py_files)
        self.assertEqual(ipynb_files, expected_ipynb_files)
        self.assertEqual(md_files, expected_md_files)

    def test6(self) -> None:
        """
        With exclude_paired_jupytext=False, paired .py files included.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        standalone_py = os.path.join(scratch_dir, "standalone.py")
        paired_py = os.path.join(scratch_dir, "paired.py")
        paired_ipynb = os.path.join(scratch_dir, "paired.ipynb")
        notebook_ipynb = os.path.join(scratch_dir, "notebook.ipynb")
        hio.to_file(standalone_py, "")
        hio.to_file(paired_py, "")
        hio.to_file(paired_ipynb, "")
        hio.to_file(notebook_ipynb, "")
        file_paths = [standalone_py, paired_py, notebook_ipynb]
        file_types = ["py", "ipynb"]
        exclude_paired_jupytext = False
        # Prepare outputs.
        expected_py_files = [standalone_py, paired_py]
        expected_ipynb_files = [notebook_ipynb]
        expected_md_files = []
        # Run test.
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            file_types,
            skip_dassert_exists=True,
            exclude_paired_jupytext=exclude_paired_jupytext,
        )
        # Check outputs.
        self.assertEqual(sorted(py_files), sorted(expected_py_files))
        self.assertEqual(ipynb_files, expected_ipynb_files)
        self.assertEqual(md_files, expected_md_files)


# #############################################################################
# Test_run_common_linting_actions
# #############################################################################


class Test_run_common_linting_actions(hunitest.TestCase):
    """
    Test _run_common_linting_actions action runner.
    """

    # TODO(ai_gp): Use the new mock for system.
    @umock.patch("helpers.hsystem.system")
    def test1(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["pre-commit"] — exactly 1 call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["file1.py", "file2.py"]
        actions = ["pre-commit"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 1
        # Run test.
        ret = lilint._run_common_linting_actions(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        call_cmd = mock_system.call_args_list[0][0][0]
        self.assertIn("pre-commit run --files", call_cmd)
        self.assertIn("file1.py file2.py", call_cmd)

    @umock.patch("helpers.hsystem.system")
    def test2(self, mock_system: umock.MagicMock) -> None:
        """
        Empty actions — zero calls, return 0.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["file1.py"]
        actions = []
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 0
        # Run test.
        ret = lilint._run_common_linting_actions(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)


# #############################################################################
# Test_run_python_linting_actions
# #############################################################################


class Test_run_python_linting_actions(hunitest.TestCase):
    """
    Test _run_python_linting_actions action runner for Python files.
    """

    @umock.patch("helpers.hsystem.system")
    def test1(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["normalize_import"] — exactly 1 call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["file1.py"]
        actions = ["normalize_import"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 1
        # Run test.
        ret = lilint._run_python_linting_actions(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        call_cmd = mock_system.call_args_list[0][0][0]
        self.assertIn("normalize_import.py", call_cmd)

    @umock.patch("helpers.hsystem.system")
    def test2(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["normalize_import", "add_class_frames"] — 2 calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["file1.py"]
        actions = ["normalize_import", "add_class_frames"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 2
        # Run test.
        ret = lilint._run_python_linting_actions(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        calls = [call[0][0] for call in mock_system.call_args_list]
        self.assertIn("normalize_import.py", calls[0])
        self.assertIn("add_class_frames.py", calls[1])

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        mock_system returns non-zero — return code is OR-combined.
        """
        # Prepare inputs.
        mock_system.side_effect = [0, 1, 0, 0]
        file_paths = ["file1.py"]
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 1
        # Run test.
        ret = lilint._run_python_linting_actions(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)

    @umock.patch("helpers.hsystem.system")
    def test4(self, mock_system: umock.MagicMock) -> None:
        """
        Empty actions — zero calls, return 0.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["file1.py"]
        actions = []
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 0
        # Run test.
        ret = lilint._run_python_linting_actions(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)


# #############################################################################
# Test_lint_python_files
# #############################################################################


class Test_lint_python_files(hunitest.TestCase):
    """
    Test _lint_python_files Python file linting.
    """

    @umock.patch("helpers.hsystem.system")
    def test1(self, mock_system: umock.MagicMock) -> None:
        """
        Empty file list — returns 0 immediately, no calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = []
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 0
        # Run test.
        ret = lilint._lint_python_files(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)

    @umock.patch("helpers.hsystem.system")
    def test2(self, mock_system: umock.MagicMock) -> None:
        """
        Two .py files, default actions — 4 calls with filenames.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.py", "bar.py"]
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 4
        expected_filenames = ["foo.py", "bar.py"]
        # Run test.
        ret = lilint._lint_python_files(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        calls = [call[0][0] for call in mock_system.call_args_list]
        for call_cmd in calls:
            for filename in expected_filenames:
                self.assertIn(filename, call_cmd)

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["normalize_import"] — exactly 1 call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.py"]
        actions = ["normalize_import"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 1
        # Run test.
        ret = lilint._lint_python_files(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        call_cmd = mock_system.call_args_list[0][0][0]
        self.assertIn("normalize_import.py", call_cmd)


# #############################################################################
# Test_lint_jupyter_files
# #############################################################################


class Test_lint_jupyter_files(hunitest.TestCase):
    """
    Test _lint_jupyter_files Jupyter notebook linting.
    """

    @umock.patch("helpers.hsystem.system")
    def test1(self, mock_system: umock.MagicMock) -> None:
        """
        Empty file list — returns 0 immediately, no calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = []
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 0
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)

    @umock.patch("helpers.hsystem.system")
    def test2(self, mock_system: umock.MagicMock) -> None:
        """
        Two notebooks, default actions — 1 shared pre-commit call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 1
        expected_call_pattern = "pre-commit run --files"
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        call_cmd = mock_system.call_args_list[0][0][0]
        self.assertIn(expected_call_pattern, call_cmd)

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["sync_jupytext"] — 2 jupytext calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        actions = ["sync_jupytext"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 2
        expected_call_patterns = [
            "jupytext --sync foo.ipynb",
            "jupytext --sync bar.ipynb",
        ]
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        calls = [call[0][0] for call in mock_system.call_args_list]
        for i, pattern in enumerate(expected_call_patterns):
            self.assertIn(pattern, calls[i])

    @umock.patch("helpers.hsystem.system")
    def test4(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["pre-commit"] — 1 shared call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        actions = ["pre-commit"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 1
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            actions,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        call_cmd = mock_system.call_args_list[0][0][0]
        self.assertIn("pre-commit run --files", call_cmd)


# #############################################################################
# Test_lint_markdown_files
# #############################################################################


class Test_lint_markdown_files(hunitest.TestCase):
    """
    Test _lint_markdown_files Markdown file linting.
    """

    @umock.patch("helpers.hsystem.system")
    @umock.patch("helpers.hsystem.find_file_in_repo")
    def test1(
        self,
        mock_find_file: umock.MagicMock,
        mock_system: umock.MagicMock,
    ) -> None:
        """
        Empty file list — returns 0 immediately, no calls.
        """
        # Prepare inputs.
        lint_script_path = "/fake/lint_txt.py"
        mock_find_file.return_value = lint_script_path
        mock_system.return_value = 0
        file_paths = []
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 0
        # Run test.
        ret = lilint._lint_markdown_files(
            file_paths,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)

    @umock.patch("helpers.hsystem.system")
    @umock.patch("helpers.hsystem.find_file_in_repo")
    def test2(
        self,
        mock_find_file: umock.MagicMock,
        mock_system: umock.MagicMock,
    ) -> None:
        """
        Two .md files — 1 call to lint_txt.py with filenames.
        """
        # Prepare inputs.
        lint_script_path = "/fake/lint_txt.py"
        mock_find_file.return_value = lint_script_path
        mock_system.return_value = 0
        file_paths = ["doc.md", "readme.md"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_call_count = 1
        expected_cmd_patterns = [
            lint_script_path,
            "--input_files",
            "doc.md",
            "readme.md",
        ]
        # Run test.
        ret = lilint._lint_markdown_files(
            file_paths,
            abort_on_error=abort_on_error,
        )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        self.assertEqual(mock_system.call_count, expected_call_count)
        cmd = mock_system.call_args_list[0][0][0]
        for pattern in expected_cmd_patterns:
            self.assertIn(pattern, cmd)
