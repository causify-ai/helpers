import os
import shutil
import filecmp
import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest
import helpers.hunit_test as hut
import helpers.create_links as create_links


class Test_create_links(hut.TestCase):
    """
    Unit tests for the `create_links.py` script.
    """

    def _create_file(self, dir_path: Path, file_name: str, content: str) -> Path:
        """
        Create a file with the given content in the specified directory.

        This helper function ensures the directory exists before creating the
        file and writing the specified content into it.

        :param dir_path: path to the directory where the file will be created
        :param file_name: name of the file to create
        :param content: content to write into the file
        :return: full path to the created file
        """
        dir_path = Path(dir_path)
        file_path = dir_path / file_name
        dir_path.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def test__find_common_files(self) -> None:
        """
        Test identifying common files between two directories.

        Create two directories, each containing identical files,
        and checks that the `_find_common_files` function identifies these files.

        :return: None
        """
        cwd: Path = Path.cwd()
        src_dir: Path = cwd / "test_src_dir"
        dst_dir: Path = cwd / "test_dst_dir"
        try:
            src_dir.mkdir(parents=True, exist_ok=True)
            dst_dir.mkdir(parents=True, exist_ok=True)
            file1_src: Path = self._create_file(src_dir, "file1.txt", "Hello, World!")
            file1_dst: Path = shutil.copy(file1_src, dst_dir)
            common_files: List[Tuple[str, str]] = create_links._find_common_files(
                str(src_dir), str(dst_dir)
            )
            self.assertEqual(len(common_files), 1)
            self.assertEqual(common_files[0], (str(file1_src), str(file1_dst)))
        finally:
            shutil.rmtree(src_dir, ignore_errors=True)
            shutil.rmtree(dst_dir, ignore_errors=True)

    def test__replace_with_links_absolute(self) -> None:
        """
        Test replacing common files with absolute symbolic links.

        Create identical files in two directories and replace the
        files in the destination directory with absolute symbolic links pointing
        to the source files.

        :return: None
        """
        with tempfile.TemporaryDirectory(prefix="test_src_") as src_dir, \
             tempfile.TemporaryDirectory(prefix="test_dst_") as dst_dir:
            file1: Path = self._create_file(src_dir, "file1.txt", "Hello, World!")
            shutil.copy(file1, dst_dir)
            common_files: List[Tuple[str, str]] = create_links._find_common_files(
                str(src_dir), str(dst_dir)
            )
            create_links._replace_with_links(common_files, use_relative_paths=False)
            for _, dst_file in common_files:
                self.assertTrue(os.path.islink(dst_file))
                self.assert_equal(os.readlink(dst_file), str(file1))

    def test__replace_with_links_relative(self) -> None:
        """
        Test replacing common files with relative symbolic links.

        Create identical files in two directories and replace the
        files in the destination directory with relative symbolic links pointing
        to the source files.

        :return: None
        """
        with tempfile.TemporaryDirectory(prefix="test_src_") as src_dir, \
             tempfile.TemporaryDirectory(prefix="test_dst_") as dst_dir:
            file1: Path = self._create_file(src_dir, "file1.txt", "Hello, World!")
            shutil.copy(file1, dst_dir)

            common_files: List[Tuple[str, str]] = create_links._find_common_files(
                src_dir, dst_dir
            )
            create_links._replace_with_links(common_files, use_relative_paths=True)
            for src_file, dst_file in common_files:
                self.assertTrue(os.path.islink(dst_file))
                expected_link: str = os.path.relpath(src_file, os.path.dirname(dst_file))
                self.assert_equal(os.readlink(dst_file), expected_link)

    def test__stage_links(self) -> None:
        """
        Test replacing symbolic links with writable file copies.

        Create symbolic links in a directory and then stage them by
        replacing each link with a copy of the original file it points to.

        :return: None
        """
        with tempfile.TemporaryDirectory(prefix="test_src_") as src_dir, \
             tempfile.TemporaryDirectory(prefix="test_dst_") as dst_dir:
            file1: Path = self._create_file(src_dir, "file1.txt", "Hello, World!")
            link1: str = os.path.join(dst_dir, "file1.txt")
            os.symlink(file1, link1)
            symlinks: List[str] = create_links._find_symlinks(dst_dir)
            create_links._stage_links(symlinks)
            for link in symlinks:
                self.assertFalse(os.path.islink(link))
                self.assertTrue(os.path.isfile(link))
                self.assertTrue(filecmp.cmp(link, file1, shallow=False))
