#!/usr/bin/env python

"""
Run tree command on directories and summarize with LLM.

This script processes directories by generating tree output and creating AI summaries.
It supports selective action execution and custom output locations.

Workflow:
1. Runs 'tree --dirsfirst -n -F --charset unicode' on each directory in alphabetical order
2. Creates 'tree_NUM.txt' files with the tree output
3. Runs 'llm -m gpt-4o-mini -f log.txt "Summarize this into 5 bullets"' on each
4. Saves the LLM output to 'llm_NUM.txt' files

Actions can be selectively skipped using --skip_action or --action flags.
Use --out_dir to organize output files in a dedicated directory.
Use --llm_prompt to customize the AI analysis with your own prompt file.
Use --from_scratch to delete the output directory before processing.

Basic usage:
> run_tree_and_llm.py --in_dir /path/to/process
> run_tree_and_llm.py --in_dir /path/to/analyze --out_dir results

Action control:
> run_tree_and_llm.py --in_dir /path/to/process --all
> run_tree_and_llm.py --in_dir /path/to/process --skip_action tree
> run_tree_and_llm.py --in_dir /path/to/process --action llm
> run_tree_and_llm.py --in_dir /path/to/process --action tree

Custom prompts and output:
> run_tree_and_llm.py --in_dir /path/to/process --llm_prompt my_prompt.txt
> run_tree_and_llm.py --in_dir /path/to/process --out_dir analysis --log_file custom.log
> run_tree_and_llm.py --in_dir /path/to/process --llm_prompt detailed_analysis.txt --out_dir reports

# Full processing with custom settings
> run_tree_and_llm.py --in_dir /projects/code --out_dir analysis --llm_prompt analysis_prompt.txt --log_file process.log

Range limiting:
# Process only the first 3 directories (1st to 3rd)
> run_tree_and_llm.py --in_dir /path/to/process --limit 1:3

Clean processing:
# Start fresh by deleting existing output directory
> run_tree_and_llm.py --in_dir /path/to/process --from_scratch
"""

import argparse
import logging
import os
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Actions
# #############################################################################

_ACTION_TREE = "tree"
_ACTION_LLM = "llm"
_VALID_ACTIONS = [_ACTION_TREE, _ACTION_LLM]
_DEFAULT_ACTIONS = [_ACTION_TREE, _ACTION_LLM]

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--in_dir",
        action="store",
        default=".",
        help="Directory containing subdirectories to process (default: current directory)",
    )
    parser.add_argument(
        "--log_file",
        action="store",
        default="log.txt",
        help="Log file for LLM processing (default: log.txt)",
    )
    parser.add_argument(
        "--out_dir",
        action="store",
        default="tmp.run_tree_and_llm",
        help="Directory to save output files (default: current directory)",
    )
    parser.add_argument(
        "--llm_prompt",
        action="store",
        help="File containing LLM prompt or use default prompt if not specified",
    )
    # TODO(ai): Factor out as a function in hparser like for --action.
    parser.add_argument(
        "--limit",
        action="store",
        help="Limit processing to directory range X:Y (1-indexed, inclusive)",
    )
    parser.add_argument(
        "--from_scratch",
        action="store_true",
        help="Delete the output directory before processing",
    )
    # Add actions arguments.
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _check_system_requirements() -> None:
    """
    Check that that required commands exist.
    """
    # Check for tree command.
    hsystem.system("which tree", suppress_output=True)
    _LOG.debug("tree command found")
    # Check for llm command.
    hsystem.system("which llm", suppress_output=True)
    _LOG.debug("llm command found")


