import logging
import os
import pathlib

import helpers.hdocker as hdocker
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestNotebookImageExtractor
# #############################################################################


class TestNotebookImageExtractor(hunitest.TestCase):

    def test_run_dockerized_notebook_image_extractor(self) -> None:
        """
        Test the `run_dockerized_notebook_image_extractor` function.

        Obtain the test notebook ('test_images.ipynb') from the input
        directory, run the Docker container to extract images, and
        verify that the expected output files are produced.
        """
        output_dir = pathlib.Path(self.get_output_dir())
        input_dir = self.get_input_dir()
        src_test_notebook = os.path.join(input_dir, "test_images.ipynb")
        # Run the container.
        hdocker.run_dockerized_notebook_image_extractor(
            notebook_path=src_test_notebook,
            output_dir=str(output_dir),
            force_rebuild=True,
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
