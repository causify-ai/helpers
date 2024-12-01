import os

import config_root.config as cconfig
import dev_scripts_helpers.notebooks.run_notebook_test_case as dshnrntca
import pytest

import helpers.hgit as hgit
import helpers.hserver as hserver


def build_config() -> cconfig.ConfigList:
    """
    Get an empty config for the test.
    """
    config = {}
    config = cconfig.Config()
    config_list = cconfig.ConfigList([config])
    return config_list


class Test_Master_buildmeister_dashboard_notebook(
    dshnrntca.Test_Run_Notebook_TestCase
):
    @pytest.mark.skipif(
        not hserver.is_inside_ci(),
        reason="No access to data from `lemonade` repo locally",
    )
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_supermodule(),
        reason="Run only in amp as super-module",
    )
    @pytest.mark.superslow("~42 sec.")
    def test1(self) -> None:
        amp_dir = hgit.get_amp_abs_path()
        notebook_path = os.path.join(
            amp_dir, "devops", "notebooks", "Master_buildmeister_dashboard.ipynb"
        )
        config_builder = "helpers.test.test_master_buildmeister_dashboard.build_config()"
        self._test_run_notebook(notebook_path, config_builder)
