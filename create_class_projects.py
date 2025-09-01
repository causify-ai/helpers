#!/usr/bin/env python3

"""
Script to generate class projects for machine learning courses.

The script processes markdown files and can perform two actions:
1. summarize: Extract level 2 headers and create bullet point summaries using LLM
2. create_project: Generate 3 project descriptions for each section with Python packages

Examples:
> create_class_projects.py --in_file input.md --action summarize --output_dir ./output
> create_class_projects.py --in_file input.md --action create_project --output_file output.md
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htqdm as htqdm

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = ["create_project"]
_DEFAULT_ACTIONS = ["create_project"]


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
        "--output_dir",
        help="Output directory for results (used with summarize action)",
    )
    parser.add_argument(
        "--output_file",
        help="Output file for results (used with create_project action)",
    )
    parser.add_argument(
        "--from_scratch",
        action="store_true",
        help="Create output directory from scratch (remove if exists)",
    )
    parser.add_argument(
        "--level",
        choices=["easy", "medium", "hard"],
        required=True,
        help="Complexity level for projects",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _check_llm_available() -> None:
    """
    Check if llm command is available in the system.
    """
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
    # Use hsystem to call llm command with input file.
    rc, output = hsystem.system_to_string(f"llm < {temp_file_path}")
    return output.strip()


def _action_create_project(
    in_file: str, output_file: str, level: str = "medium"
) -> None:
    """
    Create project descriptions based on markdown file.

    :param in_file: Input markdown file path
    :param output_file: Output file path
    :param level: Complexity level for projects (easy, medium, hard)
    """
    _LOG.info("Starting create_project action for file: %s", in_file)
    # Read input file directly.
    hdbg.dassert_file_exists(in_file)
    file_content = hio.from_file(in_file)
    # Use the entire file content instead of extracting sections.
    _LOG.info("Processing entire file content")
    # Generate projects for entire file content.
    result_lines = []
    tqdm_out = htqdm.TqdmToLogger(_LOG, level=logging.INFO)
    _LOG.debug("Generating projects for entire file")
    prompt = f"""
    You are a college level data science professor.

    Given the markdown for a lecture, come up with the description of 1 project
    that can be used to clarify the content of the lesson and train the students.

    Look for Python packages that can be used to implement those projects

    Look for freely available data sets that can be used to implement those projects.

    The Difficulty of the project can be
    - Easy, it should take around 7 days to develop
    - Medium , it should take around 10 days to complete
    - Hard, it should take 14 days to complete

    The difficulty level should be {level}.

    - Title:
    - Difficulty:
    - Tech description:
    - Project idea:
    - Data set to use:
    - Python libs:
    - Links to relevant tools
    - Links to related resources

    Avoid long texts or steps and comments, just list the projects.
    """
    prompt = hprint.dedent(prompt)
    projects = _call_llm(prompt, file_content)
    result_lines.append("# Class Projects")
    result_lines.append(projects)
    result_lines.append("")  # Empty line for spacing.
    # Save result to output file.
    if not output_file:
        base_name = os.path.splitext(os.path.basename(in_file))[0]
        output_file = f"{base_name}.projects.txt"
    hio.to_file(output_file, "\n".join(result_lines))
    _LOG.info("Projects saved to: %s", output_file)


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to execute the script.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate inputs.
    hdbg.dassert_file_exists(args.in_file)
    # Check LLM availability.
    _check_llm_available()
    # Execute selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    for action in actions:
        _LOG.info("Executing action: %s", action)
        if action == "create_project":
            # For create_project action, use output_file instead of output_dir.
            output_file = args.output_file
            if not output_file:
                # Default output file format if not specified.
                base_name = os.path.splitext(os.path.basename(args.in_file))[0]
                output_file = f"{base_name}.projects.txt"
            _action_create_project(args.in_file, output_file, args.level)
        else:
            hdbg.dfatal("Invalid action: %s", action)


if __name__ == "__main__":
    _main(_parse())
