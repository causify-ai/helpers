#!/usr/bin/env python

"""
Update markdown files with LLM-based actions.

This script provides multiple actions for processing markdown files:
- summarize: Generate and add/update a Summary section
- update_content: Refresh content to match current code
- apply_style: Apply formatting rules from ai.md_instructions.md
- lint: Run lint_txt.py to format the file

After each action (except lint), the file is automatically linted using
lint_txt.py unless --skip_lint is specified.

Note: At least one action must be specified using --action.

Examples:
```bash
# Single file examples

# Summarize a markdown file
> update_md.py --input file.md --action summarize

# Update content to match code
> update_md.py --input file.md --action update_content

# Apply style guidelines
> update_md.py --input file.md --action apply_style

# Only lint the file
> update_md.py --input file.md --action lint

# Perform multiple actions
> update_md.py --input file.md --action summarize,apply_style

# Use a specific model
> update_md.py --input file.md --action summarize --model gpt-4o

# Skip linting after actions
> update_md.py --input file.md --action summarize --skip_lint

# Multiple files examples

# Process multiple files using comma-separated list
> update_md.py --files="file1.md,file2.md,file3.md" --action summarize

# Process multiple files using repeated --input argument
> update_md.py --input file1.md --input file2.md --input file3.md --action summarize

# Process multiple files from a file list (one file per line)
> update_md.py --from_files="files.txt" --action summarize

# Process multiple files with multiple actions and progress bar
> update_md.py --files="file1.md,file2.md,file3.md" --action summarize,apply_style
```

Import as:

import dev_scripts_helpers.documentation.update_md as dsdoupmd
"""

import argparse
import logging
import re
from typing import Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Valid actions for the script.
_VALID_ACTIONS = ["summarize", "update_content", "apply_style", "lint"]
_DEFAULT_ACTIONS = []


# #############################################################################
# Helper functions
# #############################################################################


def _read_file(file_path: str) -> str:
    """
    Read the content of the markdown file.

    :param file_path: path to the markdown file
    :return: content of the file
    """
    hdbg.dassert_file_exists(file_path)
    _LOG.debug("Reading file: %s", file_path)
    content = hio.from_file(file_path)
    return content


def _write_file(file_path: str, content: str) -> None:
    """
    Write the content to the markdown file.

    :param file_path: path to the markdown file
    :param content: content to write
    """
    _LOG.debug("Writing file: %s", file_path)
    hio.to_file(file_path, content)
    _LOG.info("File updated successfully: %s", file_path)


# #############################################################################
# Action: summarize
# #############################################################################


def _generate_summary(
    content: str, *, model: str, use_llm_executable: bool
) -> str:
    """
    Generate a summary of the content using the llm library or executable.

    :param content: text content to summarize
    :param model: LLM model to use
    :param use_llm_executable: whether to use llm CLI executable or Python library
    :return: generated summary
    """
    _LOG.info("Generating summary using model: %s", model)
    # Prepare the system prompt.
    system_prompt = """
    Summarize the content of the text in 3 to 5 bullet points, each of maximum
    20 words
    """
    # Call apply_llm from hllm_cli.
    summary = hllmcli.apply_llm(
        content,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
    )
    # Clean up summary.
    summary = summary.strip()
    _LOG.debug("Generated summary:\n%s", summary)
    return summary


