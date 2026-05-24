# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Description
#
# This notebook examines ...

# %% [markdown]
# ## Imports

# %%
# %load_ext autoreload
# %autoreload 2

# System libraries.
import logging

# Third-party libraries.
# import numpy as np
# import pandas as pd
# import seaborn as sns
# import matplotlib.pyplot as plt

# %%
# # To install additional packages, use:
# import helpers.hmodule as hmodule
# hmodule.install_module_if_not_present(
#     ["pycaret"],
#     use_activate=True,
#     use_sudo=False,
#     venv_path="/opt/venv",
# )

# %%
# Helpers imports.
import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# Initialize notebook configuration and logging.
if True:
    import helpers.hnotebook as hnotebook

    hnotebook.config_notebook()
    hdbg.init_logger(verbosity=logging.INFO, use_exec_path=False)
    hnotebook.set_logger_to_print(_LOG)
else:
    import tutorial_utils as utils

    # Configure the logger for this tutorial.
    _LOG = logging.getLogger(__name__)
    utils.init_logger(_LOG)

_LOG.info("Test _LOG.info")
_LOG.debug("Test _LOG.debug")

# Convert `display` into `print()`.
try:
    from IPython.display import display
except ImportError:
    display = print  # type: ignore
