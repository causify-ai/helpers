#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "pdf2image",
#   "pillow",
#   "pyyaml",
#   "tqdm",
# ]
# ///

"""
Extract PNG images from PDF files, one image per page.

This script converts each page of a PDF file into a PNG image file.
The output files are named sequentially (slides001.png, slides002.png, etc.)
and saved to the specified output directory.

Examples:
# Extract all pages from a PDF file.
> extract_png_from_pdf.py --input_file data605/lectures/Lesson01.1-Intro.pdf --output_dir output

# Extract with custom DPI for higher quality.
> extract_png_from_pdf.py --input_file lecture.pdf --output_dir slides --dpi 300
"""

import argparse
import logging
import os

import pdf2image
import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _extract_png_from_pdf(
    input_file: str,
    output_dir: str,
    *,
    dpi: int = 200,
    from_scratch: bool = False,
) -> None:
    """
    Extract PNG images from PDF file, one per page.

    :param input_file: path to input PDF file
    :param output_dir: directory to save PNG files
    :param dpi: DPI resolution for output images (higher = better quality)
    :param from_scratch: if True, create output directory from scratch
    """
    hdbg.dassert_file_exists(
        input_file, "Input file does not exist:", input_file
    )
    _LOG.info("Processing PDF file: %s", input_file)
    # Create output directory.
    incremental = not from_scratch
    hio.create_dir(output_dir, incremental=incremental)
    _LOG.info("Output directory: %s", output_dir)
    # Convert PDF pages to images.
    _LOG.info("Converting PDF to images with DPI=%d", dpi)
    images = pdf2image.convert_from_path(input_file, dpi=dpi)
    num_pages = len(images)
    hdbg.dassert_lt(0, num_pages, "No pages found in PDF file:", input_file)
    _LOG.info("Found %d pages in PDF", num_pages)
    # Save each page as a PNG file.
    for page_num, image in enumerate(
        tqdm.tqdm(images, desc="Extracting pages"), start=1
    ):
        # Format filename with zero-padded page number.
        output_filename = f"slides{page_num:03d}.png"
        output_path = os.path.join(output_dir, output_filename)
        # Save image as PNG.
        image.save(output_path, "PNG")
        _LOG.debug("Saved: %s", output_filename)
    _LOG.info(
        "Successfully extracted %d PNG images to %s", num_pages, output_dir
    )


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
        help="Path to input PDF file",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        required=True,
        help="Directory to save output PNG files",
    )
    parser.add_argument(
        "--dpi",
        action="store",
        type=int,
        default=300,
        help="DPI resolution for output images (default: 300)",
    )
    parser.add_argument(
        "--from_scratch",
        action="store_true",
        help="Create output directory from scratch",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Extract PNG images from PDF.
    _extract_png_from_pdf(
        input_file=args.input_file,
        output_dir=args.output_dir,
        dpi=args.dpi,
        from_scratch=args.from_scratch,
    )


if __name__ == "__main__":
    _main(_parse())
