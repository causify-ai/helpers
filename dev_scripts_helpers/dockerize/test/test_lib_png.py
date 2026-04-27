import logging
import os
from typing import Tuple

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_png as dshdlipn

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_build_png_container1
# #############################################################################


class Test_build_png_container1(hunitest.TestCase):
    """
    Test building the `png` container for tikz to bitmap conversion.
    """

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Test that the PNG Docker container is built correctly.
        """
        tikz_code = r"""
        \documentclass[tikz, border=10pt]{standalone}
        \usepackage{tikz}
        \begin{document}
        \begin{tikzpicture}
            \draw[thick, fill=blue!20] (0,0) circle (1.5cm);
            \node at (0,0) {$A$};
        \end{tikzpicture}
        \end{document}
        """
        dshddout.test_container_build(
            self,
            tikz_code,
            "tex",
            "png",
            dshdlipn.run_dockerized_tikz_to_bitmap,
            positional_args=[["-density 300"]],
        )


# #############################################################################
# Test_dockerized_tikz_to_bitmap1
# #############################################################################


class Test_dockerized_tikz_to_bitmap1(hunitest.TestCase):
    def create_input_file(self) -> Tuple[str, str]:
        txt = r"""
        \documentclass[tikz, border=10pt]{standalone}
        \usepackage{tikz}

        \begin{document}

        \begin{tikzpicture}[scale=0.8]
            % Define the sets as circles with transparency
            \draw[thick, fill=blue!20, opacity=0.6] (0,0) circle (1.5cm);
            \node at (0,0) {$A$};

            \draw[thick, fill=red!20, opacity=0.6] (4,0) circle (1.5cm);
            \node at (4,0) {$B$};

            \draw[thick, fill=green!20, opacity=0.6] (2,3.5) circle (1.5cm);
            \node at (2,3.5) {$C$};
            % Add a title
            \node[font=\bfseries] at (2,-2.5) {Pairwise Exclusive Sets};
            \node[align=center] at (2,-3.3) {No overlap between any pair of sets};
        \end{tikzpicture}

        \end{document}
        """
        in_file_path = dshddout.create_test_file(self, txt, extension="tex")
        out_file_path = os.path.join(self.get_scratch_space(), "output.png")
        return in_file_path, out_file_path

    @pytest.mark.superslow
    def test_dockerized1(self) -> None:
        """
        Run `tikz_to_bitmap` inside a Docker container.
        """
        # Prepare inputs.
        in_file_path, out_file_path = self.create_input_file()
        cmd_opts = ["-density 300", "-quality 10"]
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run function.
        dshdlipn.run_dockerized_tikz_to_bitmap(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        dshddout.assert_output_file_exists(self, out_file_path)
