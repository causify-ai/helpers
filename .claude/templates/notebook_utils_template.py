"""
Utility functions for Interactive Notebook Template.

Demonstrates best practices for creating interactive notebook widgets and plots.

Import as:

import notebook_utils_template as utils
"""

import logging

from typing import Any, Optional, Tuple

import ipywidgets
import matplotlib.pyplot as plt
import numpy as np
import math
from IPython.display import clear_output, display

import helpers.hnotebook as hnotebo
import helpers.htutorial as htutori


_LOG = logging.getLogger(__name__)


def init_loggers(notebook_log: logging.Logger) -> None:
    global _LOG
    hnotebo.init_loggers(notebook_log, utils_log=_LOG)


# #############################################################################
# Pure-Python replacements for scipy.stats distributions (no scipy dependency)
# #############################################################################


def _beta_pdf(x, a, b):
    """
    Compute the Beta(a, b) PDF at points x.

    f(x; a, b) = x^(a-1) * (1-x)^(b-1) / B(a, b)
    where B(a, b) = Gamma(a)*Gamma(b) / Gamma(a+b)
    """
    x = np.asarray(x, dtype=float)
    const = math.gamma(a + b) / (math.gamma(a) * math.gamma(b))
    return const * x ** (a - 1) * (1 - x) ** (b - 1)


def _beta_cdf(x, a, b):
    """
    Compute the Beta(a, b) CDF at points x via numerical integration.

    Uses trapezoidal integration of the PDF on a fine grid, then
    interpolates to the requested x values.
    """
    x = np.asarray(x, dtype=float)
    # Use a fine grid for accurate numerical integration.
    n_fine = 10000
    x_fine = np.linspace(0, 1, n_fine)
    pdf_fine = _beta_pdf(x_fine, a, b)
    # Cumulative trapezoidal integration.
    dx = x_fine[1] - x_fine[0]
    cdf_fine = np.zeros(n_fine)
    cdf_fine[1:] = np.cumsum(0.5 * (pdf_fine[1:] + pdf_fine[:-1])) * dx
    # Interpolate to the requested x values.
    return np.interp(x, x_fine, cdf_fine)


def _norm_pdf(x, mu=0.0, sigma=1.0):
    """
    Compute the Normal(mu, sigma^2) PDF at points x.

    f(x; mu, sigma) = 1/(sigma*sqrt(2*pi)) * exp(-(x-mu)^2 / (2*sigma^2))
    """
    x = np.asarray(x, dtype=float)
    coeff = 1.0 / (sigma * np.sqrt(2 * np.pi))
    return coeff * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _norm_cdf(x, mu=0.0, sigma=1.0):
    """
    Compute the Normal(mu, sigma^2) CDF at points x.

    Uses the error function: Phi(x) = 0.5 * (1 + erf((x-mu)/(sigma*sqrt(2))))
    """
    x = np.asarray(x, dtype=float)
    z = (x - mu) / (sigma * np.sqrt(2))
    # math.erf is scalar; vectorize for array input.
    _erf = np.vectorize(math.erf)
    return 0.5 * (1.0 + _erf(z))


# #############################################################################
# Cell 1: Interactive Distribution Explorer with Plot Type Selection
# #############################################################################


