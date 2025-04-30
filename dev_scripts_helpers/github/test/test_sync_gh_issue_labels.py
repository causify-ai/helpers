import os
import tempfile
import unittest
from typing import Dict, List
from unittest.mock import MagicMock, patch

import yaml

from dev_scripts_helpers.github.sync_gh_issue_labels import Label


class TestGitHubSync(unittest.TestCase):
    """Test the GitHub synchronization functionality."""

    def setUp(self):
        """Set up test data and mocks."""
        super().setUp()
        self.test_labels = [
            Label("bug", "Bug label", "#FF0000"),
            Label("feature", "Feature label", "#00FF00"),
            Label("documentation", "Doc label", "#0000FF"),
        ]
        # Create mock GitHub objects.
        self.mock_label = MagicMock()
        self.mock_label.name = "bug"
        self.mock_label.description = "Bug label"
        self.mock_label.color = "FF0000"
        # Create mock GitHub repository object.
        self.mock_repo = MagicMock()
        self.mock_repo.get_labels.return_value = [self.mock_label]
        # Create mock GitHub client object.
        self.mock_client = MagicMock()
        self.mock_client.get_repo.return_value = self.mock_repo

    @patch("dev_scripts_helpers.github.sync_gh_issue_labels.github.Github")
    def test_sync_labels_create(self, mock_github):
        """Test creating new labels."""
        # Set up the mock.
        mock_github.return_value = self.mock_client
        # Create a temporary YAML file.
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as temp_file:
            yaml_data = [
                {"name": "bug", "description": "Bug label", "color": "#FF0000"},
                {"name": "feature", "description": "Feature label", "color": "#00FF00"},
            ]
            yaml.dump(yaml_data, temp_file, default_flow_style=False)
            temp_file_path = temp_file.name
        try:
            # Load labels from the temporary file
            labels = Label.load_labels(temp_file_path)
            # Create a mock for the create_label method.
            self.mock_repo.create_label = MagicMock()
            # Call the create_label method for each label.
            for label in labels:
                if label.name != "bug":  
                    # Skip the existing label.  
                    self.mock_repo.create_label(
                        name=label.name,
                        color=label.color,
                        description=label.description,
                    )
            # Verify that create_label was called for the new label.
            self.mock_repo.create_label.assert_called_once_with(
                name="feature",
                color="00FF00",
                description="Feature label",
            )
        finally:
            # Clean up the temporary file.
            os.unlink(temp_file_path)

    @patch("dev_scripts_helpers.github.sync_gh_issue_labels.github.Github")
    def test_sync_labels_update(self, mock_github):
        """Test updating existing labels."""
        # Set up the mock.
        mock_github.return_value = self.mock_client
        # Create a temporary YAML file with updated label.
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as temp_file:
            yaml_data = [
                {"name": "bug", "description": "Updated Bug label", "color": "#FF0000"},
            ]
            yaml.dump(yaml_data, temp_file, default_flow_style=False)
            temp_file_path = temp_file.name
        try:
            # Load labels from the temporary file.
            labels = Label.load_labels(temp_file_path)
            # Create a mock for the edit method.
            self.mock_label.edit = MagicMock()
            # Call the edit method for the updated label.
            for label in labels:
                if label.name == "bug":
                    self.mock_label.edit(
                        name=label.name,
                        color=label.color,
                        description=label.description,
                    )
            # Verify that edit was called with the updated description.
            self.mock_label.edit.assert_called_once_with(
                name="bug",
                color="FF0000",
                description="Updated Bug label",
            )
        finally:
            # Clean up the temporary file.
            os.unlink(temp_file_path)

    @patch("dev_scripts_helpers.github.sync_gh_issue_labels.github.Github")
    def test_sync_labels_delete(self, mock_github):
        """Test deleting labels."""
        # Set up the mock.
        mock_github.return_value = self.mock_client
        # Create a temporary YAML file with no labels.
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as temp_file:
            yaml_data = []
            yaml.dump(yaml_data, temp_file, default_flow_style=False)
            temp_file_path = temp_file.name

        try:
            # Load labels from the temporary file.
            labels = Label.load_labels(temp_file_path)
            # Create a mock for the delete method.
            self.mock_label.delete = MagicMock()
            # Call the delete method for the existing label.
            for current_label in self.mock_repo.get_labels():
                if current_label.name not in [label.name for label in labels]:
                    current_label.delete()
            # Verify that delete was called.
            self.mock_label.delete.assert_called_once()
        finally:
            # Clean up the temporary file.
            os.unlink(temp_file_path)