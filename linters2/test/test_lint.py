import unittest.mock as umock

import helpers.hunit_test as hunitest
import linters2.lint as llint


class Test_filter_files_by_type(hunitest.TestCase):
    """
    Test _filter_files_by_type file categorization logic.
    """

    @umock.patch("linters2.linter_utils.is_paired_jupytext_file")
    def test1(self, mock_is_paired: umock.MagicMock) -> None:
        """
        No type filters — auto-detects extensions correctly.
        """
        # Prepare inputs.
        mock_is_paired.return_value = False
        file_paths = ["foo.py", "bar.ipynb", "baz.md", "qux.txt"]
        # Run test.
        py_files, ipynb_files, md_files = llint._filter_files_by_type(
            file_paths,
            py=False,
            ipynb=False,
            md=False,
        )
        # Check outputs.
        self.assertEqual(py_files, ["foo.py"])
        self.assertEqual(ipynb_files, ["bar.ipynb"])
        self.assertEqual(md_files, ["baz.md"])

    @umock.patch("linters2.linter_utils.is_paired_jupytext_file")
    def test2(self, mock_is_paired: umock.MagicMock) -> None:
        """
        py=True filter — only .py files included.
        """
        # Prepare inputs.
        mock_is_paired.return_value = False
        file_paths = ["foo.py", "bar.ipynb", "baz.md"]
        # Run test.
        py_files, ipynb_files, md_files = llint._filter_files_by_type(
            file_paths,
            py=True,
            ipynb=False,
            md=False,
        )
        # Check outputs.
        self.assertEqual(py_files, ["foo.py"])
        self.assertEqual(ipynb_files, [])
        self.assertEqual(md_files, [])

    @umock.patch("linters2.linter_utils.is_paired_jupytext_file")
    def test3(self, mock_is_paired: umock.MagicMock) -> None:
        """
        ipynb=True filter — only .ipynb files included.
        """
        # Prepare inputs.
        mock_is_paired.return_value = False
        file_paths = ["foo.py", "bar.ipynb", "baz.md"]
        # Run test.
        py_files, ipynb_files, md_files = llint._filter_files_by_type(
            file_paths,
            py=False,
            ipynb=True,
            md=False,
        )
        # Check outputs.
        self.assertEqual(py_files, [])
        self.assertEqual(ipynb_files, ["bar.ipynb"])
        self.assertEqual(md_files, [])

    @umock.patch("linters2.linter_utils.is_paired_jupytext_file")
    def test4(self, mock_is_paired: umock.MagicMock) -> None:
        """
        md=True filter — only .md files included.
        """
        # Prepare inputs.
        mock_is_paired.return_value = False
        file_paths = ["foo.py", "bar.ipynb", "baz.md"]
        # Run test.
        py_files, ipynb_files, md_files = llint._filter_files_by_type(
            file_paths,
            py=False,
            ipynb=False,
            md=True,
        )
        # Check outputs.
        self.assertEqual(py_files, [])
        self.assertEqual(ipynb_files, [])
        self.assertEqual(md_files, ["baz.md"])

    @umock.patch("linters2.linter_utils.is_paired_jupytext_file")
    def test5(self, mock_is_paired: umock.MagicMock) -> None:
        """
        Paired jupytext .py files are excluded from Python files.
        """
        # Prepare inputs.
        mock_is_paired.side_effect = lambda f: f == "paired.py"
        file_paths = ["standalone.py", "paired.py", "notebook.ipynb"]
        # Run test.
        py_files, ipynb_files, md_files = llint._filter_files_by_type(
            file_paths,
            py=False,
            ipynb=False,
            md=False,
        )
        # Check outputs.
        self.assertEqual(py_files, ["standalone.py"])
        self.assertEqual(ipynb_files, ["notebook.ipynb"])
        self.assertEqual(md_files, [])


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
        ret = llint._run_linting_actions(
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
        ret = llint._run_linting_actions(
            files_str,
            abort_on_error=True,
            actions=["pre-commit"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
        self.assertIn("pre-commit run --files", mock_system.call_args_list[0][0][0])

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["normalize_import", "add_class_frames"] — exactly 2 calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        files_str = "file1.py"
        # Run test.
        ret = llint._run_linting_actions(
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
        ret = llint._run_linting_actions(
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
        ret = llint._run_linting_actions(
            files_str,
            abort_on_error=True,
            actions=[],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 0)


class Test_lint_python(hunitest.TestCase):
    """
    Test _lint_python Python file linting.
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
        ret = llint._lint_python(
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
        Two .py files, default actions — 3 calls with filenames in commands.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.py", "bar.py"]
        # Run test.
        ret = llint._lint_python(
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
        ret = llint._lint_python(
            file_paths,
            abort_on_error=True,
            actions=["normalize_import"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
        self.assertIn("normalize_import.py", mock_system.call_args_list[0][0][0])


class Test_lint_jupyter(hunitest.TestCase):
    """
    Test _lint_jupyter Jupyter notebook linting.
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
        ret = llint._lint_jupyter(
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
        Two notebooks, default actions — 3 shared calls + 2 jupytext calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        # Run test.
        ret = llint._lint_jupyter(
            file_paths,
            abort_on_error=True,
            actions=None,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 5)
        calls = [call[0][0] for call in mock_system.call_args_list]
        self.assertIn("pre-commit run --files", calls[0])
        self.assertIn("normalize_import.py", calls[1])
        self.assertIn("add_class_frames.py", calls[2])
        self.assertIn("jupytext --sync foo.ipynb", calls[3])
        self.assertIn("jupytext --sync bar.ipynb", calls[4])

    @umock.patch("helpers.hsystem.system")
    def test3(self, mock_system: umock.MagicMock) -> None:
        """
        actions=["sync_jupytext"] — 0 shared calls + 2 jupytext calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        # Run test.
        ret = llint._lint_jupyter(
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
        actions=["pre-commit"] — 1 shared call, 0 jupytext calls.
        """
        # Prepare inputs.
        mock_system.return_value = 0
        file_paths = ["foo.ipynb", "bar.ipynb"]
        # Run test.
        ret = llint._lint_jupyter(
            file_paths,
            abort_on_error=True,
            actions=["pre-commit"],
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
        self.assertIn("pre-commit run --files", mock_system.call_args_list[0][0][0])


class Test_lint_markdown(hunitest.TestCase):
    """
    Test _lint_markdown Markdown file linting.
    """

    @umock.patch("helpers.hsystem.system")
    @umock.patch("helpers.hsystem.find_file_in_repo")
    def test1(self, mock_find_file: umock.MagicMock, mock_system: umock.MagicMock) -> None:
        """
        Empty file list — returns 0 immediately, no calls.
        """
        # Prepare inputs.
        mock_find_file.return_value = "/fake/lint_txt.py"
        mock_system.return_value = 0
        file_paths = []
        # Run test.
        ret = llint._lint_markdown(
            file_paths,
            abort_on_error=True,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 0)

    @umock.patch("helpers.hsystem.system")
    @umock.patch("helpers.hsystem.find_file_in_repo")
    def test2(self, mock_find_file: umock.MagicMock, mock_system: umock.MagicMock) -> None:
        """
        Two .md files — 1 call to lint_txt.py with filenames.
        """
        # Prepare inputs.
        mock_find_file.return_value = "/fake/lint_txt.py"
        mock_system.return_value = 0
        file_paths = ["doc.md", "readme.md"]
        # Run test.
        ret = llint._lint_markdown(
            file_paths,
            abort_on_error=True,
        )
        # Check outputs.
        self.assertEqual(ret, 0)
        self.assertEqual(mock_system.call_count, 1)
        cmd = mock_system.call_args_list[0][0][0]
        self.assertIn("/fake/lint_txt.py", cmd)
        self.assertIn("-i", cmd)
        self.assertIn("doc.md", cmd)
        self.assertIn("readme.md", cmd)