# TODO(ai): Factor out as a function in hparser like for --action.
def _parse_limit_range(limit_str: str) -> Tuple[int, int]:
    """
    Parse limit string in format "X:Y" and return tuple (start, end).
    
    :param limit_str: string in format "X:Y" where X and Y are 1-indexed integers
    :return: tuple of (start_index, end_index) as 0-indexed integers
    """
    hdbg.dassert(":" in limit_str, "Limit format must be X:Y, got: %s", limit_str)
    parts = limit_str.split(":")
    hdbg.dassert_eq(len(parts), 2, "Limit format must be X:Y, got: %s", limit_str)
    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError as e:
        hdbg.dfatal("Invalid limit format, must be integers: %s", e)
    hdbg.dassert_lt(0, start, "Start index must be >= 1, got: %s", start)
    hdbg.dassert_lt(0, end, "End index must be >= 1, got: %s", end)
    hdbg.dassert_lte(start, end, "Start index must be <= end index, got: %s:%s", start, end)
    # Convert to 0-indexed.
    return start - 1, end - 1


def _get_directories(in_dir: str, *, limit_range: Optional[Tuple[int, int]] = None) -> List[str]:
    """
    Get all directories in in_dir sorted alphabetically.

    :param in_dir: directory to scan
    :param limit_range: optional tuple (start, end) for 0-indexed range filtering
    :return: sorted list of directory paths
    """
    hdbg.dassert(
        os.path.isdir(in_dir),
        "Input directory does not exist: %s", in_dir,
    )
    directories = []
    # Get all items in input directory.
    items = os.listdir(in_dir)
    # Filter for directories only.
    for item in items:
        full_path = os.path.join(in_dir, item)
        if os.path.isdir(full_path):
            directories.append(full_path)
    # Sort alphabetically.
    directories.sort()
    # TODO(ai): Factor out as a function in hparser like for --action.
    # Apply limit range if specified.
    if limit_range is not None:
        start_idx, end_idx = limit_range
        total_dirs = len(directories)
        hdbg.dassert_lt(start_idx, total_dirs, "Start index %s exceeds available directories %s", start_idx + 1, total_dirs)
        hdbg.dassert_lt(end_idx, total_dirs, "End index %s exceeds available directories %s", end_idx + 1, total_dirs)
        directories = directories[start_idx:end_idx + 1]
        _LOG.warning("Found %s directories, limited to range %s:%s (%s directories)", total_dirs, start_idx + 1, end_idx + 1, len(directories))
    else:
        _LOG.info("Found %s directories to process", len(directories))
    return directories


def _run_tree_on_directory(directory: str, output_file: str) -> None:
    """
    Run tree command on a directory and save output to file.

    :param directory: directory to run tree on
    :param output_file: file to save tree output
    """
    _LOG.debug("Running tree on directory: %s", directory)
    tree_cmd = f'tree --dirsfirst -n -F --charset unicode "{directory}"'
    # Run tree command and capture output.
    rc, output = hsystem.system_to_string(tree_cmd)
    hdbg.dassert_eq(rc, 0, "tree command failed on %s", directory)
    # Write output to file.
    hio.to_file(output_file, output)
    _LOG.info("Tree output saved to: %s", output_file)


