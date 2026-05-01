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
> preprocess_mkdocs.py --blog --input_dir blog --output_dir tmp.mkblogs
> preprocess_mkdocs.py --blog --input_dir blog --output_dir tmp.mkblogs --render_images

Import as:

import preprocess_mkdocs as premkdo
"""

import argparse
import logging
import os
import re
import sys
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmkdocs as hmkdocs
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Directory names that are never descended into when discovering near-code docs.
# Matched against each individual path component, not the full path.
_PRUNE_DIRS = frozenset({
    ".git", ".claude", ".venv", "venv",
    "node_modules", "__pycache__",
    "docs_mkdocs",  # MkDocs tooling — not publishable content.
    "blog",         # Separate blog pipeline.
    "test", "outcomes",  # Test infrastructure.
})


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
        "--skip_validation",
        action="store_true",
        help="Skip frontmatter validation (only for --blog mode)",
    )
    parser.add_argument(
        "--collect_from_repo",
        action="store",
        default=None,
        metavar="PATH",
        help=(
            "If set, walk PATH (the repository root) and rsync every "
            "near-code docs/ subdirectory into the staging docs dir. "
            "Ignored in --blog mode. Example: --collect_from_repo ."
        ),
    )
    parser.add_argument(
        "--mkdocs_dir",
        action="store",
        default=None,
        metavar="PATH",
        help=(
            "Directory containing mkdocs.yml, overrides/, and docs/ assets "
            "to copy into the staging area. Defaults to the directory of "
            "this script (helpers_root/docs_mkdocs/). Pass 'docs_mkdocs' "
            "when running from the csfy repo root to use the root-level "
            "config (site_url: https://docs.causify.ai)."
        ),
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _copy_directory(input_dir: str, output_dir: str, is_blog: bool) -> None:
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
    # Use rsync with -L (follow symlinks) and --ignore-errors to skip broken
    # symlinks (e.g., docs/ai_prompts pointing to a missing helpers_root path).
    # Exit code 23 means partial transfer (skipped broken symlinks) — treat as ok.
    if is_blog:
        cmd = f"rsync -aL --ignore-errors {input_dir}/. {output_dir}/ || true && chmod -R u+w {output_dir}"
    else:
        cmd = f"rsync -aL --ignore-errors {input_dir}/. {output_dir}/docs/ || true && chmod -R u+w {output_dir}"
    hsystem.system(cmd)
    _LOG.info(f"Copied directory from '{input_dir}' to '{output_dir}'")


def _collect_near_code_docs(
    repo_root: str,
    staging_docs_dir: str,
    skip_doc_paths: Optional[List[str]] = None,
) -> None:
    """
    Walk repo_root and rsync every near-code docs/ subdirectory that
    contains at least one .md file into staging_docs_dir, mirroring the
    module path.

    Each <repo_root>/<module_path>/docs/ is copied to
    staging_docs_dir/<module_path>/.  For example with REPO_ROOT=csfy-master/:
      helpers_root/docs/  ->  staging_docs_dir/helpers_root/
      dataflow/docs/      ->  staging_docs_dir/dataflow/
      infra/docs/         ->  staging_docs_dir/infra/

    The top-level docs/ (module_rel == ".") is always skipped because it is
    the primary --input_dir, already handled by _copy_directory().
    Any path in skip_doc_paths is also skipped.
    Dirs whose docs/ subtree contains no .md files are silently skipped,
    which naturally filters Next.js route dirs (apps/causify/app/.../docs/)
    and TypeScript type dirs (apps/causify/types/docs/) without hardcoded
    path exceptions.

    :param repo_root: path to the repository root to crawl
    :param staging_docs_dir: output_dir/docs/ — the assembled staging dir
    :param skip_doc_paths: paths of docs/ dirs to skip (e.g. the primary
        --input_dir already copied by _copy_directory)
    """
    if skip_doc_paths is None:
        skip_doc_paths = []
    skip_abs = {os.path.abspath(p) for p in skip_doc_paths}
    repo_root_abs = os.path.abspath(repo_root)
    hdbg.dassert_dir_exists(repo_root_abs)
    hio.create_dir(staging_docs_dir, incremental=True)
    _LOG.info(
        "Collecting near-code docs from '%s' into '%s'",
        repo_root_abs,
        staging_docs_dir,
    )
    collected = 0
    for dirpath, dirnames, _ in os.walk(repo_root_abs, topdown=True):
        # Prune in-place so os.walk never descends into excluded subtrees.
        dirnames[:] = [
            d for d in sorted(dirnames)
            if d not in _PRUNE_DIRS
            and not d.startswith(".")
            and not d.startswith("tmp.")
        ]
        if "docs" not in dirnames:
            continue
        docs_abs = os.path.abspath(os.path.join(dirpath, "docs"))
        if docs_abs in skip_abs:
            _LOG.debug("Skipping excluded docs dir: '%s'", docs_abs)
            continue
        module_rel = os.path.relpath(dirpath, repo_root_abs)
        # Top-level docs/ is the primary --input_dir; _copy_directory handles it.
        if module_rel == ".":
            continue
        # Skip dirs with no .md files (Next.js routes, TypeScript type dirs…).
        md_files = [
            f
            for _, _, files in os.walk(docs_abs)
            for f in files
            if f.endswith(".md")
        ]
        if not md_files:
            _LOG.debug("Skipping '%s': no .md files", docs_abs)
            continue
        # Flatten multi-component module paths so they land as top-level dirs
        # in the staging docs tree. MkDocs auto-nav only creates a sidebar
        # entry for a directory when it contains files directly (not just
        # subdirs), so "apps/causify" → no nav entry, but "apps_causify" →
        # nav entry with all files visible.
        dest_name = module_rel
        dest_dir = os.path.join(staging_docs_dir, dest_name)
        hio.create_dir(dest_dir, incremental=True)
        cmd = (
            f"rsync -aL --ignore-errors {docs_abs}/. {dest_dir}/ "
            f"|| true && chmod -R u+w {dest_dir}"
        )
        hsystem.system(cmd)
        _LOG.info("Collected docs: '%s' -> '%s'", docs_abs, dest_dir)
        collected += 1
    _LOG.info(
        "Collected %d near-code docs director%s",
        collected,
        "y" if collected == 1 else "ies",
    )


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
) -> None:
    """
    Render images in a markdown file (PlantUML, Mermaid, Graphviz, etc.).

    :param file_path: path to the markdown file to process
    :param force_rebuild: force rebuild of Docker images
    :param use_sudo: use sudo for Docker commands
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

    # Save images into the same directory as the file under the `figs`
    # sub dir.
    dst_dir = os.path.join(os.path.dirname(file_path), "figs")
    hio.create_dir(dst_dir, incremental=True)
    # Read the file.
    in_lines = hio.from_file(file_path).split("\n")
    # Render images (in-place, using png).
    out_lines = dshdreim._render_images(
        in_lines,
        out_file=file_path,
        dst_ext="png",
        dst_dir=dst_dir,
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
        dry_run=False,
    )
    # Write back.
    hio.to_file(file_path, "\n".join(out_lines))
    _LOG.info(f"Successfully rendered images in: {file_path}")


