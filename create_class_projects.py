#!/usr/bin/env python3

"""
Script to generate class projects for machine learning courses.

The script processes markdown files and can perform two actions:
1. summarize: Extract level 2 headers and create bullet point summaries using LLM
2. create_project: Generate 3 project descriptions for each section with Python packages

Examples:
> create_class_projects.py --in_file input.md --action summarize --output_dir ./output
> create_class_projects.py --in_file input.md --action create_project --output_dir ./output
"""

import argparse
import logging
import os
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = ["summarize", "create_project"]
_DEFAULT_ACTIONS = ["summarize"]


def _parse() -> argparse.ArgumentParser:
    """Parse command line arguments."""
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
        "--output_dir",
        required=True,
        help="Output directory for results",
    )
    parser.add_argument(
        "--from_scratch",
        action="store_true",
        help="Create output directory from scratch (remove if exists)",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _check_llm_available() -> None:
    """Check if llm command is available in the system."""
    hsystem.system("which llm", suppress_output=True)
    _LOG.debug("llm command found and available")


def _call_llm(prompt: str, content: str) -> str:
    """
    Call LLM with the given prompt and content.
    
    :param prompt: The prompt to send to LLM
    :param content: The content to process
    :return: LLM response
    """
    full_prompt = f"{prompt}\n\n{content}"
    # Write prompt to temporary file and use hsystem.system() to call llm.
    temp_file_path = "tmp.create_class_projects._call_llm.txt"
    hio.to_file(temp_file_path, full_prompt)
    try:
        # Use hsystem to call llm command with input file.
        rc, output = hsystem.system_to_string(f"llm < {temp_file_path}")
        return output.strip()
    finally:
        # Clean up temporary file.
        os.unlink(temp_file_path)


def _extract_level2_sections(file_content: str) -> List[Tuple[str, str]]:
    """
    Extract level 2 headers and their content from markdown.
    
    :param file_content: The markdown file content
    :return: List of tuples (header, content)
    """
    lines = file_content.split('\n')
    sections = []
    current_header = None
    current_content = []
    
    for line in lines:
        if line.startswith('## '):
            # Save previous section if exists.
            if current_header is not None:
                sections.append((current_header, '\n'.join(current_content)))
            # Start new section.
            current_header = line
            current_content = []
        elif line.startswith('# '):
            # Level 1 header - save previous section if exists.
            if current_header is not None:
                sections.append((current_header, '\n'.join(current_content)))
                current_header = None
                current_content = []
        else:
            # Content line.
            if current_header is not None:
                current_content.append(line)
    
    # Save last section if exists.
    if current_header is not None:
        sections.append((current_header, '\n'.join(current_content)))
    
    return sections


def _action_summarize(in_file: str, output_dir: str) -> None:
    """
    Summarize markdown file by creating bullet points for level 2 sections.
    
    :param in_file: Input markdown file path
    :param output_dir: Output directory path
    """
    _LOG.info("Starting summarize action for file: %s", in_file)
    # Read input file.
    hdbg.dassert_file_exists(in_file)
    file_content = hio.from_file(in_file)
    # Extract level 2 sections.
    sections = _extract_level2_sections(file_content)
    _LOG.debug("Found %d level 2 sections", len(sections))
    # Process each section with LLM.
    result_lines = []
    for header, content in sections:
        if content.strip():
            _LOG.debug("Processing section: %s", header)
            prompt = "Given the following markdown text summarize it into a few bullets"
            summary = _call_llm(prompt, content)
            result_lines.append(header)
            result_lines.append(summary)
            result_lines.append("")  # Empty line for spacing.
    # Save result to output file.
    base_name = os.path.splitext(os.path.basename(in_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}.summary.txt")
    hio.to_file(output_file, '\n'.join(result_lines))
    _LOG.info("Summary saved to: %s", output_file)


def _action_create_project(in_file: str, output_dir: str) -> None:
    """
    Create project descriptions based on summary file.
    
    :param in_file: Input markdown file path
    :param output_dir: Output directory path
    """
    _LOG.info("Starting create_project action for file: %s", in_file)
    # Find corresponding summary file.
    base_name = os.path.splitext(os.path.basename(in_file))[0]
    summary_file = os.path.join(output_dir, f"{base_name}.summary.txt")
    hdbg.dassert_file_exists(summary_file)
    # Read summary file.
    summary_content = hio.from_file(summary_file)
    sections = _extract_level2_sections(summary_content)
    _LOG.debug("Found %d sections in summary", len(sections))
    # Generate projects for each section.
    result_lines = []
    for header, content in sections:
        if content.strip():
            _LOG.debug("Generating projects for section: %s", header)
            prompt = (
                "Come up with the description of 3 projects that can be used to "
                "clarify the content of the file\n"
                "Look for Python packages that can be used to implement those projects"
            )
            projects = _call_llm(prompt, content)
            result_lines.append(header)
            result_lines.append(projects)
            result_lines.append("")  # Empty line for spacing.
    # Save result to output file.
    output_file = os.path.join(output_dir, f"{base_name}.projects.txt")
    hio.to_file(output_file, '\n'.join(result_lines))
    _LOG.info("Projects saved to: %s", output_file)


def _main(parser: argparse.ArgumentParser) -> None:
    """Main function to execute the script."""
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate inputs.
    hdbg.dassert_file_exists(args.in_file)
    # Create output directory if needed.
    if args.from_scratch:
        hio.create_dir(args.output_dir, incremental=False)
    else:
        hio.create_dir(args.output_dir, incremental=True)
    # Check LLM availability.
    _check_llm_available()
    # Execute selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    for action in actions:
        _LOG.info("Executing action: %s", action)
        if action == "summarize":
            _action_summarize(args.in_file, args.output_dir)
        elif action == "create_project":
            _action_create_project(args.in_file, args.output_dir)
        else:
            hdbg.dfatal("Invalid action: %s", action)


if __name__ == "__main__":
    _main(_parse())