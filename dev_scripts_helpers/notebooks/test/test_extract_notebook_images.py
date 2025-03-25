import logging
import os
import pathlib
import shutil
import typing

import helpers.hdocker as hdocker
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestNotebookImageExtractor
# #############################################################################


class TestNotebookImageExtractor(hunitest.TestCase):

    original_build_container_image = hdocker.build_container_image

    def test_run_dockerized_notebook_image_extractor(self) -> None:
        """
        Test the `run_dockerized_notebook_image_extractor` function.

        Create a temporary output directory, copy the existing test
        notebook (test_images.ipynb) into the current working directory
        for the Docker build context, run the extraction function, and
        verify that the expected output files ('test.png', 'test2.png',
        'test3.png') are produced. The test file includes different test
        cases, so we can directly test the output generation.

        :return: None
        """
        output_dir = pathlib.Path(self.get_output_dir())
        dir_name = self.get_input_dir()
        src_test_notebook = os.path.join(dir_name, "test_images.ipynb")
        # Copy the test notebook into the current working directory (build context).
        dst_test_notebook = os.path.join(os.getcwd(), "test_images.ipynb")
        shutil.copy(src_test_notebook, dst_test_notebook)
        # Run the extraction function.
        hdocker.run_dockerized_notebook_image_extractor(
            notebook_path=src_test_notebook,
            output_dir=str(output_dir),
            force_rebuild=True,
            use_sudo=False,
        )
        for item in output_dir.iterdir():
            _LOG.info("Output file: %s", item)
        # Check output.
        expected_files = ["test.png", "test2.png", "test3.png"]
        for filename in expected_files:
            expected_file = output_dir / filename
            self.assertTrue(
                os.path.exists(expected_file),
                f"Expected file '{expected_file}' not found!",
            )

    @staticmethod
    def _patched_build_container_image(
        image_name: str, dockerfile: str, force_rebuild: bool, use_sudo: bool
    ) -> str:
        """
        Modify the Dockerfile to append test notebook.

        :param image_name: name of the Docker image to be built
        :param dockerfile: original Dockerfile content
        :param force_rebuild: if `True`, forces rebuilding the image
        :param use_sudo: if `True`, uses sudo for Docker commands
        :return: name of image
        """
        extra_layer = "\n# Injecting test file for extra layer\nCOPY test_images.ipynb /app/test_images.ipynb\n"
        modified_dockerfile = dockerfile + extra_layer
        _LOG.info("Modified Dockerfile for testing:\n%s", modified_dockerfile)
        # Copy the test file into the build context.
        build_context = pathlib.Path("tmp.docker_build")
        if build_context.is_dir():
            src_file = pathlib.Path(os.getcwd()) / "test_images.ipynb"
            dst_file = build_context / "test_images.ipynb"
            _LOG.info(
                "Copying test file from %s to build context %s",
                src_file,
                dst_file,
            )
            shutil.copy(src_file, dst_file)
        else:
            _LOG.info("Build context directory not found; skipping file copy.")
        return typing.cast(
            str,
            TestNotebookImageExtractor.original_build_container_image(
                image_name, modified_dockerfile, force_rebuild, use_sudo
            ),
        )
