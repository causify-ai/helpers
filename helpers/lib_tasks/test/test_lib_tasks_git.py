import contextlib
import io
import logging
import os
import unittest.mock as umock
from typing import Any, Dict

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import helpers.lib_tasks.lib_tasks_gh as hltltagh
import helpers.lib_tasks.lib_tasks_git as hltltagi
import helpers.lib_tasks.test.test_lib_tasks as httestlib

# pylint: disable=protected-access


def _get_ctx_run_calls(ctx: Any) -> str:
    """
    Format `ctx.run()` invocations recorded on a `MockContext`.

    :param ctx: mock context returned by
        `httestlib._build_mock_context_returning_ok()`
    :return: newline-separated `str(call(...))` for each `ctx.run()` call
    """
    return "\n".join(map(str, ctx.run.mock_calls))


# #############################################################################
# Test_git_pull
# #############################################################################


class Test_git_pull(hunitest.TestCase):
    """
    Test `git_pull()`.
    """

    def test1(self) -> None:
        """
        Test that `git pull` runs on the main repo and its submodules.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        scratch_dir = self.get_scratch_space()
        # Prepare outputs.
        expected = """
        call('git pull --autostash', echo=False)
        call("git submodule foreach 'git pull --autostash'", echo=False)
        """
        # Run test.
        with umock.patch.object(
            hgit, "get_client_root", return_value=scratch_dir
        ):
            hltltagi.git_pull(ctx)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# Test_git_fetch_master
# #############################################################################


class Test_git_fetch_master(hunitest.TestCase):
    """
    Test `git_fetch_master()`.
    """

    def test1(self) -> None:
        """
        Test that fetching with `submodules=True` also fetches submodules.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        submodules = True
        # Prepare outputs.
        expected = """
        call('git fetch origin master:master', echo=False)
        call("git submodule foreach 'git fetch origin master:master'", echo=False)
        """
        # Run test.
        hltltagi.git_fetch_master(ctx, submodules=submodules)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test2(self) -> None:
        """
        Test that `submodules=False` fetches only the main repo.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        submodules = False
        # Prepare outputs.
        expected = """
        call('git fetch origin master:master', echo=False)
        """
        # Run test.
        hltltagi.git_fetch_master(ctx, submodules=submodules)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# Test_git_merge_master
# #############################################################################


class Test_git_merge_master(hunitest.TestCase):
    """
    Test `git_merge_master()`.
    """

    def helper(self, kwargs: Any, expected: str) -> None:
        """
        Run `git_merge_master()` and check the constructed command.

        :param kwargs: keyword arguments forwarded to `git_merge_master()`
        :param expected: expected single `ctx.run()` call
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        script_path = "/repo/git_merge_master.py"
        # Run test.
        with umock.patch.object(
            hsystem, "find_file_in_repo", return_value=script_path
        ):
            hltltagi.git_merge_master(ctx, **kwargs)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test1(self) -> None:
        """
        Test the default flags build a bare script invocation.
        """
        # Prepare inputs.
        kwargs: Any = {}
        # Prepare outputs.
        expected = """
        call('/repo/git_merge_master.py', echo=False)
        """
        # Run test.
        self.helper(kwargs, expected)

    def test2(self) -> None:
        """
        Test that every non-default flag appends its own CLI option.
        """
        # Prepare inputs.
        kwargs = dict(
            abort_if_not_ff=True,
            abort_if_not_clean=False,
            skip_fetch=True,
            auto_merge=False,
            submodules=False,
            dry_run=True,
        )
        # Prepare outputs.
        expected = """
        call('/repo/git_merge_master.py --abort_if_not_ff --no_abort_if_not_clean --skip_fetch --no_auto_merge --no_submodules --dry_run', echo=False)
        """
        # Run test.
        self.helper(kwargs, expected)


# #############################################################################
# Test_git_clean
# #############################################################################


class Test_git_clean(hunitest.TestCase):
    """
    Test `git_clean()`.
    """

    def test1(self) -> None:
        """
        Test the default call cleans the repo and submodules only.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        hltltagi.git_clean(ctx)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assertIn("call('git clean -fd >/dev/null 2>&1', echo=False)", actual)
        self.assertIn("git submodule foreach 'git clean -fd >/dev/null 2>&1'", actual)
        self.assertNotIn("invoke fix_perms", actual)
        self.assertIn("| xargs rm -rf", actual)

    def test2(self) -> None:
        """
        Test `dry_run=True` skips the final `xargs rm -rf` and adds `--dry-run`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        hltltagi.git_clean(ctx, dry_run=True)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assertIn("git clean -fd --dry-run >/dev/null 2>&1", actual)
        self.assertNotIn("| xargs rm -rf", actual)

    def test3(self) -> None:
        """
        Test `fix_perms_=True` also runs `invoke fix_perms` and re-cleans.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        hltltagi.git_clean(ctx, fix_perms_=True)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assertIn("call('invoke fix_perms', echo=False)", actual)


# #############################################################################
# Test_git_add_all_untracked
# #############################################################################


class Test_git_add_all_untracked(hunitest.TestCase):
    """
    Test `git_add_all_untracked()`.
    """

    def helper(self, exclude_tmp: bool, expected: str) -> None:
        """
        Run `git_add_all_untracked()` and check the constructed command.

        :param exclude_tmp: value forwarded to `git_add_all_untracked()`
        :param expected: expected single `ctx.run()` call
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        hltltagi.git_add_all_untracked(ctx, exclude_tmp=exclude_tmp)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test1(self) -> None:
        """
        Test the default call does not filter out `tmp.*` files.
        """
        # Prepare inputs.
        exclude_tmp = False
        # Prepare outputs.
        expected = """
        call('git ls-files -o --exclude-standard -z | xargs -0 git add', echo=False)
        """
        # Run test.
        self.helper(exclude_tmp, expected)

    def test2(self) -> None:
        """
        Test that `exclude_tmp=True` filters out `tmp.*` files.
        """
        # Prepare inputs.
        exclude_tmp = True
        # Prepare outputs.
        expected = """
        call("git ls-files -o --exclude-standard -z | grep -zv '^tmp\\\\.' | xargs -0 git add", echo=False)
        """
        # Run test.
        self.helper(exclude_tmp, expected)


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
        expected = "HelpersTask123_Fix_bug_3"
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
        expected = "HelpersTask123_Fix_bug_02"
        self.assert_equal(actual, expected)
        mock_get_next_name.assert_not_called()


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
        self.assertIn("already exists", actual)
        self.assertIn(branch_name, actual)


