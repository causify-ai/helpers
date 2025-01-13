#!/usr/bin/env python

"""
Show import dependencies and detect cyclic imports.

E.g.,
# Show file dependencies.
> show_imports.py <module_name>

# Show directory dependencies.
> show_imports.py --dir <module_name>

# Show level X dependencies.
> show_imports.py --max_level X <module_name>
"""

import argparse
import copy
import dataclasses
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import graphviz
import networkx as nx

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# Style config.
DIR_SHAPE = "folder"
DIR_COLOR = "cadetblue"
FILE_SHAPE = "oval"
FILE_COLOR = "cyan3"
EXTERNAL_SHAPE = "folder"
EXTERNAL_COLOR = "red"
TEXT_COLOR = "darkslategray"
CLUSTER_COLOR = "darkslategray"

# Directories structure type.
_DIR_STRUCTURE_TYPE = Dict[int, Dict[str, List[str]]]


class NotModuleError(Exception):
    pass


class _PydepsRunner:
    """
    A wrapper to interact with `pydeps`.
    """

    def __init__(
        self, module_path: str, show_cycles: bool, exclude_unimported_dirs: bool
    ) -> None:
        """
        Initialize the wrapper with a target module path.

        :param module_path: path to the input module or directory containing
            multiple modules
        :param show_cycles: if True, append `--show-cycles` option to the
            `pydeps` command
        :param exclude_unimported_dirs: if True, exclude dirs that contain files
            that are usually not imported from the module check (trash, temporary cache,
            unit tests and notebooks)
        """
        self.show_cycles = show_cycles
        # Check if the input dir is valid for imports retrieval.
        invalid_dirs = liutils.get_dirs_with_missing_init(
            module_path, exclude_unimported_dirs
        )
        if invalid_dirs:
            raise NotModuleError(
                f"The following dirs have to be modules (add `__init__.py`): {invalid_dirs}",
            )
        self.submodules = [module_path]
        # Create a temporary dir for storing intermediate results.
        # pylint: disable=consider-using-with
        # Override pylint to preserve the dir for future use.
        self.tmp_dir = tempfile.TemporaryDirectory(prefix="tmp.pydeps")

    def run(self) -> str:
        """
        Run the `pydeps` script.

        :return: the output filename
        """
        # Call `pydeps` for each submodule.
        tmp_output_filenames = []
        submodule_names = []
        for submodule in self.submodules:
            tmp_output_filename = self._run_submodule(submodule)
            tmp_output_filenames.append(tmp_output_filename)
            submodule_name = submodule.split("/")[-1]
            submodule_names.append(submodule_name)
        # Concatenate outputs.
        _tmp_concatenated_output_filename = (
            f"{self.tmp_dir.name}/concatenated_output.json"
        )
        concat_out_data: Dict[str, Dict[str, Any]] = {}
        for tmp_output_filename, submodule_name in zip(
            tmp_output_filenames, submodule_names
        ):
            out_data = hio.from_json(tmp_output_filename)
            # Check which of the new nodes have already appeared before.
            new_nodes = set(out_data.keys())
            old_nodes = set(concat_out_data.keys())
            common_nodes = new_nodes.intersection(old_nodes)
            new_nodes = new_nodes.difference(old_nodes)
            # Update the common nodes, if their names start with the
            # submodule name. In this case the more recent info about these nodes
            # is the most accurate.
            for common_node in common_nodes:
                if common_node.startswith(f"{submodule_name}."):
                    concat_out_data[common_node] = out_data[common_node]
            # Insert all the new nodes.
            for new_node in new_nodes:
                concat_out_data[new_node] = out_data[new_node]
        hio.to_json(_tmp_concatenated_output_filename, concat_out_data)
        return _tmp_concatenated_output_filename

    def cleanup(self) -> None:
        """
        Clean and delete the temporary directory.
        """
        self.tmp_dir.cleanup()

    def _run_submodule(self, submodule_path: str) -> str:
        """
        Run the `pydeps` script on the specified submodule.

        :param submodule_path: path to the input submodule
        :return: the output filename
        """
        # Initialize the `pydeps` arguments used for each call.
        pydeps_args = [
            ("--no-output", ""),
            ("--show-deps", ""),
            ("", submodule_path),
        ]
        if self.show_cycles:
            pydeps_args.append(("--show-cycles", ""))
        output_name = submodule_path.replace("/", "_")
        # Set the `pydeps` output filename.
        _tmp_output_filename = f"{self.tmp_dir.name}/{output_name}.json"
        pydeps_args.append((">", _tmp_output_filename))
        # Before running pydeps we need to make sure that it uses the code
        # in `/src` and not the ones in `/app` (see DevToolsTask406).
        cmd = "export PYTHONPATH=/src:$PYTHONPATH; pydeps"
        for arg_name, arg_value in pydeps_args:
            cmd += f" {arg_name} {arg_value}"
        hsystem.system(cmd)
        # Assert that the command produced an output.
        hdbg.dassert_path_exists(
            _tmp_output_filename, msg="`pydeps` did not produce any output"
        )
        return _tmp_output_filename


