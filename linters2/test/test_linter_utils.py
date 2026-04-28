import os
from typing import Optional

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters2.linter_utils as llinutil


# #############################################################################
# Test_is_under_dir
# #############################################################################


class Test_is_under_dir(hunitest.TestCase):
    """
    Test the _is_under_dir helper function.
    """

    def helper(self, file_name: str, dir_name: str, expected: bool) -> None:
        """
        Test helper for _is_under_dir.

        :param file_name: File name to check
        :param dir_name: Directory name to check for
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil._is_under_dir(file_name, dir_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test when directory is present in path.
        """
        # Prepare inputs.
        file_name = "path/to/test/file.py"
        dir_name = "test"
        expected = True
        # Run test.
        self.helper(file_name, dir_name, expected)

    def test2(self) -> None:
        """
        Test when directory is not present in path.
        """
        # Prepare inputs.
        file_name = "path/to/file.py"
        dir_name = "test"
        expected = False
        # Run test.
        self.helper(file_name, dir_name, expected)

    def test3(self) -> None:
        """
        Test with tmp.scratch directory present.
        """
        # Prepare inputs.
        file_name = "path/to/tmp.scratch/file.py"
        dir_name = "tmp.scratch"
        expected = True
        # Run test.
        self.helper(file_name, dir_name, expected)

    def test4(self) -> None:
        """
        Test with single directory path.
        """
        # Prepare inputs.
        file_name = "test"
        dir_name = "test"
        expected = True
        # Run test.
        self.helper(file_name, dir_name, expected)


# #############################################################################
# Test_is_under_test_dir
# #############################################################################


class Test_is_under_test_dir(hunitest.TestCase):
    """
    Test detection of test directory in file paths.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_under_test_dir.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_under_test_dir(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test file under test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.py"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test file not under test directory.
        """
        # Prepare inputs.
        file_name = "helpers/module.py"
        expected = False
        # Run test.
        self.helper(file_name, expected)


# #############################################################################
# Test_is_under_tmp_scratch_dir
# #############################################################################


