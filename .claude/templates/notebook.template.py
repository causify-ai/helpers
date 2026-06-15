# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
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
# Use this for most notebooks.
import helpers.hdbg as hdbg
import helpers.hnotebook as hnotebook

_LOG = logging.getLogger(__name__)

# Initialize notebook configuration and logging.
# hnotebook.config_notebook()
# hdbg.init_logger(verbosity=logging.INFO, use_exec_path=False)
# hnotebook.set_logger_to_print(_LOG)

import notebook_utils_template as utils
_LOG = logging.getLogger(__name__)
utils.init_loggers(_LOG)

_LOG.info("Test _LOG.info")
_LOG.debug("Test _LOG.debug")

# Convert `display` into `print()`.
try:
    from IPython.display import display
except ImportError:
    display = print  # type: ignore

# %% [markdown]
# # Part 1: Distribution Explorer

# %% [markdown]
# ## Cell 1.1: Interactive Distribution Explorer
#
# **Goal**:
# - Visualize how distribution shape parameters affect the Beta distribution
# - Understand the relationship between parameters and key statistical properties
# - Observe the probability density, cumulative distribution, and statistics simultaneously
#
# _PDF Reference_: Shows the probability density function of the distribution
# _CDF Reference_: Shows the cumulative distribution function
# _Comments_: Current parameter values (alpha, beta, mean)

# %%
# Create interactive widget to explore the Beta distribution.
utils.cell1_interactive_distribution_explorer()

# %% [markdown]
# ## Cell 1.2: Observations on Distribution Shape
#
# **Key observations**:
# - The distribution is symmetric when $\alpha = \beta$ (mean = 0.5)
# - Increasing both $\alpha$ and $\beta$ concentrates the distribution
# - Asymmetry appears when $\alpha \neq \beta$, affecting the location of the mean
# - PDF and CDF provide complementary views of the same distribution
# - Try changing the slider values to see how the shape evolves continuously

# %% [markdown]
# # Part 2: Sample Generator

# %% [markdown]
# ## Cell 2.1: Interactive Sample Generator
#
# **Goal**:
# - Understand sampling from the Beta distribution
# - Compare empirical samples to theoretical predictions
# - See the Law of Large Numbers in action
# - Observe convergence to the true mean
#
# _Histogram with PDF Overlay_: Sampled values compared to theoretical distribution
# _Summary Statistics_: Sample vs. theoretical statistics comparison
# _Comments_: Current parameter values and sample statistics

# %%
# Create interactive widget to generate and visualize samples.
utils.cell2_interactive_sample_generator()

# %% [markdown]
# ## Cell 2.2: Observations on Sampling Behavior
#
# **Key observations**:
# - As $N$ increases, the histogram approaches the theoretical PDF
# - The sample mean converges to the theoretical mean $\mu = \frac{\alpha}{\alpha + \beta}$
# - The difference between sample and theoretical mean decreases with more samples
# - Try different seeds at the same N to see sampling variability
# - Try different alpha/beta values to see how the distribution shape affects convergence
