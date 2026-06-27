#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pyan3", "pydot"]
# ///

r"""
Generate a call graph for a Python file using pyan3 and graphviz.

This script analyzes a Python file and generates a visual call graph in PDF
format using pyan3 (for DOT generation) and graphviz (for PDF conversion).
The output is automatically opened in the default PDF viewer.

Each node in the call graph is a hyperlink to the corresponding function on
GitHub.

Example usage:

Generate call graph for a single Python file:
> build_call_graph.py --input=myfile.py

Generate with GitHub links pointing to master branch:
> build_call_graph.py --input=myfile.py --use_master

Import as:

import dev_scripts_helpers.coding_tools.build_call_graph as dscbcg
"""

import argparse
import ast
import importlib.metadata
import logging
import os
from typing import Dict, Optional

import pydot

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import dev_scripts_helpers.github.to_github as dscghtogh

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_DEFAULT_OUTPUT_DIR = "tmp.build_call_graph"

_PYAN_OPTIONS = [
    # Show which functions/classes are called.
    "--uses",
    # Hide function/class definitions to reduce visual clutter.
    "--no-defines",
    # Use colors to distinguish different entities.
    "--colored",
    # Group definitions and calls by module for better organization.
    "--grouped",
]


# #############################################################################
# Helper Functions
# #############################################################################


def _extract_function_line_numbers(input_file: str) -> Dict[str, int]:
    """
    Extract function definitions and their line numbers from a Python file.

    Uses AST parsing to find all function definitions and record their
    starting line numbers.

    :param input_file: Path to the Python file to analyze
    :return: Dict mapping function names to line numbers
    """
    function_lines = {}
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_lines[node.name] = node.lineno
    except Exception as e:
        _LOG.warning("Failed to extract function line numbers: %s", e)
    return function_lines


def _get_github_url_with_line(
    *,
    file_path: str,
    line_number: Optional[int] = None,
    use_master: bool = False,
) -> str:
    """
    Generate GitHub URL for a file with optional line number reference.

    :param file_path: Path to the file
    :param line_number: Optional line number to append to URL
    :param use_master: Use master branch instead of current branch
    :return: GitHub URL for the file, optionally with line number
    """
    base_url = dscghtogh._get_github_url(
        file_path=file_path,
        use_master=use_master,
    )
    if line_number is not None:
        base_url = f"{base_url}#L{line_number}"
    return base_url


def _enhance_dot_with_github_urls(
    *,
    dot_file: str,
    input_file: str,
    use_master: bool = False,
) -> None:
    """
    Add GitHub hyperlinks to nodes in a DOT file using pydot.

    Parses the DOT file, extracts function definitions from the input Python
    file with their line numbers, and adds URL attributes to matching nodes.
    Recursively traverses subgraphs to find all nodes.

    :param dot_file: Path to the DOT file to enhance
    :param input_file: Path to the input Python file (source of truth for line numbers)
    :param use_master: Use master branch instead of current branch for URLs
    """
    _LOG.info("Extracting function line numbers from: %s", input_file)
    function_lines = _extract_function_line_numbers(input_file)
    _LOG.info("Found %d functions", len(function_lines))
    # Parse the DOT file using pydot.
    graphs = pydot.graph_from_dot_file(dot_file)
    hdbg.dassert_eq(len(graphs), 1, "Expected exactly one graph in DOT file")
    graph = graphs[0]
    # Helper function to recursively update all nodes in a graph and subgraphs.
    nodes_updated = 0
    def update_nodes_in_graph(g):
        nonlocal nodes_updated
        # Iterate through all nodes in this graph.
        for node in g.get_node_list():
            node_name = node.get_name().strip('"')
            # Skip graph metadata nodes.
            if node_name in ["graph"]:
                continue
            # Extract the function name from the node name (may include module prefix).
            # Node names from pyan3 can be:
            #   - "function_name" (simple function)
            #   - "module__function_name" (pyan3 format with __)
            #   - "module.function_name" (alternative format)
            if "__" in node_name:
                func_name = node_name.split("__")[-1]
            else:
                func_name = node_name.split(".")[-1]
            # Check if this function has a known line number.
            if func_name in function_lines:
                line_number = function_lines[func_name]
                github_url = _get_github_url_with_line(
                    file_path=input_file,
                    line_number=line_number,
                    use_master=use_master,
                )
                node.set_URL(github_url)
                # Add link icon to node label to indicate it's interactive.
                current_label = node.get_label()
                if current_label:
                    current_label = current_label.strip('"')
                    node.set_label(f"🔗 {current_label}")
                nodes_updated += 1
        # Recursively process subgraphs.
        for subgraph in g.get_subgraph_list():
            update_nodes_in_graph(subgraph)
    update_nodes_in_graph(graph)
    _LOG.info("Updated %d nodes with GitHub URLs", nodes_updated)
    # Write the enhanced DOT file back.
    graph.write_raw(dot_file)
    _LOG.info("Enhanced DOT file with GitHub URLs: %s", dot_file)


