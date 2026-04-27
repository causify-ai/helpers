import logging
import os
from typing import List

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_markdown_toc as dshdlmato

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_build_markdown_toc_container
# #############################################################################


class Test_build_markdown_toc_container1(hunitest.TestCase):
    """
    Test building the `markdown-toc` container.
    """

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Test that the markdown-toc Docker container is built correctly.
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        input_dir = self.get_input_dir()
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        input_file = os.path.join(input_dir, "test.md")
        markdown_code = """
        <!-- toc -->

        # Section 1
        ## Subsection 1.1
        # Section 2
        """
        hio.to_file(input_file, markdown_code)
        # Run test.
        dshdlmato.run_dockerized_markdown_toc(
            input_file,
            [],
            use_sudo=use_sudo,
            force_rebuild=True,
        )
        # Check outputs: file was modified in place.
        self.assertTrue(
            os.path.exists(input_file),
            msg=f"Input file {input_file} should still exist",
        )


# #############################################################################
# Test_dockerized_markdown_toc1
# #############################################################################


class Test_dockerized_markdown_toc1(hunitest.TestCase):
    def run_markdown_toc(self, txt: str, expected: str) -> None:
        """
        Test running the `markdown-toc` command in a Docker container.
        """
        cmd_opts: List[str] = []
        # Run `markdown-toc` in a Docker container.
        in_file_path = dshddout.create_test_file(self, txt, extension="md")
        use_sudo = hdocker.get_use_sudo()
        force_rebuild = False
        dshdlmato.run_dockerized_markdown_toc(
            in_file_path,
            cmd_opts,
            use_sudo=use_sudo,
            force_rebuild=force_rebuild,
        )
        # Check.
        actual = hio.from_file(in_file_path)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Test running the `markdown-toc` command inside a Docker container.
        """
        txt = """
        <!-- toc -->

        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        expected = r"""
        <!-- toc -->

        - [Good](#good)
          * [Bad](#bad)

        <!-- tocstop -->

        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        self.run_markdown_toc(txt, expected)
