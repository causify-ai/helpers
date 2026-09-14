#!/usr/bin/env -S uv run

# /// script
# dependencies = ["requests", "Pillow"]
# ///

"""
Download an image from a URL and save it to a destination file.

If `--url` points directly to an image (based on the response
`Content-Type`), it is downloaded as-is. If it points to an HTML page (e.g.,
a blog article), the `og:image` meta tag is extracted and that image is
downloaded instead.

The downloaded image is converted to the format implied by `--output`'s
extension (e.g., a source `.webp` is converted to `.png` if `--output` ends
in `.png`), so the destination format never depends on what the source
server happens to serve.

# Usage Example

- Download an image directly from its URL:
> download_images.py --url https://example.com/image.png --output image.png

- Download the hero image of an article page (extracted from its
  `og:image` meta tag):
> download_images.py --url https://example.com/article --output image.png

- Overwrite an existing destination file:
> download_images.py --url https://example.com/image.png --output image.png --no_incremental

- Show what would be downloaded without actually downloading:
> download_images.py --url https://example.com/image.png --output image.png --dry_run
"""

import argparse
import io
import logging
import os
import re

import requests
from PIL import Image

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Timeout in seconds for HTTP requests.
TIMEOUT = 30

# Some hosts (e.g., Wikimedia) reject requests without a descriptive
# User-Agent.
HEADERS = {
    "User-Agent": (
        "download_images.py/1.0 "
        "(https://github.com/causify-ai/umd_classes; saggese@gmail.com)"
    )
}

# Map a destination file extension to the corresponding Pillow format name.
EXTENSION_TO_FORMAT = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".tif": "TIFF",
    ".tiff": "TIFF",
}


def _extract_og_image(html: str, *, url: str) -> str:
    """
    Extract the `og:image` meta tag URL from an HTML page.

    :param html: HTML content of the page
    :param url: original page URL, used only for the error message
    :return: URL of the `og:image`
    """
    match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        html,
    )
    match = hdbg.dassert_re_match(
        match, "Could not find 'og:image' meta tag in '%s'", url
    )
    image_url = match.group(1)
    return image_url


def _resolve_image_url(url: str) -> str:
    """
    Resolve `url` to a direct image URL.

    If `url` already points to a binary image (based on the response
    `Content-Type`), return it unchanged. Otherwise, treat it as an HTML
    page and extract the `og:image` meta tag.

    :param url: URL to resolve
    :return: direct image URL
    """
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    if content_type.startswith("image/"):
        _LOG.debug("URL is a direct image (Content-Type='%s')", content_type)
        return url
    _LOG.info(
        "URL is not a direct image (Content-Type='%s'), extracting "
        "'og:image' meta tag",
        content_type,
    )
    image_url = _extract_og_image(resp.text, url=url)
    return image_url


def _get_format_from_extension(output_file: str) -> str:
    """
    Map `output_file`'s extension to a Pillow image format name.

    :param output_file: destination file path
    :return: Pillow format name (e.g., "PNG", "JPEG")
    """
    ext = os.path.splitext(output_file)[1].lower()
    hdbg.dassert_in(
        ext,
        EXTENSION_TO_FORMAT,
        "Unsupported output extension '%s'; supported extensions are: %s",
        ext,
        ", ".join(sorted(EXTENSION_TO_FORMAT.keys())),
    )
    format_ = EXTENSION_TO_FORMAT[ext]
    return format_


def _convert_and_save(content: bytes, output_file: str) -> None:
    """
    Convert raw image `content` to the format implied by `output_file`'s
    extension and save it there.

    :param content: raw bytes of the downloaded image
    :param output_file: destination file path
    """
    format_ = _get_format_from_extension(output_file)
    image = Image.open(io.BytesIO(content))
    source_format = image.format
    if format_ == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        # JPEG has no alpha channel: flatten onto a white background.
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode not in ("RGB", "RGBA", "L"):
        image = image.convert("RGB")
    hio.create_enclosing_dir(output_file, incremental=True)
    image.save(output_file, format=format_)
    if source_format != format_:
        _LOG.info("Converted image from '%s' to '%s'", source_format, format_)


def download_image(
    url: str, output_file: str, *, dry_run: bool = False
) -> None:
    """
    Download the image at `url`, convert it to the format implied by
    `output_file`'s extension, and save it there.

    :param url: URL of the image, or of an HTML page containing an
        `og:image` meta tag
    :param output_file: destination file path
    :param dry_run: if True, show what would be done without downloading
    """
    # Validate the output extension before doing any network work.
    _get_format_from_extension(output_file)
    image_url = _resolve_image_url(url)
    if dry_run:
        _LOG.warning(
            "[DRY_RUN] Would download '%s' to '%s'", image_url, output_file
        )
        return
    resp = requests.get(image_url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    _convert_and_save(resp.content, output_file)
    size = os.path.getsize(output_file)
    _LOG.info("Saved %d bytes to '%s'", size, output_file)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--url",
        required=True,
        action="store",
        help="URL of the image, or of an HTML page containing an "
        "'og:image' meta tag",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        action="store",
        help="Destination file path for the downloaded image",
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Overwrite the destination file even if it already exists",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually downloading",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if (
        os.path.exists(args.output)
        and not args.no_incremental
        and not args.dry_run
    ):
        _LOG.warning(
            "Output file already exists, skipping: '%s'", args.output
        )
        return
    download_image(args.url, args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    _main(_parse())
