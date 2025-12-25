#!/usr/bin/env python3
"""
Create a video from a text script and a chosen avatar using the Synthesia API.

# Do a dry-run:
> generate_synthesia_videos.py \
    --in_dir videos \
    --limit "1:3" \
    --dry_run

# Do a real run:
> generate_synthesia_videos.py \
    --in_dir videos \
    --limit "1:3"

Environment:
  SYNTHESIA_API_KEY  Your Synthesia API key (Creator plan or above).
"""

import argparse
import glob
import json
import logging
import os
import pprint
import re
from typing import Any, Dict, List, Tuple

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Seconds per HTTP request.
TIMEOUT_IN_SECS = 30


def _discover_text_files(in_dir: str) -> List[Tuple[int, str]]:
    """
    Discover all the files with format `XYZ_comment.txt` in the directory.

    :param in_dir: input directory to search
    :return: list of (slide_number, file_path) tuples sorted by slide
        number
    """
    hdbg.dassert_dir_exists(in_dir)
    # Discover all text files.
    pattern = os.path.join(in_dir, "*_comment.txt")
    text_files = glob.glob(pattern)
    # Extract slide numbers and sort.
    slides = []
    for file_path in text_files:
        filename = os.path.basename(file_path)
        match = re.match(r"(\d+)_comment\.txt", filename)
        if match:
            slide_num = int(match.group(1))
            slides.append((slide_num, file_path))
    # Sort by slide number.
    slides.sort(key=lambda x: x[0])
    _LOG.debug("Found %s text files", len(slides))
    return slides


def _headers(api_key: str) -> Dict[str, str]:
    """
    Create headers for Synthesia API requests.

    :param api_key: Synthesia API key
    :return: headers dictionary
    """
    # Synthesia docs instruct to place the API key in the Authorization header.
    # Do not prefix with "Bearer" unless your account specifically requires it.
    return {
        "Authorization": api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_video(
    api_key: str,
    script_text: str,
    avatar: str,
    title: str,
    background: str,
    *,
    aspect_ratio: str = "5:4",
    resolution: str = "720p",
    test: bool = False,
) -> str:
    """
    Create a Synthesia video and return the video_id from the API response.

    :param api_key: Synthesia API key
    :param script_text: text script
    :param avatar: avatar
    :param title: title
    :param background: background
    :param aspect_ratio: aspect ratio
    :param resolution: resolution
    :param test: test
    :return: video_id
    """
    api_base = "https://api.synthesia.io/v2"
    url = f"{api_base}/videos"
    scene: Dict[str, Any] = {
        "scriptText": script_text,
    }
    scene["avatar"] = avatar
    if background:
        scene["background"] = background
    payload: Dict[str, Any] = {
        "title": title,
        "input": [scene],
    }
    # Add video parameters (required even for audio-only in this API)
    if aspect_ratio:
        payload["aspectRatio"] = aspect_ratio
    if resolution:
        payload["resolution"] = resolution
    if test:
        payload["test"] = test
    # Call the Synthesia API.
    _LOG.debug("Creating video with parameters:\n%s", pprint.pformat(payload))
    resp = requests.post(
        url,
        headers=_headers(api_key),
        data=json.dumps(payload),
        timeout=TIMEOUT_IN_SECS,
    )
    # Check the response.
    if resp.status_code != 201:
        raise ValueError(
            f"Create video failed ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    # Extract the video ID.
    video_id = data.get("id") or data.get("videoId")
    if not video_id:
        raise ValueError(f"Unexpected response (no video id): {data}")
    return video_id


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Create a Synthesia video from text + avatar."
    )
    hparser.add_verbosity_arg(parser)
    # Flow to process slides from a directory.
    parser.add_argument(
        "--in_dir",
        required=False,
        help="Directory containing xyz_comment.txt files",
    )
    parser.add_argument(
        "--out_dir",
        required=False,
        help="Directory to save the videos",
    )
    hparser.add_limit_range_arg(parser)
    # Flow to process a single text file.
    parser.add_argument(
        "--in_file",
        required=False,
        help="Text file containing the script to be used for the video",
    )
    parser.add_argument(
        "--out_file",
        required=False,
        help="Directory to save the videos",
    )
    #
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print what will be executed without calling Synthesia API",
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Do not create incremental directories",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Create test video using Synthesia API test mode",
    )
    args = parser.parse_args()
    return args


