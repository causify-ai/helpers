import logging
import os
import unittest.mock as umock

import pytest

import dev_scripts_helpers.github.dockerized_sync_gh_issue_labels as dshgdsgil
import dev_scripts_helpers.github.sync_gh_issue_labels as dshgsgila
import helpers.hgit as hgit
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_sync_gh_issue_labels1
# #############################################################################


class Test_sync_gh_issue_labels1(hunitest.TestCase):

    # TODO(sandeep): Check the dockerized executable once the CmampTask10710 is fixed.
    @pytest.mark.skipif(
        hserver.is_inside_ci() or hserver.is_dev_csfy(),
        reason="Disabled because of CmampTask10710",
    )
    @umock.patch.dict(os.environ, {"GITHUB_TEST_TOKEN": "fake_token"})
    @umock.patch(
        "dev_scripts_helpers.github.dockerized_sync_gh_issue_labels.github.Github"
    )
    def test1(self, mock_github_cls: umock.Mock) -> None:
        """
        Test that the dockerized executable reads the input file, performs the
        necessary operations, and writes the backup file in the git root
        directory.
        """
        # Set up mock labels.
        input_label = dshgdsgil.Label("bug", "Something isn't working", "f29513")
        mock_label = umock.Mock()
        mock_label.name = input_label.name
        mock_label.color = input_label.color
        mock_label.description = input_label.description
        # Set up mock GitHub repo
        mock_repo = umock.Mock()
        mock_repo.get_labels.return_value = [mock_label]
        mock_repo.name = "test-repo"
        mock_repo.owner.login = "test-owner"
        # Set up mock GitHub client
        mock_client = umock.Mock()
        mock_client.get_repo.return_value = mock_repo
        mock_github_cls.return_value = mock_client
        # Prepare input arguments.
        input_args = {
            "in_dir_name": self.get_input_dir(),
            "owner": "test-owner",
            "repo": "test-repo",
            "token_env_var": "GITHUB_TEST_TOKEN",
        }
        input_file_path = os.path.join(
            input_args["in_dir_name"], "test_gh_issues_labels.yml"
        )
        git_root_dir = hgit.get_client_root(False)
        backup_file_name = "tmp.labels.causify-ai.helpers.yaml"
        backup_file_path = os.path.join(git_root_dir, backup_file_name)
        # Remove backup file if it exists.
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
        # Run.
        with umock.patch(
            "sys.argv",
            [
                "script",
                "--input_file",
                input_file_path,
                "--owner",
                input_args["owner"],
                "--repo",
                input_args["repo"],
                "--token_env_var",
                input_args["token_env_var"],
                "--backup",
                "--no_interactive",
                "--dry_run",
            ],
        ):
            parser = dshgsgila._parse()
            dshgsgila._main(parser)
        # Check that the backup file exists.
        self.assertTrue(
            os.path.exists(backup_file_path),
            msg="Backup file was not created.",
        )
