import logging
import os
import unittest.mock as umock
from typing import Dict, Generator, List, Optional

import pytest

import dev_scripts_helpers.github.dockerized_sync_gh_issue_labels as dshgdsgil
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _get_label_data() -> Dict[str, str]:
    return {"name": "test", "description": "test label", "color": "FF0000"}


def _make_mock_label(label_data: Dict[str, str]) -> umock.Mock:
    label = umock.Mock()
    label.name = label_data["name"]
    label.color = label_data["color"]
    label.description = label_data["description"]
    return label


# #############################################################################
# TestLabel1
# #############################################################################


class TestLabel1(hunitest.TestCase):

    def test_save_label(self) -> None:
        """
        Test saving a label object to a file.
        """
        # Prepare inputs.
        label_data = _get_label_data()
        input_label = dshgdsgil.Label(
            label_data["name"], label_data["description"], label_data["color"]
        )
        temp_dir = self.get_scratch_space()
        tmp_file_name = os.path.join(temp_dir, "test_labels.yaml")
        # Run.
        dshgdsgil.Label.save_labels([input_label], tmp_file_name)
        # Check the output.
        actual = hio.from_file(tmp_file_name)
        expected = f"""
        - name: {label_data["name"]}
          description: {label_data["description"]}
          color: {label_data["color"]}
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_load_label(self) -> None:
        """
        Test loading a label object from a file.
        """
        # Prepare inputs.
        label_data = _get_label_data()
        temp_dir = self.get_scratch_space()
        tmp_file_name = os.path.join(temp_dir, "test_labels.yaml")
        # Create a file with known content.
        txt = f"""
        - name: {label_data["name"]}
          description: {label_data["description"]}
          color: {label_data["color"]}
        """
        hio.to_file(tmp_file_name, txt)
        # Load the label.
        output_labels = dshgdsgil.Label.load_labels(tmp_file_name)
        output_label = output_labels[0]
        # Check the output.
        actual = f"""
        name={output_label.name}
        description={output_label.description}
        color={output_label.color}
        """
        expected = f"""
        name={label_data["name"]}
        description={label_data["description"]}
        color={label_data["color"]}
        """
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# TestDockerizedSyncGitHubIssueLabels
# #############################################################################


class TestDockerizedSyncGitHubIssueLabels(hunitest.TestCase):

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        self.setUp()
        # Prepare inputs.
        self.temp_dir = self.get_scratch_space()
        self.tmp_file_name = os.path.join(self.temp_dir, "test_labels.yaml")
        self.input_args = {
            "owner": "test-org",
            "repo": "test-repo",
            "token_env_var": "GITHUB_TOKEN",
            "input_file": self.tmp_file_name,
            "no_interactive": True,
        }
        # Mock the GitHub client.
        self.mock_repo = umock.Mock()
        self.mock_client = umock.Mock()
        self.mock_client.get_repo.return_value = self.mock_repo
        self.github_patch = umock.patch(
            "github.Github", return_value=self.mock_client
        )
        self.env_patch = umock.patch.dict(
            os.environ, {"GITHUB_TOKEN": "fake_token"}
        )
        self.github_patch.start()
        self.env_patch.start()

    def tear_down_test(self) -> None:
        # Stop the patches.
        self.github_patch.stop()
        self.env_patch.stop()

    def test_create_new_label(self) -> None:
        """
        Test that a new label is created when it exists in yaml but not in
        repo.
        """
        # Prepare inputs.
        self.mock_repo.get_labels.return_value = []
        label_data = _get_label_data()
        input_label = self._save_label(label_data)
        # Run.
        self._run_with_args()
        # Check if the mock was called.
        self.mock_repo.create_label.assert_called_once_with(
            name=input_label.name,
            color=input_label.color,
            description=input_label.description,
        )

    def test_update_existing_label(self) -> None:
        """
        Test that a label is updated when it exists in both yaml and repo with
        different properties.
        """
        # Prepare inputs.
        repo_label_data = {
            "name": "test",
            "description": "old desc",
            "color": "00FF00",
        }
        yaml_label_data = {
            "name": "test",
            "description": "new desc",
            "color": "FF0000",
        }
        mock_label = _make_mock_label(repo_label_data)
        self.mock_repo.get_labels.return_value = [mock_label]
        input_label = self._save_label(yaml_label_data)
        # Run.
        self._run_with_args()
        # Check if the mock was called.
        mock_label.edit.assert_called_once_with(
            name=input_label.name,
            color=input_label.color,
            description=input_label.description,
        )

    def test_identical_label(self) -> None:
        """
        Test that no changes are made when label exists and is identical.
        """
        # Prepare inputs.
        label_data = _get_label_data()
        mock_label = _make_mock_label(label_data)
        self.mock_repo.get_labels.return_value = [mock_label]
        self._save_label(label_data)
        # Run.
        self._run_with_args()
        # Check if the mock was called.
        mock_label.edit.assert_not_called()
        mock_label.delete.assert_not_called()

    def test_prune_label(self) -> None:
        """
        Test that labels that exist in repo but not in yaml are deleted when
        prune is enabled.
        """
        # Prepare inputs.
        repo_label1 = {
            "name": "to_prune1",
            "description": "desc1",
            "color": "FF0000",
        }
        repo_label2 = {
            "name": "to_prune2",
            "description": "desc2",
            "color": "00FF00",
        }
        mock_label1 = _make_mock_label(repo_label1)
        mock_label2 = _make_mock_label(repo_label2)
        self.mock_repo.get_labels.return_value = [mock_label1, mock_label2]
        # Test with no labels in the YAML file.
        dshgdsgil.Label.save_labels([], self.tmp_file_name)
        # Run.
        self._run_with_args(extra_args=["--prune"])
        # Check if the mock was called.
        mock_label1.delete.assert_called_once()
        mock_label2.delete.assert_called_once()

    def _run_with_args(self, *, extra_args: Optional[List[str]] = None) -> None:
        """
        Run `dockerized_sync_gh_issue_labels.py` script with the given
        arguments.

        :param extra_args: additional arguments to pass to the script
        """
        args = [
            "--input_file",
            self.input_args["input_file"],
            "--owner",
            self.input_args["owner"],
            "--repo",
            self.input_args["repo"],
            "--token_env_var",
            self.input_args["token_env_var"],
        ]
        if self.input_args.get("no_interactive", False):
            args.append("--no_interactive")
        if extra_args:
            args += extra_args
        with umock.patch("sys.argv", ["script"] + args):
            parser = dshgdsgil._parse()
            dshgdsgil._main(parser)

    def _save_label(self, label_data: Dict[str, str]) -> dshgdsgil.Label:
        """
        Create a Label from label_data and save it to a YAML file.

        :param label_data: the label data to save
        :return: the Label instance
        """
        label = dshgdsgil.Label(
            label_data["name"], label_data["description"], label_data["color"]
        )
        dshgdsgil.Label.save_labels([label], self.tmp_file_name)
        return label
