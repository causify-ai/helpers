#!/usr/bin/env python

"""
This script takes markdown files from an input directory and processes them
for mkdocs by:
1. Copying all files from input to output directory
2. Running a series of markdown transformations
    - Removing table of contents between <!-- toc --> and <!-- tocstop -->
    - Dedenting Python code blocks so they are aligned
    - Replacing 2 spaces indentation with 4 spaces
3. (Optional) Rendering mermaid/plantuml diagrams to images

Example usage:
> preprocess_mkdocs.py --input_dir docs --output_dir tmp.mkdocs
> preprocess_mkdocs.py --input_dir docs --output_dir tmp.mkdocs --render_images

Import as:

import preprocess_mkdocs as premkdo
"""

import argparse
import logging
import os
import sys

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmkdocs as hmkdocs
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        action="store",
        required=True,
        help="Input directory containing markdown files",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        required=True,
        help="Output directory for processed files",
    )
    parser.add_argument(
        "--render_images",
        action="store_true",
        help="Render mermaid/plantuml diagrams to images",
    )
    parser.add_argument(
        "--use_github_hosting",
        action="store_true",
        help="Use GitHub-hosted absolute URLs for images",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _copy_directory(input_dir: str, output_dir: str) -> None:
    """
    Copy all files from input directory to output directory.

    :param input_dir: Source directory path
    :param output_dir: Destination directory path
    """
    hdbg.dassert(
        os.path.exists(input_dir),
        f"Input directory '{input_dir}' does not exist",
    )
    # Remove output directory if it exists and create fresh one.
    if os.path.exists(output_dir):
        cmd = f"chmod -R u+w {output_dir} && rm -rf {output_dir}"
        hsystem.system(cmd)
    # Create fresh directory
    cmd = f"mkdir -p {output_dir}"
    hsystem.system(cmd)
    # Copy the entire directory tree and make files writable.
    cmd = f"cp -rL {input_dir}/* {output_dir} && chmod -R u+w {output_dir}"
    hsystem.system(cmd)
    _LOG.info("Copied directory from '%s' to '%s'", input_dir, output_dir)


def _render_images_in_file(
    file_path: str,
    force_rebuild: bool = False,
    use_sudo: bool = False,
    use_github_hosting: bool = False,
) -> None:
    """
    Render images in a markdown file (PlantUML, Mermaid, etc.).

    :param file_path: Path to the markdown file to process
    :param force_rebuild: force rebuild of Docker images
    :param use_sudo: use sudo for Docker commands
    :param use_github_hosting: Use GitHub absolute URLs for images
    """
    # Add the dev_scripts_helpers/documentation directory to path
    helpers_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    render_images_dir = os.path.join(
        helpers_root, "dev_scripts_helpers", "documentation"
    )
    if render_images_dir not in sys.path:
        sys.path.insert(0, render_images_dir)
    import dev_scripts_helpers.documentation.render_images as dshdreim

    # Read the file.
    in_lines = hio.from_file(file_path).split("\n")
    # Render images (in-place, using png).
    out_lines = dshdreim._render_images(
        in_lines,
        out_file=file_path,
        dst_ext="png",
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
        dry_run=False,
        use_github_hosting=use_github_hosting,
    )
    # Write back.
    hio.to_file(file_path, "\n".join(out_lines))
    _LOG.info(f"Successfully rendered images in: {file_path}")


def _process_markdown_files(
    directory: str,
    render_images: bool = False,
    use_github_hosting: bool = False,
) -> None:
    """
    Process all markdown files in the given directory recursively.

    :param directory: Directory to process
    :param render_images: Whether to render mermaid/plantuml diagrams
    :param use_github_hosting: Use GitHub absolute URLs for images
    """
    # Files to skip for image rendering (contain example snippets, not real diagrams).
    skip_image_rendering = [
        "all.architecture_diagrams.explanation.md",
    ]
    directories = sorted(os.walk(directory))
    _LOG.info("Processing %s markdown files", len(directories))
    for root, dirs, files in directories:
        _ = dirs
        files = sorted(files)
        _LOG.info("Processing %s markdown files in '%s'", len(files), root)
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                _LOG.info("Processing markdown file: %s", file_path)
                # Read the file.
                content = hio.from_file(file_path)
                # Apply preprocessing.
                processed_content = hmkdocs.preprocess_mkdocs_markdown(content)
                # Write back to the same file.
                hio.to_file(file_path, processed_content)
                # Render images if requested (skip files with example snippets).
                if render_images and file not in skip_image_rendering:
                    _LOG.info(f"Rendering images in: {file_path}")
                    _render_images_in_file(
                        file_path,
                        use_github_hosting=use_github_hosting,
                    )
                elif render_images and file in skip_image_rendering:
                    _LOG.info(
                        f"Skipping image rendering for: {file_path} (contains example snippets)"
                    )
                _LOG.debug(f"Successfully processed: {file_path}")


def _copy_assets_and_styles(input_dir: str, output_dir: str) -> None:
    """
    Copy assets and styles from the input directory to the output directory.
    """
    # Find the assets and styles directories.
    mkdocs_html_dir = os.path.join(input_dir, "mkdocs_html")
    hdbg.dassert_dir_exists(mkdocs_html_dir)
    cmd = f"cp -r {mkdocs_html_dir}/* {output_dir}"
    hsystem.system(cmd)
    # Copy the mkdocs.yml file.
    mkdocs_yml_file = os.path.join(input_dir, "mkdocs.yml")
    hdbg.dassert_file_exists(mkdocs_yml_file)
    cmd = f"cp {mkdocs_yml_file} {output_dir}"
    hsystem.system(cmd)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    input_dir = args.input_dir
    output_dir = args.output_dir
    hdbg.dassert(
        not hio.is_subdir(output_dir, input_dir),
        "Output directory '%s' can't be a subdirectory of input directory '%s'",
        output_dir,
        input_dir,
    )
    # TODO(ai): Do not f-string.
    _LOG.info(
        f"Starting mkdocs preprocessing from '{input_dir}' to '{output_dir}'"
    )
    # Copy all files from input to output directory.
    _copy_directory(input_dir, output_dir)
    # Process markdown files in place in the output directory.
    _process_markdown_files(
        output_dir,
        render_images=args.render_images,
        use_github_hosting=args.use_github_hosting,
    )
    # Copy assets and styles.
    # _copy_assets_and_styles(input_dir, output_dir)
    _LOG.info("Mkdocs preprocessing completed successfully")


if __name__ == "__main__":
    _main(_parse())
