import os
import tempfile
import unittest
from typing import Dict, List

import yaml

from dev_scripts_helpers.github.sync_gh_issue_labels import Label


class TestLabel(unittest.TestCase):
    """Test the Label class functionality."""

    def setUp(self):
        """Set up test data."""
        self.test_label = Label(
            name="test-label",
            description="A test label",
            color="#FF0000"
        )
        self.test_labels = [
            Label("bug", "Bug label", "#FF0000"),
            Label("feature", "Feature label", "#00FF00"),
            Label("documentation", "Doc label", "#0000FF"),
        ]

    def test_label_initialization(self):
        """Test label initialization."""
        self.assertEqual(self.test_label.name, "test-label")
        self.assertEqual(self.test_label.description, "A test label")
        self.assertEqual(self.test_label.color, "FF0000")  # Note: # is stripped

    def test_label_to_dict(self):
        """Test label to dictionary conversion."""
        expected = {
            "name": "test-label",
            "description": "A test label",
            "color": "FF0000",
        }
        self.assertEqual(self.test_label.to_dict(), expected)

    def test_label_repr(self):
        """Test label string representation."""
        expected = "label(name='test-label', description='A test label', color='FF0000')"
        self.assertEqual(repr(self.test_label), expected)

    def test_load_labels(self):
        """Test loading labels from YAML file."""
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as temp_file:
            yaml_data = [
                {"name": "bug", "description": "Bug label", "color": "#FF0000"},
                {"name": "feature", "description": "Feature label", "color": "#00FF00"},
            ]
            yaml.dump(yaml_data, temp_file, default_flow_style=False)
            temp_file_path = temp_file.name

        try:
            # Load labels from the temporary file
            loaded_labels = Label.load_labels(temp_file_path)
            
            # Verify the loaded labels
            self.assertEqual(len(loaded_labels), 2)
            self.assertEqual(loaded_labels[0].name, "bug")
            self.assertEqual(loaded_labels[0].description, "Bug label")
            self.assertEqual(loaded_labels[0].color, "FF0000")
            self.assertEqual(loaded_labels[1].name, "feature")
            self.assertEqual(loaded_labels[1].description, "Feature label")
            self.assertEqual(loaded_labels[1].color, "00FF00")
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    def test_save_labels(self):
        """Test saving labels to YAML file."""
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Save labels to the temporary file
            Label.save_labels(self.test_labels, temp_file_path)
            
            # Load the saved labels back
            with open(temp_file_path, "r", encoding="utf-8") as file:
                saved_data = yaml.safe_load(file)
            
            # Verify the saved data
            self.assertEqual(len(saved_data), 3)
            self.assertEqual(saved_data[0]["name"], "bug")
            self.assertEqual(saved_data[0]["description"], "Bug label")
            self.assertEqual(saved_data[0]["color"], "FF0000")
            self.assertEqual(saved_data[1]["name"], "feature")
            self.assertEqual(saved_data[1]["description"], "Feature label")
            self.assertEqual(saved_data[1]["color"], "00FF00")
            self.assertEqual(saved_data[2]["name"], "documentation")
            self.assertEqual(saved_data[2]["description"], "Doc label")
            self.assertEqual(saved_data[2]["color"], "0000FF")
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)