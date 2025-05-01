import os
import tempfile
import unittest

import yaml

from dev_scripts_helpers.github.dockerized_sync_gh_issue_labels import Label


def get_test_data() -> None:
    """
    Prepare test data for label tests.
    """
    test_label = Label(
        name="test-label", description="A test label", color="#FF0000"
    )
    test_labels = [
        Label("bug", "Bug label", "#FF0000"),
        Label("feature", "Feature label", "#00FF00"),
        Label("documentation", "Doc label", "#0000FF"),
        Label("todo", None, "#ABCDEF"),
    ]
    return test_label, test_labels


# #############################################################################
# TestLabel
# #############################################################################


class TestLabel(unittest.TestCase):
    """
    Test the Label class functionality.
    """

    def test_label_initialization(self) -> None:
        """
        Test label initialization.
        """
        # Test label with description.
        test_label, _ = get_test_data()
        self.assertEqual(test_label.name, "test-label")
        self.assertEqual(test_label.description, "A test label")
        self.assertEqual(test_label.color, "FF0000")
        # Strip '#' from color code.
        label = Label("test", "test desc", "#123456")
        self.assertEqual(label.color, "123456")

    def test_label_properties(self) -> None:
        """
        Test label property accessors.
        """
        label = Label("test", "test desc", "#123456")
        self.assertEqual(label.name, "test")
        self.assertEqual(label.description, "test desc")
        self.assertEqual(label.color, "123456")

    def test_label_to_dict(self) -> None:
        """
        Test label to dictionary conversion.
        """
        test_label, _ = get_test_data()
        expected = {
            "name": "test-label",
            "description": "A test label",
            "color": "FF0000",
        }
        self.assertEqual(test_label.to_dict(), expected)

    def test_label_repr(self) -> None:
        """
        Test label string representation.
        """
        expected = (
            "label(name='test-label', description='A test label', "
            "color='FF0000')"
        )
        test_label, _ = get_test_data()
        self.assertEqual(repr(test_label), expected)

    def test_load_labels(self) -> None:
        """
        Test loading labels from YAML file.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as temp_file:
            yaml_data = [
                {"name": "bug", "description": "Bug label", "color": "#FF0000"},
                {
                    "name": "feature",
                    "description": "Feature label",
                    "color": "#00FF00",
                },
                {"name": "todo", "description": None, "color": "#ABCDEF"},
            ]
            yaml.dump(yaml_data, temp_file, default_flow_style=False)
            temp_file_path = temp_file.name
        try:
            loaded_labels = Label.load_labels(temp_file_path)
            self.assertEqual(len(loaded_labels), 3)
            self.assertEqual(loaded_labels[0].name, "bug")
            self.assertEqual(loaded_labels[0].description, "Bug label")
            self.assertEqual(loaded_labels[0].color, "FF0000")
            self.assertEqual(loaded_labels[1].name, "feature")
            self.assertEqual(loaded_labels[1].description, "Feature label")
            self.assertEqual(loaded_labels[1].color, "00FF00")
            self.assertEqual(loaded_labels[2].name, "todo")
            self.assertIsNone(loaded_labels[2].description)
            self.assertEqual(loaded_labels[2].color, "ABCDEF")
        finally:
            os.unlink(temp_file_path)

    def test_save_labels(self) -> None:
        """
        Test saving labels to YAML file.
        """
        with tempfile.NamedTemporaryFile(
            suffix=".yml", delete=False
        ) as temp_file:
            temp_file_path = temp_file.name
        test_label, test_labels = get_test_data()
        try:
            Label.save_labels(test_labels, temp_file_path)
            with open(temp_file_path, "r", encoding="utf-8") as file:
                saved_data = yaml.safe_load(file)
            self.assertEqual(len(saved_data), 4)
            self.assertEqual(saved_data[0]["name"], "bug")
            self.assertEqual(saved_data[0]["description"], "Bug label")
            self.assertEqual(saved_data[0]["color"], "FF0000")
            self.assertEqual(saved_data[1]["name"], "feature")
            self.assertEqual(saved_data[1]["description"], "Feature label")
            self.assertEqual(saved_data[1]["color"], "00FF00")
            self.assertEqual(saved_data[2]["name"], "documentation")
            self.assertEqual(saved_data[2]["description"], "Doc label")
            self.assertEqual(saved_data[2]["color"], "0000FF")
            self.assertEqual(saved_data[3]["name"], "todo")
            self.assertIsNone(saved_data[3]["description"])
            self.assertEqual(saved_data[3]["color"], "ABCDEF")
        finally:
            os.unlink(temp_file_path)

    def test_round_trip_integrity(self) -> None:
        """
        Test that save_labels() followed by load_labels() preserves data.
        """
        with tempfile.NamedTemporaryFile(
            suffix=".yml", delete=False
        ) as temp_file:
            temp_file_path = temp_file.name
        test_label, test_labels = get_test_data()
        try:
            # Save labels to file.
            Label.save_labels(test_labels, temp_file_path)
            # Load labels back.
            loaded_labels = Label.load_labels(temp_file_path)
            # Compare original and loaded labels.
            self.assertEqual(len(loaded_labels), len(test_labels))
            for orig, loaded in zip(test_labels, loaded_labels):
                self.assertEqual(orig.name, loaded.name)
                self.assertEqual(orig.description, loaded.description)
                self.assertEqual(orig.color, loaded.color)
        finally:
            os.unlink(temp_file_path)

    def test_load_labels_error(self) -> None:
        """
        Test error handling for load_labels with non-existent file.
        """
        with self.assertRaises(FileNotFoundError):
            Label.load_labels("non_existent_file.yml")
