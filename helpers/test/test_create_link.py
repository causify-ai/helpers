import filecmp
import os
import pathlib
import shutil
from typing import List, Tuple

import helpers.create_links as hcrelink
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_create_links
# #############################################################################


class Test_create_links(hunitest.TestCase):
    """
    Unit tests for the `create_links.py` script.
    """

    def test__find_common_files(self) -> None:
        """
        Test identifying common files between two directories.

        Create two directories, each containing identical files,
        and checks that the `_find_common_files` function identifies these files.
        """
        base_dir: pathlib.Path = pathlib.Path(self.get_scratch_space())
        src_dir: pathlib.Path = base_dir / "test_src_dir"
        dst_dir: pathlib.Path = base_dir / "test_dst_dir"
        src_dir.mkdir(parents=True, exist_ok=True)
        dst_dir.mkdir(parents=True, exist_ok=True)
        file1_src: pathlib.Path = self._create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        file1_dst: pathlib.Path = shutil.copy(file1_src, dst_dir)
        common_files: List[Tuple[str, str]] = hcrelink._find_common_files(
            str(src_dir), str(dst_dir)
        )
        self.assertEqual(len(common_files), 1)
        self.assertEqual(common_files[0], (str(file1_src), str(file1_dst)))

    def test__replace_with_links_absolute(self) -> None:
        """
        Test replacing common files with absolute symbolic links.

        Create identical files in two directories and replace the files
        in the destination directory with absolute symbolic links
        pointing to the source files.
        """
        base_dir: pathlib.Path = pathlib.Path(self.get_scratch_space())
        src_dir: pathlib.Path = base_dir / "test_src_dir"
        dst_dir: pathlib.Path = base_dir / "test_dst_dir"
        file1: pathlib.Path = self._create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        shutil.copy(file1, dst_dir)
        common_files: List[Tuple[str, str]] = hcrelink._find_common_files(
            str(src_dir), str(dst_dir)
        )
        hcrelink._replace_with_links(common_files, use_relative_paths=False)
        for _, dst_file in common_files:
            self.assertTrue(os.path.islink(dst_file))
            self.assert_equal(os.readlink(dst_file), str(file1))

    def test__replace_with_links_relative(self) -> None:
        """
        Test replacing common files with relative symbolic links.

        Create identical files in two directories and replace the files
        in the destination directory with relative symbolic links
        pointing to the source files.
        """
        base_dir: pathlib.Path = pathlib.Path(self.get_scratch_space())
        src_dir: pathlib.Path = base_dir / "test_src_dir"
        dst_dir: pathlib.Path = base_dir / "test_dst_dir"
        file1: pathlib.Path = self._create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        shutil.copy(file1, dst_dir)
        common_files: List[Tuple[str, str]] = hcrelink._find_common_files(
            src_dir, dst_dir
        )
        hcrelink._replace_with_links(common_files, use_relative_paths=True)
        for src_file, dst_file in common_files:
            self.assertTrue(os.path.islink(dst_file))
            expected_link: str = os.path.relpath(
                src_file, os.path.dirname(dst_file)
            )
            self.assert_equal(os.readlink(dst_file), expected_link)

    def test__stage_links(self) -> None:
        """
        Test replacing symbolic links with writable file copies.

        Create symbolic links in a directory and then stage them by
        replacing each link with a copy of the original file it points
        to.
        """
        base_dir: pathlib.Path = pathlib.Path(self.get_scratch_space())
        src_dir: pathlib.Path = base_dir / "test_src_dir"
        dst_dir: pathlib.Path = base_dir / "test_dst_dir"
        src_dir.mkdir(parents=True, exist_ok=True)
        dst_dir.mkdir(parents=True, exist_ok=True)
        file1: pathlib.Path = self._create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        link1: pathlib.Path = dst_dir / "file1.txt"
        os.symlink(file1, link1)
        symlinks: List[str] = hcrelink._find_symlinks(dst_dir)
        hcrelink._stage_links(symlinks)
        for link in symlinks:
            self.assertFalse(os.path.islink(link))
            self.assertTrue(os.path.isfile(link))
            self.assertTrue(filecmp.cmp(link, file1, shallow=False))

    def _create_file(
        self, dir_path: pathlib.Path, file_name: str, content: str
    ) -> pathlib.Path:
        """
        Create a file with the given content in the specified directory.

        This helper function ensures the directory exists before
        creating the file and writing the specified content into it.

        :param dir_path: path to the directory where the file will be
            created
        :param file_name: name of the file to create
        :param content: content to write into the file
        :return: full path to the created file
        """
        dir_path = pathlib.Path(dir_path)
        file_path = dir_path / file_name
        hio.to_file(file_name=str(file_path), txt=content)
        return file_path
