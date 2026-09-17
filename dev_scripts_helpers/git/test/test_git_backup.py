"""
Tests for `git_backup.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_backup as dsggtgibac
"""

import os
import unittest.mock as umock

import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.git.git_backup as dsggibac

# pylint: disable=protected-access


# #############################################################################
# Test__collect_backup_files
# #############################################################################


class Test__collect_backup_files(hunitest.TestCase):
    """
    Test `_collect_backup_files()`.
    """

    def test1(self) -> None:
        """
        Test that main-repo files are collected when there are no submodules.
        """
        # Prepare inputs.
        file_mode = "all"
        include_subrepos = True
        # Prepare outputs.
        expected = [(".", "a.py"), (".", "b.py")]
        # Run test.
        with (
            umock.patch.object(
                hgit,
                "get_modified_and_untracked_files",
                return_value=["a.py", "b.py"],
            ),
            umock.patch.object(
                dsggibac.hltltagi, "_get_submodule_paths", return_value=[]
            ),
        ):
            actual = dsggibac._collect_backup_files(
                file_mode, include_subrepos
            )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test that `include_subrepos=False` skips submodule collection.
        """
        # Prepare inputs.
        file_mode = "all"
        include_subrepos = False
        # Prepare outputs.
        expected = [(".", "a.py")]
        # Run test.
        with (
            umock.patch.object(
                hgit,
                "get_modified_and_untracked_files",
                return_value=["a.py"],
            ),
            umock.patch.object(
                dsggibac.hltltagi, "_get_submodule_paths"
            ) as mock_get_submodule_paths,
        ):
            actual = dsggibac._collect_backup_files(
                file_mode, include_subrepos
            )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))
        mock_get_submodule_paths.assert_not_called()

    def test3(self) -> None:
        """
        Test that submodule files are prefixed with their submodule path.
        """
        # Prepare inputs.
        file_mode = "modified"
        include_subrepos = True
        submodule_path = self.get_scratch_space()
        files_by_dir = {".": ["a.py"], submodule_path: ["c.py"]}
        # Prepare outputs.
        expected = [(".", "a.py"), (submodule_path, "c.py")]
        # Run test.
        with (
            umock.patch.object(
                hgit,
                "get_modified_and_untracked_files",
                side_effect=lambda dir_name, mode: files_by_dir[dir_name],
            ),
            umock.patch.object(
                dsggibac.hltltagi,
                "_get_submodule_paths",
                return_value=[submodule_path],
            ),
        ):
            actual = dsggibac._collect_backup_files(
                file_mode, include_subrepos
            )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test__create_backup
# #############################################################################


class Test__create_backup(hunitest.TestCase):
    """
    Test `_create_backup()`.
    """

    def test1(self) -> None:
        """
        Test that an invalid `file_mode` raises `AssertionError`.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dsggibac._create_backup(file_mode="invalid")

    def test2(self) -> None:
        """
        Test that no collected files skips creating a zip file entirely.
        """
        # Prepare inputs.
        backup_dir = self.get_scratch_space()
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_client_root", return_value="/repo"
            ),
            umock.patch.object(
                dsggibac, "_collect_backup_files", return_value=[]
            ),
            umock.patch("zipfile.ZipFile") as mock_zip,
        ):
            dsggibac._create_backup(backup_dir=backup_dir)
        # Check outputs.
        mock_zip.assert_not_called()

    def test3(self) -> None:
        """
        Test that `dry_run=True` skips creating a zip file.
        """
        # Prepare inputs.
        backup_dir = self.get_scratch_space()
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_client_root", return_value="/repo"
            ),
            umock.patch.object(
                dsggibac,
                "_collect_backup_files",
                return_value=[(".", "a.py")],
            ),
            umock.patch("zipfile.ZipFile") as mock_zip,
        ):
            dsggibac._create_backup(backup_dir=backup_dir, dry_run=True)
        # Check outputs.
        mock_zip.assert_not_called()

    def test4(self) -> None:
        """
        Test the happy path zips every collected file under its arcname.
        """
        # Prepare inputs.
        backup_dir = self.get_scratch_space()
        all_files = [(".", "a.py"), ("helpers_root", "b.py")]
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_client_root", return_value="/repo"
            ),
            umock.patch.object(
                dsggibac, "_collect_backup_files", return_value=all_files
            ),
            umock.patch("zipfile.ZipFile") as mock_zip,
        ):
            mock_zipf = mock_zip.return_value.__enter__.return_value
            dsggibac._create_backup(backup_dir=backup_dir)
        # Check outputs.
        mock_zip.assert_called_once()
        actual = str(list(mock_zipf.write.call_args_list))
        expected = str(
            [
                umock.call(os.path.join(".", "a.py"), arcname="a.py"),
                umock.call(
                    os.path.join("helpers_root", "b.py"),
                    arcname=os.path.join("helpers_root", "b.py"),
                ),
            ]
        )
        self.assert_equal(actual, expected)


# #############################################################################
# Test_git_backup_py
# #############################################################################


class Test_git_backup_py(hunitest.TestCase):
    """
    End-to-end smoke test for the `git_backup.py` executable.
    """

    def test1(self) -> None:
        """
        Test that `--help` runs successfully.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("git_backup.py")
        cmd = f"{exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
