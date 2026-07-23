import difflib
import os

import pytest

import dev_scripts_helpers.notebooks.jupytext as dshenoju
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti


# #############################################################################
# Test_is_jupytext_version_different
# #############################################################################


# TODO(ai_gp): Factor out the common code in helper
class Test_is_jupytext_version_different(hunitest.TestCase):
    """
    Unit tests for _is_jupytext_version_different function.
    """

    def test1(self) -> None:
        """
        Test with no version match.
        """
        # Prepare inputs.
        output_txt = "Some random output without jupytext_version"
        # Run test.
        result = dshenoju._is_jupytext_version_different(output_txt)
        # Check outputs.
        self.assertFalse(result)

    def test2(self) -> None:
        """
        Test with only one version line.
        """
        # Prepare inputs.
        output_txt = "#       jupytext_version: 1.3.3"
        # Run test.
        result = dshenoju._is_jupytext_version_different(output_txt)
        # Check outputs.
        self.assertFalse(result)

    def test3(self) -> None:
        """
        Test with two different versions.
        """
        # Prepare inputs.
        output_txt = (
            "#       jupytext_version: 1.3.3\n"
            "Some output\n"
            "#       jupytext_version: 1.3.0"
        )
        # Run test.
        result = dshenoju._is_jupytext_version_different(output_txt)
        # Check outputs.
        self.assertTrue(result)

    def test4(self) -> None:
        """
        Test with version difference in diff output (expected vs actual).
        """
        # Prepare inputs.
        txt = """
        --- expected
        +++ actual
        @@ -5,7 +5,7 @@
        #       extension: .py
        #       format_name: percent
        #       format_version: '1.3'
        -#       jupytext_version: 1.3.3
        +#       jupytext_version: 1.3.0
        #   kernelspec:
        #     display_name: Python [conda env:.conda-amp_develop] *
        #     language: python
        """
        txt = hprint.dedent(txt)
        # Run test.
        result = dshenoju._is_jupytext_version_different(txt)
        # Check outputs.
        self.assertTrue(result)

    def test5(self) -> None:
        """
        Test with version non-difference in diff output (no version change).
        """
        # Prepare inputs.
        txt = """
        --- expected
        +++ actual
        @@ -5,7 +5,7 @@
        #       extension: .py
        -#       format_name: percent
        +#       format_name: plus
        #       format_version: '1.3'
        #       jupytext_version: 1.3.3
        #   kernelspec:
        #     display_name: Python [conda env:.conda-amp_develop] *
        #     language: python
        """
        txt = hprint.dedent(txt)
        # Run test.
        result = dshenoju._is_jupytext_version_different(txt)
        # Check outputs.
        self.assertFalse(result)


# #############################################################################
# Test_find_paired_file
# #############################################################################


# TODO(ai_gp): Factor out the common code in helper
class Test_find_paired_file(hunitest.TestCase):
    """
    Unit tests for _find_paired_file function.
    """

    def test1(self) -> None:
        """
        Test _find_paired_file with a .ipynb file as input.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        result = dshenoju._find_paired_file(ipynb_file)
        # Check outputs.
        self.assertEqual(result, py_file)

    def test2(self) -> None:
        """
        Test _find_paired_file with a .py file as input.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        result = dshenoju._find_paired_file(py_file)
        # Check outputs.
        self.assertEqual(result, ipynb_file)

    def test3(self) -> None:
        """
        Test _find_paired_file when paired file doesn't exist.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshenoju._find_paired_file(ipynb_file)

    def test4(self) -> None:
        """
        Test _find_paired_file with invalid file extension.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        invalid_file = f"{scratch_dir}/test_notebook.txt"
        with open(invalid_file, "w") as f:
            f.write("")
        # Run test and check output.
        with self.assertRaises((AssertionError, TypeError)):
            dshenoju._find_paired_file(invalid_file)


# #############################################################################
# Test_jupytext_py
# #############################################################################


