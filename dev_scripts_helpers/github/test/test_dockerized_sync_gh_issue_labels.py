import logging
import os
import tempfile
from typing import Dict

import dev_scripts_helpers.github.dockerized_sync_gh_issue_labels as dshgdsgil
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _get_label_data() -> Dict[str, str]:
    return {"name": "test", "description": "test label", "color": "#FF0000"}


# #############################################################################
# TestLabel1
# #############################################################################


class TestLabel1(hunitest.TestCase):

    def test_label_save_and_load(self) -> None:
        """
        Test saving and loading a label object.
        """
        # Prepare inputs.
        label_data = _get_label_data()
        input_label = dshgdsgil.Label(
            label_data["name"], label_data["description"], label_data["color"]
        )
        temp_dir = self.get_scratch_space()
        with tempfile.NamedTemporaryFile(
            dir=temp_dir, mode="w", encoding="utf-8", delete=False
        ) as tmp_file:
            tmp_file_name = tmp_file.name
        try:
            # Save the label.
            dshgdsgil.Label.save_labels([input_label], tmp_file_name)
            # Load the label.
            output_labels = dshgdsgil.Label.load_labels(tmp_file_name)
            self.assertEqual(len(output_labels), 1)
            output_label = output_labels[0]
            # Check.
            self.assertEqual(output_label.name, input_label.name)
            self.assertEqual(output_label.description, input_label.description)
            self.assertEqual(output_label.color, input_label.color)
        finally:
            os.remove(tmp_file_name)