def cell1_interactive_distribution_explorer(
    *,
    figsize: Optional[Tuple[float, float]] = None,
) -> None:
    """
    Create interactive widget to explore Beta and Normal distributions.

    Demonstrates:
    - Slider widgets for continuous parameters via build_widget_control()
    - Dropdown for selecting distribution type
    - Real-time plot updates using observe() callbacks
    - Multiple synchronized plots (1x3 layout)

    :param figsize: Optional figure size (width, height). Defaults to
        plt.rcParams["figure.figsize"]
    """
    if figsize is None:
        figsize = plt.rcParams["figure.figsize"]
    alpha_slider, alpha_box = htutori.build_widget_control(
        name="α (alpha)",
        description="α (alpha)",
        min_val=0.5,
        max_val=10,
        step=0.5,
        initial_value=2,
        is_float=True,
    )
    beta_slider, beta_box = htutori.build_widget_control(
        name="β (beta)",
        description="β (beta)",
        min_val=0.5,
        max_val=10,
        step=0.5,
        initial_value=5,
        is_float=True,
    )
    # Create dropdown for distribution type selection.
    dist_type_dropdown = ipywidgets.Dropdown(
        options=["Beta", "Normal"],
        value="Beta",
        description="Distribution Type:",
        style={"description_width": "initial"},
    )
    output = ipywidgets.Output()

    def update_plot(change: Optional[Any] = None) -> None:
        """
        Handle widget value changes and update plot.

        :param change: Dictionary with change information (unused)
        """
        _ = change
        with output:
            clear_output(wait=True)
            alpha = alpha_slider.value
            beta = beta_slider.value
            dist_type = dist_type_dropdown.value

            # Create 1x3 subplot layout.
            _, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=figsize)

            if dist_type == "Beta":
                x = np.linspace(0, 1, 1000)
                # Plot 1: PDF for reference.
                pdf = _beta_pdf(x, alpha, beta)
                ax1.plot(x, pdf, linewidth=2.5, color="steelblue", label="PDF")
                ax1.fill_between(x, pdf, alpha=0.2, color="steelblue")
                ax1.set_xlabel(
                    "x\n\nShows the probability density "
                    "function of the distribution",
                    fontsize=10,
                )
                ax1.set_ylabel("Probability Density", fontsize=12)
                ax1.set_title("PDF Reference", fontsize=14, fontweight="bold")
                ax1.grid(True, alpha=0.3)
                ax1.legend(fontsize=10)
                # Plot 2: CDF for reference.
                cdf = _beta_cdf(x, alpha, beta)
                ax2.plot(x, cdf, linewidth=2.5, color="darkorange", label="CDF")
                ax2.set_xlabel(
                    "x\n\nShows the cumulative distribution function",
                    fontsize=10,
                )
                ax2.set_ylabel("Cumulative Probability", fontsize=12)
                ax2.set_title("CDF Reference", fontsize=14, fontweight="bold")
                ax2.grid(True, alpha=0.3)
                ax2.legend(fontsize=10)
                # Plot 3: Comments.
                ax3.axis("off")
                ax3.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
                mean = alpha / (alpha + beta)
                comment_text = (
                    f"Parameters:\n"
                    f"  α (alpha): {alpha:.2f}\n"
                    f"  β (beta): {beta:.2f}\n\n"
                    f"Mean: {mean:.4f}"
                )
                htutori.add_fitted_text_box(
                    ax3, comment_text, max_fontsize=13, min_fontsize=10
                )
            else:  # Normal
                mean = alpha
                variance = beta
                std_dev = np.sqrt(variance)
                x = np.linspace(mean - 4 * std_dev, mean + 4 * std_dev, 1000)
                # Plot 1: PDF for reference.
                pdf = _norm_pdf(x, mean, std_dev)
                ax1.plot(x, pdf, linewidth=2.5, color="steelblue", label="PDF")
                ax1.fill_between(x, pdf, alpha=0.2, color="steelblue")
                ax1.set_xlabel(
                    "x\n\nShows the probability density "
                    "function of the distribution",
                    fontsize=10,
                )
                ax1.set_ylabel("Probability Density", fontsize=12)
                ax1.set_title("PDF Reference", fontsize=14, fontweight="bold")
                ax1.grid(True, alpha=0.3)
                ax1.legend(fontsize=10)
                # Plot 2: CDF for reference.
                cdf = _norm_cdf(x, mean, std_dev)
                ax2.plot(x, cdf, linewidth=2.5, color="darkorange", label="CDF")
                ax2.set_xlabel(
                    "x\n\nShows the cumulative distribution function",
                    fontsize=10,
                )
                ax2.set_ylabel("Cumulative Probability", fontsize=12)
                ax2.set_title("CDF Reference", fontsize=14, fontweight="bold")
                ax2.grid(True, alpha=0.3)
                ax2.legend(fontsize=10)
                # Plot 3: Comments.
                ax3.axis("off")
                ax3.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
                comment_text = (
                    f"Parameters:\n"
                    f"  μ (mean): {mean:.2f}\n"
                    f"  σ² (variance): {variance:.2f}\n\n"
                    f"Std dev: {std_dev:.2f}"
                )
                htutori.add_fitted_text_box(
                    ax3, comment_text, max_fontsize=13, min_fontsize=10
                )
            plt.tight_layout()
            plt.show()

    # Register callbacks for all widgets.
    alpha_slider.observe(update_plot, names="value")
    beta_slider.observe(update_plot, names="value")
    dist_type_dropdown.observe(update_plot, names="value")
    # Display initial plot.
    update_plot()
    # HTML info box describing the α and β parameters.
    param_info = ipywidgets.HTML(
        "<div style='background:#f5f5f5; padding:10px 14px; border-radius:4px; "
        "border-left:3px solid #4682b4; font-size:13px; line-height:1.8'>"
        "<b>α (alpha)</b> — For <i>Beta</i>: shape parameter that controls the "
        "distribution's skew. For <i>Normal</i>: the mean <i>μ</i> of the "
        "distribution<br>"
        "<b>β (beta)</b> — For <i>Beta</i>: shape parameter that controls the "
        "distribution's skew. For <i>Normal</i>: the variance <i>σ²</i> of "
        "the distribution<br>"
        "<b>Distribution</b> — toggle between "
        "<code>Beta</code> (supported on [0,1]) and "
        "<code>Normal</code> (unbounded)"
        "</div>"
    )
    # Create layout:
    #   Top row: controls on the left, info box on the right.
    #   Bottom: the 3 plots.
    controls = ipywidgets.VBox(
        [
            alpha_box,
            beta_box,
            dist_type_dropdown,
        ]
    )
    top_row = ipywidgets.HBox([controls, param_info])
    display(ipywidgets.VBox([top_row, output]))


