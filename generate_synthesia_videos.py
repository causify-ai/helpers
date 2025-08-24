#!/usr/bin/env python3
"""
Synthesia API helper: create a video from a text script and a chosen avatar.

> python generate_synthesia_videos.py \
    --in_dir videos \
    --slides "001:003"

> python generate_synthesia_videos.py \
    --in_dir videos \
    --slides "001:003" \
    --dry_run

Environment:
  SYNTHESIA_API_KEY  Your Synthesia API key (Creator plan or above).
"""

import argparse
import glob
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Tuple

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

API_BASE = "https://api.synthesia.io/v2"
TIMEOUT = 30  # seconds per HTTP request
POLL_EVERY = 6  # seconds between status polls
MAX_WAIT = 60 * 30  # 30 minutes max


# #############################################################################
# SynthesiaError
# #############################################################################


class SynthesiaError(RuntimeError):
    pass


def _parse_slide_range(slide_range: str) -> List[int]:
    """
    Parse slide range specification into list of slide numbers.
    
    :param slide_range: range specification like "001:003", "001,005", "001:003,005:007"
    :return: list of slide numbers
    """
    slide_numbers = []
    # Split by comma for multiple ranges.
    parts = slide_range.split(",")
    for part in parts:
        part = part.strip()
        if ":" in part:
            # Range format: 001:003
            start, end = part.split(":")
            start_num = int(start)
            end_num = int(end)
            slide_numbers.extend(range(start_num, end_num + 1))
        else:
            # Single slide: 001
            slide_numbers.append(int(part))
    return sorted(list(set(slide_numbers)))


def _discover_text_files(in_dir: str) -> List[Tuple[int, str]]:
    """
    Discover all XXX_text.txt files in the directory.
    
    :param in_dir: input directory to search
    :return: list of (slide_number, file_path) tuples sorted by slide number
    """
    hdbg.dassert_dir_exists(in_dir)
    # Discover all text files.
    pattern = os.path.join(in_dir, "*_text.txt")
    text_files = glob.glob(pattern)
    # Extract slide numbers and sort.
    slides = []
    for file_path in text_files:
        filename = os.path.basename(file_path)
        match = re.match(r"(\d+)_text\.txt", filename)
        if match:
            slide_num = int(match.group(1))
            slides.append((slide_num, file_path))
    # Sort by slide number.
    slides.sort(key=lambda x: x[0])
    _LOG.debug(f"Found {len(slides)} text files")
    return slides


def _headers(api_key: str) -> Dict[str, str]:
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
    # TODO(ai): Remove audio_only.
    audio_only: bool = False,
    test: bool = False,
) -> str:
    """
    Create a Synthesia video. Returns the video_id from the 201 response.

    The minimal required fields per docs are provided below: title, input (scenes),
    and inside a scene: scriptText + avatar. Background is optional.
    """
    url = f"{API_BASE}/videos"
    scene: Dict[str, Any] = {
        "scriptText": script_text,
    }

    # Always set avatar and background - Synthesia API requires these fields
    scene["avatar"] = avatar
    if background:
        scene["background"] = background

    # if extra_scene_overrides:
    #     scene.update(extra_scene_overrides)

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
    # payload["test"] = False
    # payload["test"] = True

    resp = requests.post(
        url, headers=_headers(api_key), data=json.dumps(payload), timeout=TIMEOUT
    )
    if resp.status_code != 201:
        raise SynthesiaError(
            f"Create video failed ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    video_id = data.get("id") or data.get("videoId")
    if not video_id:
        raise SynthesiaError(f"Unexpected response (no video id): {data}")
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
    parser.add_argument("--slide", type=int, default=0, help="Slide number")
    parser.add_argument("--in_dir", default="videos", help="Directory containing xyz_text.txt files")
    parser.add_argument("--slides", help="Range of slides to process (e.g., '001:003', '002:005,007:009')")
    parser.add_argument("--dry_run", action="store_true", help="Print what will be executed without calling Synthesia API")
    args = parser.parse_args()
    return args


def _main(args: argparse.Namespace) -> None:
    """
    Main function to create Synthesia videos.

    :param args: parsed arguments
    """
    avatar = "f4f1005e-6851-414a-9120-d48122613fa0"
    background = "workspace-media.c4ab7049-8479-4855-9856-e0d7f2854027"
    aspect = "5:4"
    resolution = "720p"
    #
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    api_key = os.getenv("SYNTHESIA_API_KEY")
    hdbg.dassert(api_key, "Environment variable SYNTHESIA_API_KEY is not set")
    in_dir = args.in_dir
    # Discover all text files in the directory.
    discovered_slides = _discover_text_files(in_dir)
    _LOG.info(f"Discovered {len(discovered_slides)} text files in {in_dir}")
    # Filter slides based on --slides parameter if provided.
    if args.slides:
        requested_slides = _parse_slide_range(args.slides)
        _LOG.info(f"Requested slides: {requested_slides}")
        # Filter discovered slides to only include requested ones.
        filtered_slides = [(slide_num, file_path) for slide_num, file_path in discovered_slides 
                          if slide_num in requested_slides]
        if not filtered_slides:
            _LOG.error(f"No slides found matching the requested range: {args.slides}")
            sys.exit(1)
    else:
        # Use all discovered slides if no range specified.
        filtered_slides = discovered_slides
    # Load scripts from filtered slides.
    slides = []
    for slide_num, file_path in filtered_slides:
        script = hio.from_file(file_path)
        out_file = f"slide{slide_num}"
        slides.append((script, out_file))
        _LOG.info(f"Loaded slide {slide_num:03d} from {file_path}")
    # Create videos.
    for script, out_file in slides:
        if args.dry_run:
            # Print what would be executed without making API calls.
            _LOG.info(f"DRY RUN: Would create video with parameters:")
            _LOG.info(f"  Title: {out_file}")
            _LOG.info(f"  Avatar: {avatar}")
            _LOG.info(f"  Background: {background}")
            _LOG.info(f"  Aspect ratio: {aspect}")
            _LOG.info(f"  Resolution: {resolution}")
            _LOG.info(f"  Script text length: {len(script)} characters")
            _LOG.debug(f"  Script text: {script[:100]}..." if len(script) > 100 else f"  Script text: {script}")
        else:
            try:
                audio_only = False
                # TODO(ai): Pass test through command line.
                test = False
                video_id = create_video(
                    api_key=api_key,
                    script_text=script,
                    avatar=avatar,
                    title=out_file,
                    background=background,
                    aspect_ratio=aspect,
                    resolution=resolution,
                    audio_only=audio_only,
                    test=test,
                    # extra_scene_overrides=extra,
                )
                _LOG.info(f"Created video: id={video_id}")
            except requests.RequestException as e:
                _LOG.error(f"HTTP error: {e}")
                sys.exit(1)
            except SynthesiaError as e:
                _LOG.error(f"Synthesia API error: {e}")
                sys.exit(1)


def main() -> None:
    """
    Main entry point.
    """
    args = _parse()
    _main(args)


if __name__ == "__main__":
    main()