class Test_is_under_tmp_scratch_dir(hunitest.TestCase):
    """
    Test detection of tmp.scratch directory in file paths.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_under_tmp_scratch_dir.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_under_tmp_scratch_dir(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test file under tmp.scratch directory.
        """
        # Prepare inputs.
        file_name = "path/to/tmp.scratch/file.py"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test file not under tmp.scratch directory.
        """
        # Prepare inputs.
        file_name = "path/to/file.py"
        expected = False
        # Run test.
        self.helper(file_name, expected)


# #############################################################################
# Test_is_py_file
# #############################################################################


class Test_is_py_file(hunitest.TestCase):
    """
    Test detection of Python files.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_py_file.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_py_file(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with .py file.
        """
        # Prepare inputs.
        file_name = "module.py"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test with non-.py file.
        """
        # Prepare inputs.
        file_name = "module.txt"
        expected = False
        # Run test.
        self.helper(file_name, expected)

    def test3(self) -> None:
        """
        Test with path containing .py file.
        """
        # Prepare inputs.
        file_name = "path/to/module.py"
        expected = True
        # Run test.
        self.helper(file_name, expected)


# #############################################################################
# Test_is_ipynb_file
# #############################################################################


class Test_is_ipynb_file(hunitest.TestCase):
    """
    Test detection of Jupyter notebook files.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_ipynb_file.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_ipynb_file(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with .ipynb file.
        """
        # Prepare inputs.
        file_name = "notebook.ipynb"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test with non-.ipynb file.
        """
        # Prepare inputs.
        file_name = "notebook.py"
        expected = False
        # Run test.
        self.helper(file_name, expected)

    def test3(self) -> None:
        """
        Test with path containing .ipynb file.
        """
        # Prepare inputs.
        file_name = "path/to/notebook.ipynb"
        expected = True
        # Run test.
        self.helper(file_name, expected)


# #############################################################################
# Test_is_text_file
# #############################################################################


class Test_is_text_file(hunitest.TestCase):
    """
    Test detection of text files with various extensions.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_text_file.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_text_file(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with .csv file.
        """
        self.helper("data.csv", True)

    def test2(self) -> None:
        """
        Test with .json file.
        """
        self.helper("config.json", True)

    def test3(self) -> None:
        """
        Test with .tsv file.
        """
        self.helper("data.tsv", True)

    def test4(self) -> None:
        """
        Test with .txt file.
        """
        self.helper("readme.txt", True)

    def test5(self) -> None:
        """
        Test with non-text file extension.
        """
        self.helper("script.py", False)

    def test6(self) -> None:
        """
        Test with path containing text file.
        """
        self.helper("path/to/data.json", True)


# #############################################################################
# Test_is_init_py
# #############################################################################


class Test_is_init_py(hunitest.TestCase):
    """
    Test detection of __init__.py files.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_init_py.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_init_py(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with __init__.py file.
        """
        # Prepare inputs.
        file_name = "__init__.py"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test with path containing __init__.py.
        """
        # Prepare inputs.
        file_name = "package/__init__.py"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test3(self) -> None:
        """
        Test with non-__init__ file.
        """
        # Prepare inputs.
        file_name = "module.py"
        expected = False
        # Run test.
        self.helper(file_name, expected)


# #############################################################################
# Test_is_executable
# #############################################################################


class Test_is_executable(hunitest.TestCase):
    """
    Test detection of executable files.
    """

    def helper(self, file_path: str, permissions: int, expected: bool) -> None:
        """
        Test helper for is_executable.

        :param file_path: Path to the file
        :param permissions: File permissions to set
        :param expected: Expected result
        """
        # Run test.
        os.chmod(file_path, permissions)
        actual = llinutil.is_executable(file_path)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with executable file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        executable_file = os.path.join(scratch_dir, "script.sh")
        with open(executable_file, "w") as f:
            f.write("#!/bin/bash\necho 'hello'")
        permissions = 0o755
        expected = True
        # Run test.
        self.helper(executable_file, permissions, expected)

    def test2(self) -> None:
        """
        Test with non-executable file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        non_executable_file = os.path.join(scratch_dir, "script.py")
        with open(non_executable_file, "w") as f:
            f.write("print('hello')")
        permissions = 0o644
        expected = False
        # Run test.
        self.helper(non_executable_file, permissions, expected)


# #############################################################################
# Test_from_python_to_ipynb_file
# #############################################################################


class Test_from_python_to_ipynb_file(hunitest.TestCase):
    """
    Test conversion of Python file paths to Jupyter notebook paths.
    """

    def helper(self, file_name: str, expected: str) -> None:
        """
        Test helper for from_python_to_ipynb_file.

        :param file_name: Python file name to convert
        :param expected: Expected notebook file name
        """
        # Run test.
        actual = llinutil.from_python_to_ipynb_file(file_name)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test conversion with simple filename.
        """
        # Prepare inputs.
        file_name = "notebook.py"
        expected = "notebook.ipynb"
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test conversion with path.
        """
        # Prepare inputs.
        file_name = "path/to/notebook.py"
        expected = "path/to/notebook.ipynb"
        # Run test.
        self.helper(file_name, expected)

    def test3(self) -> None:
        """
        Test conversion with non-.py file raises assertion.
        """
        # Prepare inputs.
        file_name = "notebook.ipynb"
        # Run test and check output.
        with self.assertRaises(AssertionError):
            llinutil.from_python_to_ipynb_file(file_name)


# #############################################################################
# Test_from_ipynb_to_python_file
# #############################################################################


class Test_from_ipynb_to_python_file(hunitest.TestCase):
    """
    Test conversion of Jupyter notebook paths to Python file paths.
    """

    def helper(self, file_name: str, expected: str) -> None:
        """
        Test helper for from_ipynb_to_python_file.

        :param file_name: Notebook file name to convert
        :param expected: Expected Python file name
        """
        # Run test.
        actual = llinutil.from_ipynb_to_python_file(file_name)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test conversion with simple filename.
        """
        # Prepare inputs.
        file_name = "notebook.ipynb"
        expected = "notebook.py"
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test conversion with path.
        """
        # Prepare inputs.
        file_name = "path/to/notebook.ipynb"
        expected = "path/to/notebook.py"
        # Run test.
        self.helper(file_name, expected)

    def test3(self) -> None:
        """
        Test conversion with non-.ipynb file raises assertion.
        """
        # Prepare inputs.
        file_name = "notebook.py"
        # Run test and check output.
        with self.assertRaises(AssertionError):
            llinutil.from_ipynb_to_python_file(file_name)


# #############################################################################
# Test_is_paired_jupytext_file
# #############################################################################


class Test_is_paired_jupytext_file(hunitest.TestCase):
    """
    Test detection of paired jupytext files.
    """

    def helper(self, file_path: str, expected: bool) -> None:
        """
        Test helper for is_paired_jupytext_file.

        :param file_path: File path to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_paired_jupytext_file(file_path)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with paired .py and .ipynb files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        py_file = os.path.join(scratch_dir, "notebook.py")
        ipynb_file = os.path.join(scratch_dir, "notebook.ipynb")
        hio.to_file(py_file, "# code")
        hio.to_file(ipynb_file, "{}")
        expected = True
        # Run test.
        self.helper(py_file, expected)

    def test2(self) -> None:
        """
        Test with unpaired .py file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        py_file = os.path.join(scratch_dir, "script.py")
        hio.to_file(py_file, "# code")
        expected = False
        # Run test.
        self.helper(py_file, expected)

    def test3(self) -> None:
        """
        Test with paired .ipynb and .py files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = os.path.join(scratch_dir, "notebook.ipynb")
        py_file = os.path.join(scratch_dir, "notebook.py")
        hio.to_file(ipynb_file, "{}")
        hio.to_file(py_file, "# code")
        expected = True
        # Run test.
        self.helper(ipynb_file, expected)

    def test4(self) -> None:
        """
        Test with unpaired .ipynb file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = os.path.join(scratch_dir, "notebook.ipynb")
        hio.to_file(ipynb_file, "{}")
        expected = False
        # Run test.
        self.helper(ipynb_file, expected)


# #############################################################################
# Test_is_shebang
# #############################################################################


class Test_is_shebang(hunitest.TestCase):
    """
    Test detection of shebang lines.
    """

    def helper(self, line: str, expected: bool) -> None:
        """
        Test helper for is_shebang.

        :param line: Line to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_shebang(line)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with standard shebang.
        """
        # Prepare inputs.
        line = "#!/bin/bash"
        expected = True
        # Run test.
        self.helper(line, expected)

    def test2(self) -> None:
        """
        Test with Python shebang.
        """
        # Prepare inputs.
        line = "#!/usr/bin/env python"
        expected = True
        # Run test.
        self.helper(line, expected)

    def test3(self) -> None:
        """
        Test with comment that is not shebang.
        """
        # Prepare inputs.
        line = "# This is a comment"
        expected = False
        # Run test.
        self.helper(line, expected)

    def test4(self) -> None:
        """
        Test with code line.
        """
        # Prepare inputs.
        line = "x = 5"
        expected = False
        # Run test.
        self.helper(line, expected)


# #############################################################################
# Test_is_comment
# #############################################################################


class Test_is_comment(hunitest.TestCase):
    """
    Test detection of comment lines.
    """

    def helper(self, line: str, expected: bool) -> None:
        """
        Test helper for is_comment.

        :param line: Line to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_comment(line)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with simple comment.
        """
        # Prepare inputs.
        line = "# This is a comment"
        expected = True
        # Run test.
        self.helper(line, expected)

    def test2(self) -> None:
        """
        Test with indented comment.
        """
        # Prepare inputs.
        line = "    # Indented comment"
        expected = True
        # Run test.
        self.helper(line, expected)

    def test3(self) -> None:
        """
        Test with shebang is not a comment.
        """
        # Prepare inputs.
        line = "#!/usr/bin/env python"
        expected = False
        # Run test.
        self.helper(line, expected)

    def test4(self) -> None:
        """
        Test with code line.
        """
        # Prepare inputs.
        line = "x = 5"
        expected = False
        # Run test.
        self.helper(line, expected)


# #############################################################################
# Test_is_separator
# #############################################################################


class Test_is_separator(hunitest.TestCase):
    """
    Test detection of separator lines.
    """

    def helper(self, line: str, expected: bool) -> None:
        """
        Test helper for is_separator.

        :param line: Line to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_separator(line)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with exact separator.
        """
        # Prepare inputs.
        line = "# #############################################################################"
        expected = True
        # Run test.
        self.helper(line, expected)

    def test2(self) -> None:
        """
        Test with similar but not exact separator.
        """
        # Prepare inputs.
        line = "# ##############################################################################"
        expected = False
        # Run test.
        self.helper(line, expected)

    def test3(self) -> None:
        """
        Test with comment line.
        """
        # Prepare inputs.
        line = "# This is a comment"
        expected = False
        # Run test.
        self.helper(line, expected)


# #############################################################################
# Test_parse_comment
# #############################################################################


class Test_parse_comment(hunitest.TestCase):
    """
    Test parsing of comment lines with regex.
    """

    def helper(self, line: str, expected_group2: Optional[str]) -> None:
        """
        Test helper for parse_comment.

        :param line: Line to parse
        :param expected_group2: Expected value from group(2), or None if no match
        """
        # Run test.
        actual = llinutil.parse_comment(line)
        # Check outputs.
        if expected_group2 is None:
            self.assertIsNone(actual)
        else:
            self.assertIsNotNone(actual)
            self.assertEqual(actual.group(2), expected_group2)

    def test1(self) -> None:
        """
        Test parsing simple comment.
        """
        # Prepare inputs.
        line = "# This is a comment"
        expected_group2 = "This is a comment"
        # Run test.
        self.helper(line, expected_group2)

    def test2(self) -> None:
        """
        Test parsing indented comment.
        """
        # Prepare inputs.
        line = "    # Indented comment"
        expected_group2 = "Indented comment"
        # Run test.
        self.helper(line, expected_group2)

    def test3(self) -> None:
        """
        Test that separator returns None.
        """
        # Prepare inputs.
        line = "# #############################################################################"
        expected_group2 = None
        # Run test.
        self.helper(line, expected_group2)

    def test4(self) -> None:
        """
        Test that shebang returns None.
        """
        # Prepare inputs.
        line = "#!/usr/bin/env python"
        expected_group2 = None
        # Run test.
        self.helper(line, expected_group2)

    def test5(self) -> None:
        """
        Test parsing with custom regex.
        """
        # Prepare inputs.
        line = "# TODO(gp): Fix this"
        regex = r"(^\s*)#\s*(TODO\([^)]+\):\s*.*)"
        # Run test.
        actual = llinutil.parse_comment(line, regex)
        # Check outputs.
        self.assertIsNotNone(actual)
        assert actual is not None
        self.assertIn("TODO(gp):", actual.group(2))


# #############################################################################
# Test_is_test_code
# #############################################################################


class Test_is_test_code(hunitest.TestCase):
    """
    Test detection of unit test code files.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_test_code.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_test_code(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with test file in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.py"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test with file not in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/module.py"
        expected = False
        # Run test.
        self.helper(file_name, expected)

    def test3(self) -> None:
        """
        Test with test file not starting with test_.
        """
        # Prepare inputs.
        file_name = "helpers/test/module_test.py"
        expected = False
        # Run test.
        self.helper(file_name, expected)

    def test4(self) -> None:
        """
        Test with test file that is not Python.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.txt"
        expected = False
        # Run test.
        self.helper(file_name, expected)


# #############################################################################
# Test_is_test_input_output_file
# #############################################################################


class Test_is_test_input_output_file(hunitest.TestCase):
    """
    Test detection of test input/output files.
    """

    def helper(self, file_name: str, expected: bool) -> None:
        """
        Test helper for is_test_input_output_file.

        :param file_name: File name to check
        :param expected: Expected result
        """
        # Run test.
        actual = llinutil.is_test_input_output_file(file_name)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test with .txt file in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/outcomes/output.txt"
        expected = True
        # Run test.
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Test with .py file in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.py"
        expected = False
        # Run test.
        self.helper(file_name, expected)

    def test3(self) -> None:
        """
        Test with .txt file not in test directory.
        """
        # Prepare inputs.
        file_name = "output.txt"
        expected = False
        # Run test.
        self.helper(file_name, expected)

    def test4(self) -> None:
        """
        Test with .txt file in tmp.scratch test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/tmp.scratch/output.txt"
        expected = False
        # Run test.
        self.helper(file_name, expected)


# #############################################################################
# Test_filter_files_by_type
# #############################################################################


class Test_filter_files_by_type(hunitest.TestCase):
    """
    Test filtering files by type using extension list.
    """

    def helper(
        self,
        extensions: list,
        expected_py_count: int,
        expected_jupyter_count: int,
        expected_md_count: int,
        expected_md_files: Optional[list] = None,
    ) -> None:
        """
        Test helper for filter_files_by_type.

        :param extensions: List of extensions to filter by
        :param expected_py_count: Expected count of Python files
        :param expected_jupyter_count: Expected count of Jupyter files
        :param expected_md_count: Expected count of Markdown files
        :param expected_md_files: Expected list of Markdown files (optional)
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        py_file = os.path.join(scratch_dir, "script.py")
        ipynb_file = os.path.join(scratch_dir, "notebook.ipynb")
        md_file = os.path.join(scratch_dir, "readme.md")
        txt_file = os.path.join(scratch_dir, "data.txt")
        # Create files based on what's needed.
        hio.to_file(py_file, "print('hello')")
        hio.to_file(ipynb_file, "{}")
        hio.to_file(md_file, "# Header")
        hio.to_file(txt_file, "some text")
        file_paths = [py_file, ipynb_file, md_file, txt_file]
        # Run test.
        py_files, jupyter_files, md_files = llinutil.filter_files_by_type(
            file_paths, extensions, skip_dassert_exists=True
        )
        # Check outputs.
        self.assertEqual(len(py_files), expected_py_count)
        self.assertEqual(len(jupyter_files), expected_jupyter_count)
        self.assertEqual(len(md_files), expected_md_count)
        if expected_md_files is not None:
            self.assertEqual(md_files, expected_md_files)

    def test1(self) -> None:
        """
        Test filtering with only Python extension.
        """
        # Prepare outputs.
        extensions = ["py"]
        expected_py_count = 1
        expected_jupyter_count = 0
        expected_md_count = 0
        # Run test.
        self.helper(
            extensions,
            expected_py_count,
            expected_jupyter_count,
            expected_md_count,
        )

    def test2(self) -> None:
        """
        Test filtering with only Jupyter extension.
        """
        # Prepare outputs.
        extensions = ["ipynb"]
        expected_py_count = 0
        expected_jupyter_count = 1
        expected_md_count = 0
        # Run test.
        self.helper(
            extensions,
            expected_py_count,
            expected_jupyter_count,
            expected_md_count,
        )

    def test3(self) -> None:
        """
        Test filtering with only Markdown extension.
        """
        # Prepare outputs.
        extensions = ["md"]
        expected_py_count = 0
        expected_jupyter_count = 0
        expected_md_count = 1
        # Run test.
        self.helper(
            extensions,
            expected_py_count,
            expected_jupyter_count,
            expected_md_count,
        )

    def test4(self) -> None:
        """
        Test filtering with text extension.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        py_file = os.path.join(scratch_dir, "script.py")
        txt_file = os.path.join(scratch_dir, "data.txt")
        # Create files.
        hio.to_file(py_file, "print('hello')")
        hio.to_file(txt_file, "some text")
        file_paths = [py_file, txt_file]
        # Prepare outputs.
        extensions = ["txt"]
        expected_md_files = [txt_file]
        # Run test.
        py_files, jupyter_files, md_files = llinutil.filter_files_by_type(
            file_paths, extensions, skip_dassert_exists=True
        )
        # Check outputs.
        self.assertEqual(len(py_files), 0)
        self.assertEqual(len(jupyter_files), 0)
        self.assertEqual(len(md_files), 1)
        self.assertEqual(md_files[0], txt_file)

    def test5(self) -> None:
        """
        Test filtering with multiple extensions.
        """
        # Prepare outputs.
        extensions = ["py", "ipynb", "md", "txt"]
        expected_py_count = 1
        expected_jupyter_count = 1
        expected_md_count = 2
        # Run test.
        self.helper(
            extensions,
            expected_py_count,
            expected_jupyter_count,
            expected_md_count,
        )

    def test6(self) -> None:
        """
        Test filtering with empty extension list returns no files.
        """
        # Prepare outputs.
        extensions = []
        expected_py_count = 0
        expected_jupyter_count = 0
        expected_md_count = 0
        # Run test.
        self.helper(
            extensions,
            expected_py_count,
            expected_jupyter_count,
            expected_md_count,
        )