# #############################################################################
# Test_git_branch_create
# #############################################################################


class Test_git_branch_create(hunitest.TestCase):
    """
    Test `git_branch_create()`.
    """

    def test1(self) -> None:
        """
        Test the happy path when already on `master` and `create_pr=False`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branch_name = "HelpersTask999_Foo"
        # Prepare outputs.
        expected = f"""
        call('git pull --autostash --rebase', echo=False)
        call('git checkout -b {branch_name}', echo=False)
        call('git push --set-upstream origin {branch_name}', echo=False)
        """
        # Run test.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
            umock.patch.object(hgit, "get_branch_name", return_value="master"),
        ):
            hltltagi.git_branch_create(
                ctx, branch_name=branch_name, create_pr=False
            )
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test2(self) -> None:
        """
        Test that not being on `master` triggers a checkout when allowed.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branch_name = "HelpersTask999_Foo"
        # Prepare outputs.
        expected = f"""
        call('git checkout master', echo=False)
        call('git pull --autostash --rebase', echo=False)
        call('git checkout -b {branch_name}', echo=False)
        call('git push --set-upstream origin {branch_name}', echo=False)
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
        ):
            hltltagi.git_branch_create(
                ctx,
                branch_name=branch_name,
                create_pr=False,
                abort_if_not_master=False,
            )
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test3(self) -> None:
        """
        Test that not being on `master` aborts when required.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
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
                hltltagi.git_branch_create(
                    ctx, branch_name=branch_name, create_pr=False
                )
        actual = str(cm.exception)
        self.assertIn("Must be on 'master' branch", actual)

    def test4(self) -> None:
        """
        Test that specifying both `branch_name` and `issue_id` raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            self.assertRaises(AssertionError) as cm,
        ):
            hltltagi.git_branch_create(
                ctx, branch_name="HelpersTask999_Foo", issue_id=999
            )
        actual = str(cm.exception)
        self.assertIn(
            "Cannot specify both --issue and --branch-name", actual
        )

    def test5(self) -> None:
        """
        Test that a numeric-only branch name is rejected.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            self.assertRaises(AssertionError) as cm,
        ):
            hltltagi.git_branch_create(ctx, branch_name="12345")
        actual = str(cm.exception)
        self.assertIn("only numbers are invalid", actual)

    def test6(self) -> None:
        """
        Test that `create_pr=True` also commits, pushes, and opens a PR.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branch_name = "HelpersTask999_Foo"
        # Prepare outputs.
        expected = f"""
        call('git pull --autostash --rebase', echo=False)
        call('git checkout -b {branch_name}', echo=False)
        call('git push --set-upstream origin {branch_name}', echo=False)
        call('git commit --allow-empty -m "Draft PR"', echo=False)
        call('git push', echo=False)
        """
        # Run test.
        with (
            umock.patch.object(hgit, "is_client_clean"),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
            umock.patch.object(hgit, "get_branch_name", return_value="master"),
            umock.patch.object(hltltagh, "gh_create_pr") as mock_create_pr,
        ):
            hltltagi.git_branch_create(
                ctx, branch_name=branch_name, create_pr=True
            )
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)
        mock_create_pr.assert_called_once_with(ctx, draft=True)


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


# #############################################################################
# Test_git_files
# #############################################################################


class Test_git_files(hunitest.TestCase):
    """
    Test `git_files()`.
    """

    def test1(self) -> None:
        """
        Test the default "files" mode prints the sorted file list vertically.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        files_as_list = ["b.py", "a.py"]
        # Prepare outputs.
        expected = """
        a.py
        b.py
        """
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_files_to_process", return_value=files_as_list
            ),
            umock.patch.object(
                hseinout,
                "filter_files_by_extensions",
                side_effect=lambda files, *args: files,
            ),
        ):
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                hltltagi.git_files(ctx, only_print_files=True)
        # Check outputs.
        actual = printed.getvalue()
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test2(self) -> None:
        """
        Test "test_files" mode maps sources to their test files.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        files_as_list = ["helpers/hgit.py"]
        test_files = ["helpers/test/test_hgit.py"]
        mode = "test_files"
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_files_to_process", return_value=files_as_list
            ),
            umock.patch.object(
                hseinout,
                "filter_files_by_extensions",
                side_effect=lambda files, *args: files,
            ),
            umock.patch.object(
                hunteuti,
                "get_test_files_for_sources",
                return_value=test_files,
            ) as mock_get_test_files,
        ):
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                hltltagi.git_files(
                    ctx, only_print_files=True, mode=mode
                )
        # Check outputs.
        mock_get_test_files.assert_called_once_with(files_as_list)

    def test3(self) -> None:
        """
        Test `on_one_line=True` joins the results on a single line.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        files_as_list = ["b.py", "a.py"]
        # Prepare outputs.
        expected = "a.py b.py"
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_files_to_process", return_value=files_as_list
            ),
            umock.patch.object(
                hseinout,
                "filter_files_by_extensions",
                side_effect=lambda files, *args: files,
            ),
        ):
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                hltltagi.git_files(
                    ctx, only_print_files=True, on_one_line=True
                )
        # Check outputs.
        actual = printed.getvalue().strip()
        self.assert_equal(actual, expected)