def _run_llm_on_file(
    input_file: str,
    output_file: str,
    log_file: str,
    *,
    llm_prompt_file: Optional[str] = None,
) -> None:
    """
    Run LLM command on input file and save summary to output file.

    :param input_file: file to process with LLM
    :param output_file: file to save LLM summary
    :param log_file: log file for LLM processing
    :param llm_prompt_file: optional file containing LLM prompt
    """
    _LOG.debug("Running LLM on file: %s", input_file)
    # Copy input file to log file for LLM processing.
    content = hio.from_file(input_file)
    hio.to_file(log_file, content)
    # Determine prompt to use.
    if llm_prompt_file:
        hdbg.dassert(
            os.path.isfile(llm_prompt_file),
            "Prompt file does not exist: %s", llm_prompt_file,
        )
        prompt = hio.from_file(llm_prompt_file).strip()
        _LOG.debug("Using custom prompt from file: %s", llm_prompt_file)
    else:
        prompt = r"""
For each directory add a short comment about its content
Include a comment about the entire directory as a whole

- Only directories should have a comment
- Do not comment single files, such as:
  (outdated) Causify Executive Manual - v2.0.gdoc

The output is a bulleted markdown like:
# DIR_NAME
- **Overall Directory Comment:**
  - This directory serves as a comprehensive resource for Causify, such as
    - Workplace processes
    - Employee information
    - Operational tools
    - Templates

- **Causify Process/**
  - Contains draft versions of
    - Company policies and procedures
    - Including HR processes
    - Invoicing
    - Vendor risk management

- **EOS Causify/**
  - Strategic planning materials based on the Entrepreneurial Operating System
    (EOS) framework.

- **Team Bios/**
  - Collection of employee bios and Predictive Index assessments
  - It serves as a people directory and HR resource

- **Templates/**
  - Repository of standardized forms (Google Forms) for surveys, invoicing, and
    financial transactions.

- **Tools/**
  - Draft documentation of conventions and best practices for the team’s daily
    collaboration tools, e.g.,
    - Asana
    - GitHub
    - Google Docs
    - Slack
    - Meetings
"""
        _LOG.debug("Using default prompt")
    # Run LLM command.
    # Use printf to avoid bash interpretation issues with hyphens in prompt.
    escaped_prompt = prompt.replace("'", "'\"'\"'")  # Escape single quotes
    llm_cmd = f"printf '%s' '{escaped_prompt}' | llm -m gpt-4o-mini -f \"{log_file}\""
    rc, output = hsystem.system_to_string(llm_cmd, abort_on_error=True)
    # Write LLM output to file.
    hio.to_file(output_file, output)
    _LOG.info("LLM summary saved to: %s", output_file)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Get the selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Check system requirements.
    _check_system_requirements()
    # TODO(ai): Factor out as a function in hparser like for --action.
    # Parse limit range if specified.
    limit_range = None
    if args.limit:
        limit_range = _parse_limit_range(args.limit)
        _LOG.info("Using limit range: %s (0-indexed: %s:%s)", args.limit, limit_range[0], limit_range[1])
    # Get directories to process.
    directories = _get_directories(args.in_dir, limit_range=limit_range)
    hdbg.dassert_lt(0, len(directories), "No directories found to process")
    # Handle output directory.
    if args.from_scratch:
        if os.path.exists(args.out_dir):
            _LOG.warning("Deleting existing output directory: %s", args.out_dir)
            hsystem.system(f'rm -rf "{args.out_dir}"')
    # Create output directory if it doesn't exist.
    hio.create_dir(args.out_dir, incremental=True)
    # Process each directory.
    for i, directory in enumerate(directories, 1):
        _LOG.info(
            "Processing directory %s/%s: %s", i, len(directories), os.path.basename(directory)
        )
        # Create filenames with output directory.
        tree_file = os.path.join(args.out_dir, f"tree_{i:03d}.txt")
        llm_file = os.path.join(args.out_dir, f"llm_{i:03d}.txt")
        log_file = os.path.join(args.out_dir, args.log_file)
        # Run tree command if action is selected.
        if _ACTION_TREE in actions:
            _run_tree_on_directory(directory, tree_file)
        else:
            _LOG.info(
                "Skipping tree collection for: %s", os.path.basename(directory)
            )
        # Run LLM command if action is selected and tree file exists.
        if _ACTION_LLM in actions:
            if os.path.isfile(tree_file):
                _run_llm_on_file(
                    tree_file, llm_file, log_file, llm_prompt_file=args.llm_prompt
                )
            else:
                _LOG.warning(
                    "Tree file %s does not exist, skipping LLM processing", tree_file
                )
        else:
            _LOG.info(
                "Skipping LLM processing for: %s", os.path.basename(directory)
            )
    _LOG.info("Completed processing %s directories", len(directories))


if __name__ == "__main__":
    _main(_parse())
