#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pymupdf", "pyyaml", "tqdm"]
# ///

r"""
Convert a PDF to Markdown using PyMuPDF (fitz).

The script extracts text and images from a PDF file and converts them to
Markdown format with embedded image references.

Automatically installs dependencies via `uv` if missing.

Usage:
# Convert PDF to markdown with images.
> convert_pdf_to_md.py --input document.pdf --action convert --output output_dir

# Convert PDF to markdown without images.
> convert_pdf_to_md.py \
    --input document.pdf \
    --action convert \
    --output output_dir \
    --skip_figures

# Clean an existing markdown file (remove PDF conversion artifacts).
> convert_pdf_to_md.py --input document.pdf --action remove_junk
"""

import argparse
import logging
import os
import re
import shutil
from typing import cast, Dict, List, Optional, Tuple

import fitz
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_VALID_ACTIONS = ["convert", "remove_junk"]
_DEFAULT_ACTIONS = ["convert", "remove_junk"]

# #############################################################################


def _remove_junk(*, pdf_path: str, output_dir: Optional[str] = None) -> None:
    """
    Remove artifacts from PDF conversion including page markers and page numbers.

    Removes:
    - HTML comments like "<!-- Page 12 -->"
    - Standalone page number headings like "### 11"
    - Excessive blank lines

    :param pdf_path: Path to input PDF file (used to derive markdown file name)
    :param output_dir: Directory containing the markdown file; defaults to input file's directory
    """
    hdbg.dassert_file_exists(pdf_path, "PDF file does not exist")
    # Derive output directory from input file location when not specified.
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(pdf_path))
    if not output_dir:
        output_dir = "."
    # Compute markdown path using the PDF stem.
    pdf_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    md_filename = pdf_stem + ".md"
    md_path = os.path.join(output_dir, md_filename)
    hdbg.dassert_file_exists(md_path, "Markdown file does not exist")
    # Read the markdown file content.
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    original_content = content
    # Remove HTML page marker comments like "<!-- Page 12 -->".
    content = re.sub(r"<!--\s*Page\s+\d+\s*-->\n*", "", content)
    # Remove standalone page number headings such as "### 11".
    content = re.sub(r"^#+\s+\d+\s*$", "", content, flags=re.MULTILINE)
    # Remove excessive blank lines (more than 2 consecutive newlines).
    content = re.sub(r"\n\n\n+", "\n\n", content)
    content = content.strip() + "\n"
    # Write cleaned content back to file if changes were made.
    if content != original_content:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)
        _LOG.info("Removed PDF junk from: %s", os.path.abspath(md_path))
    else:
        _LOG.info("No PDF junk found in: %s", os.path.abspath(md_path))


# #############################################################################


