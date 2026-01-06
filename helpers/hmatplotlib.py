"""
Matplotlib utilities and plotting helpers.

Import as:

import helpers.hmatplotlib as hmatplo
"""

import logging
import math
from typing import Any, Optional, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# Default figure size for plots.
FIG_SIZE = (20, 5)


def get_multiple_plots(
    num_plots: int,
    num_cols: int,
    y_scale: Optional[float] = None,
    *args: Any,
    **kwargs: Any,
) -> Tuple[mpl.figure.Figure, np.array]:
    """
    Create figure to accommodate `num_plots` plots.

    The figure is arranged in rows with `num_cols` columns.

    :param num_plots: number of plots
    :param num_cols: number of columns to use in the subplot
    :param y_scale: the height of each plot. If `None`, the size of the whole
        figure equals the default `figsize`
    :return: figure and array of axes
    """
    hdbg.dassert_lte(1, num_plots)
    hdbg.dassert_lte(1, num_cols)
    # Heuristic to find the dimension of the fig.
    if y_scale is not None:
        hdbg.dassert_lt(0, y_scale)
        ysize = math.ceil(num_plots / num_cols) * y_scale
        figsize: Optional[Tuple[float, float]] = (20, ysize)
    else:
        figsize = None
    if "tight_layout" not in kwargs and not kwargs.get(
        "constrained_layout", False
    ):
        kwargs["tight_layout"] = True
    fig, ax = plt.subplots(
        math.ceil(num_plots / num_cols),
        num_cols,
        figsize=figsize,
        *args,
        **kwargs,
    )
    if isinstance(ax, np.ndarray):
        ax = ax.flatten()
    else:
        ax = np.array([ax])
    # Remove extra axes that can appear when `num_cols` > 1.
    empty_axes = ax[num_plots:]
    for empty_ax in empty_axes:
        empty_ax.remove()
    return fig, ax[:num_plots]
