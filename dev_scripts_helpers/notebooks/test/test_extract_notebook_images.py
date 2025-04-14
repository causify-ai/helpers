import logging
import os

import pytest
import helpers.hunit_test as hunitest
import helpers.hserver as hserver
import dev_scripts_helpers.notebooks.extract_notebook_images as dshnbe
import dev_scripts_helpers.notebooks.dockerized_extract_notebook_images as dshndb

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestNotebookImageExtractor1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
@pytest.mark.superslow("~42 sec.")
class Test_run_dockerized_notebook_image_extractor1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test the `run_dockerized_notebook_image_extractor` function.

        Get the test notebook ('test_images.ipynb') from the input directory,
        run the Docker container to extract images, and verify that the expected
        output files are produced.
        """
        input_dir = self.get_input_dir()
        src_test_notebook = os.path.join(input_dir, "test_images.ipynb")
        output_dir = self.get_output_dir()
        # Run the container.
        dshnbe._run_dockerized_extract_notebook_images(
            notebook_path=src_test_notebook,
            output_dir=output_dir,
            force_rebuild=False,
            use_sudo=False,
        )
        for item in output_dir.iterdir():
            _LOG.info("Output file: %s", item)
        # Check output.
        expected_files = [
            "test1.png",
            "test2.png",
            "test3.png",
            "test4.png",
            "test5.png",
            "test6.png",
        ]
        for filename in expected_files:
            expected_file = output_dir / filename
            self.assertTrue(
                os.path.exists(expected_file),
                f"Expected file '{expected_file}' not found!",
            )
