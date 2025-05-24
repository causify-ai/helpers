#!/usr/bin/env python

"""
Generate a dependency report for a specified directory.

E.g.,
# Generate report for current directory
> show_deps.py .

# Generate report with max depth 2
> show_deps.py --max_level 2 .

# Show only cyclic dependencies
> show_deps.py --show_cycles .
"""

import argparse
import logging
import sys

import helpers.hdbg as hdbg
import helpers.hparser as hparser
try:
    from import_check.dependency_graph import DependencyGraph
except ImportError as e:
    logging.error("Failed to import DependencyGraph: %s", str(e))
    logging.error("Ensure you are running as a module (e.g., python -m import_check.show_deps) or check package structure")
    sys.exit(1)

_LOG = logging.getLogger(__name__)

# #############################################################################

def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser object configured with command-line options.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Path to the directory to analyze"
    )
    parser.add_argument(
        "--out_file",
        type=str,
        default="dependency_graph.dot",
        help="Path to the output DOT file"
    )
    parser.add_argument(
        "--max_level",
        type=int,
        default=-1,
        help="Maximum directory depth to analyze (-1 for no limit)"
    )
    parser.add_argument(
        "--show_cycles",
        action="store_true",
        help="Show only cyclic dependencies"
    )
    hparser.add_verbosity_arg(parser)
    return parser

# #############################################################################

def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to generate dependency report.

    :param parser: ArgumentParser object to parse command-line arguments.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert_dir_exists(args.directory, f"{args.directory} is not a valid directory")
    _LOG.info("Starting dependency analysis for %s", args.directory)
    try:
        graph = DependencyGraph(args.directory, max_level=args.max_level, show_cycles=args.show_cycles)
        graph.build_graph()
        if not graph.graph.nodes:
            _LOG.info("No Python files found or no dependencies to report in %s", args.directory)
        else:
            report = graph.get_text_report()
            print(report)
            graph.get_dot_file(args.out_file)
            _LOG.info("DOT file written to %s", args.out_file)
    except Exception as e:
        _LOG.error("Failed to generate dependency report: %s", str(e))
        sys.exit(1)

# #############################################################################

if __name__ == "__main__":
    _main(_parse())