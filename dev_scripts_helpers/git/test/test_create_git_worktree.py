"""
End-to-end tests for `create_git_worktree.py`.

Import as:

import dev_scripts_helpers.git.test.test_create_git_worktree as dsggtccgw
"""

import os
import unittest.mock as mock

import helpers.hunit_test as hunitest
import dev_scripts_helpers.git.create_git_worktree as dsgcgw


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
    actual = dsgcgw._format_title_for_branch(raw_title, issue_id)
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
    actual = dsgcgw._parse_issue_number_from_url(url)
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
    parser = dsgcgw._parse()
    with mock.patch("sys.argv", argv):
      with self.assertRaises(AssertionError):
        dsgcgw._main(parser)
