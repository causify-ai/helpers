"""
End-to-end tests for `git_create_issue_and_branch.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_create_issue_and_branch as dsggtgiab
"""

import unittest.mock as mock
from typing import List, Optional

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.git.git_create_issue_and_branch as dshggciab


def _make_is_clean_side_effect(clean_dir_name: str):
    """
    Build a `hgit.is_client_clean()` side effect where only `clean_dir_name`
    is reported as clean.

    :param clean_dir_name: the only repo target considered clean
    :return: side effect function suitable for `mock.patch(...,
        side_effect=...)`
    """

    def is_clean_side_effect(
        dir_name: str = ".", abort_if_not_clean: bool = False
    ):
        _ = abort_if_not_clean
        return dir_name == clean_dir_name

    return is_clean_side_effect


# #############################################################################
# Test__get_repo_targets
# #############################################################################


class Test__get_repo_targets(hunitest.TestCase):
    """
    Test `git_create_issue_and_branch._get_repo_targets()`.
    """

    def _helper(self, no_submodules: bool, expected: List[str]) -> None:
        """
        Run `_get_repo_targets()` with a submodule present and check the
        result.

        :param no_submodules: value passed to `no_submodules` param
        :param expected: expected repo targets
        """
        # Run test.
        with (
            mock.patch("helpers.hgit.has_submodules", return_value=True),
            mock.patch(
                "helpers.hgit.get_submodule_paths",
                return_value=["helpers_root"],
            ),
        ):
            repo_targets = dshggciab._get_repo_targets(no_submodules)
        # Check outputs.
        self.assertEqual(repo_targets, expected)

    def test1(self) -> None:
        """
        Test that the outer repo only is returned when there are no
        submodules.
        """
        # Prepare inputs.
        no_submodules = False
        # Run test.
        with mock.patch("helpers.hgit.has_submodules", return_value=False):
            repo_targets = dshggciab._get_repo_targets(no_submodules)
        # Check outputs.
        expected = ["."]
        self.assertEqual(repo_targets, expected)

    def test2(self) -> None:
        """
        Test that submodules are appended after the outer repo, by default.
        """
        # Prepare inputs.
        no_submodules = False
        # Prepare outputs.
        expected = [".", "helpers_root"]
        # Run test.
        self._helper(no_submodules, expected)

    def test3(self) -> None:
        """
        Test that `no_submodules=True` returns the outer repo only, even
        when submodules are present.
        """
        # Prepare inputs.
        no_submodules = True
        # Prepare outputs.
        expected = ["."]
        # Run test.
        self._helper(no_submodules, expected)


# #############################################################################
# Test__dassert_all_targets_clean
# #############################################################################


class Test__dassert_all_targets_clean(hunitest.TestCase):
    """
    Test `git_create_issue_and_branch._dassert_all_targets_clean()`.
    """

    def _helper(self, clean_dir_name: str) -> None:
        """
        Run `_dassert_all_targets_clean()` when every target but
        `clean_dir_name` is dirty and check that it aborts.

        :param clean_dir_name: the only repo target that is clean
        """
        # Prepare inputs.
        repo_targets = [".", "helpers_root"]
        is_clean_side_effect = _make_is_clean_side_effect(clean_dir_name)
        # Run test and check outputs.
        with mock.patch(
            "helpers.hgit.is_client_clean", side_effect=is_clean_side_effect
        ):
            with self.assertRaises(AssertionError):
                dshggciab._dassert_all_targets_clean(repo_targets)

    def test1(self) -> None:
        """
        Test that a clean outer repo and submodule do not raise.
        """
        # Prepare inputs.
        repo_targets = [".", "helpers_root"]
        # Run test.
        with mock.patch("helpers.hgit.is_client_clean", return_value=True):
            dshggciab._dassert_all_targets_clean(repo_targets)

    def test2(self) -> None:
        """
        Test that a dirty outer repo aborts.
        """
        # Prepare inputs.
        clean_dir_name = "helpers_root"
        # Run test.
        self._helper(clean_dir_name)

    def test3(self) -> None:
        """
        Test that a dirty submodule aborts.
        """
        # Prepare inputs.
        clean_dir_name = "."
        # Run test.
        self._helper(clean_dir_name)


# #############################################################################
# Test__dassert_all_targets_on_master
# #############################################################################


