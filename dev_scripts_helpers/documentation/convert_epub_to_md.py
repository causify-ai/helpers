#!/usr/bin/env python

"""
Convert EPUB file to markdown using Dockerized `pandoc` and save images.
The script removes junk content and lints the output.

Usage:
> convert_epub_to_md.py --input document.epub --output document.md

The output will contain:
- document.md: The converted markdown file
- document.md.figs/: Directory containing extracted images from the EPUB
"""

import argparse
import logging
import os
import shutil

import helpers.hdbg as hdbg
import helpers.hlint as hlint
import helpers.hio as hio
import helpers.hparser as hparser
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
    # No media directory found.
    else:
        _LOG.info("No media directory found")


def _fix_image_paths(md_file: str, images_dir_name: str) -> None:
    """
    Fix image paths in the generated markdown to use the images directory.

    Pandoc generates image references relative to the markdown file's location.
    This function updates them to use the correct relative path.

    :param md_file: Path to the markdown file
    :param images_dir_name: Name of the images directory (for path replacement)
    """
    _LOG.info("Fixing image paths in markdown...")
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    # Replace media/ references with images directory references.
    original_content = content
    content = content.replace("](media/", f"]({images_dir_name}/")
    if content != original_content:
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)
        _LOG.info("Image paths updated")
    # No image paths to update.
    else:
        _LOG.debug("No image paths to update")


# Parse command-line arguments.
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
        required=False,
        type=str,
        help="Output markdown file (default: replace .epub with .md in input filename)",
    )
    parser.add_argument(
        "--skip_figures",
        action="store_true",
        help="Skip processing figures and images when converting to markdown",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete target files if they already exist",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    # Return configured parser.
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
    # Determine output markdown file path.
    if args.output:
        # Use provided output directory.
        output_dir = args.output
        hio.create_dir(output_dir, incremental=True)
        epub_basename = os.path.basename(epub_file)
        md_filename = os.path.splitext(epub_basename)[0] + ".md"
        md_file = os.path.join(output_dir, md_filename)
    # Use same name as input, replacing .epub with .md.
    else:
        md_file = os.path.splitext(epub_file)[0] + ".md"
    # Images directory uses markdown filename with .figs extension.
    md_dir = os.path.dirname(md_file)
    md_basename = os.path.basename(md_file)
    images_dir = os.path.join(md_dir, f"{md_basename}.figs")
    images_dir_name = f"{md_basename}.figs"
    # Check for existing files.
    if os.path.exists(md_file) or os.path.exists(images_dir):
        if args.overwrite:
            if os.path.exists(md_file):
                os.remove(md_file)
                _LOG.info("Deleted existing output file: %s", md_file)
            if os.path.exists(images_dir):
                shutil.rmtree(images_dir)
                _LOG.info("Deleted existing images directory: %s", images_dir)
        else:
            raise ValueError(
                f"Output file already exists: {md_file} (use --overwrite to replace)"
            )
    if not skip_figures:
        hio.create_dir(images_dir, incremental=True)
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    add_frame = True
    actions_as_str = hparser.actions_to_string(
        actions, _VALID_ACTIONS, add_frame
    )
    _LOG.info("\n%s", actions_as_str)
    _LOG.info("Converting EPUB: %s", epub_file)
    _LOG.info("Output markdown: %s", md_file)
    if not skip_figures:
        _LOG.info("Images directory: %s", images_dir)
    extract_media_part = f"--extract-media={images_dir}" if not skip_figures else ""
    cmd = (
        f"pandoc {epub_file} "
        f"--to=gfm "
        f"--wrap=none "
        f"{extract_media_part} "
        f"-o {md_file}"
    ).strip()
    container_type = "pandoc_only"
    _LOG.info("Running pandoc conversion...")
    dshdlipa.run_dockerized_pandoc(cmd, container_type)
    if not skip_figures:
        _move_media(images_dir)
        _fix_image_paths(md_file, images_dir_name)
    _LOG.info("Conversion completed successfully")
    _LOG.info("Markdown file: %s", md_file)
    if not skip_figures:
        _LOG.info("Images saved to: %s", images_dir)
    # Execute selected actions.
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
        hlint.lint_file(md_file)


if __name__ == "__main__":
    _main(_parse())
