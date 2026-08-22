#!/usr/bin/env python

"""
Save an image to a file, from an interactive screenshot, the system
clipboard, or a URL.

The script should be run from the command line outside of a Docker
container.

# Usage Example

- Take an interactive screenshot and save it as PNG:
  > save_screenshot.py

- Save the image currently on the clipboard (e.g., copied with Cmd+Ctrl+Shift+4):
  > save_screenshot.py --from_clipboard

- Download an image from a URL, keeping its `png` / `jpg` extension:
  > save_screenshot.py --url https://example.com/image.png

- Save into a specific dir, using a specific file name:
  > save_screenshot.py --from_clipboard --path msml610/lectures_source/figures --filename Lesson12_4x3_environment.png
"""

import argparse
import datetime
import logging
import os

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Extensions recognized as image formats when inferring the file name from a
# URL.
_VALID_EXTENSIONS = ["png", "jpg", "jpeg"]

# #############################################################################
# Extension / filename helpers.
# #############################################################################


def _get_extension_from_url(url: str) -> str:
    """
    Infer the image extension (`png`, `jpg`, `jpeg`) from a URL.

    :param url: URL of the image, e.g., "https://example.com/image.jpg"
    :return: lowercase extension without the leading dot
        - Falls back to "png" if the URL has no recognized image
          extension
    """
    ext = os.path.splitext(url)[1].lstrip(".").lower()
    if ext not in _VALID_EXTENSIONS:
        _LOG.warning(
            "Could not infer image format from URL '%s': using 'png'", url
        )
        ext = "png"
    return ext


def _build_filename(path: str, filename: str, ext: str) -> str:
    """
    Build the destination file path.

    :param path: destination directory (e.g., "msml610/lectures_source/figures")
    :param filename: file name provided by the user
        - If empty, a timestamped name is generated
    :param ext: extension to use when `filename` is not provided (e.g., "png")
    :return: destination file path, e.g., "figures/screenshot.2026-08-22_10-00-00.png"
    """
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot.{timestamp}.{ext}"
    if path:
        # E.g., lectures_source/tutorial_msml610/notebooks/figures
        filename = os.path.join(path, filename)
    return filename


# #############################################################################
# Capture sources.
# #############################################################################


def _download_image(url: str, filename: str) -> None:
    """
    Download the image at `url` and save it to `filename`.

    :param url: URL of the image to download
    :param filename: destination file path
    """
    _LOG.info("Downloading image from '%s'", url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)


def _capture_from_clipboard(filename: str) -> None:
    """
    Save the image currently on the system clipboard to `filename`.

    :param filename: destination file path
    """
    hdbg.dassert(
        hserver.is_host_mac(), "Reading images from the clipboard needs macOS"
    )
    # `pngpaste` converts whatever image is on the clipboard (e.g., a
    # screenshot copied with Cmd+Ctrl+Shift+4) to PNG.
    cmd = f"pngpaste {filename}"
    hsystem.system(cmd)


def _capture_screenshot(filename: str) -> None:
    """
    Take an interactive macOS screenshot and save it to `filename`.

    :param filename: destination file path
    """
    _LOG.info("Take screenshot with Command (⌘) + Control + 4 ...")
    cmd = f"screencapture -i -t png {filename}"
    _LOG.info("cmd: %s", cmd)
    hsystem.system(cmd)


# #############################################################################
# Main.
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--url", type=str, default="", help="Download an image from a URL"
    )
    source_group.add_argument(
        "--from_clipboard",
        action="store_true",
        help="Save the image currently on the system clipboard (uses `pngpaste`)",
    )
    parser.add_argument("--path", type=str, default="", help="Destination directory")
    parser.add_argument("--filename", type=str, default="", help="File name")
    parser.add_argument(
        "--override", action="store_true", help="Override if file exists"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Determine the format: a downloaded image keeps its own extension,
    # while a screenshot or clipboard paste is always PNG.
    if args.url:
        ext = _get_extension_from_url(args.url)
    else:
        ext = "png"
    filename = _build_filename(args.path, args.filename, ext)
    _LOG.info("filename: %s", filename)
    if not args.override:
        hdbg.dassert_path_not_exists(filename)
    if args.path:
        hio.create_dir(args.path, incremental=True)
    # Save the image using the requested source.
    if args.url:
        _download_image(args.url, filename)
    elif args.from_clipboard:
        _capture_from_clipboard(filename)
    else:
        _capture_screenshot(filename)
    # Print the info about the image.
    txt = f"![]({filename})"
    _LOG.info("%s", txt)
    # <img src="image.jpg" alt="A tree" width="300" title="This is a tree">
    if hserver.is_host_mac():
        _LOG.warning("Copied to clipboard")
        cmd = f"echo '{txt}' | pbcopy"
        hsystem.system(cmd)


if __name__ == "__main__":
    _main(_parse())