class Test_jupytext_py(hunitest.TestCase):
    """
    End-to-end unit tests for jupytext.py executable.
    """

    def test5(self) -> None:
        """
        Test _pair with an unpaired ipynb file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshenoju._pair(ipynb_file)
        # Check outputs.
        expected = f"""
        [
        {{
        'function': hsystem.system
        'args': ('jupytext --update-metadata \\'{{\"jupytext\":{{\"formats\":\"ipynb,py:percent\"}}}}\\' $GIT_ROOT/dev_scripts_helpers/notebooks/test/outcomes/Test_jupytext_py.test5/tmp.scratch/test_notebook.ipynb',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system
        'args': ('jupytext --test --stop --to py:percent $GIT_ROOT/dev_scripts_helpers/notebooks/test/outcomes/Test_jupytext_py.test5/tmp.scratch/test_notebook.ipynb',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system
        'args': ('jupytext --to py:percent $GIT_ROOT/dev_scripts_helpers/notebooks/test/outcomes/Test_jupytext_py.test5/tmp.scratch/test_notebook.ipynb',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system
        'args': ('git add $GIT_ROOT/dev_scripts_helpers/notebooks/test/outcomes/Test_jupytext_py.test5/tmp.scratch/test_notebook.py',)
        'kwargs': {{}}
        }},
        ]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test6(self) -> None:
        """
        Test _test with action='test' and successful conversion.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshenoju._test(ipynb_file, "test")
        # Check outputs.
        expected = f"""
        [
        {{
        'function': hsystem.system
        'args': ('jupytext --to py:percent {ipynb_file} -o tmp.jupytext_diff.test_notebook.py',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system_to_string
        'args': ('diff {py_file} tmp.jupytext_diff.test_notebook.py',)
        'kwargs': {{'abort_on_error': False}}
        }},
        ]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test7(self) -> None:
        """
        Test _test with action='test_strict'.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshenoju._test(ipynb_file, "test_strict")
        # Check outputs.
        expected = f"""
        [
        {{
        'function': hsystem.system
        'args': ('jupytext --to py:percent {ipynb_file} -o tmp.jupytext_diff.test_notebook.py',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system_to_string
        'args': ('diff {py_file} tmp.jupytext_diff.test_notebook.py',)
        'kwargs': {{'abort_on_error': False}}
        }},
        ]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test8(self) -> None:
        """
        Test _sync with a paired ipynb file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshenoju._sync(ipynb_file)
        # Check outputs.
        ipynb_path = str(ipynb_file)
        expected = f"""[
        {{
        'function': hsystem.system
        'args': ('jupytext --to py {ipynb_path}',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system
        'args': ('jupytext --sync {ipynb_path}',)
        'kwargs': {{}}
        }},
        ]"""
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test9(self) -> None:
        """
        Test _sync with a paired .py file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshenoju._sync(py_file)
        # Check outputs.
        py_path = str(py_file)
        expected = f"""[
        {{
        'function': hsystem.system
        'args': ('jupytext --to ipynb --update {py_path}',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system
        'args': ('jupytext --sync {py_path}',)
        'kwargs': {{}}
        }},
        ]"""
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test10(self) -> None:
        """
        Test _extract_python_from_notebook creates temp file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshenoju._extract_python_from_notebook(ipynb_file)
        # Check outputs.
        expected = f"""
        [
        {{
        'function': hsystem.system
        'args': ('jupytext --to py:percent {ipynb_file} -o tmp.jupytext_diff.test_notebook.py',)
        'kwargs': {{}}
        }},
        ]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test11(self) -> None:
        """
        Test _is_notebook_in_sync checks sync status using diff.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            _, _ = dshenoju._is_notebook_in_sync(ipynb_file)
        # Check outputs: should have extract and diff calls.
        expected = f"""
        [
        {{
        'function': hsystem.system
        'args': ('jupytext --to py:percent {ipynb_file} -o tmp.jupytext_diff.test_notebook.py',)
        'kwargs': {{}}
        }},
        {{
        'function': hsystem.system_to_string
        'args': ('diff {py_file} tmp.jupytext_diff.test_notebook.py',)
        'kwargs': {{'abort_on_error': False}}
        }},
        ]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test12(self) -> None:
        """
        Test _report_newer_file with two files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        with open(file1, "w") as f:
            f.write("file1")
        with open(file2, "w") as f:
            f.write("file2")
        # Run test.
        dshenoju._report_newer_file(file1, file2)

    def test13(self) -> None:
        """
        Test jupytext.py with --action pair.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        executable = hgit.find_file_in_git_tree("jupytext.py")
        cmd = f"{executable} -f {ipynb_file} --action pair 2>&1"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            hsystem.system(cmd)
        # Check outputs.
        expected = f"""[
        {{
        'function': hsystem.system
        'args': ('{cmd}',)
        'kwargs': {{}}
        }},
        ]"""
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test14(self) -> None:
        """
        Test jupytext.py with --action test.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        executable = hgit.find_file_in_git_tree("jupytext.py")
        cmd = f"{executable} -f {ipynb_file} --action test 2>&1"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            hsystem.system(cmd)
        # Check outputs.
        expected = f"""[
        {{
        'function': hsystem.system
        'args': ('{cmd}',)
        'kwargs': {{}}
        }},
        ]"""
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test15(self) -> None:
        """
        Test jupytext.py with --action test_strict.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        executable = hgit.find_file_in_git_tree("jupytext.py")
        cmd = f"{executable} -f {ipynb_file} --action test_strict 2>&1"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            hsystem.system(cmd)
        # Check outputs.
        expected = f"""[
        {{
        'function': hsystem.system
        'args': ('{cmd}',)
        'kwargs': {{}}
        }},
        ]"""
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test16(self) -> None:
        """
        Test jupytext.py with --action sync.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        executable = hgit.find_file_in_git_tree("jupytext.py")
        cmd = f"{executable} -f {ipynb_file} --action sync 2>&1"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            hsystem.system(cmd)
        # Check outputs.
        expected = f"""[
        {{
        'function': hsystem.system
        'args': ('{cmd}',)
        'kwargs': {{}}
        }},
        ]"""
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test17(self) -> None:
        """
        Test jupytext.py with invalid action.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        executable = hgit.find_file_in_git_tree("jupytext.py")
        cmd = f"{executable} -f {ipynb_file} --action invalid_action 2>&1"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Run test.
        with self.assertRaises(Exception):
            hsystem.system(cmd)


# #############################################################################
# Test_jupytext_py_end_to_end
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_inside_docker(),
    reason="jupytext is only inside Docker dev environment",
)
class Test_jupytext_py_end_to_end(hunitest.TestCase):
    @pytest.mark.slow("~7 seconds.")
    def test1(self) -> None:
        """
        Test file syncing with `jupytext.py` end-to-end.

        Test that `jupytext.py` updates an `.ipynb` notebook when the
        paired `.py` file is changed.
        """
        # Prepare inputs.
        file_name = "notebook_for_test"
        py_text = hio.from_file(
            os.path.join(self.get_input_dir(), f"{file_name}.py.txt")
        )
        ipynb_text = hio.from_file(
            os.path.join(self.get_input_dir(), f"{file_name}.ipynb.txt")
        )
        file_path = os.path.join(self.get_scratch_space(), f"{file_name}.py")
        ipynb_path = os.path.join(self.get_scratch_space(), f"{file_name}.ipynb")
        hio.to_file(file_path, py_text)
        hio.to_file(ipynb_path, ipynb_text)
        cmd = f"jupytext --set-formats ipynb,py {ipynb_path}"
        hsystem.system(cmd)
        py_text += "\na = 0"
        hio.to_file(file_path, py_text)
        # Run test.
        executable = hgit.find_file_in_git_tree("jupytext.py")
        cmd = f"{executable} -f {file_path} --action sync 2>&1"
        hsystem.system(cmd)
        cmd = f"{executable} -f {file_path} --action test 2>&1"
        hsystem.system(cmd)
        # Check outputs.
        new_ipynb_text = hio.from_file(ipynb_path)
        differ = difflib.Differ()
        diffs = []
        old_lines = ipynb_text.splitlines()
        new_lines = new_ipynb_text.splitlines()
        for line in list(differ.compare(old_lines, new_lines)):
            if not line.startswith(" "):
                diffs.append(line)
        self.check_string("\n".join(diffs))
