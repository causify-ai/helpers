"""
Utility functions for Interactive Notebook Template.

Demonstrates best practices for creating interactive notebook widgets and plots.

Import as:

import interactive_notebook_utils_template as utils
"""

from typing import Any, Optional

import ipywidgets
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
from IPython.display import clear_output, display

import helpers.htutorial as htutori


# #############################################################################
# Cell 2: Interactive Distribution Explorer with Plot Type Selection
# #############################################################################


def cell2_interactive_distribution_explorer() -> None:
	"""
	Create interactive widget to explore Beta distribution properties.

	Demonstrates:
	- Slider widgets for continuous parameters via build_widget_control()
	- Dropdown for selecting plot type
	- Real-time plot updates using observe() callbacks
	- Multiple synchronized plots (1x4 layout)
	"""
	alpha_slider, alpha_box = htutori.build_widget_control(
		name="α (alpha)",
		description="Shape parameter alpha",
		min_val=0.5,
		max_val=10,
		step=0.5,
		initial_value=2,
		is_float=True,
	)
	beta_slider, beta_box = htutori.build_widget_control(
		name="β (beta)",
		description="Shape parameter beta",
		min_val=0.5,
		max_val=10,
		step=0.5,
		initial_value=5,
		is_float=True,
	)
	# Create dropdown for plot type selection.
	plot_type_dropdown = ipywidgets.Dropdown(
		options=["PDF", "CDF", "Statistics"],
		value="PDF",
		description="Plot Type:",
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
			plot_type = plot_type_dropdown.value
			x = np.linspace(0, 1, 1000)
			# Create 1x4 subplot layout.
			_, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(20, 5))
			# Plot 1: Main plot based on selection.
			if plot_type == "PDF":
				pdf = scipy.stats.beta.pdf(x, alpha, beta)
				ax1.plot(x, pdf, linewidth=2.5, color="steelblue")
				ax1.fill_between(x, pdf, alpha=0.2, color="steelblue")
				ax1.set_ylabel("Probability Density", fontsize=12)
				plot_title = f"Beta Distribution PDF: α={alpha}, β={beta}"
			elif plot_type == "CDF":
				cdf = scipy.stats.beta.cdf(x, alpha, beta)
				ax1.plot(x, cdf, linewidth=2.5, color="darkorange")
				ax1.set_ylabel("Cumulative Probability", fontsize=12)
				plot_title = f"Beta Distribution CDF: α={alpha}, β={beta}"
			else:  # Statistics
				ax1.axis("off")
				mean = alpha / (alpha + beta)
				variance = (alpha * beta) / (
					(alpha + beta) ** 2 * (alpha + beta + 1)
				)
				mode = (
					(alpha - 1) / (alpha + beta - 2)
					if alpha > 1 and beta > 1
					else None
				)
				stats_text = (
					f"Distribution Statistics\n\n"
					f"Mean: {mean:.4f}\n"
					f"Variance: {variance:.4f}\n"
					f"Std Dev: {np.sqrt(variance):.4f}"
				)
				if mode is not None:
					stats_text += f"\nMode: {mode:.4f}"
				htutori.add_fitted_text_box(
					ax1, stats_text, max_fontsize=14, min_fontsize=10
				)
				plot_title = "Distribution Statistics"
			ax1.set_xlabel("x", fontsize=12)
			ax1.set_title(
				plot_title, fontsize=14, fontweight="bold"
			)
			ax1.grid(True, alpha=0.3)
			# Plot 2: PDF overlay for reference.
			pdf = scipy.stats.beta.pdf(x, alpha, beta)
			ax2.plot(x, pdf, linewidth=2.5, color="steelblue", label="PDF")
			ax2.fill_between(x, pdf, alpha=0.2, color="steelblue")
			ax2.set_xlabel("x", fontsize=12)
			ax2.set_ylabel("Probability Density", fontsize=12)
			ax2.set_title("PDF Reference", fontsize=14, fontweight="bold")
			ax2.grid(True, alpha=0.3)
			ax2.legend(fontsize=10)
			# Plot 3: CDF for reference.
			cdf = scipy.stats.beta.cdf(x, alpha, beta)
			ax3.plot(x, cdf, linewidth=2.5, color="darkorange", label="CDF")
			ax3.set_xlabel("x", fontsize=12)
			ax3.set_ylabel("Cumulative Probability", fontsize=12)
			ax3.set_title("CDF Reference", fontsize=14, fontweight="bold")
			ax3.grid(True, alpha=0.3)
			ax3.legend(fontsize=10)
			# Plot 4: Comments.
			ax4.axis("off")
			ax4.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
			mean = alpha / (alpha + beta)
			comment_text = (
				f"Parameters:\n"
				f"  α (alpha): {alpha:.2f}\n"
				f"  β (beta): {beta:.2f}\n"
				f"  Plot Type: {plot_type}\n\n"
				f"Mean: {mean:.4f}\n\n"
				f"Observations:\n"
				f"- Adjust α and β to see\n"
				f"  how the shape changes\n"
				f"- PDF and CDF provide\n"
				f"  complementary views"
			)
			htutori.add_fitted_text_box(
				ax4, comment_text, max_fontsize=13, min_fontsize=10
			)
			plt.tight_layout()
			plt.show()

	# Register callbacks for all widgets.
	alpha_slider.observe(update_plot, names="value")
	beta_slider.observe(update_plot, names="value")
	plot_type_dropdown.observe(update_plot, names="value")
	# Display initial plot.
	update_plot()
	# Create layout with controls and plot.
	display(
		ipywidgets.VBox(
			[
				ipywidgets.Label(
					"Select parameters and view type:"
				),
				alpha_box,
				beta_box,
				plot_type_dropdown,
				output,
			]
		)
	)


# #############################################################################
# Cell 3: Interactive Sampling Visualization
# #############################################################################


def cell3_interactive_sample_generator() -> None:
	"""
	Create interactive widget to generate and visualize random samples.

	Demonstrates:
	- Multiple linked slider widgets via build_widget_control()
	- Logarithmic scale slider for sample count via build_log_widget_control()
	- Histogram visualization with theoretical overlay
	- Sample statistics display
	"""
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
			_, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(20, 5))
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
			pdf = scipy.stats.beta.pdf(x, alpha, beta)
			ax1.plot(
				x,
				pdf,
				linewidth=2.5,
				color="red",
				label="Theoretical PDF",
			)
			ax1.set_xlabel("x", fontsize=12)
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
			cdf = scipy.stats.beta.cdf(x, alpha, beta)
			ax3.plot(
				x,
				cdf,
				linewidth=2.5,
				color="red",
				label="Theoretical CDF",
			)
			ax3.set_xlabel("x", fontsize=12)
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
				f"Key Observations:\n"
				f"- Larger N → histogram\n"
				f"  approaches theoretical\n"
				f"- Law of Large Numbers:\n"
				f"  sample mean → μ\n"
				f"- Try different seeds to\n"
				f"  see sampling variability"
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
	# Create layout: put sliders in vertical box.
	display(
		ipywidgets.VBox(
			[
				ipywidgets.Label(
					"Configure sampling parameters:"
				),
				alpha_box,
				beta_box,
				n_box,
				seed_box,
				output,
			]
		)
	)
