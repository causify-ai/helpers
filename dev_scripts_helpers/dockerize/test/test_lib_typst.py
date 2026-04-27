import logging
import os
from typing import List, Tuple

import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_cli_utils as dsddhclut
import dev_scripts_helpers.dockerize.lib_typst as dshdlity

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_dockerized_typst1
# #############################################################################


class Test_dockerized_typst1(hunitest.TestCase):
    def create_input_file(self) -> Tuple[str, str]:
        txt = r"""
        #set page(width: 10cm, height: auto)
        #set heading(numbering: "1.")

        = Hello, Typst!

        This is a simple Typst document.

        == Section

        Some content here.
        """
        in_file_path = dsddhclut.create_test_file(self, txt, extension="typ")
        out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
        return in_file_path, out_file_path

    def test_dockerized1(self) -> None:
        """
        Run `typst` inside a Docker container.
        """
        # Prepare inputs.
        in_file_path, out_file_path = self.create_input_file()
        cmd_opts: List[str] = []
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run function.
        dshdlity.run_dockerized_typst(
            in_file_path,
            out_file_path,
            cmd_opts,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        dsddhclut.assert_output_file_exists(self, out_file_path)

    def test_command_line1(self) -> None:
        """
        Run `dockerized_typst` through the command line.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("dockerized_typst.py")
        in_file_path, out_file_path = self.create_input_file()
        # Run function.
        cmd = f"{exec_path} --input {in_file_path} --output {out_file_path}"
        hsystem.system(cmd)
        # Check output.
        dsddhclut.assert_output_file_exists(self, out_file_path)
