import logging
import os
from typing import List

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dsddut
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_dockerized_prettier1
# #############################################################################


class Test_dockerized_prettier1(hunitest.TestCase):
    """
    Test running the `prettier` command inside a Docker container.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test running the `prettier` command in a Docker container.

        This test creates a test file, runs the command inside a Docker
        container with specified command options, and checks if the
        output matches the expected result.
        """
        cmd_opts: List[str] = []
        cmd_opts.append("--parser markdown")
        cmd_opts.append("--prose-wrap always")
        tab_width = 2
        cmd_opts.append(f"--tab-width {tab_width}")
        # Run `prettier` in a Docker container.
        in_file_path = dsddut.create_test_file(self, txt, extension="txt")
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        dshdlipr.run_dockerized_prettier(
            in_file_path,
            cmd_opts,
            out_file_path,
            file_type="md",
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check.
        actual = hio.from_file(out_file_path)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        txt = """
        - A
          - B
              - C
                """
        expected = """
        - A
          - B
            - C
        """
        self.helper(txt, expected)

    def test2(self) -> None:
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        expected = r"""
        - Good time management

        1. choose the right tasks
           - avoid non-essential tasks
        """
        self.helper(txt, expected)
