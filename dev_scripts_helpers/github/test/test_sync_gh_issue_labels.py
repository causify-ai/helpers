import logging
import os
import unittest.mock as umock

import pytest

import dev_scripts_helpers.github.sync_gh_issue_labels as dshgsgila
import helpers.hgit as hgit
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_sync_gh_issue_labels1
# #############################################################################


class Test_sync_gh_issue_labels1(hunitest.TestCase):

    @pytest.mark.skipif(
        hserver.is_inside_ci() or hserver.is_dev_csfy(),
        reason="Disabled because of CmampTask10710",
    )
    @umock.patch(
        "dev_scripts_helpers.github.dockerized_sync_gh_issue_labels.github.Github"
    )
    def test1(self, mock_github: umock.Mock) -> None:
        """
        Test that the dockerized executable reads the input file, performs the
        necessary operations, and writes the backup file in the git root
        directory.
        """
        # Set up mock labels.
        label_data = {
            "name": "bug",
            "color": "f29513",
            "description": "Something isn't working",
        }
        mock_label = umock.Mock()
        for k, v in label_data.items():
            setattr(mock_label, k, v)
        # Set up mock GitHub repo.
        mock_repo = umock.Mock()
        mock_repo.get_labels.return_value = [mock_label]
        mock_client = umock.Mock()
        mock_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_client
        # Prepare input arguments.
        input_args = {
            "in_dir_name": self.get_input_dir(),
            "owner": "test-org",
            "repo": "test-repo",
            "token_env_var": "GITHUB_TEST_TOKEN",
        }
        input_file_path = os.path.join(
            input_args["in_dir_name"], "test_gh_issues_labels.yml"
        )
        git_root_dir = hgit.get_client_root(False)
        backup_file_name = "tmp.labels.test-org.test-repo.yaml"
        backup_file_path = os.path.join(git_root_dir, backup_file_name)
        # Remove backup file if it exists.
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
        # Run test.
        dshgsgila._run_dockerized_sync_gh_issue_labels(
            input_file_path,
            input_args["owner"],
            input_args["repo"],
            input_args["token_env_var"],
            dry_run=False,
            no_interactive=True,
            prune=False,
            backup=True,
        )
        # Check that the backup file exists.
        self.assertTrue(
            os.path.exists(backup_file_path),
            msg="Backup file was not created.",
        )
