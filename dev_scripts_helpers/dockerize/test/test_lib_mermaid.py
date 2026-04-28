import os

import pytest

import helpers.hdocker as hdocker
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_mermaid as dshdlime


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
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlime.run_dockerized_mermaid(
            in_file_path,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, out_file_path)

    @pytest.mark.slow
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

    @pytest.mark.slow
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
