#!/usr/bin/env python

"""
Generate multiple images using OpenAI's DALL-E API from the same prompt.

This script generates several images from a single prompt using OpenAI's image
generation API. It supports both standard and HD quality modes.

Examples:
# Generate images using prompt from file
> generate_images.py --input descr.txt --dst_dir ./images

# Generate low-res images using prompt from file
> generate_images.py --input descr.txt --dst_dir ./images --low_res
"""

import argparse
import base64
import logging
import os
import re
import urllib.request
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

import openai
from tqdm import tqdm

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse_descriptions(content: str) -> List[str]:
    """
    Extract prompts from formatted text content.

    The format is:
    ```
    # prompt_name
    text...
    more text...

    # another_prompt_name
    more text...
    ```

    Each prompt starts with '# prompt_name' followed by text on subsequent
    lines. Prompts are separated by one or more blank lines or by the next
    prompt header.

    :param content: text content containing multiple prompts
    :return: list of extracted prompt texts (without the header lines)
    """
    # Parse descriptions with names and extract only the text.
    descriptions_with_names = _parse_descriptions_with_names(content)
    return [desc_text for _, desc_text in descriptions_with_names]


def _parse_descriptions_with_names(content: str) -> List[tuple]:
    """
    Extract prompts with their names from formatted text content.

    The format is:
    ```
    # prompt_name
    text...
    more text...

    # another_prompt_name
    more text...
    ```

    Each prompt starts with '# prompt_name' followed by text on subsequent
    lines. Prompts are separated by one or more blank lines or by the next
    prompt header.

    :param content: text content containing multiple prompts
    :return: list of tuples (prompt_name, prompt_text)
    """
    descriptions = []
    lines = content.split("\n")
    current_description = []
    current_name = None
    in_description = False
    unprocessed_lines = []
    for line in lines:
        # Check if this is a header line (starts with '# ' followed by a word).
        match = re.match(r"^#\s+(\w+)", line)
        if match:
            # Save previous description if it exists.
            if current_description:
                # Join lines and strip whitespace.
                desc_text = "\n".join(current_description).strip()
                if desc_text:
                    descriptions.append((current_name, desc_text))
                current_description = []
            # Extract the prompt name.
            current_name = match.group(1)
            in_description = True
            continue
        # If we're in a description, collect lines.
        if in_description:
            current_description.append(line)
        elif line.strip():
            # Non-empty line outside of a description.
            unprocessed_lines.append(line)
    # Add the last description if it exists.
    if current_description:
        desc_text = "\n".join(current_description).strip()
        if desc_text:
            descriptions.append((current_name, desc_text))
    # Check for unprocessed lines.
    if unprocessed_lines:
        unprocessed_text = "\n".join(unprocessed_lines)
        hdbg.dassert(
            False,
            "Found lines that were not processed:\n%s",
            unprocessed_text,
        )
    return descriptions


# #############################################################################


