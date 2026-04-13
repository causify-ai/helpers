#!/usr/bin/env python

"""
Generate multiple images using OpenAI's DALL-E API from the same prompt.

This script generates several images from a single prompt using OpenAI's image
generation API. It supports both standard and HD quality modes, and multiple
models including DALL-E 2, DALL-E 3, and gpt-image-1.

Examples:
# Generate images using prompt from file
> generate_images.py --input descr.txt --dst_dir ./images

# Generate low-res images using prompt from file
> generate_images.py --input descr.txt --dst_dir ./images --low_res

# Generate images using gpt-image-1 model
> generate_images.py --input descr.txt --dst_dir ./images --model gpt-image-1
"""

import argparse
import base64
import logging
import os
import re
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

import openai
import requests
from tqdm import tqdm

_LOG = logging.getLogger(__name__)


# #############################################################################


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
    _LOG.debug("Found %s descriptions", len(descriptions))
    return descriptions


# #############################################################################


def _generate_images(
    prompt_name: str,
    prompt: str,
    count: int,
    dst_dir: str,
    *,
    low_res: bool = False,
    progress_bar: Optional[tqdm] = None,
    reference_image: Optional[str] = None,
    dry_run: bool = False,
    model_name: Optional[str] = None,
) -> None:
    """
    Generate images using OpenAI API and save to destination directory.

    :param prompt_name: optional prompt name for filename
    :param prompt: text prompt for image generation
    :param count: number of images to generate
    :param dst_dir: destination directory for generated images
    :param low_res: generate standard quality vs HD quality
    :param progress_bar: optional tqdm progress bar for tracking
    :param reference_image: optional reference image path for DALL-E 2 editing
    :param dry_run: if True, print actions without executing API calls
    :param model_name: model to use (dall-e-2, dall-e-3, gpt-image-1)
    """
    # Set image parameters based on reference image and model selection.
    use_reference = reference_image is not None
    if model_name:
        # Use explicitly specified model.
        model = model_name
        _LOG.debug("Using explicitly specified model: %s", model)
    elif use_reference:
        # Reference image requires DALL-E 2.
        hdbg.dassert_path_exists(reference_image)
        # model = "dall-e-2"
        model = "gpt-image-1"
        _LOG.warning("Using DALL-E 2 with reference image: %s", reference_image)
    else:
        # Default to DALL-E 3.
        # model = "dall-e-3"
        model = "gpt-image-1"
    # Set size and quality based on model.
    if model == "dall-e-2":
        size = "1024x1024"  # DALL-E 2 supports 256x256, 512x512, 1024x1024.
    elif model == "dall-e-3":
        size = "1024x1024"  # DALL-E 3 only supports 1024x1024, 1024x1792, 1792x1024.
        quality = "standard" if low_res else "hd"
    elif model == "gpt-image-1":
        size = "1024x1024"  # gpt-image-1 default size.
        quality = (
            "medium" if low_res else "high"
        )  # gpt-image-1 uses low/medium/high/auto.
    else:
        hdbg.dfatal("Unsupported model: %s", model)
    _LOG.debug("Generating %s images with prompt: '%s'", count, prompt[:100])
    _LOG.debug("Model: %s", model)
    _LOG.debug("Prompt name: %s", prompt_name)
    _LOG.debug("Prompt: %s", prompt)
    _LOG.debug("Count: %s", count)
    _LOG.debug("Destination directory: %s", dst_dir)
    if model in ["dall-e-3", "gpt-image-1"]:
        _LOG.debug("Quality: %s", quality)
    if use_reference:
        _LOG.debug("Reference image: %s", reference_image)
    _LOG.debug("Size: %s", size)
    if dry_run:
        for i in range(count):
            resolution_suffix = "standard" if low_res else "hd"
            if prompt_name:
                filename = (
                    f"image.{prompt_name}.{i + 1:02d}.{resolution_suffix}.png"
                )
            else:
                filename = f"image_{i + 1:02d}_{resolution_suffix}.png"
            filepath = os.path.join(dst_dir, filename)
            _LOG.debug(
                "[DRY RUN] Would save image %s/%s to: %s", i + 1, count, filepath
            )
            # Update progress bar if provided.
            if progress_bar is not None:
                progress_bar.update(1)
        return
    # Set up OpenAI client.
    client = openai.OpenAI()
    for i in range(count):
        _LOG.debug("Generating image %s/%s", i + 1, count)
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
            # Use generate endpoint for DALL-E 3 and gpt-image-1.
            # Request base64 response format to avoid URL download issues.
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
                response_format="b64_json",
            )
        # Create filename using new format.
        resolution_suffix = "low_res" if low_res else "high_res"
        filename = f"image.{prompt_name}.{i + 1:02d}.{resolution_suffix}.png"
        filepath = os.path.join(dst_dir, filename)
        # Get the image data - could be URL or base64 encoded.
        image_data = response.data[0]
        if hasattr(image_data, "url") and image_data.url:
            # Download from URL using requests library for better error handling.
            image_url = image_data.url
            _LOG.debug(
                "Downloading image '%s' from URL to %s", image_url, filepath
            )
            try:
                response_img = requests.get(image_url, timeout=30)
                response_img.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response_img.content)
            except requests.exceptions.RequestException as e:
                _LOG.error("Failed to download image from URL: %s", e)
                _LOG.error("URL: %s", image_url)
                raise
        elif hasattr(image_data, "b64_json") and image_data.b64_json:
            # Decode base64 image.
            _LOG.debug("Decoding base64 image to %s", filepath)
            image_bytes = base64.b64decode(image_data.b64_json)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
        else:
            hdbg.dfatal(
                "Image response does not contain 'url' or 'b64_json'. "
                "Response data: %s",
                image_data,
            )
        _LOG.debug("Saved image to: %s", filepath)
        # Update progress bar if provided.
        if progress_bar is not None:
            progress_bar.update(1)
    _LOG.info("Image generation complete. Images saved to: %s", dst_dir)


