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

# %%
# %load_ext autoreload
# %autoreload 2

# System libraries.
import logging

# Third-party libraries.
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# %%
# Local utility.
import helpers.hdbg as hdbg
import helpers.hnotebook as hnotebook
import interactive_notebook_utils_template as utils

_LOG = logging.getLogger(__name__)

# Initialize notebook configuration and logging.
hnotebook.config_notebook()
hdbg.init_logger(verbosity=logging.INFO, use_exec_path=False)
hnotebook.set_logger_to_print(_LOG)

# %% [markdown]
# # Cell 2: Interactive Distribution Explorer
#
# **Goal**:
# - Visualize how distribution shape parameters ($\alpha$ and $\beta$) affect the Beta distribution
# - Understand the relationship between parameters and key statistical properties
# - Observe the probability density, cumulative distribution, and statistics simultaneously
# - See real-time updates as you adjust parameters using interactive sliders
# - Build intuition for how shape parameters control distribution behavior
#
# **Plots**:
# - **Selected View** (first panel): Choose between three complementary views:
#   - _Probability Density Function (PDF)_: Shows how probability mass is distributed across the domain [0,1]
#     - Taller peaks indicate higher probability density
#     - Shape changes based on $\alpha$ and $\beta$ values
#   - _Cumulative Distribution Function (CDF)_: Shows the probability of observing values less than or equal to x
#     - Always increases from 0 to 1
#     - Steeper regions indicate higher probability density (matches PDF)
#   - _Distribution Statistics_: Displays key summary statistics
#     - Mean: $\mu = \frac{\alpha}{\alpha+\beta}$
#     - Variance: $\sigma^2 = \frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}$
#     - Mode: $\frac{\alpha-1}{\alpha+\beta-2}$ (when $\alpha > 1$ and $\beta > 1$)
# - **PDF Reference** (second panel): Continuous reference showing the probability density
# - **CDF Reference** (third panel): Reference showing cumulative probabilities
# - **Comments** (fourth panel): Text summary with current parameter values and key observations
#
# **Parameters**:
# - `α (alpha)`: Shape parameter controlling concentration toward 1
#   - Larger $\alpha$ shifts the distribution toward 1 (right-skewed)
#   - Smaller $\alpha$ shifts the distribution toward 0 (left-skewed)
#   - Range: 0.5 to 10 with 0.5 increments
# - `β (beta)`: Shape parameter controlling concentration toward 0
#   - Larger $\beta$ shifts the distribution toward 0 (left-skewed)
#   - Smaller $\beta$ shifts the distribution toward 1 (right-skewed)
#   - Range: 0.5 to 10 with 0.5 increments
# - `Plot Type`: Dropdown to select which view to display in the first panel
#   - **PDF**: Probability density function
#   - **CDF**: Cumulative distribution function
#   - **Statistics**: Summary statistics display
#
# **Key Observations**:
# - **Symmetry**: The distribution is symmetric when $\alpha = \beta$
#   - Both tails behave identically
#   - Mean is exactly 0.5
# - **Concentration**: Increasing both $\alpha$ and $\beta$ concentrates the distribution
#   - High values create a narrow peak
#   - Low values create a flat or U-shaped distribution
# - **Skewness**: Asymmetry appears when $\alpha \neq \beta$
#   - $\alpha > \beta$: Distribution skews toward 1 (mean > 0.5)
#   - $\alpha < \beta$: Distribution skews toward 0 (mean < 0.5)
# - **Mode and Mean**: The mode (peak) and mean differ when $\alpha$ and $\beta$ are very different
#   - When $\alpha = \beta = 1$: Distribution is uniform (flat)
#   - When $\alpha$ and $\beta$ are small and unequal: U-shaped distribution appears

# %%
# Create interactive widget to explore the Beta distribution.
utils.cell2_interactive_distribution_explorer()

# %% [markdown]
# # Cell 3: Interactive Sample Generator
#
# **Goal**:
# - Understand sampling from the Beta distribution
# - Compare empirical samples to theoretical predictions
# - See the Law of Large Numbers in action
# - Observe convergence to the true mean
#
# **Plots**:
# - **Left**: Histogram of sampled values with theoretical PDF overlay
# - **Right**: Summary statistics comparing samples to theory
#
# **Parameters**:
# - `α (alpha)`: Shape parameter for the Beta distribution
# - `β (beta)`: Shape parameter for the Beta distribution
# - `N samples`: Number of samples to draw
#   - Smaller $N$: More variability between sample and theoretical mean
#   - Larger $N$: Sample mean converges to theoretical mean (Law of Large Numbers)
# - `seed`: Random seed for reproducibility
#
# **Key observations**:
# - As $N$ increases, the histogram approaches the theoretical PDF
# - The sample mean approaches the theoretical mean $\mu = \frac{\alpha}{\alpha + \beta}$
# - The difference between sample and theoretical mean decreases with more samples
# - Try different seeds to see how sampling variability changes

# %%
# Create interactive widget to generate and visualize samples.
utils.cell3_interactive_sample_generator()
