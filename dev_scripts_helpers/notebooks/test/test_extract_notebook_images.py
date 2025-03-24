import logging
import os
import pathlib
import re
import shutil
import typing

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestNotebookImageExtractor
# #############################################################################


class TestNotebookImageExtractor(hunitest.TestCase):
    """
    Test for the dockerized notebook image extractor module.
    """

    original_build_container_image = hdocker.build_container_image
    original_system = hsystem.system

    @pytest.fixture(autouse=True)
    def setup_teardown_test(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> typing.Generator[None, None, None]:
        """
        Set up and tear down the test environment for each test.

        Monkey-patch the build_container_image function and the system
        command to remove any problematic '--platform' flags, then clean
        up the injected test notebook file from the build context after
        the test runs.

        :param monkeypatch: pytest monkeypatch fixture
        :return: None
        """
        self.set_up_test(monkeypatch)
        yield
        self.tear_down_test(monkeypatch)
        # Remove the copied test notebook from the current working directory (build context).
        test_file = os.path.join(os.getcwd(), "test_images.ipynb")
        if os.path.exists(test_file):
            os.remove(test_file)

    def set_up_test(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Set up per-test monkey-patching of functions.

        Monkey-patches:
          - helpers.hdocker.build_container_image to use _patched_build_container_image.
          - hsystem.system to use _patched_system.

        :param monkeypatch: The pytest monkeypatch fixture
        :return: None
        """
        monkeypatch.setattr(
            "helpers.hdocker.build_container_image",
            self._patched_build_container_image,
        )
        monkeypatch.setattr(hsystem, "system", self._patched_system)

    def tear_down_test(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Restore any monkey-patched attributes.

        :param monkeypatch: The pytest monkeypatch fixture
        :return: None
        """
        monkeypatch.undo()

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
        hio.create_dir("output", incremental=True)
        output_dir = pathlib.Path("output")
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
            expected_file = os.path.join(str(output_dir), filename)
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
        build_context = "tmp.docker_build"
        if os.path.isdir(build_context):
            src_file = os.path.join(os.getcwd(), "test_images.ipynb")
            dst_file = os.path.join(build_context, "test_images.ipynb")
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

    @staticmethod
    def _patched_system(cmd: str, suppress_output: bool = False) -> typing.Any:
        """
        Remove any '--platform' flag from the docker build command.

        :param cmd: original system command
        :param suppress_output: if True, suppresses command output
        :return: result of executing the patched command
        """
        # Some hosts find `--platform ` problematic.
        patched_cmd = re.sub(r"\s*--platform(?:=|\s+)\S+", "", cmd)
        _LOG.info("Patched system command:\n%s", patched_cmd)
        return TestNotebookImageExtractor.original_system(
            patched_cmd, suppress_output=suppress_output
        )
