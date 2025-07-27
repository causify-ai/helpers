#!/usr/bin/env python

"""
Generate multiple images using OpenAI's DALL-E API from the same prompt.

This script generates 5 images from a single prompt using OpenAI's image
generation API.  It supports both standard and HD quality modes.

Examples:
# Generate standard quality images
> dev_scripts_helpers/generate_images.py "A sunset over mountains" --dst_dir ./images --low_res

# Generate HD quality images
> dev_scripts_helpers/generate_images.py "A sunset over mountains" --dst_dir ./images

# Generate with custom image count
> dev_scripts_helpers/generate_images.py "A cat wearing a hat" --dst_dir ./images --count 3
"""

import argparse
import logging
import os
from typing import Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

import openai

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument(
        "--dst_dir",
        action="store",
        required=True,
        help="Destination directory for generated images",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of images to generate (default: 5)",
    )
    parser.add_argument(
        "--low_res",
        action="store_true",
        help="Generate standard quality images (vs HD quality)",
    )
    parser.add_argument(
        "--api_key", help="OpenAI API key (if not set via OPENAI_API_KEY env var)"
    )
    hparser.add_verbosity_arg(parser)
    return parser


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
    low_res: bool = False,
    api_key: Optional[str] = None,
) -> None:
    """
    Generate images using OpenAI API and save to destination directory.
    """
    # Set up OpenAI client.
    if api_key:
        client = openai.OpenAI(api_key=api_key)
    else:
        # Will use OPENAI_API_KEY environment variable.
        client = openai.OpenAI()
    # Ensure destination directory exists.
    hio.create_dir(dst_dir, incremental=True)
    # Set image parameters.
    size = "1024x1024"  # DALL-E 3 only supports 1024x1024, 1024x1792, 1792x1024
    quality = "standard" if low_res else "hd"
    _LOG.info("Generating %s images with prompt: '%s'", count, prompt)
    _LOG.info("Resolution: %s, Quality: %s", size, quality)
    for i in range(count):
        _LOG.info("Generating image %s/%s", i+1, count)
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
        filename = f"image_{i+1:02d}_{resolution_suffix}.png"
        filepath = os.path.join(dst_dir, filename)
        # Download the image.
        _download_image(image_url, filepath)
        _LOG.info("Saved image to: %s", filepath)
    _LOG.info("Image generation complete. Images saved to: %s", dst_dir)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    hdbg.dassert_is_not(args.prompt, None, "Prompt is required")
    hdbg.dassert_is_not(args.dst_dir, None, "Destination directory is required")
    hdbg.dassert_lte(1, args.count, "Count must be at least 1")
    hdbg.dassert_lte(
        args.count, 10, "Count should not exceed 10 for practical reasons"
    )
    _generate_images(
        prompt=args.prompt,
        count=args.count,
        dst_dir=args.dst_dir,
        low_res=args.low_res,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    _main(_parse())
