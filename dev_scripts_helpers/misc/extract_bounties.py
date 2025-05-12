#!/usr/bin/env python

"""
Given the list of potential bounties.

> curl -L -o bounties.md "https://docs.google.com/document/d/1xPgQ2tWXQuVWKkGVONjOGd5j14mXSmGeY_4d1_sGzAE/export?format=markdown"
> grep "## " bounties.md
## **Template**
## **LLMs**
### **Capture / replay interactions with OpenAI**
### **Extend hopenai.py using LangChain for Multiple Models**
### **TO\_FILE: Add progress bar to get\_completion**
### **Create an evaluation suite to compare LLM prompting and models**

Extract sections from a markdown file and create files based on section hierarchy.

This script processes a markdown file to extract level 2 (##) and level 3 (###) sections,
then creates files named with the format: level3_section,level2_section.txt

Examples:
> extract_bounties.py --input_file bounties.md
> extract_bounties.py --input_file bounties.md --output_file output.txt
"""

import argparse
import logging
import re
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: argument parser with all command-line arguments
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--input_file",
        action="store",
        required=True,
        help="Path to the markdown file to process",
    )
    parser.add_argument(
        "--output_file",
        action="store",
        required=False,
        default=None,
        help="Path to the output file to process",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _clean_up(line: str) -> str:
    # Remove the ** and TO\_FILE
    line = line.replace("**", "").replace("TO\_FILE:", "")
    # Remove \` and \_.
    line = line.replace(r"\`", "'").replace(r"\_", "_")
    #
    line = line.strip()
    return line


def _extract_sections(markdown_content: str) -> List[Tuple[str, str]]:
    """
    Extract sections from markdown content.

    :param markdown_content: string containing the markdown content
    :return: list of tuples containing (level2_section, level3_section)
    """
    sections = []
    current_level2 = None
    # Split content into lines
    lines = markdown_content.split("\n")
    for line in lines:
        # Check for level 2 headers (##).
        level2_match = re.match(r"^##\s+(.+)$", line)
        if level2_match:
            current_level2 = level2_match.group(1).strip()
            current_level2 = _clean_up(current_level2)
            continue
        # Check for level 3 headers (###).
        level3_match = re.match(r"^###\s+(.+)$", line)
        if level3_match and current_level2:
            level3_section = level3_match.group(1).strip()
            level3_section = _clean_up(level3_section)
            sections.append((current_level2, level3_section))
    return sections


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the main logic of the script.

    :param parser: argument parser with command-line arguments
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read the input file.
    content = hio.from_file(args.input_file)
    # Extract the sections.
    sections = _extract_sections(content)
    _LOG.info("Processed %d sections from %s", len(sections), args.input_file)
    # Convert the list of tuples into a string separated by commas.
    strs = [f"{level3}\t{level2}" for level2, level3 in sections]
    txt = "\n".join(strs)
    # Create a file with the string.
    if args.output_file:
        hio.to_file(args.output_file, txt)
    else:
        hsystem.to_pbcopy(txt, pbcopy=True)


if __name__ == "__main__":
    _main(_parse())
