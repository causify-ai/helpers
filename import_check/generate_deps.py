import networkx as nx
from import_check.dependency_graph import DependencyGraph

# Generate dependency graph for the helpers directory
graph = DependencyGraph("helpers")
graph.build_graph()

# Print the text report of dependencies - uncomment if needed to see the text report of dependencies (alt to i show deps)
# print("Text Report:")
# print(graph.get_text_report())

# Convert to a NetworkX graph for customization
nx_graph = graph.graph

# Filter out nodes with no dependencies (in-degree and out-degree both 0)
nodes_to_remove = [
    node
    for node in nx_graph.nodes
    if nx_graph.in_degree(node) == 0 and nx_graph.out_degree(node) == 0
]
nx_graph.remove_nodes_from(nodes_to_remove)
print(f"Removed {len(nodes_to_remove)} nodes with no dependencies")

# Shorten node labels by removing the "helpers/" prefix
for node in nx_graph.nodes:
    new_label = node.replace("helpers/", "")
    nx_graph.nodes[node]["label"] = new_label

# Add Graphviz attributes for better layout
nx_graph.graph["graph"] = {
    "ranksep": "2.0",  # Increase spacing between ranks
    "nodesep": "1.0",  # Increase spacing between nodes
    "splines": "spline",  # Use smooth curves for edges
    "overlap": "false",  # Avoid overlapping nodes
    "fontsize": "10",  # Smaller font size for labels
}

# Write the DOT file with the customized graph
nx.drawing.nx_pydot.write_dot(nx_graph, "dependency_graph.dot")
print("Dependency graph written to dependency_graph.dot")
