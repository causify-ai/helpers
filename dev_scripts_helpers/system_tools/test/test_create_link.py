import filecmp
import os
import shutil
from typing import List, Tuple
from unittest import mock

import pytest

import dev_scripts_helpers.system_tools.create_links as dshstcrli
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_create_links
# #############################################################################


class Test_create_links(hunitest.TestCase):
    """
    Unit tests for the `create_links.py` script.
    """

    def create_file(
        self, dir_path: str, file_name: str, content: str
    ) -> str:
        """
        Create a file with the given content in the specified directory.

        This helper function ensures the directory exists before creating the
        file and writing the specified content into it.

        :param dir_path: path to the directory where the file will be created
        :param file_name: name of the file to create
        :param content: content to write into the file
        :return: full path to the created file
        """
        file_path = os.path.join(dir_path, file_name)
        hio.to_file(file_name=file_path, txt=content)
        return file_path

    def test__find_common_files(self) -> None:
        """
        Test identifying common files between two directories.

        Create two directories, each containing identical files,
        and checks that the `_find_common_files` function identifies these files.
        """
        base_dir: str = self.get_scratch_space()
        src_dir: str = os.path.join(base_dir, "test_src_dir")
        dst_dir: str = os.path.join(base_dir, "test_dst_dir")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dst_dir, exist_ok=True)
        file1_src: str = self.create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        file1_dst: str = shutil.copy(file1_src, dst_dir)
        common_files: List[Tuple[str, str]] = dshstcrli._find_common_files(
            src_dir, dst_dir
        )
        self.assertEqual(len(common_files), 1)
        self.assertEqual(common_files[0], (file1_src, file1_dst))

    def test__replace_with_links_absolute(self) -> None:
        """
        Test replacing common files with absolute symbolic links.

        Create identical files in two directories and replace the files in the
        destination directory with absolute symbolic links pointing to the source
        files.
        """
        base_dir: str = self.get_scratch_space()
        src_dir: str = os.path.join(base_dir, "test_src_dir")
        dst_dir: str = os.path.join(base_dir, "test_dst_dir")
        file1: str = self.create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        shutil.copy(file1, dst_dir)
        common_files: List[Tuple[str, str]] = dshstcrli._find_common_files(
            src_dir, dst_dir
        )
        dshstcrli._replace_with_links(common_files, link_type="absolute")
        for _, dst_file in common_files:
            self.assertTrue(os.path.islink(dst_file))
            self.assert_equal(os.readlink(dst_file), file1)

    def test__replace_with_links_relative(self) -> None:
        """
        Test replacing common files with relative symbolic links.

        Create identical files in two directories and replace the files in the
        destination directory with relative symbolic links pointing to the source
        files.
        """
        base_dir: str = self.get_scratch_space()
        src_dir: str = os.path.join(base_dir, "test_src_dir")
        dst_dir: str = os.path.join(base_dir, "test_dst_dir")
        file1: str = self.create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        shutil.copy(file1, dst_dir)
        common_files: List[Tuple[str, str]] = dshstcrli._find_common_files(
            src_dir, dst_dir
        )
        dshstcrli._replace_with_links(common_files, link_type="relative")
        for src_file, dst_file in common_files:
            self.assertTrue(os.path.islink(dst_file))
            expected_link: str = os.path.relpath(
                src_file, os.path.dirname(dst_file)
            )
            self.assert_equal(os.readlink(dst_file), expected_link)

    def test__stage_links(self) -> None:
        """
        Test replacing symbolic links with writable file copies.

        Create symbolic links in a directory and then stage them by replacing
        each link with a copy of the original file it points to.
        """
        base_dir: str = self.get_scratch_space()
        src_dir: str = os.path.join(base_dir, "test_src_dir")
        dst_dir: str = os.path.join(base_dir, "test_dst_dir")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dst_dir, exist_ok=True)
        file1: str = self.create_file(
            src_dir, "file1.txt", "Hello, World!"
        )
        link1: str = os.path.join(dst_dir, "file1.txt")
        os.symlink(file1, link1)
        symlinks: List[str] = dshstcrli._find_symlinks(dst_dir)
        dshstcrli._stage_links(symlinks)
        for link in symlinks:
            self.assertFalse(os.path.islink(link))
            self.assertTrue(os.path.isfile(link))
            self.assertTrue(filecmp.cmp(link, file1, shallow=False))


# #############################################################################
# Test_create_links_py
# #############################################################################