def _extract_images_from_page(
    page: fitz.Page,
    *,
    page_num: int,
    images_dir: str,
    images_dir_name: str,
    save_images: bool = True,
) -> List[Tuple[float, str, str]]:
    """
    Extract all images from a PDF page with their positions.

    :param page: PyMuPDF page object
    :param page_num: Page number (1-indexed)
    :param images_dir: Directory to save extracted images (used only when `save_images` is True)
    :param images_dir_name: Directory name used in markdown image references
    :param save_images: If True, save image files to disk; if False, only detect images
    :return: List of tuples (y_position, image_filename, image_markdown)
    """
    image_items = []
    # Extract raster images from page.
    image_list = page.get_images(full=True)
    _LOG.debug(
        "Page %d: Found %d images via get_images()", page_num, len(image_list)
    )
    # Track which xrefs we have already processed to avoid duplicates.
    processed_xrefs = set()
    for img_index, img in enumerate(image_list, start=1):
        xref = img[0]
        if xref in processed_xrefs:
            _LOG.debug("Skipping duplicate xref %d", xref)
            continue
        processed_xrefs.add(xref)
        try:
            # Extract image from the PDF.
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
                # Place image at end of page if no position found.
                y_pos = float("inf")
                _LOG.warning(
                    "Page %d: No position found for image xref %d",
                    page_num,
                    xref,
                )
            # Generate image filename for this page and index.
            image_filename = f"page_{page_num}_img_{img_index}.{image_ext}"
            image_path = os.path.join(images_dir, image_filename)
            # Save image to disk only when not skipping figures.
            if save_images:
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                _LOG.debug(
                    "Page %d: Saved image %s (xref=%d, size=%d bytes)",
                    page_num,
                    image_filename,
                    xref,
                    len(image_bytes),
                )
            # Create markdown reference with the images directory name.
            img_markdown = f"![Figure]({images_dir_name}/{image_filename})"
            image_items.append((y_pos, image_filename, img_markdown))
        except Exception as e:
            _LOG.warning(
                "Page %d: Failed to extract image xref %d: %s",
                page_num,
                xref,
                str(e),
            )
    # Extract vector graphics by rendering page as image.
    drawings = page.get_drawings()
    _LOG.debug("Page %d: Found %d vector drawings", page_num, len(drawings))
    if drawings:
        # Render page as image to capture vector graphics if there are few raster images.
        if len(image_list) < 3:
            img_index = len(image_list) + 1
            image_filename = f"page_{page_num}_rendered_{img_index}.png"
            image_path = os.path.join(images_dir, image_filename)
            # Render and save page to disk only when not skipping figures.
            if save_images:
                _LOG.debug(
                    "Page %d: Rendering page to capture vector graphics",
                    page_num,
                )
                rect = page.rect
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)  # type: ignore
                pix.save(image_path)
                _LOG.debug(
                    "Page %d: Saved rendered page as %s",
                    page_num,
                    image_filename,
                )
                y_pos = rect.height / 2
            else:
                # Approximate position at page center when not saving figures.
                y_pos = page.rect.height / 2
            img_markdown = (
                f"![Figure (rendered)]({images_dir_name}/{image_filename})"
            )
            image_items.append((y_pos, image_filename, img_markdown))
    return image_items


