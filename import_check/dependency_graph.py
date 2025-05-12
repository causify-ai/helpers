"""
Import as:

import import_check.dependency_graph as ichdegra
"""

import ast
import logging
from pathlib import Path
from typing import Optional

import networkx as nx

import helpers.hio as hio
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# #############################################################################
# DependencyGraph
# #############################################################################


class DependencyGraph:
    """
    Generate a dependency graph for intra-directory imports.

    :param directory: Path to the directory to analyze.
    :param max_level: Max directory depth to analyze (-1 for no limit).
    :param show_cycles: If True, include only cyclic dependencies in the
        graph.
    """

    def __init__(
        self,
        directory: str,
        *,
        max_level: Optional[
            int
        ] = -1,  # TODO: Use -1 instead of None to simplify typing.
        show_cycles: bool = False,
    ) -> None:
        """
        Initialize the DependencyGraph with directory and analysis parameters.
        """
        # Following caused ValueError: Unable to determine caller function.
        # _LOG.debug(hprint.func_signature_to_str())
        # Initialize directory path
        print(f"Type of Path: {type(Path)}")
        self.directory = Path(directory).resolve()
        # Create a directed graph for dependencies.
        self.graph: nx.DiGraph = nx.DiGraph()
        # Set maximum directory depth.
        self.max_level = max_level if max_level is not None else -1  # Handle None
        # Configure cyclic dependency filtering.
        self.show_cycles = show_cycles

    def build_graph(self, abort_on_error: bool = False) -> None:
        """
        Build a directed graph of intra-directory dependencies.

        :param abort_on_error: If True, raise SyntaxError on parsing
            failures; if False, skip invalid files.
        """
        # _LOG.debug(hprint.func_signature_to_str())
        # Prepare directory analysis.
        _LOG.info("Building dependency graph for %s", self.directory)
        base_depth = len(self.directory.parts)
        _LOG.debug(hprint.to_str("base_depth"))
        # Collect Python files within `max_level` depth.
        py_files = [
            path
            for path in self.directory.rglob("*.py")
            if self.max_level == -1
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
            # TODO: Use hio.from_file and to_file to write.
            # TODO: Let's add a switch `abort_on_error` to continue or abort.
            # Parse the file as an Abstract Syntax Tree (AST).
            try:
                file_content = hio.from_file(str(py_file))
                tree = ast.parse(file_content, filename=str(py_file))
            except SyntaxError as e:
                if abort_on_error:
                    _LOG.error("Syntax error in %s: %s", py_file, e)
                    raise e
                _LOG.warning("Skipping %s due to syntax error: %s", py_file, e)
                continue
            # Extract imports from AST.
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports = (
                        [name.name for name in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module] if node.module is not None else []
                    )
                    _LOG.debug(hprint.to_str("imports"))
                    for imp in imports:
                        if imp is None:
                            _LOG.warning(
                                "Skipping None import in file %s", py_file
                            )
                            continue
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
        # Filter for cyclic dependencies if enabled.
        if self.show_cycles:
            self._filter_cycles()

    def get_text_report(self) -> str:
        """
        Generate a text report listing each module's dependencies.

        :return: Text report of dependencies, one per line.
        """
        # _LOG.debug(hprint.func_signature_to_str())
        # Initialize report.
        report = []
        # Generate report lines for each node.
        for node in self.graph.nodes:
            _LOG.debug(hprint.to_str("node"))
            dependencies = list(self.graph.successors(node))
            _LOG.debug(hprint.to_str("dependencies"))
            # Create report line based on dependencies.
            # TODO: Let's use a if-then-else for clarity.
            if dependencies:
                line = f"{node} imports {', '.join(dependencies)}"
            else:
                line = f"{node} has no dependencies"
            _LOG.debug(hprint.to_str("line"))
            report.append(line)
        return "\n".join(report)

    def get_dot_file(self, output_file: str) -> None:
        """
        Write the dependency graph to a DOT file.

        :param output_file: Path to the output DOT file.
        """
        # _LOG.debug(hprint.func_signature_to_str())
        # Write the graph to a DOT file.
        nx.drawing.nx_pydot.write_dot(self.graph, output_file)
        _LOG.info("DOT file written to %s", output_file)

    def _filter_cycles(self) -> None:
        """
        Filter the graph to show only nodes and edges in cyclic dependencies.
        """
        # _LOG.debug(hprint.func_signature_to_str())
        # Find strongly connected components.
        cycles = list(nx.strongly_connected_components(self.graph))
        # Accumulate cyclic nodes.
        _LOG.debug(hprint.to_str("cycles"))
        cyclic_nodes = set()
        for component in cycles:
            if len(component) > 1:
                cyclic_nodes.update(component)
        _LOG.debug(hprint.to_str("cyclic_nodes"))
        # Create a new graph with cyclic nodes and edges.
        new_graph = nx.DiGraph()
        for node in cyclic_nodes:
            new_graph.add_node(node)
        for u, v in self.graph.edges():
            if u in cyclic_nodes and v in cyclic_nodes:
                new_graph.add_edge(u, v)
        # Update the graph to include only cyclic dependencies.
        self.graph = new_graph
        _LOG.info(
            "Graph filtered to %d nodes and %d edges in cycles",
            len(self.graph.nodes),
            len(self.graph.edges),
        )

    # TODO: -> Optional[str]
    def _resolve_import(self, imp: str, py_file: Path) -> Optional[str]:
        """
        Resolve an import to a file path within the directory.

        :param imp: Import statement (e.g., `module.submodule`).
        :param py_file: File path where the import is found.
        :return: Relative path to the resolved file, or None if unresolved.
        """
        # _LOG.debug(hprint.func_signature_to_str())
        _LOG.info("Resolving import '%s' for file %s", imp, py_file)
        _LOG.debug(hprint.to_str("imp, py_file"))
        # Initialize base directory.
        base_dir = self.directory
        _LOG.info("Base directory: %s", base_dir)
        parts = imp.split(".")
        _LOG.debug(hprint.to_str("parts"))
        current_dir = base_dir
        # Check: direct match for directory package
        dir_name_parts = base_dir.name.split(".")
        if parts == dir_name_parts:
            init_path = base_dir / "__init__.py"
            _LOG.info("Checking base directory __init__ at %s", init_path)
            if init_path.exists():
                resolved_path = init_path.relative_to(base_dir.parent).as_posix()
                _LOG.info("Resolved directory self-import to: %s", resolved_path)
                return resolved_path
            _LOG.error("Base directory __init__.py missing at %s", init_path)
            return None
        # Handle directory name imports.
        # Current directory.
        dir_name = self.directory.name
        # Parent directory.
        parent_name = self.directory.parent.name
        # Grandparent directory, if exists.
        parent_parent_name = (
            self.directory.parent.parent.name
            if len(self.directory.parent.parts) > 1
            else ""
        )
        # Collect all parent directory names into a list for validation.
        valid_names = [dir_name, parent_name, parent_parent_name]
        parent = self.directory.parent
        while len(parent.parts) > 2:  # Stop near root
            valid_names.append(parent.parent.name)
            parent = parent.parent
        _LOG.info(
            "Directory name: %s, Parent name: %s, Parent parent name: %s, "
            "Valid names: %s, Import first part: %s",
            dir_name,
            parent_name,
            parent_parent_name,
            valid_names,
            parts[0] if parts else "",
        )
        result = None
        if parts and parts[0] in valid_names:
            parts = parts[1:]
            _LOG.debug(hprint.to_str("parts after dir_name handling"))
            if not parts:
                # Only if the `dir` name is given (e.g., "helpers"), check for
                # `__init__.py`.
                init_path = base_dir / "__init__.py"
                _LOG.info(
                    "Checking __init__.py at %s, exists: %s",
                    init_path,
                    init_path.exists(),
                )
                if init_path.exists():
                    resolved_path = init_path.relative_to(
                        self.directory.parent
                    ).as_posix()
                    _LOG.info("Resolved to: %s", resolved_path)
                    result = resolved_path
                else:
                    _LOG.error("No __init__.py found at %s", init_path)
        else:
            for i, module_name in enumerate(parts):
                _LOG.debug(hprint.to_str("i, module_name"))
                package_path = current_dir / module_name / "__init__.py"
                _LOG.info("Checking package path: %s", package_path)
                _LOG.debug(hprint.to_str("package_path"))
                if package_path.exists():
                    if i == len(parts) - 1:
                        resolved_path = package_path.relative_to(
                            self.directory.parent
                        ).as_posix()
                        _LOG.info("Resolved to: %s", resolved_path)
                        result = resolved_path
                        break
                    current_dir = current_dir / module_name
                    _LOG.debug(hprint.to_str("current_dir"))
                    continue
                # Check for a .py file.
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
                        result = resolved_path
                        break
                    # If not last part, but is a module, it can't lead further.
                    _LOG.info(
                        "Could not resolve full import '%s' beyond %s",
                        imp,
                        module_path,
                    )
                    break
                # If neither exists, the import cannot be resolved.
                _LOG.info(
                    "Could not resolve import '%s' at part '%s'", imp, module_name
                )
                break
        # Return None if module resolution was unsuccessful.
        if result is None:
            _LOG.info("Could not resolve import '%s'", imp)
        return result
