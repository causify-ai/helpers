"""
Tests for `git_branch_create.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_branch_create as dsggtgibrc
"""

import unittest.mock as umock
from typing import Tuple

import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.git.git_branch_create as dsggibrc

# pylint: disable=protected-access


def _get_system_calls(mock_system: umock.Mock) -> str:
    """
    Format `hsystem.system()` invocations recorded on a mock.

    :param mock_system: mock installed on `hsystem.system`
    :return: newline-separated `str(call(...))` for each call
    """
    return "\n".join(map(str, mock_system.mock_calls))


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
                dsggibrc.hltltagh,
                "_get_gh_issue_title",
                return_value=(base_branch_name, "url"),
            ) as mock_get_title,
            umock.patch.object(
                hgit,
                "get_branch_next_name",
                return_value=next_branch_name,
            ) as mock_get_next_name,
        ):
            actual = dsggibrc._get_branch_name_for_issue(
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
            dsggibrc._dassert_branch_available(branch_name)
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
        Test that an already-existing branch name raises with its name in
        the message.
        """
        # Prepare inputs.
        branch_name = "HelpersTask123_Fix_bug_02"
        # Run test and check output.
        with umock.patch.object(hgit, "does_branch_exist", return_value=True):
            with self.assertRaises(AssertionError) as cm:
                dsggibrc._dassert_branch_available(branch_name)
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


# #############################################################################
# Test__dassert_valid_branch_name
# #############################################################################


class Test__dassert_valid_branch_name(hunitest.TestCase):
    """
    Test `_dassert_valid_branch_name()`.
    """

    def test1(self) -> None:
        """
        Test that a numeric-only branch name is rejected.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dsggibrc._dassert_valid_branch_name("12345")
        actual = str(cm.exception)
        self.assertIn("only numbers are invalid", actual)

    def test2(self) -> None:
        """
        Test that a `{RepoPrefix}TaskXYZ_...`-shaped name passes.
        """
        # Run test and check output.
        dsggibrc._dassert_valid_branch_name("HelpersTask999_Foo")

    def test3(self) -> None:
        """
        Test that a personal scratch branch name passes.
        """
        # Run test and check output.
        dsggibrc._dassert_valid_branch_name("gp_scratch3")

    def test4(self) -> None:
        """
        Test that a name matching neither convention is rejected.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dsggibrc._dassert_valid_branch_name("not_a_valid_name")
        actual = str(cm.exception)
        self.assertIn("must follow convention", actual)


# #############################################################################
# Test__create_branch
# #############################################################################


class Test__create_branch(hunitest.TestCase):
    """
    Test `_create_branch()`.
    """

    def test1(self) -> None:
        """
        Test the happy path when already on `master` and `create_pr=False`.
        """
        # Prepare inputs.
        branch_name = "HelpersTask999_Foo"
        # Prepare outputs.
        expected = f"""
        call('git pull --autostash --rebase', suppress_output=False)
        call('git checkout -b {branch_name}', suppress_output=False)
        call('git push --set-upstream origin {branch_name}', suppress_output=False)
        """
        # Run test.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
            umock.patch.object(hgit, "get_branch_name", return_value="master"),
            umock.patch.object(
                hsystem, "system", return_value=0
            ) as mock_system,
        ):
            dsggibrc._create_branch(
                branch_name, 0, "current", "", create_pr=False
            )
        # Check outputs.
        actual = _get_system_calls(mock_system)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test2(self) -> None:
        """
        Test that not being on `master` triggers a checkout when allowed.
        """
        # Prepare inputs.
        branch_name = "HelpersTask999_Foo"
        # Prepare outputs.
        expected = f"""
        call('git checkout master', suppress_output=False)
        call('git pull --autostash --rebase', suppress_output=False)
        call('git checkout -b {branch_name}', suppress_output=False)
        call('git push --set-upstream origin {branch_name}', suppress_output=False)
        """
        # Run test.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
            umock.patch.object(
                hgit, "get_branch_name", return_value="other_branch"
            ),
            umock.patch.object(
                hsystem, "system", return_value=0
            ) as mock_system,
        ):
            dsggibrc._create_branch(
                branch_name,
                0,
                "current",
                "",
                create_pr=False,
                abort_if_not_master=False,
            )
        # Check outputs.
        actual = _get_system_calls(mock_system)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test3(self) -> None:
        """
        Test that not being on `master` aborts when required.
        """
        # Prepare inputs.
        branch_name = "HelpersTask999_Foo"
        # Run test and check output.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
            umock.patch.object(
                hgit, "get_branch_name", return_value="other_branch"
            ),
        ):
            with self.assertRaises(AssertionError) as cm:
                dsggibrc._create_branch(
                    branch_name, 0, "current", "", create_pr=False
                )
        actual = str(cm.exception)
        self.assertIn("Must be on 'master' branch", actual)

    def test4(self) -> None:
        """
        Test that specifying both `branch_name` and `issue_id` raises.
        """
        # Run test and check output.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            self.assertRaises(AssertionError) as cm,
        ):
            dsggibrc._create_branch(
                "HelpersTask999_Foo", 999, "current", ""
            )
        actual = str(cm.exception)
        self.assertIn("Cannot specify both --issue and --branch-name", actual)

    def test5(self) -> None:
        """
        Test that `create_pr=True` also commits, pushes, and opens a PR.
        """
        # Prepare inputs.
        branch_name = "HelpersTask999_Foo"
        # Prepare outputs.
        expected = f"""
        call('git pull --autostash --rebase', suppress_output=False)
        call('git checkout -b {branch_name}', suppress_output=False)
        call('git push --set-upstream origin {branch_name}', suppress_output=False)
        call('git commit --allow-empty -m "Draft PR"', suppress_output=False)
        call('git push', suppress_output=False)
        call('invoke gh_create_pr --draft', abort_on_error=False)
        """
        # Run test.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
            umock.patch.object(hgit, "get_branch_name", return_value="master"),
            umock.patch.object(
                hsystem, "system", return_value=0
            ) as mock_system,
        ):
            dsggibrc._create_branch(
                branch_name, 0, "current", "", create_pr=True
            )
        # Check outputs.
        actual = _get_system_calls(mock_system)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# Test_git_branch_create_py
# #############################################################################


class Test_git_branch_create_py(hunitest.TestCase):
    """
    End-to-end smoke test for the `git_branch_create.py` executable.
    """

    def test1(self) -> None:
        """
        Test that `--help` runs successfully.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("git_branch_create.py")
        cmd = f"{exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
