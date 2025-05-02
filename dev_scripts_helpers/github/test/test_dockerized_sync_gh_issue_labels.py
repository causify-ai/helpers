import logging
import os
import tempfile

import yaml

import dev_scripts_helpers.github.dockerized_sync_gh_issue_labels as dshgdsgil
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _get_label_data() -> dict:
    return {"name": "test", "description": "test label", "color": "#FF0000"}


# #############################################################################
# Test_Label1
# #############################################################################


class Test_Label1(hunitest.TestCase):

    def test_load_labels(self) -> None:
        """
        Test loading labels from a YAML file.
        """
        label_data = _get_label_data()
        curr_dir = os.getcwd()
        with tempfile.NamedTemporaryFile(
            dir=curr_dir, mode="w", encoding="utf-8", delete=False
        ) as tmp_file:
            yaml.dump([label_data], tmp_file)
            tmp_file_name = tmp_file.name
        try:
            labels = dshgdsgil.Label.load_labels(tmp_file_name)
            self.assertEqual(len(labels), 1)
            self.assertEqual(labels[0].name, "test")
            self.assertEqual(labels[0].description, "test label")
            self.assertEqual(labels[0].color, "FF0000")
        finally:
            os.remove(tmp_file_name)

    def test_save_labels(self) -> None:
        """
        Test saving labels to a YAML file.
        """
        label_data = _get_label_data()
        label = dshgdsgil.Label(
            label_data["name"], label_data["description"], label_data["color"]
        )
        curr_dir = os.getcwd()
        with tempfile.NamedTemporaryFile(
            dir=curr_dir, mode="w", encoding="utf-8", delete=False
        ) as tmp_file:
            tmp_file_name = tmp_file.name
        try:
            dshgdsgil.Label.save_labels([label], tmp_file_name)
            with open(tmp_file_name, "r", encoding="utf-8") as f:
                saved_data = yaml.safe_load(f)
            self.assertEqual(len(saved_data), 1)
            self.assertEqual(saved_data[0]["name"], "test")
            self.assertEqual(saved_data[0]["description"], "test label")
            self.assertEqual(saved_data[0]["color"], "FF0000")
        finally:
            os.remove(tmp_file_name)
