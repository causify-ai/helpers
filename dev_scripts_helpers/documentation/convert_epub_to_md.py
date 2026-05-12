#!/usr/bin/env python

"""
Convert EPUB file to markdown using Dockerized `pandoc` and save images in a
directory.

Usage:

> convert_epub_to_md.py --input document.epub --output output_dir

The output will contain:
- document.md: The converted markdown file
- images/: Directory containing extracted images from the EPUB
"""

import argparse
import logging
import os
import shutil
from pathlib import Path

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import dev_scripts_helpers.documentation.documentation_utils as dshddout

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = ["remove_junk", "lint"]
_DEFAULT_ACTIONS = ["remove_junk", "lint"]


def _move_media(images_dir: str) -> None:
    """
    Move extracted media files to the images directory.

    Pandoc extracts media to a `media` subdirectory. This function flattens
    that structure by moving all files directly into the images directory.

    :param images_dir: Path to the images directory
    """
    _LOG.info("Moving media files...")
    media_dir = os.path.join(images_dir, "media")
    if os.path.isdir(media_dir):
        for file_name in os.listdir(media_dir):
            file_path = os.path.join(media_dir, file_name)
            dest_path = os.path.join(images_dir, file_name)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.move(file_path, dest_path)
        shutil.rmtree(media_dir)
        _LOG.info("Media files moved successfully")
    else:
        _LOG.info("No media directory found")


def _fix_image_paths(md_file: str) -> None:
    """
    Fix image paths in the generated markdown to use the `images/` prefix.

    Pandoc generates image references relative to the markdown file's location.
    This function updates them to use the correct relative path.

    :param md_file: Path to the markdown file
    """
    _LOG.info("Fixing image paths in markdown...")
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        # Replace media/ references with images/ references.
        # Pattern: ![alt](media/filename) -> ![alt](images/filename)
        original_content = content
        content = content.replace("](media/", "](images/")
        if content != original_content:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(content)
            _LOG.info("Image paths updated")
        else:
            _LOG.debug("No image paths to update")
    except Exception as e:
        _LOG.warning("Failed to fix image paths: %s", str(e))


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: Argument parser with configured options
    """
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
        help="The EPUB file to convert to Markdown",
    )
    parser.add_argument(
        "--output",
        "-o",
        action="store",
        required=True,
        type=str,
        help="The output directory for markdown and images",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main conversion logic.

    :param parser: Argument parser with user inputs
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input file.
    epub_file = args.input
    hdbg.dassert_file_exists(epub_file, "EPUB file does not exist")
    # Prepare output directory structure.
    output_dir = Path(args.output)
    hio.create_dir(str(output_dir), incremental=True)
    images_dir = str(output_dir / "images")
    hio.create_dir(images_dir, incremental=True)
    # Generate output markdown filename.
    md_filename = Path(epub_file).stem + ".md"
    md_file = str(output_dir / md_filename)
    _LOG.info("Converting EPUB: %s", epub_file)
    _LOG.info("Output markdown: %s", md_file)
    _LOG.info("Images directory: %s", images_dir)
    # Build pandoc command for EPUB to GFM conversion.
    # Use GitHub Flavored Markdown (gfm) as output format.
    # --wrap=none preserves line breaks as they appear in the source.
    cmd = (
        f"pandoc {epub_file} "
        f"--to=gfm "
        f"--wrap=none "
        f"--extract-media={images_dir} "
        f"-o {md_file}"
    )
    container_type = "pandoc_only"
    _LOG.info("Running pandoc conversion...")
    dshdlipa.run_dockerized_pandoc(cmd, container_type)
    # Move extracted media files to images directory.
    _move_media(images_dir)
    # Fix image path references in the markdown.
    _fix_image_paths(md_file)
    _LOG.info("Conversion completed successfully")
    _LOG.info("Markdown file: %s", md_file)
    _LOG.info("Images saved to: %s", images_dir)
    # Select and execute actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Remove junk from markdown.
    to_execute, actions = hparser.mark_action("remove_junk", actions)
    if to_execute:
        _LOG.info("Removing junk from markdown...")
        content = hio.from_file(md_file)
        content = dshddout.remove_junk(content)
        hio.to_file(md_file, content)
        _LOG.info("Junk removed successfully")
    # Lint the markdown file.
    to_execute, actions = hparser.mark_action("lint", actions)
    if to_execute:
        _LOG.info("Linting markdown file...")
        lint_cmd = f"lint_txt.py --input={md_file}"
        hsystem.system(lint_cmd)


if __name__ == "__main__":
    _main(_parse())
