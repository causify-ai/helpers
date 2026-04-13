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
import random
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
    parser.add_argument(
        "prompt", nargs="?", help="Text prompt for image generation"
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
        default=5,
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
        help="Workload type (MSLM610 generates images for predefined word sets)",
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
        filename = f"image_{i + 1:02d}_{resolution_suffix}.png"
        filepath = os.path.join(dst_dir, filename)
        # Download the image.
        _download_image(image_url, filepath)
        _LOG.info("Saved image to: %s", filepath)
    _LOG.info("Image generation complete. Images saved to: %s", dst_dir)


def _generate_workload_images(
    workload: str,
    dst_dir: str,
    low_res: bool = False,
    api_key: Optional[str] = None,
) -> None:
    """
    Generate images for specific workload types.
    """
    random.seed()  # Seeds with current system time by default
    if workload != "MSLM610":
        raise ValueError(f"Unsupported workload: {workload}")
    # MSLM610 workload data.
    WORKLOAD_DATA = {
        1: ["Compass", "Spark", "Roadmap"],
        2: ["Toolbox", "Gears", "Flowchart"],
        3: ["Graph", "Symbols", "Ontology Tree"],
        4: ["Blueprint", "Layers", "Curve"],
        5: ["Book", "Equation", "Lightbulb"],
        6: ["Prior", "Posterior", "Update"],
        7: ["Code", "Dice", "Distribution"],
        8: ["Timeline", "Clock", "Arrows"],
        9: ["Arrow", "Chain", "Intervention"],
        10: ["Line Chart", "Calendar", "Horizon"],
        11: ["Neural Net", "Layers", "Circuit"],
        12: ["Agent", "Reward", "Maze"],
        13: ["Brain", "Question Mark", "Galaxy"],
    }
    values = {
        1: ["Cimabue", "Maestà", "c. 1280"],
        2: ["Giotto di Bondone", "Lamentation", "c. 1305"],
        3: ["Sandro Botticelli", "The Birth of Venus", "c. 1485"],
        4: ["Leonardo da Vinci", "Mona Lisa", "c. 1503–1506"],
        5: ["Rembrandt van Rijn", "The Night Watch", "1642"],
        6: ["Vincent van Gogh", "The Starry Night", "1889"],
        7: ["Pablo Picasso", "Guernica", 1937],
        8: ["Jackson Pollock", "No. 5, 1948", 1948],
        9: ["Mark Rothko", "Orange and Yellow", 1956],
        10: ["Andy Warhol", "Marilyn Diptych", 1962],
        11: ["Jean-Michel Basquiat", "Untitled", 1981],
        12: ["Jenny Saville", "Propped", 1992],
        13: ["Banksy", "Girl with Balloon", 2002],
    }
    # Set up OpenAI client.
    if api_key:
        client = openai.OpenAI(api_key=api_key)
    else:
        # Will use OPENAI_API_KEY environment variable.
        client = openai.OpenAI()
    # Ensure destination directory exists.
    hio.create_dir(dst_dir, incremental=True)
    # Set image parameters.
    size = "1024x1024"
    quality = "standard" if low_res else "hd"
    # Base prompt for abstract expressionist style.
    # base_prompt = "Create an abstract expressionist brushwork with fluid, organic motion for"
    # Calculate total number of images.
    total_images = sum(len(words) for words in WORKLOAD_DATA.values())
    _LOG.info("Generating %s images for workload %s", total_images, workload)
    _LOG.info("Resolution: %s, Quality: %s", size, quality)
    image_count = 0
    for number, words in WORKLOAD_DATA.items():
        for word in words:
            # Pick a random value from values dictionary
            random_number = random.choice(list(values.keys()))
            style = values[random_number][0]
            # style = values[number][0]
            prompt = "Create a painting in the style of " + style
            prompt += " for the word " + word
            prompt += ". There should be no text in the image."
            print(prompt)
            image_count += 1
            # Create filename: image.1.compass.png.
            word_clean = word.lower().replace(" ", "_")
            # filename = f"image.{style}.{word_clean}.png"
            filename = f"image.{word_clean}.{style}.png"
            filepath = os.path.join(dst_dir, filename)
            if os.path.exists(filepath):
                _LOG.info("Image already exists: %s", filepath)
                continue
            # prompt = f"{base_prompt} {word}"
            _LOG.info(
                "Generating image %s/%s: %s", image_count, total_images, word
            )
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            # Get the image URL.
            image_url = response.data[0].url
            # Download the image.
            _download_image(image_url, filepath)
            _LOG.info("Saved image to: %s", filepath)
    _LOG.info("Workload image generation complete. Images saved to: %s", dst_dir)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    hdbg.dassert_is_not(args.dst_dir, None, "Destination directory is required")
    if args.workload:
        # Workload mode.
        _generate_workload_images(
            workload=args.workload,
            dst_dir=args.dst_dir,
            low_res=args.low_res,
            api_key=args.api_key,
        )
    else:
        # Regular mode.
        hdbg.dassert_is_not(args.prompt, None, "Prompt is required")
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
