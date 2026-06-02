#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pyan3"]
# ///

r"""
Generate a call graph for a Python file using pyan3 and graphviz.

This script analyzes a Python file and generates a visual call graph in PDF
format using pyan3 (for DOT generation) and graphviz (for PDF conversion).
The output is automatically opened in the default PDF viewer.

Example usage:

Generate call graph for a single Python file:
> build_call_graph.py --input=myfile.py

Generate with custom output directory:
> build_call_graph.py --input=myfile.py --output_dir=my_graphs

Import as:

import dev_scripts_helpers.coding_tools.build_call_graph as dscbcg
"""

import argparse
import importlib.metadata
import logging
import os

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

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
    input_file: str, *, output_dir: str
) -> str:
    """
    Generate a callgraph DOT file using pyan3.

    Analyzes the provided Python file and generates a DOT format file representing
    the call graph using pyan3. Handles relative paths by converting to absolute.

    :param input_file: Path to the Python file to analyze
    :param output_dir: Directory where to save the DOT file
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
    # Verify that required system commands are available before proceeding.
    _check_dependencies()
    # Phase 1: Generate DOT file using pyan3.
    dot_file = _generate_callgraph_dot(
        args.input, output_dir=args.output_dir
    )
    # Phase 2: Convert DOT to PDF using graphviz.
    pdf_file = _convert_dot_to_pdf(
        dot_file=dot_file, output_dir=args.output_dir
    )
    # Phase 3: Open the generated PDF in the default viewer.
    _open_pdf(pdf_file=pdf_file)
    _LOG.info("Call graph generation complete: %s", pdf_file)


if __name__ == "__main__":
    _main(_parse())
