#!/usr/bin/env python3

"""
Process all Lesson* files in input directory and generate summaries and
projects.

This script finds all Lesson* files in the input directory and executes the
following workflow:
1. create_markdown_summary.py to create summaries
2. find_lesson_packages.py to find relevant Python packages (using summaries)
3. create_lesson_project.py to create projects (using summaries and packages)

The output files are generated in the specified output directory.

Examples:
> create_all_class_projects.py --input_dir ~/src/umd_msml6101/msml610/lectures_source --output_dir ~/output
> create_all_class_projects.py --input_dir . --output_dir ./results --action generate_summary
> create_all_class_projects.py --input_dir ~/lectures --output_dir ~/output --limit 1:5

Import as:

import create_all_class_projects as crallcpro
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

# Hardwired configuration constants
_MAX_NUM_BULLETS = 3
_USE_LIBRARY = False
_LEVEL = 2


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
        "--from_scratch",
        action="store_true",
        help="Create output directory from scratch (remove if exists)",
    )
    parser.add_argument(
        "--action",
        choices=["generate_summary", "generate_projects", "both"],
        default="both",
        help="Action to perform: generate_summary, generate_projects, or both (default: both)",
    )
    hparser.add_limit_range_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _find_lesson_files(input_dir: str, *, limit_range=None) -> List[str]:
    """
    Find all Lesson* files in the input directory.

    :param input_dir: Directory to search for Lesson* files
    :param limit_range: Optional tuple (start, end) for 0-indexed range
        filtering
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
    # Apply limit range if specified.
    lesson_files = hparser.apply_limit_range(
        lesson_files, limit_range, item_name="lesson files"
    )
    return lesson_files


def _generate_summary(
    in_file: str,
    output_dir: str,
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
    # Check if output file already exists.
    if os.path.exists(out_file):
        _LOG.warning("Output file already exists, skipping: %s", out_file)
        return out_file
    # Build command using f-string
    library_flag = "--use_library" if _USE_LIBRARY else ""
    cmd = (
        f"create_markdown_summary.py "
        f"--in_file {in_file} "
        f"--action summarize "
        f"--max_level {_LEVEL} "
        f"--out_file {out_file} "
        f"--max_num_bullets {_MAX_NUM_BULLETS} "
        f"{library_flag}"
    ).strip()
    _LOG.info("Running summary command: %s", cmd)
    # Execute command
    ret_code = hsystem.system(cmd)
    hdbg.dassert_eq(ret_code, 0, f"Summary command failed: {cmd}")
    return out_file


def _find_packages(in_file: str, output_dir: str) -> str:
    """
    Find packages for a lesson file using find_lesson_packages.py.

    :param in_file: Input lesson file path
    :param output_dir: Output directory
    :return: Path to generated packages file
    """
    # Extract base filename for output
    base_name = os.path.splitext(os.path.basename(in_file))[0]
    out_file = os.path.join(output_dir, f"{base_name}.packages.txt")
    # Check if output file already exists.
    if os.path.exists(out_file):
        _LOG.warning("Output file already exists, skipping: %s", out_file)
        return out_file
    # Build command
    cmd = (
        f"find_lesson_packages.py "
        f"--in_file {in_file} "
        f"--output_file {out_file}"
    )
    _LOG.info("Running find packages command: %s", cmd)
    # Execute command
    ret_code = hsystem.system(cmd)
    hdbg.dassert_eq(ret_code, 0, f"Find packages command failed: {cmd}")
    return out_file


def _generate_projects(in_file: str, output_dir: str, packages_file: str) -> List[str]:
    """
    Generate projects for a lesson file using create_lesson_project.py.

    Creates 3 separate project files for each lesson file, one for each
    difficulty level (easy, medium, hard).

    :param in_file: Input lesson file path
    :param output_dir: Output directory
    :param packages_file: Path to packages file generated by find_lesson_packages
    :return: List of paths to generated projects files
    """
    # Extract base filename for output.
    base_name = os.path.splitext(os.path.basename(in_file))[0]
    # Define difficulty levels.
    difficulty_levels = ["easy", "medium", "hard"]
    generated_files = []
    # Generate projects for each difficulty level.
    for level in difficulty_levels:
        out_file = os.path.join(output_dir, f"{base_name}.projects.{level}.txt")
        # Check if output file already exists.
        if os.path.exists(out_file):
            _LOG.warning("Output file already exists, skipping: %s", out_file)
            generated_files.append(out_file)
            continue
        # Build command.
        cmd = (
            f"create_lesson_project.py "
            f"--in_file {in_file} "
            f"--action create_project "
            f"--level {level} "
            f"--output_file {out_file} "
            f"--packages_file {packages_file}"
        )
        _LOG.info("Running projects command: %s", cmd)
        # Execute command.
        ret_code = hsystem.system(cmd)
        hdbg.dassert_eq(ret_code, 0, f"Projects command failed: {cmd}")
        generated_files.append(out_file)
    return generated_files


def _process_all_lessons(
    input_dir: str,
    output_dir: str,
    from_scratch: bool,
    action: str,
    *,
    limit_range=None,
) -> None:
    """
    Process all Lesson* files in input directory.

    :param input_dir: Input directory containing Lesson* files
    :param output_dir: Output directory for generated files
    :param from_scratch: Whether to create output directory from scratch
    :param action: Action to perform (generate_summary,
        generate_projects, or both)
    :param limit_range: Optional tuple (start, end) for 0-indexed range
        filtering
    """
    # Create output directory.
    hio.create_dir(output_dir, incremental=not from_scratch)
    # Find all lesson files.
    lesson_files = _find_lesson_files(input_dir, limit_range=limit_range)
    hdbg.dassert_ne(
        len(lesson_files), 0, f"No Lesson* files found in {input_dir}"
    )
    # Process each lesson file
    # TODO(ai): Add a progress bar.
    for lesson_file in lesson_files:
        _LOG.info("Processing %s", lesson_file)
        
        # Step 1: Generate summary (always needed for the new flow)
        if action in ["generate_summary", "both"]:
            summary_file = _generate_summary(lesson_file, output_dir)
            _LOG.info("Generated summary: %s", summary_file)
        elif action == "generate_projects":
            # Even for projects only, we need the summary first
            base_name = os.path.splitext(os.path.basename(lesson_file))[0]
            summary_file = os.path.join(output_dir, f"{base_name}.summary.txt")
            if not os.path.exists(summary_file):
                summary_file = _generate_summary(lesson_file, output_dir)
                _LOG.info("Generated summary (required for projects): %s", summary_file)
        
        # Step 2 & 3: Find packages and generate projects
        if action in ["generate_projects", "both"]:
            # Find packages using the summary file.
            packages_file = _find_packages(summary_file, output_dir)
            _LOG.info("Generated packages: %s", packages_file)
            # Generate projects using the summary file and packages file.
            projects_files = _generate_projects(
                summary_file, 
                output_dir, 
                packages_file
            )
            _LOG.info("Generated projects: %s", ", ".join(projects_files))


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    # Validate input directory
    hdbg.dassert_dir_exists(args.input_dir)
    # Parse limit range if specified.
    limit_range = hparser.parse_limit_range_args(args)
    # Process all lessons
    _process_all_lessons(
        args.input_dir,
        args.output_dir,
        args.from_scratch,
        args.action,
        limit_range=limit_range,
    )
    _LOG.info("All lesson files processed successfully")


if __name__ == "__main__":
    _main(_parse())
