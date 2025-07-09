import logging
import os

import numpy as np
import pandas as pd

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class Test_rename_file_if_exists(hunitest.TestCase):
    """
    Test that the function renames existing files correctly.
    """

    def check_file(
        self,
        file_to_rename: str,
        before_extension: bool,
        expected_file_name: str,
    ) -> None:
        """
        Check that file is renamed correctly.
        """
        # Create a target file to rename.
        scratch_dir = self.get_scratch_space()
        file_name = "test_file.txt"
        file_path = os.path.join(scratch_dir, file_name)
        lines = ""
        hio.to_file(file_path, lines)
        # Rename the file.
        file_to_rename = os.path.join(scratch_dir, file_to_rename)
        suffix = "suffix"
        hio.rename_file_if_exists(
            file_to_rename, suffix, before_extension=before_extension
        )
        # Check that file is renamed.
        expected_file_path = os.path.join(scratch_dir, expected_file_name)
        self.assertTrue(os.path.exists(expected_file_path))

    def test1(self) -> None:
        """
        Test that suffix is added before an extension.
        """
        file_to_rename = "test_file.txt"
        before_extension = True
        expected_file_name = "test_file.suffix.txt"
        self.check_file(file_to_rename, before_extension, expected_file_name)

    def test2(self) -> None:
        """
        Test that suffix is added after an extension.
        """
        file_to_rename = "test_file.txt"
        before_extension = False
        expected_file_name = "test_file.txt.suffix"
        self.check_file(file_to_rename, before_extension, expected_file_name)

    def test3(self) -> None:
        """
        Test that non-existing file is not renamed.
        """
        file_to_rename = "not_exist.txt"
        before_extension = False
        expected_file_name = "not_exist.txt"
        with self.assertRaises(AssertionError):
            self.check_file(file_to_rename, before_extension, expected_file_name)


class Test_find_all_files1(hunitest.TestCase):
    def test1(self) -> None:
        dir_name = hgit.get_client_root(super_module=False)
        # Check that there are files.
        pattern = "*"
        only_files = True
        use_relative_paths = True
        all_files = hio.listdir(
            dir_name, pattern, only_files, use_relative_paths
        )
        self.assertGreater(len(all_files), 0)
        # Check that there are more files than Python files.
        exclude_paired_jupytext = False
        py_files = hio.keep_python_files(all_files, exclude_paired_jupytext)
        self.assertGreater(len(py_files), 0)
        self.assertGreater(len(all_files), len(py_files))
        # Check that there are more Python files than not paired Python files.
        exclude_paired_jupytext = True
        not_paired_py_files = hio.keep_python_files(
            all_files, exclude_paired_jupytext
        )
        self.assertGreater(len(not_paired_py_files), 0)
        self.assertGreater(len(py_files), len(not_paired_py_files))


class Test_change_filename_extension1(hunitest.TestCase):
    def test1(self) -> None:
        file_name = "./core/dataflow_model/notebooks/Master_experiment_runner.py"
        actual = hio.change_filename_extension(file_name, "py", "ipynb")
        expected = (
            "./core/dataflow_model/notebooks/Master_experiment_runner.ipynb"
        )
        self.assert_equal(actual, expected)


class Test_load_df_from_json(hunitest.TestCase):
    def test1(self) -> None:
        test_json_path = os.path.join(self.get_input_dir(), "test.json")
        actual_result = hio.load_df_from_json(test_json_path)
        expected_result = pd.DataFrame(
            {
                "col1": ["a", "b", "c", "d"],
                "col2": ["a", "b", np.nan, np.nan],
                "col3": ["a", "b", "c", np.nan],
            }
        )
        actual_result = hpandas.df_to_str(actual_result)
        expected_result = hpandas.df_to_str(expected_result)
        self.assertEqual(actual_result, expected_result)


# #############################################################################
# Test_safe_rm_file
# #############################################################################


class Test_safe_rm_file(hunitest.TestCase):

    def test_successful_removal_within_git_client(self) -> None:
        """
        Test successful removal of directory within Git client.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_dir = os.path.join(scratch_dir, "test_dir_to_remove")
        os.makedirs(test_dir)
        # Create a test file in the directory to ensure it has content
        test_file = os.path.join(test_dir, "test_file.txt")
        hio.to_file(test_file, "test content")
        # Verify directory exists before removal
        self.assertTrue(os.path.exists(test_dir))
        # Run test.
        hio.safe_rm_file(test_dir)
        # Check output.
        self.assertFalse(os.path.exists(test_dir))

    def test_removal_of_nested_directory(self) -> None:
        """
        Test removal of deeply nested directory structure.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        nested_dir = os.path.join(scratch_dir, "parent", "child", "grandchild")
        os.makedirs(nested_dir)
        # Create files at different levels
        hio.to_file(os.path.join(nested_dir, "file1.txt"), "content1")
        hio.to_file(os.path.join(os.path.dirname(nested_dir), "file2.txt"), "content2")
        parent_dir = os.path.join(scratch_dir, "parent")
        # Verify directory exists
        self.assertTrue(os.path.exists(parent_dir))
        # Run test.
        hio.safe_rm_file(parent_dir)
        # Check output.
        self.assertFalse(os.path.exists(parent_dir))

    def test_directory_does_not_exist(self) -> None:
        """
        Test that function raises assertion error for non-existent directory.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        non_existent_dir = os.path.join(scratch_dir, "non_existent_directory")
        # Ensure directory doesn't exist
        self.assertFalse(os.path.exists(non_existent_dir))
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hio.safe_rm_file(non_existent_dir)
        self.assertIn("does not exist", str(cm.exception))

    def test_cannot_delete_git_root(self) -> None:
        """
        Test that function prevents deletion of Git client root directory.
        """
        # Prepare inputs.
        git_root = hgit.find_git_root()
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hio.safe_rm_file(git_root)
        self.assertIn("Cannot delete Git client root", str(cm.exception))

    def test_directory_outside_git_client_rejected(self) -> None:
        """
        Test that function rejects directories outside Git client.
        """
        # Prepare inputs.
        # Use /tmp which should be outside any Git client
        outside_dir = "/tmp"
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hio.safe_rm_file(outside_dir)
        self.assertIn("is not within Git client root", str(cm.exception))
