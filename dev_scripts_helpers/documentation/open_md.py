#!/usr/bin/env python

"""
Render markdown files and open them in the browser or in the PDF viewer.

For a description of this file, see:
`helpers_root/dev_scripts_helpers/documentation/open_md.README.md`
"""

import argparse
import hashlib
import json
import logging
import os
import platform
import re
import shlex
import subprocess
import sys
import urllib.parse
from typing import Dict, List, Optional, Tuple

import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import helpers.hdaemon as hdaemon
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# How to encode the links to files with a repo-root path.
_LINK_TYPES = ("master", "branch", "local")
_DEFAULT_LINK_TYPE = "local"

# Default depth of the table of contents added in `pandoc` and `pdf` modes.
_DEFAULT_TOC_DEPTH = 2

# Marker of a table of contents already in the file, see `hmarkdown_toc`.
_TOC_MARKER = "<!-- toc -->"

# Branch used by `--link_type master`.
_MASTER_BRANCH = "master"

# Inline markdown link to a repo-root path, e.g., `[text](/docs/a.md#sec)`.
# Images (`![alt](...)`) and protocol-relative URLs (`//host/...`) don't match.
_REPO_ROOT_LINK_RE = re.compile(
    r"(?<!!)(\[[^\]]*\])\((/(?!/)[^)\s#]*)(#[^)\s]*)?\)"
)

# #############################################################################


def _strip_rendered_source_blocks(file_path: str) -> None:
    """
    Remove the commented-out original diagram source left by render_images.py.

    `render_images.py` preserves the original diagram source (e.g., a `mermaid`
    fence) as a block of `<!-- ... -->`-commented lines (between
    `rendered_images:begin`/`rendered_images:end` markers) so it can be
    restored later with `--remove_figs`.
    That preservation isn't needed for a disposable preview copy, and it's
    actively harmful here
    - a diagram edge like `A --> B` still contains a literal `-->`, so wrapping
      it as `<!-- A --> B -->` makes the HTML/CommonMark parser close the
      comment at the first `-->` (right after `A`), leaking the rest of the
      line as visible text in the rendered output
    - Deleting the block sidesteps the collision entirely for this preview-only
      copy.

    :param file_path: path to the file to strip in place
    """
    lines = hio.from_file(file_path).split("\n")
    out_lines = []
    in_block = False
    for line in lines:
        if "rendered_images:begin" in line:
            in_block = True
            continue
        if "rendered_images:end" in line:
            in_block = False
            continue
        if not in_block:
            out_lines.append(line)
    hio.to_file(file_path, "\n".join(out_lines))


def _get_stem(input_file: str) -> str:
    """
    Return the input basename without extension, used to name its outputs.

    E.g., 'docs/design.architecture.md' -> 'design.architecture'.

    :param input_file: path to the input markdown file
    :return: basename without the last extension
    """
    return os.path.splitext(os.path.basename(input_file))[0]


def _run_render_images(input_file: str) -> str:
    """
    Run render_images.py on input to process embedded diagrams.

    :param input_file: Input markdown file path
    :return: Path to processed file
    """
    # Find render_images.py.
    render_images_script = hgit.find_file("render_images.py")
    hdbg.dassert_file_exists(render_images_script)
    # Create output filename, one per input so that several files can be
    # processed without overwriting each other.
    output_file = f"tmp.open_md.{_get_stem(input_file)}.render_images.md"
    # Run render_images.py.
    cmd = (
        f"{render_images_script} --input {input_file} "
        f"--output {output_file} --action render"
    )
    _LOG.info("Running render_images: %s", cmd)
    hsystem.system(cmd)
    hdbg.dassert_file_exists(output_file)
    # Drop the commented-out original diagram source: it's not needed to
    # view this disposable preview copy, and it's the source of leaked-text
    # rendering artifacts (see `_strip_rendered_source_blocks()`).
    _strip_rendered_source_blocks(output_file)
    return output_file


