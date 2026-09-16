"""
Tests for `git_branch_subset_copy.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_branch_subset_copy as dsggtgibsc
"""

import os
import unittest.mock as umock
from typing import Any

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.git.git_branch_subset_copy as dsggibsc

# pylint: disable=protected-access


# #############################################################################
# Test__copy_branch_subset
# #############################################################################


class Test__copy_branch_subset(hunitest.TestCase):
    """
    Test `_copy_branch_subset()`.
    """

    def helper(self, orig_dir: str, *args: Any, **kwargs: Any) -> None:
        """
        `cd` into `orig_dir` and run `_copy_branch_subset()`.

        The function under test captures `original_dir = os.getcwd()`
        and `os.chdir()`s into `dst_dir`, restoring `original_dir` in a
        `finally`; this real (not mocked) `chdir` dance is replicated
        here so `original_dir`, and any relative path resolved against
        it, matches `orig_dir`. The real process cwd (captured before
        `chdir`) is always restored, even on failure, so the test
        process does not leak a `cwd` change into later tests.

        :param orig_dir: directory to `chdir()` into before the call,
            standing in for the caller's real working directory
        """
        real_cwd = os.getcwd()
        try:
            os.chdir(orig_dir)
            dsggibsc._copy_branch_subset(*args, **kwargs)
        finally:
            os.chdir(real_cwd)

    def test1(self) -> None:
        """
        Test that missing both `from_file` and `--pr` raises.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dsggibsc._copy_branch_subset(dst_dir=self.get_scratch_space())
        actual = str(cm.exception)
        self.assertIn("from_file or --pr must be provided", actual)

    def test2(self) -> None:
        """
        Test that a missing `dst_dir` raises.
        """
        # Prepare inputs.
        from_file = os.path.join(self.get_scratch_space(), "files.txt")
        hio.to_file(from_file, "a.py\n")
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dsggibsc._copy_branch_subset(from_file=from_file)
        actual = str(cm.exception)
        self.assertIn("dst_dir must be provided", actual)

    def test3(self) -> None:
        """
        Test the happy path: checkout, branch creation, and file copy.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dst_dir = os.path.join(scratch_dir, "dst")
        hio.create_dir(dst_dir, incremental=True)
        orig_dir = os.path.join(scratch_dir, "orig")
        hio.create_dir(orig_dir, incremental=True)
        from_file = os.path.join(orig_dir, "files.txt")
        hio.to_file(from_file, "a.py\nb.py\n")
        branch_name = "HelpersTask1_Foo_2"
        # Prepare outputs.
        expected = f"""
        call('git checkout master', suppress_output=False)
        call("invoke git_branch_create --branch-name '{branch_name}'", suppress_output=False)
        call('copy_across_clients.py --dir1 {orig_dir} --dir2 {dst_dir} --from_file {from_file}')
        """
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_next_name", return_value=branch_name
            ),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            self.helper(orig_dir, from_file=from_file, dst_dir=dst_dir)
        # Check outputs.
        actual = "\n".join(
            str(umock.call(*c["args"], **c["kwargs"])) for c in sys_calls
        )
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test4(self) -> None:
        """
        Test that `--pr` mode also copies the `pr<NUM>.pytest.sh` script.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dst_dir = os.path.join(scratch_dir, "dst")
        hio.create_dir(dst_dir, incremental=True)
        orig_dir = os.path.join(scratch_dir, "orig")
        hio.create_dir(orig_dir, incremental=True)
        pr = 17
        # `_copy_branch_subset()` reads `from_file` (its basename, once
        # overridden by `--pr`) both before `chdir(dst_dir)` (relative to
        # `orig_dir`) and after (relative to `dst_dir`), so the fixture
        # file must exist in both places.
        from_file_name = f"pr{pr}.files.txt"
        hio.to_file(os.path.join(orig_dir, from_file_name), "a.py\n")
        hio.to_file(os.path.join(dst_dir, from_file_name), "a.py\n")
        pytest_src = os.path.join(orig_dir, f"pr{pr}.pytest.sh")
        hio.to_file(pytest_src, "pytest a.py\n")
        branch_name = "gp_scratch_1"
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_next_name", return_value=branch_name
            ),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            self.helper(orig_dir, pr=pr, dst_dir=dst_dir)
        # Check outputs.
        actual_calls = "\n".join(str(c["args"]) for c in sys_calls)
        # `gp_scratch*` branches skip the naming-convention check.
        self.assertIn("--no-check-branch-name", actual_calls)
        sys_call_fns = [c["function"] for c in sys_calls]
        self.assert_equal(str(sys_call_fns), str(["hsystem.system"] * 4))
        pytest_dst = os.path.join(dst_dir, f"pr{pr}.pytest.sh")
        self.assertEqual(
            sys_calls[3]["args"], (f"cp {pytest_src} {pytest_dst}",)
        )

    def test5(self) -> None:
        """
        Test that `dry_run=True` skips checkout, branch creation, and
        file copy.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dst_dir = os.path.join(scratch_dir, "dst")
        hio.create_dir(dst_dir, incremental=True)
        orig_dir = os.path.join(scratch_dir, "orig")
        hio.create_dir(orig_dir, incremental=True)
        from_file = os.path.join(orig_dir, "files.txt")
        hio.to_file(from_file, "a.py\n")
        branch_name = "HelpersTask1_Foo_2"
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_next_name", return_value=branch_name
            ),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            self.helper(
                orig_dir,
                from_file=from_file,
                dst_dir=dst_dir,
                dry_run=True,
            )
        # Check outputs.
        self.assertEqual(sys_calls, [])


# #############################################################################
# Test_git_branch_subset_copy_py
# #############################################################################


class Test_git_branch_subset_copy_py(hunitest.TestCase):
    """
    End-to-end smoke test for the `git_branch_subset_copy.py` executable.
    """

    def test1(self) -> None:
        """
        Test that `--help` runs successfully.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("git_branch_subset_copy.py")
        cmd = f"{exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