def _process_slides(
    args: argparse.Namespace,
    slides_info: List[Tuple[int, str]],
    avatar: str,
    background: str,
    aspect: str,
    resolution: str,
) -> None:
    """
    Process slides from a directory.

    :param args: parsed arguments
    :param slides_info: filtered slides in the format (slide_num,
        file_path)
    :param avatar: avatar
    :param background: background
    :param aspect: aspect
    :param resolution: resolution
    """
    hdbg.dassert_isinstance(slides_info, list)
    hdbg.dassert_lte(0, len(slides_info), "slides_info is empty")
    # Load scripts from filtered slides.
    slides = []
    for slide_info_tmp in slides_info:
        hdbg.dassert_isinstance(slide_info_tmp, tuple)
        hdbg.dassert_eq(len(slide_info_tmp), 3)
        slide_num, in_file, out_file = slide_info_tmp
        script = hio.from_file(in_file)
        slides.append((script, out_file))
        _LOG.info("Loaded text for slide %d from '%s'", slide_num, in_file)
    # Create videos.
    for script, out_file in slides:
        if args.dry_run:
            # Print what would be executed without making API calls.
            _LOG.warning("DRY RUN: Create video with parameters:")
            _LOG.info("  Title: %s", out_file)
            _LOG.info("  Avatar: %s", avatar)
            _LOG.info("  Background: %s", background)
            _LOG.info("  Aspect ratio: %s", aspect)
            _LOG.info("  Resolution: %s", resolution)
            _LOG.info("  Script text length: %s characters", len(script))
            _LOG.info("  Script text:\n%s", script)
        else:
            api_key = os.getenv("SYNTHESIA_API_KEY")
            hdbg.dassert(
                api_key, "Environment variable SYNTHESIA_API_KEY is not set"
            )
            test = args.test
            video_id = create_video(
                api_key=api_key,
                script_text=script,
                avatar=avatar,
                title=out_file,
                background=background,
                aspect_ratio=aspect,
                resolution=resolution,
                test=test,
                # extra_scene_overrides=extra,
            )
            _LOG.info("Creating video: id=%s", video_id)


def _main(args: argparse.Namespace) -> None:
    """
    Main function to create Synthesia videos.

    :param args: parsed arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # avatar = "f4f1005e-6851-414a-9120-d48122613fa0"
    avatar = "3b4c81e9-d476-40f6-93ff-2b817557cc1d"
    background = "workspace-media.c4ab7049-8479-4855-9856-e0d7f2854027"
    aspect = "5:4"
    resolution = "720p"
    # Process slides.
    if args.in_dir:
        in_dir = args.in_dir
        hdbg.dassert_dir_exists(in_dir)
        #
        if args.no_incremental:
            hio.backup_file_or_dir_if_exists(args.out_dir)
        hio.create_dir(args.out_dir, incremental=True)
        # Discover all text files in the directory.
        discovered_slides = _discover_text_files(in_dir)
        _LOG.info(
            "Discovered %s text files in %s", len(discovered_slides), in_dir
        )
        # Parse limit range from command line arguments.
        limit_range = hparser.parse_limit_range_args(args)
        # Apply limit range filtering to discovered slides.
        slide_tuples = [
            (slide_num, file_path) for slide_num, file_path in discovered_slides
        ]
        filtered_slide_tuples = hparser.apply_limit_range(
            slide_tuples, limit_range, item_name="slides"
        )
        # Prepare workload.
        slides_info = []
        for slide_num, file_path in filtered_slide_tuples:
            out_file = f"slide{slide_num}"
            slides_info.append((slide_num, file_path, out_file))
        # Process slides.
        _process_slides(
            args, slides_info, avatar, background, aspect, resolution
        )
    elif args.in_file:
        hdbg.dassert_file_exists(args.in_file)
        hio.backup_file_or_dir_if_exists(args.out_file)
        hio.create_enclosing_dir(args.out_file, incremental=True)
        # Prepare workload.
        slides_info = [(0, args.in_file, args.out_file)]
        # Process slides.
        _process_slides(
            args, slides_info, avatar, background, aspect, resolution
        )
    else:
        raise ValueError("Either --in_dir or --in_file must be provided")


def main() -> None:
    """
    Main entry point.
    """
    args = _parse()
    _main(args)


if __name__ == "__main__":
    main()
