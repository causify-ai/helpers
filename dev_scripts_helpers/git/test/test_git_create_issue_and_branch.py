"""
End-to-end tests for `git_create_issue_and_branch.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_create_issue_and_branch as dsggtgiab
"""

import json
import unittest.mock as mock
from typing import Any, Dict, List, Optional, Tuple

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.git.git_create_issue_and_branch as dshggciab


def _make_is_clean_side_effect(clean_dir_name: str):
    """
    Build a `hgit.is_client_clean()` side effect where only `clean_dir_name` is
    reported as clean.

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


def _make_system_to_string_side_effect(
    projects: List[Dict[str, Any]], cmds: List[str]
):
    """
    Build a `hsystem.system_to_string()` side effect that records each command.

    `gh project list` is answered with `projects` and any other command (i.e.,
    `invoke gh_issue_create`) with a created issue #1290.

    :param projects: projects returned by `gh project list`
    :param cmds: list that each command run is appended to
    :return: side effect function suitable for `mock.patch(...,
        side_effect=...)`
    """

    def system_to_string_side_effect(
        cmd: str, **kwargs: Any
    ) -> Tuple[int, str]:
        _ = kwargs
        cmds.append(cmd)
        if cmd.startswith("gh project list"):
            output = json.dumps(
                {"projects": projects, "totalCount": len(projects)}
            )
        else:
            output = "Created issue #1290"
        return 0, output

    return system_to_string_side_effect


# #############################################################################
# Test__get_repo_targets
# #############################################################################


class Test__get_repo_targets(hunitest.TestCase):
    """
    Test `git_create_issue_and_branch._get_repo_targets()`.
    """

    def _helper(self, submodules: bool, expected: List[str]) -> None:
        """
        Run `_get_repo_targets()` with a submodule present and check the result.

        :param submodules: value passed to `submodules` param
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
            repo_targets = dshggciab._get_repo_targets(submodules)
        # Check outputs.
        self.assertEqual(repo_targets, expected)

    def test1(self) -> None:
        """
        Test that the outer repo only is returned when there are no
        submodules.
        """
        # Prepare inputs.
        submodules = True
        # Run test.
        with mock.patch("helpers.hgit.has_submodules", return_value=False):
            repo_targets = dshggciab._get_repo_targets(submodules)
        # Check outputs.
        expected = ["."]
        self.assertEqual(repo_targets, expected)

    def test2(self) -> None:
        """
        Test that submodules are appended after the outer repo when
        `submodules=True` is requested.
        """
        # Prepare inputs.
        submodules = True
        # Prepare outputs.
        expected = [".", "helpers_root"]
        # Run test.
        self._helper(submodules, expected)

    def test3(self) -> None:
        """
        Test that the default (`submodules=False`) returns the outer repo
        only, even when submodules are present.
        """
        # Prepare inputs.
        submodules = False
        # Prepare outputs.
        expected = ["."]
        # Run test.
        self._helper(submodules, expected)


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
# Test__resolve_gh_project
# #############################################################################


