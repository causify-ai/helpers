#!/usr/bin/env python3
"""
Stop Synthesia video generation.

This script cancels video generation jobs from the Synthesia API using their
Cancel Video Generation endpoint.

Usage:
> python stop_synthesia_videos.py --ids "id1 id2 id3"
> python stop_synthesia_videos.py --delete-all

Environment:
  SYNTHESIA_API_KEY  Your Synthesia API key (Creator plan or above).
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List

import requests

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

API_BASE = "https://api.synthesia.io/v2"
TIMEOUT = 30  # seconds per HTTP request


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


def get_all_videos(api_key: str) -> List[Dict[str, Any]]:
    """
    Get all videos from Synthesia API.

    :param api_key: Synthesia API key
    :return: list of video objects
    """
    url = f"{API_BASE}/videos"
    params = {"limit": 100, "offset": 0}
    all_videos = []
    while True:
        resp = requests.get(
            url, headers=_headers(api_key), params=params, timeout=TIMEOUT
        )
        if resp.status_code != 200:
            raise SynthesiaError(
                f"Get videos failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        videos = data.get("videos", [])
        all_videos.extend(videos)
        if len(videos) < params["limit"]:
            break
        params["offset"] += params["limit"]
    _LOG.debug(f"Retrieved {len(all_videos)} total videos")
    return all_videos


def cancel_video(api_key: str, video_id: str) -> bool:
    """
    Cancel a specific video generation.

    :param api_key: Synthesia API key
    :param video_id: video ID to cancel
    :return: True if successful, False otherwise
    """
    # Make API call to cancel video generation.
    url = f"{API_BASE}/videos/{video_id}/cancel"
    resp = requests.post(url, headers=_headers(api_key), timeout=TIMEOUT)
    # Check response and log result.
    if resp.status_code == 200:
        _LOG.info("Successfully cancelled video %s", video_id)
        return True
    else:
        _LOG.error(
            "Failed to cancel video %s (%s): %s",
            video_id,
            resp.status_code,
            resp.text,
        )
        return False


def delete_video(api_key: str, video_id: str) -> bool:
    """
    Delete a specific video.

    :param api_key: Synthesia API key
    :param video_id: video ID to delete
    :return: True if successful, False otherwise
    """
    # Make API call to delete video.
    url = f"{API_BASE}/videos/{video_id}"
    resp = requests.delete(url, headers=_headers(api_key), timeout=TIMEOUT)
    # Check response (both 200 and 204 are success for delete).
    if resp.status_code in [200, 204]:
        _LOG.info("Successfully deleted video %s", video_id)
        return True
    else:
        _LOG.error(
            "Failed to delete video %s (%s): %s",
            video_id,
            resp.status_code,
            resp.text,
        )
        return False


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Stop Synthesia video generation."
    )
    hparser.add_verbosity_arg(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--ids",
        help="Space-separated list of video IDs to cancel (e.g., 'id1 id2 id3')",
    )
    group.add_argument(
        "--delete-all",
        action="store_true",
        help="Delete all completed and in-progress videos",
    )
    args = parser.parse_args()
    return args


def _main(args: argparse.Namespace) -> None:
    """
    Main function to stop video generation.

    :param args: parsed arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate API key is available.
    api_key = os.getenv("SYNTHESIA_API_KEY")
    hdbg.dassert(api_key, "Environment variable SYNTHESIA_API_KEY is not set")
    try:
        if args.delete_all:
            # Delete all videos mode.
            _LOG.info("Deleting all videos...")
            videos = get_all_videos(api_key)
            _LOG.info("Found %s videos to delete", len(videos))
            # Process each video for deletion.
            success_count = 0
            for video in videos:
                video_id = video.get("id")
                if video_id:
                    if delete_video(api_key, video_id):
                        success_count += 1
            _LOG.info(
                "Successfully deleted %s out of %s videos",
                success_count,
                len(videos),
            )
        else:
            # Cancel specific video IDs mode.
            video_ids = args.ids.split()
            _LOG.info("Attempting to cancel %s videos", len(video_ids))
            # Process each video ID for cancellation.
            success_count = 0
            for video_id in video_ids:
                if cancel_video(api_key, video_id):
                    success_count += 1
            _LOG.info(
                "Successfully cancelled %s out of %s videos",
                success_count,
                len(video_ids),
            )
    except requests.RequestException as e:
        _LOG.error("HTTP error: %s", e)
        sys.exit(1)
    except SynthesiaError as e:
        _LOG.error("Synthesia API error: %s", e)
        sys.exit(1)


def main() -> None:
    """
    Main entry point.
    """
    args = _parse()
    _main(args)


if __name__ == "__main__":
    main()
