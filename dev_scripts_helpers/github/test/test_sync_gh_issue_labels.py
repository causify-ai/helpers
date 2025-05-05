import logging
import os
import unittest.mock as umock

import pytest

import dev_scripts_helpers.github.sync_gh_issue_labels as dshgsgila
import helpers.hgit as hgit
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_sync_gh_issue_labels1
# #############################################################################


@pytest.mark.slow("~6 sec.")
class Test_sync_gh_issue_labels1(hunitest.TestCase):

    @umock.patch(
        "dev_scripts_helpers.github.dockerized_sync_gh_issue_labels.github.Github"
    )
    def test_backup_file_written(self, mock_github: umock.Mock) -> None:
        """
        Test that the backup file is written as intended by mocking GitHub API
        interactions.
        """
        # Set up mock GitHub repo and labels.
        mock_label = umock.Mock()
        mock_label.name = "bug"
        mock_label.color = "f29513"
        mock_label.description = "Something isn't working"
        mock_repo = umock.Mock()
        mock_repo.get_labels.return_value = [mock_label]
        mock_client = umock.Mock()
        mock_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_client
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test_gh_issues_labels.yml")
        owner = "test-org"
        repo = "test-repo"
        git_root_dir = hgit.get_client_root(False)
        backup_file_name = f"tmp.labels.{owner}.{repo}.yaml"
        backup_file_path = os.path.join(git_root_dir, backup_file_name)
        # Remove backup file if it exists.
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
        # Run test.
        dshgsgila._run_dockerized_sync_gh_issue_labels(
            input_file_path,
            owner,
            repo,
            "fake_token",
            dry_run=False,
            no_interactive=True,
            prune=False,
            backup=True,
        )
        # Check that the backup file exists.
        self.assertTrue(os.path.exists(backup_file_path))
        # Check the contents of the backup file.
        with open(backup_file_path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("name: bug", content)
        self.assertIn("color: f29513", content)
        self.assertIn("description: Something isn't working", content)