@dataclasses.dataclass
class _NodeInfo:
    """
    Store information about a node in a dependency graph.
    """

    node_name: str
    # A number of 'hops' between the node and the module we're interested in, see
    # https://github.com/thebjorn/pydeps#bacon-scoring.
    bacon: int
    imported_by: Optional[List[str]] = None
    imports: Optional[List[str]] = None
    path: Optional[str] = None
    # `truncated` should be set to True when the name of the node is truncated.
    # A node name is truncated when a part of its path has been removed, e.g.,
    # 'a.b.c' -> 'a.b'.
    truncated: bool = False
    # Used for labeling external dependencies.
    is_external: Optional[bool] = None
    # Used for labeling file dependencies.
    is_file: Optional[bool] = None

    def check_external(self, reference_path: str) -> None:
        """
        Check if the node is an external dependency.

        The dependency is checked with respect to the module path of reference.
        The node's status is recorded in the node's info.

        :param reference_path: reference module path
        """
        is_external = False
        if self.path is not None:
            if not self.path.startswith(reference_path):
                is_external = True
                # Temporary fix in order not to mark as external those modules that
                # have the same names as some modules from `dev_tools`, which have been
                # added to PYTHONPATH.
                dev_tools_modules = [
                    "documentation",
                    "github_labels",
                    "helpers",
                    "import_check",
                    "linters",
                ]
                for dev_tools_module in dev_tools_modules:
                    if dev_tools_module in self.path:
                        is_external = False
        self.is_external = is_external

    def check_is_file(self) -> None:
        """
        Check if the node is a file dependency.
        """
        is_file = False
        if self.path is not None:
            if not self.path.endswith("__init__.py"):
                is_file = True
        self.is_file = is_file


