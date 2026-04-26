import os
import unittest.mock as umock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters2.lint as lilint


# #############################################################################
# Test_filter_files_by_type
# #############################################################################


class Test_filter_files_by_type(hunitest.TestCase):
    """
    Test _filter_files_by_type file categorization logic.
    """

    def _create_files(self, names: list[str]) -> dict[str, str]:
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
        Default filters — auto-detects extensions with defaults.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md", "qux.txt"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
            paths["qux.txt"],
        ]
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            keep_python_files=True,
            keep_jupyter_files=True,
            keep_markdown_files=False,
            skip_dassert_exists=True,
        )
        self.assertEqual(py_files, [paths["foo.py"]])
        self.assertEqual(ipynb_files, [paths["bar.ipynb"]])
        self.assertEqual(md_files, [])

    def test2(self) -> None:
        """
        py=True filter — only .py files included.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            keep_python_files=True,
            keep_jupyter_files=False,
            keep_markdown_files=False,
            skip_dassert_exists=True,
        )
        self.assertEqual(py_files, [paths["foo.py"]])
        self.assertEqual(ipynb_files, [])
        self.assertEqual(md_files, [])

    def test3(self) -> None:
        """
        ipynb=True filter — only .ipynb files included.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            keep_python_files=False,
            keep_jupyter_files=True,
            keep_markdown_files=False,
            skip_dassert_exists=True,
        )
        self.assertEqual(py_files, [])
        self.assertEqual(ipynb_files, [paths["bar.ipynb"]])
        self.assertEqual(md_files, [])

    def test4(self) -> None:
        """
        md=True filter — only .md files included.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            keep_python_files=False,
            keep_jupyter_files=False,
            keep_markdown_files=True,
            skip_dassert_exists=True,
        )
        self.assertEqual(py_files, [])
        self.assertEqual(ipynb_files, [])
        self.assertEqual(md_files, [paths["baz.md"]])

    def test5(self) -> None:
        """
        Paired jupytext .py files are excluded from Python files.
        """
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
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths,
            keep_python_files=True,
            keep_jupyter_files=True,
            keep_markdown_files=False,
            skip_dassert_exists=True,
        )
        self.assertEqual(py_files, [standalone_py])
        self.assertEqual(ipynb_files, [notebook_ipynb])
        self.assertEqual(md_files, [])


# #############################################################################
# Test_run_linting_actions
# #############################################################################


class Test_run_linting_actions(hunitest.TestCase):
    """
    Test _run_linting_actions command dispatcher.
    """

    @umock.patch("helpers.hsystem.system")
    def test1(self, mock_system: umock.MagicMock) -> None:
        """
        All default actions — 3 calls to system for py files.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        files_str = "file1.py file2.py"
        # Run test.
        ret = lilint._run_linting_actions(
            files_str,
            abort_on_error=True,
            actions=None,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 3)
        calls = [call[0][0] for call in mock_system.call_args_list]
        self.assertIn("pre-commit run --files", calls[0])
        self.assertIn("normalize_import.py", calls[1])
        self.assertIn("add_class_frames.py", calls[2])
        for call_cmd in calls:
            self.assertIn("file1.py file2.py", call_cmd)

    @umock.patch("helpers.hsystem.system")
    def test2(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["pre-commit"] — exactly 1 call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        files_str = "file1.py"
        # Run test.
        ret = lilint._run_linting_actions(
            files_str,
            abort_on_error=True,
            actions=["pre-commit"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
        call_cmd = mock_system.call_args_list[0][0][0]
        self.assertIn("pre-commit run --files", call_cmd)

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["normalize_import", "add_class_frames"] — 2 calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        files_str = "file1.py"
        # Run test.
        ret = lilint._run_linting_actions(
            files_str,
            abort_on_error=True,
            actions=["normalize_import", "add_class_frames"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 2)
        calls = [call[0][0] for call in mock_system.call_args_list]
        self.assertIn("normalize_import.py", calls[0])
        self.assertIn("add_class_frames.py", calls[1])

    @umock.patch("helpers.hsystem.system")
    def test4(self, mock_system: umock.MagicMock) -> None:
        """
        mock_system returns non-zero — return code is OR-combined.
        """
        # Prepare inputs.
        mock_system.side_effect = [0, 1, 0]
        files_str = "file1.py"
        # Run test.
        ret = lilint._run_linting_actions(
            files_str,
            abort_on_error=True,
            actions=None,
        )
        # Check outputs.
        self.assertEqual(ret, 1)

    @umock.patch("helpers.hsystem.system")
    def test5(self, mock_system: umock.MagicMock) -> None:
        """
        actions=[] — zero calls, return 0.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        files_str = "file1.py"
        # Run test.
        ret = lilint._run_linting_actions(
            files_str,
            abort_on_error=True,
            actions=[],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 0)


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
        # Run test.
        ret = lilint._lint_python_files(
            file_paths,
            abort_on_error=True,
            actions=None,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 0)

    @umock.patch("helpers.hsystem.system")
    def test2(self, mock_system: umock.MagicMock) -> None:
        """
        Two .py files, default actions — 3 calls with filenames.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.py", "bar.py"]
        # Run test.
        ret = lilint._lint_python_files(
            file_paths,
            abort_on_error=True,
            actions=None,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 3)
        calls = [call[0][0] for call in mock_system.call_args_list]
        for call_cmd in calls:
            self.assertIn("foo.py", call_cmd)
            self.assertIn("bar.py", call_cmd)

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["normalize_import"] — exactly 1 call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.py"]
        # Run test.
        ret = lilint._lint_python_files(
            file_paths,
            abort_on_error=True,
            actions=["normalize_import"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
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
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            abort_on_error=True,
            actions=None,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 0)

    @umock.patch("helpers.hsystem.system")
    def test2(self, mock_system: umock.MagicMock) -> None:
        """
        Two notebooks, default actions — 3 shared calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            abort_on_error=True,
            actions=None,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 3)
        calls = [call[0][0] for call in mock_system.call_args_list]
        self.assertIn("pre-commit run --files", calls[0])
        self.assertIn("normalize_import.py", calls[1])
        self.assertIn("add_class_frames.py", calls[2])

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["sync_jupytext"] — 2 jupytext calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            abort_on_error=True,
            actions=["sync_jupytext"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 2)
        calls = [call[0][0] for call in mock_system.call_args_list]
        self.assertIn("jupytext --sync foo.ipynb", calls[0])
        self.assertIn("jupytext --sync bar.ipynb", calls[1])

    @umock.patch("helpers.hsystem.system")
    def test4(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["pre-commit"] — 1 shared call.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        # Run test.
        ret = lilint._lint_jupyter_files(
            file_paths,
            abort_on_error=True,
            actions=["pre-commit"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
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
        mock_find_file.return_value = "/fake/lint_txt.py"
        mock_system.return_value = 0
        file_paths = []
        # Run test.
        ret = lilint._lint_markdown_files(
            file_paths,
            abort_on_error=True,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 0)

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
        mock_find_file.return_value = "/fake/lint_txt.py"
        mock_system.return_value = 0
        file_paths = ["doc.md", "readme.md"]
        # Run test.
        ret = lilint._lint_markdown_files(
            file_paths,
            abort_on_error=True,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
        cmd = mock_system.call_args_list[0][0][0]
        self.assertIn("/fake/lint_txt.py", cmd)
        self.assertIn("--files", cmd)
        self.assertIn("doc.md", cmd)
        self.assertIn("readme.md", cmd)
