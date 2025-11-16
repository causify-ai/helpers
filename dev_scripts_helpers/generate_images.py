#!/usr/bin/env python

"""
Generate multiple images using OpenAI's DALL-E API from the same prompt.

This script generates several images from a single prompt using OpenAI's image
generation API.  It supports both standard and HD quality modes.

Examples:
# Generate images using prompt from file
> generate_images.py --input descr.txt --dst_dir ./images

# Generate low-res images using prompt from file
> generate_images.py --input descr.txt --dst_dir ./images --low_res
"""

import argparse
import logging
import os
import re
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

import openai
from tqdm import tqdm

_LOG = logging.getLogger(__name__)

# #############################################################################


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


def _parse_descriptions(content: str) -> List[str]:
    """
    Parse descriptions from input file content.

    Supports two formats:
    1. Single description: entire content is treated as one prompt
    2. Multiple descriptions in numbered format:
       1. **Description of the image 1**
          Text...
       2. **Description of the image 2**
          Text...

    :param content: raw file content
    :return: list of description strings
    """
    # Try to match numbered format.
    # Pattern: number followed by period, optional space, then description.
    pattern = r"^\s*\d+\.\s+\*\*.*?\*\*\s*$"
    lines = content.split("\n")
    # Check if file contains numbered descriptions.
    has_numbered_format = any(re.match(pattern, line) for line in lines)
    if not has_numbered_format:
        # Single description: return entire content as one item.
        _LOG.debug("Detected single description format")
        return [content.strip()]
    # Parse multiple numbered descriptions.
    _LOG.debug("Detected multiple description format")
    descriptions = []
    current_desc = []
    in_description = False
    for line in lines:
        if re.match(pattern, line):
            # Start of new description.
            if current_desc:
                # Save previous description.
                desc_text = "\n".join(current_desc).strip()
                if desc_text:
                    descriptions.append(desc_text)
            # Start collecting new description.
            current_desc = [line]
            in_description = True
        elif in_description:
            # Continue collecting current description.
            current_desc.append(line)
    # Add last description.
    if current_desc:
        desc_text = "\n".join(current_desc).strip()
        if desc_text:
            descriptions.append(desc_text)
    return descriptions


def _download_image(url: str, filepath: str) -> None:
    """
    Download an image from URL to local file.
    """
    import urllib.request

    _LOG.info("Downloading image to %s", filepath)
    urllib.request.urlretrieve(url, filepath)


def _generate_images(
    prompt: str,
    count: int,
    dst_dir: str,
    *,
    low_res: bool = False,
    api_key: Optional[str] = None,
    progress_bar: Optional[tqdm] = None,
    desc_idx: Optional[int] = None,
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
    :param desc_idx: optional description index for filename prefix
    :param dry_run: if True, print actions without executing API calls
    """
    # Set image parameters.
    size = "1024x1024"  # DALL-E 3 only supports 1024x1024, 1024x1792, 1792x1024
    quality = "standard" if low_res else "hd"
    _LOG.info("Generating %s images with prompt: '%s'", count, prompt[:100])
    _LOG.info("Resolution: %s, Quality: %s", size, quality)
    if dry_run:
        _LOG.info("[DRY RUN] Would generate images with the following settings:")
        _LOG.info("[DRY RUN] Prompt: %s", prompt)
        _LOG.info("[DRY RUN] Count: %s", count)
        _LOG.info("[DRY RUN] Destination directory: %s", dst_dir)
        _LOG.info("[DRY RUN] Quality: %s", quality)
        _LOG.info("[DRY RUN] Size: %s", size)
        for i in range(count):
            resolution_suffix = "standard" if low_res else "hd"
            if desc_idx is not None:
                filename = f"desc_{desc_idx:02d}_image_{i + 1:02d}_{resolution_suffix}.png"
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
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,  # DALL-E 3 only supports n=1.
        )
        # Get the image URL.
        image_url = response.data[0].url
        # Create filename.
        resolution_suffix = "standard" if low_res else "hd"
        if desc_idx is not None:
            filename = f"desc_{desc_idx:02d}_image_{i + 1:02d}_{resolution_suffix}.png"
        else:
            filename = f"image_{i + 1:02d}_{resolution_suffix}.png"
        filepath = os.path.join(dst_dir, filename)
        # Download the image.
        _download_image(image_url, filepath)
        _LOG.info("Saved image to: %s", filepath)
        # Update progress bar if provided.
        if progress_bar is not None:
            progress_bar.update(1)
    _LOG.info("Image generation complete. Images saved to: %s", dst_dir)




def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    hdbg.dassert_is_not(args.dst_dir, None, "Destination directory is required")
    # Regular mode.
    # Get descriptions from command line or file.
    descriptions = []
    if args.input:
        # Read descriptions from file.
        hdbg.dassert(
            os.path.exists(args.input),
            "Input file does not exist:",
            args.input,
        )
        _LOG.info("Reading descriptions from file: %s", args.input)
        content = hio.from_file(args.input)
        descriptions = _parse_descriptions(content)
        # Print number of descriptions if multiple.
        if len(descriptions) > 1:
            _LOG.info("Found %s descriptions in input file", len(descriptions))
    elif args.prompt:
        # Use prompt from command line.
        descriptions = [args.prompt]
    else:
        # Neither input file nor prompt provided.
        hdbg.dassert(
            False,
            "Either prompt or --input file is required",
        )
    hdbg.dassert_lte(1, args.count, "Count must be at least 1")
    hdbg.dassert_lte(
        args.count, 10, "Count should not exceed 10 for practical reasons"
    )
    # Calculate total number of images to generate.
    total_images = len(descriptions) * args.count
    if args.dry_run:
        _LOG.info("[DRY RUN] Would generate %s images (%s descriptions x %s images each)", total_images, len(descriptions), args.count)
    else:
        _LOG.info(
            "Generating %s images (%s descriptions x %s images each)",
            total_images,
            len(descriptions),
            args.count,
        )
    # Handle destination directory creation.
    if args.from_scratch:
        if args.dry_run:
            _LOG.info("[DRY RUN] Would create destination directory from scratch: %s", args.dst_dir)
        else:
            _LOG.info("Creating destination directory from scratch: %s", args.dst_dir)
            hio.create_dir(args.dst_dir, incremental=False)
    else:
        # Ensure directory exists (will be created by _generate_images if needed).
        pass
    # Create progress bar for total image generation.
    with tqdm(total=total_images, desc="Generating images") as pbar:
        for desc_idx, description in enumerate(descriptions, start=1):
            _LOG.info(
                "Processing description %s/%s", desc_idx, len(descriptions)
            )
            _LOG.debug("Description: %s", description[:200])
            # Generate images for this description.
            _generate_images(
                prompt=description,
                count=args.count,
                dst_dir=args.dst_dir,
                low_res=args.low_res,
                api_key=args.api_key,
                progress_bar=pbar,
                desc_idx=desc_idx if len(descriptions) > 1 else None,
                dry_run=args.dry_run,
            )


if __name__ == "__main__":
    _main(_parse())
