#!/usr/bin/env python
"""
Dockerized DOCX-to-Markdown Converter Template.

This script converts a DOCX file to Markdown using a Dockerized pandoc environment.
It is intended as a template to explain the process.

Usage Instructions:

  1. In your working directory, ensure you have your DOCX file ready (e.g., my_document.docx).
     Then run the script with the appropriate arguments. For example:
       dev_scripts_helpers/dockerize/dockerized_template/dockerized_template.py \
           --docx_file my_document.docx \
           --md_file my_document.md

  2. The script will:
       - Convert the input DOCX file to a Markdown file.
       - Extract any embedded media (e.g., images) into a folder derived from the Markdown file name
         (e.g., "my_document.md" -> "my_document_figs").
       - Execute pandoc within a Docker container for a consistent conversion environment.

Notes:
  - Docker-specific options (such as forcing a rebuild or using sudo) are supported via the helper functions.
  - The pandoc command is constructed to always start with the token "pandoc" to ensure proper parsing by the helper routines.
  - Any line marked with "FILL THIS LIKE:" is a placeholder that you can customize to suit your needs.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for the conversion script.

    The script expects:
      --docx_file: Path to the input DOCX file.
      --md_file:   Path to the output Markdown file.
    """
    # Create an ArgumentParser instance with the provided docstring.
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # FILL THIS LIKE: Required argument for the DOCX file (input).
    parser.add_argument(
        "--docx_file",
        required=True,
        type=str,
        help="Path to the DOCX file to convert.",
    )
    # FILL THIS LIKE: Required argument for the Markdown file (output).
    parser.add_argument(
        "--md_file",
        required=True,
        type=str,
        help="Path to the output Markdown file.",
    )
    # Add Docker-specific arguments (e.g., --dockerized_force_rebuild, --dockerized_use_sudo).
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # FILL THIS LIKE: Define folder for extracted media (e.g., images) by replacing ".md" with "_figs".
    md_file_figs = args.md_file.replace(".md", "_figs")
    _LOG.info("Converting '%s' to Markdown '%s'...", args.docx_file, args.md_file)
    # FILL THIS LIKE: Build the pandoc command. IMPORTANT: The command string must start with 'pandoc'.
    pandoc_cmd = (
        # FILL THIS LIKE: 'pandoc' executable token.
        "pandoc "
        +
        # FILL THIS LIKE: Input DOCX file.
        f"{args.docx_file} "
        +
        # FILL THIS LIKE: Flag to extract embedded media to the specified folder.
        f"--extract-media {md_file_figs} "
        +
        # FILL THIS LIKE: Conversion: input format DOCX, output format strict Markdown.
        "-f docx -t markdown_strict "
        +
        # FILL THIS LIKE: Specify output Markdown file with '-o'.
        f"-o {args.md_file}"
    )
    _LOG.debug("Pandoc command: %s", pandoc_cmd)
    # FILL THIS LIKE: Run pandoc within a Docker container using our helper function.
    # This function will handle:
    #   - Converting host file paths to Docker container paths.
    #   - Executing the command in a reproducible Docker environment.
    # hdocker.run_dockerized_pandoc(
    #     pandoc_cmd,
    #     container_type="pandoc_only",
    #     force_rebuild=args.dockerized_force_rebuild,
    #     use_sudo=args.dockerized_use_sudo,
    # )
    _LOG.info("Finished converting '%s' to '%s'.", args.docx_file, args.md_file)


if __name__ == "__main__":
    _main(_parse())
