#!/usr/bin/env python3

"""
Process all Lesson* files in input directory and generate summaries and
projects.

This script finds all Lesson* files in the input directory and calls:
1. create_markdown_summary.py to create summaries
2. create_class_projects.py to create projects

The output files are generated in the specified output directory.

Examples:
> generate_all_projects.py --input_dir ~/src/umd_msml6101/msml610/lectures_source --output_dir ~/output
> generate_all_projects.py --input_dir . --output_dir ./results --max_num_bullets 5

Import as:

import generate_all_projects as geallpr
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

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
        "--input_dir",
        required=True,
        help="Input directory containing Lesson* files",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--max_num_bullets",
        type=int,
        default=3,
        help="Maximum number of bullets for summaries (default: 3)",
    )
    parser.add_argument(
        "--use_library",
        action="store_true",
        help="Use library instead of command line llm tool",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def find_lesson_files(input_dir: str) -> List[str]:
    """
    Find all Lesson* files in the input directory.

    :param input_dir: Directory to search for Lesson* files
    :return: List of full paths to Lesson* files
    """
    hdbg.dassert(
        os.path.isdir(input_dir), f"Directory does not exist: {input_dir}"
    )
    lesson_files = []
    for filename in os.listdir(input_dir):
        if filename.startswith("Lesson") and filename.endswith(".txt"):
            full_path = os.path.join(input_dir, filename)
            lesson_files.append(full_path)
    lesson_files.sort()
    _LOG.info("Found %s Lesson* files: %s", len(lesson_files), lesson_files)
    return lesson_files


def generate_summary(
    in_file: str,
    output_dir: str,
    max_num_bullets: int,
    use_library: bool,
) -> str:
    """
    Generate summary for a lesson file using create_markdown_summary.py.

    :param in_file: Input lesson file path
    :param output_dir: Output directory
    :param max_num_bullets: Maximum number of bullets
    :param use_library: Whether to use library instead of CLI
    :return: Path to generated summary file
    """
    # Extract base filename for output
    base_name = os.path.splitext(os.path.basename(in_file))[0]
    out_file = os.path.join(output_dir, f"{base_name}.summary.txt")

    # Build command
    cmd_parts = [
        "python",
        "create_markdown_summary.py",
        "--in_file",
        in_file,
        "--action",
        "summarize",
        "--out_file",
        out_file,
        "--max_num_bullets",
        str(max_num_bullets),
    ]

    if use_library:
        cmd_parts.append("--use_library")

    cmd = " ".join(cmd_parts)
    _LOG.info("Running summary command: %s", cmd)

    # Execute command
    ret_code = hsystem.system(cmd)
    hdbg.dassert_eq(ret_code, 0, f"Summary command failed: {cmd}")

    return out_file


def generate_projects(in_file: str, output_dir: str) -> str:
    """
    Generate projects for a lesson file using create_class_projects.py.

    :param in_file: Input lesson file path
    :param output_dir: Output directory
    :return: Path to generated projects file
    """
    # Extract base filename for output
    base_name = os.path.splitext(os.path.basename(in_file))[0]
    out_file = os.path.join(output_dir, f"{base_name}.projects.txt")
    # Build command
    cmd = (
        f"python create_class_projects.py "
        f"--in_file {in_file} "
        f"--action create_project "
        f"--out_file {out_file}"
    )
    _LOG.info("Running projects command: %s", cmd)
    # Execute command
    ret_code = hsystem.system(cmd)
    hdbg.dassert_eq(ret_code, 0, f"Projects command failed: {cmd}")
    return out_file


def process_all_lessons(
    input_dir: str,
    output_dir: str,
    max_num_bullets: int,
    use_library: bool,
) -> None:
    """
    Process all Lesson* files in input directory.

    :param input_dir: Input directory containing Lesson* files
    :param output_dir: Output directory for generated files
    :param max_num_bullets: Maximum number of bullets for summaries
    :param use_library: Whether to use library instead of CLI
    """
    # Create output directory if it doesn't exist
    hio.create_dir(output_dir, incremental=True)

    # Find all lesson files
    lesson_files = find_lesson_files(input_dir)

    if not lesson_files:
        _LOG.warning("No Lesson* files found in %s", input_dir)
        return

    # Process each lesson file
    for lesson_file in lesson_files:
        _LOG.info("Processing %s", lesson_file)

        try:
            # Generate summary
            summary_file = generate_summary(
                lesson_file, output_dir, max_num_bullets, use_library
            )
            _LOG.info("Generated summary: %s", summary_file)

            # Generate projects
            projects_file = generate_projects(lesson_file, output_dir)
            _LOG.info("Generated projects: %s", projects_file)

        except Exception as e:
            _LOG.error("Failed to process %s: %s", lesson_file, e)
            raise


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    # Validate input directory
    if not os.path.isdir(args.input_dir):
        raise ValueError(f"Input directory does not exist: {args.input_dir}")
    # Process all lessons
    process_all_lessons(
        args.input_dir,
        args.output_dir,
        args.max_num_bullets,
        args.use_library,
    )
    _LOG.info("All lesson files processed successfully")


if __name__ == "__main__":
    _main(_parse())
