#!/usr/bin/env -S uv run

"""
Generate book chapter from markdown slides and PNG images.

This script processes markdown slides and corresponding PNG images to create
a book chapter format with LLM-generated commentary for each slide.

Examples:
# Generate book chapter from markdown and PNG directory
> generate_book_chapter.py \
    --input_file data605/lectures_source/Lesson01.1-Intro.txt \
    --input_png_dir output \
    --output_dir test

# Generate book chapter from markdown and PDF file
> generate_book_chapter.py \
    --input_file data605/lectures_source/Lesson01.1-Intro.txt \
    --input_pdf_file data605/lectures/Lesson01.1-Intro.pdf \
    --output_dir test
"""

# /// script
# dependencies = [
#   "pandas>=2.0.0",
#   "openai",
#   "tqdm",
#   "pyyaml",
#   "requests",
#   "python-dotenv",
#   "pdf2image",
#   "pillow",
# ]
# ///

import argparse
import logging
import os
from typing import List, Optional

import pdf2image
import tqdm

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdockexe
import helpers.hio as hio
import helpers.hllm as hllm
import helpers.hparser as hparser
import dev_scripts_helpers.slides.slides_utils as dshsslut

_LOG = logging.getLogger(__name__)

# Default system prompt for the LLM.
_DEFAULT_SYSTEM_PROMPT = """
You are a college professor expert of machine learning and big data.

Given the following slide in markdown format, create a detailed commentary
that explains the content and context of the slide.
- Use plain language and do not use fancy words
- Create bullet points for the discussion following the same structure as the
  original slide
- The discussion for each slide should contain around 100-150 words
- Do not use bold or italicize the text
- Use "we" and "let's" instead of saying "This slide says"
- Focus on explaining the concepts, providing context, and highlighting
  important points

The output should be in markdown format without a heading.
"""


def _extract_png_from_pdf(
    input_pdf_file: str,
    output_png_dir: str,
    *,
    dpi: int = 200,
) -> None:
    """
    Extract PNG images from PDF file using pdf2image.

    :param input_pdf_file: path to input PDF file
    :param output_png_dir: directory to save PNG files
    :param dpi: DPI resolution for output images
    """
    hdbg.dassert_file_exists(input_pdf_file)
    _LOG.info("Extracting PNG images from PDF: %s", input_pdf_file)
    # Create output directory.
    hio.create_dir(output_png_dir, incremental=False)
    _LOG.info("Output PNG directory: %s", output_png_dir)
    # Convert PDF pages to images.
    _LOG.info("Converting PDF to images with DPI=%d", dpi)
    images = pdf2image.convert_from_path(input_pdf_file, dpi=dpi)
    num_pages = len(images)
    hdbg.dassert_lt(0, num_pages, "No pages found in PDF file:", input_pdf_file)
    _LOG.info("Found %d pages in PDF", num_pages)
    # Save each page as a PNG file.
    for page_num, image in enumerate(
        tqdm.tqdm(images, desc="Extracting pages"), start=1
    ):
        # Format filename with zero-padded page number.
        output_filename = f"slides{page_num:03d}.png"
        output_path = os.path.join(output_png_dir, output_filename)
        # Save image as PNG.
        image.save(output_path, "PNG")
        _LOG.debug("Saved: %s", output_filename)
    _LOG.info(
        "Successfully extracted %d PNG images to %s", num_pages, output_png_dir
    )


def _get_png_files_from_directory(png_dir: str) -> List[str]:
    """
    Get sorted list of PNG files from directory.

    :param png_dir: directory containing PNG files
    :return: sorted list of PNG file paths with pattern slides*.png
    """
    hdbg.dassert_dir_exists(png_dir)
    # List all PNG files matching the pattern slides*.png.
    png_files = []
    for filename in os.listdir(png_dir):
        if filename.startswith("slides") and filename.endswith(".png"):
            png_files.append(os.path.join(png_dir, filename))
    # Sort files to ensure correct ordering.
    png_files.sort()
    _LOG.info("Found %d PNG files in directory: %s", len(png_files), png_dir)
    return png_files


@hcacsimp.simple_cache(cache_type="json")
def _generate_slide_commentary(
    slide_content: str,
    system_prompt: str,
    model: str,
) -> str:
    """
    Generate commentary for a single slide using LLM.

    :param slide_content: markdown content of the slide
    :param system_prompt: system prompt for the LLM
    :param model: LLM model to use
    :return: generated commentary text
    """
    _LOG.debug("Generating commentary for slide")
    # Process images from slide.
    processed_slides, images_as_base64 = dshsslut.process_slide_images(
        [slide_content]
    )
    user_prompt = processed_slides[0]
    # Get completion from LLM.
    response = hllm.get_completion(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        cache_mode="NORMAL",
        temperature=0.1,
    )
    return response


