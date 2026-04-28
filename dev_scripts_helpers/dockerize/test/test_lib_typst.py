import os
from typing import List

import pytest

import helpers.hdocker as hdocker
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_typst as dshdlity


# #############################################################################
# Test_build_typst_container1
# #############################################################################


class Test_build_typst_container1(hunitest.TestCase):
    """
    Test building the `typst` container.
    """

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Test that the Typst Docker container is built correctly and `typst
        --version` runs inside it.

        Set `DOCKER_FORCE_REBUILD=1` to rebuild from scratch, e.g.:
        ```bash
        > DOCKER_FORCE_REBUILD=1 pytest test_dockerized_typst.py::Test_run_dockerized_typst::test4
        ```
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        force_rebuild = True
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Run test.
        image_name = hdocker.build_container_image(
            dshdlity.TYPST_CONTAINER_IMAGE,
            dshdlity.TYPST_DOCKERFILE,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        exists, image_id = hdocker.image_exists(image_name, use_sudo)
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'typst --version'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertTrue(
            exists,
            msg=f"Typst Docker image '{image_name}' was not found after build",
        )
        self.assertNotEqual(image_id, "", msg="Expected a non-empty image ID")
        self.assertIn(
            "typst",
            output.lower(),
            msg=f"Expected 'typst' in version output, got: {output}",
        )


# #############################################################################
# Test_run_dockerized_typst1
# #############################################################################


class Test_run_dockerized_typst1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Run `typst` inside a Docker container.
        """
        # Prepare inputs.
        txt = r"""
        #set page(width: 10cm, height: auto)
        #set heading(numbering: "1.")

        = Hello, Typst!

        This is a simple Typst document.

        == Section

        Some content here.
        """
        in_file_path = dshddout.create_test_file(self, txt, extension="typ")
        out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
        cmd_opts: List[str] = []
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlity.run_dockerized_typst(
            in_file_path,
            out_file_path,
            cmd_opts,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, out_file_path)
