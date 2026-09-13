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

# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# %%
# Only needed for a package not preinstalled in the Docker image; drop this
# cell entirely otherwise.
# !pip install -q <PACKAGE_NAME>==<VERSION>

# import <PACKAGE_NAME>
# print("<PACKAGE_NAME> version: ", <PACKAGE_NAME>.__version__)

# %%
import helpers.hdbg as hdbg
import helpers.hintrospection as hintros
import helpers.hnotebook as hnotebook

# Replace `PACKAGE_NAME_utils` with this notebook's own paired utils module,
# e.g. `import sklearn_distributions_utils as utils`.
import PACKAGE_NAME_utils as utils

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
# - Understand the relationship between parameters and key statistical
#   properties
# - Observe the probability density, cumulative distribution, and statistics
#   simultaneously

# %% [markdown]
# **Implementation**: `cell1_interactive_distribution_explorer(figsize=None)`
# - Builds `alpha` and `beta` sliders via `build_widget_control()`, and a
#   `Distribution Type` dropdown for `Beta` vs `Normal`
# - Recomputes the PDF and CDF on every change, via `_beta_pdf()` /
#   `_beta_cdf()` or `_norm_pdf()` / `_norm_cdf()` depending on the dropdown
# - Draws 3 panels:
#   - The PDF, via `ax1.plot()`
#   - The CDF, via `ax2.plot()`
#   - A comments panel with the current parameters and the distribution's
#     mean

# %%
hintros.print_obj_info(utils.cell1_interactive_distribution_explorer)

# %% [markdown]
# **Usage**
# - Inputs
#   - **`alpha`**: shape parameter $\alpha$ for `Beta`, or the mean $\mu$
#     for `Normal`
#   - **`beta`**: shape parameter $\beta$ for `Beta`, or the variance
#     $\sigma^2$ for `Normal`
#   - **`Distribution Type`**: toggle between `Beta` (bounded on $[0, 1]$)
#     and `Normal` (unbounded)
#
# - Panels
#   - **`PDF Reference`**: Shows the probability density function of the
#     distribution
#   - **`CDF Reference`**: Shows the cumulative distribution function
#   - **`Comments`**: Current parameter values (alpha, beta, mean)

# %%
# Create interactive widget to explore the Beta distribution.
utils.cell1_interactive_distribution_explorer()

# %% [markdown]
# **Guided usage**
# - Leave `Distribution Type` on `Beta`, with `alpha=2` and `beta=5`
#   - Observe the PDF skew toward 0, since `beta > alpha`
# - Set `alpha` and `beta` to the same value, e.g. both 5
#   - Observe the PDF become symmetric around 0.5
# - Raise `alpha` and `beta` together, e.g. to 8 and 8
#   - Observe the PDF narrow and concentrate around the mean
# - Switch `Distribution Type` to `Normal`
#   - Observe `alpha` and `beta` now read as $\mu$ and $\sigma^2$, and the
#     x-axis stretch to $(-\infty, \infty)$ instead of staying inside
#     $[0, 1]$

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

# %% [markdown]
# **Implementation**: `cell2_interactive_sample_generator(figsize=None)`
# - Builds `alpha`/`beta` sliders, a logarithmic `N (total samples)` slider
#   via `build_log_widget_control()`, and a `seed` slider
# - Draws `n_samples` from `np.random.beta(alpha, beta, size=n_samples)`
#   with a fixed seed, for reproducibility
# - Draws 4 panels:
#   - The sample histogram against the theoretical PDF
#   - Sample statistics (mean, std, min, max, median) against theory
#   - The empirical CDF against the theoretical CDF
#   - A comments panel with the current parameters and sample size

# %%
hintros.print_obj_info(utils.cell2_interactive_sample_generator)

# %% [markdown]
# **Usage**
# - Inputs
#   - **`alpha`**: shape parameter $\alpha$ of the `Beta` distribution
#     sampled
#   - **`beta`**: shape parameter $\beta$ of the `Beta` distribution sampled
#   - **`N (total samples)`**: number of samples drawn, on a log scale
#   - **`seed`**: random seed, so the same draw can be reproduced
#
# - Panels
#   - **`Sample Distribution`**: histogram of the drawn samples, with the
#     theoretical PDF overlaid
#   - **`Sample Statistics`**: sample mean, std, min, max, and median, next
#     to the theoretical mean and their difference
#   - **`CDF Comparison`**: the empirical CDF against the theoretical CDF
#   - **`Comments`**: current parameters and sample size

# %%
# Create interactive widget to generate and visualize samples.
utils.cell2_interactive_sample_generator()

# %% [markdown]
# **Guided usage**
# - Leave `N (total samples)` at its smallest value
#   - Observe the histogram sit far from the theoretical PDF, and the
#     sample mean noticeably off the theoretical mean
# - Drag `N (total samples)` up toward its largest value
#   - Observe the histogram approach the theoretical PDF, and the
#     sample/theory mean difference in the Statistics panel shrink toward 0
# - Keep `N` fixed and change `seed`
#   - Observe the histogram and statistics shift slightly each time: the
#     same $N$ still leaves sampling variability
# - Change `alpha` and `beta` to a more skewed pair, e.g. `alpha=1, beta=8`
#   - Observe the empirical CDF need a larger `N` to hug the theoretical
#     CDF as tightly as it did for the symmetric case
