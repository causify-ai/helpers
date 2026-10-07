#!/usr/bin/env python

import logging

import pytest

import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_download_with_chrome_py_uv_run
# #############################################################################


class Test_download_with_chrome_py_uv_run(hunitest.TestCase):
    """
    Test the `download_with_chrome.py` executable through `uv run`.

    The script declares its dependencies inline, so `uv` installs them on the
    fly instead of requiring them in the test environment.
    """

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Test that `--help` runs and succeeds.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("download_with_chrome.py")
        cmd = f"uv run {exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
