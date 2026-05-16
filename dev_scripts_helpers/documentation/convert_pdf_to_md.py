#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pymupdf", "pyyaml"]
# ///

r"""
Convert a PDF to Markdown using PyMuPDF (fitz).

The script extracts text and images from a PDF file and converts them to
Markdown format with embedded image references.

Automatically installs dependencies via `uv` if missing.

Usage:
# Convert PDF to markdown with images.
> convert_pdf_to_md.py \
    --input document.pdf \
    --output output_dir

# Convert PDF to markdown without images.
> convert_pdf_to_md.py \
    --input document.pdf \
    --output output_dir \
    --skip_figures

# With verbose logging.
> convert_pdf_to_md.py \
    --input document.pdf \
    --output output_dir \
    -v DEBUG
"""

import argparse
import logging
import os
from typing import Dict, List, Tuple

import fitz

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr

_LOG = logging.getLogger(__name__)

# #############################################################################


def _extract_images_from_page(
    page: fitz.Page,
    *,
    page_num: int,
    images_dir: str,
) -> List[Tuple[float, str, str]]:
    """
    Extract all images from a PDF page with their positions.

    :param page: PyMuPDF page object
    :param page_num: Page number (1-indexed)
    :param images_dir: Directory to save extracted images
    :return: List of tuples (y_position, image_filename, image_markdown)
    """
    image_items = []
    image_list = page.get_images(full=True)
    _LOG.info(
        "Page %d: Found %d images via get_images()", page_num, len(image_list)
    )
    # Track which xrefs we've already processed to avoid duplicates.
    processed_xrefs = set()
    for img_index, img in enumerate(image_list, start=1):
        xref = img[0]
        if xref in processed_xrefs:
            _LOG.debug("Skipping duplicate xref %d", xref)
            continue
        processed_xrefs.add(xref)
        try:
            # Extract image.
            base_image = page.parent.extract_image(xref)  # type: ignore
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            # Get image position on the page.
            rects = page.get_image_rects(xref)  # type: ignore
            if rects:
                # Use the first rectangle's y0 (top) coordinate.
                y_pos = rects[0].y0
                _LOG.debug("Image xref %d positioned at y=%.2f", xref, y_pos)
            else:
                # If no position found, place at end of page.
                y_pos = float("inf")
                _LOG.warning(
                    "Page %d: No position found for image xref %d",
                    page_num,
                    xref,
                )
            # Generate filename.
            image_filename = f"page_{page_num}_img_{img_index}.{image_ext}"
            image_path = os.path.join(images_dir, image_filename)
            # Save image.
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            _LOG.info(
                "Page %d: Saved image %s (xref=%d, size=%d bytes)",
                page_num,
                image_filename,
                xref,
                len(image_bytes),
            )
            # Create markdown reference.
            img_markdown = f"![Figure](images/{image_filename})"
            image_items.append((y_pos, image_filename, img_markdown))
        except Exception as e:
            _LOG.warning(
                "Page %d: Failed to extract image xref %d: %s",
                page_num,
                xref,
                str(e),
            )
    # Try to extract vector graphics as images.
    drawings = page.get_drawings()
    _LOG.info("Page %d: Found %d vector drawings", page_num, len(drawings))
    if drawings:
        # Render the entire page as an image to capture vector graphics.
        # We'll do this only if there are drawings and few raster images.
        if len(image_list) < 3:
            _LOG.info(
                "Page %d: Rendering page to capture vector graphics", page_num
            )
            # Get page dimensions.
            rect = page.rect
            # Render page at 2x resolution for better quality.
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)  # type: ignore
            img_index = len(image_list) + 1
            image_filename = f"page_{page_num}_rendered_{img_index}.png"
            image_path = os.path.join(images_dir, image_filename)
            pix.save(image_path)
            _LOG.info(
                "Page %d: Saved rendered page as %s", page_num, image_filename
            )
            # Position at page center.
            y_pos = rect.height / 2
            img_markdown = f"![Figure (rendered)](images/{image_filename})"
            image_items.append((y_pos, image_filename, img_markdown))
    return image_items


