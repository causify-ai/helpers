"""
Graph visualization utilities for networkx graphs.

Import as:

import helpers.hgraphviz as hgraphv
"""

import io
import logging
from typing import Any, Dict, Mapping, Optional, Tuple

import graphviz
import matplotlib.axes as maxes
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

# TODO(ai_gp): Use import PIL if possible.
from PIL import Image

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# Default figure size for DAG visualizations
FIG_SIZE = (10, 8)

# Default DPI for image rendering
FIG_DPI = 150


# TODO(ai_gp): Add support for figsize and DPI.
def _graph_to_graphviz_dot(
    G: nx.DiGraph,
    title: str,
    *,
    node_colors: Optional[Mapping[str, Any]] = None,
    edge_colors: Optional[Mapping[Tuple[str, str], Any]] = None,
) -> str:
    """
    Convert a networkx DiGraph to a graphviz DOT string with styling.

    Use the style from `.claude/templates/graphviz.template.md`

    :param G: Directed acyclic graph
    :param title: Graph title
    :param node_colors: Optional per-node fill color
    :param edge_colors: Optional per-edge color
    :return: DOT string for graphviz rendering
    """

    # Map matplotlib colors to hex for graphviz.
    def _to_hex(color: Any) -> str:
        if isinstance(color, str):
            if color.startswith("#"):
                return color
            return color
        return "#A6C8F4"

    # Build the DOT representation.
    lines = ["digraph {", "    rankdir=TB;", "    splines=true;"]
    lines.append("    nodesep=0.6;")
    lines.append("    ranksep=0.6;")
    lines.append(
        '    node [shape=box, style="rounded,filled", fontname="Helvetica", '
        "fontsize=11, penwidth=1.4];"
    )
    # Add nodes with colors.
    for node in G.nodes():
        color = _to_hex((node_colors or {}).get(node, "#A6C8F4"))
        lines.append(f'    "{node}" [fillcolor="{color}"];')
    # Add edges with colors if specified.
    for u, v in G.edges():
        color = (edge_colors or {}).get((u, v), "#555555")
        color = _to_hex(color)
        lines.append(f'    "{u}" -> "{v}" [color="{color}", penwidth=2.0];')
    lines.append("}")
    return "\n".join(lines)


def plot_dag_with_graphviz(
    G: nx.DiGraph,
    title: str,
    *,
    node_colors: Optional[Mapping[str, Any]] = None,
    edge_colors: Optional[Mapping[Tuple[str, str], Any]] = None,
    ax: Optional[maxes.Axes] = None,
    figsize: Optional[Tuple[int, int]] = None,
    dpi: int = FIG_DPI,
) -> None:
    """
    Render a DAG using graphviz DOT format with professional styling.

    Uses graphviz's layout engine for automatic positioning and supports
    custom node and edge colors. Nodes are rounded rectangles with optional
    fill colors. The figsize parameter controls the output size of the
    rendered graph.

    :param G: Directed acyclic graph to plot
    :param title: Title displayed on the axes
    :param node_colors: Optional per-node fill color
    :param edge_colors: Optional per-edge color
    :param ax: Matplotlib axes to draw on
    :param figsize: Size of output graph as (width, height) in inches
    :param dpi: Resolution in dots per inch
    """
    if figsize is None:
        figsize = FIG_SIZE
    dot_str = _graph_to_graphviz_dot(
        G, title, node_colors=node_colors, edge_colors=edge_colors, size=figsize
    )
    # Render to PNG with specified DPI.
    g = graphviz.Source(dot_str, format="png")
    # TODO(gp): DPI setting doesn't work in graphviz.Source.
    png_data = g.pipe(format="png")
    img = Image.open(io.BytesIO(png_data))
    if ax is not None:
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(title, fontsize=12, fontweight="bold")
    else:
        fig, ax_new = plt.subplots(figsize=figsize)
        ax_new.imshow(img)
        ax_new.axis("off")
        ax_new.set_title(title, fontsize=12, fontweight="bold")
        fig.tight_layout()


def plot_dag_with_networkx_rounded_boxes(
    G: nx.DiGraph,
    title: str,
    *,
    node_colors: Optional[Mapping[str, Any]] = None,
    edge_colors: Optional[Mapping[Tuple[str, str], Any]] = None,
    ax: Optional[maxes.Axes] = None,
) -> None:
    """
    Render a DAG using NetworkX with rounded box nodes.

    :param G: Directed acyclic graph to plot
    :param title: Title displayed on the axes
    :param node_colors: Optional per-node fill color
    :param edge_colors: Optional per-edge color
    :param ax: Matplotlib axes to draw on
    """
    # Use hierarchical layout for better visualization.
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    # Draw edges with visible arrow heads.
    edge_list = list(G.edges())
    if edge_list:
        edge_color_list = [
            (edge_colors or {}).get(e, "#555555") for e in edge_list
        ]
        nx.draw_networkx_edges(
            G,
            pos,
            arrowsize=35,
            arrowstyle="-|>",
            width=2.0,
            ax=ax,
            edge_color=edge_color_list,
        )
    else:
        nx.draw_networkx_edges(
            G,
            pos,
            arrowsize=35,
            arrowstyle="-|>",
            width=2.0,
            ax=ax,
        )
    # Draw nodes as rounded rectangles.
    node_color_list = (
        [(node_colors or {}).get(n, "#A6C8F4") for n in G.nodes()]
        if node_colors
        else "#A6C8F4"
    )
    if ax is not None:
        for i, node in enumerate(G.nodes()):
            x, y = pos[node]
            text_len = len(str(node))
            width = max(0.25, text_len * 0.08)
            height = 0.2
            # Get the appropriate node color.
            color = (
                node_color_list[i]
                if isinstance(node_color_list, list)
                else node_color_list
            )
            box = mpatches.FancyBboxPatch(
                (x - width / 2, y - height / 2),
                width,
                height,
                boxstyle="round,pad=0.02",
                facecolor=color,
                edgecolor="black",
                linewidth=1.5,
            )
            ax.add_patch(box)
            ax.text(
                x,
                y,
                str(node),
                ha="center",
                va="center",
                fontsize=9,
                fontweight="normal",
            )
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.axis("off")
        ax.margins(0.2)


