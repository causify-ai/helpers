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
# # <PACKAGE_NAME> API
#
# A guided exploration of the <PACKAGE_NAME> library:
# - **Core abstraction**: <describe main concept>
# - **Use case**: <what problem it solves>
# - **Learning path**: primitives → composition → patterns

# %% [markdown]
# ## Imports and Setup

# %%
# %load_ext autoreload
# %autoreload 2

import logging
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# %%
import helpers.hdbg as hdbg
import helpers.hnotebook as hnotebook

hdbg.init_logger(verbosity=logging.INFO)
_LOG = logging.getLogger(__name__)
hnotebook.config_notebook()

try:
    from IPython.display import display
except ImportError:
    display = print  # type: ignore

# %% [markdown]
# ## Library Overview
#
# - **What problem it solves**: <main problem>
# - **Key abstraction**: <core concept>
# - **Mental model**:
#
# | Object | Description | Comments |
# |--------|-------------|----------|
# | `Explainer(...)` | Main entry point | Wraps model + training data |
# | `.explain(x)` | Instance explanation | Returns Explanation object |
# | `Explanation.values` | Per-feature contributions | shape (n_samples, n_features) |
#
# - **Key classes**:
#   - `Explainer`: Main class for generating explanations
#   - `Explanation`: Result object holding values, baseline, and metadata

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
# **Key observations** (applies to both Beta and Normal distributions):
# - **Symmetric distributions**: When $\alpha = \beta$ (Beta) or when centered around the mean (Normal), the distribution is symmetric
# - **Concentration**: Increasing both parameters concentrates the distribution — larger $\alpha, \beta$ values for Beta, or smaller $\sigma$ for Normal
# - **Skew / Asymmetry**: For Beta, asymmetry appears when $\alpha \neq \beta$, shifting the density left or right
# - **Support**: Beta is bounded on $[0, 1]$ (ideal for proportions), while Normal is unbounded $(-\infty, \infty)$ (ideal for real-valued data)
# - **Parameter interpretation**: Beta parameters $\alpha, \beta$ control shape flexibly; Normal parameters $\mu, \sigma$ control location and scale
# - **Complementary views**: PDF and CDF provide complementary views of the same distribution regardless of type
# - **Interactive exploration**: Try changing the slider values to see how the shape evolves continuously

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

# %%
# Create interactive widget to generate and visualize samples.
utils.cell2_interactive_sample_generator()

# %% [markdown]
# **Key observations**:
# - As $N$ increases, the histogram approaches the theoretical PDF
# - The sample mean converges to the theoretical mean $\mu = \frac{\alpha}{\alpha + \beta}$
# - The difference between sample and theoretical mean decreases with more samples
# - Try different seeds at the same N to see sampling variability
# - Try different alpha/beta values to see how the distribution shape affects convergence
