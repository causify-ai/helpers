import logging
import os
from typing import Tuple

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_graphviz as dshdligr

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_build_graphviz_container1
# #############################################################################


class Test_build_graphviz_container1(hunitest.TestCase):
    """
    Test building the `graphviz` container.
    """

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Test that the Graphviz Docker container is built correctly.
        """
        graphviz_code = """
        digraph {
            a -> b[label="0.2"];
            a -> c[label="0.4"];
            c -> b[label="0.6"];
        }
        """
        dshddout.test_container_build(
            self,
            graphviz_code,
            "dot",
            "png",
            dshdligr.run_dockerized_graphviz,
            positional_args=[[]],
        )


# #############################################################################
# Test_dockerized_graphviz1
# #############################################################################


class Test_run_dockerized_graphviz1(hunitest.TestCase):
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
        in_file_path = dshddout.create_test_file(self, txt, extension="dot")
        out_file_path = os.path.join(self.get_scratch_space(), "output.png")
        return in_file_path, out_file_path

    def test1(self) -> None:
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
        dshddout.assert_output_file_exists(self, out_file_path)
