"""
Tests for `git_branch_diff.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_branch_diff as dsggtgibrd
"""

import unittest.mock as umock
from typing import Any, Dict, List

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.git.git_branch_diff as dsggibrd

# pylint: disable=protected-access


# #############################################################################
# Test__git_diff_with_branch
# #############################################################################


class Test__git_diff_with_branch(hunitest.TestCase):
    """
    Test `_git_diff_with_branch()`.
    """

    def call(self, **overrides: Any) -> None:
        """
        Call `_git_diff_with_branch()` with default args, overridable.

        :param overrides: keyword args overriding the defaults
        """
        kwargs: Dict[str, Any] = dict(
            hash_="base_hash",
            tag="base",
            dir_name=".",
            subdir="",
            diff_type="",
            file_types="",
            skip_file_types="",
            files_filter="",
            from_file_filter="",
            only_print_files=False,
            dry_run=False,
        )
        kwargs.update(overrides)
        dsggibrd._git_diff_with_branch(**kwargs)

    def test1(self) -> None:
        """
        Test that diffing while on `master` raises `AssertionError`.
        """
        # Prepare inputs & run test and check output.
        with (
            umock.patch.object(hgit, "get_branch_name", return_value="master"),
            self.assertRaises(AssertionError),
        ):
            self.call()

    def test2(self) -> None:
        """
        Test that no matching files short-circuits before creating anything.
        """
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="HelpersTask1_Foo"
            ),
            umock.patch.object(hsystem, "system_to_files", return_value=[]),
            umock.patch.object(dsggibrd, "_get_moved_files", return_value={}),
            umock.patch.object(hio, "create_dir") as mock_create_dir,
        ):
            self.call()
        # Check outputs.
        mock_create_dir.assert_not_called()

    def test3(self) -> None:
        """
        Test that `only_print_files=True` exits before creating anything.
        """
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="HelpersTask1_Foo"
            ),
            umock.patch.object(
                hsystem, "system_to_files", return_value=["a.py"]
            ),
            umock.patch.object(dsggibrd, "_get_moved_files", return_value={}),
            umock.patch.object(hio, "create_dir") as mock_create_dir,
        ):
            self.call(only_print_files=True)
        # Check outputs.
        mock_create_dir.assert_not_called()

    def test4(self) -> None:
        """
        Test the happy path builds a vimdiff script for a matching file.
        """
        # Prepare inputs.
        dst_dir = "/tmp/myorg/myrepo/tmp.base"
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="HelpersTask1_Foo"
            ),
            umock.patch.object(
                hsystem, "system_to_files", return_value=["a.py"]
            ),
            umock.patch.object(dsggibrd, "_get_moved_files", return_value={}),
            umock.patch.object(
                hgit,
                "get_repo_full_name_from_client",
                return_value="myorg/myrepo",
            ),
            umock.patch.object(hio, "create_dir") as mock_create_dir,
            umock.patch.object(hsystem, "system", return_value=0) as mock_system,
            umock.patch.object(dsggibrd.os, "system") as mock_os_system,
            umock.patch.object(
                hio, "create_executable_script"
            ) as mock_create_script,
        ):
            self.call(dry_run=False)
        # Check outputs.
        mock_create_dir.assert_called_once_with(dst_dir, incremental=False)
        script_file_name, script_txt = mock_create_script.call_args[0]
        self.assertEqual(script_file_name, "./tmp.vimdiff_branch_with_base.sh")
        self.assertEqual(script_txt, f"vimdiff {dst_dir}/a.py /dev/null")
        # `hsystem.system()` is not used to run the vimdiff script, since it
        # pipes stdout and would break vimdiff's connection to the terminal.
        actual = "\n".join(map(str, mock_system.mock_calls))
        expected = f"""
        call('git show base_hash:a.py >{dst_dir}/a.py', abort_on_error=False)
        call('rm -rf {dst_dir}')
        """
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)
        mock_os_system.assert_called_once_with(script_file_name)

    def test5(self) -> None:
        """
        Test that a moved file is not diffed, while other files still are.
        """
        # Prepare inputs.
        dst_dir = "/tmp/myorg/myrepo/tmp.base"
        files = ["dir1/foo.py", "dir2/foo.py", "bar.py"]
        moves = {"dir1/foo.py": "dir2/foo.py"}
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="HelpersTask1_Foo"
            ),
            umock.patch.object(hsystem, "system_to_files", return_value=files),
            umock.patch.object(dsggibrd, "_get_moved_files", return_value=moves),
            umock.patch.object(
                hgit,
                "get_repo_full_name_from_client",
                return_value="myorg/myrepo",
            ),
            umock.patch.object(hio, "create_dir"),
            umock.patch.object(hsystem, "system", return_value=0),
            umock.patch.object(dsggibrd.os, "system"),
            umock.patch.object(
                hio, "create_executable_script"
            ) as mock_create_script,
        ):
            self.call(dry_run=False)
        # Check outputs.
        _, script_txt = mock_create_script.call_args[0]
        self.assertEqual(script_txt, f"vimdiff {dst_dir}/bar.py /dev/null")

    def test6(self) -> None:
        """
        Test that only moved files short-circuits before creating anything.
        """
        # Prepare inputs.
        files = ["dir1/foo.py", "dir2/foo.py"]
        moves = {"dir1/foo.py": "dir2/foo.py"}
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="HelpersTask1_Foo"
            ),
            umock.patch.object(hsystem, "system_to_files", return_value=files),
            umock.patch.object(dsggibrd, "_get_moved_files", return_value=moves),
            umock.patch.object(hio, "create_dir") as mock_create_dir,
        ):
            self.call()
        # Check outputs.
        mock_create_dir.assert_not_called()

    def helper_moves(
        self,
        files: List[str],
        moves: Dict[str, str],
        expected: str,
    ) -> None:
        """
        Run with `only_print_files=True` and check the logged `Move` lines.

        :param files: files listed by `git diff`
        :param moves: moved files returned by `_get_moved_files()`
        :param expected: expected `Move` lines, one per line
        """
        # Run test.
        only_print_files = True
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="HelpersTask1_Foo"
            ),
            umock.patch.object(hsystem, "system_to_files", return_value=files),
            umock.patch.object(dsggibrd, "_get_moved_files", return_value=moves),
            self.assertLogs(dsggibrd._LOG, level="INFO") as logs,
        ):
            self.call(only_print_files=only_print_files)
        # Check outputs.
        actual = [
            line.split(":", 2)[2] for line in logs.output if "Move" in line
        ]
        actual = "\n".join(actual)
        self.assert_equal(actual, expected, dedent=True)

    def test7(self) -> None:
        """
        Test that a move outside of the filtered files is not reported.
        """
        # Prepare inputs.
        files = ["bar.py"]
        moves = {"dir1/foo.py": "dir2/foo.py"}
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper_moves(files, moves, expected)

    def test8(self) -> None:
        """
        Test that a moved file is reported as `Move 'X' to 'Y'`.
        """
        # Prepare inputs.
        files = ["dir1/foo.py", "dir2/foo.py"]
        moves = {"dir1/foo.py": "dir2/foo.py"}
        # Prepare outputs.
        expected = """
        Move 'dir1/foo.py' to 'dir2/foo.py'
        """
        # Run test.
        self.helper_moves(files, moves, expected)

    def test9(self) -> None:
        """
        Test that added and deleted files are diffed against `/dev/null`.
        """
        # Prepare inputs.
        dst_dir = "/tmp/myorg/myrepo/tmp.base"
        # `new.py` is added (exists only in the branch), while `deleted.py` is
        # deleted (exists only in the base).
        files = ["deleted.py", "new.py"]

        def _system(cmd: str, **kwargs: Any) -> int:
            _ = kwargs
            # The added file does not exist in the base, so `git show` fails.
            rc = 1 if "new.py" in cmd else 0
            return rc

        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="HelpersTask1_Foo"
            ),
            umock.patch.object(hsystem, "system_to_files", return_value=files),
            umock.patch.object(dsggibrd, "_get_moved_files", return_value={}),
            umock.patch.object(
                hgit,
                "get_repo_full_name_from_client",
                return_value="myorg/myrepo",
            ),
            umock.patch.object(hio, "create_dir"),
            umock.patch.object(hsystem, "system", side_effect=_system),
            umock.patch.object(
                dsggibrd.os.path,
                "exists",
                side_effect=lambda f: f == "new.py",
            ),
            umock.patch.object(dsggibrd.os, "system"),
            umock.patch.object(
                hio, "create_executable_script"
            ) as mock_create_script,
        ):
            self.call(dry_run=False)
        # Check outputs.
        _, script_txt = mock_create_script.call_args[0]
        expected = f"""
        vimdiff {dst_dir}/deleted.py /dev/null
        vimdiff /dev/null new.py
        """
        self.assert_equal(script_txt, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# Test__get_moved_files
# #############################################################################


class Test__get_moved_files(hunitest.TestCase):
    """
    Test `_get_moved_files()`.
    """

    def helper(
        self, hash_: str, output: str, expected_cmd: str
    ) -> Dict[str, str]:
        """
        Call `_get_moved_files()` with a mocked `git` output.

        :param hash_: what to diff against
        :param output: mocked output of `git diff`
        :param expected_cmd: command expected to be run
        :return: moved files
        """
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, output)
        ) as mock_system_to_string:
            actual = dsggibrd._get_moved_files(hash_, ".")
        mock_system_to_string.assert_called_once_with(expected_cmd)
        return actual

    def test1(self) -> None:
        """
        Test that exact moves are parsed as `old -> new`.
        """
        # Prepare inputs.
        hash_ = "base_hash"
        output = "R100\tdir1/foo.py\tdir2/foo.py\nR100\tbar.py\tbaz.py"
        expected_cmd = (
            "cd . && git diff --name-status --find-renames=100%"
            " --diff-filter=R base_hash HEAD"
        )
        # Run test.
        actual = self.helper(hash_, output, expected_cmd)
        # Check outputs.
        expected = {"dir1/foo.py": "dir2/foo.py", "bar.py": "baz.py"}
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that no moves gives an empty mapping.
        """
        # Prepare inputs.
        hash_ = "base_hash"
        output = ""
        expected_cmd = (
            "cd . && git diff --name-status --find-renames=100%"
            " --diff-filter=R base_hash HEAD"
        )
        # Run test.
        actual = self.helper(hash_, output, expected_cmd)
        # Check outputs.
        self.assertEqual(actual, {})

    def test3(self) -> None:
        """
        Test that an empty hash diffs the working dir against `HEAD`.
        """
        # Prepare inputs.
        hash_ = ""
        output = "R100\tfoo.py\tbar.py"
        expected_cmd = (
            "cd . && git diff --name-status --find-renames=100%"
            " --diff-filter=R HEAD"
        )
        # Run test.
        actual = self.helper(hash_, output, expected_cmd)
        # Check outputs.
        self.assertEqual(actual, {"foo.py": "bar.py"})


# #############################################################################
# Test__git_diff_with_branch_wrapper
# #############################################################################


class Test__git_diff_with_branch_wrapper(hunitest.TestCase):
    """
    Test `_git_diff_with_branch_wrapper()`.
    """

    def call(self, **overrides: Any) -> None:
        """
        Call `_git_diff_with_branch_wrapper()` with default args.

        :param overrides: keyword args overriding the defaults
        """
        kwargs: Dict[str, Any] = dict(
            hash_="h",
            tag="base",
            dir_name=".",
            subdir="",
            include_submodules=False,
            diff_type="",
            file_types="",
            skip_file_types="",
            files_filter="",
            from_file_filter="",
            only_print_files=False,
            dry_run=False,
        )
        kwargs.update(overrides)
        dsggibrd._git_diff_with_branch_wrapper(**kwargs)

    def test1(self) -> None:
        """
        Test that `dir_name != "."` raises `AssertionError`.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            self.call(dir_name="subdir")

    def test2(self) -> None:
        """
        Test that `include_submodules=False` diffs only the main repo.
        """
        # Run test.
        with umock.patch.object(dsggibrd, "_git_diff_with_branch") as mock_diff:
            self.call(include_submodules=False)
        # Check outputs.
        mock_diff.assert_called_once()

    def test3(self) -> None:
        """
        Test that `include_submodules=True` also diffs an existing `amp`.
        """
        # Run test.
        with (
            umock.patch.object(dsggibrd, "_git_diff_with_branch") as mock_diff,
            umock.patch.object(hgit, "is_amp_present", return_value=True),
            umock.patch.object(hsystem, "cd") as mock_cd,
        ):
            mock_cd.return_value.__enter__ = umock.Mock(return_value=None)
            mock_cd.return_value.__exit__ = umock.Mock(return_value=False)
            self.call(include_submodules=True)
        # Check outputs.
        self.assertEqual(mock_diff.call_count, 2)

    def test4(self) -> None:
        """
        Test that `include_submodules=True` skips a missing `amp`.
        """
        # Run test.
        with (
            umock.patch.object(dsggibrd, "_git_diff_with_branch") as mock_diff,
            umock.patch.object(hgit, "is_amp_present", return_value=False),
        ):
            self.call(include_submodules=True)
        # Check outputs.
        mock_diff.assert_called_once()


