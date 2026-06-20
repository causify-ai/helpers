#!/usr/bin/env python

# TODO(ai_gp): Explain the meaning of mode and backend
"""
Render and open markdown files in different modes.

Usage:
> open_md.py --input xyz.md --mode github
> open_md.py --input xyz.md --mode pandoc --backend global
> open_md.py --input xyz.md --mode grip --backend global
> open_md.py --input xyz.md --mode grip_daemon --backend global
"""

import argparse
import logging
import os
import platform
import subprocess

import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Valid modes and backends.
# TODO(ai_gp): Inline these constants.
_VALID_MODES = ["github", "pandoc", "grip", "grip_daemon"]
_VALID_BACKENDS = ["global", "dockerized"]

# #############################################################################


def _run_render_images(input_file: str) -> str:
    """
    Run render_images.py on input to process embedded diagrams.

    :param input_file: Input markdown file path
    :return: Path to processed file
    """
    # Find render_images.py.
    render_images_script = hgit.find_file("render_images.py")
    hdbg.dassert_file_exists(render_images_script)
    # Create output filename.
    output_file = "tmp.open_md.render_images.md"
    # Run render_images.py.
    # TODO(ai_gp): Build it with a list.
    cmd = f"{render_images_script} --input {input_file} --output {output_file} --action render"
    _LOG.info("Running render_images: %s", cmd)
    hsystem.system(cmd)
    hdbg.dassert_file_exists(output_file)
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
        if parts.endswith(".git"):
            parts = parts[:-4]
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
        _LOG.warning("Cannot open file on unsupported OS: %s",
                     platform.system())


def _open_on_github(input_file: str) -> None:
    """
    Open markdown file on GitHub in the browser.

    :param input_file: Path to the markdown file
    """
    _LOG.info("Opening file on GitHub: '%s'", input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Get absolute path and repo root.
    abs_file = os.path.abspath(input_file)
    repo_root = hgit.get_client_root(super_module=True)
    # Compute relative path from repo root.
    rel_path = os.path.relpath(abs_file, repo_root)
    # Get remote URL and convert to HTTPS.
    ret, remote_url = hsystem.system_to_one_line("git remote get-url origin")
    hdbg.dassert_eq(ret, 0, "Failed to get git remote URL")
    remote_url = remote_url.strip()
    remote_url = _convert_ssh_to_https(remote_url)
    # Get current branch.
    branch = hgit.get_branch_name(".")
    # Build GitHub URL.
    url = f"{remote_url}/blob/{branch}/{rel_path}"
    _LOG.info("GitHub URL: %s", url)
    # Open URL in browser.
    _open_file(url)


def _render_with_pandoc(
    input_file: str,
    *,
    backend: str,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Render markdown with pandoc to HTML and open in browser.

    :param input_file: Path to markdown file
    :param backend: "global" or "dockerized"
    :param force_rebuild: Force rebuild Docker image (for dockerized only)
    :param use_sudo: Use sudo for Docker (for dockerized only)
    """
    _LOG.info("Rendering with pandoc (backend=%s): '%s'", backend, input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Preprocess with render_images.
    processed_file = _run_render_images(input_file)
    # Determine output file.
    output_file = "tmp.open_md.pandoc.html"
    file_dir = os.path.dirname(os.path.abspath(processed_file))
    if backend == "global":
        # Run pandoc to HTML.
        cmd = (
            f"pandoc {processed_file} "
            f"-o {output_file} "
            f"--resource-path={file_dir} "
            f"--standalone"
        )
        _LOG.info("Running pandoc: %s", cmd)
        hsystem.system(cmd)
    elif backend == "dockerized":
        # Use dockerized pandoc.
        # TODO(ai_gp): Build it with multiple lines.
        cmd = f"pandoc {processed_file} -o {output_file} --resource-path={file_dir} --standalone"
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
    _open_file(output_file)


def _render_with_grip(
    input_file: str,
    *,
    backend: str,
) -> None:
    """
    Export markdown with grip and open HTML in browser.

    :param input_file: Path to markdown file
    :param backend: "global" or "dockerized"
    """
    _LOG.info("Rendering with grip (backend=%s): '%s'", backend, input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Preprocess with render_images.
    processed_file = _run_render_images(input_file)
    # Determine output file.
    output_file = "tmp.open_md.grip.html"
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
    # Open the output file.
    _open_file(output_file)


def _render_with_grip_daemon(
    input_file: str,
    *,
    backend: str,
) -> None:
    """
    Start grip daemon for live markdown preview.

    :param input_file: Path to markdown file
    :param backend: "global" or "dockerized"
    """
    _LOG.info("Starting grip daemon (backend=%s): '%s'", backend, input_file)
    # Validate input file exists.
    hdbg.dassert_file_exists(input_file)
    # Preprocess with render_images.
    processed_file = _run_render_images(input_file)
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


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to the markdown file to render/open",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=_VALID_MODES,
        required=True,
        help="Rendering mode",
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=_VALID_BACKENDS,
        default="global",
        help="Backend to use for rendering",
    )
    hdocker.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Dispatch to appropriate handler based on mode.
    if args.mode == "github":
        _open_on_github(args.input)
    elif args.mode == "pandoc":
        _render_with_pandoc(
            args.input,
            backend=args.backend,
            force_rebuild=args.dockerized_force_rebuild,
            use_sudo=args.dockerized_use_sudo,
        )
    elif args.mode == "grip":
        _render_with_grip(args.input, backend=args.backend)
    elif args.mode == "grip_daemon":
        _render_with_grip_daemon(args.input, backend=args.backend)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    _main(_parse())
