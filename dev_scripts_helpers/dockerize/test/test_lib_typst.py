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


#@pytest.mark.slow
class Test_build_typst_container1(hunitest.TestCase):
    """
    Test building the `typst` container.
    """

    def test1(self) -> None:
        """
        Test that the Typst Docker container is built correctly.
        """
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        dshdlity.build_typst_container_image(
            force_rebuild=force_rebuild, use_sudo=use_sudo
        )

    def test2(self) -> None:
        """
        Test that the Typst version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        image_name = dshdlity.get_typst_container_image_name()
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'typst --version'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Check version output.
        expected = "typst 0.14.2 (b33de9de)\n"
        self.assert_equal(output, expected)


# #############################################################################
# Test_run_dockerized_typst1
# #############################################################################


#@pytest.mark.slow
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
