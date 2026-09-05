"""
Import as:

import dev_scripts_helpers.coding_tools.vim_highlighting.test.test_txt_syntax as dshctvhtts
"""

import logging
import os
import shlex
import subprocess

import pytest

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)  # noqa: F841


def _run_vim_export_syntax(
    test_file_path: str, vimrc_path: str, scratch_dir: str
) -> str:
    """
    Run Vim on `test_file_path` and extract syntax highlighting info.

    :param test_file_path: file to open in Vim and inspect. This is a
        golden input fixture tracked in git, so Vim is never pointed at it
        directly: we run against a scratch copy instead. This protects the
        fixture in case something external (e.g., a stray interactive Vim
        session, a plugin, shell state) mutates whatever file Vim has open,
        which has been observed to happen in practice.
    :param vimrc_path: minimal vimrc defining `:ExportSyntax`
    :param scratch_dir: dir where Vim writes `test_syntax_output.txt`
    :return: syntax highlighting output from Vim
    """
    hdbg.dassert_file_exists(test_file_path)
    hdbg.dassert_file_exists(vimrc_path)
    # Copy the fixture into the scratch dir and run Vim on the copy only,
    # so the tracked fixture can never be mutated by this test.
    scratch_file_path = os.path.join(
        scratch_dir, os.path.basename(test_file_path)
    )
    hio.to_file(scratch_file_path, hio.from_file(test_file_path))
    output_file = os.path.join(scratch_dir, "test_syntax_output.txt")
    # Run vim to export syntax information.
    scratch_dir_tmp = shlex.quote(scratch_dir)
    vimrc_path_tmp = shlex.quote(vimrc_path)
    test_file_path_tmp = shlex.quote(scratch_file_path)
    # - `--noplugin` and `-i NONE` isolate the run from the user's personal
    #   Vim plugins and shada/viminfo state (e.g., autosave plugins), so this
    #   test can't accidentally mutate the input fixture on disk.
    # - `< /dev/null` prevents Vim from reading stray bytes off the
    #   subprocess's inherited stdin as if they were keystrokes.
    cmd = (
        f"cd {scratch_dir_tmp} && vim -N -i NONE --noplugin "
        f"-u {vimrc_path_tmp} -c ExportSyntax -c qa! "
        f"{test_file_path_tmp} < /dev/null"
    )
    _LOG.info("cmd=%s", cmd)
    # Run vim with output suppressed.
    subprocess.run(cmd, shell=True, capture_output=True, check=False, timeout=10)
    # Read the generated output file.
    hdbg.dassert_file_exists(output_file)
    actual = hio.from_file(output_file)
    _LOG.info("actual=%s", actual)
    return actual


# #############################################################################
# TestTxtSyntaxHighlighting
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_host_gp_mac(), reason="Tests only run on GP's Mac"
)
class TestTxtSyntaxHighlighting(hunitest.TestCase):
    """
    Test Vim syntax highlighting for txt files.
    """

    def helper(self) -> str:
        """
        Run Vim and extract syntax highlighting info.

        :return: Syntax highlighting output from Vim
        """
        # Prepare inputs.
        input_dir = self.get_input_dir(use_only_test_class=True)
        test_file_path = os.path.join(input_dir, "test_syntax_examples.txt")
        vimrc_path = os.path.join(input_dir, "test_minimal.vimrc")
        scratch_dir = self.get_scratch_space()
        actual = _run_vim_export_syntax(test_file_path, vimrc_path, scratch_dir)
        return actual

    def test1(self) -> None:
        """
        Test that Vim successfully exports syntax highlighting information.
        """
        # Run test.
        actual = self.helper()
        # Check outputs.
        hdbg.dassert_lt(
            0, len(actual), "Syntax highlighting output should not be empty"
        )
        # Verify the output contains expected syntax group markers.
        self.assertIn("txtHeader1", actual)
        self.assertIn("txtHeader2", actual)

    def test2(self) -> None:
        """
        Test that syntax highlighting output matches expected golden file.
        """
        # Run test.
        actual = self.helper()
        # Check outputs using golden file testing.
        self.check_string(actual)


# #############################################################################
# TestSmdSyntaxHighlighting
# #############################################################################


@pytest.mark.skipif(
    not hserver.is_host_gp_mac(), reason="Tests only run on GP's Mac"
)
class TestSmdSyntaxHighlighting(hunitest.TestCase):
    """
    Test Vim syntax highlighting for `.smd` files.

    `.smd` files use the `smd` filetype, which is wired up (in the real
    `~/.vimrc`) to use the `txt_syntax` syntax, same as `.txt` and `.md`
    files. This test replicates that wiring in a minimal vimrc so it does
    not depend on the user's personal dotfiles.
    """

    def helper(self) -> str:
        """
        Run Vim and extract syntax highlighting info.

        :return: Syntax highlighting output from Vim
        """
        # Prepare inputs.
        input_dir = self.get_input_dir(use_only_test_class=True)
        test_file_path = os.path.join(input_dir, "syntax_check.smd")
        vimrc_path = os.path.join(input_dir, "test_minimal.vimrc")
        scratch_dir = self.get_scratch_space()
        actual = _run_vim_export_syntax(test_file_path, vimrc_path, scratch_dir)
        return actual

    def test1(self) -> None:
        """
        Test that Vim successfully exports syntax highlighting information.
        """
        # Run test.
        actual = self.helper()
        # Check outputs.
        hdbg.dassert_lt(
            0, len(actual), "Syntax highlighting output should not be empty"
        )
        # Verify the output contains expected syntax group markers.
        self.assertIn("txtHeader1", actual)
        self.assertIn("txtHeader2", actual)
        self.assertIn("txtBold", actual)
        self.assertIn("txtItalic", actual)

    def test2(self) -> None:
        """
        Test that syntax highlighting output matches expected golden file.
        """
        # Run test.
        actual = self.helper()
        # Check outputs using golden file testing.
        self.check_string(actual)