class Test__dassert_all_targets_on_master(hunitest.TestCase):
    """
    Test `git_create_issue_and_branch._dassert_all_targets_on_master()`.
    """

    def _helper(self, original_branch: str, mocked_branch_name: str) -> None:
        """
        Run `_dassert_all_targets_on_master()` and check that it aborts.

        :param original_branch: outer repo branch passed to the function
        :param mocked_branch_name: value returned by mocked
            `hgit.get_branch_name()` for the submodule
        """
        # Prepare inputs.
        repo_targets = [".", "helpers_root"]
        # Run test and check outputs.
        with mock.patch(
            "helpers.hgit.get_branch_name", return_value=mocked_branch_name
        ):
            with self.assertRaises(AssertionError):
                dshggciab._dassert_all_targets_on_master(
                    repo_targets, original_branch
                )

    def test1(self) -> None:
        """
        Test that the outer repo and submodule both on `master` do not
        raise.
        """
        # Prepare inputs.
        repo_targets = [".", "helpers_root"]
        original_branch = "master"
        # Run test.
        with mock.patch("helpers.hgit.get_branch_name", return_value="master"):
            dshggciab._dassert_all_targets_on_master(
                repo_targets, original_branch
            )

    def test2(self) -> None:
        """
        Test that the outer repo not being on `master` aborts.
        """
        # Prepare inputs.
        original_branch = "HelpersTask1290_Test"
        mocked_branch_name = "master"
        # Run test.
        self._helper(original_branch, mocked_branch_name)

    def test3(self) -> None:
        """
        Test that a submodule not being on `master` aborts.
        """
        # Prepare inputs.
        original_branch = "master"
        mocked_branch_name = "HelpersTask1290_Test"
        # Run test.
        self._helper(original_branch, mocked_branch_name)


# #############################################################################
# Test__create_branch_in_submodule
# #############################################################################


