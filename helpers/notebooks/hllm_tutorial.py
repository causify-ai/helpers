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

# %%
# !sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet openai requests)"

# %%
import helpers.hllm as hllm
import helpers.hpandas as hpandas

# %%
val = hllm.get_model_stats()

# %%
import pprint

pprint.pprint(val[0])

# %%
import pandas as pd

# %%
# Normalize the nested JSON
df = pd.json_normalize(val, sep="_")
df
# View the resulting DataFrame
# print(df.T)  # Transpose just for readable vertical inspection

# %%
df.iloc[0].T

# %%
col_names = ["id", "context_length", "pricing_prompt", "pricing_completion"]

# %%
df.dtypes

# %% [markdown]
# #

# %%
for col in df.columns:
    print(hpandas.infer_column_types(df[col]))

# %%
df.apply(lambda x: pd.Series(hpandas.infer_column_types(x))).T

# %%
hpandas.infer_column_types_df(df)


# %%
pd.to_numeric(df["pricing_request"], errors="coerce").notna()

# %%
df["pricing_completion"]

# %%
df.sort_values("pricing_prompt")[col_names]

# %%
df[["pricing_prompt", "pricing_completion"]].plot.scatter(
    x="pricing_prompt", y="pricing_completion"
)

# %%
df["price_ratio"] = df["pricing_completion"] / df["pricing_prompt"]

# %%

# %%
# df["total_price"] =