class _NodesInfo:
    """
    Read, process and write dependency nodes information.
    """

    def __init__(self, dependencies_filename: str) -> None:
        """
        Load dependencies info from the dependencies file.

        :param dependencies_filename: name of the file with node dependencies
        """
        self.nodes_info: List[_NodeInfo] = []
        self._read_textual_output(dependencies_filename)

    def write_textual_output(self, filename: str) -> None:
        """
        Save dependency nodes in a text file.

        :param filename: output filename
        """
        output = {}
        for node_info in self.nodes_info:
            output_node_info = dataclasses.asdict(node_info)
            output[output_node_info.pop("node_name")] = output_node_info
        output = dict(sorted(output.items()))
        hio.to_json(filename, output)

    def label_external_dependencies(self, reference_path: str) -> None:
        """
        Label the nodes as external or not.

        Add a label `is_external` to nodes, which indicates whether a node is external
        or not with respect to the module path of reference.

        :param reference_path: reference module path
        """
        for node_info in self.nodes_info:
            node_info.check_external(reference_path)

    def label_file_dependencies(self) -> None:
        """
        Label the nodes as files or not.

        Add a label `is_file` to nodes, which indicates whether a node
        is a file dependency or not.
        """
        for node_info in self.nodes_info:
            node_info.check_is_file()

    def remove_external_dependencies(self) -> None:
        """
        Remove all the external dependency nodes.

        External dependencies are modules / libraries that are not in
        the current repo, e.g., Python standard libraries or third-party
        libraries.
        """
        modified_nodes_info = []
        for node_info in self.nodes_info:
            if not node_info.is_external:
                modified_nodes_info.append(node_info)
        self.nodes_info = modified_nodes_info

    def file_to_directory_dependencies(self) -> None:
        """
        Convert all the file nodes to directory nodes.
        """
        for node_info in self.nodes_info:
            if node_info.is_file:
                modules = node_info.node_name.split(".")[:-1]
                new_node_name = ".".join(modules)
                # If the name should be changed, change it and update the
                # `truncated` label.
                if new_node_name != node_info.node_name:
                    node_info.node_name = new_node_name
                    node_info.truncated = True

    def truncate_node_level(self, max_level: int) -> None:
        """
        Truncate the level of all the nodes to the given level.

        E.g., if the input `max_level` is 2, then `dir1/dir2/file` is truncated
        to `dir1/dir2/`.

        :param max_level: the dependency level to truncate to
        """
        for node_info in self.nodes_info:
            new_node_name = ".".join(node_info.node_name.split(".")[:max_level])
            if new_node_name != node_info.node_name:
                # Change the name and update the `truncated` label.
                node_info.node_name = new_node_name
                node_info.truncated = True

    def prepend_prefix_to_internal_node_names(self, prefix: str) -> None:
        """
        Prepend the specified prefix to each internal node name.

        :param prefix: a prefix to prepend
        """
        # Create a mapping of node names to nodes.
        mapped_nodes_info = self.map_name_to_node()
        for i, _ in enumerate(self.nodes_info):
            if not self.nodes_info[i].is_external:
                # Update the node name.
                self.nodes_info[
                    i
                ].node_name = f"{prefix}.{self.nodes_info[i].node_name}"
                # Update the node imports-related data.
                self.nodes_info[i] = self._prepend_prefix_to_internal_imports(
                    self.nodes_info[i], prefix, mapped_nodes_info
                )

    def remove_internal_module_nodes(self) -> None:
        """
        Remove all the internal module nodes from the dependencies.

        A module node is a node with the path ending with '__init__.py'
        or with the path set to None.
        """
        modified_nodes_info = []
        for node_info in self.nodes_info:
            if node_info.is_external or node_info.is_file:
                # Keep only external nodes and nodes that are files.
                modified_nodes_info.append(node_info)
        self.nodes_info = modified_nodes_info

    def map_name_to_node(self) -> Dict[str, _NodeInfo]:
        """
        Create a mapping from node names to nodes.

        :return: a mapping from node names to nodes
        """
        mapped_nodes_info: Dict[str, _NodeInfo] = {}
        for node_info in self.nodes_info:
            mapped_nodes_info[node_info.node_name] = node_info
        return mapped_nodes_info

    @staticmethod
    def _prepend_prefix_to_internal_imports(
        node_info: _NodeInfo,
        prefix: str,
        mapped_nodes_info: Dict[str, _NodeInfo],
    ) -> _NodeInfo:
        """
        Prepend the specified prefix to node's import data.

        :param node_info: dependency node to update
        :param prefix: a prefix to prepend
        :param mapped_nodes_info: a mapping from node names to nodes
        :return: a modified node
        """
        modified_node_info = copy.copy(node_info)
        # Prepend the prefix to the import data related to the node.
        if node_info.imported_by is not None:
            imported_by_modified = []
            for imp in node_info.imported_by:
                imp_modified = imp
                if imp in mapped_nodes_info:
                    if not mapped_nodes_info[imp].is_external:
                        # Update the import if it is an internal dependency.
                        imp_modified = f"{prefix}.{imp}"
                imported_by_modified.append(imp_modified)
            modified_node_info.imported_by = imported_by_modified
        if node_info.imports is not None:
            imports_modified = []
            for imp in node_info.imports:
                imp_modified = imp
                if imp in mapped_nodes_info:
                    if not mapped_nodes_info[imp].is_external:
                        # Update the import if it is an internal dependency.
                        imp_modified = f"{prefix}.{imp}"
                imports_modified.append(imp_modified)
            modified_node_info.imports = imports_modified
        return modified_node_info

    def _read_textual_output(self, dependencies_filename: str) -> None:
        """
        Read the textual output from a file and parse it.

        :param dependencies_filename: name of the file with node dependencies
        """
        pydeps_output = hio.from_json(dependencies_filename)
        for node_name, node_info in pydeps_output.items():
            # `node_info` is a dictionary containing <node_property>:<property_value>
            # pairs, where node properties are ["bacon", "imported_by", "imports",
            # "path"]. Some properties may be unspecified (e.g., when a node does
            # not depend on any module, `node_info` does not contain the "imports" key).
            node = _NodeInfo(node_name, node_info["bacon"])
            if "imported_by" in node_info:
                node.imported_by = node_info["imported_by"]
            if "imports" in node_info:
                node.imports = node_info["imports"]
            if "path" in node_info:
                node.path = node_info["path"]
            self.nodes_info.append(node)


