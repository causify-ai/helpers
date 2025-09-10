#!/usr/bin/env python3
"""
Download Synthesia videos.

This script downloads completed videos from the Synthesia API using their
download URLs and saves them with meaningful names.

Usage:
> download_synthesia_video.py --ids "id1 id2 id3"
> download_synthesia_video.py --ids "id1 id2" --out_dir downloads

The videos will be saved with names like: slide1.id1.mp4, slide2.id2.mp4

Environment:
  SYNTHESIA_API_KEY  Your Synthesia API key (Creator plan or above).
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

API_BASE = "https://api.synthesia.io/v2"
TIMEOUT = 30  # seconds per HTTP request
DOWNLOAD_TIMEOUT = 300  # 5 minutes for video downloads


# #############################################################################
# SynthesiaError
# #############################################################################


class SynthesiaError(RuntimeError):
    pass


def _headers(api_key: str) -> Dict[str, str]:
    """
    Create headers for Synthesia API requests.

    :param api_key: Synthesia API key
    :return: headers dictionary
    """
    return {
        "Authorization": api_key.strip(),
        "Accept": "application/json",
    }


def get_video(api_key: str, video_id: str) -> Dict[str, Any]:
    """
    Get video details from Synthesia API.

    :param api_key: Synthesia API key
    :param video_id: video ID to retrieve
    :return: video object
    """
    url = f"{API_BASE}/videos/{video_id}"
    resp = requests.get(url, headers=_headers(api_key), timeout=TIMEOUT)
    if resp.status_code != 200:
        raise SynthesiaError(
            f"Get video failed ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def _download_file(url: str, file_path: str) -> bool:
    """
    Download a file from URL using streaming download.

    :param url: URL to download from
    :param file_path: local file path to save to
    :return: True if successful, False otherwise
    """
    with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as resp:
        resp.raise_for_status()
        total_size = int(resp.headers.get("content-length", 0))
        downloaded = 0
        # TODO(ai): Use hio.to_file.
        with open(file_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        _LOG.debug(f"Download progress: {progress:.1f}%")
        _LOG.info(f"Downloaded {downloaded} bytes to {file_path}")
        return True


def download_video(api_key: str, video_id: str, out_dir: str) -> bool:
    """
    Download a specific video.

    :param api_key: Synthesia API key
    :param video_id: video ID to download
    :param out_dir: output directory
    :return: True if successful, False otherwise
    """
    # Get video details from API.
    video = get_video(api_key, video_id)
    # Validate video is ready for download.
    status = video.get("status")
    if status not in ["completed", "complete"]:
        _LOG.warning("Video %s is not completed (status: %s)", video_id, status)
        return False
    # Check download information is available.
    download_info = video.get("download")
    if not download_info:
        _LOG.error("No download information available for video %s", video_id)
        return False
    # Handle both string URL and dict with "video" key formats.
    if isinstance(download_info, str):
        video_url = download_info
    elif isinstance(download_info, dict):
        video_url = download_info.get("video")
        if not video_url:
            _LOG.error("No video download URL available for video %s", video_id)
            return False
    else:
        _LOG.error("Invalid download information format for video %s", video_id)
        return False
    # Generate safe output filename.
    title = video.get("title", "video")
    # Clean title to be filesystem-safe.
    safe_title = "".join(c for c in title if c.isalnum() or c in "._-")
    filename = f"{safe_title}.{video_id}.mp4"
    file_path = os.path.join(out_dir, filename)
    _LOG.info("Downloading video %s (%s) to %s", video_id, title, file_path)
    # Perform the actual download.
    return _download_file(video_url, file_path)


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(description="Download Synthesia videos.")
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--ids",
        required=True,
        help="Space-separated list of video IDs to download (e.g., 'id1 id2 id3')",
    )
    parser.add_argument(
        "--out_dir",
        default=".",
        help="Output directory for downloaded videos (default: current directory)",
    )
    args = parser.parse_args()
    return args


def _main(args: argparse.Namespace) -> None:
    """
    Main function to download videos.

    :param args: parsed arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate API key is available.
    api_key = os.getenv("SYNTHESIA_API_KEY")
    hdbg.dassert(api_key, "Environment variable SYNTHESIA_API_KEY is not set")
    # Ensure output directory exists.
    out_dir = args.out_dir
    hio.create_dir(out_dir, incremental=True)
    # Parse video IDs from command line.
    video_ids = args.ids.split()
    _LOG.info("Attempting to download %s videos to %s", len(video_ids), out_dir)
    # Process each video ID for download.
    success_count = 0
    for video_id in video_ids:
        if download_video(api_key, video_id, out_dir):
            success_count += 1
    _LOG.info(
        "Successfully downloaded %s out of %s videos",
        success_count,
        len(video_ids),
    )
    # Exit with error if some downloads failed.
    if success_count < len(video_ids):
        sys.exit(1)


def main() -> None:
    """
    Main entry point.
    """
    args = _parse()
    _main(args)


if __name__ == "__main__":
    main()
