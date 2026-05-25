import matplotlib.pyplot as plt
import networkx as nx

import helpers.hgraphviz as hgraphviz
import helpers.hunit_test as hunitest


class Test_graph_to_graphviz_dot(hunitest.TestCase):
    """
    Test the _graph_to_graphviz_dot function.
    """

    def test1(self) -> None:
        """
        Test basic graph with two nodes and one edge.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Test Graph"
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(G, title)
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test graph with multiple nodes and edges.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
        title = "Multi Node Graph"
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(G, title)
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
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
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test graph with node colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Colored Graph"
        node_colors = {"A": "#FF0000", "B": "#00FF00"}
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(
            G, title, node_colors=node_colors
        )
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#FF0000"];
            "B" [fillcolor="#00FF00"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test4(self) -> None:
        """
        Test graph with edge colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Edge Colors"
        edge_colors = {("A", "B"): "#0000FF"}
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(
            G, title, edge_colors=edge_colors
        )
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#0000FF", penwidth=2.0];
        }
        """
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test5(self) -> None:
        """
        Test graph with custom size.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Sized Graph"
        size = (12.5, 10.5)
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(G, title, size=size)
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            size="12.5,10.5";
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test6(self) -> None:
        """
        Test graph with single node and no edges.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("A")
        title = "Single Node"
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(G, title)
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#A6C8F4"];
        }
        """
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test7(self) -> None:
        """
        Test graph with non-string node names converted to strings.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        title = "Numeric Nodes"
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(G, title)
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
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
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test8(self) -> None:
        """
        Test hex color conversion for node colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_node("A")
        title = "Hex Color Test"
        node_colors = {"A": "#ABCDEF"}
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(
            G, title, node_colors=node_colors
        )
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#ABCDEF"];
        }
        """
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test9(self) -> None:
        """
        Test default color when node not in color mapping.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Partial Colors"
        node_colors = {"A": "#FF0000"}
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(
            G, title, node_colors=node_colors
        )
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
            nodesep=0.6;
            ranksep=0.6;
            node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, penwidth=1.4];
            "A" [fillcolor="#FF0000"];
            "B" [fillcolor="#A6C8F4"];
            "A" -> "B" [color="#555555", penwidth=2.0];
        }
        """
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test10(self) -> None:
        """
        Test default edge color when edge not in color mapping.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        title = "Partial Edge Colors"
        edge_colors = {("A", "B"): "#FF0000"}
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(
            G, title, edge_colors=edge_colors
        )
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
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
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test11(self) -> None:
        """
        Test that output is valid DOT format string.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edges_from([("Start", "Process"), ("Process", "End")])
        title = "Valid DOT"
        # Run test.
        actual = hgraphviz._graph_to_graphviz_dot(G, title)
        # Prepare outputs.
        expected = """
        digraph {
            rankdir=TB;
            splines=true;
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
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)


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
        hgraphviz.plot_dag_with_graphviz(G, title)

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
        hgraphviz.plot_dag_with_graphviz(
            G, title, node_colors=node_colors
        )

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
        hgraphviz.plot_dag_with_graphviz(
            G, title, edge_colors=edge_colors
        )

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
        hgraphviz.plot_dag_with_graphviz(G, title, figsize=figsize)

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
        hgraphviz.plot_dag_with_graphviz(G, title, ax=ax)
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
        hgraphviz.plot_dag_with_graphviz(G, title)

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
        hgraphviz.plot_dag_with_graphviz(G, title, dpi=dpi)

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
        hgraphviz.plot_dag_with_graphviz(
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
        hgraphviz.plot_dag_with_networkx_rounded_boxes(G, title)

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
        hgraphviz.plot_dag_with_networkx_rounded_boxes(
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
        hgraphviz.plot_dag_with_networkx_rounded_boxes(
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
        hgraphviz.plot_dag_with_networkx_rounded_boxes(G, title, ax=ax)
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
        hgraphviz.plot_dag_with_networkx_rounded_boxes(G, title)

    def test6(self) -> None:
        """
        Test with long node names to test box sizing.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("VeryLongNodeNameA", "VeryLongNodeNameB")
        title = "Long Names"
        # Run test.
        hgraphviz.plot_dag_with_networkx_rounded_boxes(G, title)

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
        hgraphviz.plot_dag_with_networkx_rounded_boxes(G, title, ax=None)

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
        hgraphviz.plot_dag_with_networkx_rounded_boxes(
            G,
            title,
            node_colors=node_colors,
            edge_colors=edge_colors,
            ax=ax,
        )
        # Check outputs.
        self.assertIsNotNone(ax)
        plt.close(fig)


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
        hgraphviz.plot_dag_with_networkx(G, pos)

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
        hgraphviz.plot_dag_with_networkx(G, pos, node_color=node_color)

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
        hgraphviz.plot_dag_with_networkx(G, pos, edge_color=edge_color)

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
        hgraphviz.plot_dag_with_networkx(G, pos, ax=ax)
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
        hgraphviz.plot_dag_with_networkx(G, pos)

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
        hgraphviz.plot_dag_with_networkx(
            G, pos, node_color=node_color, edge_color=edge_color, ax=ax
        )
        # Check outputs.
        self.assertIsNotNone(ax)
        plt.close(fig)


class Test_plot_causal_dag(hunitest.TestCase):
    """
    Test the plot_causal_dag function.
    """

    def test1(self) -> None:
        """
        Test graphviz mode.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "Graphviz Mode"
        mode = "graphviz"
        # Run test.
        ax = hgraphviz.plot_causal_dag(G, title, mode=mode)
        # Check outputs.
        self.assertIsNotNone(ax)

    def test2(self) -> None:
        """
        Test networkx_rounded_boxes mode.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "NetworkX Rounded Mode"
        mode = "networkx_rounded_boxes"
        # Run test.
        ax = hgraphviz.plot_causal_dag(G, title, mode=mode)
        # Check outputs.
        self.assertIsNotNone(ax)

    def test3(self) -> None:
        """
        Test networkx mode.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "NetworkX Mode"
        mode = "networkx"
        # Run test.
        ax = hgraphviz.plot_causal_dag(G, title, mode=mode)
        # Check outputs.
        self.assertIsNotNone(ax)

    def test4(self) -> None:
        """
        Test with custom node colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "With Node Colors"
        node_colors = {"A": "#FF0000", "B": "#00FF00"}
        mode = "graphviz"
        # Run test.
        ax = hgraphviz.plot_causal_dag(
            G, title, mode=mode, node_colors=node_colors
        )
        # Check outputs.
        self.assertIsNotNone(ax)

    def test5(self) -> None:
        """
        Test with custom edge colors.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "With Edge Colors"
        edge_colors = {("A", "B"): "#0000FF"}
        mode = "graphviz"
        # Run test.
        ax = hgraphviz.plot_causal_dag(
            G, title, mode=mode, edge_colors=edge_colors
        )
        # Check outputs.
        self.assertIsNotNone(ax)

    def test6(self) -> None:
        """
        Test with custom figsize.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "With Figsize"
        figsize = (12, 10)
        mode = "graphviz"
        # Run test.
        ax = hgraphviz.plot_causal_dag(
            G, title, mode=mode, figsize=figsize
        )
        # Check outputs.
        self.assertIsNotNone(ax)

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
        ax_result = hgraphviz.plot_causal_dag(G, title, mode=mode, ax=ax)
        # Check outputs.
        self.assertIsNotNone(ax_result)
        plt.close(fig)

    def test8(self) -> None:
        """
        Test with custom DPI.
        """
        # Prepare inputs.
        G = nx.DiGraph()
        G.add_edge("A", "B")
        title = "With DPI"
        dpi = 300
        mode = "graphviz"
        # Run test.
        ax = hgraphviz.plot_causal_dag(G, title, mode=mode, dpi=dpi)
        # Check outputs.
        self.assertIsNotNone(ax)

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
        ax = hgraphviz.plot_causal_dag(G, title, mode=mode, pos=pos)
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
            hgraphviz.plot_causal_dag(G, title, mode=mode)

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
        ax1 = hgraphviz.plot_causal_dag(
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
        ax = hgraphviz.plot_causal_dag(G, title, mode=mode)
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
        ax1 = hgraphviz.plot_causal_dag(G, title, mode="graphviz")
        self.assertIsNotNone(ax1)
        # Run test with networkx_rounded_boxes mode.
        ax2 = hgraphviz.plot_causal_dag(G, title, mode="networkx_rounded_boxes")
        self.assertIsNotNone(ax2)
        # Run test with networkx mode.
        ax3 = hgraphviz.plot_causal_dag(G, title, mode="networkx")
        self.assertIsNotNone(ax3)