class DependenceGraphComputer:
    """
    Compute a dependency graph.
    """

    def __init__(
        self,
        nodes_info: _NodesInfo,
        root_module_name: str,
        *,
        cluster: bool = True,
        show_cycles: bool = False,
    ) -> None:
        """
        Initialize the class for computing a dependency graph.

        :param nodes_info: a list of dependency nodes
        :param root_module_name: name of the root module
        :param cluster: if True, apply folder clustering to the graph
        :param show_cycles: if True, show cyclic dependencies only
        """
        self._nodes_info = copy.copy(nodes_info)
        self._root_module_name = root_module_name
        self._cluster = cluster
        self._show_cycles = show_cycles
        # Create the root graph and set strict to `True` to collapse all the
        # duplicated edges.
        self._root_graph: graphviz.Digraph = graphviz.Digraph(strict=True)
        self.structured_graph: nx.Graph = nx.DiGraph()

    def collect_graph_data(self) -> None:
        """
        Create a graph from the loaded dependency nodes.
        """
        # Remove the module nodes, only file nodes are used for graph creation.
        self._nodes_info.remove_internal_module_nodes()
        # Create a mapping between the node names and the nodes.
        self._mapped_nodes_info = self._nodes_info.map_name_to_node()
        # Check if we have any dependency nodes.
        if len(self._nodes_info.nodes_info) == 0:
            _LOG.info("No dependencies to show.")
        # If we have dependency nodes, add the corresponding nodes and edges to the
        # graph.
        else:
            self._add_nodes_to_graph()
            self._add_edges_to_graph()
            self._remove_isolated_nodes_from_graph()

    def plot_graph(
        self,
        out_filename: str,
        *,
        out_format: str = "pdf",
        save_source: Optional[bool] = False,
    ) -> None:
        """
        Plot the graph and save the result.

        :param out_filename: name of the output file
        :param out_format: output format
            - "pdf"
            - "svg"
            - "png"
        :param save_source: if set to True, the graph source file will not be deleted
        """
        hdbg.dassert_in(out_format, ["pdf", "svg", "png"])
        if out_filename.endswith(f".{out_format}"):
            # If `out_filename` already contains the extension, remove it.
            out_filename = f".{out_format}".join(
                out_filename.split(f".{out_format}")[:-1]
            )
        # Plot the graph in the output file.
        self._root_graph.render(
            out_filename, format=out_format, cleanup=not save_source
        )

    def create_dot_graph(self) -> None:
        """
        Create a graphviz dot graph for plotting the graph.

        - Create subgraphs for lower directory levels
        - Create subgraphs for upper directory levels
        - Update the upper levels' subgraphs with the lower level subgraphs
        """
        if self._show_cycles:
            # Keep the cycles only.
            self._remove_non_cyclic_dependencies()
        # Compute the directory structure for all the nodes in the structured
        # graph.
        directories = self._extract_directories_structure()
        # Get the maximum directory level.
        max_level = max(directories.keys())
        if max_level == -1:
            return
        # Create a dictionary of subgraphs.
        self._subgraphs: Dict[str, graphviz.Digraph] = {}
        # For each directory level, starting from the deepest one, create
        # a subgraph for each directory of that level.
        for dir_level in reversed(range(1, max_level + 1)):
            dir_level_directories = directories[dir_level]
            for dir_ in dir_level_directories.keys():
                if dir_ not in self._subgraphs:
                    # Create a corresponding subgraph if it doesn't already exist.
                    # The subgraph name is simply the name of directory.
                    subgraph_name = dir_.split(".")[-1]
                    self._subgraphs[dir_] = self._create_subgraph(
                        subgraph_name, CLUSTER_COLOR
                    )
                # Add the files from the directory as subgraph nodes.
                for node in dir_level_directories[dir_]:
                    self._add_internal_node(node, dir_)
            # If the dir level is not the deepest one,
            # update the subgraphs of the lower level.
            if dir_level < max_level:
                directories = self._update_lower_level_directories(
                    directories, dir_level
                )
        root_graph_name = list(directories[1].keys())[0]
        # Add the external dependencies to the root graph.
        for ext_node in directories[-1]:
            self._add_external_node(ext_node)
        # Add the root graph with internal dependencies to the root graph with all
        # the dependencies.
        self._root_graph.subgraph(self._subgraphs[root_graph_name])
        # Add the edges.
        for from_node, to_node in sorted(self.structured_graph.edges):
            self._root_graph.edge(from_node, to_node)

    def _create_subgraph(self, name: str, color: str) -> graphviz.Digraph:
        """
        Create a subgraph with the specified name and color.

        :param name: subgraph name
        :param color: color of the cluster frame
        :return: created subgraph
        """
        if self._cluster:
            cluster = "cluster_"
        else:
            cluster = ""
        graph = graphviz.Digraph(
            f"{cluster}{name}",
            graph_attr={"compound": "true", "label": name},
            node_attr={"style": "filled"},
            body=[f"\tcolor={color}"],
        )
        return graph

    def _add_nodes_to_graph(self) -> None:
        """
        Add dependency nodes to the graph.
        """
        for node_info in self._nodes_info.nodes_info:
            self.structured_graph.add_node(node_info.node_name)

    def _add_edges_to_graph(self) -> None:
        """
        Add edges to the graph inferred from the nodes' imports.
        """
        # Sort the node names by length; used for checking the truncated imports' names.
        sorted_nodes = sorted(
            list(self.structured_graph.nodes()), key=len, reverse=True
        )
        for node_info in self._nodes_info.nodes_info:
            if node_info.imports is not None:
                for imp in node_info.imports:
                    if imp not in sorted_nodes:
                        # If the import node was not added to the graph, check if
                        # its truncated version was added to the graph.
                        imported_node = next(
                            (node for node in sorted_nodes if node in imp), None
                        )
                    else:
                        # Don't map to nodes which have been truncated, but are not
                        # the truncated version of `imp` (if they were a truncated
                        # version of `imp`, their name would be different from `imp`).
                        if not self._mapped_nodes_info[imp].truncated:
                            imported_node = imp
                        else:
                            imported_node = None
                    if (
                        imported_node is not None
                        and imported_node != node_info.node_name
                    ):
                        # Add an edge if the imported node is different from the current node.
                        self.structured_graph.add_edge(
                            node_info.node_name, imported_node
                        )

    def _remove_isolated_nodes_from_graph(self) -> None:
        """
        Remove nodes without any edges from the graph.
        """
        # Store the nodes that are connected to at least one other node.
        connected_nodes = set()
        new_structured_graph = copy.deepcopy(self.structured_graph)
        for (n1, n2) in self.structured_graph.edges:
            connected_nodes.add(n1)
            connected_nodes.add(n2)
        # Remove all the other nodes.
        for node in self.structured_graph.nodes():
            if node not in connected_nodes:
                new_structured_graph.remove_node(node)
        self.structured_graph = new_structured_graph

    def _remove_non_cyclic_dependencies(self) -> None:
        """
        Remove non-cyclic dependencies from the graph.
        """
        new_structured_graph = copy.deepcopy(self.structured_graph)
        # Find cycles in the graph.
        simple_cycles = list(nx.simple_cycles(self.structured_graph))
        # Find the nodes that belong to cyclic dependencies.
        nodes_in_cycles: List[str] = sum(simple_cycles, [])
        # Remove all the other nodes.
        for node in self.structured_graph.nodes():
            if node not in nodes_in_cycles:
                new_structured_graph.remove_node(node)
        self.structured_graph = new_structured_graph

    def _add_internal_node(self, node: str, directory: str) -> None:
        """
        Add an internal node to one of the dot graph subgraphs.

        :param node: node name
        :param directory: directory name
        """
        # Extract the graph node label.
        if self._cluster:
            # When clustering is applied, there is no need for
            # displaying the full node name path.
            node_label = node.split(".")[-1]
        else:
            node_label = node
        if self._mapped_nodes_info[node].truncated:
            # Visualize the node as a directory.
            node_shape = DIR_SHAPE
            node_color = DIR_COLOR
        else:
            # Visualize the node as a file.
            node_shape = FILE_SHAPE
            node_color = FILE_COLOR
        self._subgraphs[directory].node(
            node,
            node_label,
            shape=node_shape,
            color=node_color,
            labelfontcolor=TEXT_COLOR,
        )

    def _add_external_node(self, node: str) -> None:
        """
        Add an external node to the root dot graph.

        :param node: node name
        """
        self._root_graph.node(
            node,
            node,
            shape=EXTERNAL_SHAPE,
            color=EXTERNAL_COLOR,
        )

    def _extract_directories_structure(self) -> _DIR_STRUCTURE_TYPE:
        """
        Extract directories' names, levels and files they contain.

        :return: the directory structure of the following format:
            <directory level>: {<directory 1>: [<file 1>, ... ], ... }
        """
        directories: _DIR_STRUCTURE_TYPE = {}
        # Level -1 is used to indicate external directories.
        directories[-1] = {}
        # For each node of the graph, extract the structure of the directory
        # containing it.
        for node in sorted((self.structured_graph.nodes())):
            if self._mapped_nodes_info[node].is_external:
                # If external, apply level -1.
                directories[-1][node] = []
            elif self._mapped_nodes_info[node].is_file:
                # If internal and is a file, extract the structure of the directory
                # containing it.
                modules = node.split(".")[:-1]
                if modules:
                    # Extract the directory name.
                    dir_name = ".".join(modules)
                    # Extract the directory level.
                    dir_level = len(modules)
                    # Add the level to the directories, if it does not exist
                    # already.
                    if dir_level not in directories:
                        directories[dir_level] = {}
                    # Tag the directory with its directory level, if it's not
                    # already tagged.
                    if dir_name not in directories[dir_level]:
                        directories[dir_level][dir_name] = []
                    # Add the file to the directory structure.
                    directories[dir_level][dir_name].append(node)
        # If some directory levels between 1 and the maximum level
        # are missing, add them to the structure.
        dir_levels = max(directories.keys())
        for dir_level in range(1, dir_levels + 1):
            if dir_level not in directories:
                directories[dir_level] = {}
        return directories

    def _update_lower_level_directories(
        self, directories: _DIR_STRUCTURE_TYPE, dir_level: int
    ) -> _DIR_STRUCTURE_TYPE:
        """
        Update directories from a given directory level.

        Update the directories with lower level directories.
        For each directory of the `dir_level` + 1, add it to the directory that
        contains it (in the level `dir_level`).

        :param directories: directories structure to update
        :param dir_level: directory level to update
        :return: updated directories structure
        """
        # Copy the input structure.
        directories_copy = copy.deepcopy(directories)
        # Get the lower level directories.
        lower_level_directories = directories[dir_level + 1].keys()
        # For each directory of the lower level, update its upper level
        # directory (from the input `dir_level`).
        for dir_ in lower_level_directories:
            # Upper level directory name of a.b.c is a.b.
            upper_level_dir_name = dir_.split(".")[:-1]
            upper_level_dir_name = ".".join(upper_level_dir_name)
            if upper_level_dir_name not in self._subgraphs:
                # Create upper level dir if it doesn't already exist.
                # Subgraph name of a.b is just b.
                subgraph_name = upper_level_dir_name.rsplit(".", maxsplit=1)[-1]
                # Create a subgraph in the dot graph.
                self._subgraphs[upper_level_dir_name] = self._create_subgraph(
                    subgraph_name, CLUSTER_COLOR
                )
                # Add the directory to the directory structure as well.
                directories_copy[dir_level][upper_level_dir_name] = []
            # Update the upper level directory dot subgraph.
            self._subgraphs[upper_level_dir_name].subgraph(self._subgraphs[dir_])
        return directories_copy


