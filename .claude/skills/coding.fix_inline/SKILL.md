---
description: Find and remove the functions that are too thin
model: haiku
---

- I will pass you one of more files `<FILES>`

- Look for functions that are too "thin", i.e., that call another function
  directly without doing much else
  - E.g.,
		```
		def cell1_plot_dag(
				G: nx.DiGraph,
				title: str,
				*,
				node_colors: Optional[Mapping[str, Any]] = None,
				edge_colors: Optional[Mapping[Tuple[str, str], Any]] = None,
				ax: Optional[maxes.Axes] = None,
				figsize: Optional[Tuple[int, int]] = None,
				pos: Optional[Dict] = None,
				dpi: int = hgraphviz.FIG_DPI,
		) -> maxes.Axes:
				return hgraphviz.plot_causal_dag(
						G,
						title,
						mode="graphviz",
						node_colors=node_colors,
						edge_colors=edge_colors,
						ax=ax,
						figsize=figsize,
						dpi=dpi,
				)
		```

- Ask to the user if it's ok to remove them

- Remove the functions and then look for all the invocations of the removed
	function and inline the called function

- Read and apply to `<FILES>` the rules from `.claude/skills/coding.rules.md`
