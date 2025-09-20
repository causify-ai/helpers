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
import base64
import logging
import os
import re
from typing import List, Optional, Tuple

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


def _extract_image_paths_from_slide(slide_content: str) -> List[str]:
    """
    Extract image paths from slide markdown content.

    :param slide_content: slide content as markdown string
    :return: list of image file paths found in the slide
    """
    # Pattern to match markdown image syntax: ![](path/to/image.ext)
    image_pattern = r'!\[.*?\]\(([^)]+)\)'
    matches = re.findall(image_pattern, slide_content)
    return matches


def _convert_image_to_base64(image_path: str) -> str:
    """
    Convert image file to base64 string.

    :param image_path: path to the image file
    :return: base64 encoded string of the image
    """
    hdbg.dassert_file_exists(image_path)
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_string = base64.b64encode(image_data).decode('utf-8')
    return base64_string


def _process_slide_images(slides_group: List[str]) -> Tuple[List[str], List[str]]:
    """
    Process images from a group of slides.

    :param slides_group: list of slide contents
    :return: tuple of (processed_slides, images_as_base64)
    """
    images_as_base64 = []
    processed_slides = []

    for slide_content in slides_group:
        # Extract image paths from this slide
        image_paths = _extract_image_paths_from_slide(slide_content)

        # Convert images to base64 and add to collection
        for image_path in image_paths:
            if os.path.exists(image_path):
                try:
                    base64_image = _convert_image_to_base64(image_path)
                    images_as_base64.append(base64_image)
                    _LOG.debug("Converted image to base64: %s", image_path)
                except Exception as e:
                    _LOG.warning("Failed to convert image %s: %s", image_path, e)
            else:
                _LOG.warning("Image file not found: %s", image_path)

        processed_slides.append(slide_content)

    return processed_slides, images_as_base64


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

    # Process images from slides
    processed_slides, images_as_base64 = _process_slide_images(slides_group)

    # Combine slides into user prompt.
    user_prompt = "\n\n".join(processed_slides)
    _LOG.debug("Processing %d slides with LLM", len(processed_slides))
    if images_as_base64:
        _LOG.info("Including %d images in LLM request", len(images_as_base64))

    # Get completion from LLM with images if present.
    response = hllm.get_completion(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        cache_mode="NORMAL",
        temperature=0.1,
        images_as_base64=images_as_base64 if images_as_base64 else None,
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