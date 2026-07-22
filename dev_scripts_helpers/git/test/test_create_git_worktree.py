"""
End-to-end tests for `create_git_worktree.py`.

Import as:

import dev_scripts_helpers.git.test.test_create_git_worktree as dsggtccgw
"""

import os
import unittest.mock as mock

import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.git.create_git_worktree as dshgcgiwo


# #############################################################################
# Test_format_title_for_branch
# #############################################################################


class Test_format_title_for_branch(hunitest.TestCase):
    """
    Tests for `_format_title_for_branch()` function.
    """

    def helper(
        self,
        raw_title: str,
        issue_id: int,
        expected: str,
    ) -> None:
        """
        Test helper for `_format_title_for_branch`.

        :param raw_title: Raw GitHub issue title to format
        :param issue_id: Issue number
        :param expected: Expected formatted branch name
        """
        # Run test.
        actual = dshgcgiwo._format_title_for_branch(raw_title, issue_id)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test formatting a simple issue title.
        """
        # Prepare inputs.
        raw_title = "Implement Task Janitor"
        issue_id = 1291
        # Prepare outputs.
        expected = "HelpersTask1291_Implement_Task_Janitor"
        # Run test.
        self.helper(raw_title, issue_id, expected)

    def test2(self) -> None:
        """
        Test formatting title with special characters.
        """
        # Prepare inputs.
        raw_title = "Fix: bug (critical) / urgent"
        issue_id = 1290
        # Prepare outputs.
        expected = "HelpersTask1290_Fix_bug_critical_urgent"
        # Run test.
        self.helper(raw_title, issue_id, expected)

    def test3(self) -> None:
        """
        Test formatting title with multiple spaces.
        """
        # Prepare inputs.
        raw_title = "Update  multiple   spaces"
        issue_id = 100
        # Prepare outputs.
        expected = "HelpersTask100_Update_multiple_spaces"
        # Run test.
        self.helper(raw_title, issue_id, expected)

    def test4(self) -> None:
        """
        Test formatting empty title (edge case).
        """
        # Prepare inputs.
        raw_title = ""
        issue_id = 1
        # Prepare outputs.
        expected = "HelpersTask1_"
        # Run test.
        self.helper(raw_title, issue_id, expected)

    def test5(self) -> None:
        """
        Test formatting title with quotes and dashes.
        """
        # Prepare inputs.
        raw_title = 'Fix "broken" feature - urgent'
        issue_id = 500
        # Prepare outputs.
        expected = "HelpersTask500_Fix__broken__feature___urgent"
        # Run test.
        self.helper(raw_title, issue_id, expected)


# #############################################################################
# Test_parse_issue_number_from_url
# #############################################################################


class Test_parse_issue_number_from_url(hunitest.TestCase):
    """
    Tests for `_parse_issue_number_from_url()` function.
    """

    def helper(
        self,
        url: str,
        expected: int,
    ) -> None:
        """
        Test helper for `_parse_issue_number_from_url`.

        :param url: GitHub issue URL
        :param expected: Expected issue number
        """
        # Run test.
        actual = dshgcgiwo._parse_issue_number_from_url(url)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test parsing standard GitHub issue URL.
        """
        # Prepare inputs.
        url = "https://github.com/causify-ai/helpers/issues/1290"
        # Prepare outputs.
        expected = 1290
        # Run test.
        self.helper(url, expected)

    def test2(self) -> None:
        """
        Test parsing issue URL with trailing slash.
        """
        # Prepare inputs.
        url = "https://github.com/causify-ai/helpers/issues/999/"
        # Prepare outputs.
        expected = 999
        # Run test.
        self.helper(url, expected)

    def test3(self) -> None:
        """
        Test parsing URL with multiple trailing slashes.
        """
        # Prepare inputs.
        url = "https://github.com/causify-ai/helpers/issues/123///"
        # Prepare outputs.
        expected = 123
        # Run test.
        self.helper(url, expected)

    def test4(self) -> None:
        """
        Test parsing URL with large issue number.
        """
        # Prepare inputs.
        url = "https://github.com/causify-ai/helpers/issues/9999"
        # Prepare outputs.
        expected = 9999
        # Run test.
        self.helper(url, expected)


