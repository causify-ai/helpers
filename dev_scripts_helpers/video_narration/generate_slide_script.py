#!/usr/bin/env python

"""
Generate presentation script from markdown slides using LLM processing.

This script processes markdown slides (identified by headers starting with '*')
and generates a presentation script by passing groups of N slides to an LLM
for analysis and script generation.

Examples:
# Process slides in groups of 3
> generate_slide_script.py --in_file slides.md --out_file script.md --slides_per_group 3
"""

import argparse
import logging
from typing import List, Optional

import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hllm as hllm
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Default system prompt for the LLM.
_DEFAULT_SYSTEM_PROMPT = """
You are a college professor expert of machine learning and big data.

Given the following markdown slides, create a script to highlight the most
important points of each slide.

Each slide should contain around 450 words.

Create a short transitions between slides.

The output should have a format like:

# Slide <i>: <Title>

<Discussion of the slide #i>

# Slide <i+1>: <Title>

<Discussion of the slide #i+1>
"""

# #############################################################################


def _extract_slides_from_file(file_path: str) -> List[str]:
    """
    Extract slides from markdown file.

    :param file_path: path to input markdown file
    :return: list of slide contents as strings
    """
    hdbg.dassert_file_exists(file_path)
    # Read the file.
    content = hio.from_file(file_path)
    lines = content.splitlines()
    # Extract slides using the markdown parsing functionality.
    header_list, _ = hmarkdo.extract_slides_from_markdown(lines)
    _LOG.debug("Found %d slides", len(header_list))
    # Extract slide content.
    slides = []
    for i, header_info in enumerate(header_list):
        # Get start and end line numbers.
        start_line = header_info.line_number - 1  # Convert to 0-based indexing.
        if i + 1 < len(header_list):
            end_line = header_list[i + 1].line_number - 1
        else:
            end_line = len(lines)
        # Extract slide content.
        slide_lines = lines[start_line:end_line]
        slide_content = "\n".join(slide_lines)
        slides.append(slide_content)
    return slides


def _process_slides_group(
    slides_group: List[str],
    system_prompt: str,
    model: str,
) -> str:
    """
    Process a group of slides through LLM to generate presentation script.

    :param slides_group: list of slide contents to process
    :param system_prompt: system prompt for the LLM
    :param model: LLM model to use
    :return: generated script content
    """
    hdbg.dassert_isinstance(slides_group, list)
    hdbg.dassert_lt(0, len(slides_group))
    # Combine slides into user prompt.
    user_prompt = "\n\n".join(slides_group)
    _LOG.debug("Processing %d slides with LLM", len(slides_group))
    # Get completion from LLM.
    response = hllm.get_completion(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        cache_mode="NORMAL",
        temperature=0.1,
    )
    return response


def _generate_slide_script(
    in_file: str,
    out_file: str,
    *,
    slides_per_group: int = 3,
    limit_range: Optional[tuple] = None,
) -> None:
    """
    Generate presentation script from markdown slides.

    :param in_file: path to input markdown file
    :param out_file: path to output script file
    :param slides_per_group: number of slides to process in each LLM call
    :param limit_range: optional tuple (start, end) to limit slides processed
    """
    _LOG.info("Reading slides from: %s", in_file)
    slides = _extract_slides_from_file(in_file)
    _LOG.info("Found %d slides total", len(slides))
    # Apply limit range if specified.
    if limit_range is not None:
        start, end = limit_range
        slides = slides[start:end + 1]
        _LOG.info("Limited to slides %d-%d (%d slides)", start, end, len(slides))
    # Process slides in groups.
    output_parts = []
    total_groups = (len(slides) + slides_per_group - 1) // slides_per_group
    for i in tqdm.tqdm(range(0, len(slides), slides_per_group),
                       total=total_groups,
                       desc="Processing slide groups"):
        group_end = min(i + slides_per_group, len(slides))
        slides_group = slides[i:group_end]
        _LOG.info("Processing slides %d-%d", i + 1, group_end)
        # Process the group.
        script_content = _process_slides_group(
            slides_group=slides_group,
            system_prompt=_DEFAULT_SYSTEM_PROMPT,
            model="",
        )
        output_parts.append(script_content)
    # Combine all generated scripts.
    full_script = "\n\n".join(output_parts)
    # Write output.
    _LOG.info("Writing script to: %s", out_file)
    hio.to_file(out_file, full_script)
    _LOG.info("Script generation completed")


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--in_file",
        action="store",
        required=True,
        help="Input markdown file with slides",
    )
    parser.add_argument(
        "--out_file",
        action="store",
        required=True,
        help="Output file for generated script",
    )
    parser.add_argument(
        "--slides_per_group",
        action="store",
        type=int,
        default=3,
        help="Number of slides to process per LLM call (default: 3)",
    )
    hparser.add_limit_range_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse limit range.
    limit_range = hparser.parse_limit_range_args(args)
    # Generate the slide script.
    _generate_slide_script(
        in_file=args.in_file,
        out_file=args.out_file,
        slides_per_group=args.slides_per_group,
        limit_range=limit_range,
    )


if __name__ == "__main__":
    _main(_parse())