class Test__create_branch_in_submodule(hunitest.TestCase):
    """
    Test `git_create_issue_and_branch._create_branch_in_submodule()`.
    """

    def _helper(
        self,
        does_branch_exist: bool,
        expected: str,
        *,
        create_pr: bool = True,
    ) -> None:
        """
        Run `_create_branch_in_submodule()` and check the captured system
        calls.

        :param does_branch_exist: value returned by mocked
            `hgit.does_branch_exist()`
        :param expected: expected system calls
        :param create_pr: value passed to `create_pr` param
        """
        # Prepare inputs.
        submodule_path = "helpers_root"
        branch_name = "HelpersTask1290_Test_Branch"
        # Run test and capture system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch(
                "helpers.hgit.does_branch_exist",
                return_value=does_branch_exist,
            ),
        ):
            dshggciab._create_branch_in_submodule(
                submodule_path, branch_name, create_pr=create_pr
            )
        # Check outputs.
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test1(self) -> None:
        """
        Test creating a new branch (by name) in a submodule.
        """
        # Prepare inputs.
        does_branch_exist = False
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('cd helpers_root && invoke git_branch_create --branch-name HelpersTask1290_Test_Branch',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        # Run test.
        self._helper(does_branch_exist, expected)

    def test2(self) -> None:
        """
        Test checking out a branch that already exists in the submodule.
        """
        # Prepare inputs.
        does_branch_exist = True
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('cd helpers_root && git checkout HelpersTask1290_Test_Branch',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        # Run test.
        self._helper(does_branch_exist, expected)

    def test3(self) -> None:
        """
        Test that `create_pr=False` skips draft PR creation in the
        submodule.
        """
        # Prepare inputs.
        does_branch_exist = False
        create_pr = False
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('cd helpers_root && invoke git_branch_create --branch-name HelpersTask1290_Test_Branch --no-create-pr',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        # Run test.
        self._helper(does_branch_exist, expected, create_pr=create_pr)


# #############################################################################
# Test_create_worktree
# #############################################################################


class Test_create_worktree(hunitest.TestCase):
    """
    Tests for `_create_worktree()` function.
    """

    def _helper(
        self, submodule_paths: Optional[List[str]], expected: str
    ) -> None:
        """
        Run `_create_worktree()` and check the captured system calls and the
        returned worktree path.

        :param submodule_paths: value passed to `submodule_paths` param
        :param expected: expected system calls
        """
        # Prepare inputs.
        branch_name = "HelpersTask1290_Test_Branch"
        issue_id = 1290
        original_branch = "master"
        # Run test and capture system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("os.getcwd", return_value="/home/user/helpers1"),
        ):
            worktree_path = dshggciab._create_worktree(
                branch_name, issue_id, original_branch, submodule_paths
            )
        # Check outputs.
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)
        # Verify returned worktree path.
        expected_path = "/home/user/helpers1_worktree_1290"
        self.assertEqual(worktree_path, expected_path)

    def test1(self) -> None:
        """
        Test creating a worktree.
        """
        # Prepare inputs.
        submodule_paths = None
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('git checkout master',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git worktree add /home/user/helpers1_worktree_1290 HelpersTask1290_Test_Branch',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        # Run test.
        self._helper(submodule_paths, expected)

    def test2(self) -> None:
        """
        Test creating a worktree with a submodule: the submodule is
        initialized and checked out on the same branch, not left on a
        detached HEAD.
        """
        # Prepare inputs.
        submodule_paths = ["helpers_root"]
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('git checkout master',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git worktree add /home/user/helpers1_worktree_1290 HelpersTask1290_Test_Branch',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git -C /home/user/helpers1_worktree_1290 submodule update --init --recursive',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git -C /home/user/helpers1_worktree_1290/helpers_root checkout HelpersTask1290_Test_Branch',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        # Run test.
        self._helper(submodule_paths, expected)


# #############################################################################
# Test_git_create_issue_and_branch_py
# #############################################################################


class Test_git_create_issue_and_branch_py(hunitest.TestCase):
    """
    End-to-end tests for the `git_create_issue_and_branch.py` executable.
    """

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `_main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshggciab._parse()
        with mock.patch("sys.argv", argv):
            dshggciab._main(parser)

    def test1(self) -> None:
        """
        Test that script validates title is provided when creating new issue.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
        ]
        # Run test and check for error.
        with self.assertRaises(AssertionError):
            self._run_main(argv)

    def test2(self) -> None:
        """
        Test creating issue with title and body text.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_title",
            "Test Issue",
            "--gh_issue_body",
            "Test body text",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=("", "Created issue #1290"),
            ),
            mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="HelpersTask1290_Test",
            ),
            mock.patch("helpers.hgit.has_submodules", return_value=False),
            mock.patch(
                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
            ),
        ):
            self._run_main(argv)
        # Check outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test3(self) -> None:
        """
        Test using existing issue without creating worktree.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="HelpersTask1290_Test",
            ),
            mock.patch("helpers.hgit.has_submodules", return_value=False),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_gh_issue_title",
                return_value=(
                    "HelpersTask1290_Test",
                    "http://example.com/1290",
                ),
            ),
            mock.patch("helpers.hgit.does_branch_exist", return_value=False),
            mock.patch(
                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
            ),
        ):
            self._run_main(argv)
        # Check outputs.
        expected = r"""[
        {
        'function': hsystem.system_to_string,
        'args': ('cd . && (git diff --cached --name-only; git ls-files -m) | sort | uniq',),
        'kwargs': {},
        },
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test4(self) -> None:
        """
        Test with --create_worktree flag.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--create_worktree",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch(
                "helpers.hgit.get_branch_name",
                side_effect=[
                    "master",
                    "HelpersTask1290_Test",
                    "HelpersTask1290_Test",
                ],
            ),
            mock.patch("helpers.hgit.has_submodules", return_value=False),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_gh_issue_title",
                return_value=(
                    "HelpersTask1290_Test",
                    "http://example.com/1290",
                ),
            ),
            mock.patch("helpers.hgit.does_branch_exist", return_value=False),
            mock.patch("os.getcwd", return_value="/home/user/helpers1"),
            mock.patch(
                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
            ),
            mock.patch("shutil.copy"),
            mock.patch("builtins.print"),
        ):
            self._run_main(argv)
        # Check outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git checkout master',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git worktree add /home/user/helpers1_worktree_1290 HelpersTask1290_Test',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git checkout master',),
        'kwargs': {},
        },
        ]"""
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test5(self) -> None:
        """
        Test symmetric branch and worktree creation with one submodule
        present: the branch is created in both the outer repo and the
        submodule, and the submodule's worktree is checked out on that
        branch.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--create_worktree",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch("helpers.hgit.has_submodules", return_value=True),
            mock.patch(
                "helpers.hgit.get_submodule_paths",
                return_value=["helpers_root"],
            ),
            mock.patch(
                "helpers.hgit.get_branch_name",
                side_effect=[
                    "master",
                    "master",
                    "HelpersTask1290_Test",
                    "HelpersTask1290_Test",
                ],
            ),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_gh_issue_title",
                return_value=(
                    "HelpersTask1290_Test",
                    "http://example.com/1290",
                ),
            ),
            mock.patch("helpers.hgit.does_branch_exist", return_value=False),
            mock.patch("os.getcwd", return_value="/home/user/helpers1"),
            mock.patch(
                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
            ),
            mock.patch("shutil.copy"),
            mock.patch("builtins.print"),
        ):
            self._run_main(argv)
        # Check outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('cd helpers_root && invoke git_branch_create --branch-name HelpersTask1290_Test',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git checkout master',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git worktree add /home/user/helpers1_worktree_1290 HelpersTask1290_Test',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git -C /home/user/helpers1_worktree_1290 submodule update --init --recursive',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git -C /home/user/helpers1_worktree_1290/helpers_root checkout HelpersTask1290_Test',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git checkout master',),
        'kwargs': {},
        },
        ]"""
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test6(self) -> None:
        """
        Test that a dirty outer repo aborts before touching the submodule.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
        ]
        is_clean_side_effect = _make_is_clean_side_effect("helpers_root")
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.has_submodules", return_value=True),
            mock.patch(
                "helpers.hgit.get_submodule_paths",
                return_value=["helpers_root"],
            ),
            mock.patch(
                "helpers.hgit.is_client_clean",
                side_effect=is_clean_side_effect,
            ),
        ):
            with self.assertRaises(AssertionError):
                self._run_main(argv)
        # Check outputs: nothing should have been created anywhere.
        expected = "[]"
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test7(self) -> None:
        """
        Test that a dirty submodule aborts before touching the outer repo.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
        ]
        is_clean_side_effect = _make_is_clean_side_effect(".")
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.has_submodules", return_value=True),
            mock.patch(
                "helpers.hgit.get_submodule_paths",
                return_value=["helpers_root"],
            ),
            mock.patch(
                "helpers.hgit.is_client_clean",
                side_effect=is_clean_side_effect,
            ),
        ):
            with self.assertRaises(AssertionError):
                self._run_main(argv)
        # Check outputs: nothing should have been created anywhere.
        expected = "[]"
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test8(self) -> None:
        """
        Test that the outer repo not being on `master` aborts before
        creating any branch.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch("helpers.hgit.has_submodules", return_value=True),
            mock.patch(
                "helpers.hgit.get_submodule_paths",
                return_value=["helpers_root"],
            ),
            mock.patch(
                "helpers.hgit.get_branch_name",
                side_effect=["HelpersTask999_Other", "master"],
            ),
        ):
            with self.assertRaises(AssertionError):
                self._run_main(argv)
        # Check outputs: nothing should have been created anywhere.
        expected = "[]"
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test9(self) -> None:
        """
        Test that a submodule not being on `master` aborts before creating
        any branch.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch("helpers.hgit.has_submodules", return_value=True),
            mock.patch(
                "helpers.hgit.get_submodule_paths",
                return_value=["helpers_root"],
            ),
            mock.patch(
                "helpers.hgit.get_branch_name",
                side_effect=["master", "HelpersTask999_Other"],
            ),
        ):
            with self.assertRaises(AssertionError):
                self._run_main(argv)
        # Check outputs: nothing should have been created anywhere.
        expected = "[]"
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test10(self) -> None:
        """
        Test that `--no_submodules` reproduces today's outer-repo-only
        behavior, even when a submodule is present (the submodule is never
        touched).
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--no_submodules",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="HelpersTask1290_Test",
            ),
            # A submodule is present, but must be ignored due to
            # `--no_submodules`.
            mock.patch("helpers.hgit.has_submodules", return_value=True),
            mock.patch(
                "helpers.hgit.get_submodule_paths",
                return_value=["helpers_root"],
            ),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_gh_issue_title",
                return_value=(
                    "HelpersTask1290_Test",
                    "http://example.com/1290",
                ),
            ),
            mock.patch("helpers.hgit.does_branch_exist", return_value=False),
            mock.patch(
                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
            ),
        ):
            self._run_main(argv)
        # Check outputs: only the outer repo is touched.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)