def _generate_book_chapter(
    input_file: str,
    output_dir: str,
    *,
    input_png_dir: Optional[str] = None,
    input_pdf_file: Optional[str] = None,
    dpi: int = 200,
    image_width: str = "80%",
) -> None:
    """
    Generate book chapter from markdown slides and PNG directory or PDF file.

    :param input_file: path to input markdown file with slides
    :param output_dir: directory to save output files
    :param input_png_dir: directory containing PNG files (slides*.png)
    :param input_pdf_file: PDF file to extract PNG images from
    :param dpi: DPI resolution for PDF extraction
    :param image_width: width of images in output (e.g., "80%", "50%")
    """
    hdbg.dassert_file_exists(input_file)
    # Validate that exactly one of input_png_dir or input_pdf_file is provided.
    has_png_dir = input_png_dir is not None
    has_pdf_file = input_pdf_file is not None
    hdbg.dassert(
        has_png_dir or has_pdf_file,
        "Must provide either --input_png_dir or --input_pdf_file",
    )
    hdbg.dassert(
        not (has_png_dir and has_pdf_file),
        "Cannot provide both --input_png_dir and --input_pdf_file",
    )
    # Create output directory.
    hio.create_dir(output_dir, incremental=True)
    # Extract base name from input file.
    input_basename = os.path.basename(input_file)
    if input_basename.endswith(".txt"):
        base_name = input_basename[:-4]
    elif input_basename.endswith(".md"):
        base_name = input_basename[:-3]
    else:
        base_name = input_basename
    _LOG.info("Using base name: %s", base_name)
    # Handle PDF extraction if needed.
    if input_pdf_file:
        # Create PNG directory as {base_name}.png inside output_dir.
        png_dir_name = f"{base_name}.png"
        input_png_dir = os.path.join(output_dir, png_dir_name)
        _LOG.info("Extracting PNG files from PDF to: %s", input_png_dir)
        _extract_png_from_pdf(input_pdf_file, input_png_dir, dpi=dpi)
    else:
        hdbg.dassert_dir_exists(input_png_dir)
    _LOG.info("Reading slides from: %s", input_file)
    # Extract slides from markdown file.
    slides, titles = dshsslut.extract_slides_from_file(input_file)
    num_slides = len(slides)
    _LOG.info("Found %d slides in markdown file", num_slides)
    # Get PNG files from directory.
    png_files = _get_png_files_from_directory(input_png_dir)
    num_pngs = len(png_files)
    _LOG.info("Found %d PNG files in directory", num_pngs)
    # Check that slide count matches PNG count.
    hdbg.dassert_eq(
        # +1 because the first slide is the title slide.
        num_slides + 1,
        num_pngs,
        "Number of slides in markdown (%d) does not match number of PNG files (%d)",
        num_slides,
        num_pngs,
    )
    # Generate commentary for each slide.
    output_parts = []
    # First, handle the title slide (first PNG, no content).
    _LOG.info("Processing title slide (1/%d)", num_slides + 1)
    slide_output = []
    slide_output.append("\\newpage")
    slide_output.append("")
    # Add centered image with specified width and empty alt text.
    slide_output.append(f"![]({png_files[0]}){{width={image_width}}}")
    slide_output.append("")
    output_parts.append("\n".join(slide_output))
    # Then process content slides (slides from markdown with corresponding PNGs).
    # Note: png_files[0] is the title slide, so we pair slides[i] with png_files[i+1].
    for idx, (slide_content, slide_title, png_path) in enumerate(
        tqdm.tqdm(
            zip(slides, titles, png_files[1:]),
            total=num_slides,
            desc="Processing slides",
        ),
        start=2,
    ):
        _LOG.info("Processing slide %d/%d", idx, num_slides + 1)
        # Create output for this slide.
        slide_output = []
        # Add page break before slide.
        slide_output.append("\\newpage")
        slide_output.append("")
        # Add title, image, and commentary.
        # Use original slide title from input markdown.
        slide_output.append(f"# {slide_title}")
        slide_output.append("")
        # Add centered image with specified width and empty alt text.
        slide_output.append(f"![]({png_path}){{width={image_width}}}")
        slide_output.append("")
        # Generate commentary for this slide.
        commentary = _generate_slide_commentary(
            slide_content=slide_content,
            system_prompt=_DEFAULT_SYSTEM_PROMPT,
            model="",
        )
        slide_output.append(commentary)
        slide_output.append("")
        # Add to output parts.
        output_parts.append("\n".join(slide_output))
    # Combine all slides.
    full_output = "\n".join(output_parts)
    # Format output with prettier.
    _LOG.info("Formatting output with prettier")
    full_output = hdockexe.prettier_on_str(full_output, "md")
    # Write output file.
    output_file = os.path.join(output_dir, f"{base_name}.book_chapter.txt")
    _LOG.info("Writing output to: %s", output_file)
    hio.to_file(output_file, full_output)
    _LOG.info("Book chapter generation completed")


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_file",
        action="store",
        required=True,
        help="Input markdown file with slides (e.g., Lesson01.1-Intro.txt)",
    )
    # Create mutually exclusive group for PNG dir or PDF file.
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input_png_dir",
        action="store",
        help="Directory containing PNG files (slides001.png, slides002.png, etc.)",
    )
    input_group.add_argument(
        "--input_pdf_file",
        action="store",
        help="PDF file to extract PNG images from",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        required=True,
        help="Output directory to save results",
    )
    parser.add_argument(
        "--dpi",
        action="store",
        type=int,
        default=200,
        help="DPI for PDF extraction (default: 200)",
    )
    parser.add_argument(
        "--image_width",
        action="store",
        type=str,
        default="80%",
        help="Width of images in output markdown (e.g., 80%%, 50%%) (default: 80%%)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Generate the book chapter.
    _generate_book_chapter(
        input_file=args.input_file,
        output_dir=args.output_dir,
        input_png_dir=args.input_png_dir,
        input_pdf_file=args.input_pdf_file,
        dpi=args.dpi,
        image_width=args.image_width,
    )


if __name__ == "__main__":
    _main(_parse())
