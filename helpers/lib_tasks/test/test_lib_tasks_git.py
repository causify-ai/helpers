import unittest.mock as umock

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

    def test1(self) -> None:
        """
        Test modified files mode with tar.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "tar"
        modified = True
        branch = False
        last_commit = False
        files = ""
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test2(self) -> None:
        """
        Test modified files mode with diff.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "diff"
        modified = True
        branch = False
        last_commit = False
        files = ""
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test3(self) -> None:
        """
        Test branch mode with tar.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "tar"
        modified = False
        branch = True
        last_commit = False
        files = ""
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test4(self) -> None:
        """
        Test branch mode with diff.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "diff"
        modified = False
        branch = True
        last_commit = False
        files = ""
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test5(self) -> None:
        """
        Test last commit mode with tar.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "tar"
        modified = False
        branch = False
        last_commit = True
        files = ""
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test6(self) -> None:
        """
        Test last commit mode with diff.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "diff"
        modified = False
        branch = False
        last_commit = True
        files = ""
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test7(self) -> None:
        """
        Test with specific files using tar.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "tar"
        modified = True
        branch = False
        last_commit = False
        files = __file__
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test8(self) -> None:
        """
        Test with specific files using diff.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "diff"
        modified = True
        branch = False
        last_commit = False
        files = __file__
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

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
        Test with multiple files using tar (edge case for boundary conditions).
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "tar"
        modified = True
        branch = False
        last_commit = False
        files = f"{__file__} {__file__}"
        # Run test and check outputs.
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )


# #############################################################################
# Test__get_branch_name_for_issue
# #############################################################################


class Test__get_branch_name_for_issue(hunitest.TestCase):
    """
    Test `_get_branch_name_for_issue()`.
    """

    def test1(self) -> None:
        """
        Test that an omitted suffix auto-picks the next free one.
        """
        # Prepare inputs.
        issue_id = 123
        repo_short_name = "current"
        suffix = ""
        # Prepare outputs.
        expected = "HelpersTask123_Fix_bug_3"
        # Run test.
        with (
            umock.patch.object(
                hltltagh,
                "_get_gh_issue_title",
                return_value=("HelpersTask123_Fix_bug", "url"),
            ) as mock_get_title,
            umock.patch.object(
                hgit,
                "get_branch_next_name",
                return_value="HelpersTask123_Fix_bug_3",
            ) as mock_get_next_name,
        ):
            actual = hltltagi._get_branch_name_for_issue(
                issue_id, repo_short_name, suffix
            )
        # Check outputs.
        self.assert_equal(actual, expected)
        mock_get_title.assert_called_once_with(issue_id, repo_short_name)
        mock_get_next_name.assert_called_once_with(
            curr_branch_name="HelpersTask123_Fix_bug"
        )

    def test2(self) -> None:
        """
        Test that an explicit suffix is appended without auto-picking one.
        """
        # Prepare inputs.
        issue_id = 123
        repo_short_name = "current"
        suffix = "02"
        # Prepare outputs.
        expected = "HelpersTask123_Fix_bug_02"
        # Run test.
        with (
            umock.patch.object(
                hltltagh,
                "_get_gh_issue_title",
                return_value=("HelpersTask123_Fix_bug", "url"),
            ),
            umock.patch.object(
                hgit, "get_branch_next_name"
            ) as mock_get_next_name,
        ):
            actual = hltltagi._get_branch_name_for_issue(
                issue_id, repo_short_name, suffix
            )
        # Check outputs.
        self.assert_equal(actual, expected)
        mock_get_next_name.assert_not_called()

    def test3(self) -> None:
        """
        Test edge case with issue_id=0 (boundary condition).
        """
        # Prepare inputs.
        issue_id = 0
        repo_short_name = "current"
        suffix = ""
        # Prepare outputs.
        expected = "HelpersTask0_Fix_bug_1"
        # Run test.
        with (
            umock.patch.object(
                hltltagh,
                "_get_gh_issue_title",
                return_value=("HelpersTask0_Fix_bug", "url"),
            ),
            umock.patch.object(
                hgit,
                "get_branch_next_name",
                return_value="HelpersTask0_Fix_bug_1",
            ),
        ):
            actual = hltltagi._get_branch_name_for_issue(
                issue_id, repo_short_name, suffix
            )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test edge case with empty repo_short_name (boundary condition).
        """
        # Prepare inputs.
        issue_id = 123
        repo_short_name = ""
        suffix = ""
        # Prepare outputs.
        expected = "HelpersTask123_Fix_bug_1"
        # Run test.
        with (
            umock.patch.object(
                hltltagh,
                "_get_gh_issue_title",
                return_value=("HelpersTask123_Fix_bug", "url"),
            ),
            umock.patch.object(
                hgit,
                "get_branch_next_name",
                return_value="HelpersTask123_Fix_bug_1",
            ),
        ):
            actual = hltltagi._get_branch_name_for_issue(
                issue_id, repo_short_name, suffix
            )
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test__dassert_branch_available
# #############################################################################


class Test__dassert_branch_available(hunitest.TestCase):
    """
    Test `_dassert_branch_available()`.
    """

    def test1(self) -> None:
        """
        Test that an available branch name does not raise.
        """
        # Prepare inputs.
        branch_name = "HelpersTask123_Fix_bug_02"
        # Run test.
        with umock.patch.object(
            hgit, "does_branch_exist", return_value=False
        ) as mock_does_branch_exist:
            hltltagi._dassert_branch_available(branch_name)
        # Check outputs.
        mock_does_branch_exist.assert_called_once_with(
            branch_name, mode="all"
        )

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
        # Run test.
        with umock.patch.object(
            hgit, "does_branch_exist", return_value=False
        ) as mock_does_branch_exist:
            hltltagi._dassert_branch_available(branch_name)
        # Check outputs.
        mock_does_branch_exist.assert_called_once_with(
            branch_name, mode="all"
        )

    def test4(self) -> None:
        """
        Test edge case with very long branch name (boundary condition).
        """
        # Prepare inputs.
        branch_name = "HelpersTask123_" + "a" * 200 + "_LongBranchName"
        # Run test.
        with umock.patch.object(
            hgit, "does_branch_exist", return_value=False
        ) as mock_does_branch_exist:
            hltltagi._dassert_branch_available(branch_name)
        # Check outputs.
        mock_does_branch_exist.assert_called_once_with(
            branch_name, mode="all"
        )
