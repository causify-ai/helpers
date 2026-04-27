import os

import pytest

import helpers.hdocker as hdocker
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_plantum as dshdlipl


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
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlipl.run_dockerized_plantuml(
            in_file_path,
            out_file_path,
            dst_ext,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, out_file_path)

    @pytest.mark.slow
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

    @pytest.mark.slow
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
