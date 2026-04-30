import os

import pytest

import helpers.hdocker as hdocker
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_mermaid as dshdlime


# #############################################################################
# Test_build_mermaid_container1
# #############################################################################


#@pytest.mark.slow
class Test_build_mermaid_container1(hunitest.TestCase):
    """
    Test building the `mermaid` container.
    """

    def test1(self) -> None:
        """
        Test that the Mermaid Docker container is built correctly.
        """
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        dshdlime.build_mermaid_container_image(
            force_rebuild=force_rebuild, use_sudo=use_sudo
        )

    def test2(self) -> None:
        """
        Test that the Mermaid version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        image_name = dshdlime.get_mermaid_container_image_name()
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'mmdc --version'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Check version output.
        expected = "11.12.0\n"
        self.assert_equal(output, expected)


# #############################################################################
# Test_run_dockerized_mermaid1
# #############################################################################


class Test_run_dockerized_mermaid1(hunitest.TestCase):
    """
    Test running mermaid diagrams in a Docker container.
    """

    def helper(self, txt: str) -> None:
        """
        Test running mermaid diagram in a Docker container.

        :param txt: Mermaid diagram code
        """
        # Prepare inputs.
        in_file_path = dshddout.create_test_file(self, txt, extension="mmd")
        out_file_path = os.path.join(self.get_scratch_space(), "output.svg")
        cmd_opts = []
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlime.run_dockerized_mermaid(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, out_file_path)

    def test1(self) -> None:
        """
        Run `mermaid` flowchart with simple sequence inside a Docker container.
        """
        # Prepare inputs.
        txt = """
        graph TD
            A[Start] --> B[Process]
            B --> C[End]
        """
        # Run test.
        self.helper(txt)

    def test2(self) -> None:
        """
        Run `mermaid` flowchart with decision branches inside a Docker container.
        """
        # Prepare inputs.
        txt = """
        graph LR
            A[Input] --> B{Decision}
            B -->|Yes| C[Action 1]
            B -->|No| D[Action 2]
            C --> E[Output]
            D --> E
        """
        # Run test.
        self.helper(txt)