# #############################################################################
# Test_git_branch_files
# #############################################################################


class Test_git_branch_files(hunitest.TestCase):
    """
    Test `git_branch_files()`.
    """

    def test1(self) -> None:
        """
        Test that the branch summary is printed with the expected header.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        summary = "M\tfoo.py\nA\tbar.py"
        # Prepare outputs.
        expected = f"""
        # git_branch_files:
        Difference between HEAD and master:
        {summary}
        """
        # Run test.
        with umock.patch.object(
            hgit, "get_summary_files_in_branch", return_value=summary
        ) as mock_get_summary:
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                hltltagi.git_branch_files(ctx)
        # Check outputs.
        actual = hprint.remove_non_printable_chars(printed.getvalue())
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)
        mock_get_summary.assert_called_once_with("master", dir_name=".")


# #############################################################################
# Test__delete_branches
# #############################################################################


class Test__delete_branches(hunitest.TestCase):
    """
    Test `_delete_branches()`.
    """

    def test1(self) -> None:
        """
        Test that no merged branches results in no deletion call.
        """
        # Prepare inputs.
        tag = "local"
        confirm_delete = True
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_merged_branches", return_value=[]
            ),
            umock.patch.object(hgit, "delete_branches") as mock_delete,
        ):
            hltltagi._delete_branches(tag, confirm_delete)
        # Check outputs.
        mock_delete.assert_not_called()

    def test2(self) -> None:
        """
        Test that local branches are deleted using their bare names.
        """
        # Prepare inputs.
        tag = "local"
        confirm_delete = True
        branches = ["HelpersTask1_Foo", "HelpersTask2_Bar"]
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_merged_branches", return_value=branches
            ),
            umock.patch.object(hgit, "delete_branches") as mock_delete,
        ):
            hltltagi._delete_branches(tag, confirm_delete)
        # Check outputs.
        mock_delete.assert_called_once_with(
            ".", tag, branches, confirm_delete
        )

    def test3(self) -> None:
        """
        Test that remote branches are prefixed with `origin/`.
        """
        # Prepare inputs.
        tag = "remote"
        confirm_delete = False
        branches = ["HelpersTask1_Foo"]
        # Prepare outputs.
        expected_branches = ["origin/HelpersTask1_Foo"]
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_merged_branches", return_value=branches
            ),
            umock.patch.object(hgit, "delete_branches") as mock_delete,
        ):
            hltltagi._delete_branches(tag, confirm_delete)
        # Check outputs.
        mock_delete.assert_called_once_with(
            ".", tag, expected_branches, confirm_delete
        )


# #############################################################################
# Test_git_branch_delete_merged
# #############################################################################


class Test_git_branch_delete_merged(hunitest.TestCase):
    """
    Test `git_branch_delete_merged()`.
    """

    def test1(self) -> None:
        """
        Test that merged local/remote branches are deleted while on master.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        confirm_delete = True
        # Prepare outputs.
        expected = """
        call('git fetch --all --prune', echo=False)
        call('git fetch --all --prune', echo=False)
        """
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value="master"
            ),
            umock.patch.object(
                hltltagi, "_delete_branches"
            ) as mock_delete_branches,
        ):
            hltltagi.git_branch_delete_merged(ctx, confirm_delete)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)
        mock_delete_branches.assert_any_call("local", confirm_delete)
        mock_delete_branches.assert_any_call("remote", confirm_delete)

    def test2(self) -> None:
        """
        Test that running off `master` raises `AssertionError`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with umock.patch.object(
            hgit, "get_branch_name", return_value="other_branch"
        ):
            with self.assertRaises(AssertionError):
                hltltagi.git_branch_delete_merged(ctx)


# #############################################################################
# Test__get_open_pr_info
# #############################################################################


class Test__get_open_pr_info(hunitest.TestCase):
    """
    Test `_get_open_pr_info()`.
    """

    def test1(self) -> None:
        """
        Test that a non-zero return code means no PR: return `None`.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1_Foo"
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(1, "")
        ):
            actual = hltltagi._get_open_pr_info(branch_name)
        # Check outputs.
        self.assertIsNone(actual)

    def test2(self) -> None:
        """
        Test that a closed/merged PR (state != OPEN) returns `None`.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1_Foo"
        txt = '{"number": 1, "title": "t", "state": "MERGED"}'
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, txt)
        ):
            actual = hltltagi._get_open_pr_info(branch_name)
        # Check outputs.
        self.assertIsNone(actual)

    def test3(self) -> None:
        """
        Test that an open PR's info dict is returned as-is.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1_Foo"
        txt = '{"number": 1, "title": "t", "state": "OPEN"}'
        # Prepare outputs.
        expected = {"number": 1, "title": "t", "state": "OPEN"}
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, txt)
        ):
            actual = hltltagi._get_open_pr_info(branch_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_git_branch_rename
# #############################################################################


class Test_git_branch_rename(hunitest.TestCase):
    """
    Test `git_branch_rename()`.
    """

    def test1(self) -> None:
        """
        Test that the same name for old and new branch raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with umock.patch.object(
            hgit, "get_branch_name", return_value="HelpersTask1_Foo"
        ):
            with self.assertRaises(AssertionError):
                hltltagi.git_branch_rename(ctx, "HelpersTask1_Foo")

    def test2(self) -> None:
        """
        Test the rename sequence when there is no open PR to carry over.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        old_name = "HelpersTask1_Foo"
        new_name = "HelpersTask1_Bar"
        # Prepare outputs.
        expected = f"""
        call('git branch -m {new_name}', echo=False)
        call('git push origin --delete {old_name}', echo=False)
        call('git branch --unset-upstream {new_name}', echo=False)
        call('git push origin {new_name}', echo=False)
        call('git push origin -u {new_name}', echo=False)
        """
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value=old_name
            ),
            umock.patch.object(hsystem, "query_yes_no"),
            umock.patch.object(
                hltltagi, "_get_open_pr_info", return_value=None
            ),
            umock.patch.object(hltltagh, "gh_create_pr") as mock_create_pr,
        ):
            hltltagi.git_branch_rename(ctx, new_name)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)
        mock_create_pr.assert_not_called()

    def test3(self) -> None:
        """
        Test that an open PR matching the old branch name is recreated.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        old_name = "HelpersTask1_Foo"
        new_name = "HelpersTask1_Bar"
        pr_info = {
            "number": 17,
            "title": old_name,
            "body": "body text",
            "isDraft": True,
            "labels": [{"name": "bug"}],
            "reviewRequests": [{"login": "reviewer1"}],
            "assignees": [{"login": "assignee1"}],
        }
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value=old_name
            ),
            umock.patch.object(hsystem, "query_yes_no"),
            umock.patch.object(
                hltltagi, "_get_open_pr_info", return_value=pr_info
            ),
            umock.patch.object(hltltagh, "gh_create_pr") as mock_create_pr,
        ):
            hltltagi.git_branch_rename(ctx, new_name)
        # Check outputs.
        mock_create_pr.assert_called_once_with(
            ctx,
            body="body text",
            draft=True,
            title=new_name,
            reviewer="reviewer1",
            labels="bug",
            assignee="assignee1",
        )
        actual = _get_ctx_run_calls(ctx)
        self.assertIn(f"gh pr comment {pr_info['number']}", actual)

    def test4(self) -> None:
        """
        Test that a PR with a custom title is not carried over.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        old_name = "HelpersTask1_Foo"
        new_name = "HelpersTask1_Bar"
        pr_info = {
            "number": 17,
            "title": "Custom title",
            "body": "body text",
            "isDraft": True,
            "labels": [],
            "reviewRequests": [],
            "assignees": [],
        }
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value=old_name
            ),
            umock.patch.object(hsystem, "query_yes_no"),
            umock.patch.object(
                hltltagi, "_get_open_pr_info", return_value=pr_info
            ),
            umock.patch.object(hltltagh, "gh_create_pr") as mock_create_pr,
        ):
            hltltagi.git_branch_rename(ctx, new_name)
        # Check outputs.
        mock_create_pr.assert_not_called()
        actual = _get_ctx_run_calls(ctx)
        self.assertNotIn("gh pr comment", actual)