class Test_create_links_py(hunitest.TestCase):
    """
    End-to-end tests for the `create_links.py` executable.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        """
        Setup and teardown for each test.
        """
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Save the current working directory before the test runs.
        """
        self._original_cwd = os.getcwd()

    def tear_down_test(self) -> None:
        """
        Restore the working directory saved by `set_up_test()`.
        """
        os.chdir(self._original_cwd)

    def _create_dirs(self, base_dir: str) -> Tuple[str, str]:
        """
        Create the `src_dir`/`dst_dir` fixture shared by the tests below.

        `src_dir` contains `file1.txt`, `file2.txt`, and `subdir/file3.txt`.
        `dst_dir` contains copies of only `file1.txt` and `file2.txt`, so
        both are candidates for `--replace_links`, while `subdir/file3.txt`
        exercises the "missing from `dst_dir`" case.

        :param base_dir: scratch directory to create the dirs under
        :return: `(src_dir, dst_dir)`
        """
        src_dir = os.path.join(base_dir, "src_dir")
        dst_dir = os.path.join(base_dir, "dst_dir")
        hio.to_file(os.path.join(src_dir, "file1.txt"), "content1")
        hio.to_file(os.path.join(src_dir, "file2.txt"), "content2")
        hio.to_file(os.path.join(src_dir, "subdir", "file3.txt"), "content3")
        hio.create_dir(dst_dir, incremental=True)
        shutil.copy(os.path.join(src_dir, "file1.txt"), dst_dir)
        shutil.copy(os.path.join(src_dir, "file2.txt"), dst_dir)
        return src_dir, dst_dir

    def _get_dir_state(self, dir_path: str) -> str:
        """
        Freeze the state of `dir_path` into a deterministic string.

        For each file report whether it is a symlink (its link type and whether
        it resolves) or a regular file, together with its content. Reporting the
        link type/resolution instead of the raw `os.readlink()` target keeps the
        frozen state stable across machines and scratch-dir locations.

        :param dir_path: directory to inspect
        :return: one line per file, sorted by relative path, e.g. `file1.txt:
            symlink (relative, resolves) content='content1'`
        """
        rows: List[Tuple[str, str]] = []
        for root, _, files in os.walk(dir_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, dir_path)
                if os.path.islink(file_path):
                    target = os.readlink(file_path)
                    if os.path.isabs(target):
                        link_type = "absolute"
                        resolved_target = target
                    else:
                        link_type = "relative"
                        resolved_target = os.path.join(
                            os.path.dirname(file_path), target
                        )
                    if os.path.exists(resolved_target):
                        resolution = "resolves"
                        content = hio.from_file(resolved_target)
                    else:
                        resolution = "missing"
                        content = ""
                    kind = f"symlink ({link_type}, {resolution})"
                else:
                    kind = "file"
                    content = hio.from_file(file_path)
                rows.append(
                    (rel_path, f"{rel_path}: {kind} content='{content}'")
                )
        rows.sort(key=lambda row: row[0])
        return "\n".join(line for _, line in rows)

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `dshstcrli._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshstcrli._parse()
        with mock.patch("sys.argv", argv):
            dshstcrli._main(parser)

    def test1(self) -> None:
        """Test `--replace_links --link_type relative` turns the files common to
        `src_dir`/`dst_dir` into relative symlinks resolving to `src_dir`'s
        content.
        """
        # Prepare inputs.
        base_dir = self.get_scratch_space()
        src_dir, dst_dir = self._create_dirs(base_dir)
        argv = [
            "create_links.py",
            "--src_dir",
            src_dir,
            "--dst_dir",
            dst_dir,
            "--replace_links",
            "--link_type",
            "relative",
        ]
        # Prepare outputs.
        expected = """
        file1.txt: symlink (relative, resolves) content='content1'
        file2.txt: symlink (relative, resolves) content='content2'
        """
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = self._get_dir_state(dst_dir)
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """Test `--replace_links --link_type absolute` turns the files common to
        `src_dir`/`dst_dir` into absolute symlinks resolving to `src_dir`'s
        content.
        """
        # Prepare inputs.
        base_dir = self.get_scratch_space()
        src_dir, dst_dir = self._create_dirs(base_dir)
        argv = [
            "create_links.py",
            "--src_dir",
            src_dir,
            "--dst_dir",
            dst_dir,
            "--replace_links",
            "--link_type",
            "absolute",
        ]
        # Prepare outputs.
        expected = """
        file1.txt: symlink (absolute, resolves) content='content1'
        file2.txt: symlink (absolute, resolves) content='content2'
        """
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = self._get_dir_state(dst_dir)
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """Test `--stage_links` replaces the relative symlinks created by
        `--replace_links` with writable copies matching `src_dir`'s content.
        """
        # Prepare inputs.
        base_dir = self.get_scratch_space()
        src_dir, dst_dir = self._create_dirs(base_dir)
        replace_argv = [
            "create_links.py",
            "--src_dir",
            src_dir,
            "--dst_dir",
            dst_dir,
            "--replace_links",
            "--link_type",
            "relative",
        ]
        self._run_main(replace_argv)
        stage_argv = ["create_links.py", "--src_dir", dst_dir, "--stage_links"]
        # Prepare outputs.
        expected = """
        file1.txt: file content='content1'
        file2.txt: file content='content2'
        """
        # Run test.
        self._run_main(stage_argv)
        # Check outputs.
        actual = self._get_dir_state(dst_dir)
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test `--stage_links` resolves relative symlinks relative to each link's
        own directory, not the process's current working directory.

        Regression test for a bug where `_stage_links()` checked
        `os.path.exists()` on the raw `os.readlink()` target, which is only
        correct when the process's current directory equals the symlink's own
        directory.
        """
        # Prepare inputs.
        base_dir = self.get_scratch_space()
        src_dir, dst_dir = self._create_dirs(base_dir)
        replace_argv = [
            "create_links.py",
            "--src_dir",
            src_dir,
            "--dst_dir",
            dst_dir,
            "--replace_links",
            "--link_type",
            "relative",
        ]
        self._run_main(replace_argv)
        stage_argv = ["create_links.py", "--src_dir", dst_dir, "--stage_links"]
        # Prepare outputs.
        expected = """
        file1.txt: file content='content1'
        file2.txt: file content='content2'
        """
        # Run test.
        # Move to a directory unrelated to `dst_dir` before staging, so
        # relative-symlink resolution cannot accidentally rely on the
        # process's current working directory.
        elsewhere_dir = os.path.join(base_dir, "elsewhere")
        hio.create_dir(elsewhere_dir, incremental=True)
        os.chdir(elsewhere_dir)
        self._run_main(stage_argv)
        # Check outputs.
        actual = self._get_dir_state(dst_dir)
        self.assert_equal(actual, expected, dedent=True)