class Test__resolve_gh_project(hunitest.TestCase):
    """
    Test `git_create_issue_and_branch._resolve_gh_project()`.
    """

    def _helper(
        self,
        gh_project: str,
        projects: List[Dict[str, Any]],
        expected: Tuple[str, int],
        expected_cmd: str,
    ) -> None:
        """
        Run `_resolve_gh_project()` with a mocked `gh project list` and check
        the result and the command that was run.

        :param gh_project: value passed to `gh_project` param
        :param projects: projects returned by the mocked `gh project list`
        :param expected: expected (owner, number)
        :param expected_cmd: expected `gh` command, or "" if `gh` must not be
            called (i.e., the project is a URL)
        """
        # Prepare inputs.
        repo_full_name_with_host = "github.com/gpsaggese/umd_classes"
        output = json.dumps({"projects": projects, "totalCount": len(projects)})
        # Run test.
        with mock.patch(
            "helpers.hsystem.system_to_string", return_value=(0, output)
        ) as mock_system_to_string:
            actual = dshggciab._resolve_gh_project(
                gh_project, repo_full_name_with_host
            )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))
        if expected_cmd:
            mock_system_to_string.assert_called_once_with(expected_cmd)
        else:
            mock_system_to_string.assert_not_called()

    def test1(self) -> None:
        """
        Test that a personal project URL is parsed without calling `gh`.
        """
        # Prepare inputs.
        gh_project = "https://github.com/users/gpsaggese/projects/4"
        projects: List[Dict[str, Any]] = []
        # Prepare outputs.
        expected = ("gpsaggese", 4)
        expected_cmd = ""
        # Run test.
        self._helper(gh_project, projects, expected, expected_cmd)

    def test2(self) -> None:
        """
        Test that an organization project URL with a trailing path (e.g., a
        view) is parsed, using the owner of the URL and not the repo's.
        """
        # Prepare inputs.
        gh_project = "https://github.com/orgs/causify-ai/projects/12/views/1"
        projects: List[Dict[str, Any]] = []
        # Prepare outputs.
        expected = ("causify-ai", 12)
        expected_cmd = ""
        # Run test.
        self._helper(gh_project, projects, expected, expected_cmd)

    def test3(self) -> None:
        """
        Test that a title is looked up among the projects of the repo's owner.
        """
        # Prepare inputs.
        gh_project = "Optimal_strategy_for_racket_sports"
        projects = [
            {"number": 2, "title": "Other"},
            {"number": 4, "title": "Optimal_strategy_for_racket_sports"},
        ]
        # Prepare outputs.
        expected = ("gpsaggese", 4)
        expected_cmd = (
            "gh project list --owner gpsaggese --limit 200 --format json"
        )
        # Run test.
        self._helper(gh_project, projects, expected, expected_cmd)

    def test4(self) -> None:
        """
        Test that a title matching no project aborts.
        """
        # Prepare inputs.
        gh_project = "Optimal_strategy_for_racket_sports"
        projects = [{"number": 2, "title": "Other"}]
        output = json.dumps({"projects": projects, "totalCount": 1})
        repo_full_name_with_host = "github.com/gpsaggese/umd_classes"
        # Run test and check for error.
        with mock.patch(
            "helpers.hsystem.system_to_string", return_value=(0, output)
        ):
            with self.assertRaises(AssertionError):
                dshggciab._resolve_gh_project(
                    gh_project, repo_full_name_with_host
                )

    def test5(self) -> None:
        """
        Test that a title matching more than one project aborts, since the
        project would be ambiguous.
        """
        # Prepare inputs.
        gh_project = "Dup"
        projects = [
            {"number": 2, "title": "Dup"},
            {"number": 3, "title": "Dup"},
        ]
        output = json.dumps({"projects": projects, "totalCount": 2})
        repo_full_name_with_host = "github.com/gpsaggese/umd_classes"
        # Run test and check for error.
        with mock.patch(
            "helpers.hsystem.system_to_string", return_value=(0, output)
        ):
            with self.assertRaises(AssertionError):
                dshggciab._resolve_gh_project(
                    gh_project, repo_full_name_with_host
                )


# #############################################################################
# Test__add_issue_to_project
# #############################################################################