# #############################################################################
# Test_git_branch_next_name
# #############################################################################


class Test_git_branch_next_name(hunitest.TestCase):
    """
    Test `git_branch_next_name()`.
    """

    def test1(self) -> None:
        """
        Test that an explicit `branch_name` is forwarded as-is.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branch_name = "HelpersTask1_Foo"
        method = "linear_scan"
        # Run test.
        with umock.patch.object(
            hgit,
            "get_branch_next_name",
            return_value="HelpersTask1_Foo_2",
        ) as mock_get_next_name:
            hltltagi.git_branch_next_name(
                ctx, branch_name=branch_name, method=method
            )
        # Check outputs.
        mock_get_next_name.assert_called_once_with(
            curr_branch_name=branch_name,
            method=method,
            log_verb=logging.INFO,
        )

    def test2(self) -> None:
        """
        Test that `issue_id` is resolved to a branch name via the GH issue title.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        issue_id = 123
        repo_short_name = "current"
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
                return_value="HelpersTask123_Fix_bug_2",
            ) as mock_get_next_name,
        ):
            hltltagi.git_branch_next_name(
                ctx, issue_id=issue_id, repo_short_name=repo_short_name
            )
        # Check outputs.
        mock_get_title.assert_called_once_with(issue_id, repo_short_name)
        mock_get_next_name.assert_called_once_with(
            curr_branch_name="HelpersTask123_Fix_bug",
            method="auto",
            log_verb=logging.INFO,
        )

    def test3(self) -> None:
        """
        Test that specifying both `branch_name` and `issue_id` raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hltltagi.git_branch_next_name(
                ctx, branch_name="HelpersTask1_Foo", issue_id=123
            )


# #############################################################################
# Test_git_branch_copy
# #############################################################################


class Test_git_branch_copy(hunitest.TestCase):
    """
    Test `git_branch_copy()`.
    """

    def test1(self) -> None:
        """
        Test the default flow: merge master, then create a brand-new branch.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        curr_branch_name = "HelpersTask1_Foo"
        new_branch_name = "HelpersTask1_Foo_2"
        # Prepare outputs.
        expected = f"""
        call('git clean -fd', echo=False)
        call('invoke git_merge_master --abort-if-not-ff --no-auto-merge --no-submodules', echo=False)
        call("git checkout master && invoke git_branch_create --branch-name '{new_branch_name}'", echo=False)
        call('git merge --squash --ff {curr_branch_name} && git reset HEAD', echo=False)
        """
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value=curr_branch_name
            ),
            umock.patch.object(
                hgit,
                "get_branch_next_name",
                return_value=new_branch_name,
            ),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
        ):
            hltltagi.git_branch_copy(ctx)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test2(self) -> None:
        """
        Test that `skip_git_merge_master=True` skips the merge-master step.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        curr_branch_name = "HelpersTask1_Foo"
        new_branch_name = "HelpersTask1_Foo_2"
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value=curr_branch_name
            ),
            umock.patch.object(
                hgit,
                "get_branch_next_name",
                return_value=new_branch_name,
            ),
            umock.patch.object(
                hgit, "does_branch_exist", return_value=False
            ),
        ):
            hltltagi.git_branch_copy(ctx, skip_git_merge_master=True)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assertNotIn("git_merge_master", actual)

    def test3(self) -> None:
        """
        Test that an existing target branch is checked out instead of created.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        curr_branch_name = "HelpersTask1_Foo"
        new_branch_name = "HelpersTask1_Existing"
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_name", return_value=curr_branch_name
            ),
            umock.patch.object(hgit, "does_branch_exist", return_value=True),
        ):
            hltltagi.git_branch_copy(
                ctx,
                new_branch_name=new_branch_name,
                skip_git_merge_master=True,
            )
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assertIn(f"git checkout {new_branch_name}", actual)
        self.assertNotIn("git_branch_create", actual)

    def test4(self) -> None:
        """
        Test that copying the `master` branch itself raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with (
            umock.patch.object(hgit, "get_branch_name", return_value="master"),
            self.assertRaises(AssertionError),
        ):
            hltltagi.git_branch_copy(ctx)

    def test5(self) -> None:
        """
        Test that `use_patch=True` raises since it is not implemented.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hltltagi.git_branch_copy(ctx, use_patch=True)


