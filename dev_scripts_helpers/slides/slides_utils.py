#!/usr/bin/env python

import base64
import logging
import os
import re
from typing import List, Tuple


import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo

_LOG = logging.getLogger(__name__)

# Default system prompt for the LLM.
_DEFAULT_SYSTEM_PROMPT = """
You are a college professor expert of machine learning and big data.

Given the following slides in markdown format create a discussion of the slide
to highlight the most important points of each slide
- Use plain language and do not use fancy words
- Create bullet points for the discussion following the same structure as the
  original slide
- The discussion for each slide should contain around 100 words
- Do not use bold or italicize the text
- Create a short transitions in less than 20 words between slides when needed.
- Use "we" and "let's" instead of saying "This slide says"

The output should have a format like:

# <Title>

Description of the slide
"""

# - Bullet point 1
# - Bullet point 2
# - Bullet point ...

# #############################################################################


def _extract_image_paths_from_slide(slide_content: str) -> List[str]:
    """
    Extract image paths from slide markdown content.

    :param slide_content: slide content as markdown string
    :return: list of image file paths found in the slide
    """
    # Pattern to match markdown image syntax: ![](path/to/image.ext)
    image_pattern = r"!\[.*?\]\(([^)]+)\)"
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
        base64_string = base64.b64encode(image_data).decode("utf-8")
    return base64_string


def process_slide_images(slides_group: List[str]) -> Tuple[List[str], List[str]]:
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


# ########


def extract_slides_from_file(file_path: str) -> Tuple[List[str], List[str]]:
    """
    Extract slides from markdown file.

    :param file_path: path to input markdown file
    :return: tuple of (list of slide contents as strings, list of slide titles)
    """
    hdbg.dassert_file_exists(file_path)
    # Read the file.
    content = hio.from_file(file_path)
    lines = content.splitlines()
    # Extract slides using the markdown parsing functionality.
    header_list, _ = hmarkdo.extract_slides_from_markdown(lines)
    _LOG.debug("Found %d slides", len(header_list))
    # Extract slide content and titles.
    slides = []
    titles = []
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
        # Extract slide title from header.
        titles.append(header_info.description)
    return slides, titles
