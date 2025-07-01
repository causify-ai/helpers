# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# CONTENTS:
# - [Description](#description)
# - [Imports](#imports)
# - [GH workflows state](#gh-workflows-state)
# - [Allure reports](#allure-reports)
# - [Number of open pull requests](#number-of-open-pull-requests)
# - [Code coverage HTML-page](#code-coverage-html-page)
# - [Code Coverage Page - CodeCov](#code-coverage-page---codecov)

# %% [markdown]
#  TODO(Grisha): does it belong to the `devops` dir?

# %% [markdown]
# <a name='description'></a>
# # Description

# %% [markdown]
# The notebook reports the latest build status for multiple repos.

# %% [markdown]
# <a name='imports'></a>
# # Imports

# %%
# %load_ext autoreload
# %autoreload 2
# %matplotlib inline

# %%
import logging

import pandas as pd

import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hprint as hprint
import helpers.lib_tasks_gh as hlitagh

# %%
hdbg.init_logger(verbosity=logging.INFO)
_LOG = logging.getLogger(__name__)
_LOG.info("%s", henv.get_system_signature()[0])
hprint.config_notebook()

# %%
# Set the display options to print the full table.
pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)


# %% [markdown]
# <a name='gh-workflows-state'></a>
# # GH workflows state

# %%
repo_list = [
    "cryptokaizen/cmamp",
    "cryptokaizen/orange",
    "cryptokaizen/lemonade",
    "causify-ai/kaizenflow",
]
workflow_df = hlitagh.gh_get_details_for_all_workflows(repo_list)
workflow_df = workflow_df[["repo_name", "workflow_name", "conclusion", "url"]]

# %%
status_color_mapping = {
    "success": "green",
    "failure": "red",
}

hlitagh.render_repo_workflow_status_table(workflow_df, status_color_mapping)

# %% [markdown]
# <a name='allure-reports'></a>
# # Allure reports

# %% [markdown]
# - fast tests: http://172.30.2.44/allure_reports/cmamp/fast/latest/index.html
# - slow tests: http://172.30.2.44/allure_reports/cmamp/slow/latest/index.html
# - superslow tests: http://172.30.2.44/allure_reports/cmamp/superslow/latest/index.html

# %% [markdown]
# <a name='number-of-open-pull-requests'></a>
# # Number of open pull requests

# %%
for repo in repo_list:
    number_prs = len(hlitagh.gh_get_open_prs(repo))
    _LOG.info("%s: %s", repo, number_prs)

# %% [markdown]
# <a name='code-coverage-html-page'></a>
# # Code coverage HTML-page

# %% [markdown]
# http://172.30.2.44/html_coverage/runner_master/

# %% [markdown]
# <a name='code-coverage-page---codecov'></a>
# # Code Coverage Page - CodeCov

# %% [markdown]
# - Helpers: https://app.codecov.io/gh/causify-ai/helpers