# #############################################################################
# Test_git_branch_subset_copy
# #############################################################################


class Test_git_branch_subset_copy(hunitest.TestCase):
    """
    Test `git_branch_subset_copy()`.
    """

    def helper(
        self, orig_dir: str, *args: Any, **kwargs: Any
    ) -> None:
        """
        `cd` into `orig_dir` and run `git_branch_subset_copy()`.

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
            hltltagi.git_branch_subset_copy(*args, **kwargs)
        finally:
            os.chdir(real_cwd)

    def test1(self) -> None:
        """
        Test that missing both `from_file` and `--pr` raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hltltagi.git_branch_subset_copy(ctx, dst_dir=self.get_scratch_space())
        actual = str(cm.exception)
        self.assertIn("from_file or --pr must be provided", actual)

    def test2(self) -> None:
        """
        Test that a missing `dst_dir` raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        from_file = os.path.join(self.get_scratch_space(), "files.txt")
        hio.to_file(from_file, "a.py\n")
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hltltagi.git_branch_subset_copy(ctx, from_file=from_file)
        actual = str(cm.exception)
        self.assertIn("dst_dir must be provided", actual)

    def test3(self) -> None:
        """
        Test the happy path: checkout, branch creation, and file copy.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        scratch_dir = self.get_scratch_space()
        dst_dir = os.path.join(scratch_dir, "dst")
        hio.create_dir(dst_dir, incremental=True)
        orig_dir = os.path.join(scratch_dir, "orig")
        hio.create_dir(orig_dir, incremental=True)
        from_file = os.path.join(orig_dir, "files.txt")
        hio.to_file(from_file, "a.py\nb.py\n")
        branch_name = "HelpersTask1_Foo_2"
        # Prepare outputs.
        expected_calls = f"""
        call('git checkout master', echo=False)
        call("invoke git_branch_create --branch-name '{branch_name}'", echo=False)
        """
        expected_sys_call = (
            f"copy_across_clients.py --dir1 {orig_dir} --dir2 {dst_dir} "
            f"--from_file {from_file}"
        )
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_next_name", return_value=branch_name
            ),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            self.helper(
                orig_dir, ctx, from_file=from_file, dst_dir=dst_dir
            )
        # Check outputs.
        actual_calls = _get_ctx_run_calls(ctx)
        self.assert_equal(
            actual_calls, expected_calls, fuzzy_match=True, dedent=True
        )
        self.assertEqual(len(sys_calls), 1)
        self.assertEqual(sys_calls[0]["function"], "hsystem.system")
        self.assertEqual(sys_calls[0]["args"], (expected_sys_call,))

    def test4(self) -> None:
        """
        Test that `--pr` mode also copies the `pr<NUM>.pytest.sh` script.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        scratch_dir = self.get_scratch_space()
        dst_dir = os.path.join(scratch_dir, "dst")
        hio.create_dir(dst_dir, incremental=True)
        orig_dir = os.path.join(scratch_dir, "orig")
        hio.create_dir(orig_dir, incremental=True)
        pr = 17
        # `git_branch_subset_copy()` reads `from_file` (its basename, once
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
            self.helper(orig_dir, ctx, pr=pr, dst_dir=dst_dir)
        # Check outputs.
        actual_calls = _get_ctx_run_calls(ctx)
        # `gp_scratch*` branches skip the naming-convention check.
        self.assertIn("--no-check-branch-name", actual_calls)
        sys_call_fns = [c["function"] for c in sys_calls]
        self.assert_equal(str(sys_call_fns), str(["hsystem.system"] * 2))
        pytest_dst = os.path.join(dst_dir, f"pr{pr}.pytest.sh")
        self.assertEqual(
            sys_calls[1]["args"], (f"cp {pytest_src} {pytest_dst}",)
        )


# #############################################################################
# Test__git_diff_with_branch
# #############################################################################


class Test__git_diff_with_branch(hunitest.TestCase):
    """
    Test `_git_diff_with_branch()`.
    """

    def call(self, **overrides: Any) -> Any:
        """
        Call `_git_diff_with_branch()` with default args, overridable.

        :param overrides: keyword args overriding the defaults
        :return: the `ctx` used for the call
        """
        ctx = httestlib._build_mock_context_returning_ok()
        kwargs: Dict[str, Any] = dict(
            ctx=ctx,
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
        hltltagi._git_diff_with_branch(**kwargs)
        return ctx

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
            umock.patch.object(
                hsystem, "system_to_files", return_value=[]
            ),
            umock.patch.object(hio, "create_dir") as mock_create_dir,
        ):
            ctx = self.call()
        # Check outputs.
        mock_create_dir.assert_not_called()
        self.assertEqual(_get_ctx_run_calls(ctx), "")

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
            umock.patch.object(hio, "create_dir") as mock_create_dir,
        ):
            ctx = self.call(only_print_files=True)
        # Check outputs.
        mock_create_dir.assert_not_called()
        self.assertEqual(_get_ctx_run_calls(ctx), "")

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
            umock.patch.object(
                hgit,
                "get_repo_full_name_from_client",
                return_value="myorg/myrepo",
            ),
            umock.patch.object(hio, "create_dir") as mock_create_dir,
            umock.patch.object(
                hsystem, "system", return_value=0
            ) as mock_system,
            umock.patch.object(
                hio, "create_executable_script"
            ) as mock_create_script,
        ):
            ctx = self.call(dry_run=False)
        # Check outputs.
        mock_create_dir.assert_called_once_with(dst_dir, incremental=False)
        mock_system.assert_called_once_with(
            f"git show base_hash:a.py >{dst_dir}/a.py", abort_on_error=False
        )
        script_file_name, script_txt = mock_create_script.call_args[0]
        self.assertEqual(script_file_name, "./tmp.vimdiff_branch_with_base.sh")
        self.assertEqual(script_txt, f"vimdiff {dst_dir}/a.py /dev/null")
        actual = _get_ctx_run_calls(ctx)
        self.assertIn(
            f"call('{script_file_name}', echo=False, pty=True)", actual
        )
        self.assertIn(f"call('rm -rf {dst_dir}', echo=False)", actual)


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
        ctx = httestlib._build_mock_context_returning_ok()
        kwargs: Dict[str, Any] = dict(
            ctx=ctx,
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
        hltltagi._git_diff_with_branch_wrapper(**kwargs)

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
        with umock.patch.object(
            hltltagi, "_git_diff_with_branch"
        ) as mock_diff:
            self.call(include_submodules=False)
        # Check outputs.
        mock_diff.assert_called_once()

    def test3(self) -> None:
        """
        Test that `include_submodules=True` also diffs an existing `amp`.
        """
        # Run test.
        with (
            umock.patch.object(
                hltltagi, "_git_diff_with_branch"
            ) as mock_diff,
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
            umock.patch.object(
                hltltagi, "_git_diff_with_branch"
            ) as mock_diff,
            umock.patch.object(hgit, "is_amp_present", return_value=False),
        ):
            self.call(include_submodules=True)
        # Check outputs.
        mock_diff.assert_called_once()


# #############################################################################
# Test_git_branch_diff
# #############################################################################


class Test_git_branch_diff(hunitest.TestCase):
    """
    Test `git_branch_diff()`.
    """

    def helper(self, kwargs: Any, expected_hash: str, expected_tag: str) -> None:
        """
        Run `git_branch_diff()` and check the resolved hash and tag.

        :param kwargs: keyword arguments forwarded to `git_branch_diff()`
        :param expected_hash: expected `hash_value` passed to the wrapper
        :param expected_tag: expected `tag` passed to the wrapper
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_branch_hash", return_value="base_hash"
            ),
            umock.patch.object(
                hltltagi, "_git_diff_with_branch_wrapper"
            ) as mock_wrapper,
        ):
            hltltagi.git_branch_diff(ctx, **kwargs)
        # Check outputs.
        actual_hash = mock_wrapper.call_args[0][1]
        actual_tag = mock_wrapper.call_args[0][2]
        self.assertEqual(actual_hash, expected_hash)
        self.assertEqual(actual_tag, expected_tag)

    def test1(self) -> None:
        """
        Test the default `target="base"` resolves to the branch point.
        """
        # Prepare inputs.
        kwargs: Any = {}
        # Run test.
        self.helper(kwargs, "base_hash", "base")

    def test2(self) -> None:
        """
        Test `target="master"` resolves to `origin/master`.
        """
        # Prepare inputs.
        kwargs = dict(target="master")
        # Run test.
        self.helper(kwargs, "origin/master", "origin_master")

    def test3(self) -> None:
        """
        Test `target="head"` resolves to an empty hash.
        """
        # Prepare inputs.
        kwargs = dict(target="head")
        # Run test.
        self.helper(kwargs, "", "head")

    def test4(self) -> None:
        """
        Test `last_commit=True` overrides the target to `HEAD^`.
        """
        # Prepare inputs.
        kwargs = dict(last_commit=True)
        # Run test.
        self.helper(kwargs, "HEAD^", "last_commit")

    def test5(self) -> None:
        """
        Test `target="hash"` uses the given `hash_value` verbatim.
        """
        # Prepare inputs.
        kwargs = dict(target="hash", hash_value="deadbeef")
        # Run test.
        self.helper(kwargs, "deadbeef", "hash@deadbeef")

    def test6(self) -> None:
        """
        Test that an invalid `target` raises `AssertionError`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hltltagi.git_branch_diff(ctx, target="invalid")

    def test7(self) -> None:
        """
        Test that `target="hash"` without `hash_value` raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hltltagi.git_branch_diff(ctx, target="hash")

    def test8(self) -> None:
        """
        Test that `hash_value` with `target="base"` raises.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hltltagi.git_branch_diff(ctx, hash_value="deadbeef")


# #############################################################################
# Test_git_repo_copy
# #############################################################################


class Test_git_repo_copy(hunitest.TestCase):
    """
    Test `git_repo_copy()`.
    """

    def test1(self) -> None:
        """
        Test that the file is copied to the mapped destination path.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        file_name = "helpers/hgit.py"
        src_git_dir = "/src/helpers1"
        dst_git_dir = "/src/helpers2"
        dst_file_path = "/src/helpers2/helpers/hgit.py"
        # Run test.
        with (
            umock.patch.object(
                hgit, "resolve_git_client_dir", side_effect=lambda d: d
            ),
            umock.patch.object(
                hgit,
                "project_file_name_in_git_client",
                return_value=dst_file_path,
            ) as mock_project_file,
            umock.patch.object(
                hsystem, "system_to_string"
            ) as mock_system_to_string,
        ):
            hltltagi.git_repo_copy(
                ctx, file_name, src_git_dir, dst_git_dir
            )
        # Check outputs.
        mock_project_file.assert_called_once_with(
            file_name,
            src_git_dir,
            dst_git_dir,
            check_src_file_exists=True,
            check_dst_file_exists=False,
        )
        mock_system_to_string.assert_called_once_with(
            f"cp {file_name} {dst_file_path}"
        )


