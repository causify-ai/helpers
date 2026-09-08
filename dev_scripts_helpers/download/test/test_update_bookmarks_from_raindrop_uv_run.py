#!/usr/bin/env python

import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest


class Test_update_bookmarks_from_raindrop_py_uv_run(hunitest.TestCase):
    """
    End-to-end test for the `update_bookmarks_from_raindrop.py` script via `uv run`.
    """

    def test1(self) -> None:
        """
        Test that the script runs successfully with `--help` via `uv run`.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("update_bookmarks_from_raindrop.py")
        cmd = f"uv run {exec_path} --help"
        # Run test.
        rc, output = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
