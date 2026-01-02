#!/usr/bin/env python

"""
Extract Google Doc links from .gdoc files in a directory.

This script searches for all `.gdoc` files in a given directory and extracts
their Google Doc IDs to generate markdown-formatted links.

Usage:
    extract_gdoc_map.py --input_dir INPUT_DIR [--output_file OUTPUT_FILE] [--style {full_path,default}]

Example:
    extract_gdoc_map.py --input_dir "/path/to/google/drive"
    extract_gdoc_map.py --input_dir "/path/to/google/drive" --output_file "doc_links.md" --style full_path

Import as:

import dev_scripts_helpers.documentation.extract_gdoc_map as dsdoexgm
"""

import argparse
import json
import logging
import os
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _extract_doc_info(file_path: str) -> Tuple[str, str]:
    """
    Extract Google Doc ID from a .gdoc file.

    :param file_path: path to the .gdoc file
    :return: tuple of (file_path, doc_id)
    """
    _LOG.debug("Reading file: %s", file_path)
    # Read file content.
    content = hio.from_file(file_path)
    content = content.strip()
    # Parse JSON content.
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        _LOG.warning("Failed to parse JSON in %s: %s", file_path, e)
        return file_path, ""
    # Extract doc_id.
    doc_id = data.get("doc_id", "")
    if not doc_id:
        _LOG.warning("No doc_id found in %s", file_path)
    return file_path, doc_id


def _find_gdoc_files(input_dir: str) -> List[str]:
    """
    Find all .gdoc files in the given directory.

    :param input_dir: directory to search for .gdoc files
    :return: list of full paths to .gdoc files
    """
    hdbg.dassert_dir_exists(input_dir)
    _LOG.info("Searching for .gdoc files in: %s", input_dir)
    # Find all .gdoc files recursively.
    gdoc_files = hio.listdir(
        input_dir,
        pattern="*.gdoc",
        only_files=True,
        use_relative_paths=False,
    )
    _LOG.info("Found %d .gdoc files", len(gdoc_files))
    return gdoc_files


def _generate_doc_links_full_path(
    gdoc_files: List[str],
    input_dir: str,
) -> str:
    """
    Generate markdown links with full path in link text.

    :param gdoc_files: list of paths to .gdoc files
    :param input_dir: base directory for computing relative paths
    :return: markdown-formatted text with links
    """
    lines = []
    # Process each file.
    for file_path in gdoc_files:
        file_path_str, doc_id = _extract_doc_info(file_path)
        if doc_id:
            # Get relative path from input_dir.
            rel_path = os.path.relpath(file_path_str, input_dir)
            # Get the filename without extension.
            base_name = os.path.basename(file_path_str)
            base_name = base_name.replace(".gdoc", "")
            # Format: - [full_path/filename.gdoc/filename](URL).
            link_text = f"{rel_path}/{base_name}"
            # Generate markdown link.
            google_doc_url = f"https://docs.google.com/document/d/{doc_id}"
            link = f"- [{link_text}]({google_doc_url})"
            lines.append(link)
            # Also log to console.
            _LOG.info("%s -> %s", file_path_str, google_doc_url)
    content = "\n".join(lines)
    return content


def _generate_doc_links_default(
    gdoc_files: List[str],
    input_dir: str,
) -> str:
    """
    Generate markdown links with directory and filename separated.

    Format: Full path to .gdoc file as bullet, filename as indented sub-bullet.

    :param gdoc_files: list of paths to .gdoc files
    :param input_dir: base directory for computing relative paths
    :return: markdown-formatted text with links
    """
    lines = []
    # Process each file.
    for file_path in gdoc_files:
        file_path_str, doc_id = _extract_doc_info(file_path)
        if doc_id:
            # Get relative path from input_dir (includes .gdoc filename).
            rel_path = os.path.relpath(file_path_str, input_dir)
            # Get the filename without extension.
            base_name = os.path.basename(file_path_str)
            base_name = base_name.replace(".gdoc", "")
            # Generate markdown link URL.
            google_doc_url = f"https://docs.google.com/document/d/{doc_id}"
            # Add full path as main bullet.
            lines.append(f"- {rel_path}")
            # Add filename as indented sub-bullet with link.
            link = f"  - [{base_name}]({google_doc_url})"
            lines.append(link)
            # Also log to console.
            _LOG.info("%s -> %s", file_path_str, google_doc_url)
    content = "\n".join(lines)
    return content


def _generate_doc_links(
    gdoc_files: List[str],
    input_dir: str,
    *,
    style: str = "default",
) -> str:
    """
    Generate markdown-formatted links for Google Docs.

    :param gdoc_files: list of paths to .gdoc files
    :param input_dir: base directory for computing relative paths
    :param style: output style - 'full_path' shows full path in link text,
        'default' separates directory from filename
    :return: markdown-formatted text with links
    """
    hdbg.dassert_in(style, ["full_path", "default"])
    if style == "full_path":
        return _generate_doc_links_full_path(gdoc_files, input_dir)
    elif style == "default":
        return _generate_doc_links_default(gdoc_files, input_dir)


def extract_gdoc_map(
    input_dir: str,
    *,
    output_file: str = "",
    style: str = "default",
) -> str:
    """
    Extract Google Doc links from .gdoc files in a directory.

    :param input_dir: directory containing .gdoc files
    :param output_file: optional output file path to save results
    :param style: output style - 'full_path' or 'default'
    :return: markdown-formatted content with Google Doc links
    """
    # Find all .gdoc files.
    gdoc_files = _find_gdoc_files(input_dir)
    if not gdoc_files:
        _LOG.warning("No .gdoc files found in %s", input_dir)
        return ""
    # Generate markdown links.
    content = _generate_doc_links(gdoc_files, input_dir, style=style)
    # Write to file if output_file is provided.
    if output_file:
        hio.to_file(output_file, content)
        _LOG.info("Output written to: %s", output_file)
    return content


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        action="store",
        required=True,
        help="Directory containing .gdoc files",
    )
    parser.add_argument(
        "--output_file",
        action="store",
        default="",
        help="Optional output file path to save results (default: print to console)",
    )
    parser.add_argument(
        "--style",
        action="store",
        choices=["full_path", "default"],
        default="default",
        help="Output style: 'full_path' shows full path in link text, 'default' separates directory from filename (default: default)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Extract Google Doc links.
    content = extract_gdoc_map(
        args.input_dir,
        output_file=args.output_file,
        style=args.style,
    )
    # Print to console if no output file specified.
    if not args.output_file and content:
        _LOG.info("\n%s", content)


if __name__ == "__main__":
    _main(_parse())
