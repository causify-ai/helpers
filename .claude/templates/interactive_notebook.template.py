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

# Tutorial-specific imports.
import interactive_notebook_utils_template as utils

# Initialize notebook configuration and logging.
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
# # Cell 1: Interactive Distribution Explorer
#
# **Goal**:
# - Visualize how distribution shape parameters affect the Beta distribution
# - Understand the relationship between parameters and key statistical properties
# - Observe the probability density, cumulative distribution, and statistics simultaneously
#
# **Plots**:
# - **Selected View** (first panel): Choose between three complementary views via dropdown
#   - _Probability Density Function (PDF)_: Shows probability mass distribution across [0,1]
#   - _Cumulative Distribution Function (CDF)_: Shows probability of values ≤ x
#   - _Distribution Statistics_: Displays mean, variance, and mode
# - **PDF Reference** (second panel): Continuous reference showing the probability density
# - **CDF Reference** (third panel): Reference showing cumulative probabilities
# - **Comments** (fourth panel): Text summary with current parameter values and observations
#
# **Parameters**:
# - `α (alpha)`: Shape parameter controlling concentration toward 1
#   - Range: 0.5 to 10 with 0.5 increments
# - `β (beta)`: Shape parameter controlling concentration toward 0
#   - Range: 0.5 to 10 with 0.5 increments
# - `Plot Type`: Dropdown to select view in the first panel
#   - Options: PDF, CDF, Statistics
#
# **Key Observations**:
# - **Symmetry**: Distribution is symmetric when $\alpha = \beta$ (mean = 0.5)
# - **Concentration**: Increasing both $\alpha$ and $\beta$ concentrates the distribution
# - **Skewness**: Asymmetry appears when $\alpha \neq \beta$ (affects location of mean)
# - **Mode and Mean**: These differ when $\alpha$ and $\beta$ are very different

# %%
# Create interactive widget to explore the Beta distribution.
utils.cell1_interactive_distribution_explorer()

# %% [markdown]
# # Cell 2: Interactive Sample Generator
#
# **Goal**:
# - Understand sampling from the Beta distribution
# - Compare empirical samples to theoretical predictions
# - See the Law of Large Numbers in action
# - Observe convergence to the true mean
#
# **Plots**:
# - **Histogram with PDF Overlay** (left): Sampled values compared to theoretical distribution
# - **Summary Statistics** (right): Sample vs. theoretical statistics comparison
#
# **Parameters**:
# - `α (alpha)`: Shape parameter for the Beta distribution
#   - Range: 0.5 to 10 with 0.5 increments
# - `β (beta)`: Shape parameter for the Beta distribution
#   - Range: 0.5 to 10 with 0.5 increments
# - `N (total samples)`: Number of samples to draw
#   - Smaller $N$: More variability between sample and theoretical mean
#   - Larger $N$: Sample mean converges to theoretical mean (Law of Large Numbers)
# - `seed`: Random seed for reproducibility
#
# **Key Observations**:
# - As $N$ increases, the histogram approaches the theoretical PDF
# - The sample mean converges to the theoretical mean $\mu = \frac{\alpha}{\alpha + \beta}$
# - The difference between sample and theoretical mean decreases with more samples
# - Try different seeds to see how sampling variability changes

# %%
# Create interactive widget to generate and visualize samples.
utils.cell2_interactive_sample_generator()
