import logging
import os
from typing import Tuple

import helpers.hdocker as hdocker
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dsddut
import dev_scripts_helpers.dockerize.lib_graphviz as dshdligr

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_dockerized_graphviz1
# #############################################################################


class Test_dockerized_graphviz1(hunitest.TestCase):
    def create_input_file(self) -> Tuple[str, str]:
        txt = r"""
        digraph {
            a -> b[label="0.2",weight="0.2"];
            a -> c[label="0.4",weight="0.4"];
            c -> b[label="0.6",weight="0.6"];
            c -> e[label="0.6",weight="0.6"];
            e -> e[label="0.1",weight="0.1"];
            e -> b[label="0.7",weight="0.7"];
        }
        """
        in_file_path = dsddut.create_test_file(self, txt, extension="dot")
        out_file_path = os.path.join(self.get_scratch_space(), "output.png")
        return in_file_path, out_file_path

    def test_dockerized1(self) -> None:
        """
        Run `graphviz` inside a Docker container.
        """
        # Prepare inputs.
        in_file_path, out_file_path = self.create_input_file()
        cmd_opts = []
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run function.
        dshdligr.run_dockerized_graphviz(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        dsddut.assert_output_file_exists(self, out_file_path)
