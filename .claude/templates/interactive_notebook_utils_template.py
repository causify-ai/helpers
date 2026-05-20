"""
Utility functions for Interactive Notebook Template.

Demonstrates best practices for creating interactive notebook widgets and plots.

Import as:

import interactive_notebook_utils_template as utils
"""

import ipywidgets
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
from IPython.display import display


# #############################################################################
# Cell 1: Basic Distribution Display
# #############################################################################


def cell1_plot_distribution_pdf() -> None:
    """
    Display basic distribution PDF with fixed parameters.

    Shows the probability density function of a Beta distribution and
    demonstrates basic plotting conventions.
    """
    # Create x values for plotting.
    x = np.linspace(0, 1, 1000)
    # Calculate PDF for Beta(2, 5) distribution.
    alpha, beta = 2, 5
    pdf = scipy.stats.beta.pdf(x, alpha, beta)
    # Create figure and plot.
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, pdf, linewidth=2, color="blue", label=f"Beta({alpha}, {beta})")
    ax.fill_between(x, pdf, alpha=0.3, color="blue")
    ax.set_xlabel("x", fontsize=12)
    ax.set_ylabel("Probability Density", fontsize=12)
    ax.set_title("Beta Distribution PDF", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


# #############################################################################
# Cell 2: Interactive Distribution Visualization
# #############################################################################


def _create_beta_pdf_plot(ax, alpha: float, beta: float) -> None:
    """
    Plot Beta distribution PDF on given axes.

    :param ax: Matplotlib axes object
    :param alpha: Shape parameter alpha
    :param beta: Shape parameter beta
    """
    x = np.linspace(0, 1, 1000)
    pdf = scipy.stats.beta.pdf(x, alpha, beta)
    ax.clear()
    ax.plot(x, pdf, linewidth=2.5, color="steelblue")
    ax.fill_between(x, pdf, alpha=0.2, color="steelblue")
    ax.set_xlabel("x", fontsize=11)
    ax.set_ylabel("Probability Density", fontsize=11)
    ax.set_title(f"Beta Distribution PDF: α={alpha}, β={beta}", fontsize=12)
    ax.grid(True, alpha=0.3)


def _create_beta_cdf_plot(ax, alpha: float, beta: float) -> None:
    """
    Plot Beta distribution CDF on given axes.

    :param ax: Matplotlib axes object
    :param alpha: Shape parameter alpha
    :param beta: Shape parameter beta
    """
    x = np.linspace(0, 1, 1000)
    cdf = scipy.stats.beta.cdf(x, alpha, beta)
    ax.clear()
    ax.plot(x, cdf, linewidth=2.5, color="darkorange")
    ax.set_xlabel("x", fontsize=11)
    ax.set_ylabel("Cumulative Probability", fontsize=11)
    ax.set_title(f"Beta Distribution CDF: α={alpha}, β={beta}", fontsize=12)
    ax.grid(True, alpha=0.3)


def _create_statistics_text(ax, alpha: float, beta: float) -> None:
    """
    Display distribution statistics as text.

    :param ax: Matplotlib axes object
    :param alpha: Shape parameter alpha
    :param beta: Shape parameter beta
    """
    # Calculate statistics.
    mean = alpha / (alpha + beta)
    variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
    mode = (alpha - 1) / (alpha + beta - 2) if alpha > 1 and beta > 1 else None
    # Create text content.
    ax.clear()
    ax.axis("off")
    stats_text = (
        f"Distribution Statistics\n\n"
        f"Mean: {mean:.4f}\n"
        f"Variance: {variance:.4f}\n"
        f"Std Dev: {np.sqrt(variance):.4f}"
    )
    if mode is not None:
        stats_text += f"\nMode: {mode:.4f}"
    ax.text(
        0.5,
        0.5,
        stats_text,
        fontsize=12,
        ha="center",
        va="center",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )


def cell2_interactive_distribution_explorer() -> None:
    """
    Create interactive widget to explore Beta distribution properties.

    Demonstrates:
    - Slider widgets for continuous parameters
    - Dropdown for selecting plot type
    - Real-time plot updates using observe() callbacks
    - Complex widget control architecture
    """
    # Create sliders for distribution parameters.
    alpha_slider = ipywidgets.FloatSlider(
        value=2,
        min=0.5,
        max=10,
        step=0.5,
        description="α (alpha):",
        continuous_update=False,
    )
    beta_slider = ipywidgets.FloatSlider(
        value=5,
        min=0.5,
        max=10,
        step=0.5,
        description="β (beta):",
        continuous_update=False,
    )
    # Create dropdown for plot type selection.
    plot_type_dropdown = ipywidgets.Dropdown(
        options=["PDF", "CDF", "Statistics"],
        value="PDF",
        description="Plot Type:",
    )
    # Create figure with single subplot.
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.close()

    # Update function called when any widget changes.
    def _on_widget_change(change):
        """Handle widget value changes and update plot."""
        alpha = alpha_slider.value
        beta = beta_slider.value
        plot_type = plot_type_dropdown.value
        # Clear and update plot based on selection.
        if plot_type == "PDF":
            _create_beta_pdf_plot(ax, alpha, beta)
        elif plot_type == "CDF":
            _create_beta_cdf_plot(ax, alpha, beta)
        else:  # Statistics
            _create_statistics_text(ax, alpha, beta)
        fig.canvas.draw_idle()

    # Register callbacks for all widgets.
    alpha_slider.observe(_on_widget_change, names="value")
    beta_slider.observe(_on_widget_change, names="value")
    plot_type_dropdown.observe(_on_widget_change, names="value")
    # Display initial plot.
    _on_widget_change(None)
    # Create layout with controls and plot.
    controls = ipywidgets.HBox([alpha_slider, beta_slider, plot_type_dropdown])
    display(controls)
    display(fig)


# #############################################################################
# Cell 3: Interactive Sampling Visualization
# #############################################################################


def cell3_interactive_sample_generator() -> None:
    """
    Create interactive widget to generate and visualize random samples.

    Demonstrates:
    - Multiple linked slider widgets
    - Histogram visualization
    - Sample statistics display
    - Using htutorial helper functions for widget building
    """
    # Create sliders for distribution parameters.
    alpha_slider = ipywidgets.FloatSlider(
        value=3,
        min=0.5,
        max=10,
        step=0.5,
        description="α:",
        continuous_update=False,
    )
    beta_slider = ipywidgets.FloatSlider(
        value=4,
        min=0.5,
        max=10,
        step=0.5,
        description="β:",
        continuous_update=False,
    )
    n_samples_slider = ipywidgets.IntSlider(
        value=1000,
        min=100,
        max=5000,
        step=100,
        description="N samples:",
        continuous_update=False,
    )
    seed_slider = ipywidgets.IntSlider(
        value=42,
        min=0,
        max=1000,
        step=1,
        description="seed:",
        continuous_update=False,
    )
    # Create figure with subplots.
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    plt.close()

    # Update function for generating samples and updating plots.
    def _on_sample_change(change):
        """Handle parameter changes and regenerate samples."""
        alpha = alpha_slider.value
        beta = beta_slider.value
        n_samples = n_samples_slider.value
        seed = seed_slider.value
        # Generate samples with fixed seed.
        np.random.seed(seed)
        samples = np.random.beta(alpha, beta, size=n_samples)
        # Update histogram plot.
        axes[0].clear()
        axes[0].hist(
            samples, bins=40, density=True, alpha=0.7, color="steelblue"
        )
        # Overlay theoretical PDF.
        x = np.linspace(0, 1, 1000)
        pdf = scipy.stats.beta.pdf(x, alpha, beta)
        axes[0].plot(x, pdf, linewidth=2.5, color="red", label="Theoretical PDF")
        axes[0].set_xlabel("x", fontsize=11)
        axes[0].set_ylabel("Density", fontsize=11)
        axes[0].set_title(f"Histogram of {n_samples} Samples", fontsize=12)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        # Update statistics display.
        axes[1].clear()
        axes[1].axis("off")
        mean_sample = np.mean(samples)
        std_sample = np.std(samples)
        mean_theory = alpha / (alpha + beta)
        # Create statistics text.
        stats_text = (
            f"Sample Statistics (N={n_samples})\n\n"
            f"Sample Mean: {mean_sample:.4f}\n"
            f"Theory Mean: {mean_theory:.4f}\n"
            f"Difference: {abs(mean_sample - mean_theory):.4f}\n\n"
            f"Sample Std: {std_sample:.4f}\n"
            f"Min: {np.min(samples):.4f}\n"
            f"Max: {np.max(samples):.4f}\n"
            f"Median: {np.median(samples):.4f}"
        )
        axes[1].text(
            0.5,
            0.5,
            stats_text,
            fontsize=11,
            ha="center",
            va="center",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5),
            family="monospace",
        )
        fig.canvas.draw_idle()

    # Register callbacks.
    alpha_slider.observe(_on_sample_change, names="value")
    beta_slider.observe(_on_sample_change, names="value")
    n_samples_slider.observe(_on_sample_change, names="value")
    seed_slider.observe(_on_sample_change, names="value")
    # Display initial plot.
    _on_sample_change(None)
    # Create layout: put sliders in vertical box.
    controls = ipywidgets.VBox(
        [alpha_slider, beta_slider, n_samples_slider, seed_slider]
    )
    display(controls)
    display(fig)