class Test__add_issue_to_project(hunitest.TestCase):
    """
    Test `git_create_issue_and_branch._add_issue_to_project()`.
    """

    def test1(self) -> None:
        """
        Test that the issue is added to the project by URL.
        """
        # Prepare inputs.
        issue_id = 1290
        repo_full_name_with_host = "github.com/gpsaggese/umd_classes"
        project_owner = "gpsaggese"
        project_number = 4
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            dshggciab._add_issue_to_project(
                issue_id,
                repo_full_name_with_host,
                project_owner,
                project_number,
            )
        # Check outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('gh project item-add 4 --owner gpsaggese --url https://github.com/gpsaggese/umd_classes/issues/1290',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)


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
                "helpers.lib_tasks.lib_tasks_gh._get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._dassert_no_duplicate_open_issue"
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
        present and `--submodules` passed: the branch is created in both
        the outer repo and the submodule, the submodule's worktree is
        checked out on that branch, and the issue is updated with the
        companion PR links (since `--create_pr` defaults to True and there
        is more than one repo target).
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--create_worktree",
            "--submodules",
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
            mock.patch("tempfile.gettempdir", return_value="/tmp"),
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
        'function': hsystem.system_to_string,
        'args': ('gh issue view 1290 --json body -q .body',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('gh pr view --json url -q .url',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('cd helpers_root && gh pr view --json url -q .url',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system,
        'args': ('gh issue edit 1290 --body-file /tmp/tmp.git_create_issue_and_branch.issue_1290_body.md',),
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
        Test that a dirty outer repo aborts before touching the submodule,
        with `--submodules` passed.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--submodules",
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
        Test that a dirty submodule aborts before touching the outer repo,
        with `--submodules` passed.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--submodules",
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
        creating any branch, with `--submodules` passed.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--submodules",
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
        any branch, with `--submodules` passed.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--submodules",
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
        Test that the default (no `--submodules` flag) is outer-repo-only,
        even when a submodule is present (the submodule is never touched).
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
            mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="HelpersTask1290_Test",
            ),
            # A submodule is present, but must be ignored since
            # `--submodules` was not passed.
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

    def test11(self) -> None:
        """
        Test that `--gh_project` given as a URL adds an existing issue to the
        project, before creating the branch.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_id",
            "1290",
            "--gh_project",
            "https://github.com/users/gpsaggese/projects/4",
        ]
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="HelpersTask1290_Test",
            ),
            mock.patch("helpers.hgit.has_submodules", return_value=False),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_repo_full_name_from_cmd",
                return_value=("github.com/gpsaggese/umd_classes", "umd_classes"),
            ),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_gh_issue_title",
                return_value=(
                    "HelpersTask1290_Test",
                    "http://example.com/1290",
                ),
            ),
            mock.patch("helpers.hgit.does_branch_exist", return_value=False),
        ):
            self._run_main(argv)
        # Check outputs.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('gh project item-add 4 --owner gpsaggese --url https://github.com/gpsaggese/umd_classes/issues/1290',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test12(self) -> None:
        """
        Test that `--gh_project` given as a title is resolved before the issue
        is created and that the new issue is then added to the project.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_title",
            "Test Issue",
            "--gh_project",
            "Optimal_strategy_for_racket_sports",
        ]
        projects = [
            {"number": 2, "title": "Other"},
            {"number": 4, "title": "Optimal_strategy_for_racket_sports"},
        ]
        cmds: List[str] = []
        system_to_string_side_effect = _make_system_to_string_side_effect(
            projects, cmds
        )
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch(
                "helpers.hsystem.system_to_string",
                side_effect=system_to_string_side_effect,
            ),
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="HelpersTask1290_Test",
            ),
            mock.patch("helpers.hgit.has_submodules", return_value=False),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_repo_full_name_from_cmd",
                return_value=("github.com/gpsaggese/umd_classes", "umd_classes"),
            ),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._dassert_no_duplicate_open_issue"
            ),
        ):
            self._run_main(argv)
        # Check outputs: the project is resolved before the issue is created.
        expected_cmds = [
            "gh project list --owner gpsaggese --limit 200 --format json",
            "invoke gh_issue_create --title 'Test Issue' --assignees @me",
        ]
        self.assert_equal(str(cmds), str(expected_cmds))
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('gh project item-add 4 --owner gpsaggese --url https://github.com/gpsaggese/umd_classes/issues/1290',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test13(self) -> None:
        """
        Test that a `--gh_project` title matching no project aborts before the
        issue is created.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_title",
            "Test Issue",
            "--gh_project",
            "Missing_project",
        ]
        projects = [{"number": 2, "title": "Other"}]
        cmds: List[str] = []
        system_to_string_side_effect = _make_system_to_string_side_effect(
            projects, cmds
        )
        # Run test with mocked system calls.
        with (
            hunteuti.capture_sys_calls() as invocations,
            mock.patch(
                "helpers.hsystem.system_to_string",
                side_effect=system_to_string_side_effect,
            ),
            mock.patch("helpers.hgit.is_client_clean", return_value=True),
            mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="HelpersTask1290_Test",
            ),
            mock.patch("helpers.hgit.has_submodules", return_value=False),
            mock.patch(
                "helpers.lib_tasks.lib_tasks_gh._get_repo_full_name_from_cmd",
                return_value=("github.com/gpsaggese/umd_classes", "umd_classes"),
            ),
        ):
            with self.assertRaises(AssertionError):
                self._run_main(argv)
        # Check outputs: only the project lookup ran, no issue was created.
        expected_cmds = [
            "gh project list --owner gpsaggese --limit 200 --format json",
        ]
        self.assert_equal(str(cmds), str(expected_cmds))
        hunteuti.assert_sys_calls(self, invocations, "[]")