def _convert_ssh_to_https(remote_url: str) -> str:
    """
    Convert `git@github.com:org/repo.git` to `https://github.com/org/repo`.

    :param remote_url: Remote URL (SSH or HTTPS)
    :return: HTTPS URL
    """
    # If already HTTPS, return as-is.
    if remote_url.startswith("https://"):
        return remote_url.replace(".git", "")
    # Convert SSH to HTTPS: git@github.com:org/repo.git ->
    # https://github.com/org/repo
    if remote_url.startswith("git@"):
        # Extract host and path from: git@github.com:org/repo.git
        parts = remote_url.replace(":", "/").replace("git@", "https://")
        # Remove .git suffix if present.
        parts = parts.removesuffix(".git")
        return parts
    # Fallback: return as-is.
    return remote_url


def _open_file(file_path: str) -> None:
    """
    Open a file using platform-appropriate command.

    :param file_path: Path to the file to open
    """
    # On macOS, use the 'open' command.
    if platform.system() == "Darwin":
        subprocess.run(["open", file_path], check=True)
        _LOG.info("Opened file: '%s'", file_path)
    # On Linux, use xdg-open.
    elif platform.system() == "Linux":
        subprocess.run(["xdg-open", file_path], check=True)
        _LOG.info("Opened file: '%s'", file_path)
    else:
        _LOG.warning("Cannot open file on unsupported OS: %s", platform.system())