# #############################################################################
# Test_branch_exists
# #############################################################################


class Test_branch_exists(hunitest.TestCase):
    """
    Tests for `_branch_exists()` function.
    """

    def test1(self) -> None:
        """
        Test that function returns False for non-existent branch.
        """
        # Prepare inputs.
        branch_name = "NonExistentBranch12345"
        # Run test.
        actual = dshgcgiwo._branch_exists(branch_name)
        # Check outputs.
        self.assertFalse(actual)

    def test2(self) -> None:
        """
        Test that function returns True for existing branch when mocked.
        """
        # Prepare inputs.
        branch_name = "SomeBranch"
        # Run test and mock the system call.
        # TODO(ai_gp): Use with hunteuti.capture_sys_calls() as invocations:
        with mock.patch("helpers.hsystem.system", return_value=None):
            actual = dshgcgiwo._branch_exists(branch_name)
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# Test_create_branch
# #############################################################################


class Test_create_branch(hunitest.TestCase):
    """
    Tests for `_create_branch()` function.
    """

    # TODO(ai_gp): Create a helper with /coding.factor_common_code
    def test1(self) -> None:
        """
        Test creating a new branch that doesn't exist.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1290_Test_Branch"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "dev_scripts_helpers.git.create_git_worktree._branch_exists",
                return_value=False,
            ):
                with mock.patch(
                    "dev_scripts_helpers.git.create_git_worktree._commit_issue_files"
                ):
                    dshgcgiwo._create_branch(branch_name, create_pr=True)
        # Check outputs: should call invoke git_branch_create with PR creation
        # enabled.
        expected = """
        [{'args': ('invoke git_branch_create --branch-name '
                   'HelpersTask1290_Test_Branch',),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 20}}]
        """
        hunteuti.assert_sys_calls(self, invocations, expected, dedent=True)

    def test2(self) -> None:
        """
        Test that branch creation is skipped if branch already exists.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1290_Existing_Branch"
        # Run test and mock branch_exists to return True.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "dev_scripts_helpers.git.create_git_worktree._branch_exists",
                return_value=True,
            ):
                dshgcgiwo._create_branch(branch_name, create_pr=True)
        # Check outputs: no system calls should be made.
        expected = "[]"
        hunteuti.assert_sys_calls(self, invocations, expected, dedent=True)

    def test3(self) -> None:
        """
        Test creating a branch without creating a PR.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1290_Test_Branch_No_PR"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "dev_scripts_helpers.git.create_git_worktree._branch_exists",
                return_value=False,
            ):
                with mock.patch(
                    "dev_scripts_helpers.git.create_git_worktree._commit_issue_files"
                ):
                    dshgcgiwo._create_branch(branch_name, create_pr=False)
        # Check outputs: should call invoke git_branch_create with PR creation disabled.
        expected = """
        [{'args': ('invoke git_branch_create --branch-name '
                   'HelpersTask1290_Test_Branch_No_PR --no-create-pr',),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 20}}]
        """
        hunteuti.assert_sys_calls(self, invocations, expected, dedent=True)


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
                worktree_path = dshgcgiwo._create_worktree(branch_name, issue_id)
        # Check outputs.
        expected = """
        [{'args': ('git worktree add /home/user/helpers1_worktree_1290 '
                   'HelpersTask1290_Test_Branch',),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 20}}]
        """
        hunteuti.assert_sys_calls(self, invocations, expected, dedent=True)
        # Verify returned worktree path.
        expected_path = "/home/user/helpers1_worktree_1290"
        self.assertEqual(worktree_path, expected_path)


# #############################################################################
# Test_create_git_worktree_py
# #############################################################################


class Test_create_git_worktree_py(hunitest.TestCase):
    """
    End-to-end tests for the `create_git_worktree.py` executable.
    """

    def test1(self) -> None:
        """
        Test that script validates body file exists using mocking.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        non_existent_file = os.path.join(scratch_dir, "nonexistent.md")
        argv = [
            "create_git_worktree.py",
            "--gh_issue_title",
            "Test Issue",
            "--gh_issue_body_file",
            non_existent_file,
            "--gh_assignee",
            "testuser",
        ]
        # Run test and check for error.
        parser = dshgcgiwo._parse()
        with mock.patch("sys.argv", argv):
            with self.assertRaises(AssertionError):
                dshgcgiwo._main(parser)

    def test3(self) -> None:
        """
        Test --create_worktree flag when False (default).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        body_file = os.path.join(scratch_dir, "body.md")
        with open(body_file, "w") as f:
            f.write("Test body")
        argv = [
            "create_git_worktree.py",
            "--gh_issue_id",
            "1290",
            "--instr_file",
            body_file,
        ]
        # Run test with mocked system calls.
        parser = dshgcgiwo._parse()
        with mock.patch("sys.argv", argv):
            with hunteuti.capture_sys_calls() as invocations:
                with mock.patch(
                    "helpers.hsystem.system_to_string",
                    return_value=("", "Test Issue Title"),
                ):
                    with mock.patch(
                        "dev_scripts_helpers.git.create_git_worktree._check_no_subrepos"
                    ):
                        with mock.patch(
                            "dev_scripts_helpers.git.create_git_worktree._branch_exists",
                            return_value=False,
                        ):
                            with mock.patch(
                                "dev_scripts_helpers.git.create_git_worktree._commit_issue_files"
                            ):
                                dshgcgiwo._main(parser)
        # Check outputs: branch creation via invoke, no worktree creation.
        expected = """
        [{'args': ('invoke git_branch_create --branch-name '
                   'HelpersTask1290_Test_Issue_Title',),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 20}}]
        """
        hunteuti.assert_sys_calls(self, invocations, expected, dedent=True)

    def test4(self) -> None:
        """
        Test --create_worktree flag when True.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        body_file = os.path.join(scratch_dir, "body.md")
        with open(body_file, "w") as f:
            f.write("Test body")
        argv = [
            "create_git_worktree.py",
            "--gh_issue_id",
            "1290",
            "--instr_file",
            body_file,
            "--create_worktree",
        ]
        # Run test with mocked system calls.
        parser = dshgcgiwo._parse()
        # TODO(ai_gp): Find a better way to mock since this is insane.
        with mock.patch("sys.argv", argv):
            with hunteuti.capture_sys_calls() as invocations:
                with mock.patch(
                    "helpers.hsystem.system_to_string",
                    return_value=("", "Test Issue Title"),
                ):
                    with mock.patch(
                        "dev_scripts_helpers.git.create_git_worktree._check_no_subrepos"
                    ):
                        with mock.patch(
                            "dev_scripts_helpers.git.create_git_worktree._branch_exists",
                            return_value=False,
                        ):
                            with mock.patch(
                                "os.getcwd", return_value="/home/user/helpers1"
                            ):
                                with mock.patch(
                                    "dev_scripts_helpers.git.create_git_worktree._commit_issue_files"
                                ):
                                    with mock.patch(
                                        "builtins.print"
                                    ):  # Mock print to avoid output
                                        dshgcgiwo._main(parser)
        # Check outputs: branch creation via invoke and worktree creation.
        expected = """
        [{'args': ('invoke git_branch_create --branch-name '
                   'HelpersTask1290_Test_Issue_Title',),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 20}},
         {'args': ('git worktree add /home/user/helpers1_worktree_1290 '
                   'HelpersTask1290_Test_Issue_Title',),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 20}}]
        """
        hunteuti.assert_sys_calls(self, invocations, expected, dedent=True)