# #############################################################################
# Test__get_submodule_paths
# #############################################################################


class Test__get_submodule_paths(hunitest.TestCase):
    """
    Test `_get_submodule_paths()`.
    """

    def test1(self) -> None:
        """
        Test that a missing `.gitmodules` file returns an empty list.
        """
        # Run test.
        with umock.patch.object(os.path, "exists", return_value=False):
            actual = hltltagi._get_submodule_paths()
        # Check outputs.
        self.assertEqual(actual, [])

    def test2(self) -> None:
        """
        Test that submodule paths are parsed out of `.gitmodules`.
        """
        # Prepare inputs.
        output = (
            "submodule.helpers_root.path helpers_root\n"
            "submodule.amp.path amp\n"
        )
        # Prepare outputs.
        expected = ["helpers_root", "amp"]
        # Run test.
        with (
            umock.patch.object(os.path, "exists", return_value=True),
            umock.patch.object(
                hsystem, "system_to_string", return_value=(0, output)
            ),
        ):
            actual = hltltagi._get_submodule_paths()
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test__get_branch_name
# #############################################################################


class Test__get_branch_name(hunitest.TestCase):
    """
    Test `_get_branch_name()`.
    """

    def test1(self) -> None:
        """
        Test that the branch name is stripped of surrounding whitespace.
        """
        # Prepare inputs.
        submodule_path = self.get_scratch_space()
        hio.create_dir(
            os.path.join(submodule_path, ".git"), incremental=True
        )
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, "master\n")
        ):
            actual = hltltagi._get_branch_name(submodule_path)
        # Check outputs.
        self.assertEqual(actual, "master")