# #############################################################################
# Test__resolve_target
# #############################################################################


class Test__resolve_target(hunitest.TestCase):
    """
    Test `_resolve_target()`.
    """

    def test1(self) -> None:
        """
        Test the default `target="base"` resolves to the branch point.
        """
        # Run test.
        with umock.patch.object(
            hgit, "get_branch_hash", return_value="base_hash"
        ):
            actual = dsggibrd._resolve_target("base", "", False)
        # Check outputs.
        self.assertEqual(actual, ("base_hash", "base"))

    def test2(self) -> None:
        """
        Test `target="master"` resolves to `origin/master`.
        """
        # Run test.
        actual = dsggibrd._resolve_target("master", "", False)
        # Check outputs.
        self.assertEqual(actual, ("origin/master", "origin_master"))

    def test3(self) -> None:
        """
        Test `target="head"` resolves to an empty hash.
        """
        # Run test.
        actual = dsggibrd._resolve_target("head", "", False)
        # Check outputs.
        self.assertEqual(actual, ("", "head"))

    def test4(self) -> None:
        """
        Test `last_commit=True` overrides the target to `HEAD^`.
        """
        # Run test.
        actual = dsggibrd._resolve_target("base", "", True)
        # Check outputs.
        self.assertEqual(actual, ("HEAD^", "last_commit"))

    def test5(self) -> None:
        """
        Test `target="hash"` uses the given `hash_value` verbatim.
        """
        # Run test.
        actual = dsggibrd._resolve_target("hash", "deadbeef", False)
        # Check outputs.
        self.assertEqual(actual, ("deadbeef", "hash@deadbeef"))

    def test6(self) -> None:
        """
        Test that an invalid `target` raises `AssertionError`.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dsggibrd._resolve_target("invalid", "", False)

    def test7(self) -> None:
        """
        Test that `target="hash"` without `hash_value` raises.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dsggibrd._resolve_target("hash", "", False)

    def test8(self) -> None:
        """
        Test that `hash_value` with `target="base"` raises.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dsggibrd._resolve_target("base", "deadbeef", False)


# #############################################################################
# Test_git_branch_diff_py
# #############################################################################


class Test_git_branch_diff_py(hunitest.TestCase):
    """
    End-to-end smoke test for the `git_branch_diff.py` executable.
    """

    def test1(self) -> None:
        """
        Test that `--help` runs successfully.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("git_branch_diff.py")
        cmd = f"{exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