def _process_markdown_files(
    directory: str,
    render_images: bool = False,
    is_blog: bool = False,
    skip_validation: bool = False,
    force_rebuild: bool = False,
) -> None:
    """
    Process all markdown files in the given directory recursively.

    :param directory: directory to process
    :param render_images: whether to render mermaid/plantuml/graphviz
        diagrams
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
        posts_dir = os.path.join(directory, "docs", "posts")
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
                processed_content = hmkdocs.preprocess_mkdocs_markdown(content)
                # Write back to the same file.
                hio.to_file(file_path, processed_content)
                # Render images (for both blogs and docs).
                if render_images and file not in skip_image_rendering:
                    _LOG.info(f"Rendering images in: {file_path}")
                    try:
                        _render_images_in_file(
                            file_path,
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
    target_figs_dir = os.path.join(output_dir, "docs", "posts", "figs")
    hio.create_dir(target_figs_dir, incremental=True)
    # Move all PNG files from root figs to blog figs.
    cmd = f"cp -r {root_figs_dir}/* {target_figs_dir}/ 2>/dev/null || true"
    hsystem.system(cmd)
    _LOG.info(f"Moved images from '{root_figs_dir}' to '{target_figs_dir}'")


def _write_404_page(output_dir: str) -> None:
    """
    Write a 404.md page into the docs staging directory.

    The file is generated rather than kept in the repo so it stays out of
    version control while still being built into the site.

    :param output_dir: destination directory path (e.g. ``tmp.mkdocs/``)
    """
    content = """\
