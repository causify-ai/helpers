#!/usr/bin/env python

"""
Detect cyclic imports.

> detect_import_cycles.py <module_name>
"""

import argparse
import logging
import sys
from typing import List

import networkx as nx

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import import_check.show_imports as ichshimp

_LOG = logging.getLogger(__name__)


def _check_import_cycles(
    module_path: str, *, exclude_unimported_dirs: bool = True
) -> List[List[str]]:
    """
    Detect import cycles in a module.

    :param module_path: path to the input module
    :param exclude_unimported_dirs: if set to True, dirs with unit tests and notebooks,
        trash and tmp cache dirs will be excluded from the module check
    :return: a list of lists of modules forming import cycles
    """
    # Retrieve the dependency information.
    dependency_level = 0
    directory_dependencies = False
    external_dependencies = False
    show_cycles = True
    nodes_info = ichshimp.retrieve_dependencies(
        module_path,
        dependency_level,
        directory_dependencies,
        external_dependencies,
        show_cycles,
        exclude_unimported_dirs=exclude_unimported_dirs,
    )
    # Build a graph.
    module_name = module_path.split("/")[-1]
    dependence_graph_computer = ichshimp.DependenceGraphComputer(
        nodes_info, module_name, show_cycles=show_cycles
    )
    dependence_graph_computer.collect_graph_data()
    graph = dependence_graph_computer.structured_graph
    # Detect cycles.
    cycles = set(tuple(g) for g in nx.simple_cycles(graph))
    cycles = sorted([sorted(x) for x in cycles])
    return cycles


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("module", type=str, help="Path to the target module")
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=False)
    hdbg.dassert_dir_exists(
        args.module, f"{args.module} is not a valid directory"
    )
    cycles = _check_import_cycles(args.module)
    if not cycles:
        _LOG.info("No cyclic imports detected")
    else:
        for cycle in cycles:
            _LOG.error("Cyclic imports detected: (%s)", ", ".join(cycle))
        sys.exit(-1)


if __name__ == "__main__":
    _main(_parse())
