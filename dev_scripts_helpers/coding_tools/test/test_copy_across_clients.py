"""
Import as:

import dev_scripts_helpers.coding_tools.test.test_copy_across_clients as dsctccac
"""

import logging
import os
import shutil
from typing import Dict, List, Optional
from unittest import mock


import pytest

import dev_scripts_helpers.coding_tools.copy_across_clients as dshctcacl
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_copy_across_clients_py
# #############################################################################


class Test_copy_across_clients_py(hunitest.TestCase):
    """
    End-to-end tests for the `copy_across_clients.py` executable.
    """

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `module._main()` with mocked `sys.argv`.

        :param argv: Command-line argument list
        """
        parser = dshctcacl._parse()
        with mock.patch("sys.argv", argv):
            dshctcacl._main(parser)

    def _setup_test_dirs(
        self, scratch_dir: str, dir_names: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Create and return test directories.

        :param scratch_dir: Base scratch directory
        :param dir_names: List of directory names to create (default: ["dir1", "dir2"])
        :return: Dict mapping dir name -> full path
        """
        if dir_names is None:
            dir_names = ["dir1", "dir2"]
        dirs = {}
        for name in dir_names:
            path = os.path.join(scratch_dir, name)
            hio.create_dir(path, incremental=True)
            dirs[name] = path
        return dirs

    def _create_test_files(
        self, parent_dir: str, files_spec: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Create test files in a directory structure.

        :param parent_dir: Parent directory path
        :param files_spec: Dict mapping filename (or "dir/file") -> content
        :return: Dict mapping relative path -> full path
        """
        created = {}
        for filepath, content in files_spec.items():
            full_path = os.path.join(parent_dir, filepath)
            dir_path = os.path.dirname(full_path)
            if dir_path and dir_path != parent_dir:
                hio.create_dir(dir_path, incremental=True)
            hio.to_file(full_path, content)
            created[filepath] = full_path
        return created

    def test1(self) -> None:
        """
        Test copying specific files with --files option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dirs = self._setup_test_dirs(scratch_dir)
        files_spec = {
            "file1.txt": "file1 content",
            "subdir/file2.txt": "file2 content",
        }
        self._create_test_files(dirs["dir1"], files_spec)
        dir1 = dirs["dir1"]
        dir2 = dirs["dir2"]
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--files",
            "file1.txt",
            "subdir/file2.txt",
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        file1_path = os.path.join(dir2, "file1.txt")
        file2_path = os.path.join(dir2, "subdir", "file2.txt")
        actual_file1 = hio.from_file(file1_path)
        actual_file2 = hio.from_file(file2_path)
        expected_file1 = "file1 content"
        expected_file2 = "file2 content"
        self.assert_equal(actual_file1, expected_file1)
        self.assert_equal(actual_file2, expected_file2)

    def test2(self) -> None:
        """
        Test copying files from a list file with --from_file option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dirs = self._setup_test_dirs(scratch_dir)
        files_spec = {
            "file1.txt": "file1 content",
            "file2.txt": "file2 content",
        }
        self._create_test_files(dirs["dir1"], files_spec)
        files_list = os.path.join(scratch_dir, "files.txt")
        files_list_content = "file1.txt\nfile2.txt\n"
        hio.to_file(files_list, files_list_content)
        dir1 = dirs["dir1"]
        dir2 = dirs["dir2"]
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            f"--from_file={files_list}",
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        file1_path = os.path.join(dir2, "file1.txt")
        file2_path = os.path.join(dir2, "file2.txt")
        self.assertTrue(os.path.exists(file1_path))
        self.assertTrue(os.path.exists(file2_path))

    @pytest.mark.skipif(
        shutil.which("rsync") is None, reason="rsync not installed"
    )
    def test3(self) -> None:
        """
        Test copying entire directory with --dir option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir_names = ["source", "dest"]
        dirs = self._setup_test_dirs(scratch_dir, dir_names)
        files_spec = {
            "file1.txt": "file1 content",
            "subdir/file2.txt": "file2 content",
        }
        self._create_test_files(dirs["source"], files_spec)
        dir1 = dirs["source"]
        dir2 = dirs["dest"]
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--dir",
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        file1_path = os.path.join(dir2, "file1.txt")
        file2_path = os.path.join(dir2, "subdir", "file2.txt")
        self.assertTrue(os.path.exists(file1_path))
        self.assertTrue(os.path.exists(file2_path))

    def test4(self) -> None:
        """
        Test dry run with --dry_run option.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dirs = self._setup_test_dirs(scratch_dir)
        files_spec = {"file1.txt": "file1 content"}
        self._create_test_files(dirs["dir1"], files_spec)
        dir1 = dirs["dir1"]
        dir2 = dirs["dir2"]
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--files",
            "file1.txt",
            "--dry_run",
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        file1_path = os.path.join(dir2, "file1.txt")
        self.assertFalse(os.path.exists(file1_path))

    def test5(self) -> None:
        """
        Test deletion of destination file when source doesn't exist.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dirs = self._setup_test_dirs(scratch_dir)
        files_spec = {"file1.txt": "file1 content"}
        self._create_test_files(dirs["dir1"], files_spec)
        file2_dest_path = os.path.join(dirs["dir2"], "file2.txt")
        hio.to_file(file2_dest_path, "file2 content")
        dir1 = dirs["dir1"]
        dir2 = dirs["dir2"]
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
            "--files",
            "file1.txt",
            "file2.txt",
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        file1_path = os.path.join(dir2, "file1.txt")
        self.assertTrue(os.path.exists(file1_path))
        self.assertFalse(os.path.exists(file2_dest_path))

    def test6(self) -> None:
        """
        Test error when no copy option is provided.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dirs = self._setup_test_dirs(scratch_dir)
        dir1 = dirs["dir1"]
        dir2 = dirs["dir2"]
        argv = [
            "copy_across_clients.py",
            f"--dir1={dir1}",
            f"--dir2={dir2}",
        ]
        # Run test and check outputs.
        with self.assertRaises(SystemExit):
            self._run_main(argv)

    def test7(self) -> None:
        """
        Test error when directories don't exist.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir_names = ["existing"]
        dirs = self._setup_test_dirs(scratch_dir, dir_names)
        nonexistent_dir = os.path.join(scratch_dir, "nonexistent")
        existing_dir = dirs["existing"]
        argv = [
            "copy_across_clients.py",
            f"--dir1={nonexistent_dir}",
            f"--dir2={existing_dir}",
            "--files",
            "file.txt",
        ]
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            self._run_main(argv)