def _find_git_root_from_dir(start_dir: str) -> str:
    """
    Find the git root directory containing a dir, handling subrepos.

    Walks up from `start_dir` to find the closest ancestor with .git.

    :param start_dir: Path to the dir where to start the search
    :return: Git root directory
    """
    current_dir = os.path.abspath(start_dir)
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        git_dir = os.path.join(current_dir, ".git")
        if os.path.exists(git_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    # Fallback: use the main repo root
    return hgit.get_client_root(super_module=True)


def _find_git_root_for_file(file_path: str) -> str:
    """
    Find the git root directory for a file, handling subrepos.

    Walks up from file's directory to find the closest ancestor with .git.

    :param file_path: Path to the file
    :return: Git root directory
    """
    return _find_git_root_from_dir(os.path.dirname(os.path.abspath(file_path)))


def _get_remote_url_and_branch(repo_root: str) -> Tuple[str, str]:
    """
    Get the HTTPS URL of the `origin` remote and the current branch of a repo.

    :param repo_root: git root directory of the repo
    :return: HTTPS URL of the remote (e.g., `https://github.com/org/repo`) and
        name of the current branch
    """
    orig_dir = os.getcwd()
    try:
        os.chdir(repo_root)
        ret, remote_url = hsystem.system_to_one_line("git remote get-url origin")
        hdbg.dassert_eq(ret, 0, "Failed to get git remote URL")
        remote_url = remote_url.strip()
        remote_url = _convert_ssh_to_https(remote_url)
        # Get current branch for this repo.
        branch = hgit.get_branch_name(".")
    finally:
        os.chdir(orig_dir)
    return remote_url, branch


def _open_on_github(input_file: str) -> None:
    """
    Open markdown file on GitHub in the browser.

    Handles files in subrepos by detecting the correct git root.

    :param input_file: Path to the markdown file
    """
    _LOG.info("Opening file on GitHub: '%s'", input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Get absolute path and find the correct git root (handles subrepos).
    abs_file = os.path.abspath(input_file)
    repo_root = _find_git_root_for_file(abs_file)
    _LOG.info("Git root: %s", repo_root)
    # Compute relative path from repo root.
    rel_path = os.path.relpath(abs_file, repo_root)
    # Get remote URL for this git repo and convert to HTTPS.
    remote_url, branch = _get_remote_url_and_branch(repo_root)
    # Build GitHub URL.
    url = f"{remote_url}/blob/{branch}/{rel_path}"
    _LOG.info("GitHub URL: %s", url)
    # Open URL in browser.
    _open_file(url)


def _encode_links(file_path: str, input_file: str, link_type: str) -> None:
    """
    Rewrite the links with a repo-root path in a file, in place.

    A link like `[prd](/docs/prd.md#goal)` is relative to the root of the repo
    containing `input_file`: it resolves on GitHub but not in a page opened from
    disk, where `/docs/prd.md` means the root of the file system.
    Links in fenced code blocks, images, and links with other targets are left
    as they are.

    :param file_path: path to the file to rewrite in place (a copy of
        `input_file`)
    :param input_file: path to the original markdown file, used to find the repo
        root
    :param link_type: how to encode the links; a link to a dir (existing, or
        ending with `/`) is a `tree` URL on GitHub, other links are `blob` URLs
        - `local`: `file://` URL of the file in the working tree
        - `branch`: GitHub URL of the file on the current branch
        - `master`: GitHub URL of the file on the `master` branch
    """
    hdbg.dassert_in(link_type, _LINK_TYPES)
    lines = hio.from_file(file_path).split("\n")
    # Avoid querying git when there is nothing to rewrite.
    if not any(_REPO_ROOT_LINK_RE.search(line) for line in lines):
        return
    repo_root = _find_git_root_for_file(input_file)
    _LOG.debug("link_type=%s repo_root=%s", link_type, repo_root)
    # Remote URL and ref of each repo that a link points to.
    repos: Dict[str, Tuple[str, str]] = {}

    def _get_remote_url_and_ref(root: str) -> Tuple[str, str]:
        if root not in repos:
            remote_url, branch = _get_remote_url_and_branch(root)
            ref = _MASTER_BRANCH if link_type == "master" else branch
            repos[root] = (remote_url, ref)
        return repos[root]

    def _encode(match: re.Match) -> str:
        text, path, anchor = match.group(1), match.group(2), match.group(3) or ""
        rel_path = path.lstrip("/")
        abs_path = os.path.join(repo_root, rel_path)
        if link_type == "local":
            url = "file://" + urllib.parse.quote(abs_path)
        else:
            # A trailing slash marks a dir even if it doesn't exist yet.
            is_dir = path.endswith("/") or os.path.isdir(abs_path)
            kind = "tree" if is_dir else "blob"
            # The target can be in a submodule (e.g., `helpers_root`), possibly
            # reached through a symlink (e.g., `.claude`): GitHub only knows it
            # in the repo of the submodule, with the path relative to its root.
            real_path = os.path.realpath(abs_path)
            if is_dir:
                target_root = _find_git_root_from_dir(real_path)
            else:
                target_root = _find_git_root_for_file(real_path)
            remote_url, ref = _get_remote_url_and_ref(target_root)
            target_rel_path = os.path.relpath(real_path, target_root)
            if target_rel_path == ".":
                target_rel_path = ""
            elif path.endswith("/"):
                target_rel_path += "/"
            url = f"{remote_url}/{kind}/{ref}/{target_rel_path}"
        return f"{text}({url}{anchor})"

    out_lines = []
    in_fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence:
            line = _REPO_ROOT_LINK_RE.sub(_encode, line)
        out_lines.append(line)
    hio.to_file(file_path, "\n".join(out_lines))


def _compute_resource_path(input_file: str, processed_file: str) -> str:
    """
    Compute a pandoc `--resource-path` value covering both source dirs.

    `processed_file` (the output of `render_images.py`) is a temp file
    written to the CWD, so its dir alone isn't enough to resolve resources
    (e.g., images) that are relative to the original `input_file`'s
    directory instead.

    :param input_file: path to the original markdown file
    :param processed_file: path to the render_images-processed markdown file
    :return: `os.pathsep`-joined, deduplicated list of directories
    """
    processed_dir = os.path.dirname(os.path.abspath(processed_file))
    input_dir = os.path.dirname(os.path.abspath(input_file))
    return os.pathsep.join(dict.fromkeys([input_dir, processed_dir]))


def _get_toc_depth(args: argparse.Namespace, input_file: str) -> int:
    """
    Get the depth of the table of contents to add when rendering a file.

    - `--no_toc`: no TOC
    - `--toc`: always add the TOC
    - otherwise: add the TOC unless the file already has one (a `<!-- toc -->`
      marker), to avoid showing two TOCs

    :param args: parsed command line arguments
    :param input_file: file to render
    :return: depth of the TOC, 0 for no TOC
    """
    if args.no_toc:
        toc_depth = 0
    elif args.toc:
        toc_depth = args.toc_depth
    elif _TOC_MARKER in hio.from_file(input_file):
        toc_depth = 0
    else:
        toc_depth = args.toc_depth
    return toc_depth


# JavaScript injected in the rendered HTML to make it reload itself.
#
# Chrome never re-reads a `file://` page when the file changes on disk, and the
# page can't `fetch()` other local files (opaque origin), but it can load a
# `<script src>`. So every second the page loads the tiny build file, which
# sets `window.__open_md_build`, and reloads itself if the build id changed.
# The placeholders are replaced with JSON string literals by
# `_inject_live_reload()`.
_LIVE_RELOAD_SNIPPET = """
    <script>
    (function () {
      var build = __BUILD_ID__;
      setInterval(function () {
        var script = document.createElement("script");
        script.src = __BUILD_FILE__ + "?" + Date.now();
        script.onload = function () {
          script.remove();
          if (window.__open_md_build && window.__open_md_build !== build) {
            location.reload();
          }
        };
        script.onerror = function () {
          script.remove();
        };
        document.head.appendChild(script);
      }, 1000);
    })();
    </script>
    """


def _inject_live_reload(html_file: str) -> None:
    """
    Make a rendered HTML page reload itself in the browser when re-rendered.

    Insert a polling script (see `_LIVE_RELOAD_SNIPPET`) before `</head>` and
    write next to the page a build file `<html_file without .html>.build.js`
    storing the build id (hash of the page content before the injection):
    - The build file is written last, so the browser never reloads onto a
      half-written page
    - Re-rendering an unchanged file leaves the build id unchanged, so the tab
      doesn't reload for nothing

    :param html_file: path to the rendered HTML file to modify in place
    """
    hdbg.dassert_file_exists(html_file)
    html = hio.from_file(html_file)
    build_id = hashlib.md5(html.encode()).hexdigest()
    build_file = f"{os.path.splitext(html_file)[0]}.build.js"
    # The page and the build file are in the same dir, so a relative name works.
    snippet = hprint.dedent(_LIVE_RELOAD_SNIPPET)
    snippet = snippet.replace("__BUILD_ID__", json.dumps(build_id))
    snippet = snippet.replace(
        "__BUILD_FILE__", json.dumps(os.path.basename(build_file))
    )
    hdbg.dassert_in("</head>", html, "No '</head>' in '%s'", html_file)
    html = html.replace("</head>", snippet + "\n</head>", 1)
    hio.to_file(html_file, html)
    _LOG.info("Injected live reload in '%s' (build %s)", html_file, build_id[:8])
    # Signal the new build to the open page only after the HTML is complete.
    hio.to_file(
        build_file, f"window.__open_md_build = {json.dumps(build_id)};\n"
    )


def _render_with_pandoc(
    input_file: str,
    *,
    backend: str,
    force_rebuild: bool = False,
    use_sudo: bool = False,
    style_file: Optional[str] = None,
    skip_open: bool = False,
    live_reload: bool = False,
    link_type: str = _DEFAULT_LINK_TYPE,
    toc_depth: int = 0,
) -> None:
    """
    Render markdown with pandoc to HTML and open in browser.

    :param input_file: Path to markdown file
    :param backend: "global" or "dockerized"
    :param force_rebuild: Force rebuild Docker image (for dockerized only)
    :param use_sudo: Use sudo for Docker (for dockerized only)
    :param style_file: path to an HTML snippet (e.g., a `<style>` block) injected
        into the `<head>` via pandoc's `--include-in-header`; None means use
        pandoc's bare default styling
    :param skip_open: don't open the rendered output (used for `--daemon` watch
        re-runs, where the first run already opened it)
    :param live_reload: make the HTML reload itself in the browser when it is
        re-rendered (used by `--daemon`), see `_inject_live_reload()`
    :param link_type: how to encode the links with a repo-root path, see
        `_encode_links()`
    :param toc_depth: depth of the table of contents added by pandoc, 0 for no
        table of contents
    """
    _LOG.info("Rendering with pandoc (backend=%s): '%s'", backend, input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Preprocess with render_images.
    processed_file = _run_render_images(input_file)
    _encode_links(processed_file, input_file, link_type)
    # Name the output after the input basename without extension, so that
    # several previews can coexist, e.g., 'docs/design.architecture.md' ->
    # 'tmp.design.architecture.html'.
    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"tmp.{input_basename}.html"
    file_dir = _compute_resource_path(input_file, processed_file)
    toc_opts = f"--toc --toc-depth={toc_depth} " if toc_depth > 0 else ""
    # Add the optional style/header-include and matching syntax highlighting.
    style_opts = ""
    if style_file is not None:
        hdbg.dassert_file_exists(style_file)
        style_opts = (
            f"--highlight-style=pygments --include-in-header={style_file}"
        )
    if backend == "global":
        # Run pandoc to HTML.
        cmd = (
            f"pandoc {processed_file} "
            f"-o {output_file} "
            f"--resource-path={file_dir} "
            f"--standalone "
            f"--embed-resources "
            f"--mathjax "
            f"{toc_opts}"
            f"{style_opts}"
        )
        _LOG.info("Running pandoc: %s", cmd)
        hsystem.system(cmd)
    elif backend == "dockerized":
        # Use dockerized pandoc.
        cmd = (
            f"pandoc {processed_file} "
            f"-o {output_file} "
            f"--resource-path={file_dir} "
            f"--standalone "
            f"--embed-resources "
            f"--mathjax "
            f"{toc_opts}"
            f"{style_opts}"
        )
        _LOG.info("Running dockerized pandoc: %s", cmd)
        dshdlipa.run_dockerized_pandoc(
            cmd,
            "pandoc_only",
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
    else:
        raise ValueError(f"Invalid backend: {backend}")
    # Validate output exists.
    hdbg.dassert_file_exists(output_file)
    if live_reload:
        _inject_live_reload(output_file)
    # Open the output file.
    if not skip_open:
        _open_file(output_file)


def _render_with_pdf(
    input_file: str,
    *,
    backend: str,
    force_rebuild: bool = False,
    use_sudo: bool = False,
    skip_open: bool = False,
    link_type: str = _DEFAULT_LINK_TYPE,
    toc_depth: int = 0,
) -> None:
    """
    Render markdown to PDF with pandoc and open it.

    Requires a LaTeX distribution (e.g., MacTeX/TeX Live providing `xelatex`)
    on the `global` backend, or in the Docker image on `dockerized`.

    :param input_file: Path to markdown file
    :param backend: "global" or "dockerized"
    :param force_rebuild: Force rebuild Docker image (for dockerized only)
    :param use_sudo: Use sudo for Docker (for dockerized only)
    :param skip_open: don't open the rendered output (used for `--daemon` watch
        re-runs, where the first run already opened it)
    :param link_type: how to encode the links with a repo-root path, see
        `_encode_links()`
    :param toc_depth: depth of the table of contents added by pandoc, 0 for no
        table of contents
    """
    _LOG.info(
        "Rendering with pandoc to PDF (backend=%s): '%s'", backend, input_file
    )
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Preprocess with render_images.
    processed_file = _run_render_images(input_file)
    _encode_links(processed_file, input_file, link_type)
    # Determine output file, one per input.
    output_file = f"tmp.{_get_stem(input_file)}.pdf"
    file_dir = _compute_resource_path(input_file, processed_file)
    cmd = (
        f"pandoc {processed_file} "
        f"-o {output_file} "
        f"--resource-path={file_dir} "
        f"--pdf-engine=xelatex "
        f"-V geometry:margin=1in"
    )
    if toc_depth > 0:
        cmd += f" --toc --toc-depth={toc_depth}"
    if backend == "global":
        _LOG.info("Running pandoc: %s", cmd)
        hsystem.system(cmd)
    elif backend == "dockerized":
        _LOG.info("Running dockerized pandoc: %s", cmd)
        dshdlipa.run_dockerized_pandoc(
            cmd,
            "pandoc_only",
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
    else:
        raise ValueError(f"Invalid backend: {backend}")
    # Validate output exists.
    hdbg.dassert_file_exists(output_file)
    # Open the output file.
    if not skip_open:
        _open_file(output_file)


def _render_with_grip(
    input_file: str,
    *,
    backend: str,
    skip_open: bool = False,
    live_reload: bool = False,
    link_type: str = _DEFAULT_LINK_TYPE,
) -> None:
    """
    Export markdown with grip and open HTML in browser.

    :param input_file: Path to markdown file
    :param backend: "global" or "dockerized"
    :param skip_open: don't open the rendered output (used for `--daemon` watch
        re-runs, where the first run already opened it)
    :param live_reload: make the HTML reload itself in the browser when it is
        re-rendered (used by `--daemon`), see `_inject_live_reload()`
    :param link_type: how to encode the links with a repo-root path, see
        `_encode_links()`
    """
    _LOG.info("Rendering with grip (backend=%s): '%s'", backend, input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Preprocess with render_images.
    processed_file = _run_render_images(input_file)
    _encode_links(processed_file, input_file, link_type)
    # Determine output file, one per input.
    output_file = f"tmp.{_get_stem(input_file)}.grip.html"
    # Run grip to export HTML.
    if backend == "global":
        cmd = f"grip --export {processed_file} {output_file}"
    elif backend == "dockerized":
        cmd = f"uvx grip --export {processed_file} {output_file}"
    else:
        raise ValueError(f"Invalid backend: {backend}")
    _LOG.info("Running grip: %s", cmd)
    hsystem.system(cmd)
    # Validate output exists.
    hdbg.dassert_file_exists(output_file)
    if live_reload:
        _inject_live_reload(output_file)
    # Open the output file.
    if not skip_open:
        _open_file(output_file)


def _render_with_grip_daemon(
    input_file: str,
    *,
    backend: str,
    link_type: str = _DEFAULT_LINK_TYPE,
) -> None:
    """
    Start grip daemon for live markdown preview.

    The daemon serves the page over HTTP, where the browser blocks the links to
    `file://` URLs: use `--link_type branch` or `master` to get working links.

    :param input_file: Path to markdown file
    :param backend: "global" or "dockerized"
    :param link_type: how to encode the links with a repo-root path, see
        `_encode_links()`
    """
    _LOG.info("Starting grip daemon (backend=%s): '%s'", backend, input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Preprocess with render_images.
    processed_file = _run_render_images(input_file)
    _encode_links(processed_file, input_file, link_type)
    # Run grip in daemon mode (opens browser automatically).
    if backend == "global":
        cmd = f"grip -b --quiet {processed_file}"
    elif backend == "dockerized":
        cmd = f"uvx grip -b --quiet {processed_file}"
    else:
        raise ValueError(f"Invalid backend: {backend}")
    _LOG.info("Running grip daemon: %s", cmd)
    hsystem.system(cmd)


# #############################################################################


def _get_files_to_render(args: argparse.Namespace) -> List[str]:
    """
    Select the files to render from the command line.

    :param args: parsed command line arguments
    :return: paths of the files to render
    """
    # `hgit.get_files_to_process()` selects the files modified in the branch
    # when nothing is specified, which would open a surprising number of
    # tabs: require an explicit selection instead.
    selection_opts = [
        args.input,
        args.files,
        args.from_file,
        args.modified,
        args.branch,
        args.last_commit,
        args.all_files,
    ]
    hdbg.dassert(
        any(selection_opts),
        "No files selected; use -i/--input, -f/--files, --from_file, "
        "--modified, --branch, --last_commit, or --all_files",
    )
    files = hseinout.parse_file_selection_args(args)
    # The selections based on git return files of any type: keep only the
    # markdown ones.
    if args.modified or args.branch or args.last_commit or args.all_files:
        files = hseinout.filter_files_by_extensions(files, "md", "")
    hdbg.dassert_lt(0, len(files), "No files selected")
    if args.mode != "github":
        # The outputs are named after the input basename, so two files with the
        # same basename (in different dirs) would overwrite each other.
        stems = [_get_stem(file_) for file_ in files]
        hdbg.dassert_no_duplicates(
            stems, "Files must have distinct basenames, got: %s", files
        )
    return files


def _build_render_cmd(args: argparse.Namespace, input_file: str) -> str:
    """
    Build the command line to render a single file, used for `--daemon` runs.

    :param args: parsed command line arguments
    :param input_file: file to render
    :return: command line running this script on `input_file` only
    """
    cmd = [
        shlex.quote(sys.executable),
        shlex.quote(os.path.abspath(sys.argv[0])),
        f"--input {shlex.quote(input_file)}",
        f"--mode {args.mode}",
        f"--backend {args.backend}",
        f"--link_type {args.link_type}",
        f"--toc_depth {args.toc_depth}",
        f"-v {args.log_level}",
    ]
    if args.toc:
        cmd.append("--toc")
    if args.no_toc:
        cmd.append("--no_toc")
    if args.css:
        cmd.append(f"--css {shlex.quote(args.css)}")
    if args.dockerized_force_rebuild:
        cmd.append("--dockerized_force_rebuild")
    if args.dockerized_use_sudo:
        cmd.append("--dockerized_use_sudo")
    # Only the HTML outputs reload themselves, while the PDF viewer reloads
    # the PDF.
    if args.mode in ("pandoc", "grip"):
        cmd.append("--live_reload")
    return " ".join(cmd)


def _render_file(
    args: argparse.Namespace, input_file: str, style_file: str
) -> None:
    """
    Render a single file according to the selected mode.

    :param args: parsed command line arguments
    :param input_file: file to render
    :param style_file: HTML snippet to include in the header (pandoc mode only)
    """
    if args.mode == "github":
        _open_on_github(input_file)
    elif args.mode == "pandoc":
        _render_with_pandoc(
            input_file,
            backend=args.backend,
            force_rebuild=args.dockerized_force_rebuild,
            use_sudo=args.dockerized_use_sudo,
            style_file=style_file,
            skip_open=args.skip_open,
            live_reload=args.live_reload,
            link_type=args.link_type,
            toc_depth=_get_toc_depth(args, input_file),
        )
    elif args.mode == "pdf":
        _render_with_pdf(
            input_file,
            backend=args.backend,
            force_rebuild=args.dockerized_force_rebuild,
            use_sudo=args.dockerized_use_sudo,
            skip_open=args.skip_open,
            link_type=args.link_type,
            toc_depth=_get_toc_depth(args, input_file),
        )
    elif args.mode == "grip":
        _render_with_grip(
            input_file,
            backend=args.backend,
            skip_open=args.skip_open,
            live_reload=args.live_reload,
            link_type=args.link_type,
        )
    elif args.mode == "grip_daemon":
        _render_with_grip_daemon(
            input_file, backend=args.backend, link_type=args.link_type
        )
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hseinout.add_file_selection_args(parser)
    parser.add_argument(
        "--mode",
        type=str,
        choices=["github", "pandoc", "pdf", "grip", "grip_daemon"],
        default="pandoc",
        help="Rendering mode",
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["global", "dockerized"],
        default="global",
        help="Backend to use for rendering",
    )
    parser.add_argument(
        "--link_type",
        type=str,
        choices=list(_LINK_TYPES),
        default=_DEFAULT_LINK_TYPE,
        help="How to encode the links with a repo-root path (e.g., "
        "`[prd](/docs/prd.md)`) in the rendered output: `local` for a "
        "`file://` URL, `branch` for a GitHub URL on the current branch, "
        "`master` for a GitHub URL on the `master` branch (ignored by "
        "`--mode github`)",
    )
    toc_group = parser.add_mutually_exclusive_group()
    toc_group.add_argument(
        "--toc",
        action="store_true",
        help="(pandoc and pdf modes only) Always add a table of contents, "
        "also to a file that already has one (a `<!-- toc -->` marker); by "
        "default it is added unless the file has one",
    )
    toc_group.add_argument(
        "--no_toc",
        action="store_true",
        help="(pandoc and pdf modes only) Don't add a table of contents",
    )
    parser.add_argument(
        "--toc_depth",
        type=int,
        default=_DEFAULT_TOC_DEPTH,
        help="(pandoc and pdf modes only) Depth of the table of contents, "
        "from 1 to 6",
    )
    parser.add_argument(
        "--css",
        type=str,
        default=None,
        help="(pandoc mode only) Path to a custom HTML snippet (e.g., a "
        "`<style>` block) to inject into the output via pandoc's "
        "--include-in-header, overriding the default GitHub-like style "
        "(bigger font, yellowish verbatim, wider layout)",
    )
    hdaemon.add_daemon_arg(
        parser,
        help_text="Watch the input file(s) for changes and re-render (pandoc, "
        "pdf, grip modes only); the output is opened only on the first run "
        "and the HTML outputs reload themselves in the browser",
    )
    parser.add_argument(
        "--skip_open",
        action="store_true",
        help="Don't open the rendered output (used internally by --daemon "
        "watch re-runs)",
    )
    parser.add_argument(
        "--live_reload",
        action="store_true",
        help="(pandoc and grip modes only) Make the rendered HTML reload "
        "itself in the browser when it is re-rendered (used internally by "
        "--daemon)",
    )
    hdocker.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert_lte(1, args.toc_depth)
    hdbg.dassert_lte(args.toc_depth, 6)
    files = _get_files_to_render(args)
    if args.mode == "grip_daemon":
        # grip serves a single file per port.
        hdbg.dassert_eq(
            len(files),
            1,
            "grip_daemon supports a single file, got: %s",
            files,
        )
    if args.daemon:
        # `grip_daemon` already watches the file itself, so `--daemon` only
        # makes sense for the one-shot pandoc/pdf/grip modes.
        hdbg.dassert_in(
            args.mode,
            ("pandoc", "pdf", "grip"),
            "--daemon is only supported for pandoc/pdf/grip modes ("
            "grip_daemon already watches for changes)",
        )
        # Watch runs skip opening the output: the first run already opened
        # it, and the HTML reloads itself.
        hdaemon.run_reactive_daemon_mode_multi(
            files,
            lambda file_: _build_render_cmd(args, file_),
            "open_md",
            watch_cmd_suffix=" --skip_open",
        )
        return
    # Resolve the style/header-include: explicit --css wins, otherwise
    # default to the bundled GitHub-like style.
    style_file = ""
    if args.mode == "pandoc":
        style_file = args.css or hgit.find_file("github_style.html")
    for input_file in files:
        _render_file(args, input_file, style_file)


if __name__ == "__main__":
    _main(_parse())
