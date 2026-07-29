"""
End-to-end tests for `git_create_issue_and_branch.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_create_issue_and_branch as dsggtgiab
"""

import unittest.mock as mock

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.git.git_create_issue_and_branch as dshggciab


# #############################################################################
# Test_create_worktree
# #############################################################################


class Test_create_worktree(hunitest.TestCase):
    """
    Tests for `_create_worktree()` function.
    """

    def test1(self) -> None:
        """
        Test creating a worktree.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1290_Test_Branch"
        issue_id = 1290
        original_branch = "master"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch("os.getcwd", return_value="/home/user/helpers1"):
                worktree_path = dshggciab._create_worktree(branch_name, issue_id, original_branch)
        # Check outputs.
        expected_str = r"""[
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
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)
        # Verify returned worktree path.
        expected_path = "/home/user/helpers1_worktree_1290"
        self.assertEqual(worktree_path, expected_path)


# #############################################################################
# Test_git_create_issue_and_branch_py
# #############################################################################


class Test_git_create_issue_and_branch_py(hunitest.TestCase):
    """
    End-to-end tests for the `git_create_issue_and_branch.py` executable.
    """

    def test1(self) -> None:
        """
        Test that script validates title is provided when creating new issue.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
        ]
        # Run test and check for error.
        parser = dshggciab._parse()
        with mock.patch("sys.argv", argv):
            with self.assertRaises(AssertionError):
                dshggciab._main(parser)

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
        parser = dshggciab._parse()
        with mock.patch("sys.argv", argv):
            with hunteuti.capture_sys_calls() as invocations:
                with mock.patch(
                    "helpers.hsystem.system_to_string",
                    return_value=("", "Created issue #1290"),
                ):
                    with mock.patch(
                        "helpers.hgit.get_branch_name", return_value="HelpersTask1290_Test"
                    ):
                        with mock.patch(
                            "helpers.hgit.has_submodules", return_value=False
                        ):
                            with mock.patch(
                                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
                            ):
                                dshggciab._main(parser)
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
        parser = dshggciab._parse()
        with mock.patch("sys.argv", argv):
            with hunteuti.capture_sys_calls() as invocations:
                with mock.patch(
                    "helpers.hgit.get_branch_name", return_value="HelpersTask1290_Test"
                ):
                    with mock.patch(
                        "helpers.hgit.has_submodules", return_value=False
                    ):
                        with mock.patch(
                            "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
                        ):
                            dshggciab._main(parser)
        # Check outputs.
        # TODO(ai_gp): Fill this in.
        expected = r"""[
        ]"""
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
        parser = dshggciab._parse()
        with mock.patch("sys.argv", argv):
            with hunteuti.capture_sys_calls() as invocations:
                with mock.patch(
                    "helpers.hgit.get_branch_name", return_value="HelpersTask1290_Test"
                ):
                    with mock.patch(
                        "helpers.hgit.has_submodules", return_value=False
                    ):
                        with mock.patch(
                            "os.getcwd", return_value="/home/user/helpers1"
                        ):
                            with mock.patch(
                                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
                            ):
                                with mock.patch(
                                    "shutil.copy"
                                ):
                                    with mock.patch(
                                        "builtins.print"
                                    ):
                                        dshggciab._main(parser)
        # Check outputs.
        # TODO(ai_gp): Fill this in.
        expected = r"""[
        ]"""
        hunteuti.assert_sys_calls(self, invocations, expected)