def plot_dag_with_networkx(
    G: nx.DiGraph,
    pos: Dict,
    *,
    node_color: Any = None,
    edge_color: Any = None,
    ax: Optional[maxes.Axes] = None,
) -> None:
    """
    Render a DAG using NetworkX's drawing functions.

    :param G: Graph to draw
    :param pos: Node position dictionary
    :param node_color: Single color or list of colors for nodes
    :param edge_color: Single color or list of colors for edges
    :param ax: Matplotlib axes object
    """
    # Draw nodes with customizable color and size.
    node_kwargs = {"node_size": 2000, "edgecolors": "black", "ax": ax}
    if node_color is not None:
        node_kwargs["node_color"] = node_color
    nx.draw_networkx_nodes(G, pos, **node_kwargs)
    # Draw edges with arrows and customizable colors.
    edge_kwargs = {"arrowsize": 20, "arrowstyle": "-|>", "width": 1.8, "ax": ax}
    if edge_color is not None:
        edge_kwargs["edge_color"] = edge_color
    nx.draw_networkx_edges(G, pos, **edge_kwargs)


def plot_causal_dag(
    G: nx.DiGraph,
    title: str,
    *,
    mode: str = "graphviz",
    node_colors: Optional[Mapping[str, Any]] = None,
    edge_colors: Optional[Mapping[Tuple[str, str], Any]] = None,
    ax: Optional[maxes.Axes] = None,
    figsize: Optional[Tuple[int, int]] = None,
    dpi: int = FIG_DPI,
    pos: Optional[Dict] = None,
) -> Optional[maxes.Axes]:
    """
    Render a DAG using the specified visualization mode.

    Dispatches to the appropriate plotting function based on the mode
    parameter. Supports three rendering backends:
      - "graphviz": Uses graphviz DOT format with automatic layout
      - "networkx_rounded_boxes": Uses NetworkX with rounded box nodes
      - "networkx": Uses basic NetworkX drawing functions

    :param G: Directed acyclic graph to plot
    :param title: Title displayed on the axes
    :param mode: Visualization mode
        - "graphviz": Uses graphviz DOT format with automatic layout
        - "networkx_rounded_boxes": Uses NetworkX with rounded box nodes
        - "networkx": Uses basic NetworkX drawing functions
    :param node_colors: Per-node fill color mapping
    :param edge_colors: Per-edge color mapping
    :param ax: Matplotlib axes to draw on
        - Default: Creates new figure if None
    :param figsize: Size as (width, height) in inches
        - For "graphviz" mode: controls the rendered graph output size
        - For other modes: controls the matplotlib figure size
    :param dpi: Resolution in dots per inch
    :param pos: Node position dictionary
        - Only used with mode="networkx"
    :return: The axes containing the plot
    """
    # Validate the visualization mode.
    hdbg.dassert_in(
        mode,
        ("graphviz", "networkx_rounded_boxes", "networkx"),
        "Invalid visualization mode '%s'",
        mode,
    )
    # Create a new figure if no axes provided.
    fig = None
    if ax is None:
        if figsize is None:
            figsize = FIG_SIZE
        fig, ax = plt.subplots(figsize=figsize)
    # Dispatch to the appropriate plotting function.
    if mode == "graphviz":
        plot_dag_with_graphviz(
            G,
            title,
            node_colors=node_colors,
            edge_colors=edge_colors,
            ax=ax,
            figsize=figsize,
            dpi=dpi,
        )
    elif mode == "networkx_rounded_boxes":
        plot_dag_with_networkx_rounded_boxes(
            G,
            title,
            node_colors=node_colors,
            edge_colors=edge_colors,
            ax=ax,
        )
    elif mode == "networkx":
        if pos is None:
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        node_color = list(node_colors.values())[0] if node_colors else None
        edge_color = list(edge_colors.values())[0] if edge_colors else None
        plot_dag_with_networkx(
            G,
            pos,
            node_color=node_color,
            edge_color=edge_color,
            ax=ax,
        )
        ax.set_title(title, fontsize=12, fontweight="bold")
    # Finalize the figure layout if it was created.
    if fig is not None:
        fig.tight_layout()
    return ax
