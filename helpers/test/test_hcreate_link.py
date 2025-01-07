import os
import shutil
import filecmp
import pytest
from pathlib import Path

import helpers.hunit_test as hut
import helpers.create_links as create_links


class Test_create_links(hut.TestCase):
    """
    Unit tests for the `create_links.py` script.
    """

    def _prepare_directories(self):
        """
        Prepare source and destination directories with test data.
        """
        # Set up input and scratch directories.
        src_dir = self.get_input_dir()
        dst_dir = self.get_scratch_space()
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dst_dir, exist_ok=True)
        return src_dir, dst_dir

    def _create_file(self, dir_path, file_name, content):
        """
        Helper to create a file with the given content.
        """
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def test__find_common_files(self):
        """
        Test `create_links._find_common_files()` for identifying common files.
        """
        src_dir, dst_dir = self._prepare_directories()
        # Create common and unique files.
        file1_src = self._create_file(src_dir, "file1.txt", "Hello, World!")
        file1_dst = shutil.copy(file1_src, dst_dir)
        self._create_file(src_dir, "file2.txt", "This is only in source.")
        self._create_file(dst_dir, "file3.txt", "This is only in destination.")
        # Find common files.
        common_files = create_links._find_common_files(src_dir, dst_dir)
        self.assert_equal(len(common_files), 1)
        self.assert_equal(common_files[0], (file1_src, file1_dst))

    def test__replace_with_links_absolute(self):
        """
        Test replacing files with absolute symbolic links.
        """
        src_dir, dst_dir = self._prepare_directories()
        file1 = self._create_file(src_dir, "file1.txt", "Hello, World!")
        shutil.copy(file1, dst_dir)
        # Replace with absolute symbolic links.
        common_files = create_links._find_common_files(src_dir, dst_dir)
        create_links._replace_with_links(common_files, use_relative_paths=False)
        # Verify.
        for _, dst_file in common_files:
            self.assertTrue(os.path.islink(dst_file))
            self.assert_equal(os.readlink(dst_file), file1)

    def test__replace_with_links_relative(self):
        """
        Test replacing files with relative symbolic links.
        """
        src_dir, dst_dir = self._prepare_directories()
        file1 = self._create_file(src_dir, "file1.txt", "Hello, World!")
        shutil.copy(file1, dst_dir)
        # Replace with relative symbolic links.
        common_files = create_links._find_common_files(src_dir, dst_dir)
        create_links._replace_with_links(common_files, use_relative_paths=True)
        # Verify.
        for src_file, dst_file in common_files:
            self.assertTrue(os.path.islink(dst_file))
            expected_link = os.path.relpath(src_file, os.path.dirname(dst_file))
            self.assert_equal(os.readlink(dst_file), expected_link)

    def test__stage_links(self):
        """
        Test staging symbolic links (replacing them with writable file copies).
        """
        src_dir, dst_dir = self._prepare_directories()
        file1 = self._create_file(src_dir, "file1.txt", "Hello, World!")
        link1 = os.path.join(dst_dir, "file1.txt")
        os.symlink(file1, link1)
        # Stage links by replacing them with file copies.
        symlinks = create_links._find_symlinks(dst_dir)
        create_links._stage_links(symlinks)
        # Verify.
        for link in symlinks:
            self.assertFalse(os.path.islink(link))
            self.assertTrue(os.path.isfile(link))
            self.assertTrue(filecmp.cmp(link, file1, shallow=False))


