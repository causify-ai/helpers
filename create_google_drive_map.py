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
5. Optionally combines all LLM outputs into a single markdown file
6. Optionally creates a table with directory metadata (owner, department, content)

Actions can be selectively skipped using --skip_action or --action flags.
Use --out_dir to organize output files in a dedicated directory.
Use --from_scratch to delete the output directory before processing.

Basic usage:
> create_google_drive_map.py --in_dir /path/to/process
> create_google_drive_map.py --in_dir /path/to/analyze --out_dir results

Action control:
> create_google_drive_map.py --in_dir /path/to/process --all
> create_google_drive_map.py --in_dir /path/to/process --skip_action tree
> create_google_drive_map.py --in_dir /path/to/process --action llm
> create_google_drive_map.py --in_dir /path/to/process --action tree
> create_google_drive_map.py --in_dir /path/to/process --action combine
> create_google_drive_map.py --in_dir /path/to/process --action table

Custom output:
> create_google_drive_map.py --in_dir /path/to/process --out_dir analysis
> create_google_drive_map.py --in_dir /path/to/process --out_dir reports

# Full processing with custom settings
> create_google_drive_map.py --in_dir /projects/code --out_dir analysis

# Combine existing LLM outputs into a single markdown file
> create_google_drive_map.py --in_dir /path/to/process --action combine --out_dir existing_results

# Create directory table
> create_google_drive_map.py --in_dir /path/to/process --action table --out_dir results

Range limiting:
# Process only the first 3 directories (1st to 3rd)
> create_google_drive_map.py --in_dir /path/to/process --limit 1:3

