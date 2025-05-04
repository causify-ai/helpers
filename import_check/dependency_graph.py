# Standard library imports
import ast
import logging
from pathlib import Path
from typing import Union

# Third-party imports
import networkx as nx
from networkx.drawing.nx_pydot import write_dot

_LOG = logging.getLogger(__name__)


# #############################################################################
# DependencyGraph
# #############################################################################


class DependencyGraph:
    """
    Generate a dependency graph for intra-directory imports.

    Args:
        directory (str): Path to the directory to analyze.
        max_level (int, optional): Max directory depth to analyze (default: None).
        show_cycles (bool, optional): Show only cyclic dependencies (default: False).

    Attributes:
        directory (Path): Resolved directory path.
        graph (nx.DiGraph): Directed graph of dependencies.
        max_level (int, optional): Max directory depth to analyze.
        show_cycles (bool): Whether to show only cyclic dependencies.
    """

    def __init__(
        self,
        directory: str,
        max_level: Union[int, None] = None,
        show_cycles: bool = False,
    ):
        self.directory = Path(directory).resolve()
        self.graph = nx.DiGraph()
        self.max_level = max_level
        self.show_cycles = show_cycles

    def build_graph(self) -> None:
        """
        Build a directed graph of intra-directory dependencies.

        Returns:
            None

        Raises:
            SyntaxError: Skipped with a warning if a Python file has a syntax error.
        """
        _LOG.info(f"Building dependency graph for {self.directory}")
        # Calculate the base depth of the directory
        base_depth = len(self.directory.parts)
        # Find Python files up to max_level
        py_files = [
            path
            for path in self.directory.rglob("*.py")
            if self.max_level is None
            or (len(path.parent.parts) - base_depth) <= self.max_level
        ]
        _LOG.info(f"Found Python files: {py_files}")
        for py_file in py_files:
            relative_path = py_file.relative_to(self.directory.parent).as_posix()
            _LOG.info(
                f"Processing file {py_file}, relative path: {relative_path}"
            )
            self.graph.add_node(relative_path)
            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
            except SyntaxError as e:
                _LOG.warning(f"Skipping {py_file} due to syntax error: {e}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Extract import names based on node type
                    imports = (
                        [name.name for name in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module]
                    )
                    for imp in imports:
                        _LOG.info(f"Found import: {imp}")
                        imp_path = self._resolve_import(imp, py_file)
                        if imp_path:
                            _LOG.info(
                                f"Adding edge: {relative_path} -> {imp_path}"
                            )
                            self.graph.add_edge(relative_path, imp_path)
                        else:
                            _LOG.info(f"No edge added for import {imp}")
        # Filter for cyclic dependencies if show_cycles is True
        if self.show_cycles:
            self._filter_cycles()

    def get_text_report(self) -> str:
        """
        Generate a text report listing each module's dependencies.

        Returns:
            str: Text report of dependencies, one per line.
        """
        report = []
        for node in self.graph.nodes:
            dependencies = list(self.graph.successors(node))
            line = (
                f"{node} imports {', '.join(dependencies)}"
                if dependencies
                else f"{node} has no dependencies"
            )
            report.append(line)
        return "\n".join(report)

    def get_dot_file(self, output_file: str) -> None:
        """
        Write the dependency graph to a DOT file.

        Args:
            output_file (str): Path to the output DOT file.

        Returns:
            None
        """
        write_dot(self.graph, output_file)
        _LOG.info(f"DOT file written to {output_file}")

    def _filter_cycles(self) -> None:
        """
        Filter the graph to show only nodes and edges in cyclic dependencies.

        Returns:
            None
        """
        # Find strongly connected components (cycles)
        cycles = list(nx.strongly_connected_components(self.graph))
        # Keep only components with more than one node (i.e., cycles)
        cyclic_nodes = set()
        for component in cycles:
            if len(component) > 1:
                cyclic_nodes.update(component)
        # Create a new graph with only cyclic nodes and their edges
        new_graph = nx.DiGraph()
        for node in cyclic_nodes:
            new_graph.add_node(node)
        for u, v in self.graph.edges():
            if u in cyclic_nodes and v in cyclic_nodes:
                new_graph.add_edge(u, v)
        self.graph = new_graph
        _LOG.info(
            f"Graph filtered to {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges in cycles"
        )

    def _resolve_import(self, imp: str, py_file: Path) -> str:
        """
        Resolve an import to a file path within the directory.

        Args:
            imp (str): Import statement (e.g., "module.submodule").
            py_file (Path): File path where the import is found.

        Returns:
            str: Relative path to the resolved file, or None if unresolved.
        """
        _LOG.info(f"Resolving import '{imp}' for file {py_file}")
        base_dir = self.directory
        _LOG.info(f"Base directory: {base_dir}")
        parts = imp.split(".")
        current_dir = base_dir
        dir_name = self.directory.name  # for example, "helpers"
        # Handle imports starting with the directory name
        if parts[0] == dir_name:
            # Skip the first part dir,  solve for next
            parts = parts[1:]
            if not parts:
                # Only if the dir name is given (e.g., "helpers"), check for __init__.py
                init_path = base_dir / "__init__.py"
                if init_path.exists():
                    resolved_path = init_path.relative_to(
                        self.directory.parent
                    ).as_posix()
                    _LOG.info(f"Resolved to: {resolved_path}")
                    return resolved_path
                _LOG.info(f"Could not resolve import '{imp}' (directory only)")
                return None
        for i, module_name in enumerate(parts):
            # Check for package with __init__.py
            package_path = current_dir / module_name / "__init__.py"
            _LOG.info(f"Checking package path: {package_path}")
            if package_path.exists():
                # If last part, return the __init__.py path
                if i == len(parts) - 1:
                    resolved_path = package_path.relative_to(
                        self.directory.parent
                    ).as_posix()
                    _LOG.info(f"Resolved to: {resolved_path}")
                    return resolved_path
                # else, continue to the next part
                current_dir = current_dir / module_name
                continue
            # Check for a .py file
            module_path = current_dir / f"{module_name}.py"
            _LOG.info(f"Checking module path: {module_path}")
            if module_path.exists():
                # If last part, return the .py path
                if i == len(parts) - 1:
                    resolved_path = module_path.relative_to(
                        self.directory.parent
                    ).as_posix()
                    _LOG.info(f"Resolved to: {resolved_path}")
                    return resolved_path
                # If notlast part, but is a module, it can't lead further
                _LOG.info(
                    f"Could not resolve full import '{imp}' beyond {module_path}"
                )
                return None
            # If neither exists, the import cannot be resolved
            _LOG.info(f"Could not resolve import '{imp}' at part '{module_name}'")
            return None
        _LOG.info(f"Could not resolve import '{imp}'")
        return None