def _analyze_font_sizes(page: fitz.Page) -> Dict[str, float]:  # type: ignore
    """
    Analyze font sizes in a page to determine heading thresholds.

    :param page: PyMuPDF page object
    :return: Dictionary with font size statistics
        - Keys: "median", "h1_threshold", "h2_threshold", "h3_threshold"
        - Values: Computed font size thresholds as floats
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
    # Return default thresholds if no font sizes detected.
    if not font_sizes:
        return {
            "median": 10,
            "h1_threshold": 16,
            "h2_threshold": 14,
            "h3_threshold": 12,
        }
    # Compute heading thresholds based on median font size.
    font_sizes.sort()
    median_size = font_sizes[len(font_sizes) // 2]
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
    font_thresholds: Dict[str, float],  # type: ignore
) -> List[Tuple[float, str, str]]:
    """
    Extract text with formatting information to identify headers.

    :param page: PyMuPDF page object
    :param page_num: Page number (1-indexed)
    :param font_thresholds: Dictionary with font size thresholds
        - Keys: "h1_threshold", "h2_threshold", "h3_threshold"
        - Values: Minimum font sizes for each heading level
    :return: List of tuples (y_position, markdown_type, content)
        - y_position: Vertical position on page
        - markdown_type: "h1", "h2", "h3", or "text"
        - content: Extracted text content
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
        # Format text content from the block.
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
    output_dir: Optional[str],
    skip_figures: bool = False,
    overwrite: bool = False,
) -> None:
    """
    Convert a PDF file to Markdown with extracted images.

    :param pdf_path: Path to input PDF file
    :param output_dir: Directory to save markdown and images; defaults to input file's directory
    :param skip_figures: If True, do not extract images; include references as HTML comments
    :param overwrite: If True, delete existing output files before conversion
    """
    hdbg.dassert_file_exists(pdf_path, "PDF file does not exist")
    # Derive output directory from input file location when not specified.
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(pdf_path))
    if not output_dir:
        output_dir = "."
    hio.create_dir(output_dir, incremental=True)
    # Compute output paths and directory names using the PDF stem.
    pdf_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    images_dir_name = f"{pdf_stem}.figs"
    images_dir = os.path.join(output_dir, images_dir_name)
    md_filename = pdf_stem + ".md"
    md_path = os.path.join(output_dir, md_filename)
    # Handle existing output files: delete if overwrite flag is set.
    if os.path.exists(md_path) or os.path.exists(images_dir):
        if overwrite:
            if os.path.exists(md_path):
                os.remove(md_path)
                _LOG.info("Deleted existing output file: %s", md_path)
            if os.path.exists(images_dir):
                shutil.rmtree(images_dir)
                _LOG.info("Deleted existing images directory: %s", images_dir)
        else:
            raise ValueError(
                f"Output file already exists: {md_path} (use --overwrite to replace)"
            )
    # Create images directory to store extracted figures.
    if not skip_figures:
        hio.create_dir(images_dir, incremental=True)
    # Open PDF and prepare for extraction.
    _LOG.debug("Opening PDF: %s", pdf_path)
    doc = fitz.open(pdf_path)
    md_lines = []
    total_images = 0
    # Process each page of the PDF.
    for page_num, page in tqdm(
        enumerate(doc, start=1),  # type: ignore
        total=len(doc),
        desc="Extracting pages",
    ):
        page = cast(fitz.Page, page)
        _LOG.debug("=" * 60)
        _LOG.debug("Processing page %d of %d", page_num, len(doc))
        # Analyze font sizes to determine heading thresholds.
        font_thresholds = _analyze_font_sizes(page)
        # Extract images with positions (save files only when not skipping figures).
        image_items = _extract_images_from_page(
            page,
            page_num=page_num,
            images_dir=images_dir,
            images_dir_name=images_dir_name,
            save_images=not skip_figures,
        )
        total_images += len(image_items)
        # Extract text with formatting information.
        text_items = _extract_text_with_formatting(
            page,
            page_num=page_num,
            font_thresholds=font_thresholds,
        )
        _LOG.debug("Page %d: Found %d text items", page_num, len(text_items))
        # Create items list combining text and images, each as (y_position, type, content).
        items = []
        for y_pos, md_type, content in text_items:
            items.append((y_pos, md_type, content))
        for y_pos, _, img_markdown in image_items:
            items.append((y_pos, "image", img_markdown))
        # Sort all items by y-position to maintain document order.
        items.sort(key=lambda x: x[0])
        # Add page marker comment.
        md_lines.append(f"\n\n<!-- Page {page_num} -->\n\n")
        # Process items in order and format as markdown.
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
                # Comment out image references when figures are skipped.
                if skip_figures:
                    md_lines.append(f"<!-- {content} -->")
                else:
                    md_lines.append(content)
                _LOG.debug("Inserted image at y=%.2f", y_pos)
    # Join markdown lines and apply prettier formatting.
    markdown_content = "\n\n".join(md_lines)
    _LOG.info("Applying prettier formatting to markdown")
    markdown_content = dshdlipr.prettier_on_str(
        markdown_content,
        file_type="md",
        print_width=80,
    )
    # Write formatted markdown to file.
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    _LOG.debug("=" * 60)
    # Log extraction results based on figure skip setting.
    if not skip_figures:
        _LOG.debug("Extracted %d total images", total_images)
        _LOG.debug("Images saved to: %s", os.path.abspath(images_dir))
    else:
        _LOG.debug(
            "Image references included as HTML comments (figures skipped)"
        )
    _LOG.info("Markdown saved to: %s", os.path.abspath(md_path))


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for the PDF to markdown conversion script.

    :return: Configured `ArgumentParser` instance with all required and optional arguments
    """
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
        default=None,
        help="Output directory for markdown and images (default: same directory as input)",
    )
    parser.add_argument(
        "--skip_figures",
        action="store_true",
        help="Skip processing figures and images from the PDF",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete target files if they already exist",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the main script logic for PDF to markdown conversion.

    Parses command-line arguments and executes selected actions (convert and/or
    remove_junk) based on user input.

    :param parser: Configured `ArgumentParser` instance
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Execute convert action.
#    # TODO(ai_gp): Use the --action functions in hparser.py
    if "convert" in actions:
        _pdf_to_markdown(
            pdf_path=args.input,
            output_dir=args.output,
            skip_figures=args.skip_figures,
            overwrite=args.overwrite,
        )
    # Execute remove_junk action for cleanup.
    if "remove_junk" in actions:
        _remove_junk(pdf_path=args.input, output_dir=args.output)


if __name__ == "__main__":
    _main(_parse())