# #############################################################################
# Cell 2: Interactive Sampling Visualization
# #############################################################################


def cell2_interactive_sample_generator(
    *,
    figsize: Optional[Tuple[float, float]] = None,
) -> None:
    """
    Create interactive widget to generate and visualize random samples.

    Demonstrates:
    - Multiple linked slider widgets via build_widget_control()
    - Logarithmic scale slider for sample count via build_log_widget_control()
    - Histogram visualization with theoretical overlay
    - Sample statistics display

    :param figsize: Optional figure size (width, height). Defaults to
        plt.rcParams["figure.figsize"]
    """
    if figsize is None:
        figsize = plt.rcParams["figure.figsize"]
    alpha_slider, alpha_box = htutori.build_widget_control(
        name="α (alpha)",
        description="Shape parameter alpha",
        min_val=0.5,
        max_val=10,
        step=0.5,
        initial_value=3,
        is_float=True,
    )
    beta_slider, beta_box = htutori.build_widget_control(
        name="β (beta)",
        description="Shape parameter beta",
        min_val=0.5,
        max_val=10,
        step=0.5,
        initial_value=4,
        is_float=True,
    )
    # Create N samples widget with logarithmic slider.
    # Uses exponents 2-12 for base 2: gives values 4, 8, ..., 4096
    # Initial exponent 10 gives initial value of 1024
    n_exp_slider, n_box = htutori.build_log_widget_control(
        name="log(N)",
        description="N (total samples)",
        min_exp=2,
        max_exp=12,
        initial_exp=10,
        base=2,
    )
    seed_slider, seed_box = htutori.build_widget_control(
        name="seed",
        description="Random seed",
        min_val=0,
        max_val=1000,
        step=1,
        initial_value=42,
        is_float=False,
    )
    output = ipywidgets.Output()

    def update_plot(change: Optional[Any] = None) -> None:
        """
        Handle parameter changes and regenerate samples.

        :param change: Dictionary with change information (unused)
        """
        _ = change
        with output:
            clear_output(wait=True)
            alpha = alpha_slider.value
            beta = beta_slider.value
            n_samples = 2**n_exp_slider.value
            seed = seed_slider.value
            # Generate samples with fixed seed.
            np.random.seed(seed)
            samples = np.random.beta(alpha, beta, size=n_samples)
            # Create 1x4 subplot layout.
            _, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=figsize)
            # Plot 1: Histogram of samples with theoretical PDF overlay.
            ax1.hist(
                samples,
                bins=40,
                density=True,
                alpha=0.7,
                color="steelblue",
                label=f"Histogram (N={n_samples})",
            )
            x = np.linspace(0, 1, 1000)
            pdf = _beta_pdf(x, alpha, beta)
            ax1.plot(
                x,
                pdf,
                linewidth=2.5,
                color="red",
                label="Theoretical PDF",
            )
            ax1.set_xlabel(
                "x\n\nSampled values compared to "
                "theoretical distribution",
                fontsize=10,
            )
            ax1.set_ylabel("Density", fontsize=12)
            ax1.set_title(
                f"Sample Distribution (N={n_samples})",
                fontsize=14,
                fontweight="bold",
            )
            ax1.legend(fontsize=10)
            ax1.grid(True, alpha=0.3)
            # Plot 2: Sample statistics.
            ax2.axis("off")
            ax2.set_title(
                "Sample Statistics", fontsize=14, fontweight="bold", pad=20
            )
            mean_sample = np.mean(samples)
            std_sample = np.std(samples)
            mean_theory = alpha / (alpha + beta)
            stats_text = (
                f"Sample Mean: {mean_sample:.4f}\n"
                f"Theory Mean: {mean_theory:.4f}\n"
                f"Difference: {abs(mean_sample - mean_theory):.4f}\n\n"
                f"Sample Std: {std_sample:.4f}\n"
                f"Min: {np.min(samples):.4f}\n"
                f"Max: {np.max(samples):.4f}\n"
                f"Median: {np.median(samples):.4f}"
            )
            htutori.add_fitted_text_box(
                ax2, stats_text, max_fontsize=13, min_fontsize=10
            )
            # Plot 3: CDF comparison.
            x_sorted = np.sort(samples)
            y_ecdf = np.arange(1, len(x_sorted) + 1) / len(x_sorted)
            ax3.plot(
                x_sorted,
                y_ecdf,
                linewidth=1.5,
                color="steelblue",
                label="Empirical CDF",
                alpha=0.7,
            )
            cdf = _beta_cdf(x, alpha, beta)
            ax3.plot(
                x,
                cdf,
                linewidth=2.5,
                color="red",
                label="Theoretical CDF",
            )
            ax3.set_xlabel(
                "x\n\nSample vs. theoretical "
                "statistics comparison",
                fontsize=10,
            )
            ax3.set_ylabel("Cumulative Probability", fontsize=12)
            ax3.set_title("CDF Comparison", fontsize=14, fontweight="bold")
            ax3.legend(fontsize=10)
            ax3.grid(True, alpha=0.3)
            # Plot 4: Comments.
            ax4.axis("off")
            ax4.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
            comment_text = (
                f"Parameters:\n"
                f"  α (alpha): {alpha:.2f}\n"
                f"  β (beta): {beta:.2f}\n"
                f"  N (samples): {n_samples}\n"
                f"  seed: {seed}\n\n"
                f"Sample statistics:\n"
                f"  mean: {mean_sample:.4f}\n"
                f"  std: {std_sample:.4f}\n"
                f"  theory mean: {mean_theory:.4f}"
            )
            htutori.add_fitted_text_box(
                ax4, comment_text, max_fontsize=12, min_fontsize=9
            )
            plt.tight_layout()
            plt.show()

    # Register callbacks.
    alpha_slider.observe(update_plot, names="value")
    beta_slider.observe(update_plot, names="value")
    n_exp_slider.observe(update_plot, names="value")
    seed_slider.observe(update_plot, names="value")
    # Display initial plot.
    update_plot()
    # HTML info box describing the sampling parameters.
    sample_info = ipywidgets.HTML(
        "<div style='background:#f5f5f5; padding:10px 14px; border-radius:4px; "
        "border-left:3px solid #4682b4; font-size:13px; line-height:1.8'>"
        "<b>α (alpha)</b> — Shape parameter that controls the "
        "distribution's skew<br>"
        "<b>β (beta)</b> — Shape parameter that controls the "
        "distribution's skew<br>"
        "<b>N (samples)</b> — Number of random samples to draw from the "
        "Beta distribution. Uses a log₂ slider for wide range<br>"
        "<b>seed</b> — Random seed for reproducibility "
        "(same seed → same samples)"
        "</div>"
    )
    # Create layout:
    #   Top row: controls on the left, info box on the right.
    #   Bottom: the 4 plots.
    controls = ipywidgets.VBox(
        [
            alpha_box,
            beta_box,
            n_box,
            seed_box,
        ]
    )
    top_row = ipywidgets.HBox([controls, sample_info])
    display(ipywidgets.VBox([top_row, output]))
