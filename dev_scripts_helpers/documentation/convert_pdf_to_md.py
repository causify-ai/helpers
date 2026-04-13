#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pymupdf", "pyyaml"]
# ///

"""
Convert PDF file to markdown and extract figures.

# Usage:

1) Run this command to convert a PDF to markdown:

> IN_FILE_NAME="document.pdf"
> OUT_FILE_NAME="document.md"
> convert_pdf_to_md.py --input $IN_FILE_NAME --output $OUT_FILE_NAME

Figures will be extracted to a directory `$OUT_FILE_NAME.figs/` in the same location
as the markdown file.
"""

import argparse
import logging
import os

import fitz

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# PDF Processing
# #############################################################################


def _extract_text_and_images(pdf_path: str, output_dir: str) -> str:
    """
    Extract text and images from PDF using pymupdf.

    :param pdf_path: path to the input PDF file
    :param output_dir: directory to save extracted images
    :return: markdown text with image references
    """
    hdbg.dassert_file_exists(pdf_path)
    hio.create_dir(output_dir, incremental=False)
    _LOG.info("Opening PDF: %s", pdf_path)
    pdf_document = fitz.open(pdf_path)
    markdown_content = []
    image_counter = 0
    fig_dir_name = os.path.basename(output_dir)
    # Process each page.
    for page_num in range(len(pdf_document)):
        _LOG.debug("Processing page %d", page_num + 1)
        page = pdf_document[page_num]
        # Extract text from the page.
        text = page.get_text()  # type: ignore
        if text.strip():
            markdown_content.append(text)
        # Extract images from the page.
        images = page.get_images()
        for img_ref in images:
            image_counter += 1
            # Get image data.
            xref = img_ref[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            # Save image.
            image_filename = f"figure_{image_counter:03d}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            _LOG.debug("Saved image: %s", image_path)
            # Add markdown reference.
            markdown_content.append(
                f"\n![Figure {image_counter}]({fig_dir_name}/{image_filename})\n"
            )
    pdf_document.close()
    _LOG.info("Extracted %d images from PDF", image_counter)
    return "\n".join(markdown_content)


def _clean_markdown(content: str) -> str:
    """
    Clean up extracted markdown content.

    :param content: raw markdown content
    :return: cleaned markdown content
    """
    # Remove excessive blank lines.
    lines = content.split("\n")
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        cleaned_lines.append(line)
        prev_blank = is_blank
    return "\n".join(cleaned_lines).strip()


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        action="store",
        required=True,
        type=str,
        help="The PDF file to convert to Markdown",
    )
    parser.add_argument(
        "--output",
        "-o",
        action="store",
        required=True,
        type=str,
        help="The output Markdown file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    pdf_file = args.input
    md_file = args.output
    # Validate input file exists.
    hdbg.dassert_file_exists(
        pdf_file, "Input PDF file does not exist:", pdf_file
    )
    # Create the folder for the figures.
    md_file_figs = md_file.replace(".md", ".figs")
    _LOG.info("Creating figures directory: %s", md_file_figs)
    # Extract text and images.
    _LOG.info("Extracting text and images from PDF...")
    markdown_content = _extract_text_and_images(pdf_file, md_file_figs)
    # Clean up markdown.
    _LOG.info("Cleaning up markdown content...")
    markdown_content = _clean_markdown(markdown_content)
    # Write markdown to file.
    _LOG.info("Writing markdown to: %s", md_file)
    hio.to_file(md_file, markdown_content)
    _LOG.info(
        "Successfully converted '%s' to '%s'",
        pdf_file,
        md_file,
    )
    _LOG.info("Figures saved to: %s", md_file_figs)


if __name__ == "__main__":
    _main(_parse())
