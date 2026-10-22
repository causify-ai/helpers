import logging

import helpers.hunit_test as hunitest
from helpers import hgit, hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_call_graph_viewer_py_uv_run
# #############################################################################


class Test_call_graph_viewer_py_uv_run(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that `uv run` installs the declared dependencies and starts the
        script.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("call_graph_viewer.py")
        cmd = f"uv run {exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