# #############################################################################
# Definition of the pipeline
# #############################################################################


def retrieve_dependencies(
    module_path: str,
    dependency_level: int,
    directory_dependencies: bool,
    external_dependencies: bool,
    show_cycles: bool,
    *,
    exclude_unimported_dirs: bool = True,
) -> _NodesInfo:
    """
    Retrieve the directory dependencies.

    - Call `pydeps`
    - Modify the output node names
    - Apply the required filters

    See `_show_dependencies` for the description of the parameters.

    :return: the dependency data
    """
    # Call `pydeps`.
    _LOG.info("Retrieving imports for %s", module_path)
    pydeps_runner = _PydepsRunner(
        module_path, show_cycles, exclude_unimported_dirs
    )
    tmp_output_filename = pydeps_runner.run()
    # Load the nodes info.
    _LOG.info("Processing dependency graph nodes")
    nodes_info = _NodesInfo(tmp_output_filename)
    # Remove the temporary directory.
    pydeps_runner.cleanup()
    # Add labels to the nodes.
    module_abs_path = os.path.abspath(module_path)
    nodes_info.label_external_dependencies(f"{module_abs_path}/")
    nodes_info.label_file_dependencies()
    # If the input directory contains submodules, prepend the directory name
    # to each submodule dependency node name and the related imports.
    if len(pydeps_runner.submodules) > 1:
        module_name = module_path.split("/")[-1]
        nodes_info.prepend_prefix_to_internal_node_names(module_name)
    # Modify the output node names and apply the required filters.
    if dependency_level > 0:
        nodes_info.truncate_node_level(dependency_level)
    if directory_dependencies:
        nodes_info.file_to_directory_dependencies()
    if not external_dependencies:
        nodes_info.remove_external_dependencies()
    return nodes_info


