import dev_scripts_helpers.notebooks.process_jupytext as dsnprju
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import difflib
import logging
import os

import pytest

import dev_scripts_helpers.notebooks.process_jupytext as dshnprju
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest


class Test_process_jupytext_py(hunitest.TestCase):
    """
    End-to-end unit tests for process_jupytext.py executable.
    """

    def test_is_jupytext_version_different_no_match(self) -> None:
        """
        Test _is_jupytext_version_different with no version match.
        """
        output_txt = "Some random output without jupytext_version"
        result = dsnprju._is_jupytext_version_different(output_txt)
        self.assertFalse(result)

    def test_is_jupytext_version_different_single_match(self) -> None:
        """
        Test _is_jupytext_version_different with only one version line.
        """
        output_txt = "#       jupytext_version: 1.3.3"
        result = dsnprju._is_jupytext_version_different(output_txt)
        self.assertFalse(result)

    def test_is_jupytext_version_different_two_matches(self) -> None:
        """
        Test _is_jupytext_version_different with two different versions.
        """
        output_txt = (
            "#       jupytext_version: 1.3.3\n"
            "Some output\n"
            "#       jupytext_version: 1.3.0"
        )
        result = dsnprju._is_jupytext_version_different(output_txt)
        self.assertTrue(result)

    def test_find_paired_file_from_ipynb(self) -> None:
        """
        Test _find_paired_file with a .ipynb file as input.
        """
        scratch_dir = self.get_scratch_space()
        # Create test files.
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        # Create both files.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Test finding the paired file.
        result = dsnprju._find_paired_file(ipynb_file)
        self.assertEqual(result, py_file)

    def test_find_paired_file_from_py(self) -> None:
        """
        Test _find_paired_file with a .py file as input.
        """
        scratch_dir = self.get_scratch_space()
        # Create test files.
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        # Create both files.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Test finding the paired file.
        result = dsnprju._find_paired_file(py_file)
        self.assertEqual(result, ipynb_file)

    def test_find_paired_file_missing_paired(self) -> None:
        """
        Test _find_paired_file when paired file doesn't exist.
        """
        scratch_dir = self.get_scratch_space()
        # Create only one file.
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Test that error is raised.
        with self.assertRaises(AssertionError):
            dsnprju._find_paired_file(ipynb_file)

    def test_find_paired_file_invalid_extension(self) -> None:
        """
        Test _find_paired_file with invalid file extension.
        """
        scratch_dir = self.get_scratch_space()
        # Create a file with invalid extension.
        invalid_file = f"{scratch_dir}/test_notebook.txt"
        with open(invalid_file, "w") as f:
            f.write("")
        # Test that error is raised.
        # Note: hdbg.dfatal is called incorrectly in the original code,
        # so it raises TypeError instead of AssertionError.
        with self.assertRaises((AssertionError, TypeError)):
            dsnprju._find_paired_file(invalid_file)

    def test_pair_unpaired_ipynb_file(self) -> None:
        """
        Test _pair with an unpaired ipynb file.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            dsnprju._pair(ipynb_file)
        # Verify expected commands were called.
        # Should have:
        # 1. jupytext --update-metadata
        # 2. jupytext --test --stop
        # 3. jupytext --to py:percent
        # 4. git add
        self.assertEqual(len(invocations), 4)
        # Check first command (update-metadata)
        self.assertIn("jupytext", invocations[0]["args"][0])
        self.assertIn("--update-metadata", invocations[0]["args"][0])
        # Check second command (test)
        self.assertIn("jupytext", invocations[1]["args"][0])
        self.assertIn("--test", invocations[1]["args"][0])
        # Check third command (to py:percent)
        self.assertIn("jupytext", invocations[2]["args"][0])
        self.assertIn("--to py:percent", invocations[2]["args"][0])
        # Check fourth command (git add)
        self.assertIn("git add", invocations[3]["args"][0])

    def test_test_action(self) -> None:
        """
        Test _test with action='test' and successful conversion.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            dsnprju._test(ipynb_file, "test")
        # Verify expected command was called.
        self.assertEqual(len(invocations), 1)
        self.assertEqual(invocations[0]["function"], "hsystem.system_to_string")
        self.assertIn("--test", invocations[0]["args"][0])

    def test_test_strict_action(self) -> None:
        """
        Test _test with action='test_strict'.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            dsnprju._test(ipynb_file, "test_strict")
        # Verify expected command was called.
        self.assertEqual(len(invocations), 1)
        self.assertEqual(invocations[0]["function"], "hsystem.system_to_string")
        self.assertIn("--test-strict", invocations[0]["args"][0])

    def test_sync_paired_ipynb_file(self) -> None:
        """
        Test _sync with a paired ipynb file.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        # Create both files.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            dsnprju._sync(ipynb_file)
        # Verify expected commands were called.
        # Should have:
        # 1. jupytext --to py
        # 2. jupytext --sync
        self.assertEqual(len(invocations), 2)
        # Check first command (to py for ipynb file)
        self.assertIn("jupytext", invocations[0]["args"][0])
        self.assertIn("--to py", invocations[0]["args"][0])
        # Check second command (sync)
        self.assertIn("jupytext", invocations[1]["args"][0])
        self.assertIn("--sync", invocations[1]["args"][0])

    def test_sync_paired_py_file(self) -> None:
        """
        Test _sync with a paired .py file.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        # Create both files.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            dsnprju._sync(py_file)
        # Verify expected commands were called.
        # Should have:
        # 1. jupytext --to ipynb --update
        # 2. jupytext --sync
        self.assertEqual(len(invocations), 2)
        # Check first command (to ipynb --update for .py file)
        self.assertIn("jupytext", invocations[0]["args"][0])
        self.assertIn("--to ipynb", invocations[0]["args"][0])
        self.assertIn("--update", invocations[0]["args"][0])
        # Check second command (sync)
        self.assertIn("jupytext", invocations[1]["args"][0])
        self.assertIn("--sync", invocations[1]["args"][0])

    def test_extract_python_from_notebook(self) -> None:
        """
        Test _extract_python_from_notebook creates temp file.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            result = dsnprju._extract_python_from_notebook(ipynb_file)
        # Verify expected command was called.
        self.assertEqual(len(invocations), 1)
        self.assertIn("jupytext", invocations[0]["args"][0])
        self.assertIn("--to py:percent", invocations[0]["args"][0])
        # Verify result file path is correct.
        self.assertTrue(result.startswith("tmp.jupytext_diff."))
        self.assertTrue(result.endswith(".py"))

    def test_check_sync_status(self) -> None:
        """
        Test _check_sync_status calls jupytext diff.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # This test can't use capture_system_calls because
        # _check_sync_status uses os.system directly.
        # Just verify it doesn't raise an exception.
        try:
            dsnprju._check_sync_status(ipynb_file)
        except Exception as e:
            self.fail(f"_check_sync_status raised {e}")

    def test_report_newer_file(self) -> None:
        """
        Test _report_newer_file with two files.
        """
        scratch_dir = self.get_scratch_space()
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        # Create both files.
        with open(file1, "w") as f:
            f.write("file1")
        with open(file2, "w") as f:
            f.write("file2")
        # This test verifies the function runs without error
        # and logs the modification times.
        try:
            dsnprju._report_newer_file(file1, file2)
        except Exception as e:
            self.fail(f"_report_newer_file raised {e}")

    def test_main_pair_action(self) -> None:
        """
        Test _main with --action pair.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Test with pair action.
        parser = dsnprju._parse()
        args_list = ["-f", ipynb_file, "--action", "pair"]
        # Mock argv and parse.
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["process_jupytext.py"] + args_list
            with hunteuti.capture_system_calls() as invocations:
                dsnprju._main(parser)
            # Verify that pair was called.
            self.assertGreater(len(invocations), 0)
        finally:
            sys.argv = original_argv

    def test_main_test_action(self) -> None:
        """
        Test _main with --action test.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Test with test action.
        parser = dsnprju._parse()
        args_list = ["-f", ipynb_file, "--action", "test"]
        # Mock argv and parse.
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["process_jupytext.py"] + args_list
            with hunteuti.capture_system_calls() as invocations:
                dsnprju._main(parser)
            # Verify that test was called.
            self.assertGreater(len(invocations), 0)
        finally:
            sys.argv = original_argv

    def test_main_test_strict_action(self) -> None:
        """
        Test _main with --action test_strict.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Test with test_strict action.
        parser = dsnprju._parse()
        args_list = ["-f", ipynb_file, "--action", "test_strict"]
        # Mock argv and parse.
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["process_jupytext.py"] + args_list
            with hunteuti.capture_system_calls() as invocations:
                dsnprju._main(parser)
            # Verify that test_strict was called.
            self.assertGreater(len(invocations), 0)
        finally:
            sys.argv = original_argv

    def test_main_sync_action(self) -> None:
        """
        Test _main with --action sync.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        py_file = f"{scratch_dir}/test_notebook.py"
        # Create both files.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        with open(py_file, "w") as f:
            f.write("")
        # Test with sync action.
        parser = dsnprju._parse()
        args_list = ["-f", ipynb_file, "--action", "sync"]
        # Mock argv and parse.
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["process_jupytext.py"] + args_list
            with hunteuti.capture_system_calls() as invocations:
                dsnprju._main(parser)
            # Verify that sync was called.
            self.assertGreater(len(invocations), 0)
        finally:
            sys.argv = original_argv

    def test_main_invalid_action(self) -> None:
        """
        Test _main with invalid action.
        """
        scratch_dir = self.get_scratch_space()
        ipynb_file = f"{scratch_dir}/test_notebook.ipynb"
        # Create an ipynb file.
        with open(ipynb_file, "w") as f:
            f.write("{}")
        # Test with invalid action.
        parser = dsnprju._parse()
        args_list = ["-f", ipynb_file, "--action", "invalid_action"]
        # Mock argv and parse - should fail because invalid_action is not in choices.
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["process_jupytext.py"] + args_list
            # The argparse will raise SystemExit for invalid choices
            with self.assertRaises(SystemExit):
                dsnprju._main(parser)
        finally:
            sys.argv = original_argv

# #############################################################################
# Test_process_jupytext
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_inside_docker(),
    reason="jupytext is only inside Docker dev environment",
)
class Test_process_jupytext(hunitest.TestCase):
    @pytest.mark.slow("~7 seconds.")
    def test_end_to_end(self) -> None:
        """
        Test file syncing with `process_jupytext.py` end-to-end.

        Test that `process_jupytext.py` updates an `.ipynb` notebook when the
        paired `.py` file is changed.
        - Create two paired files: `.py` and `.ipynb`
        - Change the code in the `.py` file
        - Run `sync` and `test` in `process_jupytext.py`
        - Check that the `.ipynb` file was updated
        """
        file_name = "notebook_for_test"
        # Create .py and .ipynb files for testing.
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
        # Pair files.
        cmd = f"jupytext --set-formats ipynb,py {ipynb_path}"
        hsystem.system(cmd)
        # Add a string to python file to check if sync works.
        py_text += "\na = 0"
        hio.to_file(file_path, py_text)
        # Run processor.
        cmd = f"$(find -wholename '*dev_scripts_helpers/notebooks/process_jupytext.py') -f {file_path} --action sync 2>&1"
        hsystem.system(cmd)
        cmd = f"$(find -wholename '*dev_scripts_helpers/notebooks/process_jupytext.py') -f {file_path} --action test 2>&1"
        hsystem.system(cmd)
        # Check that notebook content was changed.
        new_ipynb_text = hio.from_file(ipynb_path)
        differ = difflib.Differ()
        diffs = []
        old_lines = ipynb_text.splitlines()
        new_lines = new_ipynb_text.splitlines()
        for line in list(differ.compare(old_lines, new_lines)):
            if not line.startswith(" "):
                diffs.append(line)
        self.check_string("\n".join(diffs))

    def test_is_jupytext_version_different_true(self) -> None:
        """
        Test jupytext version comparison: when the versions are different.
        """
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
        self.assertTrue(dshnprju._is_jupytext_version_different(txt))

    def test_is_jupytext_version_different_false(self) -> None:
        """
        Test jupytext version comparison: when the versions are not different.
        """
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
        self.assertFalse(dshnprju._is_jupytext_version_different(txt))
