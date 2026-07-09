"""
Import as:

import dev_scripts_helpers.coding_tools.test.test_copy_across_clients as dsctccac
"""

import os
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_copy_across_clients_py
# #############################################################################


class Test_copy_across_clients_py(hunitest.TestCase):
    """
    End-to-end tests for the `copy_across_clients.py` executable.
    """

    def _run_main(self, argv):
        """
        Run `module._main()` with mocked `sys.argv`.

        :param argv: Command-line argument list
        """
        import dev_scripts_helpers.coding_tools.copy_across_clients as dscoac

        parser = dscoac._parse()
        with mock.patch("sys.argv", argv):
            dscoac._main(parser)

    def test1(self) -> None:
        """
        Test copying specific files with --files option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir1 = os.path.join(scratch_dir, "dir1")
        dir2 = os.path.join(scratch_dir, "dir2")
        hio.create_dir(dir1, incremental=True)
        hio.create_dir(dir2, incremental=True)
        # Create test files in dir1.
        file1_path = os.path.join(dir1, "file1.txt")
        hio.to_file(file1_path, "file1 content")
        subdir_path = os.path.join(dir1, "subdir")
        hio.create_dir(subdir_path, incremental=True)
        file2_path = os.path.join(subdir_path, "file2.txt")
        hio.to_file(file2_path, "file2 content")
        # Run test.
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--files",
            "file1.txt",
            "subdir/file2.txt",
        ]
        self._run_main(argv)
        # Check outputs.
        self.assertTrue(os.path.exists(os.path.join(dir2, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(dir2, "subdir", "file2.txt")))
        actual_file1 = hio.from_file(os.path.join(dir2, "file1.txt"))
        actual_file2 = hio.from_file(os.path.join(dir2, "subdir", "file2.txt"))
        self.assertEqual(actual_file1, "file1 content")
        self.assertEqual(actual_file2, "file2 content")

    def test2(self) -> None:
        """
        Test copying files from a list file with --from_file option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir1 = os.path.join(scratch_dir, "dir1")
        dir2 = os.path.join(scratch_dir, "dir2")
        hio.create_dir(dir1, incremental=True)
        hio.create_dir(dir2, incremental=True)
        # Create test files.
        file1_path = os.path.join(dir1, "file1.txt")
        hio.to_file(file1_path, "file1 content")
        file2_path = os.path.join(dir1, "file2.txt")
        hio.to_file(file2_path, "file2 content")
        # Create file list.
        files_list = os.path.join(scratch_dir, "files.txt")
        hio.to_file(files_list, "file1.txt\nfile2.txt\n")
        # Run test.
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            f"--from_file={files_list}",
        ]
        self._run_main(argv)
        # Check outputs.
        self.assertTrue(os.path.exists(os.path.join(dir2, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(dir2, "file2.txt")))

    def test3(self) -> None:
        """
        Test copying entire directory with --dir option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir1 = os.path.join(scratch_dir, "source")
        dir2 = os.path.join(scratch_dir, "dest")
        hio.create_dir(dir1, incremental=True)
        hio.create_dir(dir2, incremental=True)
        # Create test files.
        file1_path = os.path.join(dir1, "file1.txt")
        hio.to_file(file1_path, "file1 content")
        subdir_path = os.path.join(dir1, "subdir")
        hio.create_dir(subdir_path, incremental=True)
        file2_path = os.path.join(subdir_path, "file2.txt")
        hio.to_file(file2_path, "file2 content")
        # Run test.
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--dir",
        ]
        self._run_main(argv)
        # Check outputs.
        self.assertTrue(os.path.exists(os.path.join(dir2, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(dir2, "subdir", "file2.txt")))

    def test4(self) -> None:
        """
        Test dry run with --dry_run option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir1 = os.path.join(scratch_dir, "dir1")
        dir2 = os.path.join(scratch_dir, "dir2")
        hio.create_dir(dir1, incremental=True)
        hio.create_dir(dir2, incremental=True)
        # Create test file.
        file1_path = os.path.join(dir1, "file1.txt")
        hio.to_file(file1_path, "file1 content")
        # Run test with dry run.
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--files",
            "file1.txt",
            "--dry_run",
        ]
        self._run_main(argv)
        # Check outputs: file should NOT be copied.
        self.assertFalse(os.path.exists(os.path.join(dir2, "file1.txt")))

    def test5(self) -> None:
        """
        Test deletion of destination file when source doesn't exist.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir1 = os.path.join(scratch_dir, "dir1")
        dir2 = os.path.join(scratch_dir, "dir2")
        hio.create_dir(dir1, incremental=True)
        hio.create_dir(dir2, incremental=True)
        # Create source file.
        file1_path = os.path.join(dir1, "file1.txt")
        hio.to_file(file1_path, "file1 content")
        # Create destination file that shouldn't exist (file2.txt not in dir1).
        file2_dest_path = os.path.join(dir2, "file2.txt")
        hio.to_file(file2_dest_path, "file2 content")
        # Run test.
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--files",
            "file1.txt",
            "file2.txt",
        ]
        self._run_main(argv)
        # Check outputs.
        self.assertTrue(os.path.exists(os.path.join(dir2, "file1.txt")))
        # file2.txt should be deleted since it doesn't exist in dir1.
        self.assertFalse(os.path.exists(file2_dest_path))

    def test6(self) -> None:
        """
        Test error when no copy option is provided.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir1 = os.path.join(scratch_dir, "dir1")
        dir2 = os.path.join(scratch_dir, "dir2")
        hio.create_dir(dir1, incremental=True)
        hio.create_dir(dir2, incremental=True)
        # Run test: no --files, --from_file, or --dir provided.
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
        ]
        # Should fail due to missing mutually exclusive group.
        with self.assertRaises(SystemExit):
            self._run_main(argv)

    def test7(self) -> None:
        """
        Test error when directories don't exist.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        nonexistent_dir = os.path.join(scratch_dir, "nonexistent")
        existing_dir = os.path.join(scratch_dir, "existing")
        hio.create_dir(existing_dir, incremental=True)
        # Run test: nonexistent_dir doesn't exist.
        argv = [
            "copy_across_clients.py",
            f"--dir1={nonexistent_dir}",
            f"--dir2={existing_dir}",
            "--files",
            "file.txt",
        ]
        # Should fail due to directory not existing.
        with self.assertRaises(AssertionError):
            self._run_main(argv)