Clean processing:
# Start fresh by deleting existing output directory
> create_google_drive_map.py --in_dir /path/to/process --from_scratch
"""

import argparse
import logging
import os
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import llm
from tqdm import tqdm

_LOG = logging.getLogger(__name__)

# #############################################################################
# Actions
# #############################################################################

_ACTION_TREE = "tree"
_ACTION_LLM = "llm"
_ACTION_COMBINE = "combine"
_ACTION_TABLE = "table"
_VALID_ACTIONS = [_ACTION_TREE, _ACTION_LLM, _ACTION_COMBINE, _ACTION_TABLE]
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
        required=True,
        help="Directory containing subdirectories to process",
    )
    parser.add_argument(
        "--out_dir",
        action="store",
        default="tmp.run_tree_and_llm",
        help="Directory to save output files (default: current directory)",
    )
    # Add limit range argument.
    hparser.add_limit_range_arg(parser)
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
    # Apply limit range if specified.
    directories = hparser.apply_limit_range(directories, limit_range, item_name="directories")
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


def _create_directory_table(directories: List[str], out_dir: str) -> None:
    """
    Create a markdown table with directory information.
    
    Maps directory names to owners, departments, and content descriptions.
    
    :param directories: list of directory paths that were processed
    :param out_dir: directory to save the table file
    """
    _LOG.info("Creating directory table")
    
    # Directory mapping data.
    directory_info = {
        "All Causify": {
            "owner": "",
            "department": "General",
            "content": ""
        },
        "Archives (Vielka)": {
            "owner": "Vielka",
            "department": "General",
            "content": ""
        },
        "Causify Customers (Denis)": {
            "owner": "Denis",
            "department": "Sales",
            "content": ""
        },
        "Causify Products": {
            "owner": "",
            "department": "Product",
            "content": ""
        },
        "Compliance": {
            "owner": "Denis",
            "department": "Compliance",
            "content": ""
        },
        "Customer: BWD": {
            "owner": "Eng",
            "department": "Engineering",
            "content": ""
        },
        "Customer: Enel": {
            "owner": "Eng",
            "department": "Engineering",
            "content": ""
        },
        "Customer: Xerox": {
            "owner": "Eng",
            "department": "Engineering",
            "content": ""
        },
        "Employee-Contractor Documents": {
            "owner": "Brad",
            "department": "HR",
            "content": ""
        },
        "Eng": {
            "owner": "GP",
            "department": "Engineering",
            "content": ""
        },
        "Eng - External": {
            "owner": "GP",
            "department": "Engineering",
            "content": ""
        },
        "Eng - TO_REORG": {
            "owner": "GP",
            "department": "Engineering",
            "content": ""
        },
        "Eng - Team leaders": {
            "owner": "GP",
            "department": "Engineering",
            "content": ""
        },
        "Executive Folder": {
            "owner": "Joel",
            "department": "Executive",
            "content": ""
        },
        "Finance": {
            "owner": "Brad",
            "department": "Finance",
            "content": ""
        },
        "General": {
            "owner": "Joel",
            "department": "General",
            "content": ""
        },
        "Grants": {
            "owner": "",
            "department": "Finance",
            "content": ""
        },
        "HR": {
            "owner": "",
            "department": "HR",
            "content": ""
        },
        "Investment - TO_REORG": {
            "owner": "Joel",
            "department": "Finance",
            "content": ""
        },
        "Investor Data Room": {
            "owner": "Brad",
            "department": "Finance",
            "content": ""
        },
        "Marketing": {
            "owner": "Joel",
            "department": "Marketing",
            "content": ""
        },
        "New Market Planning": {
            "owner": "Joel",
            "department": "Strategy",
            "content": ""
        },
        "Phaseshift LTD": {
            "owner": "GP",
            "department": "Engineering",
            "content": ""
        },
        "Private": {
            "owner": "GP, Joel, Paul",
            "department": "General",
            "content": ""
        },
        "Process": {
            "owner": "GP",
            "department": "Operations",
            "content": ""
        },
        "Product: FinTech apps": {
            "owner": "Eng",
            "department": "Product",
            "content": ""
        },
        "Sales General": {
            "owner": "Joel",
            "department": "Sales",
            "content": ""
        }
    }
    
    # Start building the table.
    table_lines = []
    table_lines.append("# Directory Index\n")
    table_lines.append("## Directories to Process\n")
    
    # List directories with indices.
    for i, directory in enumerate(directories):
        table_lines.append(f"  [{i}]: {directory}")
    
    table_lines.append("\n## Directory Information\n")
    table_lines.append("| Name | Owner | Department | Content |")
    table_lines.append("| :---- | :---- | :---- | :---- |")
    
    # Process each directory.
    for i, directory in enumerate(tqdm(directories, desc="Processing directories for table"), 1):
        dir_name = os.path.basename(directory)
        
        # Try to find matching info.
        info = None
        for key in directory_info:
            # Check for exact match or partial match.
            if key in dir_name or dir_name in key:
                info = directory_info[key]
                break
        
        # If no match found, use defaults.
        if info is None:
            info = {"owner": "", "department": "", "content": ""}
        
        # Clean up directory name for display (remove owner info in parentheses).
        display_name = dir_name
        if " (" in display_name and ")" in display_name:
            display_name = display_name.split(" (")[0]

        # Fill content with a one line summary of the content using a call to LLM.
        content_summary = ""
        tree_file = os.path.join(out_dir, f"tree_{i:03d}.txt")
        hdbg.dassert_file_exists(tree_file)
        
        # Read the tree content.
        tree_content = hio.from_file(tree_file)
        
        prompt = f"""
        Provide a one-line summary of less than 150 characters of the contents of this directory based on the tree structure:

        {tree_content}"""
        prompt = hprint.dedent(prompt)
        # Use llm library
        model = llm.get_model("gpt-4o-mini")
        response = model.prompt(prompt)
        content_summary = response.text()
        
        # Add row to table.
        table_lines.append(
            f"| {display_name} | {info['owner']} | {info['department']} | {content_summary} |"
        )
    
    # Write table to file.
    output_file = os.path.join(out_dir, "directory_table.md")
    table_content = "\n".join(table_lines)
    hio.to_file(output_file, table_content)
    _LOG.info("Directory table saved to: %s", output_file)


def _combine_llm_outputs(directories: List[str], out_dir: str) -> None:
    """
    Combine all LLM output files into a single markdown file.
    
    Reads all llm_XXX.txt files, matches them with corresponding directories,
    and creates a combined markdown file with directory names as H1 headers
    and content with incremented header levels.
    
    :param directories: list of directory paths that were processed
    :param out_dir: directory containing LLM output files
    """
    _LOG.info("Combining LLM outputs into google_drive_map.md")
    combined_content = []
    
    # Process each directory and its corresponding LLM file.
    for i, directory in enumerate(directories, 1):
        llm_file = os.path.join(out_dir, f"llm_{i:03d}.txt")
        
        # Check if LLM file exists.
        if not os.path.isfile(llm_file):
            _LOG.warning("LLM file not found: %s, skipping", llm_file)
            continue
            
        # Read the LLM content.
        llm_content = hio.from_file(llm_file)
        
        # Get the directory name for the header.
        dir_name = os.path.basename(directory)
        
        # Add H1 header with directory name.
        combined_content.append(f"# {dir_name}\n")
        
        # Process the content to increase header levels.
        lines = llm_content.split("\n")
        for line in lines:
            # Increase header level for markdown headers.
            if line.startswith("#"):
                # Increase by one level (add one more #).
                new_line = "#" + line
                combined_content.append(new_line)
            else:
                combined_content.append(line)
        
        # Add extra newline between sections.
        combined_content.append("")
    
    # Write the combined content to output file.
    output_file = os.path.join(out_dir, "google_drive_map.md")
    final_content = "\n".join(combined_content)
    hio.to_file(output_file, final_content)
    _LOG.info("Combined output saved to: %s", output_file)


def _run_llm_on_file(
    input_file: str,
    output_file: str,
    log_file: str,
) -> None:
    """
    Run LLM command on input file and save summary to output file.

    :param input_file: file to process with LLM
    :param output_file: file to save LLM summary
    :param log_file: log file for LLM processing
    """
    _LOG.debug("Running LLM on file: %s", input_file)
    # Copy input file to log file for LLM processing.
    content = hio.from_file(input_file)
    hio.to_file(log_file, content)
    # Use the default prompt.
    prompt = r"""
        For each directory add a short comment about its content
        Include a comment about the entire directory as a whole

        - Only directories should have a comment
        - Do not comment single files, such as:
        (outdated) Causify Executive Manual - v2.0.gdoc

        The output is a bulleted markdown like:
        ```
        # {DIR_NAME}
        ## Overall
        - This directory serves as a comprehensive resource for Causify, such as
            - Workplace processes
            - Employee information
            - Operational tools
            - Templates

        ## Causify Process
        -  Contains draft versions of
            - Company policies and procedures
            - Including HR processes
            - Invoicing
            - Vendor risk management
        """
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
    # Parse limit range if specified.
    limit_range = hparser.parse_limit_range_args(args)
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
        log_file = os.path.join(args.out_dir, "log.txt")
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
                _run_llm_on_file(tree_file, llm_file, log_file)
            else:
                _LOG.warning(
                    "Tree file %s does not exist, skipping LLM processing", tree_file
                )
        else:
            _LOG.info(
                "Skipping LLM processing for: %s", os.path.basename(directory)
            )
    
    # Run combine action if selected.
    if _ACTION_COMBINE in actions:
        _combine_llm_outputs(directories, args.out_dir)
    
    # Run table action if selected.
    if _ACTION_TABLE in actions:
        _create_directory_table(directories, args.out_dir)
    
    _LOG.info("Completed processing %s directories", len(directories))


if __name__ == "__main__":
    _main(_parse())
