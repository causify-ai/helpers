import logging
import unittest.mock as umock
from typing import List

import pytest

import helpers.hgit as hgit
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_gh as hltltagh
import helpers.lib_tasks.lib_tasks_git as hltltagi
import helpers.lib_tasks.test.test_lib_tasks as httestlib

# pylint: disable=protected-access

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__get_branch_name_for_issue
# #############################################################################


# TODO(ai_gp): Move this test class after public function tests to
# prioritize testing public-facing behavior first (testing.rules.md:##
# Test From the Outside-In)
# TODO(ai_gp): Add edge case tests for boundary conditions such as issue_id=0
# and empty repo_short_name (testing.rules.md:## Test Coverage)
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
        # TODO(ai_gp): Mock external dependencies (git, GitHub API) instead
        # of internal helper wrappers (hgit, lib_tasks_gh) (testing.rules.md:##
        # Mock Only External Dependencies)
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


# #############################################################################
# Test__dassert_branch_available
# #############################################################################


# TODO(ai_gp): Move this test class after public function tests to
# prioritize testing public-facing behavior first (testing.rules.md:##
# Test From the Outside-In)
# TODO(ai_gp): Add edge case tests for boundary conditions such as empty
# branch_name and very long branch names (testing.rules.md:## Test Coverage)
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
        # TODO(ai_gp): Mock external dependency (git) instead of internal
        # helper wrapper (hgit) (testing.rules.md:## Mock Only External
        # Dependencies)
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
        # TODO(ai_gp): Use assert_equal() to compare whole output instead of
        # multiple assertIn() calls for individual pieces (testing.rules.md:##
        # Compare Whole Output with `assert_equal`, Not Piecewise)
        self.assertIn("already exists", actual)
        self.assertIn(branch_name, actual)


# #############################################################################
# TestLibTasksGitCreatePatch1
# #############################################################################


@pytest.mark.slow(reason="Around 7s")
@pytest.mark.skipif(
    not hgit.is_in_amp_as_supermodule(),
    reason="Run only in amp as super-module",
)
# TODO(ai_gp): Add edge case tests for boundary conditions such as multiple
# files and very long file paths (testing.rules.md:## Test Coverage)
# TODO(ai_gp): Rename class to Test_git_patch_create to follow the naming
# convention for functions (testing.rules.md:## Naming Conventions for a
# Function)
class TestLibTasksGitCreatePatch1(hunitest.TestCase):
    """
    Test `git_patch_create()`.
    """

    @staticmethod
    def helper(
        modified: bool, branch: bool, last_commit: bool, files: str
    ) -> None:
        ctx = httestlib._build_mock_context_returning_ok()
        #
        mode = "tar"
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )
        #
        mode = "diff"
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test1(self) -> None:
        """
        Test modified files mode.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        files = ""
        # Run test and check outputs.
        # TODO(ai_gp): Split the helper to test tar and diff modes
        # separately; each test should test one case (testing.rules.md:## Test
        # One Thing)
        self.helper(modified, branch, last_commit, files)

    def test2(self) -> None:
        """
        Test branch mode.
        """
        # Prepare inputs.
        modified = False
        branch = True
        last_commit = False
        files = ""
        # Run test and check outputs.
        # TODO(ai_gp): Split the helper to test tar and diff modes
        # separately; each test should test one case (testing.rules.md:## Test
        # One Thing)
        self.helper(modified, branch, last_commit, files)

    def test3(self) -> None:
        """
        Test last commit mode.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = False
        branch = False
        last_commit = True
        files = ""
        # Run test and check outputs.
        # TODO(ai_gp): Split the helper to test tar and diff modes
        # separately; each test should test one case (testing.rules.md:## Test
        # One Thing)
        self.helper(modified, branch, last_commit, files)

    def test4(self) -> None:
        """
        Test with specific files.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        files = __file__
        # Run test and check outputs.
        # TODO(ai_gp): Split the helper to test tar and diff modes
        # separately; each test should test one case (testing.rules.md:## Test
        # One Thing)
        self.helper(modified, branch, last_commit, files)

    def test5(self) -> None:
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
