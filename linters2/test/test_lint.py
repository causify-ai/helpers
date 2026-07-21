import os
import unittest.mock as umock
from typing import Dict, List, Optional, Tuple

import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import linters2.lint as lilint


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

    def _setup_jupytext_test_files(
        self,
    ) -> Tuple[str, str, str, str, List[str], List[str]]:
        """
        Create paired and standalone jupytext-compatible test files.

        Returns: (standalone_py, paired_py, paired_ipynb, notebook_ipynb,
        file_paths, file_types)
        """
        scratch_dir = self.get_scratch_space()
        #
        standalone_py = os.path.join(scratch_dir, "standalone.py")
        hio.to_file(standalone_py, "")
        #
        paired_py = os.path.join(scratch_dir, "paired.py")
        hio.to_file(paired_py, "")
        #
        paired_ipynb = os.path.join(scratch_dir, "paired.ipynb")
        hio.to_file(paired_ipynb, "")
        #
        notebook_ipynb = os.path.join(scratch_dir, "notebook.ipynb")
        hio.to_file(notebook_ipynb, "")
        file_paths = [standalone_py, paired_py, notebook_ipynb]
        file_types = ["py", "ipynb"]
        return standalone_py, paired_py, paired_ipynb, notebook_ipynb, file_paths, file_types

    def _assert_filter_results(
        self,
        actual_py: List[str],
        actual_ipynb: List[str],
        actual_md: List[str],
        expected_py: List[str],
        expected_ipynb: List[str],
        expected_md: List[str],
        *,
        sort_py: bool = False,
    ) -> None:
        """Assert filter results match expectations."""
        if sort_py:
            self.assertEqual(sorted(actual_py), sorted(expected_py))
        else:
            self.assertEqual(actual_py, expected_py)
        self.assertEqual(actual_ipynb, expected_ipynb)
        self.assertEqual(actual_md, expected_md)

    def _run_and_check_filter(
        self,
        file_paths: List[str],
        file_types: List[str],
        expected_py: List[str],
        expected_ipynb: List[str],
        expected_md: List[str],
        *,
        exclude_paired_jupytext: Optional[bool] = None,
        sort_py: bool = False,
    ) -> None:
        """Run _filter_files_by_type and check results."""
        kwargs = {"skip_dassert_exists": True}
        if exclude_paired_jupytext is not None:
            kwargs["exclude_paired_jupytext"] = exclude_paired_jupytext
        py_files, ipynb_files, md_files = lilint._filter_files_by_type(
            file_paths, file_types, **kwargs
        )
        self._assert_filter_results(
            py_files,
            ipynb_files,
            md_files,
            expected_py,
            expected_ipynb,
            expected_md,
            sort_py=sort_py,
        )

    def test1(self) -> None:
        """
        Default filters: py,ipynb extensions.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md", "qux.txt"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
            paths["qux.txt"],
        ]
        self._run_and_check_filter(
            file_paths,
            ["py", "ipynb"],
            [paths["foo.py"]],
            [paths["bar.ipynb"]],
            [],
        )

    def test2(self) -> None:
        """
        py extension only: only .py files included.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        self._run_and_check_filter(
            file_paths,
            ["py"],
            [paths["foo.py"]],
            [],
            [],
        )

    def test3(self) -> None:
        """
        ipynb extension only: only .ipynb files included.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        self._run_and_check_filter(
            file_paths,
            ["ipynb"],
            [],
            [paths["bar.ipynb"]],
            [],
        )

    def test4(self) -> None:
        """
        md extension only: only .md files included.
        """
        paths = self._create_files(["foo.py", "bar.ipynb", "baz.md"])
        file_paths = [
            paths["foo.py"],
            paths["bar.ipynb"],
            paths["baz.md"],
        ]
        self._run_and_check_filter(
            file_paths,
            ["md"],
            [],
            [],
            [paths["baz.md"]],
        )

    def test5(self) -> None:
        """
        Paired jupytext .py files excluded by default.
        """
        standalone_py, _, _, notebook_ipynb, file_paths, file_types = (
            self._setup_jupytext_test_files()
        )
        self._run_and_check_filter(
            file_paths,
            file_types,
            [standalone_py],
            [notebook_ipynb],
            [],
            exclude_paired_jupytext=True,
        )

    def test6(self) -> None:
        """
        With exclude_paired_jupytext=False, paired .py files included.
        """
        standalone_py, paired_py, _, notebook_ipynb, file_paths, file_types = (
            self._setup_jupytext_test_files()
        )
        self._run_and_check_filter(
            file_paths,
            file_types,
            [standalone_py, paired_py],
            [notebook_ipynb],
            [],
            exclude_paired_jupytext=False,
            sort_py=True,
        )


# #############################################################################
# Test_run_common_linting_actions
# #############################################################################


class Test_run_common_linting_actions(hunitest.TestCase):
    """
    Test _run_common_linting_actions action runner.
    """

    def test1(self) -> None:
        """
        actions=["pre-commit"]: exactly 1 call.
        """
        # Prepare inputs.
        file_paths = ["file1.py", "file2.py"]
        actions = ["pre-commit"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("pre-commit run --files file1.py file2.py --color always",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            }
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._run_common_linting_actions(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test2(self) -> None:
        """
        Empty actions: zero calls, return 0.
        """
        # Prepare inputs.
        file_paths = ["file1.py"]
        actions = []
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = []
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._run_common_linting_actions(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)


# #############################################################################
# Test_run_python_linting_actions
# #############################################################################


class Test_run_python_linting_actions(hunitest.TestCase):
    """
    Test _run_python_linting_actions action runner for Python files.
    """

    def test1(self) -> None:
        """
        actions=["normalize_import"]: exactly 1 call.
        """
        # Prepare inputs.
        file_paths = ["file1.py"]
        actions = ["normalize_import"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("linters2/normalize_import.py --no_report_command_line file1.py",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            }
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._run_python_linting_actions(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test2(self) -> None:
        """
        actions=["normalize_import", "add_class_frames"]: 2 calls.
        """
        # Prepare inputs.
        file_paths = ["file1.py"]
        actions = ["normalize_import", "add_class_frames"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("linters2/normalize_import.py --no_report_command_line file1.py",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
            {
                "function": "hsystem.system",
                "args": ("linters2/add_class_frames.py --no_report_command_line file1.py",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._run_python_linting_actions(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test3(self) -> None:
        """
        mock_system returns non-zero: return code is OR-combined.
        """
        # Prepare inputs.
        file_paths = ["file1.py"]
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 1
        # Run test.
        with hunteuti.capture_sys_calls(side_effect=[0, 1, 0, 0]) as sys_calls:
            ret = lilint._run_python_linting_actions(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)

    def test4(self) -> None:
        """
        Empty actions: zero calls, return 0.
        """
        # Prepare inputs.
        file_paths = ["file1.py"]
        actions = []
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = []
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._run_python_linting_actions(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)


# #############################################################################
# Test_lint_python_files
# #############################################################################


class Test_lint_python_files(hunitest.TestCase):
    """
    Test _lint_python_files Python file linting.
    """

    def test1(self) -> None:
        """
        Empty file list: returns 0 immediately, no calls.
        """
        # Prepare inputs.
        file_paths = []
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = []
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_python_files(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test2(self) -> None:
        """
        Two .py files, default actions: 4 calls with filenames.
        """
        # Prepare inputs.
        file_paths = ["foo.py", "bar.py"]
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("pre-commit run --files foo.py bar.py --color always",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
            {
                "function": "hsystem.system",
                "args": ("linters2/normalize_import.py --no_report_command_line foo.py bar.py",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
            {
                "function": "hsystem.system",
                "args": ("linters2/add_class_frames.py --no_report_command_line foo.py bar.py",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
            {
                "function": "hsystem.system",
                "args": ("linters2/fix_comments.py --no_report_command_line foo.py bar.py",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_python_files(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test3(self) -> None:
        """
        actions=["normalize_import"]: exactly 1 call.
        """
        # Prepare inputs.
        file_paths = ["foo.py"]
        actions = ["normalize_import"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("linters2/normalize_import.py --no_report_command_line foo.py",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_python_files(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)


# #############################################################################
# Test_lint_jupyter_files
# #############################################################################


class Test_lint_jupyter_files(hunitest.TestCase):
    """
    Test _lint_jupyter_files Jupyter notebook linting.
    """

    def test1(self) -> None:
        """
        Empty file list: returns 0 immediately, no calls.
        """
        # Prepare inputs.
        file_paths = []
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = []
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_jupyter_files(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test2(self) -> None:
        """
        Two notebooks, default actions: 1 shared pre-commit call.
        """
        # Prepare inputs.
        file_paths = ["foo.ipynb", "bar.ipynb"]
        actions = lilint._DEFAULT_ACTIONS
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("pre-commit run --files foo.ipynb bar.ipynb --color always",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_jupyter_files(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test3(self) -> None:
        """
        actions=["sync_jupytext"]: 2 jupytext calls.
        """
        # Prepare inputs.
        file_paths = ["foo.ipynb", "bar.ipynb"]
        actions = ["sync_jupytext"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("jupytext --sync foo.ipynb",),
                "kwargs": {
                    "print_command": True,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
            {
                "function": "hsystem.system",
                "args": ("jupytext --sync bar.ipynb",),
                "kwargs": {
                    "print_command": True,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_jupyter_files(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test4(self) -> None:
        """
        actions=["pre-commit"]: 1 shared call.
        """
        # Prepare inputs.
        file_paths = ["foo.ipynb", "bar.ipynb"]
        actions = ["pre-commit"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("pre-commit run --files foo.ipynb bar.ipynb --color always",),
                "kwargs": {
                    "print_command": False,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_jupyter_files(
                file_paths,
                actions,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)


# #############################################################################
# Test_lint_markdown_files
# #############################################################################


class Test_lint_markdown_files(hunitest.TestCase):
    """
    Test _lint_markdown_files Markdown file linting.
    """

    @umock.patch("helpers.hsystem.find_file_in_repo")
    def test1(
        self,
        mock_find_file: umock.MagicMock,
    ) -> None:
        """
        Empty file list: returns 0 immediately, no calls.
        """
        # Prepare inputs.
        lint_script_path = "/fake/lint_txt.py"
        mock_find_file.return_value = lint_script_path
        file_paths = []
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = []
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_markdown_files(
                file_paths,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    @umock.patch("helpers.hsystem.find_file_in_repo")
    def test2(
        self,
        mock_find_file: umock.MagicMock,
    ) -> None:
        """
        Two .md files: 1 call to lint_txt.py with filenames.
        """
        # Prepare inputs.
        lint_script_path = "/fake/lint_txt.py"
        mock_find_file.return_value = lint_script_path
        file_paths = ["doc.md", "readme.md"]
        abort_on_error = True
        # Prepare outputs.
        expected_return_code = 0
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": ("/fake/lint_txt.py --input_files doc.md readme.md",),
                "kwargs": {
                    "print_command": True,
                    "abort_on_error": True,
                    "suppress_output": False,
                },
            },
        ]
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            ret = lilint._lint_markdown_files(
                file_paths,
                abort_on_error=abort_on_error,
            )
        # Check outputs.
        self.assertEqual(ret, expected_return_code)
        expected_str = hunteuti.sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)
