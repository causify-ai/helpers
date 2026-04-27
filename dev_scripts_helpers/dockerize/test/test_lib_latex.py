import logging
import os
from typing import List, Tuple

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_latex as dshdlila

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_build_latex_container
# #############################################################################


class Test_build_latex_container1(hunitest.TestCase):
    """
    Test building the `latex` container.
    """

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Test that the LaTeX Docker container is built correctly.
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "test.tex")
        #
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        output_file = os.path.join(output_dir, "test.pdf")
        latex_code = r"""
        \documentclass{article}
        \begin{document}
        Hello, World!
        \end{document}
        """
        hio.to_file(input_file, latex_code)
        # Run test.
        dshdlila.run_basic_latex(
            input_file,
            [],
            True,
            output_file,
            force_rebuild=True,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, output_file)


# #############################################################################
# Test_dockerized_latex1
# #############################################################################


class Test_dockerized_latex1(hunitest.TestCase):
    def create_input_file(self) -> Tuple[str, str]:
        txt = r"""
        \documentclass{article}

        \begin{document}

        Hello, World!

        \end{document}
        """
        in_file_path = dshddout.create_test_file(self, txt, extension="tex")
        out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
        return in_file_path, out_file_path

    @pytest.mark.superslow
    def test_dockerized1(self) -> None:
        """
        Run `latex` inside a Docker container.
        """
        # Prepare inputs.
        in_file_path, out_file_path = self.create_input_file()
        cmd_opts: List[str] = []
        run_latex_again = True
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run function.
        dshdlila.run_basic_latex(
            in_file_path,
            cmd_opts,
            run_latex_again,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        dshddout.assert_output_file_exists(self, out_file_path)

    # TODO(gp): This doesn't work since:
    # 1) `convert_latex_cmd_to_arguments()` is monkey patching with parsing the
    # arguments. Maybe we need to pass multiple arguments to the mocking since
    # it's called multiple times.
    # 2) we re-execute `hdbg.init_logger()` which messes up the global state.
    # def test3(self) -> None:
    #     """
    #     Test the code to run `latex` using the parser.
    #     """
    #     from unittest.mock import patch
    #     import argparse
    #     # Prepare inputs.
    #     in_file_path = self.create_input_file()
    #     out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
    #     # Run function.
    #     mock_args = argparse.Namespace(
    #             input=in_file_path,
    #             output=out_file_path,
    #             run_latex_again=False,
    #             dockerized_force_rebuild=False,
    #             dockerized_use_sudo=hdocker.get_use_sudo(),
    #             log_level=logging.INFO
    #     )
    #     with patch("argparse.ArgumentParser.parse_known_args", return_value=(mock_args, [])):
    #         hdl._main(hdl._parse())
    #     # Check output.
    #     self.assertTrue(os.path.exists(out_file_path), msg=f"Output file {out_file_path} not found")