def _analyze_font_sizes(page: fitz.Page) -> Dict:  # type: ignore
    """
    Analyze font sizes in a page to determine heading thresholds.

    :param page: PyMuPDF page object
    :return: Dictionary with font size statistics
    """
    text_dict = page.get_text("dict")  # type: ignore
    font_sizes = []
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    if size > 0:
                        font_sizes.append(size)
    if not font_sizes:
        return {
            "median": 10,
            "h1_threshold": 16,
            "h2_threshold": 14,
            "h3_threshold": 12,
        }
    font_sizes.sort()
    median_size = font_sizes[len(font_sizes) // 2]
    # Thresholds for different heading levels.
    h1_threshold = median_size * 1.5
    h2_threshold = median_size * 1.3
    h3_threshold = median_size * 1.1
    _LOG.debug(
        "Font size analysis: median=%.2f, h1>=%.2f, h2>=%.2f, h3>=%.2f",
        median_size,
        h1_threshold,
        h2_threshold,
        h3_threshold,
    )
    return {
        "median": median_size,
        "h1_threshold": h1_threshold,
        "h2_threshold": h2_threshold,
        "h3_threshold": h3_threshold,
    }


def _extract_text_with_formatting(
    page: fitz.Page,
    *,
    page_num: int,
    font_thresholds: Dict,  # type: ignore
) -> List[Tuple[float, str, str]]:
    """
    Extract text with formatting information to identify headers.

    :param page: PyMuPDF page object
    :param page_num: Page number (1-indexed)
    :param font_thresholds: Dictionary with font size thresholds
    :return: List of tuples (y_position, markdown_type, content)
    """
    text_dict = page.get_text("dict")  # type: ignore
    text_items = []
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        block_y = block.get("bbox", [0, 0, 0, 0])[1]
        # Collect all text and font info from the block.
        block_text = []
        max_font_size = 0
        is_bold = False
        for line in block.get("lines", []):
            line_text = []
            for span in line.get("spans", []):
                text = span.get("text", "")
                size = span.get("size", 0)
                font = span.get("font", "")
                line_text.append(text)
                if size > max_font_size:
                    max_font_size = size
                if "Bold" in font or "bold" in font:
                    is_bold = True
            if line_text:
                block_text.append("".join(line_text))
        if not block_text:
            continue
        content = " ".join(block_text).strip()
        if not content:
            continue
        # Determine markdown type based on font size.
        if max_font_size >= font_thresholds["h1_threshold"]:
            md_type = "h1"
        elif max_font_size >= font_thresholds["h2_threshold"]:
            md_type = "h2"
        elif max_font_size >= font_thresholds["h3_threshold"]:
            md_type = "h3"
        elif is_bold and len(content) < 100:
            md_type = "h3"
        else:
            md_type = "text"
        text_items.append((block_y, md_type, content))
        _LOG.debug(
            "Page %d: Block at y=%.2f, size=%.2f, type=%s: %s",
            page_num,
            block_y,
            max_font_size,
            md_type,
            content[:50],
        )
    return text_items


def _pdf_to_markdown(
    *,
    pdf_path: str,
    output_dir: str,
    skip_figures: bool = False,
) -> None:
    """
    Convert a PDF file to Markdown with extracted images.

    :param pdf_path: Path to input PDF file
    :param output_dir: Directory to save markdown and images
    :param skip_figures: If True, skip image extraction and processing
    """
    hdbg.dassert_file_exists(pdf_path, "PDF file does not exist")
    hdbg.dassert(os.path.isfile(pdf_path), "Path is not a file")
    # Create output directory structure.
    hio.create_dir(output_dir, incremental=True)
    images_dir: str = ""
    if not skip_figures:
        images_dir = os.path.join(output_dir, "images")
        hio.create_dir(images_dir, incremental=True)
    _LOG.info("Opening PDF: %s", pdf_path)
    doc = fitz.open(pdf_path)
    md_lines = []
    total_images = 0
    for page_num, page in enumerate(doc, start=1):  # type: ignore
        _LOG.info("=" * 60)
        _LOG.info("Processing page %d of %d", page_num, len(doc))
        # Analyze font sizes to determine heading thresholds.
        font_thresholds = _analyze_font_sizes(page)
        # Extract images with their positions (if not skipped).
        image_items: List[Tuple[float, str, str]] = []
        if not skip_figures:
            image_items = _extract_images_from_page(
                page,
                page_num=page_num,
                images_dir=images_dir,  # type: ignore
            )
            total_images += len(image_items)
        # Extract text with formatting information.
        text_items = _extract_text_with_formatting(
            page,
            page_num=page_num,
            font_thresholds=font_thresholds,
        )
        _LOG.info("Page %d: Found %d text items", page_num, len(text_items))
        # Create items list with both text and images.
        # Each item is (y_position, type, content).
        items = []
        # Add text items.
        for y_pos, md_type, content in text_items:
            items.append((y_pos, md_type, content))
        # Add images.
        for y_pos, _, img_markdown in image_items:
            items.append((y_pos, "image", img_markdown))
        # Sort all items by y-position (top to bottom).
        items.sort(key=lambda x: x[0])
        # Add page marker.
        md_lines.append(f"\n\n<!-- Page {page_num} -->\n\n")
        # Process items in order.
        for y_pos, item_type, content in items:
            if item_type == "h1":
                md_lines.append(f"# {content}")
            elif item_type == "h2":
                md_lines.append(f"## {content}")
            elif item_type == "h3":
                md_lines.append(f"### {content}")
            elif item_type == "text":
                md_lines.append(content)
            elif item_type == "image":
                md_lines.append(content)
                _LOG.debug("Inserted image at y=%.2f", y_pos)
    # Save markdown file.
    markdown_content = "\n\n".join(md_lines)
    # Apply prettier formatting to the markdown.
    _LOG.info("Applying prettier formatting to markdown")
    markdown_content = dshdlipr.prettier_on_str(
        markdown_content,
        file_type="md",
        print_width=80,
    )
    pdf_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    md_filename = pdf_stem + ".md"
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    _LOG.info("=" * 60)
    if not skip_figures:
        _LOG.info("Extracted %d total images", total_images)
        _LOG.info("Images saved to: %s", os.path.abspath(images_dir))
    else:
        _LOG.info("Figure extraction was skipped")
    _LOG.info("Markdown saved to: %s", os.path.abspath(md_path))


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Path to input PDF file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        default=".",
        help="Output directory for markdown and images (default: current directory)",
    )
    parser.add_argument(
        "--skip_figures",
        action="store_true",
        help="Skip processing figures and images from the PDF",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Run conversion.
    _pdf_to_markdown(
        pdf_path=args.input,
        output_dir=args.output,
        skip_figures=args.skip_figures,
    )


if __name__ == "__main__":
    _main(_parse())
