#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from pathlib import Path

import helpers.hdbg as hdbg
import helpers.hsystem as hsystem

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

_LOG = logging.getLogger(__name__)


def extract_slides_pandoc(ppt_path: str, output_dir: str) -> bool:
    """
    Extract slides as images using pandoc.
    
    :param ppt_path: path to PowerPoint presentation file
    :param output_dir: directory to save extracted slides
    :return: True if extraction successful
    """
    hdbg.dassert(os.path.exists(ppt_path), f"PowerPoint file not found: {ppt_path}")
    _LOG.debug(f"Extracting slides from {ppt_path} to {output_dir}")
    try:
        # Build pandoc command to extract slides as images
        output_pattern = os.path.join(output_dir, "slide_%03d.png")
        cmd = f'pandoc "{ppt_path}" --extract-media "{output_dir}" -o "{output_pattern}"'
        _LOG.debug(f"Running command: {cmd}")
        # Execute pandoc command using hsystem
        rc, output = hsystem.system_to_string(cmd, abort_on_error=False)
        if rc == 0:
            _LOG.info("Pandoc extraction successful")
            return True
        else:
            _LOG.error(f"Pandoc failed with return code {rc}: {output}")
            hdbg.dfatal(f"Pandoc error: {output}")
    except Exception as e:
        _LOG.error(f"Error during pandoc extraction: {e}")
        hdbg.dfatal(f"Error with pandoc: {e}")


def extract_notes_text(ppt_path: str, output_dir: str):
    """
    Extract notes from PowerPoint presentation.
    
    :param ppt_path: path to PowerPoint presentation file
    :param output_dir: directory to save extracted notes
    """
    hdbg.dassert(os.path.exists(ppt_path), f"PowerPoint file not found: {ppt_path}")
    _LOG.debug(f"Extracting notes from {ppt_path}")
    try:
        presentation = Presentation(ppt_path)
        all_notes = []
        # Process each slide to extract notes
        for i, slide in enumerate(presentation.slides, 1):
            slide_notes = []
            # Check if slide has notes and extract them
            if slide.has_notes_slide:
                notes_slide = slide.notes_slide
                # Extract text from all shapes in notes slide
                for shape in notes_slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_notes.append(shape.text.strip())
            # Prepare notes content for this slide
            notes_content = "\n".join(slide_notes) if slide_notes else "No notes"
            # Write individual slide notes file
            slide_notes_path = os.path.join(output_dir, f"slide_{i:03d}_notes.txt")
            with open(slide_notes_path, 'w', encoding='utf-8') as f:
                f.write(f"Slide {i} Notes:\n")
                f.write("=" * 20 + "\n")
                f.write(notes_content)
                f.write("\n")
            all_notes.append(f"Slide {i}:\n{notes_content}\n")
        # Write combined notes file
        all_notes_path = os.path.join(output_dir, "all_notes.txt")
        with open(all_notes_path, 'w', encoding='utf-8') as f:
            f.write("PowerPoint Presentation Notes\n")
            f.write("=" * 30 + "\n\n")
            f.write("\n".join(all_notes))
        _LOG.info(f"Extracted notes for {len(presentation.slides)} slides")
    except Exception as e:
        _LOG.error(f"Error extracting notes: {e}")
        raise


def extract_text_content(ppt_path: str, output_dir: str):
    """
    Extract all text content from slides.
    
    :param ppt_path: path to PowerPoint presentation file
    :param output_dir: directory to save extracted text content
    """
    hdbg.dassert(os.path.exists(ppt_path), f"PowerPoint file not found: {ppt_path}")
    _LOG.debug(f"Extracting text content from {ppt_path}")
    try:
        presentation = Presentation(ppt_path)
        all_text = []
        # Process each slide to extract text content
        for i, slide in enumerate(presentation.slides, 1):
            slide_text = []
            # Extract text from all shapes in slide
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
                # Handle table shapes specifically
                elif shape.shape_type == MSO_SHAPE_TYPE.TABLE:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                slide_text.append(cell.text.strip())
            # Prepare text content for this slide
            text_content = "\n".join(slide_text) if slide_text else "No text content"
            # Write individual slide text file
            slide_text_path = os.path.join(output_dir, f"slide_{i:03d}_text.txt")
            with open(slide_text_path, 'w', encoding='utf-8') as f:
                f.write(f"Slide {i} Text Content:\n")
                f.write("=" * 25 + "\n")
                f.write(text_content)
                f.write("\n")
            all_text.append(f"Slide {i}:\n{text_content}\n")
        # Write combined text content file
        all_text_path = os.path.join(output_dir, "all_text_content.txt")
        with open(all_text_path, 'w', encoding='utf-8') as f:
            f.write("PowerPoint Presentation Text Content\n")
            f.write("=" * 35 + "\n\n")
            f.write("\n".join(all_text))
        _LOG.info(f"Extracted text content for {len(presentation.slides)} slides")
    except Exception as e:
        _LOG.error(f"Error extracting text content: {e}")
        raise


def _check_platform() -> None:
    """
    Check that the script is running on Linux or MacOS.
    
    :raises: SystemExit if running on unsupported platform
    """
    platform = sys.platform.lower()
    if not (platform.startswith('linux') or platform.startswith('darwin')):
        _LOG.error(f"Unsupported platform: {platform}. This script only works on Linux and MacOS.")
        sys.exit(1)
    _LOG.debug(f"Running on supported platform: {platform}")


def main():
    """
    Main function to extract slides, notes, and text content from PowerPoint presentations.
    """
    # Check platform compatibility
    _check_platform()
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Extract slides from PowerPoint presentation as images using pandoc and save notes as text files"
    )
    parser.add_argument("ppt_file", help="Path to PowerPoint presentation file")
    parser.add_argument(
        "-o", "--output-dir", 
        help="Output directory (default: presentation_name_extracted)"
    )
    parser.add_argument(
        "--check-pandoc", 
        action="store_true",
        help="Check if pandoc is available before processing"
    )
    args = parser.parse_args()
    # Validate input file
    ppt_path = args.ppt_file
    hdbg.dassert(os.path.exists(ppt_path), f"PowerPoint file not found: {ppt_path}")
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        ppt_name = Path(ppt_path).stem
        output_dir = f"{ppt_name}_extracted"
    os.makedirs(output_dir, exist_ok=True)
    _LOG.info(f"Extracting presentation: {ppt_path}")
    _LOG.info(f"Output directory: {output_dir}")
    # Check pandoc availability if requested
    if args.check_pandoc:
        try:
            rc, output = hsystem.system_to_string("pandoc --version", abort_on_error=False)
            if rc == 0:
                version_line = output.strip().split('\n')[0]
                _LOG.info(f"Pandoc found: {version_line}")
            else:
                hdbg.dfatal("Pandoc not available")
        except Exception as e:
            _LOG.error(f"Error checking pandoc: {e}")
            hdbg.dfatal("Pandoc not found in PATH")
    # Extract slides using pandoc
    _LOG.info("Extracting slides using pandoc...")
    extract_slides_pandoc(ppt_path, output_dir)
    _LOG.info("Successfully extracted slides using pandoc")
    # Extract notes from presentation
    _LOG.info("Extracting notes...")
    extract_notes_text(ppt_path, output_dir)
    # Extract text content from slides
    _LOG.info("Extracting text content...")
    extract_text_content(ppt_path, output_dir)
    _LOG.info(f"Extraction complete! Check the '{output_dir}' directory.")


if __name__ == "__main__":
    main()