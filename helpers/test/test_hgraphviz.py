import io
from typing import Any, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image

import helpers.hgraphviz as hgraphv
import helpers.hunit_test as hunitest


# #############################################################################
# Test_graph_to_graphviz_dot
# #############################################################################


class Test_graph_to_graphviz_dot(hunitest.TestCase):
    """
    Test the _graph_to_graphviz_dot function.
    """

    def helper(
        self,
        G: nx.DiGraph,
        title: str,
        expected: str,
        *,
        node_colors: Optional[Dict[str, str]] = None,
        edge_colors: Optional[Dict[Tuple[str, str], str]] = None,
        size: Optional[Tuple[float, float]] = None,
        dpi: int = hgraphv.FIG_DPI,
    ) -> None:
        """
        Test helper for _graph_to_graphviz_dot.

        :param G: Input directed acyclic graph
        :param title: Graph title
        :param expected: Expected DOT output string
        :param node_colors: Optional per-node fill colors
        :param edge_colors: Optional per-edge colors
        :param size: Optional figure size
        :param dpi: Dots per inch for rendering
        """
        # Run test.
        actual = hgraphv._graph_to_graphviz_dot(
            G, title, node_colors=node_colors, edge_colors=edge_colors, size=size, dpi=dpi
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test basic graph with two nodes and one edge.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Test Graph"
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected)

    def test2(self) -> None:
        """
        Test graph with multiple nodes and edges.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
        title = "Multi Node Graph"
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "C" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
            "A" -> "C" [color="#555555", penwidth=2.0];
            "B" -> "C" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected)

    def test3(self) -> None:
        """
        Test graph with node colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Colored Graph"
        node_colors = {"A": "#FF0000", "B": "#00FF00"}
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#FF0000"];
            "B" [fillcolor="#00FF00"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected, node_colors=node_colors)

    def test4(self) -> None:
        """
        Test graph with edge colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Edge Colors"
        edge_colors = {("A", "B"): "#0000FF"}
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#0000FF", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected, edge_colors=edge_colors)

    def test5(self) -> None:
        """
        Test graph with custom size.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Sized Graph"
        size = (12.5, 10.5)
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            size="12.5,10.5";
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected, size=size)

    def test6(self) -> None:
        """
        Test graph with single node and no edges.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("A")
        title = "Single Node"
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
        }
        """
        # Run test.
        self.helper(G, title, expected)

    def test7(self) -> None:
        """
        Test graph with non-string node names converted to strings.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        title = "Numeric Nodes"
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "1" [fillcolor="#A6C8F4"];
            "2" [fillcolor="#A6C8F4"];
            "3" [fillcolor="#A6C8F4"];
            "1" -> "2" [color="#555555", penwidth=2.0];
            "2" -> "3" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected)

    def test8(self) -> None:
        """
        Test hex color conversion for node colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("A")
        title = "Hex Color Test"
        node_colors = {"A": "#ABCDEF"}
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#ABCDEF"];
        }
        """
        # Run test.
        self.helper(G, title, expected, node_colors=node_colors)

    def test9(self) -> None:
        """
        Test default color when node not in color mapping.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Partial Colors"
        node_colors = {"A": "#FF0000"}
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#FF0000"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected, node_colors=node_colors)

    def test10(self) -> None:
        """
        Test default edge color when edge not in color mapping.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        title = "Partial Edge Colors"
        edge_colors = {("A", "B"): "#FF0000"}
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "C" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#FF0000", penwidth=2.0];
            "B" -> "C" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected, edge_colors=edge_colors)

    def test11(self) -> None:
        """
        Test that output is valid DOT format string.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("Start", "Process"), ("Process", "End")])
        title = "Valid DOT"
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=150;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "Start" [fillcolor="#A6C8F4"];
            "Process" [fillcolor="#A6C8F4"];
            "End" [fillcolor="#A6C8F4"];
            "Start" -> "Process" [color="#555555", penwidth=2.0];
            "Process" -> "End" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        self.helper(G, title, expected)

    def test12(self) -> None:
        """
        Test graph with custom DPI.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "DPI Graph"
        dpi = 200
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=200;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        actual = hgraphv._graph_to_graphviz_dot(
            G, title, dpi=dpi
        )
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test13(self) -> None:
        """
        Test graph with high DPI (300).
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "High DPI"
        dpi = 300
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            dpi=300;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        actual = hgraphv._graph_to_graphviz_dot(
            G, title, dpi=dpi
        )
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test14(self) -> None:
        """
        Test graph with both size and DPI.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Size and DPI"
        size = (12.5, 10.5)
        dpi = 200
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            size="12.5,10.5";
            dpi=200;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Run test.
        actual = hgraphv._graph_to_graphviz_dot(
            G, title, size=size, dpi=dpi
        )
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)


# #############################################################################
# Test_plot_dag_with_graphviz
# #############################################################################


class Test_plot_dag_with_graphviz(hunitest.TestCase):
    """
    Test the plot_dag_with_graphviz function.
    """

    def test1(self) -> None:
        """
        Test basic DAG plotting with graphviz.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        title = "Test DAG"
        # Run test and check no exception is raised.
        hgraphv.plot_dag_with_graphviz(G, title)

    def test2(self) -> None:
        """
        Test with custom node colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Colored DAG"
        node_colors = {"A": "#FF0000", "B": "#00FF00"}
        # Run test.
        hgraphv.plot_dag_with_graphviz(G, title, node_colors=node_colors)

    def test3(self) -> None:
        """
        Test with custom edge colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Edge Colored DAG"
        edge_colors = {("A", "B"): "#0000FF"}
        # Run test.
        hgraphv.plot_dag_with_graphviz(G, title, edge_colors=edge_colors)

    def test4(self) -> None:
        """
        Test with custom figsize.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Sized DAG"
        figsize = (12, 10)
        # Run test.
        hgraphv.plot_dag_with_graphviz(G, title, figsize=figsize)

    def test5(self) -> None:
        """
        Test with matplotlib axes provided.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "DAG on Axes"
        fig, ax = plt.subplots()
        # Run test.
        hgraphv.plot_dag_with_graphviz(G, title, ax=ax)
        # Check outputs.
        self.assertIsNotNone(ax.images)
        plt.close(fig)

    def test6(self) -> None:
        """
        Test with single node graph.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("Only")
        title = "Single Node"
        # Run test.
        hgraphv.plot_dag_with_graphviz(G, title)

    def test7(self) -> None:
        """
        Test with DPI parameter.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "High DPI"
        dpi = 300
        # Run test.
        hgraphv.plot_dag_with_graphviz(G, title, dpi=dpi)

    def test8(self) -> None:
        """
        Test with all parameters provided.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
        title = "Full Featured"
        node_colors = {"A": "#FF0000", "B": "#00FF00", "C": "#0000FF"}
        edge_colors = {
            ("A", "B"): "#FFFF00",
            ("B", "C"): "#FF00FF",
            ("A", "C"): "#00FFFF",
        }
        figsize = (14, 12)
        dpi = 200
        fig, ax = plt.subplots()
        # Run test.
        hgraphv.plot_dag_with_graphviz(
            G,
            title,
            node_colors=node_colors,
            edge_colors=edge_colors,
            ax=ax,
            figsize=figsize,
            dpi=dpi,
        )
        # Check outputs.
        self.assertIsNotNone(ax)
        plt.close(fig)


# #############################################################################
# Test_plot_dag_with_networkx_rounded_boxes
# #############################################################################


class Test_plot_dag_with_networkx_rounded_boxes(hunitest.TestCase):
    """
    Test the plot_dag_with_networkx_rounded_boxes function.
    """

    def test1(self) -> None:
        """
        Test basic DAG plotting with networkx rounded boxes.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        title = "NetworkX Rounded Boxes"
        # Run test and check no exception is raised.
        hgraphv.plot_dag_with_networkx_rounded_boxes(G, title)

    def test2(self) -> None:
        """
        Test with custom node colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Colored Boxes"
        node_colors = {"A": "#FF0000", "B": "#00FF00"}
        # Run test.
        hgraphv.plot_dag_with_networkx_rounded_boxes(
            G, title, node_colors=node_colors
        )

    def test3(self) -> None:
        """
        Test with custom edge colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Edge Colors"
        edge_colors = {("A", "B"): "#0000FF"}
        # Run test.
        hgraphv.plot_dag_with_networkx_rounded_boxes(
            G, title, edge_colors=edge_colors
        )

    def test4(self) -> None:
        """
        Test with matplotlib axes provided.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "With Axes"
        fig, ax = plt.subplots()
        # Run test.
        hgraphv.plot_dag_with_networkx_rounded_boxes(G, title, ax=ax)
        # Check outputs.
        self.assertIsNotNone(ax)
        plt.close(fig)

    def test5(self) -> None:
        """
        Test with single node.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("Single")
        title = "Single Node"
        # Run test.
        hgraphv.plot_dag_with_networkx_rounded_boxes(G, title)

    def test6(self) -> None:
        """
        Test with long node names to test box sizing.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("VeryLongNodeNameA", "VeryLongNodeNameB")
        title = "Long Names"
        # Run test.
        hgraphv.plot_dag_with_networkx_rounded_boxes(G, title)

    def test7(self) -> None:
        """
        Test without axes (should not crash).
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        title = "No Axes"
        # Run test.
        hgraphv.plot_dag_with_networkx_rounded_boxes(G, title, ax=None)

    def test8(self) -> None:
        """
        Test with all parameters.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
        title = "Full Parameters"
        node_colors = {"A": "#FF0000", "B": "#00FF00", "C": "#0000FF"}
        edge_colors = {
            ("A", "B"): "#FFFF00",
            ("B", "C"): "#FF00FF",
            ("A", "C"): "#00FFFF",
        }
        fig, ax = plt.subplots()
        # Run test.
        hgraphv.plot_dag_with_networkx_rounded_boxes(
            G,
            title,
            node_colors=node_colors,
            edge_colors=edge_colors,
            ax=ax,
        )
        # Check outputs.
        self.assertIsNotNone(ax)
        plt.close(fig)


# #############################################################################
# Test_plot_dag_with_networkx
# #############################################################################


class Test_plot_dag_with_networkx(hunitest.TestCase):
    """
    Test the plot_dag_with_networkx function.
    """

    def test1(self) -> None:
        """
        Test basic DAG plotting with networkx.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        pos = nx.spring_layout(G, seed=42)
        # Run test.
        hgraphv.plot_dag_with_networkx(G, pos)

    def test2(self) -> None:
        """
        Test with custom node color.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        pos = nx.spring_layout(G, seed=42)
        node_color = "#FF0000"
        # Run test.
        hgraphv.plot_dag_with_networkx(G, pos, node_color=node_color)

    def test3(self) -> None:
        """
        Test with custom edge color.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        pos = nx.spring_layout(G, seed=42)
        edge_color = "#0000FF"
        # Run test.
        hgraphv.plot_dag_with_networkx(G, pos, edge_color=edge_color)

    def test4(self) -> None:
        """
        Test with matplotlib axes provided.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        pos = nx.spring_layout(G, seed=42)
        fig, ax = plt.subplots()
        # Run test.
        hgraphv.plot_dag_with_networkx(G, pos, ax=ax)
        # Check outputs.
        self.assertIsNotNone(ax)
        plt.close(fig)

    def test5(self) -> None:
        """
        Test with single node.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("A")
        pos = {"A": (0, 0)}
        # Run test.
        hgraphv.plot_dag_with_networkx(G, pos)

    def test6(self) -> None:
        """
        Test with all parameters.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        pos = nx.spring_layout(G, seed=42)
        node_color = "#FF0000"
        edge_color = "#00FF00"
        fig, ax = plt.subplots()
        # Run test.
        hgraphv.plot_dag_with_networkx(
            G, pos, node_color=node_color, edge_color=edge_color, ax=ax
        )
        # Check outputs.
        self.assertIsNotNone(ax)
        plt.close(fig)


# #############################################################################
# Test_plot_causal_dag
# #############################################################################


class Test_plot_causal_dag(hunitest.TestCase):
    """
    Test the plot_causal_dag function.
    """

    def helper(
        self,
        mode: str,
        title: str,
        *,
        G: Optional[nx.DiGraph] = None,
        node_colors: Optional[Dict[str, str]] = None,
        edge_colors: Optional[Dict[Tuple[str, str], str]] = None,
        figsize: Optional[Tuple[int, int]] = None,
        dpi: int = hgraphv.FIG_DPI,
        pos: Optional[Dict[Any, Tuple[float, float]]] = None,
    ) -> None:
        """
        Test helper for plot_causal_dag.

        :param mode: Visualization mode
        :param title: Graph title
        :param G: Input directed acyclic graph (defaults to simple A->B)
        :param node_colors: Optional per-node fill colors
        :param edge_colors: Optional per-edge colors
        :param figsize: Optional figure size
        :param dpi: Resolution in dots per inch
        :param pos: Optional node position dictionary
        """
        if G is None:
            G = nx.DiGraph()
            G.add_edge("A", "B")
        # Run test.
        ax = hgraphv.plot_causal_dag(
            G,
            title,
            mode=mode,
            node_colors=node_colors,
            edge_colors=edge_colors,
            figsize=figsize,
            dpi=dpi,
            pos=pos,
        )
        # Check outputs.
        self.assertIsNotNone(ax)

    def test1(self) -> None:
        """
        Test graphviz mode.
        """
        # Prepare inputs.
        title = "Graphviz Mode"
        mode = "graphviz"
        # Run test.
        self.helper(mode, title)

    def test2(self) -> None:
        """
        Test networkx_rounded_boxes mode.
        """
        # Prepare inputs.
        title = "NetworkX Rounded Mode"
        mode = "networkx_rounded_boxes"
        # Run test.
        self.helper(mode, title)

    def test3(self) -> None:
        """
        Test networkx mode.
        """
        # Prepare inputs.
        title = "NetworkX Mode"
        mode = "networkx"
        # Run test.
        self.helper(mode, title)

    def test4(self) -> None:
        """
        Test with custom node colors.
        """
        # Prepare inputs.
        title = "With Node Colors"
        node_colors = {"A": "#FF0000", "B": "#00FF00"}
        mode = "graphviz"
        # Run test.
        self.helper(mode, title, node_colors=node_colors)

    def test5(self) -> None:
        """
        Test with custom edge colors.
        """
        # Prepare inputs.
        title = "With Edge Colors"
        edge_colors = {("A", "B"): "#0000FF"}
        mode = "graphviz"
        # Run test.
        self.helper(mode, title, edge_colors=edge_colors)

    def test6(self) -> None:
        """
        Test with custom figsize.
        """
        # Prepare inputs.
        title = "With Figsize"
        figsize = (12, 10)
        mode = "graphviz"
        # Run test.
        self.helper(mode, title, figsize=figsize)

    def test7(self) -> None:
        """
        Test with provided axes.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "With Axes"
        fig, ax = plt.subplots()
        mode = "graphviz"
        # Run test.
        ax_result = hgraphv.plot_causal_dag(G, title, mode=mode, ax=ax)
        # Check outputs.
        self.assertIsNotNone(ax_result)
        plt.close(fig)

    def test8(self) -> None:
        """
        Test with custom DPI.
        """
        # Prepare inputs.
        title = "With DPI"
        dpi = 300
        mode = "graphviz"
        # Run test.
        self.helper(mode, title, dpi=dpi)

    def test9(self) -> None:
        """
        Test with pos parameter (for networkx mode).
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        title = "With Pos"
        pos = nx.spring_layout(G, seed=42)
        mode = "networkx"
        # Run test.
        ax = hgraphv.plot_causal_dag(G, title, mode=mode, pos=pos)
        # Check outputs.
        self.assertIsNotNone(ax)

    def test10(self) -> None:
        """
        Test invalid mode raises assertion error.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Invalid Mode"
        mode = "invalid_mode"
        # Run test and check exception.
        with self.assertRaises(AssertionError):
            hgraphv.plot_causal_dag(G, title, mode=mode)

    def test11(self) -> None:
        """
        Test complex graph with all modes.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
        title = "Complex DAG"
        node_colors = {"A": "#FF0000", "B": "#00FF00", "C": "#0000FF"}
        edge_colors = {
            ("A", "B"): "#FFFF00",
            ("B", "C"): "#FF00FF",
            ("A", "C"): "#00FFFF",
        }
        # Run test with graphviz mode.
        ax1 = hgraphv.plot_causal_dag(
            G,
            title,
            mode="graphviz",
            node_colors=node_colors,
            edge_colors=edge_colors,
        )
        # Check outputs.
        self.assertIsNotNone(ax1)

    def test12(self) -> None:
        """
        Test networkx mode returns axes with title.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "NetworkX Title Test"
        mode = "networkx"
        # Run test.
        ax = hgraphv.plot_causal_dag(G, title, mode=mode)
        # Check outputs.
        self.assertIsNotNone(ax)
        if ax is not None:
            self.assertEqual(ax.get_title(), title)

    def test13(self) -> None:
        """
        Test single node with different modes.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("OnlyNode")
        title = "Single Node"
        # Run test with graphviz mode.
        ax1 = hgraphv.plot_causal_dag(G, title, mode="graphviz")
        self.assertIsNotNone(ax1)
        # Run test with networkx_rounded_boxes mode.
        ax2 = hgraphv.plot_causal_dag(G, title, mode="networkx_rounded_boxes")
        self.assertIsNotNone(ax2)
        # Run test with networkx mode.
        ax3 = hgraphv.plot_causal_dag(G, title, mode="networkx")
        self.assertIsNotNone(ax3)


# #############################################################################
# Test_graphviz_image_properties
# #############################################################################


class Test_graphviz_image_properties(hunitest.TestCase):
    """
    Test that DPI and figsize are correctly applied to rendered images.
    """

    def _get_image_from_graph(
        self,
        G: nx.DiGraph,
        title: str,
        figsize: Optional[Tuple[int, int]] = None,
        dpi: int = hgraphv.FIG_DPI,
    ) -> Image.Image:
        """
        Helper to render a graph and extract the image.

        :param G: Input directed acyclic graph
        :param title: Graph title
        :param figsize: Optional figure size
        :param dpi: Dots per inch for rendering
        :return: PIL Image object
        """
        # Create a temporary figure and axis
        if figsize is None:
            figsize = hgraphv.FIG_SIZE
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        # Render the graph
        hgraphv.plot_dag_with_graphviz(
            G, title, ax=ax, figsize=figsize, dpi=dpi
        )
        # Save to bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi)
        buf.seek(0)
        # Load and return the image
        img = Image.open(buf)
        img.load()
        plt.close(fig)
        return img

    def test_default_dpi(self) -> None:
        """
        Test that default DPI (150) is applied to the image.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Default DPI"
        # Get image.
        img = self._get_image_from_graph(G, title)
        # Check DPI.
        # PIL returns DPI as a tuple (x_dpi, y_dpi)
        img_dpi = img.info.get("dpi", (hgraphv.FIG_DPI, hgraphv.FIG_DPI))
        self.assertIsNotNone(img_dpi)
        # DPI should be close to the default (150)
        self.assertGreater(img_dpi[0], 100)
        self.assertLess(img_dpi[0], 200)

    def test_high_dpi_200(self) -> None:
        """
        Test that DPI of 200 is applied to the image.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "High DPI 200"
        dpi = 200
        # Get image.
        img = self._get_image_from_graph(G, title, dpi=dpi)
        # Check DPI.
        img_dpi = img.info.get("dpi", (dpi, dpi))
        self.assertIsNotNone(img_dpi)
        # DPI should be close to 200
        self.assertGreater(img_dpi[0], 180)
        self.assertLess(img_dpi[0], 220)

    def test_high_dpi_300(self) -> None:
        """
        Test that DPI of 300 is applied to the image.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "High DPI 300"
        dpi = 300
        # Get image.
        img = self._get_image_from_graph(G, title, dpi=dpi)
        # Check DPI.
        img_dpi = img.info.get("dpi", (dpi, dpi))
        self.assertIsNotNone(img_dpi)
        # DPI should be close to 300
        self.assertGreater(img_dpi[0], 280)
        self.assertLess(img_dpi[0], 320)

    def test_low_dpi_100(self) -> None:
        """
        Test that DPI of 100 is applied to the image.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Low DPI 100"
        dpi = 100
        # Get image.
        img = self._get_image_from_graph(G, title, dpi=dpi)
        # Check DPI.
        img_dpi = img.info.get("dpi", (dpi, dpi))
        self.assertIsNotNone(img_dpi)
        # DPI should be close to 100
        self.assertGreater(img_dpi[0], 80)
        self.assertLess(img_dpi[0], 120)

    def test_figsize_small(self) -> None:
        """
        Test that small figsize (8, 6) is applied correctly.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Small Size"
        figsize = (8, 6)
        dpi = 100
        # Get image.
        img = self._get_image_from_graph(G, title, figsize=figsize, dpi=dpi)
        # Check image dimensions.
        # Expected: width = 8 inches * 100 dpi = 800 pixels (approximate)
        # Expected: height = 6 inches * 100 dpi = 600 pixels (approximate)
        width, height = img.size
        expected_width = figsize[0] * dpi
        expected_height = figsize[1] * dpi
        # Allow 10% tolerance due to padding/borders
        self.assertGreater(width, expected_width * 0.9)
        self.assertLess(width, expected_width * 1.1)
        self.assertGreater(height, expected_height * 0.9)
        self.assertLess(height, expected_height * 1.1)

    def test_figsize_large(self) -> None:
        """
        Test that large figsize (14, 10) is applied correctly.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Large Size"
        figsize = (14, 10)
        dpi = 100
        # Get image.
        img = self._get_image_from_graph(G, title, figsize=figsize, dpi=dpi)
        # Check image dimensions.
        # Expected: width = 14 inches * 100 dpi = 1400 pixels (approximate)
        # Expected: height = 10 inches * 100 dpi = 1000 pixels (approximate)
        width, height = img.size
        expected_width = figsize[0] * dpi
        expected_height = figsize[1] * dpi
        # Allow 10% tolerance due to padding/borders
        self.assertGreater(width, expected_width * 0.9)
        self.assertLess(width, expected_width * 1.1)
        self.assertGreater(height, expected_height * 0.9)
        self.assertLess(height, expected_height * 1.1)

    def test_figsize_and_dpi_combination(self) -> None:
        """
        Test that both figsize and DPI work correctly together.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        title = "Combined Parameters"
        figsize = (12, 8)
        dpi = 150
        # Get image.
        img = self._get_image_from_graph(G, title, figsize=figsize, dpi=dpi)
        # Check DPI.
        img_dpi = img.info.get("dpi", (dpi, dpi))
        self.assertGreater(img_dpi[0], 130)
        self.assertLess(img_dpi[0], 170)
        # Check image dimensions.
        width, height = img.size
        expected_width = figsize[0] * dpi
        expected_height = figsize[1] * dpi
        self.assertGreater(width, expected_width * 0.9)
        self.assertLess(width, expected_width * 1.1)
        self.assertGreater(height, expected_height * 0.9)
        self.assertLess(height, expected_height * 1.1)

    def test_dpi_affects_image_size(self) -> None:
        """
        Test that higher DPI produces larger pixel dimensions for same figsize.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "DPI Comparison"
        figsize = (10, 8)
        # Get images with different DPI values.
        img_150 = self._get_image_from_graph(G, title, figsize=figsize, dpi=150)
        img_300 = self._get_image_from_graph(G, title, figsize=figsize, dpi=300)
        # Check that higher DPI produces larger image.
        size_150 = img_150.size[0] * img_150.size[1]
        size_300 = img_300.size[0] * img_300.size[1]
        # 300 DPI image should be roughly 4x the pixel area (2x in each dimension)
        ratio = size_300 / size_150
        self.assertGreater(ratio, 3.5)
        self.assertLess(ratio, 4.5)

    def test_figsize_consistency(self) -> None:
        """
        Test that different DPI values with same figsize maintain aspect ratio.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Aspect Ratio"
        figsize = (12, 8)
        # Get images with different DPI values.
        img_100 = self._get_image_from_graph(G, title, figsize=figsize, dpi=100)
        img_200 = self._get_image_from_graph(G, title, figsize=figsize, dpi=200)
        # Check aspect ratios are the same.
        aspect_100 = img_100.size[0] / img_100.size[1]
        aspect_200 = img_200.size[0] / img_200.size[1]
        expected_aspect = figsize[0] / figsize[1]
        # All should be close to the expected aspect ratio
        self.assertAlmostEqual(aspect_100, expected_aspect, places=1)
        self.assertAlmostEqual(aspect_200, expected_aspect, places=1)
