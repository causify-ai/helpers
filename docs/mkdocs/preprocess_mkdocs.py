#!/usr/bin/env python

"""
This script takes markdown files from an input directory and processes them
for mkdocs by:

1. Copying all files from input to output directory
2. For documentation (default):
    - Removing table of contents (TOC)
    - Dedenting Python code blocks so they are aligned
    - Replacing 2 spaces indentation with 4 spaces
3. For blogs (--blog flag):
    - Validating required frontmatter fields
    - Skipping TOC removal and code formatting
4. (Optional) Rendering mermaid/plantuml/graphviz diagrams to images

Example usage:
# For documentation:
> preprocess_mkdocs.py --input_dir docs --output_dir tmp.mkdocs
> preprocess_mkdocs.py --input_dir docs --output_dir tmp.mkdocs --render_images

# For blogs:
> preprocess_mkdocs.py --blog --input_dir blog/docs --output_dir blog/tmp.docs
> preprocess_mkdocs.py --blog --input_dir blog/docs --output_dir blog/tmp.docs --render_images

Import as:

import preprocess_mkdocs as premkdo
"""

import argparse
import logging
import os
import re
import sys

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmkdocs as hmkdocs
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


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
        "--blog",
        action="store_true",
        help="Process as blog (validate frontmatter, skip TOC/code processing)",
    )
    parser.add_argument(
        "--render_images",
        action="store_true",
        help="Render mermaid/plantuml/graphviz diagrams to images",
    )
    parser.add_argument(
        "--force_rebuild",
        action="store_true",
        help="Force rebuild of all images (ignore cache)",
    )
    parser.add_argument(
        "--use_github_hosting",
        action="store_true",
        help="Use GitHub-hosted absolute URLs for images",
    )
    parser.add_argument(
        "--skip_validation",
        action="store_true",
        help="Skip frontmatter validation (only for --blog mode)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _copy_directory(input_dir: str, output_dir: str) -> None:
    """
    Copy all files from input directory to output directory.

    :param input_dir: source directory path
    :param output_dir: destination directory path
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
    # Use '/.' to include hidden files (like .authors.yml)
    cmd = f"cp -rL {input_dir}/. {output_dir}/ && chmod -R u+w {output_dir}"
    hsystem.system(cmd)
    _LOG.info(f"Copied directory from '{input_dir}' to '{output_dir}'")


def _validate_frontmatter(file_path: str, content: str) -> None:
    """
    Validate that blog post has required frontmatter fields.

    Required fields:
    - title
    - authors
    - date
    - description
    - categories

    :param file_path: path to the file being validated
    :param content: content of the markdown file
    """
    # Check if frontmatter exists.
    if not content.startswith("---"):
        raise ValueError(
            f"Missing frontmatter in '{file_path}'. "
            f"Blog posts must start with '---' followed by YAML frontmatter."
        )
    # Extract frontmatter (between first and second '---').
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter_match:
        raise ValueError(
            f"Invalid frontmatter format in '{file_path}'. "
            f"Frontmatter must be enclosed between '---' markers."
        )
    frontmatter = frontmatter_match.group(1)
    # Required fields.
    required_fields = {
        "title": r'title:\s*["\']?.+["\']?',
        "authors": r"authors:\s*\n\s*-\s*.+",
        "date": r"date:\s*\d{4}-\d{2}-\d{2}",
        "description": r"description:\s*.+",
        "categories": r"categories:\s*\n\s*-\s*.+",
    }
    errors = []
    for field_name, pattern in required_fields.items():
        if not re.search(pattern, frontmatter, re.MULTILINE):
            errors.append(f"  - Missing or invalid '{field_name}' field")
    if errors:
        error_msg = (
            f"\n{'=' * 70}\n"
            f"FRONTMATTER VALIDATION FAILED: {file_path}\n"
            f"{'=' * 70}\n"
            f"The following required fields are missing or invalid:\n"
            + "\n".join(errors)
            + f"\n\nRequired frontmatter format:\n"
            f"---\n"
            f'title: "Your Blog Post Title"\n'
            f"authors:\n"
            f"  - author_id\n"
            f"date: YYYY-MM-DD\n"
            f"description: Brief description of the blog post\n"
            f"categories:\n"
            f"  - Category1\n"
            f"---\n"
            f"{'=' * 70}\n"
        )
        raise ValueError(error_msg)
    _LOG.info(f"✓ Frontmatter validation passed: {os.path.basename(file_path)}")


def _render_images_in_file(
    file_path: str,
    force_rebuild: bool = False,
    use_sudo: bool = False,
    use_github_hosting: bool = False,
) -> None:
    """
    Render images in a markdown file (PlantUML, Mermaid, Graphviz, etc.).

    :param file_path: path to the markdown file to process
    :param force_rebuild: force rebuild of Docker images
    :param use_sudo: use sudo for Docker commands
    :param use_github_hosting: use GitHub absolute URLs for images
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
    is_blog: bool = False,
    skip_validation: bool = False,
    force_rebuild: bool = False,
) -> None:
    """
    Process all markdown files in the given directory recursively.

    :param directory: directory to process
    :param render_images: whether to render mermaid/plantuml/graphviz
        diagrams
    :param use_github_hosting: use GitHub absolute URLs for images
    :param is_blog: Whether processing blog posts (affects validation
        and processing)
    :param skip_validation: skip frontmatter validation (only for blogs)
    """
    # Files to skip for image rendering (contain example snippets, not real diagrams).
    skip_image_rendering = [
        "all.architecture_diagrams.explanation.md",
    ]
    # For blogs, only process the posts directory.
    if is_blog:
        posts_dir = os.path.join(directory, "posts")
        if not os.path.exists(posts_dir):
            _LOG.warning(f"Posts directory not found: {posts_dir}")
            return
        process_dir = posts_dir
    else:
        process_dir = directory
    directories = sorted(os.walk(process_dir))
    _LOG.info(f"Processing {len(directories)} directories")
    validation_errors = []
    for root, dirs, files in directories:
        _ = dirs
        files = sorted(files)
        _LOG.info(f"Processing {len(files)} files in '{root}'")
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                _LOG.info(f"Processing markdown file: {file_path}")
                content = hio.from_file(file_path)
                # validate blogs frontmatter.
                if is_blog and not skip_validation:
                    try:
                        _validate_frontmatter(file_path, content)
                    except ValueError as e:
                        validation_errors.append(str(e))
                        _LOG.error(f"Validation failed for {file_path}")
                        continue  # Skip further processing if validation fails.
                # For documentation: apply preprocessing transformations.
                if not is_blog:
                    processed_content = hmkdocs.preprocess_mkdocs_markdown(
                        content
                    )
                    # Write back to the same file.
                    hio.to_file(file_path, processed_content)
                # Render images (for both blogs and docs).
                if render_images and file not in skip_image_rendering:
                    _LOG.info(f"Rendering images in: {file_path}")
                    try:
                        _render_images_in_file(
                            file_path,
                            use_github_hosting=use_github_hosting,
                            force_rebuild=force_rebuild,
                        )
                    except Exception as e:
                        error_msg = (
                            f"Failed to render images in {file_path}: {str(e)}"
                        )
                        _LOG.error(error_msg)
                        validation_errors.append(error_msg)
                elif render_images and file in skip_image_rendering:
                    _LOG.info(
                        f"Skipping image rendering for: {file_path} (contains example snippets)"
                    )

                _LOG.debug(f"Successfully processed: {file_path}")
    if validation_errors:
        error_summary = (
            f"\n{'=' * 70}\n"
            f"PREPROCESSING FAILED\n"
            f"{'=' * 70}\n"
            f"Found {len(validation_errors)} error(s):\n\n"
            + "\n".join(validation_errors)
            + f"\n{'=' * 70}\n"
        )
        raise RuntimeError(error_summary)