---
title: 404 – Page Not Found
hide:
  - toc
---
# 404 – Page Not Found
The page you're looking for doesn't exist or has been moved.
[← Back to Home](/)
"""
    dest = os.path.join(output_dir, "docs", "404.md")
    hio.to_file(dest, content)
    _LOG.info("Written 404 page to '%s'", dest)


def _copy_assets_and_styles(output_dir: str, mkdocs_dir: Optional[str] = None) -> None:
    """
    Copy assets and styles from the input directory to the output directory.
    Only used for documentation (not blogs).

    :param output_dir: destination directory path
    :param mkdocs_dir: directory containing mkdocs.yml, overrides/, and
        docs/ assets. Defaults to the directory of this script
        (helpers_root/docs_mkdocs/). Pass the repo-root docs_mkdocs/ when
        deploying the full csfy docs site.
    """
    if mkdocs_dir is not None:
        mkdocs_html_dir = os.path.abspath(mkdocs_dir)
    else:
        # Default: helpers_root/docs_mkdocs/ (location of this script).
        mkdocs_html_dir = os.path.dirname(os.path.abspath(__file__))
    hdbg.dassert_dir_exists(mkdocs_html_dir)
    cmd = f"cp -r {mkdocs_html_dir}/docs/* {output_dir}/docs"
    hsystem.system(cmd)
    # Copy the mkdocs.yml file.
    mkdocs_yml_file = os.path.join(mkdocs_html_dir, "properdocs.yml")
    hdbg.dassert_file_exists(mkdocs_yml_file)
    cmd = f"cp {mkdocs_yml_file} {output_dir}"
    hsystem.system(cmd)
    # Copy theme overrides directory if present.
    overrides_dir = os.path.join(mkdocs_html_dir, "overrides")
    if os.path.isdir(overrides_dir):
        cmd = f"cp -r {overrides_dir} {output_dir}"
        hsystem.system(cmd)
    # Copy top-level papers/ directory so PDF links resolve (e.g. /papers/KaizenFlow/KaizenFlow.pdf).
    papers_dir = "papers"
    if os.path.isdir(papers_dir):
        cmd = f"cp -r {papers_dir} {output_dir}/docs/"
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
    _copy_directory(input_dir, output_dir, is_blog)
    # Collect near-code docs/ dirs from the repo tree (non-blog only).
    if args.collect_from_repo and not is_blog:
        staging_docs_dir = os.path.join(output_dir, "docs")
        _collect_near_code_docs(
            repo_root=args.collect_from_repo,
            staging_docs_dir=staging_docs_dir,
            skip_doc_paths=[os.path.abspath(input_dir)],
        )
    # Process markdown files in place in the output directory.
    _process_markdown_files(
        output_dir,
        render_images=args.render_images,
        is_blog=is_blog,
        skip_validation=args.skip_validation,
        force_rebuild=args.force_rebuild,
    )
    # Move misplaced images to correct location (for blogs with rendered images).
    if args.render_images:
        _move_misplaced_images(output_dir, is_blog)
    # Copy assets and styles (only for documentation, not blogs).
    if not is_blog:
        _copy_assets_and_styles(output_dir, mkdocs_dir=args.mkdocs_dir)
        _write_404_page(output_dir)
    _LOG.info(f"Mkdocs preprocessing ({mode}) completed successfully")


if __name__ == "__main__":
    _main(_parse())
