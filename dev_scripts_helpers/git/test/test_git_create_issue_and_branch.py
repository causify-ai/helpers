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
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch("os.getcwd", return_value="/home/user/helpers1"):
                worktree_path = dshggciab._create_worktree(branch_name, issue_id)
        # Check outputs.
        expected_str = r"""[
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
                        "helpers.hgit.get_branch_name",
                        return_value="HelpersTask1290_Test",
                    ):
                        with mock.patch(
                            "helpers.hgit.has_submodules", return_value=False
                        ):
                            with mock.patch(
                                "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
                            ):
                                dshggciab._main(parser)
        # Check outputs: only git_branch_create is captured (system_to_string is mocked).
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
                    "helpers.hgit.get_branch_name",
                    return_value="HelpersTask1290_Test",
                ):
                    with mock.patch(
                        "helpers.hgit.has_submodules", return_value=False
                    ):
                        with mock.patch(
                            "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
                        ):
                            dshggciab._main(parser)
        # Check outputs: git_branch_create called with existing issue ID.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
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
                    "helpers.hgit.get_branch_name",
                    return_value="HelpersTask1290_Test",
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
                                with mock.patch("builtins.print"):
                                    dshggciab._main(parser)
        # Check outputs: git_branch_create and git worktree add calls.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1290',),
        'kwargs': {'log_level': 20},
        },
        {
        'function': hsystem.system,
        'args': ('git worktree add /home/user/helpers1_worktree_1290 HelpersTask1290_Test',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test5(self) -> None:
        """
        Test creating issue with body from file.
        """
        # Prepare inputs.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_title",
            "Test Issue",
            "--gh_issue_body_file",
            "/tmp/test_body.txt",
        ]
        # Run test with mocked system calls.
        parser = dshggciab._parse()
        with mock.patch("sys.argv", argv):
            with hunteuti.capture_sys_calls() as invocations:
                with mock.patch("helpers.hdbg.dassert_file_exists"):
                    with mock.patch(
                        "builtins.open",
                        mock.mock_open(read_data="Body content from file"),
                    ):
                        with mock.patch(
                            "helpers.hsystem.system_to_string",
                            return_value=("", "Created issue #1291"),
                        ):
                            with mock.patch(
                                "helpers.hgit.get_branch_name",
                                return_value="HelpersTask1291_Test",
                            ):
                                with mock.patch(
                                    "helpers.hgit.has_submodules",
                                    return_value=False,
                                ):
                                    with mock.patch(
                                        "dev_scripts_helpers.git.git_create_issue_and_branch._commit_issue_files"
                                    ):
                                        dshggciab._main(parser)
        # Check outputs: git_branch_create called with parsed issue ID from system_to_string.
        expected = r"""[
        {
        'function': hsystem.system,
        'args': ('invoke git_branch_create --issue-id 1291',),
        'kwargs': {'log_level': 20},
        },
        ]"""
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test6(self) -> None:
        """
        Test that --gh_issue_body and --gh_issue_body_file are mutually exclusive.
        """
        # Prepare inputs: try to use both body options.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_title",
            "Test Issue",
            "--gh_issue_body",
            "Body text",
            "--gh_issue_body_file",
            "/tmp/body.txt",
        ]
        # Run test and expect error from argparse.
        parser = dshggciab._parse()
        with self.assertRaises(SystemExit):
            with mock.patch("sys.argv", argv):
                dshggciab._main(parser)

    def test7(self) -> None:
        """
        Test that --gh_issue_title and --gh_issue_id are mutually exclusive.
        """
        # Prepare inputs: try to use both issue source options.
        argv = [
            "git_create_issue_and_branch.py",
            "--gh_issue_title",
            "Test Issue",
            "--gh_issue_id",
            "1290",
        ]
        # Run test and expect error from argparse.
        parser = dshggciab._parse()
        with self.assertRaises(SystemExit):
            with mock.patch("sys.argv", argv):
                dshggciab._main(parser)
