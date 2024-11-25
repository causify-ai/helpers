"""
Import as:

import dev_scripts_helpers.notebooks.run_notebook_test_case as dsnrnteca
"""

import logging

import helpers.hjupyter as hjupyte
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class Test_Run_Notebook_TestCase(hunitest.TestCase):
    """
    Check that a notebook is not broken by running it end-to-end.
    """

    def _test_run_notebook(
        self, notebook_path: str, config_builder: str, *, extra_opts: str = ""
    ) -> None:
        """
        Test that a notebook runs end-to-end.

        :param notebook_path: path to a notebook file to run, use
            `hgit.get_amp_abs_path()` when testing a notebook that is in `amp`
        :param config_builder: a function to use as config builder that returns
            a list of configs
        :param extra_opts: options for "run_notebook.py", e.g., "--publish_notebook"
        """
        dst_dir = self.get_scratch_space()
        opts = f"--no_suppress_output --num_threads 'serial'{extra_opts} -v DEBUG 2>&1"
        cmd = hjupyte.build_run_notebook_cmd(
            config_builder, dst_dir, notebook_path, extra_opts=opts
        )
        _LOG.debug("cmd=%s", cmd)
        # Execute.
        rc = hsystem.system(
            cmd, abort_on_error=True, suppress_output=False, log_level="echo"
        )
        _LOG.debug("rc=%s", rc)
        # Make sure that the run finishes successfully.
        self.assertEqual(rc, 0)