# #############################################################################


def _generate_images_from_file(
    prompt: Optional[str],
    input_file: Optional[str],
    style: str,
    dst_dir: str,
    count: int,
    *,
    low_res: bool = False,
    reference_image: Optional[str] = None,
    dry_run: bool = False,
    no_backup: bool = False,
    model_name: Optional[str] = None,
) -> None:
    """
    Generate images from prompts (command line or file) and save to directory.

    :param prompt: optional text prompt for image generation
    :param input_file: optional path to file containing prompts
    :param style: style to use for image generation (optional)
    :param dst_dir: destination directory for generated images
    :param count: number of images to generate per prompt
    :param low_res: generate standard quality vs HD quality
    :param reference_image: optional reference image path for DALL-E 2 editing
    :param dry_run: if True, print actions without executing API calls
    :param model_name: model to use (dall-e-2, dall-e-3, gpt-image-1)
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
            _LOG.info(
                "Found %s descriptions in input file",
                len(descriptions_with_names),
            )
            # Debug: print first description to verify extraction.
            _LOG.debug(
                "First description preview: %s",
                descriptions_with_names[0][1][:100],
            )
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
    hdbg.dassert_lte(
        count, 10, "Count should not exceed 10 for practical reasons"
    )
    #
    if style != "":
        _LOG.info("Adding style: %s", style)
        if style == "style1":
            style = """
            Use a unified minimalist flat-illustration style: clean vector lines, uniform
            stroke weight, simple geometric shapes, muted blue-gray color palette, no
            gradients, no shadows, no textures, no writings, centered composition, generous
            white space.
            """
        elif style == "style2":
            style = """
            Use a unified minimalist flat-illustration style: clean vector lines,
            simple geometric shapes, muted blue-white color palette, no
            gradients, no shadows, no textures, no writings, centered composition

            Use transparent background.
            """
        elif style == "causify":
            style = """
            Modern, tech-centric vector illustration in a monochromatic
            blue-to-cyan palette, featuring clean geometric shapes with rounded
            corners, uniform stroke weight, and crisp vector lines. Subtle glow
            and soft highlights add depth without shadows or textures. Icons
            are semi-flat with slight dimensionality, abstract and symbolic, no
            text or labels. Composition is centered and balanced with clear
            visual flow using arrows and connectors, generous spacing, and a
            dark or transparent background. Polished, minimal, and suitable for
            AI, analytics, and decision-making visuals.
            """
        else:
            raise ValueError("Invalid style: %s" % style)
        style = hprint.dedent(style)
        descriptions_with_names = [
            (tag, style + "\n" + description)
            for tag, description in descriptions_with_names
        ]
    # Calculate total number of images to generate.
    total_images = len(descriptions_with_names) * count
    _LOG.debug(
        "Generating %s images (%s descriptions x %s images each)",
        total_images,
        len(descriptions_with_names),
        count,
    )
    # Ensure destination directory exists.
    if not no_backup:
        hio.backup_file_or_dir_if_exists(dst_dir)
    hio.create_dir(dst_dir, incremental=True)
    # Create progress bar for total image generation.
    with tqdm(total=total_images, desc="Generating images") as pbar:
        for desc_idx, (prompt_name, description) in enumerate(
            descriptions_with_names, start=1
        ):
            _LOG.debug(
                "Processing description %s/%s",
                desc_idx,
                len(descriptions_with_names),
            )
            _LOG.debug("Description: %s", description[:200])
            # Generate images for this description.
            _generate_images(
                prompt_name,
                description,
                count,
                dst_dir,
                low_res=low_res,
                progress_bar=pbar,
                reference_image=reference_image,
                dry_run=dry_run,
                model_name=model_name,
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
        "--style",
        help="Style to use for image generation (optional)",
        default="",
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
        default=1,
        help="Number of images to generate (default: 1)",
    )
    parser.add_argument(
        "--low_res",
        action="store_true",
        help="Generate standard quality images (vs HD quality)",
    )
    parser.add_argument(
        "--reference_image",
        help="Path to reference image for DALL-E 2 editing (optional)",
    )
    parser.add_argument(
        "--model",
        choices=["dall-e-2", "dall-e-3", "gpt-image-1"],
        help="Model to use for image generation (default: gpt-image-1)",
    )
    parser.add_argument(
        "--workload",
        help="Workload type for specialized image generation (optional)",
    )
    parser.add_argument(
        "--no_backup",
        action="store_true",
        help="Do not backup the destination directory",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print what would be done without executing API calls",
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
        style=args.style,
        dst_dir=args.dst_dir,
        count=args.count,
        low_res=args.low_res,
        reference_image=args.reference_image,
        dry_run=args.dry_run,
        no_backup=args.no_backup,
        model_name=args.model,
    )


if __name__ == "__main__":
    _main(_parse())
