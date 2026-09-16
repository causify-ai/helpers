import unittest.mock as umock
from typing import Tuple

import pytest

import helpers.hgit as hgit
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_gh as hltltagh
import helpers.lib_tasks.lib_tasks_git as hltltagi
import helpers.lib_tasks.test.test_lib_tasks as httestlib

# pylint: disable=protected-access


# #############################################################################
# Test_git_patch_create
# #############################################################################


@pytest.mark.slow(reason="Around 7s")
@pytest.mark.skipif(
    not hgit.is_in_amp_as_supermodule(),
    reason="Run only in amp as super-module",
)
class Test_git_patch_create(hunitest.TestCase):
    """
    Test `git_patch_create()`.
    """

    def helper(
        self,
        mode: str,
        modified: bool,
        branch: bool,
        last_commit: bool,
        files: str,
        fetch_origin: bool = False,
    ) -> None:
        """
        Helper for `git_patch_create()`.

        :param mode: "tar" or "diff"
        :param modified: test modified files
        :param branch: test branch mode
        :param last_commit: test last commit mode
        :param files: specific files to test
        :param fetch_origin: whether to fetch origin master first
        """
        if fetch_origin:
            hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test1(self) -> None:
        """
        Test modified files mode with tar.
        """
        # Prepare inputs.
        mode = "tar"
        modified = True
        branch = False
        last_commit = False
        files = ""
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files, fetch_origin=True)

    def test2(self) -> None:
        """
        Test modified files mode with diff.
        """
        # Prepare inputs.
        mode = "diff"
        modified = True
        branch = False
        last_commit = False
        files = ""
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files, fetch_origin=True)

    def test3(self) -> None:
        """
        Test branch mode with tar.
        """
        # Prepare inputs.
        mode = "tar"
        modified = False
        branch = True
        last_commit = False
        files = ""
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files)

    def test4(self) -> None:
        """
        Test branch mode with diff.
        """
        # Prepare inputs.
        mode = "diff"
        modified = False
        branch = True
        last_commit = False
        files = ""
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files)

    def test5(self) -> None:
        """
        Test last commit mode with tar.
        """
        # Prepare inputs.
        mode = "tar"
        modified = False
        branch = False
        last_commit = True
        files = ""
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files, fetch_origin=True)

    def test6(self) -> None:
        """
        Test last commit mode with diff.
        """
        # Prepare inputs.
        mode = "diff"
        modified = False
        branch = False
        last_commit = True
        files = ""
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files, fetch_origin=True)

    def test7(self) -> None:
        """
        Test with specific files using tar.
        """
        # Prepare inputs.
        mode = "tar"
        modified = True
        branch = False
        last_commit = False
        files = __file__
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files, fetch_origin=True)

    def test8(self) -> None:
        """
        Test with specific files using diff.
        """
        # Prepare inputs.
        mode = "diff"
        modified = True
        branch = False
        last_commit = False
        files = __file__
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files, fetch_origin=True)

    def test9(self) -> None:
        """
        Test with all flags False raises AssertionError.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "diff"
        modified = False
        branch = False
        last_commit = False
        files = __file__
        # Prepare outputs.
        expected = """
        * Failed assertion *
        '0'
        ==
        '1'
        Specify only one among --modified, --branch, --last-commit
        """
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hltltagi.git_patch_create(
                ctx, mode, modified, branch, last_commit, files
            )
        actual = str(cm.exception)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test10(self) -> None:
        """
        Test with multiple files using tar.
        """
        # Prepare inputs.
        mode = "tar"
        modified = True
        branch = False
        last_commit = False
        files = f"{__file__} {__file__}"
        # Run test and check outputs.
        self.helper(mode, modified, branch, last_commit, files, fetch_origin=True)


# #############################################################################
# Test__get_branch_name_for_issue
# #############################################################################


class Test__get_branch_name_for_issue(hunitest.TestCase):
    """
    Test `_get_branch_name_for_issue()`.
    """

    def helper(
        self,
        issue_id: int,
        repo_short_name: str,
        suffix: str,
        base_branch_name: str,
        next_branch_name: str,
        expected: str,
    ) -> Tuple[umock.MagicMock, umock.MagicMock]:
        """
        Helper for `_get_branch_name_for_issue()`.

        Mock `_get_gh_issue_title()` and `get_branch_next_name()`, run the
        function under test, and check its output.

        :param issue_id: GitHub issue number
        :param repo_short_name: short name of the repo
        :param suffix: explicit suffix, or "" to auto-pick one
        :param base_branch_name: branch name returned by
            `_get_gh_issue_title()`
        :param next_branch_name: branch name returned by
            `get_branch_next_name()`
        :param expected: expected output of `_get_branch_name_for_issue()`
        :return: mocks for `_get_gh_issue_title()` and
            `get_branch_next_name()`, so that callers can assert on how
            they were called
        """
        # Run test.
        with (
            umock.patch.object(
                hltltagh,
                "_get_gh_issue_title",
                return_value=(base_branch_name, "url"),
            ) as mock_get_title,
            umock.patch.object(
                hgit,
                "get_branch_next_name",
                return_value=next_branch_name,
            ) as mock_get_next_name,
        ):
            actual = hltltagi._get_branch_name_for_issue(
                issue_id, repo_short_name, suffix
            )
        # Check outputs.
        self.assert_equal(actual, expected)
        return mock_get_title, mock_get_next_name

    def test1(self) -> None:
        """
        Test that an omitted suffix auto-picks the next free one.
        """
        # Prepare inputs.
        issue_id = 123
        repo_short_name = "current"
        suffix = ""
        base_branch_name = "HelpersTask123_Fix_bug"
        next_branch_name = "HelpersTask123_Fix_bug_3"
        # Prepare outputs.
        expected = "HelpersTask123_Fix_bug_3"
        # Run test and check outputs.
        mock_get_title, mock_get_next_name = self.helper(
            issue_id,
            repo_short_name,
            suffix,
            base_branch_name,
            next_branch_name,
            expected,
        )
        mock_get_title.assert_called_once_with(issue_id, repo_short_name)
        mock_get_next_name.assert_called_once_with(
            curr_branch_name=base_branch_name
        )

    def test2(self) -> None:
        """
        Test that an explicit suffix is appended without auto-picking one.
        """
        # Prepare inputs.
        issue_id = 123
        repo_short_name = "current"
        suffix = "02"
        base_branch_name = "HelpersTask123_Fix_bug"
        next_branch_name = ""
        # Prepare outputs.
        expected = "HelpersTask123_Fix_bug_02"
        # Run test and check outputs.
        _, mock_get_next_name = self.helper(
            issue_id,
            repo_short_name,
            suffix,
            base_branch_name,
            next_branch_name,
            expected,
        )
        mock_get_next_name.assert_not_called()

    def test3(self) -> None:
        """
        Test edge case with issue_id=0 (boundary condition).
        """
        # Prepare inputs.
        issue_id = 0
        repo_short_name = "current"
        suffix = ""
        base_branch_name = "HelpersTask0_Fix_bug"
        next_branch_name = "HelpersTask0_Fix_bug_1"
        # Prepare outputs.
        expected = "HelpersTask0_Fix_bug_1"
        # Run test and check outputs.
        self.helper(
            issue_id,
            repo_short_name,
            suffix,
            base_branch_name,
            next_branch_name,
            expected,
        )

    def test4(self) -> None:
        """
        Test edge case with empty repo_short_name (boundary condition).
        """
        # Prepare inputs.
        issue_id = 123
        repo_short_name = ""
        suffix = ""
        base_branch_name = "HelpersTask123_Fix_bug"
        next_branch_name = "HelpersTask123_Fix_bug_1"
        # Prepare outputs.
        expected = "HelpersTask123_Fix_bug_1"
        # Run test and check outputs.
        self.helper(
            issue_id,
            repo_short_name,
            suffix,
            base_branch_name,
            next_branch_name,
            expected,
        )


# #############################################################################
# Test__dassert_branch_available
# #############################################################################


class Test__dassert_branch_available(hunitest.TestCase):
    """
    Test `_dassert_branch_available()`.
    """

    def helper(self, branch_name: str) -> None:
        """
        Helper for `_dassert_branch_available()` when the branch is
        available.

        Mock `does_branch_exist()` to report the branch as available, run
        the function under test, and check that it was called correctly.

        :param branch_name: branch name to check
        """
        # Run test.
        with umock.patch.object(
            hgit, "does_branch_exist", return_value=False
        ) as mock_does_branch_exist:
            hltltagi._dassert_branch_available(branch_name)
        # Check outputs.
        mock_does_branch_exist.assert_called_once_with(
            branch_name, mode="all"
        )

    def test1(self) -> None:
        """
        Test that an available branch name does not raise.
        """
        # Prepare inputs.
        branch_name = "HelpersTask123_Fix_bug_02"
        # Run test and check outputs.
        self.helper(branch_name)

    def test2(self) -> None:
        """
        Test that an already-existing branch name raises with its name in the message.
        """
        # Prepare inputs.
        branch_name = "HelpersTask123_Fix_bug_02"
        # Run test and check output.
        with umock.patch.object(hgit, "does_branch_exist", return_value=True):
            with self.assertRaises(AssertionError) as cm:
                hltltagi._dassert_branch_available(branch_name)
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        cond=False
        Branch 'HelpersTask123_Fix_bug_02' already exists
        """
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test3(self) -> None:
        """
        Test edge case with empty branch_name (boundary condition).
        """
        # Prepare inputs.
        branch_name = ""
        # Run test and check outputs.
        self.helper(branch_name)

    def test4(self) -> None:
        """
        Test edge case with very long branch name (boundary condition).
        """
        # Prepare inputs.
        branch_name = "HelpersTask123_" + "a" * 200 + "_LongBranchName"
        # Run test and check outputs.
        self.helper(branch_name)
