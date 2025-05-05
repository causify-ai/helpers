import ast
import logging
from pathlib import Path
from typing import Union

import networkx as nx

_LOG = logging.getLogger(__name__)

# #############################################################################
# DependencyGraph
# #############################################################################

class DependencyGraph:
    """
    Generate a dependency graph for intra-directory imports.

    :param directory: Path to the directory to analyze.
    :param max_level: Max directory depth to analyze.
    :param show_cycles: Show only cyclic dependencies.
    """

    def __init__(
        self,
        directory: str,
        *,
        # TODO: Use -1 instead of None to simplify typing.
        max_level: Union[int, None] = None,
        show_cycles: bool = False,
    ) -> None:
        # Initialize basic attributes.
        self.directory = Path(directory).resolve()
        _LOG.debug(hprint.to_str("self.directory"))
        # Create a directed graph of dependencies.
        self.graph: nx.DiGraph = nx.DiGraph()
        self.max_level = max_level
        _LOG.debug(hprint.to_str("self.max_level"))
        # Determine whether to show only cyclic dependencies.
        self.show_cycles = show_cycles
        _LOG.debug(hprint.to_str("self.show_cycles"))

    def build_graph(self) -> None:
        """
        Build a directed graph of intra-directory dependencies.
        """
        _LOG.debug(hprint.func_signature_to_str())
        _LOG.info("Building dependency graph for %s", self.directory)
        # Calculate the base depth of the directory.
        base_depth = len(self.directory.parts)
        _LOG.debug(hprint.to_str("base_depth"))
        # Find Python files up to `max_level`.
        py_files = [
            path
            for path in self.directory.rglob("*.py")
            if self.max_level is None
            or (len(path.parent.parts) - base_depth) <= self.max_level
        ]
        _LOG.info("Found Python files: %s", py_files)
        _LOG.debug(hprint.to_str("py_files"))
        # Process each Python file to build the dependency graph.
        for py_file in py_files:
            relative_path = py_file.relative_to(self.directory.parent).as_posix()
            _LOG.info(
                "Processing file %s, relative path: %s", py_file, relative_path
            )
            _LOG.debug(hprint.to_str("relative_path"))
            self.graph.add_node(relative_path)
            # Attempt to parse the file as an Abstract Syntax Tree (AST).
            # TODO: Use hio.from_file and to_file to write.
            # TODO: Let's add a switch `abort_on_error` to continue or abort.
            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
            except SyntaxError as e:
                _LOG.warning("Skipping %s due to syntax error: %s", py_file, e)
                continue
            # Walk through the AST and parse import statements.
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Extract import names based on `node` type.
                    imports = (
                        [name.name for name in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module]
                    )
                    _LOG.debug(hprint.to_str("imports"))
                    # Add edges for each import found.
                    for imp in imports:
                        _LOG.info("Found import: %s", imp)
                        _LOG.debug(hprint.to_str("imp"))
                        imp_path = self._resolve_import(imp, py_file)
                        if imp_path:
                            _LOG.info(
                                "Adding edge: %s -> %s", relative_path, imp_path
                            )
                            self.graph.add_edge(relative_path, imp_path)
                            _LOG.debug(hprint.to_str("self.graph"))
                        else:
                            _LOG.info("No edge added for import %s", imp)
        # Filter for cyclic dependencies if `show_cycles` is `True`.
        if self.show_cycles:
            self._filter_cycles()

    def get_text_report(self) -> str:
        """
        Generate a text report listing each module's dependencies.

        :return: Text report of dependencies, one per line.
        """
        _LOG.debug(hprint.func_signature_to_str())
        # Accumulate report lines.
        report = []
        # Iterate over all nodes to report their dependencies.
        for node in self.graph.nodes:
            _LOG.debug(hprint.to_str("node"))
            dependencies = list(self.graph.successors(node))
            _LOG.debug(hprint.to_str("dependencies"))
            # Conditional report creation depending on dependencies presence.
            # TODO: Let's use a if-then-else for clarity.
            line = (
                f"{node} imports {', '.join(dependencies)}"
                if dependencies
                else f"{node} has no dependencies"
            )
            _LOG.debug(hprint.to_str("line"))
            report.append(line)
        # Join all lines into a single string separated by newline.
        return "\n".join(report)

    def get_dot_file(self, output_file: str) -> None:
        """
        Write the dependency graph to a DOT file.

        :param output_file: Path to the output DOT file.
        """
        _LOG.debug(hprint.func_signature_to_str())
        # Write the graph to a DOT file.
        networkx.drawing.nx_pydot.write_dot(self.graph, output_file)
        _LOG.info("DOT file written to %s", output_file)

    def _filter_cycles(self) -> None:
        """
        Filter the graph to show only nodes and edges in cyclic dependencies.
        """
        _LOG.debug(hprint.func_signature_to_str())
        # Find all strongly connected components in the graph.
        cycles = list(nx.strongly_connected_components(self.graph))
        _LOG.debug(hprint.to_str("cycles"))
        # Accumulate cyclic nodes.
        cyclic_nodes = set()
        # Keep only components with more than one node (i.e., cycles).
        for component in cycles:
            if len(component) > 1:
                cyclic_nodes.update(component)
        _LOG.debug(hprint.to_str("cyclic_nodes"))
        # Create a new graph with only cyclic nodes and their edges.
        new_graph = nx.DiGraph()
        for node in cyclic_nodes:
            new_graph.add_node(node)
        for u, v in self.graph.edges():
            if u in cyclic_nodes and v in cyclic_nodes:
                new_graph.add_edge(u, v)
        # Replace the original graph with a new graph containing only cyclic edges.
        self.graph = new_graph
        # Log a summary of the cyclic graph result.
        _LOG.info(
            "Graph filtered to %d nodes and %d edges in cycles",
            len(self.graph.nodes),
            len(self.graph.edges),
        )

    # TODO: -> Optional[str]
    def _resolve_import(self, imp: str, py_file: Path) -> str:
        """
        Resolve an import to a file path within the directory.

        :param imp: Import statement (e.g., `module.submodule`).
        :param py_file: File path where the import is found.
        :return: Relative path to the resolved file, or None if
            unresolved.
        """
        _LOG.debug(hprint.func_signature_to_str())
        _LOG.info("Resolving import '%s' for file %s", imp, py_file)
        _LOG.debug(hprint.to_str("imp, py_file"))
        # Define base directory and other parameters for module resolution.
        base_dir = self.directory
        _LOG.info("Base directory: %s", base_dir)
        parts = imp.split(".")
        _LOG.debug(hprint.to_str("parts"))
        current_dir = base_dir
        _LOG.debug(hprint.to_str("current_dir"))
        # E.g., "helpers".
        dir_name = self.directory.name
        _LOG.debug(hprint.to_str("dir_name"))
        # Handle imports starting with the directory name.
        if parts[0] == dir_name:
            # Skip the first part `dir`, solve for next.
            parts = parts[1:]
            _LOG.debug(hprint.to_str("parts after dir_name handling"))
            if not parts:
                # Only if the `dir` name is given (e.g., "helpers"), check for
                # `__init__.py`.
                init_path = base_dir / "__init__.py"
                _LOG.debug(hprint.to_str("init_path"))
                if init_path.exists():
                    resolved_path = init_path.relative_to(
                        self.directory.parent
                    ).as_posix()
                    _LOG.info("Resolved to: %s", resolved_path)
                    return resolved_path
                _LOG.info("Could not resolve import '%s' (directory only)", imp)
                return None
        # Iterate over each module name in resolved path.
        for i, module_name in enumerate(parts):
            _LOG.debug(hprint.to_str("i, module_name"))
            # Check for package with `__init__.py`.
            package_path = current_dir / module_name / "__init__.py"
            _LOG.info("Checking package path: %s", package_path)
            _LOG.debug(hprint.to_str("package_path"))
            if package_path.exists():
                # If last part, return the `__init__.py` path.
                if i == len(parts) - 1:
                    resolved_path = package_path.relative_to(
                        self.directory.parent
                    ).as_posix()
                    _LOG.info("Resolved to: %s", resolved_path)
                    return resolved_path
                # Otherwise, continue to the next part.
                current_dir = current_dir / module_name
                _LOG.debug(hprint.to_str("current_dir"))
                continue
            # Check for a `.py` file.
            module_path = current_dir / f"{module_name}.py"
            _LOG.info("Checking module path: %s", module_path)
            _LOG.debug(hprint.to_str("module_path"))
            if module_path.exists():
                # If last part, return the `.py` path.
                if i == len(parts) - 1:
                    resolved_path = module_path.relative_to(
                        self.directory.parent
                    ).as_posix()
                    _LOG.info("Resolved to: %s", resolved_path)
                    return resolved_path
                # If not last part, but is a module, it can't lead further.
                _LOG.info(
                    "Could not resolve full import '%s' beyond %s",
                    imp,
                    module_path,
                )
                return None
            # If neither exists, the import cannot be resolved.
            _LOG.info(
                "Could not resolve import '%s' at part '%s'", imp, module_name
            )
            return None
        # Return None if module resolution was unsuccessful.
        _LOG.info("Could not resolve import '%s'", imp)
        return None