# #############################################################################
# Cell 4: Parameter Heatmap Exploration
# #############################################################################


def cell4_mean_variance_heatmap() -> None:
    """
    Create interactive heatmap showing distribution properties over parameter space.

    Demonstrates:
    - Dropdown for selecting which statistic to display
    - Computing statistics across a 2D parameter grid
    - Heatmap visualization with colorbar
    - Complex multi-dimensional interactive exploration
    """
    # Create dropdown for selecting statistic.
    stat_dropdown = ipywidgets.Dropdown(
        options=["Mean", "Variance", "Skewness", "Kurtosis"],
        value="Mean",
        description="Statistic:",
    )
    # Create figure for heatmap.
    fig, ax = plt.subplots(figsize=(10, 8))
    plt.close()

    # Update function for computing and displaying heatmap.
    def _on_stat_change(change):
        """Update heatmap based on selected statistic."""
        stat_name = stat_dropdown.value
        # Create parameter grid.
        alphas = np.linspace(0.5, 8, 30)
        betas = np.linspace(0.5, 8, 30)
        # Compute statistics across grid.
        stat_grid = np.zeros((len(betas), len(alphas)))
        for i, beta in enumerate(betas):
            for j, alpha in enumerate(alphas):
                if stat_name == "Mean":
                    stat_grid[i, j] = alpha / (alpha + beta)
                elif stat_name == "Variance":
                    stat_grid[i, j] = (alpha * beta) / (
                        (alpha + beta) ** 2 * (alpha + beta + 1)
                    )
                elif stat_name == "Skewness":
                    stat_grid[i, j] = scipy.stats.beta.stats(
                        alpha, beta, moments="s"
                    )
                else:  # Kurtosis
                    stat_grid[i, j] = scipy.stats.beta.stats(
                        alpha, beta, moments="k"
                    )
        # Clear and plot heatmap.
        ax.clear()
        im = ax.imshow(stat_grid, cmap="viridis", aspect="auto", origin="lower")
        ax.set_xlabel("α (alpha)", fontsize=12)
        ax.set_ylabel("β (beta)", fontsize=12)
        ax.set_title(
            f"{stat_name} Over Parameter Space", fontsize=13, fontweight="bold"
        )
        # Set tick labels.
        ax.set_xticks(np.linspace(0, len(alphas) - 1, 6))
        ax.set_xticklabels([f"{v:.1f}" for v in np.linspace(0.5, 8, 6)])
        ax.set_yticks(np.linspace(0, len(betas) - 1, 6))
        ax.set_yticklabels([f"{v:.1f}" for v in np.linspace(0.5, 8, 6)])
        # Add colorbar.
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(stat_name, fontsize=11)
        fig.canvas.draw_idle()

    # Register callback.
    stat_dropdown.observe(_on_stat_change, names="value")
    # Display initial plot.
    _on_stat_change(None)
    display(stat_dropdown)
    display(fig)