def _move_misplaced_images(output_dir: str, is_blog: bool) -> None:
    """
    Move images that were created in ./figs/ to the correct location.

    This is a workaround for render_images creating images in the wrong
    location when processing blog posts.

    :param output_dir: output directory (e.g., blog/tmp.docs)
    :param is_blog: whether processing blog posts
    """
    if not is_blog:
        return
    root_figs_dir = "figs"
    if not os.path.exists(root_figs_dir):
        _LOG.debug("No misplaced figs directory found")
        return
    # Target location for blog images.
    target_figs_dir = os.path.join(output_dir, "posts", "figs")
    hio.create_dir(target_figs_dir, incremental=True)
    # Move all PNG files from root figs to blog figs.
    cmd = f"cp -r {root_figs_dir}/* {target_figs_dir}/ 2>/dev/null || true"
    hsystem.system(cmd)
    _LOG.info(f"Moved images from '{root_figs_dir}' to '{target_figs_dir}'")


def _copy_assets_and_styles(input_dir: str, output_dir: str) -> None:
    """
    Copy assets and styles from the input directory to the output directory.
    Only used for documentation (not blogs).

    :param input_dir: Source directory path
    :param output_dir: destination directory path
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
    is_blog = args.blog
    hdbg.dassert(
        not hio.is_subdir(output_dir, input_dir),
        "Output directory '%s' can't be a subdirectory of input directory '%s'",
        output_dir,
        input_dir,
    )
    mode = "blog" if is_blog else "documentation"
    _LOG.info(
        f"Starting mkdocs preprocessing ({mode}) from '{input_dir}' to '{output_dir}'"
    )
    # Copy all files from input to output directory.
    _copy_directory(input_dir, output_dir)
    # Process markdown files in place in the output directory.
    _process_markdown_files(
        output_dir,
        render_images=args.render_images,
        use_github_hosting=args.use_github_hosting,
        is_blog=is_blog,
        skip_validation=args.skip_validation,
        force_rebuild=args.force_rebuild,
    )
    # Move misplaced images to correct location (for blogs with rendered images).
    if args.render_images:
        _move_misplaced_images(output_dir, is_blog)
    # Copy assets and styles (only for documentation, not blogs).
    if not is_blog:
        _copy_assets_and_styles(input_dir, output_dir)
    _LOG.info(f"Mkdocs preprocessing ({mode}) completed successfully")


if __name__ == "__main__":
    _main(_parse())
