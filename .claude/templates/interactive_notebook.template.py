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
# # Cell 1: Basic Distribution Display
#
# **Goal**:
# - Introduce the Beta distribution
# - Show a simple static plot
# - Understand probability density functions (PDF)
#
# **Plots**:
# - Probability density function (PDF) of the Beta distribution with fixed shape parameters
#   - Shows the characteristic curve shape
#   - Illustrates how the Beta distribution behaves on the interval $[0, 1]$
#
# **Key observations**:
# - The shape of the Beta distribution changes dramatically with different $\alpha$ and $\beta$ values
# - When $\alpha = \beta$, the distribution is symmetric around 0.5
# - When $\alpha > \beta$, the distribution skews toward 1
# - When $\alpha < \beta$, the distribution skews toward 0
# - The Beta distribution is a continuous probability distribution on $[0, 1]$, parameterized by shape parameters $\alpha$ and $\beta$

# %%
# Display the Beta distribution PDF with fixed parameters.
utils.cell1_plot_distribution_pdf()

# %% [markdown]
# # Cell 2: Interactive Distribution Explorer
#
# **Goal**:
# - Explore how changing distribution parameters affects the shape
# - Understand the relationship between $\alpha$, $\beta$, and distribution properties
# - See real-time updates as you adjust sliders
#
# **Plots**:
# - **PDF View**: Shows the probability density function shape
# - **CDF View**: Shows cumulative probability (useful for understanding quantiles)
# - **Statistics View**: Displays mean, variance, and mode
#
# **Parameters**:
# - `α (alpha)`: Controls the concentration toward 1
#   - Larger $\alpha$ shifts density toward 1
#   - Smaller $\alpha$ shifts density toward 0
# - `β (beta)`: Controls the concentration toward 0
#   - Larger $\beta$ shifts density toward 0
#   - Smaller $\beta$ shifts density toward 1
# - `Plot Type`: Choose which visualization to display
#
# **Key insights**:
# - The mean is $\mu = \frac{\alpha}{\alpha + \beta}$
# - The variance is $\sigma^2 = \frac{\alpha \beta}{(\alpha+\beta)^2(\alpha+\beta+1)}$
# - Both parameters affect the spread (variance) of the distribution

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

# %% [markdown]
# # Cell 4: Parameter Heatmap Exploration
#
# **Goal**:
# - Visualize how distribution statistics vary across the parameter space
# - Understand the joint effect of both $\alpha$ and $\beta$
# - Identify regions where the distribution has desired properties
#
# **Plots**:
# - **Heatmap**: Color represents the selected statistic across all $(\alpha, \beta)$ combinations
#   - Colors: darker = lower values, brighter = higher values
#   - Helps identify sweet spots for specific distribution properties
#
# **Parameters**:
# - `Statistic`: Choose which property to visualize
#   - **Mean**: The expected value $\mu = \frac{\alpha}{\alpha + \beta}$
#   - **Variance**: The spread $\sigma^2 = \frac{\alpha \beta}{(\alpha+\beta)^2(\alpha+\beta+1)}$
#   - **Skewness**: Asymmetry of the distribution
#   - **Kurtosis**: Heavy-tailedness of the distribution
#
# **Key observations**:
# - The mean increases along lines where $\frac{\alpha}{\alpha+\beta}$ is constant
# - Variance is maximized around $\alpha = \beta \approx 1$ (U-shaped distribution)
# - Variance is minimized at the corners (when one parameter is much larger)
# - Skewness and kurtosis reveal the distribution's shape properties

# %%
# Visualize distribution statistics across parameter space.
utils.cell4_mean_variance_heatmap()
