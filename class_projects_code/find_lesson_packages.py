#!/usr/bin/env python3

"""
Script to find Python packages related to lesson content.

The script processes markdown files to find 5 Python packages related to the lesson content.

Example:
> find_lesson_packages.py --in_file input.md --output_file packages.md
"""

import argparse
import logging
import os

import class_project_utils as cutil
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--in_file",
        required=True,
        help="Input markdown file path",
    )
    parser.add_argument(
        "--output_file",
        help="Output file for results",
    )
    hparser.add_verbosity_arg(parser)
    return parser




def find_packages(in_file: str, output_file: str = None) -> str:
    """
    Find packages related to the lesson content.

    :param in_file: Input markdown file path
    :param output_file: Output file path (optional)
    :return: Generated package suggestions as string
    """
    _LOG.info("Starting find_packages for file: %s", in_file)
    # Read input file directly.
    hdbg.dassert_file_exists(in_file)
    file_content = hio.from_file(in_file)
    # Use the entire file content to find related packages.
    _LOG.info("Processing entire file content to find packages")
    # Generate package suggestions for entire file content.
    result_lines = []
    _LOG.debug("Finding packages for entire file")
    prompt = """
    You are a college level data science professor.

    Given the markdown for a lecture, come up with the description of 5 Python
    free packages that relate to the content of the lesson.

    The output must follow the template with information about the package like
    - Package:
    - Description:
    - Website:
    - Documentation:

    Avoid long texts or steps and comments, just list the packages
    """
    prompt = hprint.dedent(prompt)
    packages = cutil.call_llm(prompt, file_content)
    result_lines.append("# Related Python Packages")
    result_lines.append(packages)
    result_lines.append("")  # Empty line for spacing.
    
    result_content = "\n".join(result_lines)
    
    # Save result to output file if specified.
    if output_file:
        hio.to_file(output_file, result_content)
        _LOG.info("Package suggestions saved to: %s", output_file)
    
    return result_content


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to execute the script.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate inputs.
    hdbg.dassert_file_exists(args.in_file)
    # Check LLM availability.
    cutil.check_llm_available()
    
    # Generate default output file if not specified.
    output_file = args.output_file
    if not output_file:
        base_name = os.path.splitext(os.path.basename(args.in_file))[0]
        output_file = f"{base_name}.packages.txt"
    
    # Execute find_packages.
    find_packages(args.in_file, output_file)


if __name__ == "__main__":
    _main(_parse())