# #############################################################################
# Test_git_branches
# #############################################################################


class Test_git_branches(hunitest.TestCase):
    """
    Test `git_branches()`.
    """

    def test1(self) -> None:
        """
        Test that only the main repo branch is printed with no submodules.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Prepare outputs.
        expected = """
        . -> master
        """
        # Run test.
        with (
            umock.patch.object(
                hltltagi, "_get_branch_name", return_value="master"
            ),
            umock.patch.object(
                hltltagi, "_get_submodule_paths", return_value=[]
            ),
        ):
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                hltltagi.git_branches(ctx)
        # Check outputs.
        actual = printed.getvalue()
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)

    def test2(self) -> None:
        """
        Test that each submodule's branch is printed after the main repo.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branches = {".": "master", "helpers_root": "dev"}
        # Prepare outputs.
        expected = """
        . -> master
        helpers_root -> dev
        """
        # Run test.
        with (
            umock.patch.object(
                hltltagi,
                "_get_branch_name",
                side_effect=lambda path: branches[path],
            ),
            umock.patch.object(
                hltltagi,
                "_get_submodule_paths",
                return_value=["helpers_root"],
            ),
        ):
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                hltltagi.git_branches(ctx)
        # Check outputs.
        actual = printed.getvalue()
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# Test_git_branch_is_merged
# #############################################################################


