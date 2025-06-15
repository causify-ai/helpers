import logging
import os

import helpers.hunit_test as hunitest
import helpers.hprint as hprint
import dev_scripts_helpers.notebooks.dockerized_extract_notebook_images as dshndb

_LOG = logging.getLogger(__name__)

# #############################################################################
# TestNotebookImageExtractor1
# #############################################################################


class TestNotebookImageExtractor1(hunitest.TestCase):
    def test1(self) -> None:
        # Prepare the input.
        input_dir = self.get_input_dir(
            test_class_name="Test_run_dockerized_notebook_image_extractor1",
            test_method_name="test_run_dockerized_notebook_image_extractor")
        _LOG.info(hprint.to_str("input_dir"))
        src_test_notebook = os.path.join(input_dir, "test_notebook_image_extractor.ipynb")
        # Run the function.
        act = dshndb._NotebookImageExtractor._extract_regions_from_notebook(
            src_test_notebook
        )
        # Check the output.
        print(act)
