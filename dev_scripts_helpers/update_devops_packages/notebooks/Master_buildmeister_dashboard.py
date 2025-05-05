# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# CONTENTS:
# - [Description](#description)
# - [Imports](#imports)
# - [Utils](#utils)
# - [GH workflows state](#gh-workflows-state)
# - [Allure reports](#allure-reports)
# - [Number of open pull requests](#number-of-open-pull-requests)
# - [Code coverage HTML-page](#code-coverage-html-page)
# - [Code Coverage Page - CodeCov](#code-coverage-page---codecov)

#  TODO(Grisha): does it belong to the `devops` dir?

# <a name='description'></a>
# # Description

# The notebook reports the latest build status for multiple repos.

# <a name='imports'></a>
# # Imports

# %load_ext autoreload
# %autoreload 2
# %matplotlib inline

# +
import logging
from typing import Dict

import pandas as pd
from IPython.display import Markdown, display

import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hpandas as hpandas
import helpers.hprint as hprint
import helpers.lib_tasks_gh as hlitagh

# -

hdbg.init_logger(verbosity=logging.INFO)
_LOG = logging.getLogger(__name__)
_LOG.info("%s", henv.get_system_signature()[0])
hprint.config_notebook()

# Set the display options to print the full table.
pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)

# <a name='utils'></a>
# # Utils


# +
def make_clickable(url: str) -> str:
    """
    Wrapper to make the URL value clickable.

    :param url: URL value to convert
    :return: clickable URL link
    """
    return f'<a href="{url}" target="_blank">{url}</a>'


def color_format(val: str, status_color_mapping: Dict[str, str]) -> str:
    """
    Return the color depends on status.

    :param val: value of the status e.g. `failure`
    :param status_color_mapping: mapping statuses to the colors e.g.:
    ```
    {
       "success": "green",
       "failure": "red",
    }
    ```
    """
    if val in status_color_mapping:
        color = status_color_mapping[val]
    else:
        color = "grey"
    return f"background-color: {color}"


# -

# <a name='gh-workflows-state'></a>
# # GH workflows state

repo_list = [
    "cryptokaizen/cmamp",
    "cryptokaizen/orange",
    "cryptokaizen/lemonade",
    "causify-ai/kaizenflow",
]
workflow_df = hlitagh.gh_get_details_for_all_workflows(repo_list)
# Reorder columns.
columns_order = ["repo_name", "workflow_name", "conclusion", "url"]
workflow_df = workflow_df[columns_order]
# Make URL values clickable.
workflow_df["url"] = workflow_df["url"].apply(make_clickable)
_LOG.info(hpandas.df_to_str(workflow_df, log_level=logging.INFO))

status_color_mapping = {
    "success": "green",
    "failure": "red",
}
repos = workflow_df["repo_name"].unique()
display(Markdown("## Overall Status"))
current_timestamp = pd.Timestamp.now(tz="America/New_York")
display(Markdown(f"**Last run: {current_timestamp}**"))
for repo in repos:
    # Calculate the overall status.
    repo_df = workflow_df[workflow_df["repo_name"] == repo]
    overall_status = hlitagh.gh_get_overall_build_status_for_repo(repo_df)
    display(Markdown(f"## {repo}: {overall_status}"))
    repo_df = repo_df.drop(columns=["repo_name"])
    display(
        repo_df.style.map(
            color_format,
            status_color_mapping=status_color_mapping,
            subset=["conclusion"],
        )
    )

# <a name='allure-reports'></a>
# # Allure reports

# - fast tests: http://172.30.2.44/allure_reports/cmamp/fast/latest/index.html
# - slow tests: http://172.30.2.44/allure_reports/cmamp/slow/latest/index.html
# - superslow tests: http://172.30.2.44/allure_reports/cmamp/superslow/latest/index.html

# <a name='number-of-open-pull-requests'></a>
# # Number of open pull requests

for repo in repo_list:
    number_prs = len(hlitagh.gh_get_open_prs(repo))
    _LOG.info("%s: %s", repo, number_prs)

# <a name='code-coverage-html-page'></a>
# # Code coverage HTML-page

# http://172.30.2.44/html_coverage/runner_master/

# <a name='code-coverage-page---codecov'></a>
# # Code Coverage Page - CodeCov

# - Helpers: https://app.codecov.io/gh/causify-ai/helpers
