from typing import List

import pytest

import helpers.hgit as hgit
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_git as hltltagi
import helpers.lib_tasks.test.test_lib_tasks as httestlib

# pylint: disable=protected-access


# #############################################################################
# TestLibTasksGitCreatePatch1
# #############################################################################


@pytest.mark.slow(reason="Around 7s")
@pytest.mark.skipif(
    not hgit.is_in_amp_as_supermodule(),
    reason="Run only in amp as super-module",
)
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
        # Run test.
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
        # Run test.
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
        # Run test.
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
        # Run test.
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
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hltltagi.git_patch_create(
                ctx, mode, modified, branch, last_commit, files
            )
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '0'
        ==
        '1'
        Specify only one among --modified, --branch, --last-commit
        """
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)
