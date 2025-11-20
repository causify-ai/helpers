#!/usr/bin/env python

"""
Summarize a markdown file using LLM and update its Summary section.

This script reads a markdown file, generates a summary using the llm CLI tool,
<<<<<<< HEAD
and intelligently places the summary:
- After `<!-- tocstop -->` tag if present (ideal for files with TOC)
- Otherwise, replaces existing `# Summary` section if found
- Otherwise, adds at the beginning of the file
=======
and updates or adds a `# Summary` section at the beginning of the file.
>>>>>>> master

Examples:
```bash
# Summarize a markdown file using default model
> summarize_md.py --input file.md

# Summarize using a specific model
> summarize_md.py --input file.md --model gpt-4o

# Dry run to see what would be done
> summarize_md.py --input file.md --dry_run
```

Import as:

import dev_scripts_helpers.documentation.summarize_md as dsdosum
"""

import argparse
import logging
import os
import re
import tempfile

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        action="store",
        required=True,
        help="Input markdown file to summarize",
    )
    parser.add_argument(
        "--model",
        action="store",
        default="gpt-4o-mini",
        help="LLM model to use for summarization (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print what would be done without modifying the file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _check_llm_available() -> None:
    """
    Check if the llm command is available.
    """
    _LOG.debug("Checking if llm command is available")
    hsystem.system("which llm", suppress_output=True)


def _read_file(file_path: str) -> str:
    """
    Read the content of the markdown file.

    :param file_path: path to the markdown file
    :return: content of the file
    """
    hdbg.dassert(os.path.isfile(file_path), "File does not exist:", file_path)
    _LOG.debug("Reading file: %s", file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def _generate_summary(content: str, *, model: str) -> str:
    """
    Generate a summary of the content using the llm CLI.

    :param content: text content to summarize
    :param model: LLM model to use
    :return: generated summary
    """
    _LOG.debug("Generating summary using model: %s", model)
    # Create a temporary file with the content.
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".summarize_md.input.txt",
        delete=False,
        encoding="utf-8",
    ) as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    _LOG.debug("Temporary input file: %s", tmp_file_path)
    # Prepare the prompt.
    prompt = "Summarize the content of the text in 3 to 5 bullet points."
    # Call llm CLI.
    cmd = f"cat {tmp_file_path} | llm -m {model} '{prompt}'"
    _LOG.debug("Running command: %s", cmd)
    rc, summary = hsystem.system_to_string(cmd)
    hdbg.dassert_eq(rc, 0, "llm command failed with return code:", rc)
    # Clean up summary.
    summary = summary.strip()
    _LOG.debug("Generated summary:\n%s", summary)
    return summary


def _find_summary_section(content: str) -> tuple:
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


<<<<<<< HEAD
def _find_tocstop_position(content: str) -> int:
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


=======
>>>>>>> master
def _update_summary_section(
    content: str, summary: str, *, dry_run: bool
) -> str:
    """
    Update or add the Summary section in the content.

<<<<<<< HEAD
    Places the summary:
    1. After <!-- tocstop --> tag if it exists
    2. Otherwise, replaces existing # Summary section if found
    3. Otherwise, adds at the beginning of the file

=======
>>>>>>> master
    :param content: original markdown content
    :param summary: generated summary text
    :param dry_run: if True, only return the new content without writing
    :return: updated content
    """
    _LOG.debug("Updating Summary section")
    # Create the new summary section.
    new_summary_section = f"# Summary\n\n{summary}\n\n"
<<<<<<< HEAD
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
                if toc_match and (summary_start + toc_match.start()) < summary_end:
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
=======
    # Check if Summary section exists.
    start_pos, end_pos = _find_summary_section(content)
    if start_pos is not None:
        # Replace existing summary.
        _LOG.info("Replacing existing Summary section")
        new_content = (
            content[:start_pos] + new_summary_section + content[end_pos:]
        )
    else:
        # Add summary at the beginning.
>>>>>>> master
        _LOG.info("Adding new Summary section at the beginning")
        new_content = new_summary_section + content
    return new_content


def _write_file(file_path: str, content: str) -> None:
    """
    Write the content to the markdown file.

    :param file_path: path to the markdown file
    :param content: content to write
    """
    _LOG.debug("Writing file: %s", file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    _LOG.info("File updated successfully: %s", file_path)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Check if llm command is available.
    _check_llm_available()
    # Read the input file.
    input_file = args.input
    content = _read_file(input_file)
    # Generate summary.
    summary = _generate_summary(content, model=args.model)
    # Update the summary section.
    new_content = _update_summary_section(
        content, summary, dry_run=args.dry_run
    )
    # Write the updated content.
    if args.dry_run:
        _LOG.info("Dry run mode: not writing to file")
        _LOG.info("Updated content would be:\n%s", new_content[:500])
    else:
        _write_file(input_file, new_content)


if __name__ == "__main__":
    _main(_parse())
