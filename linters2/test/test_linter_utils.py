import os

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

    def test1(self) -> None:
        """
        Test when directory is present in path.
        """
        # Prepare inputs.
        file_name = "path/to/test/file.py"
        dir_name = "test"
        # Run test.
        actual = llinutil._is_under_dir(file_name, dir_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test when directory is not present in path.
        """
        # Prepare inputs.
        file_name = "path/to/file.py"
        dir_name = "test"
        # Run test.
        actual = llinutil._is_under_dir(file_name, dir_name)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test with tmp.scratch directory present.
        """
        # Prepare inputs.
        file_name = "path/to/tmp.scratch/file.py"
        dir_name = "tmp.scratch"
        # Run test.
        actual = llinutil._is_under_dir(file_name, dir_name)
        # Check outputs.
        self.assertTrue(actual)

    def test4(self) -> None:
        """
        Test with single directory path.
        """
        # Prepare inputs.
        file_name = "test"
        dir_name = "test"
        # Run test.
        actual = llinutil._is_under_dir(file_name, dir_name)
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# Test_is_under_test_dir
# #############################################################################


class Test_is_under_test_dir(hunitest.TestCase):
    """
    Test detection of test directory in file paths.
    """

    def test1(self) -> None:
        """
        Test file under test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.py"
        # Run test.
        actual = llinutil.is_under_test_dir(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test file not under test directory.
        """
        # Prepare inputs.
        file_name = "helpers/module.py"
        # Run test.
        actual = llinutil.is_under_test_dir(file_name)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_is_under_tmp_scratch_dir
# #############################################################################


class Test_is_under_tmp_scratch_dir(hunitest.TestCase):
    """
    Test detection of tmp.scratch directory in file paths.
    """

    def test1(self) -> None:
        """
        Test file under tmp.scratch directory.
        """
        # Prepare inputs.
        file_name = "path/to/tmp.scratch/file.py"
        # Run test.
        actual = llinutil.is_under_tmp_scratch_dir(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test file not under tmp.scratch directory.
        """
        # Prepare inputs.
        file_name = "path/to/file.py"
        # Run test.
        actual = llinutil.is_under_tmp_scratch_dir(file_name)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_is_py_file
# #############################################################################


class Test_is_py_file(hunitest.TestCase):
    """
    Test detection of Python files.
    """

    def test1(self) -> None:
        """
        Test with .py file.
        """
        # Prepare inputs.
        file_name = "module.py"
        # Run test.
        actual = llinutil.is_py_file(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with non-.py file.
        """
        # Prepare inputs.
        file_name = "module.txt"
        # Run test.
        actual = llinutil.is_py_file(file_name)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test with path containing .py file.
        """
        # Prepare inputs.
        file_name = "path/to/module.py"
        # Run test.
        actual = llinutil.is_py_file(file_name)
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# Test_is_ipynb_file
# #############################################################################


class Test_is_ipynb_file(hunitest.TestCase):
    """
    Test detection of Jupyter notebook files.
    """

    def test1(self) -> None:
        """
        Test with .ipynb file.
        """
        # Prepare inputs.
        file_name = "notebook.ipynb"
        # Run test.
        actual = llinutil.is_ipynb_file(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with non-.ipynb file.
        """
        # Prepare inputs.
        file_name = "notebook.py"
        # Run test.
        actual = llinutil.is_ipynb_file(file_name)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test with path containing .ipynb file.
        """
        # Prepare inputs.
        file_name = "path/to/notebook.ipynb"
        # Run test.
        actual = llinutil.is_ipynb_file(file_name)
        # Check outputs.
        self.assertTrue(actual)


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

    def test1(self) -> None:
        """
        Test with __init__.py file.
        """
        # Prepare inputs.
        file_name = "__init__.py"
        # Run test.
        actual = llinutil.is_init_py(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with path containing __init__.py.
        """
        # Prepare inputs.
        file_name = "package/__init__.py"
        # Run test.
        actual = llinutil.is_init_py(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test3(self) -> None:
        """
        Test with non-__init__ file.
        """
        # Prepare inputs.
        file_name = "module.py"
        # Run test.
        actual = llinutil.is_init_py(file_name)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_is_executable
# #############################################################################


class Test_is_executable(hunitest.TestCase):
    """
    Test detection of executable files.
    """

    def test1(self) -> None:
        """
        Test with executable file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        executable_file = os.path.join(scratch_dir, "script.sh")
        with open(executable_file, "w") as f:
            f.write("#!/bin/bash\necho 'hello'")
        os.chmod(executable_file, 0o755)
        # Run test.
        actual = llinutil.is_executable(executable_file)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with non-executable file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        non_executable_file = os.path.join(scratch_dir, "script.py")
        with open(non_executable_file, "w") as f:
            f.write("print('hello')")
        os.chmod(non_executable_file, 0o644)
        # Run test.
        actual = llinutil.is_executable(non_executable_file)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_from_python_to_ipynb_file
# #############################################################################


class Test_from_python_to_ipynb_file(hunitest.TestCase):
    """
    Test conversion of Python file paths to Jupyter notebook paths.
    """

    def test1(self) -> None:
        """
        Test conversion with simple filename.
        """
        # Prepare inputs.
        file_name = "notebook.py"
        # Prepare outputs.
        expected = "notebook.ipynb"
        # Run test.
        actual = llinutil.from_python_to_ipynb_file(file_name)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test conversion with path.
        """
        # Prepare inputs.
        file_name = "path/to/notebook.py"
        # Prepare outputs.
        expected = "path/to/notebook.ipynb"
        # Run test.
        actual = llinutil.from_python_to_ipynb_file(file_name)
        # Check outputs.
        self.assert_equal(actual, expected)

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

    def test1(self) -> None:
        """
        Test conversion with simple filename.
        """
        # Prepare inputs.
        file_name = "notebook.ipynb"
        # Prepare outputs.
        expected = "notebook.py"
        # Run test.
        actual = llinutil.from_ipynb_to_python_file(file_name)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test conversion with path.
        """
        # Prepare inputs.
        file_name = "path/to/notebook.ipynb"
        # Prepare outputs.
        expected = "path/to/notebook.py"
        # Run test.
        actual = llinutil.from_ipynb_to_python_file(file_name)
        # Check outputs.
        self.assert_equal(actual, expected)

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

    def test1(self) -> None:
        """
        Test with paired .py and .ipynb files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        py_file = os.path.join(scratch_dir, "notebook.py")
        ipynb_file = os.path.join(scratch_dir, "notebook.ipynb")
        # Create both files.
        hio.to_file(py_file, "# code")
        hio.to_file(ipynb_file, "{}")
        # Run test.
        actual = llinutil.is_paired_jupytext_file(py_file)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with unpaired .py file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        py_file = os.path.join(scratch_dir, "script.py")
        # Create only .py file.
        hio.to_file(py_file, "# code")
        # Run test.
        actual = llinutil.is_paired_jupytext_file(py_file)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test with paired .ipynb and .py files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = os.path.join(scratch_dir, "notebook.ipynb")
        py_file = os.path.join(scratch_dir, "notebook.py")
        # Create both files.
        hio.to_file(ipynb_file, "{}")
        hio.to_file(py_file, "# code")
        # Run test.
        actual = llinutil.is_paired_jupytext_file(ipynb_file)
        # Check outputs.
        self.assertTrue(actual)

    def test4(self) -> None:
        """
        Test with unpaired .ipynb file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = os.path.join(scratch_dir, "notebook.ipynb")
        # Create only .ipynb file.
        hio.to_file(ipynb_file, "{}")
        # Run test.
        actual = llinutil.is_paired_jupytext_file(ipynb_file)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_is_shebang
# #############################################################################


class Test_is_shebang(hunitest.TestCase):
    """
    Test detection of shebang lines.
    """

    def test1(self) -> None:
        """
        Test with standard shebang.
        """
        # Prepare inputs.
        line = "#!/bin/bash"
        # Run test.
        actual = llinutil.is_shebang(line)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with Python shebang.
        """
        # Prepare inputs.
        line = "#!/usr/bin/env python"
        # Run test.
        actual = llinutil.is_shebang(line)
        # Check outputs.
        self.assertTrue(actual)

    def test3(self) -> None:
        """
        Test with comment that is not shebang.
        """
        # Prepare inputs.
        line = "# This is a comment"
        # Run test.
        actual = llinutil.is_shebang(line)
        # Check outputs.
        self.assertFalse(actual)

    def test4(self) -> None:
        """
        Test with code line.
        """
        # Prepare inputs.
        line = "x = 5"
        # Run test.
        actual = llinutil.is_shebang(line)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_is_comment
# #############################################################################


class Test_is_comment(hunitest.TestCase):
    """
    Test detection of comment lines.
    """

    def test1(self) -> None:
        """
        Test with simple comment.
        """
        # Prepare inputs.
        line = "# This is a comment"
        # Run test.
        actual = llinutil.is_comment(line)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with indented comment.
        """
        # Prepare inputs.
        line = "    # Indented comment"
        # Run test.
        actual = llinutil.is_comment(line)
        # Check outputs.
        self.assertTrue(actual)

    def test3(self) -> None:
        """
        Test with shebang is not a comment.
        """
        # Prepare inputs.
        line = "#!/usr/bin/env python"
        # Run test.
        actual = llinutil.is_comment(line)
        # Check outputs.
        self.assertFalse(actual)

    def test4(self) -> None:
        """
        Test with code line.
        """
        # Prepare inputs.
        line = "x = 5"
        # Run test.
        actual = llinutil.is_comment(line)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_is_separator
# #############################################################################


class Test_is_separator(hunitest.TestCase):
    """
    Test detection of separator lines.
    """

    def test1(self) -> None:
        """
        Test with exact separator.
        """
        # Prepare inputs.
        line = "# #############################################################################"
        # Run test.
        actual = llinutil.is_separator(line)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with similar but not exact separator.
        """
        # Prepare inputs.
        line = "# ##############################################################################"
        # Run test.
        actual = llinutil.is_separator(line)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test with comment line.
        """
        # Prepare inputs.
        line = "# This is a comment"
        # Run test.
        actual = llinutil.is_separator(line)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_parse_comment
# #############################################################################


class Test_parse_comment(hunitest.TestCase):
    """
    Test parsing of comment lines with regex.
    """

    def test1(self) -> None:
        """
        Test parsing simple comment.
        """
        # Prepare inputs.
        line = "# This is a comment"
        # Run test.
        actual = llinutil.parse_comment(line)
        # Check outputs.
        self.assertIsNotNone(actual)
        assert actual is not None
        self.assertEqual(actual.group(2), "This is a comment")

    def test2(self) -> None:
        """
        Test parsing indented comment.
        """
        # Prepare inputs.
        line = "    # Indented comment"
        # Run test.
        actual = llinutil.parse_comment(line)
        # Check outputs.
        self.assertIsNotNone(actual)
        assert actual is not None
        self.assertEqual(actual.group(2), "Indented comment")

    def test3(self) -> None:
        """
        Test that separator returns None.
        """
        # Prepare inputs.
        line = "# #############################################################################"
        # Run test.
        actual = llinutil.parse_comment(line)
        # Check outputs.
        self.assertIsNone(actual)

    def test4(self) -> None:
        """
        Test that shebang returns None.
        """
        # Prepare inputs.
        line = "#!/usr/bin/env python"
        # Run test.
        actual = llinutil.parse_comment(line)
        # Check outputs.
        self.assertIsNone(actual)

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

    def test1(self) -> None:
        """
        Test with test file in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.py"
        # Run test.
        actual = llinutil.is_test_code(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with file not in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/module.py"
        # Run test.
        actual = llinutil.is_test_code(file_name)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test with test file not starting with test_.
        """
        # Prepare inputs.
        file_name = "helpers/test/module_test.py"
        # Run test.
        actual = llinutil.is_test_code(file_name)
        # Check outputs.
        self.assertFalse(actual)

    def test4(self) -> None:
        """
        Test with test file that is not Python.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.txt"
        # Run test.
        actual = llinutil.is_test_code(file_name)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_is_test_input_output_file
# #############################################################################


class Test_is_test_input_output_file(hunitest.TestCase):
    """
    Test detection of test input/output files.
    """

    def test1(self) -> None:
        """
        Test with .txt file in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/outcomes/output.txt"
        # Run test.
        actual = llinutil.is_test_input_output_file(file_name)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test with .py file in test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/test_module.py"
        # Run test.
        actual = llinutil.is_test_input_output_file(file_name)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test with .txt file not in test directory.
        """
        # Prepare inputs.
        file_name = "output.txt"
        # Run test.
        actual = llinutil.is_test_input_output_file(file_name)
        # Check outputs.
        self.assertFalse(actual)

    def test4(self) -> None:
        """
        Test with .txt file in tmp.scratch test directory.
        """
        # Prepare inputs.
        file_name = "helpers/test/tmp.scratch/output.txt"
        # Run test.
        actual = llinutil.is_test_input_output_file(file_name)
        # Check outputs.
        self.assertFalse(actual)