def _show_dependencies(
    module_path: str,
    dependency_level: int,
    directory_dependencies: bool,
    external_dependencies: bool,
    show_cycles: bool,
    output_format: str,
    output_filename: Optional[str],
    *,
    save_graph_source: Optional[bool] = False,
    exclude_unimported_dirs: bool = True,
) -> str:
    """
    Retrieve and save the module dependencies.

    The output format can be a textual description of the dependencies
    or a graph plot.

    :param module_path: path to the input module
    :param dependency_level: dependency level
    :param directory_dependencies: if True, file dependencies are aggregated to
        directory dependencies and not shown
    :param external_dependencies: if True, external dependencies are shown
    :param show_cycles: if True, only cyclic dependencies are shown
    :param output_format: the output format
        - "txt"
        - "pdf"
        - "svg"
        - "png"
    :param output_filename: filename of the output
    :param save_graph_source: if set to True, the graph source file will not be deleted and can be
        used for testing/debugging
    :param exclude_unimported_dirs: if set to True, dirs with unit tests and notebooks, trash and
        tmp cache dirs will be excluded from the module check
    :return: path to the output file
    """
    hdbg.dassert_in(output_format, ["txt", "pdf", "svg", "png"])
    # Retrieve the dependencies in the module.
    nodes_info = retrieve_dependencies(
        module_path,
        dependency_level,
        directory_dependencies,
        external_dependencies,
        show_cycles,
        exclude_unimported_dirs=exclude_unimported_dirs,
    )
    # Save the output in the specified format.
    module_name = module_path.split("/")[-1]
    if not output_filename:
        output_filename = f"{module_name}_dependencies.{output_format}"
    if output_format != "txt":
        # Create a graph.
        # If the `directory_dependencies` option is set to True, disable clustering.
        _LOG.info("Visualizing dependency graph")
        apply_clustering = not directory_dependencies
        dependence_graph_computer = DependenceGraphComputer(
            nodes_info,
            module_name,
            cluster=apply_clustering,
            show_cycles=show_cycles,
        )
        dependence_graph_computer.collect_graph_data()
        dependence_graph_computer.create_dot_graph()
        # Plot the graph.
        dependence_graph_computer.plot_graph(
            output_filename,
            out_format=output_format,
            save_source=save_graph_source,
        )
    else:
        # Generate the textual output.
        nodes_info.write_textual_output(output_filename)
    return output_filename


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("module", type=str, help="Path to the target module")
    parser.add_argument(
        "--dir", action="store_true", help="Show only directory dependencies"
    )
    parser.add_argument(
        "--ext", action="store_true", help="Show external dependencies"
    )
    parser.add_argument(
        "--max_level",
        type=int,
        default=0,
        help="Maximum dependency level, 0 -> infinite",
    )
    parser.add_argument(
        "--show_cycles", action="store_true", help="Show only import cycles"
    )
    parser.add_argument(
        "--out_format",
        type=str,
        default="png",
        choices=["txt", "pdf", "svg", "png"],
        help="Output format",
    )
    parser.add_argument(
        "--out_filename",
        type=str,
        default=None,
        help="Write output to 'out_filename'",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert_dir_exists(
        args.module, f"{args.module} is not a valid directory"
    )
    out_filename = _show_dependencies(
        args.module,
        args.max_level,
        args.dir,
        args.ext,
        args.show_cycles,
        args.out_format,
        args.out_filename,
    )
    _LOG.info("Finished analyzing imports. Output saved to %s", out_filename)


if __name__ == "__main__":
    _main(_parse())