class Test_git_branch_is_merged(hunitest.TestCase):
    """
    Test `git_branch_is_merged()`.
    """

    def test1(self) -> None:
        """
        Test that the PR and remote-branch lookups run for the current branch.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branch_name = "HelpersTask1_Foo"
        # Prepare outputs.
        expected = f"""
        call('gh pr list --base master --head {branch_name}', pty=True)
        call('git ls-remote --heads origin {branch_name}', pty=True)
        """
        # Run test.
        with umock.patch.object(
            hgit, "get_branch_name", return_value=branch_name
        ):
            hltltagi.git_branch_is_merged(ctx)
        # Check outputs.
        actual = _get_ctx_run_calls(ctx)
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)


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
                hltltagi, "_get_submodule_paths", return_value=[]
            ),
        ):
            actual = hltltagi._collect_backup_files(
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
                hltltagi, "_get_submodule_paths"
            ) as mock_get_submodule_paths,
        ):
            actual = hltltagi._collect_backup_files(
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
                hltltagi,
                "_get_submodule_paths",
                return_value=[submodule_path],
            ),
        ):
            actual = hltltagi._collect_backup_files(
                file_mode, include_subrepos
            )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_git_backup
# #############################################################################


class Test_git_backup(hunitest.TestCase):
    """
    Test `git_backup()`.
    """

    def test1(self) -> None:
        """
        Test that an invalid `file_mode` raises `AssertionError`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hltltagi.git_backup(ctx, file_mode="invalid")

    def test2(self) -> None:
        """
        Test that no collected files skips creating a zip file entirely.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        backup_dir = self.get_scratch_space()
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_client_root", return_value="/repo"
            ),
            umock.patch.object(
                hltltagi, "_collect_backup_files", return_value=[]
            ),
            umock.patch("zipfile.ZipFile") as mock_zip,
        ):
            hltltagi.git_backup(ctx, backup_dir=backup_dir)
        # Check outputs.
        mock_zip.assert_not_called()

    def test3(self) -> None:
        """
        Test that `dry_run=True` skips creating a zip file.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        backup_dir = self.get_scratch_space()
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_client_root", return_value="/repo"
            ),
            umock.patch.object(
                hltltagi,
                "_collect_backup_files",
                return_value=[(".", "a.py")],
            ),
            umock.patch("zipfile.ZipFile") as mock_zip,
        ):
            hltltagi.git_backup(ctx, backup_dir=backup_dir, dry_run=True)
        # Check outputs.
        mock_zip.assert_not_called()

    def test4(self) -> None:
        """
        Test the happy path zips every collected file under its arcname.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        backup_dir = self.get_scratch_space()
        all_files = [(".", "a.py"), ("helpers_root", "b.py")]
        # Run test.
        with (
            umock.patch.object(
                hgit, "get_client_root", return_value="/repo"
            ),
            umock.patch.object(
                hltltagi, "_collect_backup_files", return_value=all_files
            ),
            umock.patch("zipfile.ZipFile") as mock_zip,
        ):
            mock_zipf = mock_zip.return_value.__enter__.return_value
            hltltagi.git_backup(ctx, backup_dir=backup_dir)
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
# Test__has_ug_write_perms
# #############################################################################


class Test__has_ug_write_perms(hunitest.TestCase):
    """
    Test `_has_ug_write_perms()`.
    """

    def test1(self) -> None:
        """
        Test that a file writable by both user and group returns `True`.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "rw.txt")
        hio.to_file(file_path, "x")
        os.chmod(file_path, 0o660)
        # Run test.
        actual = hltltagi._has_ug_write_perms(file_path)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test that a file not writable by group returns `False`.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "ro_group.txt")
        hio.to_file(file_path, "x")
        os.chmod(file_path, 0o600)
        # Run test.
        actual = hltltagi._has_ug_write_perms(file_path)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test that a non-existent path returns `False` instead of raising.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "missing.txt")
        # Run test.
        actual = hltltagi._has_ug_write_perms(file_path)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test__fix_file_perms
# #############################################################################


class Test__fix_file_perms(hunitest.TestCase):
    """
    Test `_fix_file_perms()`.
    """

    def test1(self) -> None:
        """
        Test that `chmod ug+w` is applied to a read-only file.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "ro.txt")
        hio.to_file(file_path, "x")
        os.chmod(file_path, 0o400)
        # Run test.
        actual = hltltagi._fix_file_perms(file_path)
        # Check outputs.
        self.assertTrue(actual)
        self.assertTrue(hltltagi._has_ug_write_perms(file_path))


# #############################################################################
# Test_git_fix_perms
# #############################################################################


class Test_git_fix_perms(hunitest.TestCase):
    """
    Test `git_fix_perms()`.
    """

    def helper(self) -> Any:
        """
        Create a scratch dir with one wrong-perm and one correct-perm file.

        :return: `(ctx, dir_name, wrong_file, correct_file)`
        """
        ctx = httestlib._build_mock_context_returning_ok()
        dir_name = self.get_scratch_space()
        os.chmod(dir_name, 0o770)
        wrong_file = os.path.join(dir_name, "wrong.txt")
        hio.to_file(wrong_file, "x")
        os.chmod(wrong_file, 0o400)
        correct_file = os.path.join(dir_name, "correct.txt")
        hio.to_file(correct_file, "x")
        os.chmod(correct_file, 0o660)
        return ctx, dir_name, wrong_file, correct_file

    def test1(self) -> None:
        """
        Test `check=True, fix=False` reports the wrong-perm file only.
        """
        # Prepare inputs.
        ctx, dir_name, wrong_file, correct_file = self.helper()
        # Run test.
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            hltltagi.git_fix_perms(
                ctx, check=True, fix=False, dir_name=dir_name
            )
        # Check outputs.
        actual = printed.getvalue()
        self.assertIn(wrong_file, actual)
        self.assertNotIn(correct_file, actual)
        # Fixing was not requested: permissions are unchanged.
        self.assertFalse(hltltagi._has_ug_write_perms(wrong_file))

    def test2(self) -> None:
        """
        Test `fix=True` actually applies `chmod ug+w` to the wrong-perm file.
        """
        # Prepare inputs.
        ctx, dir_name, wrong_file, _ = self.helper()
        # Run test.
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            hltltagi.git_fix_perms(
                ctx, check=False, fix=True, dir_name=dir_name
            )
        # Check outputs.
        self.assertTrue(hltltagi._has_ug_write_perms(wrong_file))

    def test3(self) -> None:
        """
        Test that all-correct permissions print the all-clear message.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        dir_name = self.get_scratch_space()
        os.chmod(dir_name, 0o770)
        correct_file = os.path.join(dir_name, "correct.txt")
        hio.to_file(correct_file, "x")
        os.chmod(correct_file, 0o660)
        # Run test.
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            hltltagi.git_fix_perms(ctx, dir_name=dir_name)
        # Check outputs.
        actual = printed.getvalue()
        self.assertIn(
            "All files/directories have correct permissions (ug+w)", actual
        )
