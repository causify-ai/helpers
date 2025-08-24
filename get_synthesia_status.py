#!/usr/bin/env python3
"""
Get Synthesia video generation status.

This script retrieves the status of video generation jobs from the Synthesia API
and displays them in a formatted table.

Usage:
> python get_synthesia_status.py

Environment:
  SYNTHESIA_API_KEY  Your Synthesia API key (Creator plan or above).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import requests

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

API_BASE = "https://api.synthesia.io/v2"
TIMEOUT = 30  # seconds per HTTP request


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


def _format_timestamp(timestamp: str) -> str:
    """
    Format ISO timestamp to readable format.
    
    :param timestamp: ISO timestamp string
    :return: formatted timestamp
    """
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return timestamp


def get_videos_status(api_key: str, *, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get list of videos and their status from Synthesia API.
    
    :param api_key: Synthesia API key
    :param limit: maximum number of videos to retrieve
    :param offset: offset for pagination
    :return: list of video objects
    """
    url = f"{API_BASE}/videos"
    params = {
        "limit": limit,
        "offset": offset,
    }
    resp = requests.get(
        url, headers=_headers(api_key), params=params, timeout=TIMEOUT
    )
    if resp.status_code != 200:
        raise SynthesiaError(
            f"Get videos failed ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    videos = data.get("videos", [])
    _LOG.debug(f"Retrieved {len(videos)} videos")
    return videos


def display_videos_status(videos: List[Dict[str, Any]]) -> None:
    """
    Display videos status in a formatted table.
    
    :param videos: list of video objects from API
    """
    if not videos:
        print("No videos found.")
        return
    
    # Print header.
    headers = ["ID", "Created", "Updated", "Title", "Status", "Download"]
    print("\t".join(headers))
    print("-" * 80)
    
    # Print video data.
    for video in videos:
        video_id = video.get("id", "N/A")
        created_at = _format_timestamp(video.get("createdAt"))
        updated_at = _format_timestamp(video.get("lastUpdatedAt"))
        title = video.get("title", "N/A")
        status = video.get("status", "N/A")
        download = "Yes" if video.get("download") else "No"
        
        row = [video_id, created_at, updated_at, title, status, download]
        print("\t".join(row))


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Get Synthesia video generation status."
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--limit", 
        type=int, 
        default=20, 
        help="Maximum number of videos to retrieve (default: 20)"
    )
    parser.add_argument(
        "--offset", 
        type=int, 
        default=0, 
        help="Offset for pagination (default: 0)"
    )
    args = parser.parse_args()
    return args


def _main(args: argparse.Namespace) -> None:
    """
    Main function to get and display video status.
    
    :param args: parsed arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    
    api_key = os.getenv("SYNTHESIA_API_KEY")
    hdbg.dassert(api_key, "Environment variable SYNTHESIA_API_KEY is not set")
    videos = get_videos_status(
        api_key, limit=args.limit, offset=args.offset
    )
    display_videos_status(videos)
    _LOG.info(f"Retrieved status for {len(videos)} videos")


def main() -> None:
    """
    Main entry point.
    """
    args = _parse()
    _main(args)


if __name__ == "__main__":
    main()