def _get_pyan3_version() -> str:
    """
    Get the installed version of pyan3.

    Returns 'unknown' if the package is not installed.

    :return: Version string or 'unknown' if not installed
    """
    try:
        return importlib.metadata.version("pyan3")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _check_dependencies() -> None:
    """
    Check that required system dependencies are installed.

    Raises an exception if `dot` or `pyan3` commands are not available.

    :raises: Exception if required commands are not found
    """
    for cmd in ["dot", "pyan3"]:
        check_cmd = f"which {cmd}"
        _LOG.info("Executing: %s", check_cmd)
        hsystem.system(check_cmd, suppress_output=True)


def _generate_callgraph_dot(
    input_file: str,
    *,
    output_dir: str,
    use_master: bool = False,
) -> str:
    """
    Generate a callgraph DOT file using pyan3 with GitHub hyperlinks.

    Analyzes the provided Python file and generates a DOT format file representing
    the call graph using pyan3. Enhances the DOT file with GitHub hyperlinks for
    each function node. Handles relative paths by converting to absolute.

    :param input_file: Path to the Python file to analyze
    :param output_dir: Directory where to save the DOT file
    :param use_master: Use master branch instead of current branch for GitHub URLs
    :return: Path to the generated DOT file
    """
    _LOG.info("Generating callgraph DOT file from: %s", input_file)
    # Convert relative paths to absolute to avoid ambiguity.
    if not os.path.isabs(input_file):
        input_file = os.path.abspath(input_file)
    _LOG.info("Resolved input file: %s", input_file)
    hdbg.dassert_file_exists(input_file, "Input Python file does not exist")
    # Create output directory if needed.
    hio.create_dir(output_dir, incremental=True)
    dot_file = os.path.join(output_dir, "callgraph.dot")
    # Build pyan3 command with options for readable output.
    pyan_options = " ".join(_PYAN_OPTIONS)
    if False:
        # Add --root.
        root = hgit.find_git_root()
        pyan_options += f" --root {root}"
    cmd = f"pyan3 {input_file} --dot {pyan_options} > {dot_file}"
    _LOG.info("Executing: %s", cmd)
    hsystem.system(cmd)
    hdbg.dassert_file_exists(dot_file, "Failed to generate DOT file")
    _LOG.info("Generated DOT file: %s", dot_file)
    # Enhance the DOT file with GitHub hyperlinks.
    _enhance_dot_with_github_urls(
        dot_file=dot_file,
        input_file=input_file,
        use_master=use_master,
    )
    return dot_file


def _convert_dot_to_pdf(*, dot_file: str, output_dir: str) -> str:
    """
    Convert a DOT file to PDF using graphviz dot command.

    Use the `dot` utility to render the call graph from DOT format to PDF.

    :param dot_file: Path to the DOT file
    :param output_dir: Directory where to save the PDF file
    :return: Path to the generated PDF file
    """
    _LOG.info("Converting DOT file to PDF: %s", dot_file)
    hdbg.dassert_file_exists(dot_file, "DOT file does not exist")
    pdf_file = os.path.join(output_dir, "callgraph.pdf")
    # Use graphviz dot utility to render PDF from DOT format.
    cmd = f"dot -Tpdf {dot_file} -o {pdf_file}"
    _LOG.info("Executing: %s", cmd)
    hsystem.system(cmd)
    hdbg.dassert_file_exists(pdf_file, "Failed to generate PDF file")
    _LOG.info("Generated PDF file: %s", pdf_file)
    return pdf_file


def _open_pdf(*, pdf_file: str) -> None:
    """
    Open a PDF file using the system's default PDF viewer.

    Uses the `open` command to display the generated PDF in the default viewer.

    :param pdf_file: Path to the PDF file to open
    """
    _LOG.info("Opening PDF file: %s", pdf_file)
    hdbg.dassert_file_exists(pdf_file, "PDF file does not exist")
    # Use the system's default PDF viewer to open the file.
    cmd = f"open {pdf_file}"
    _LOG.info("Executing: %s", cmd)
    hsystem.system(cmd)


# #############################################################################
# Parser and Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for the call graph generator.

    :return: Configured argument parser with input file and output directory options
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        action="store",
        required=True,
        help="Path to the Python file to analyze",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Output directory for generated files (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--use_master",
        action="store_true",
        help="Use master branch instead of current branch for GitHub hyperlinks",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the call graph generation script.

    Orchestrates the three-phase process: dependency checking, DOT generation,
    PDF conversion, and automatic opening in the default viewer.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Log script initialization and configuration.
    pyan3_version = _get_pyan3_version()
    _LOG.info("Using pyan3 version: %s", pyan3_version)
    _LOG.info("Starting call graph generation")
    _LOG.info("Input file: %s", args.input)
    _LOG.info("Output directory: %s", args.output_dir)
    _LOG.info("Use master branch: %s", args.use_master)
    # Verify that required system commands are available before proceeding.
    _check_dependencies()
    # Phase 1: Generate DOT file using pyan3.
    dot_file = _generate_callgraph_dot(
        args.input,
        output_dir=args.output_dir,
        use_master=args.use_master,
    )
    # Phase 2: Convert DOT to PDF using graphviz.
    pdf_file = _convert_dot_to_pdf(dot_file=dot_file, output_dir=args.output_dir)
    # Phase 3: Open the generated PDF in the default viewer.
    _open_pdf(pdf_file=pdf_file)
    _LOG.info("Call graph generation complete: %s", pdf_file)


if __name__ == "__main__":
    _main(_parse())
