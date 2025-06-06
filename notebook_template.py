# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# CONTENTS:
# - [Description](#description)

# %% [markdown]
# <a name='description'></a>
# # Description
#
# This notebook examines ...

# %%
# #!sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet jupyterlab-vim)"
# #!jupyter labextension enable

# %%
# %load_ext autoreload
# %autoreload 2

import logging

import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hprint as hprint

# %%
print(henv.get_system_signature()[0])

hprint.config_notebook()

# %%
# hdbg.init_logger(verbosity=logging.DEBUG)
hdbg.init_logger(verbosity=logging.INFO)
# hdbg.test_logger()
_LOG = logging.getLogger(__name__)
