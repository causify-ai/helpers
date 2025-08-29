#!/usr/bin/env python

"""
Run tree command on directories and summarize with LLM.

Run tree command on directories and summarize with LLM.

This script:
1. Runs 'tree --dirsfirst -n -F --charset unicode' on each directory in alphabetical order
2. Creates 'dir_NUM.txt' files with the tree output  
3. Runs 'llm -m gpt-4o-mini -f log.txt "Summarize this into 5 bullets"' on each
4. Saves the LLM output to 'out_NUM.txt' files

Actions can be selectively skipped using --skip_action or --action flags.

Example usage:
    python run_tree_and_llm.py --target_dir /path/to/process
    python run_tree_and_llm.py --target_dir /path/to/process --skip_action tree
    python run_tree_and_llm.py --target_dir /path/to/process --action llm
"""

import argparse
import logging
import os
import platform
from typing import List, Optional

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
        "--target_dir",
        action="store",
        default=".",
        help="Directory containing subdirectories to process (default: current directory)"
    )
    parser.add_argument(
        "--log_file", 
        action="store", 
        default="log.txt",
        help="Log file for LLM processing (default: log.txt)"
    )
    parser.add_argument(
        "--out_dir",
        action="store",
        default=".",
        help="Directory to save output files (default: current directory)"
    )
    parser.add_argument(
        "--llm_prompt",
        action="store",
        help="File containing LLM prompt or use default prompt if not specified"
    )
    # Add actions arguments.
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _check_system_requirements() -> None:
    """
    Check that we're running on Linux and that required commands exist.
    """
    # Check for tree command.
    hsystem.system("which tree", suppress_output=True)
    _LOG.debug("tree command found")
    # Check for llm command.
    hsystem.system("which llm", suppress_output=True)
    _LOG.debug("llm command found")


def _get_directories(target_dir: str) -> List[str]:
    """
    Get all directories in target_dir sorted alphabetically.
    
    :param target_dir: directory to scan
    :return: sorted list of directory paths
    """
    hdbg.dassert(os.path.isdir(target_dir), f"Target directory does not exist: {target_dir}")
    directories = []
    # Get all items in target directory.
    try:
        items = os.listdir(target_dir)
    except OSError as e:
        hdbg.dfatal(f"Cannot list directory {target_dir}: {e}")
    # Filter for directories only.
    for item in items:
        full_path = os.path.join(target_dir, item)
        if os.path.isdir(full_path):
            directories.append(full_path)
    # Sort alphabetically.
    directories.sort()
    _LOG.info(f"Found {len(directories)} directories to process")
    return directories


def _run_tree_on_directory(directory: str, output_file: str) -> None:
    """
    Run tree command on a directory and save output to file.
    
    :param directory: directory to run tree on
    :param output_file: file to save tree output
    """
    _LOG.debug(f"Running tree on directory: {directory}")
    tree_cmd = f'tree --dirsfirst -n -F --charset unicode "{directory}"'
    # Run tree command and capture output.
    rc, output = hsystem.system_to_string(tree_cmd)
    hdbg.dassert_eq(rc, 0, f"tree command failed on {directory}")
    # Write output to file.
    hio.to_file(output_file, output)
    _LOG.info(f"Tree output saved to: {output_file}")


def _run_llm_on_file(input_file: str, output_file: str, log_file: str, *, llm_prompt_file: Optional[str] = None) -> None:
    """
    Run LLM command on input file and save summary to output file.
    
    :param input_file: file to process with LLM
    :param output_file: file to save LLM summary
    :param log_file: log file for LLM processing
    :param llm_prompt_file: optional file containing LLM prompt
    """
    _LOG.debug(f"Running LLM on file: {input_file}")
    # Copy input file to log file for LLM processing.
    content = hio.from_file(input_file)
    hio.to_file(log_file, content)
    # Determine prompt to use.
    if llm_prompt_file:
        hdbg.dassert(os.path.isfile(llm_prompt_file), f"Prompt file does not exist: {llm_prompt_file}")
        prompt = hio.from_file(llm_prompt_file).strip()
        _LOG.debug(f"Using custom prompt from file: {llm_prompt_file}")
    else:
        prompt = "Summarize this into 5 bullets"
        _LOG.debug("Using default prompt")
    # Run LLM command.
    llm_cmd = f'llm -m gpt-4o-mini -f "{log_file}" "{prompt}"'
    rc, output = hsystem.system_to_string(llm_cmd)
    hdbg.dassert_eq(rc, 0, f"LLM command failed on {input_file}")
    # Write LLM output to file.
    hio.to_file(output_file, output)
    _LOG.info(f"LLM summary saved to: {output_file}")


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Get the selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info(f"Selected actions: {actions}")
    # Check system requirements.
    _check_system_requirements()
    # Get directories to process.
    directories = _get_directories(args.target_dir)
    hdbg.dassert_lt(0, len(directories), "No directories found to process")
    # Create output directory if it doesn't exist.
    hio.create_dir(args.out_dir, incremental=False)
    # Process each directory.
    for i, directory in enumerate(directories, 1):
        _LOG.info(f"Processing directory {i}/{len(directories)}: {os.path.basename(directory)}")
        # Create filenames with output directory.
        dir_file = os.path.join(args.out_dir, f"dir_{i:03d}.txt")
        out_file = os.path.join(args.out_dir, f"out_{i:03d}.txt")
        log_file = os.path.join(args.out_dir, args.log_file)
        # Run tree command if action is selected.
        if _ACTION_TREE in actions:
            _run_tree_on_directory(directory, dir_file)
        else:
            _LOG.info(f"Skipping tree collection for: {os.path.basename(directory)}")
        # Run LLM command if action is selected and tree file exists.
        if _ACTION_LLM in actions:
            if os.path.isfile(dir_file):
                _run_llm_on_file(dir_file, out_file, log_file, llm_prompt_file=args.llm_prompt)
            else:
                _LOG.warning(f"Tree file {dir_file} does not exist, skipping LLM processing")
        else:
            _LOG.info(f"Skipping LLM processing for: {os.path.basename(directory)}")
    _LOG.info(f"Completed processing {len(directories)} directories")


if __name__ == "__main__":
    _main(_parse())