def _encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.

    :param image_path: path to the image file
    :return: base64 encoded string of the image
    """
    hdbg.dassert_path_exists(image_path)
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# #############################################################################


def _generate_images(
    prompt: str,
    count: int,
    dst_dir: str,
    *,
    low_res: bool = False,
    api_key: Optional[str] = None,
    progress_bar: Optional[tqdm] = None,
    prompt_name: Optional[str] = None,
    reference_image: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """
    Generate images using OpenAI API and save to destination directory.

    :param prompt: text prompt for image generation
    :param count: number of images to generate
    :param dst_dir: destination directory for generated images
    :param low_res: generate standard quality vs HD quality
    :param api_key: OpenAI API key
    :param progress_bar: optional tqdm progress bar for tracking
    :param prompt_name: optional prompt name for filename
    :param reference_image: optional reference image path for DALL-E 2 editing
    :param dry_run: if True, print actions without executing API calls
    """
    # Set image parameters based on reference image.
    use_reference = reference_image is not None
    if use_reference:
        hdbg.dassert_path_exists(reference_image)
        model = "dall-e-2"
        size = "1024x1024"  # DALL-E 2 supports 256x256, 512x512, 1024x1024.
        _LOG.info("Using DALL-E 2 with reference image: %s", reference_image)
    else:
        model = "dall-e-3"
        size = "1024x1024"  # DALL-E 3 only supports 1024x1024, 1024x1792, 1792x1024.
        quality = "standard" if low_res else "hd"
    _LOG.info("Generating %s images with prompt: '%s'", count, prompt[:100])
    _LOG.info("Model: %s, Size: %s", model, size)
    if not use_reference:
        _LOG.info("Quality: %s", quality)
    if dry_run:
        _LOG.info("[DRY RUN] Would generate images with the following settings:")
        _LOG.info("[DRY RUN] Model: %s", model)
        _LOG.info("[DRY RUN] Prompt: %s", prompt)
        _LOG.info("[DRY RUN] Count: %s", count)
        _LOG.info("[DRY RUN] Destination directory: %s", dst_dir)
        if not use_reference:
            _LOG.info("[DRY RUN] Quality: %s", quality)
        _LOG.info("[DRY RUN] Size: %s", size)
        if use_reference:
            _LOG.info("[DRY RUN] Reference image: %s", reference_image)
        for i in range(count):
            resolution_suffix = "standard" if low_res else "hd"
            if prompt_name:
                filename = f"image.{prompt_name}.{i + 1:02d}.{resolution_suffix}.png"
            else:
                filename = f"image_{i + 1:02d}_{resolution_suffix}.png"
            filepath = os.path.join(dst_dir, filename)
            _LOG.info("[DRY RUN] Would save image %s/%s to: %s", i + 1, count, filepath)
            # Update progress bar if provided.
            if progress_bar is not None:
                progress_bar.update(1)
        return
    # Set up OpenAI client.
    if api_key:
        client = openai.OpenAI(api_key=api_key)
    else:
        # Will use OPENAI_API_KEY environment variable.
        client = openai.OpenAI()
    # Ensure destination directory exists.
    hio.create_dir(dst_dir, incremental=True)
    for i in range(count):
        _LOG.info("Generating image %s/%s", i + 1, count)
        if use_reference:
            # Use DALL-E 2 edit endpoint with reference image.
            with open(reference_image, "rb") as image_file:
                response = client.images.edit(
                    model=model,
                    image=image_file,
                    prompt=prompt,
                    size=size,
                    n=1,
                )
        else:
            # Use DALL-E 3 generate endpoint.
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,  # DALL-E 3 only supports n=1.
            )
        # Get the image URL.
        image_url = response.data[0].url
        # Create filename using new format.
        resolution_suffix = "standard" if low_res else "hd"
        if prompt_name:
            filename = f"image.{prompt_name}.{i + 1:02d}.{resolution_suffix}.png"
        else:
            filename = f"image_{i + 1:02d}_{resolution_suffix}.png"
        filepath = os.path.join(dst_dir, filename)
        # Download the image directly.
        _LOG.info("Downloading image to %s", filepath)
        urllib.request.urlretrieve(image_url, filepath)
        _LOG.info("Saved image to: %s", filepath)
        # Update progress bar if provided.
        if progress_bar is not None:
            progress_bar.update(1)
    _LOG.info("Image generation complete. Images saved to: %s", dst_dir)


# #############################################################################


def _generate_images_from_file(
    prompt: Optional[str],
    input_file: Optional[str],
    dst_dir: str,
    count: int,
    *,
    low_res: bool = False,
    api_key: Optional[str] = None,
    reference_image: Optional[str] = None,
    dry_run: bool = False,
    from_scratch: bool = False,
) -> None:
    """
    Generate images from prompts (command line or file) and save to directory.

    :param prompt: optional text prompt for image generation
    :param input_file: optional path to file containing prompts
    :param dst_dir: destination directory for generated images
    :param count: number of images to generate per prompt
    :param low_res: generate standard quality vs HD quality
    :param api_key: OpenAI API key
    :param reference_image: optional reference image path for DALL-E 2 editing
    :param dry_run: if True, print actions without executing API calls
    :param from_scratch: if True, create destination directory from scratch
    """
    # Get descriptions from command line or file.
    descriptions_with_names = []
    if input_file:
        # Read descriptions from file.
        hdbg.dassert_path_exists(input_file)
        _LOG.info("Reading descriptions from file: %s", input_file)
        content = hio.from_file(input_file)
        descriptions_with_names = _parse_descriptions_with_names(content)
        # Print number of descriptions if multiple.
        if len(descriptions_with_names) > 1:
            _LOG.info("Found %s descriptions in input file", len(descriptions_with_names))
            # Debug: print first description to verify extraction.
            _LOG.debug("First description preview: %s", descriptions_with_names[0][1][:100])
    elif prompt:
        # Use prompt from command line.
        descriptions_with_names = [(None, prompt)]
    else:
        # Neither input file nor prompt provided.
        hdbg.dassert(
            False,
            "Either prompt or --input file is required",
        )
    hdbg.dassert_lte(1, count, "Count must be at least 1")
    hdbg.dassert_lte(count, 10, "Count should not exceed 10 for practical reasons")
    # Calculate total number of images to generate.
    total_images = len(descriptions_with_names) * count
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would generate %s images (%s descriptions x %s images each)",
            total_images,
            len(descriptions_with_names),
            count,
        )
    else:
        _LOG.info(
            "Generating %s images (%s descriptions x %s images each)",
            total_images,
            len(descriptions_with_names),
            count,
        )
    # Handle destination directory creation.
    if from_scratch:
        if dry_run:
            _LOG.info(
                "[DRY RUN] Would create destination directory from scratch: %s",
                dst_dir,
            )
        else:
            _LOG.info("Creating destination directory from scratch: %s", dst_dir)
            hio.create_dir(dst_dir, incremental=False)
    else:
        # Ensure directory exists (will be created by _generate_images if needed).
        pass
    # Create progress bar for total image generation.
    with tqdm(total=total_images, desc="Generating images") as pbar:
        for desc_idx, (prompt_name, description) in enumerate(descriptions_with_names, start=1):
            _LOG.info(
                "Processing description %s/%s", desc_idx, len(descriptions_with_names)
            )
            _LOG.debug("Description: %s", description[:200])
            # Generate images for this description.
            _generate_images(
                prompt=description,
                count=count,
                dst_dir=dst_dir,
                low_res=low_res,
                api_key=api_key,
                progress_bar=pbar,
                prompt_name=prompt_name,
                reference_image=reference_image,
                dry_run=dry_run,
            )


# #################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "prompt", nargs="?", help="Text prompt for image generation"
    )
    parser.add_argument(
        "--input",
        action="store",
        help="Path to file containing the image description prompt",
    )
    parser.add_argument(
        "--dst_dir",
        action="store",
        required=True,
        help="Destination directory for generated images",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of images to generate (default: 5)",
    )
    parser.add_argument(
        "--low_res",
        action="store_true",
        help="Generate standard quality images (vs HD quality)",
    )
    parser.add_argument(
        "--api_key",
        help="OpenAI API key (if not set via OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--reference_image",
        help="Path to reference image for DALL-E 2 editing (optional)",
    )
    parser.add_argument(
        "--workload",
        help="Workload type for specialized image generation (optional)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print what would be done without executing API calls",
    )
    parser.add_argument(
        "--from_scratch",
        action="store_true",
        help="Create destination directory from scratch (delete if exists)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    hdbg.dassert_is_not(args.dst_dir, None, "Destination directory is required")
    # Generate images from command line or file.
    _generate_images_from_file(
        prompt=args.prompt,
        input_file=args.input,
        dst_dir=args.dst_dir,
        count=args.count,
        low_res=args.low_res,
        api_key=args.api_key,
        reference_image=args.reference_image,
        dry_run=args.dry_run,
        from_scratch=args.from_scratch,
    )


if __name__ == "__main__":
    _main(_parse())