def _find_summary_section(content: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Find the Summary section in the content.

    :param content: markdown content
    :return: tuple of (start_pos, end_pos) or (None, None) if not found
    """
    _LOG.debug("Searching for existing Summary section")
    # Look for "# Summary" header.
    pattern = r"^# Summary\s*$"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        _LOG.debug("No Summary section found")
        return None, None
    # Find the start of the summary section.
    start_pos = match.start()
    # Find the end of the summary section (next # header or end of file).
    next_header_pattern = r"\n# [^#]"
    next_match = re.search(next_header_pattern, content[start_pos + 1 :])
    if next_match:
        end_pos = start_pos + 1 + next_match.start()
    else:
        end_pos = len(content)
    _LOG.debug("Found Summary section from pos %d to %d", start_pos, end_pos)
    return start_pos, end_pos


def _find_tocstop_position(content: str) -> Optional[int]:
    """
    Find the position right after the <!-- tocstop --> tag.

    :param content: markdown content
    :return: position after tocstop tag, or None if not found
    """
    _LOG.debug("Searching for <!-- tocstop --> tag")
    pattern = r"<!-- tocstop -->"
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        _LOG.debug("No <!-- tocstop --> tag found")
        return None
    # Return position after the tag and any following newlines.
    end_pos = match.end()
    # Skip any trailing whitespace/newlines after the tag.
    while end_pos < len(content) and content[end_pos] in ("\n", "\r", " "):
        end_pos += 1
    _LOG.debug("Found <!-- tocstop --> at position %d", end_pos)
    return end_pos


def _update_summary_section(content: str, summary: str) -> str:
    """
    Update or add the Summary section in the content.

    Places the summary:
    1. After <!-- tocstop --> tag if it exists
    2. Otherwise, replaces existing # Summary section if found
    3. Otherwise, adds at the beginning of the file

    :param content: original markdown content
    :param summary: generated summary text
    :return: updated content
    """
    _LOG.debug("Updating Summary section")
    # Create the new summary section.
    new_summary_section = f"# Summary\n\n{summary}\n\n"
    # Check if tocstop exists.
    tocstop_pos = _find_tocstop_position(content)
    # Check if Summary section exists.
    summary_start, summary_end = _find_summary_section(content)
    if tocstop_pos is not None:
        # Place summary after tocstop tag.
        _LOG.info("Placing Summary section after <!-- tocstop --> tag")
        # If there's an existing summary section, remove it first.
        if summary_start is not None:
            # Special handling: if summary is before tocstop, we need to be careful
            # not to remove the TOC section itself.
            if summary_start < tocstop_pos:
                # Find where the summary content actually ends (before TOC or next header).
                # Look for either <!-- toc --> or the next # header.
                toc_start_pattern = r"<!-- toc -->"
                toc_match = re.search(
                    toc_start_pattern, content[summary_start:], re.IGNORECASE
                )
                if (
                    toc_match
                    and (summary_start + toc_match.start()) < summary_end
                ):
                    # The TOC starts within what we detected as the summary section.
                    # Only remove up to the TOC start.
                    actual_summary_end = summary_start + toc_match.start()
                else:
                    actual_summary_end = summary_end
                # Remove the old summary section.
                content = content[:summary_start] + content[actual_summary_end:]
                # Adjust tocstop_pos.
                tocstop_pos -= actual_summary_end - summary_start
                # Re-find tocstop position in case content changed.
                tocstop_pos = _find_tocstop_position(content)
            else:
                # Summary is after tocstop, just remove it normally.
                content = content[:summary_start] + content[summary_end:]
        # Insert summary after tocstop.
        new_content = (
            content[:tocstop_pos] + new_summary_section + content[tocstop_pos:]
        )
    elif summary_start is not None:
        # Replace existing summary (no tocstop).
        _LOG.info("Replacing existing Summary section")
        new_content = (
            content[:summary_start] + new_summary_section + content[summary_end:]
        )
    else:
        # Add summary at the beginning (no tocstop, no existing summary).
        _LOG.info("Adding new Summary section at the beginning")
        new_content = new_summary_section + content
    return new_content


def _action_summarize(
    input_file: str,
    *,
    model: str,
    use_llm_executable: bool,
    skip_lint: bool,
) -> None:
    """
    Generate and add/update a Summary section in the markdown file.

    :param input_file: path to input markdown file
    :param model: LLM model to use
    :param use_llm_executable: whether to use llm CLI executable
    :param skip_lint: if True, skip linting the file
    """
    _LOG.info("Action: summarize")
    # Read the input file.
    content = _read_file(input_file)
    # Generate summary.
    summary = _generate_summary(
        content, model=model, use_llm_executable=use_llm_executable
    )
    # Update the summary section.
    new_content = _update_summary_section(content, summary)
    # Write the updated content.
    _write_file(input_file, new_content)
    # Lint the file for proper formatting.
    if not skip_lint:
        hlint.lint_file(input_file)


# #############################################################################
# Action: update_content
# #############################################################################


def _action_update_content(
    input_file: str,
    *,
    model: str,
    use_llm_executable: bool,
    skip_lint: bool,
) -> None:
    """
    Update the content of the file to match current code.

    :param input_file: path to input markdown file
    :param model: LLM model to use
    :param use_llm_executable: whether to use llm CLI executable
    :param skip_lint: if True, skip linting the file
    """
    _LOG.info("Action: update_content")
    # Read input file.
    _LOG.debug("Reading input file: %s", input_file)
    input_content = _read_file(input_file)
    input_size = len(input_content)
    _LOG.info("Input file size: %d characters", input_size)
    # Prepare the system prompt.
    system_prompt = """
    Update the content of the file to make sure it matches the code.

    Important:
    - Return ONLY the updated markdown text
    - Do not add explanations or comments
    - Preserve all technical content and code blocks
    - Update any outdated information to match current code
    """
    # Estimate expected output size (assume similar size to input).
    expected_num_chars = int(input_size * 1.2)
    # Apply LLM to update the content.
    _LOG.info("Applying LLM to update markdown content")
    updated_content = hllmcli.apply_llm(
        input_content,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
        expected_num_chars=expected_num_chars,
    )
    # Write output file.
    _write_file(input_file, updated_content)
    output_size = len(updated_content)
    _LOG.info("Output file size: %d characters", output_size)
    # Lint the file for proper formatting.
    if not skip_lint:
        hlint.lint_file(input_file)


# #############################################################################
# Action: apply_style
# #############################################################################


def _get_style_system_prompt() -> str:
    """
    Get the system prompt from the ai.md_instructions.md file.

    :return: content of the notes instructions file
    """
    # Build path to the instructions file.
    instructions_path = hgit.find_file_in_git_tree(
        "ai.md_instructions.md", super_module=True
    )
    _LOG.debug("Reading instructions from: %s", instructions_path)
    hdbg.dassert_file_exists(instructions_path)
    # Read the instructions.
    instructions = hio.from_file(instructions_path)
    _LOG.debug("Read %d characters from instructions file", len(instructions))
    # Create the system prompt.
    system_prompt = f"""Apply the rules of the following document to the input text:

{instructions}

Important:
- Return ONLY the formatted markdown text
- Do not add explanations or comments
- Preserve all technical content and code blocks
- Apply the formatting rules strictly"""
    return system_prompt


def _action_apply_style(
    input_file: str,
    *,
    model: str,
    use_llm_executable: bool,
    skip_lint: bool,
) -> None:
    """
    Apply documentation formatting rules to the markdown file.

    :param input_file: path to input markdown file
    :param model: LLM model to use
    :param use_llm_executable: whether to use llm CLI executable
    :param skip_lint: if True, skip linting the file
    """
    _LOG.info("Action: apply_style")
    hdbg.dassert_file_exists(input_file)
    # Get the system prompt.
    system_prompt = _get_style_system_prompt()
    # Read input file.
    _LOG.debug("Reading input file: %s", input_file)
    input_content = _read_file(input_file)
    input_size = len(input_content)
    _LOG.info("Input file size: %d characters", input_size)
    # Estimate expected output size (assume similar size to input).
    expected_num_chars = int(input_size * 1.2)
    # Apply LLM to format the content.
    _LOG.info("Applying LLM to format markdown content")
    formatted_content = hllmcli.apply_llm(
        input_content,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
        expected_num_chars=expected_num_chars,
    )
    # Write output file.
    _write_file(input_file, formatted_content)
    output_size = len(formatted_content)
    _LOG.info("Output file size: %d characters", output_size)
    # Lint the file for proper formatting.
    if not skip_lint:
        hlint.lint_file(input_file)


# #############################################################################
# Action: lint
# #############################################################################


def _action_lint(input_file: str) -> None:
    """
    Run lint_txt.py on the markdown file.

    :param input_file: path to input markdown file
    """
    _LOG.info("Action: lint")
    # Lint the file for proper formatting.
    hlint.lint_file(input_file)


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_multi_file_args(parser)
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    parser.add_argument(
        "-m",
        "--model",
        action="store",
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--use_llm_executable",
        action="store_true",
        default=False,
        help="Use llm CLI executable instead of Python library (default: False)",
    )
    parser.add_argument(
        "--skip_lint",
        action="store_true",
        default=False,
        help="Skip running lint_txt.py after each action (default: False)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Get selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Ensure at least one action is specified.
    hdbg.dassert(
        len(actions) > 0,
        "At least one action must be specified using --action",
    )
    # Parse input files.
    input_files = hparser.parse_multi_file_args(args)
    _LOG.info("Number of files to process: %d", len(input_files))
    _LOG.info("Actions to perform: %s", ", ".join(actions))
    if args.skip_lint:
        _LOG.info("Linting disabled (--skip_lint)")
    # Process each file.
    if len(input_files) > 1:
        # Use progress bar for multiple files.
        from tqdm.autonotebook import tqdm
        import helpers.htqdm as htqdm

        tqdm_out = htqdm.TqdmToLogger(_LOG, level=logging.INFO)
        file_iterator = tqdm(input_files, desc="Processing files", file=tqdm_out)
    else:
        # No progress bar for single file.
        file_iterator = input_files
    for input_file in file_iterator:
        _LOG.info("Processing file: %s", input_file)
        # Execute each action for the current file.
        for action in actions:
            if action == "summarize":
                _action_summarize(
                    input_file,
                    model=args.model,
                    use_llm_executable=args.use_llm_executable,
                    skip_lint=args.skip_lint,
                )
            elif action == "update_content":
                _action_update_content(
                    input_file,
                    model=args.model,
                    use_llm_executable=args.use_llm_executable,
                    skip_lint=args.skip_lint,
                )
            elif action == "apply_style":
                _action_apply_style(
                    input_file,
                    model=args.model,
                    use_llm_executable=args.use_llm_executable,
                    skip_lint=args.skip_lint,
                )
            elif action == "lint":
                _action_lint(input_file)
            else:
                hdbg.dfatal("Invalid action: %s", action)
    _LOG.info("All actions completed successfully for all files")


if __name__ == "__main__":
    _main(_parse())
