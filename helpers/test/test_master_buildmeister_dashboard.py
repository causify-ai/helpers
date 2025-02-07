import os

import pytest

import config_root.config as cconfig
import dev_scripts_helpers.notebooks.run_notebook_test_case as dshnrntca
import helpers.hgit as hgit
import helpers.hserver as hserver
import helpers.lib_tasks_gh as hlitagh


def build_config() -> cconfig.ConfigList:
    """
    Get an empty config for the test.
    """
    config = {}
    config = cconfig.Config()
    config_list = cconfig.ConfigList([config])
    return config_list


# #############################################################################
# Test_Master_buildmeister_dashboard_notebook
# #############################################################################


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
        config_builder = (
            "helpers.test.test_master_buildmeister_dashboard.build_config()"
        )
        self._test_run_notebook(notebook_path, config_builder)

    @pytest.mark.skipif(
        not hserver.is_inside_ci(),
        reason="No access to data from `lemonade` repo locally",
    )
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_supermodule(),
        reason="Run only in amp as super-module",
    )
    @pytest.mark.superslow("~30 sec.")
    def test2(self) -> None:
        """
        Check that we can get status for all the workflows.
        """
        repo_list = [
            "causify-ai/cmamp",
            "causify-ai/orange",
            "causify-ai/lemonade",
            "causify-ai/kaizenflow",
            "causify-ai/helpers",
            "causify-ai/quant_dashboard",
        ]
        for repo_name in repo_list:
            hlitagh.gh_get_workflow_type_names(repo_name)
