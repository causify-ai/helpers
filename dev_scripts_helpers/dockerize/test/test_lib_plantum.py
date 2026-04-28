import os

import pytest

import helpers.hdocker as hdocker
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_plantum as dshdlipl


# #############################################################################
# Test_build_plantum_container1
# #############################################################################


@pytest.mark.slow
class Test_build_plantum_container1(hunitest.TestCase):
    """
    Test building the `plantum` container.
    """

    def test1(self) -> None:
        """
        Test that the PlantUML Docker container is built correctly.
        """
        # Prepare inputs.
        plantum_code = r"""
        @startuml
        Alice -> Bob: Hello
        Bob -> Alice: Hi back
        @enduml
        """
        plantum_code = plantum_code.strip()
        # Run test.
        dshddout.test_container_build(
            self,
            plantum_code,
            "puml",
            "svg",
            dshdlipl.run_dockerized_plantuml,
            positional_args=[["svg"]],
        )

    def test2(self) -> None:
        """
        Test that the PlantUML version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        image_name = dshdlipl.get_plantuml_container_image_name()
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'plantuml -version 2>&1 | head -1'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Freeze version output.
        self.check_string(output)


# #############################################################################
# Test_run_dockerized_plantuml1
# #############################################################################


class Test_run_dockerized_plantuml1(hunitest.TestCase):
    """
    Test running PlantUML diagrams in a Docker container.
    """

    def helper(self, txt: str, dst_ext: str, output_name: str) -> None:
        """
        Test running PlantUML diagram in a Docker container.

        :param txt: PlantUML diagram code
        :param dst_ext: Output file extension (e.g., "svg", "png")
        :param output_name: Output file name (e.g., "output.svg")
        """
        # Prepare inputs.
        in_file_path = dshddout.create_test_file(self, txt, extension="puml")
        out_file_path = os.path.join(self.get_scratch_space(), output_name)
        cmd_opts = [dst_ext]
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlipl.run_dockerized_plantuml(
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
        Run `plantuml` sequence diagram to SVG inside a Docker container.
        """
        # Prepare inputs.
        txt = """
        @startuml
        Alice -> Bob: Hello
        Bob -> Alice: Hi back
        @enduml
        """
        dst_ext = "svg"
        output_name = "output.svg"
        # Run test.
        self.helper(txt, dst_ext, output_name)

    def test2(self) -> None:
        """
        Run `plantuml` class diagram to PNG inside a Docker container.
        """
        # Prepare inputs.
        txt = """
        @startuml
        class User {
            name: String
            email: String
        }
        class Post {
            title: String
            content: String
        }
        User "1" --> "*" Post
        @enduml
        """
        dst_ext = "png"
        output_name = "output.png"
        # Run test.
        self.helper(txt, dst_ext, output_name)
