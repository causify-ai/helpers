#!/usr/bin/env python3

"""
Create a composite presentation video from slide MP4 files with PIP overlays.

This script processes MP4 files in a directory to create a concatenated video
with picture-in-picture overlays. For each XXX_slide.mp4 file, it can include:
- XXX_pip.mp4 as a centered PIP overlay
- XXX_comment.mp4 as a bottom-right PIP overlay

The script supports two modes:
1. Default mode: Uses fixed positioning (center for pip, bottom-right for comment)
2. Plan mode: Uses a plan.txt file to specify custom coordinates, width, and duration handling

Plan.txt Format (new file-based structure):
# Capital market offerings.
slide=videos/001_slide.mp4
  pip=videos/001_pip.mp4
    coords: [x, y]
    width: pixels
    duration: "fill" | "normal"
  comment=videos/001_comment.mp4
    coords: [x, y]
    width: pixels
    duration: "fill" | "normal"

Duration modes:
- "fill": Video is slowed down to match segment duration
- "normal": Video keeps original duration, last frame frozen if needed

Examples:
# Basic usage
> create_presentation_video.py --in_dir ./videos --out_file final.mp4

# With custom video settings
> create_presentation_video.py --in_dir ./videos --out_file final.mp4 --resolution 1920x1080 --quality high

# With plan file for custom positioning
> create_presentation_video.py --in_dir ./videos --out_file final.mp4 --plan plan.txt

Import as:
    import create_presentation_video as cpv
"""

import argparse
import glob
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from moviepy import (
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# OverlayConfig
# #############################################################################


# Data structures for plan configuration.
class OverlayConfig:
    """
    Configuration for pip or comment overlay.
    """

    def __init__(
        self, coords: Tuple[int, int], width: int, duration: str = "normal"
    ):
        self.coords = coords
        self.width = width
        self.duration = duration  # "fill" or "normal"


# #############################################################################
# SlideConfig
# #############################################################################


class SlideConfig:
    """
    Configuration for a single slide.
    """

    def __init__(self, slide_num: int):
        self.slide_num = slide_num
        self.slide_path: Optional[str] = None
        self.pip_path: Optional[str] = None
        self.comment_path: Optional[str] = None
        self.pip: Optional[OverlayConfig] = None
        self.comment: Optional[OverlayConfig] = None


def _parse_plan_file(plan_file_path: str) -> Dict[int, SlideConfig]:
    """
    Parse plan.txt file and return slide configurations.

    :param plan_file_path: path to plan.txt file
    :return: dictionary mapping slide numbers to SlideConfig objects
    """
    hdbg.dassert_file_exists(plan_file_path)
    slide_configs = {}
    current_slide_config = None
    current_slide_num = None
    with open(plan_file_path, "r") as file:
        lines = file.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            i += 1
            continue
        # Check if this is a slide line
        if line.startswith("slide="):
            # Save previous slide config if exists
            if current_slide_config and current_slide_num is not None:
                slide_configs[current_slide_num] = current_slide_config
            # Extract slide number from filename (e.g., "videos/001_slide.mp4" -> 1)
            slide_path = line.split("=", 1)[1]
            # Remove inline comments from path
            slide_path = slide_path.split("#")[0].strip()
            filename = os.path.basename(slide_path)
            match = re.match(r"(\d+)_slide\.mp4", filename)
            if match:
                current_slide_num = int(match.group(1))
                current_slide_config = SlideConfig(current_slide_num)
                current_slide_config.slide_path = slide_path
                _LOG.debug(f"Parsing slide {current_slide_num}: {slide_path}")
            else:
                _LOG.warning(f"Could not extract slide number from: {slide_path}")
                i += 1
                continue
        # Check if this is a pip line (handle indented lines)
        elif (
            "pip=" in line and line.lstrip().startswith("pip=")
        ) and current_slide_config:
            pip_path = line.lstrip().split("=", 1)[1]
            # Remove inline comments from path
            pip_path = pip_path.split("#")[0].strip()
            current_slide_config.pip_path = pip_path
            _LOG.debug(
                f"Found pip path for slide {current_slide_num}: {pip_path}"
            )
            # Parse pip configuration from following lines
            pip_coords = None
            pip_width = None
            pip_duration = "normal"
            i += 1
            while (
                i < len(lines)
                and lines[i].strip()
                and not lines[i]
                .strip()
                .startswith(("slide=", "pip=", "comment=", "#"))
            ):
                config_line = lines[i].strip()
                if config_line.startswith("coords:"):
                    coords_str = config_line.split(":", 1)[1].strip()
                    # Remove inline comments
                    coords_str = coords_str.split("#")[0].strip()
                    pip_coords = eval(coords_str)  # Parse [x, y] format
                elif config_line.startswith("width:"):
                    width_str = config_line.split(":", 1)[1].strip()
                    # Remove inline comments
                    width_str = width_str.split("#")[0].strip()
                    pip_width = int(width_str)
                elif config_line.startswith("duration:"):
                    duration_str = config_line.split(":", 1)[1].strip()
                    # Remove inline comments
                    duration_str = duration_str.split("#")[0].strip()
                    pip_duration = duration_str.strip('"')
                i += 1
            # Create pip overlay config
            if pip_coords is not None and pip_width is not None:
                current_slide_config.pip = OverlayConfig(
                    pip_coords, pip_width, pip_duration
                )
            i -= 1  # Adjust for the extra increment
        # Check if this is a comment line (handle indented lines)
        elif (
            "comment=" in line and line.lstrip().startswith("comment=")
        ) and current_slide_config:
            comment_path = line.lstrip().split("=", 1)[1]
            # Remove inline comments from path
            comment_path = comment_path.split("#")[0].strip()
            current_slide_config.comment_path = comment_path
            _LOG.debug(
                f"Found comment path for slide {current_slide_num}: {comment_path}"
            )
            # Parse comment configuration from following lines
            comment_coords = None
            comment_width = None
            comment_duration = "normal"
            i += 1
            while (
                i < len(lines)
                and lines[i].strip()
                and not lines[i]
                .strip()
                .startswith(("slide=", "pip=", "comment=", "#"))
            ):
                config_line = lines[i].strip()
                if config_line.startswith("coords:"):
                    coords_str = config_line.split(":", 1)[1].strip()
                    # Remove inline comments
                    coords_str = coords_str.split("#")[0].strip()
                    comment_coords = eval(coords_str)  # Parse [x, y] format
                elif config_line.startswith("width:"):
                    width_str = config_line.split(":", 1)[1].strip()
                    # Remove inline comments
                    width_str = width_str.split("#")[0].strip()
                    comment_width = int(width_str)
                elif config_line.startswith("duration:"):
                    duration_str = config_line.split(":", 1)[1].strip()
                    # Remove inline comments
                    duration_str = duration_str.split("#")[0].strip()
                    comment_duration = duration_str.strip('"')
                i += 1
            # Create comment overlay config
            if comment_coords is not None and comment_width is not None:
                current_slide_config.comment = OverlayConfig(
                    comment_coords, comment_width, comment_duration
                )
            i -= 1  # Adjust for the extra increment
        i += 1
    # Save last slide config
    if current_slide_config and current_slide_num is not None:
        slide_configs[current_slide_num] = current_slide_config
    # Debug logging and file existence validation
    for slide_num, slide_config in slide_configs.items():
        _LOG.debug(f"Slide {slide_num}: slide_path={slide_config.slide_path}")
        _LOG.debug(f"Slide {slide_num}: pip_path={slide_config.pip_path}")
        _LOG.debug(f"Slide {slide_num}: comment_path={slide_config.comment_path}")
        if slide_config.pip:
            _LOG.debug(
                f"Slide {slide_num}: pip config={slide_config.pip.coords}, {slide_config.pip.width}, {slide_config.pip.duration}"
            )
        if slide_config.comment:
            _LOG.debug(
                f"Slide {slide_num}: comment config={slide_config.comment.coords}, {slide_config.comment.width}, {slide_config.comment.duration}"
            )
    _LOG.debug(f"Parsed {len(slide_configs)} slide configurations from plan file")
    return slide_configs


def _validate_plan_files(
    slide_configs: Dict[int, SlideConfig], in_dir: str
) -> None:
    """
    Validate that all files specified in slide configurations exist.

    :param slide_configs: dictionary of slide configurations
    :param in_dir: input directory for resolving relative paths
    """
    for slide_num, slide_config in slide_configs.items():
        # Check slide file
        if slide_config.slide_path:
            slide_file = slide_config.slide_path
            if not os.path.isabs(slide_file):
                slide_file = os.path.join(in_dir, slide_file)
            hdbg.dassert_file_exists(
                slide_file, f"Slide file for slide {slide_num} not found"
            )

        # Check pip file
        if slide_config.pip_path:
            pip_file = slide_config.pip_path
            if not os.path.isabs(pip_file):
                pip_file = os.path.join(in_dir, pip_file)
            hdbg.dassert_file_exists(
                pip_file, f"Pip file for slide {slide_num} not found"
            )

        # Check comment file
        if slide_config.comment_path:
            comment_file = slide_config.comment_path
            if not os.path.isabs(comment_file):
                comment_file = os.path.join(in_dir, comment_file)
            hdbg.dassert_file_exists(
                comment_file, f"Comment file for slide {slide_num} not found"
            )


def _parse_slide_range(slide_range: str) -> List[int]:
    """
    Parse slide range specification into list of slide numbers.

    :param slide_range: range specification like "001-003", "001,005",
        "001-003,005-007"
    :return: list of slide numbers
    """
    slide_numbers = []
    # Split by comma for multiple ranges
    parts = slide_range.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            # Range format: 001-003
            start, end = part.split("-")
            start_num = int(start)
            end_num = int(end)
            slide_numbers.extend(range(start_num, end_num + 1))
        else:
            # Single slide: 001
            slide_numbers.append(int(part))
    return sorted(list(set(slide_numbers)))


def _discover_slide_files(
    in_dir: str,
    slide_range: Optional[str] = None,
    slide_configs: Optional[Dict[int, SlideConfig]] = None,
) -> List[Tuple[int, str]]:
    """
    Discover XXX_slide.mp4 files in the directory, optionally filtered by range
    or plan.

    :param in_dir: input directory to search
    :param slide_range: optional range specification like "001-003"
    :param slide_configs: optional slide configurations from plan file
    :return: list of (slide_number, file_path) tuples sorted by slide
        number
    """
    hdbg.dassert_dir_exists(in_dir)
    # If slide_configs provided, prioritize plan-based discovery.
    if slide_configs:
        _LOG.debug(
            f"Using plan-based slide discovery for {len(slide_configs)} slides"
        )
        slides = []
        for slide_num in sorted(slide_configs.keys()):
            slide_config = slide_configs[slide_num]
            if slide_config.slide_path:
                # Use slide path from plan file
                slide_file = slide_config.slide_path
                if not os.path.isabs(slide_file):
                    slide_file = os.path.join(in_dir, slide_file)
                if os.path.exists(slide_file):
                    slides.append((slide_num, slide_file))
                else:
                    _LOG.warning(
                        f"Slide file not found for plan entry: {slide_file}"
                    )
            else:
                # Fallback to default naming
                slide_file = os.path.join(in_dir, f"{slide_num:03d}_slide.mp4")
                if os.path.exists(slide_file):
                    slides.append((slide_num, slide_file))
                else:
                    _LOG.warning(
                        f"Slide file not found for plan entry: {slide_num:03d}_slide.mp4"
                    )
    elif slide_range:
        # Parse requested slide numbers
        requested_slides = _parse_slide_range(slide_range)
        slides = []
        for slide_num in requested_slides:
            slide_file = os.path.join(in_dir, f"{slide_num:03d}_slide.mp4")
            if os.path.exists(slide_file):
                slides.append((slide_num, slide_file))
            else:
                _LOG.warning(f"Slide file not found: {slide_num:03d}_slide.mp4")
    else:
        # Discover all slides
        pattern = os.path.join(in_dir, "*_slide.mp4")
        slide_files = glob.glob(pattern)
        # Extract slide numbers and sort.
        slides = []
        for file_path in slide_files:
            filename = os.path.basename(file_path)
            match = re.match(r"(\d+)_slide\.mp4", filename)
            if match:
                slide_num = int(match.group(1))
                slides.append((slide_num, file_path))
        # Sort by slide number.
        slides.sort(key=lambda x: x[0])
    _LOG.debug(f"Found {len(slides)} slide files")
    return slides


def _find_companion_files(
    in_dir: str, slide_num: int, slide_config: Optional[SlideConfig] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Find pip and comment files for a given slide number.

    :param in_dir: input directory to search
    :param slide_num: slide number to find companions for
    :param slide_config: optional slide configuration with file paths
    :return: (pip_file_path, comment_file_path) tuple, None if not found
    """
    pip_path = None
    comment_path = None

    _LOG.debug(f"Looking for companions for slide {slide_num}")
    _LOG.debug(f"slide_config provided: {slide_config is not None}")

    # Use paths from slide config if available
    if slide_config:
        _LOG.debug(f"slide_config.pip_path: {slide_config.pip_path}")
        _LOG.debug(f"slide_config.comment_path: {slide_config.comment_path}")

        if slide_config.pip_path:
            pip_file = slide_config.pip_path
            if not os.path.isabs(pip_file):
                pip_file = os.path.join(in_dir, pip_file)
            _LOG.debug(f"Checking pip file: {pip_file}")
            pip_path = pip_file if os.path.exists(pip_file) else None
            _LOG.debug(f"Pip file exists: {pip_path is not None}")

        if slide_config.comment_path:
            comment_file = slide_config.comment_path
            if not os.path.isabs(comment_file):
                comment_file = os.path.join(in_dir, comment_file)
            _LOG.debug(f"Checking comment file: {comment_file}")
            comment_path = comment_file if os.path.exists(comment_file) else None
            _LOG.debug(f"Comment file exists: {comment_path is not None}")

    # Fallback to default naming if not found in config
    if pip_path is None:
        pip_file = os.path.join(in_dir, f"{slide_num:03d}_pip.mp4")
        _LOG.debug(f"Fallback pip check: {pip_file}")
        pip_path = pip_file if os.path.exists(pip_file) else None

    if comment_path is None:
        comment_file = os.path.join(in_dir, f"{slide_num:03d}_comment.mp4")
        _LOG.debug(f"Fallback comment check: {comment_file}")
        comment_path = comment_file if os.path.exists(comment_file) else None

    _LOG.debug(
        f"Final result - pip_path: {pip_path}, comment_path: {comment_path}"
    )
    return pip_path, comment_path


def _extend_video_with_freeze(
    video_clip: VideoFileClip, target_duration: float
) -> VideoFileClip:
    """
    Extend video to target duration by freezing the last frame.

    :param video_clip: video clip to extend
    :param target_duration: target duration in seconds
    :return: extended video clip
    """
    if video_clip.duration >= target_duration:
        return video_clip.with_duration(target_duration)
    # Freeze last frame for remaining duration.
    last_frame = video_clip.get_frame(video_clip.duration - 0.01)
    freeze_duration = target_duration - video_clip.duration
    freeze_clip = ImageClip(last_frame, duration=freeze_duration)
    # Concatenate original video with frozen frame.
    extended_clip = concatenate_videoclips([video_clip, freeze_clip])
    return extended_clip


def _slow_video_to_duration(
    video_clip: VideoFileClip, target_duration: float, file_path: str = "unknown"
) -> VideoFileClip:
    """
    Slow down video to match target duration.

    :param video_clip: video clip to slow down
    :param target_duration: target duration in seconds
    :param file_path: path to the video file for logging
    :return: slowed video clip
    """
    if video_clip.duration >= target_duration:
        return video_clip.with_duration(target_duration)

    # Calculate the slowdown factor for logging
    slowdown_factor = target_duration / video_clip.duration

    # Log the slowdown information.
    _LOG.info(
        f"Slowing down {file_path}: {video_clip.duration:.2f}s -> {target_duration:.2f}s (factor: {slowdown_factor:.2f}x)"
    )

    # Use MoviePy's with_speed_scaled method to properly slow down the video
    # We can specify the final_duration directly, which is more accurate
    slowed_clip = video_clip.with_speed_scaled(final_duration=target_duration)

    # Verify the actual duration after speed change
    actual_duration = slowed_clip.duration
    _LOG.info(
        f"Actual slowed duration for {file_path}: {actual_duration:.2f}s (target: {target_duration:.2f}s)"
    )

    # Verify the slowdown was successful
    if not _verify_video_slowdown(
        video_clip, slowed_clip, target_duration, file_path
    ):
        _LOG.error(f"Video slowdown verification failed for {file_path}")

    return slowed_clip


def _verify_video_slowdown(
    original_clip: VideoFileClip,
    slowed_clip: VideoFileClip,
    target_duration: float,
    file_path: str = "unknown",
) -> bool:
    """
    Verify that video has been properly slowed down.

    :param original_clip: original video clip
    :param slowed_clip: slowed video clip
    :param target_duration: expected target duration
    :param file_path: path to the video file for logging
    :return: True if slowdown was successful, False otherwise
    """
    original_duration = original_clip.duration
    actual_duration = slowed_clip.duration

    # Check if duration was actually changed
    if abs(actual_duration - original_duration) < 0.1:
        _LOG.error(
            f"Video duration was not changed for {file_path}: {original_duration:.2f}s -> {actual_duration:.2f}s"
        )
        return False

    # Check if we reached the target duration (within 0.5s tolerance)
    if abs(actual_duration - target_duration) > 0.5:
        _LOG.warning(
            f"Target duration not reached for {file_path}: got {actual_duration:.2f}s, expected {target_duration:.2f}s"
        )
        return False

    # Calculate actual speed factor
    actual_speed_factor = original_duration / actual_duration
    expected_speed_factor = original_duration / target_duration

    _LOG.info(f"Slowdown verification for {file_path}:")
    _LOG.info(f"  Original duration: {original_duration:.2f}s")
    _LOG.info(f"  Target duration: {target_duration:.2f}s")
    _LOG.info(f"  Actual duration: {actual_duration:.2f}s")
    _LOG.info(f"  Expected speed factor: {expected_speed_factor:.3f}x")
    _LOG.info(f"  Actual speed factor: {actual_speed_factor:.3f}x")

    return True


def _adjust_video_duration(
    video_clip: VideoFileClip,
    target_duration: float,
    duration_mode: str = "normal",
    file_path: str = "unknown",
) -> VideoFileClip:
    """
    Adjust video duration based on mode.

    :param video_clip: video clip to adjust
    :param target_duration: target duration in seconds
    :param duration_mode: "fill" to slow down, "normal" to freeze last
        frame
    :param file_path: path to the video file for logging
    :return: adjusted video clip
    """
    if duration_mode == "fill":
        return _slow_video_to_duration(video_clip, target_duration, file_path)
    else:
        return _extend_video_with_freeze(video_clip, target_duration)


def _create_pip_overlay(
    pip_clip: VideoFileClip,
    main_width: int,
    main_height: int,
    position: str = "center",
    pip_scale: float = 0.25,
) -> VideoFileClip:
    """
    Create PIP overlay with specified position and size.

    :param pip_clip: PIP video clip
    :param main_width: width of main video
    :param main_height: height of main video
    :param position: 'center' or 'bottom-right'
    :param pip_scale: scale factor for PIP size relative to main video
    :return: positioned PIP clip
    """
    # Calculate PIP dimensions.
    pip_width = int(main_width * pip_scale)
    pip_height = int(main_height * pip_scale)
    # Resize PIP clip.
    pip_clip = pip_clip.resized((pip_width, pip_height))
    # Set position.
    if position == "center":
        x_pos = (main_width - pip_width) // 2
        y_pos = (main_height - pip_height) // 2
    elif position == "bottom-right":
        margin = 20
        x_pos = main_width - pip_width - margin
        y_pos = main_height - pip_height - margin
    else:
        # Default to center.
        x_pos = (main_width - pip_width) // 2
        y_pos = (main_height - pip_height) // 2
    # Position the clip.
    pip_clip = pip_clip.with_position((x_pos, y_pos))
    return pip_clip


def _create_custom_overlay(
    overlay_clip: VideoFileClip,
    coords: Tuple[int, int],
    width: int,
) -> VideoFileClip:
    """
    Create overlay with custom coordinates and width.

    :param overlay_clip: video clip to overlay
    :param coords: (x, y) coordinates for positioning
    :param width: target width in pixels
    :return: positioned overlay clip
    """
    # Calculate height maintaining aspect ratio.
    aspect_ratio = overlay_clip.h / overlay_clip.w
    height = int(width * aspect_ratio)
    # Resize clip to specified dimensions.
    overlay_clip = overlay_clip.resized((width, height))
    # Position the clip.
    x_pos, y_pos = coords
    overlay_clip = overlay_clip.with_position((x_pos, y_pos))
    return overlay_clip


def _get_video_duration(video_path: str) -> float:
    """
    Get duration of a video file in seconds.

    :param video_path: path to video file
    :return: duration in seconds
    """
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        _LOG.warning(f"Could not get duration for {video_path}: {e}")
        return 0.0


def _print_processing_plan(
    slides: List[Tuple[int, str]],
    in_dir: str,
    slide_configs: Optional[Dict[int, SlideConfig]] = None,
) -> None:
    """
    Print detailed plan of videos to process with durations.

    :param slides: list of (slide_number, slide_path) tuples
    :param in_dir: input directory
    :param slide_configs: optional slide configurations from plan file
    """
    _LOG.info("Processing Plan:")
    _LOG.info("=================")
    for slide_num, slide_path in slides:
        # Get slide duration
        slide_duration = _get_video_duration(slide_path)
        _LOG.info(f"{slide_num:03d}_slide.mp4 ({slide_duration:.1f}s)")
        # Get slide config if available
        slide_config = slide_configs.get(slide_num) if slide_configs else None
        # Check for pip file
        pip_path, comment_path = _find_companion_files(
            in_dir, slide_num, slide_config
        )
        if pip_path:
            pip_duration = _get_video_duration(pip_path)
            _LOG.info(f"- pip present ({pip_duration:.1f}s)")
        else:
            _LOG.info("- pip missing")
        # Check for comment file
        if comment_path:
            comment_duration = _get_video_duration(comment_path)
            _LOG.info(f"- comment present ({comment_duration:.1f}s)")
        else:
            _LOG.info("- comment missing")
        _LOG.info("")


def _create_slide_segment(
    slide_path: str,
    pip_path: Optional[str],
    comment_path: Optional[str],
    *,
    pip_scale: float = 0.25,
    slide_config: Optional[SlideConfig] = None,
) -> Tuple[VideoFileClip, float]:
    """
    Create a composite video segment for one slide.

    :param slide_path: path to main slide video
    :param pip_path: path to pip video (optional)
    :param comment_path: path to comment video (optional)
    :param pip_scale: scale factor for PIP overlays (used when no
        slide_config)
    :param slide_config: configuration from plan.txt file (optional)
    :return: tuple of (composite video clip, final duration)
    """
    # Load main slide video.
    main_clip = VideoFileClip(slide_path)
    clips = [main_clip]
    # Determine target duration.
    durations = [main_clip.duration]
    pip_clip = None
    comment_clip = None
    # Load optional clips.
    if pip_path:
        pip_clip = VideoFileClip(pip_path)
        durations.append(pip_clip.duration)
    if comment_path:
        comment_clip = VideoFileClip(comment_path)
        durations.append(comment_clip.duration)
    # Segment duration is the longest duration between pip and comment movies.
    target_duration = max(durations)
    # Report which video is the longest (main_clip, pip_clip, comment_clip).
    _LOG.info(f"Longest video: {max(durations)}s")
    _LOG.info(f"Main clip: {main_clip.duration}s")
    if pip_clip:
        _LOG.info(f"PIP clip: {pip_clip.duration}s")
    if comment_clip:
        _LOG.info(f"Comment clip: {comment_clip.duration}s")
    # Extend main clip to target duration.
    main_clip = _extend_video_with_freeze(main_clip, target_duration)
    clips[0] = main_clip
    # Add PIP overlay.
    if pip_clip:
        if slide_config and slide_config.pip:
            # Use plan configuration.
            pip_duration_mode = slide_config.pip.duration
            pip_clip = _adjust_video_duration(
                pip_clip, target_duration, pip_duration_mode, pip_path
            )
            pip_overlay = _create_custom_overlay(
                pip_clip, slide_config.pip.coords, slide_config.pip.width
            )
        else:
            # Use default behavior.
            pip_clip = _extend_video_with_freeze(pip_clip, target_duration)
            pip_overlay = _create_pip_overlay(
                pip_clip, main_clip.w, main_clip.h, "center", pip_scale
            )
        clips.append(pip_overlay)
    # Add comment overlay.
    if comment_clip:
        if slide_config and slide_config.comment:
            # Use plan configuration.
            comment_duration_mode = slide_config.comment.duration
            comment_clip = _adjust_video_duration(
                comment_clip, target_duration, comment_duration_mode, comment_path
            )
            comment_overlay = _create_custom_overlay(
                comment_clip,
                slide_config.comment.coords,
                slide_config.comment.width,
            )
        else:
            # Use default behavior.
            comment_clip = _extend_video_with_freeze(
                comment_clip, target_duration
            )
            comment_overlay = _create_pip_overlay(
                comment_clip, main_clip.w, main_clip.h, "bottom-right", pip_scale
            )
        clips.append(comment_overlay)
    # Print the duration of each clip.
    _LOG.info(f"Clips: {clips}")
    for clip in clips:
        _LOG.info(f"Clip: {clip.duration}s")
    # Create composite.
    if len(clips) == 1:
        return clips[0], target_duration
    else:
        return CompositeVideoClip(clips), target_duration


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--in_dir",
        help="Input directory containing XXX_slide.mp4, XXX_pip.mp4, and XXX_comment.mp4 files (default: current directory)",
    )
    parser.add_argument(
        "--out_file",
        required=True,
        help="Output video file path",
    )
    parser.add_argument(
        "--resolution",
        default="1920x1080",
        help="Output video resolution (default: 1920x1080)",
    )
    parser.add_argument(
        "--quality",
        choices=["low", "medium", "high"],
        default="medium",
        help="Output video quality (default: medium)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Output video frame rate (default: 24)",
    )
    parser.add_argument(
        "--pip_scale",
        type=float,
        default=0.25,
        help="Scale factor for PIP overlays relative to main video (default: 0.25)",
    )
    parser.add_argument(
        "--slides",
        help="Range of slides to process (e.g., '001-003', '001,005', '001-003,007-009')",
    )
    parser.add_argument(
        "--plan",
        help="Path to plan.txt file specifying custom positioning and sizing for overlays",
    )
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to create the presentation video.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Set input directory.
    in_dir = args.in_dir if args.in_dir else "."
    hdbg.dassert_dir_exists(in_dir)
    # Validate output file extension.
    out_file = args.out_file
    hdbg.dassert(
        out_file.lower().endswith(".mp4"),
        f"Output file must have .mp4 extension: {out_file}",
    )
    # Parse resolution.
    try:
        width, height = map(int, args.resolution.split("x"))
    except ValueError:
        hdbg.dfatal(
            f"Invalid resolution format: {args.resolution}. Use WIDTHxHEIGHT format"
        )
    # Ensure output directory exists.
    output_dir = os.path.dirname(out_file)
    if output_dir:
        hio.create_dir(output_dir, incremental=True)
    _LOG.info(f"Input directory: {in_dir}")
    _LOG.info(f"Output file: {out_file}")
    _LOG.info(f"Resolution: {width}x{height}")
    _LOG.info(f"Quality: {args.quality}")
    _LOG.info(f"FPS: {args.fps}")
    _LOG.info(f"PIP scale: {args.pip_scale}")
    # Parse plan file if provided.
    slide_configs = {}
    if args.plan:
        _LOG.info(f"Plan file: {args.plan}")
        slide_configs = _parse_plan_file(args.plan)
        # Validate that all files specified in plan exist
        _validate_plan_files(slide_configs, in_dir)
    # Discover slide files.
    slides = _discover_slide_files(
        in_dir, args.slides, slide_configs if slide_configs else None
    )
    if not slides:
        if args.plan:
            hdbg.dfatal(
                f"No matching slide files found for plan entries in: {args.plan}"
            )
        elif args.slides:
            hdbg.dfatal(f"No matching slide files found for range: {args.slides}")
        else:
            hdbg.dfatal(f"No XXX_slide.mp4 files found in directory: {in_dir}")
    _LOG.info(f"Found {len(slides)} slides to process")
    # Print processing plan.
    _print_processing_plan(
        slides, in_dir, slide_configs if slide_configs else None
    )
    # Create video segments for each slide.
    video_segments = []
    for slide_num, slide_path in slides:
        _LOG.info(
            f"Processing slide {slide_num:03d}: {os.path.basename(slide_path)}"
        )
        # Get slide configuration if available.
        slide_config = slide_configs.get(slide_num) if slide_configs else None
        # Find companion files.
        pip_path, comment_path = _find_companion_files(
            in_dir, slide_num, slide_config
        )
        if pip_path:
            _LOG.debug(f"  Found PIP: {os.path.basename(pip_path)}")
        if comment_path:
            _LOG.debug(f"  Found comment: {os.path.basename(comment_path)}")
        # Create composite segment.
        segment, segment_duration = _create_slide_segment(
            slide_path,
            pip_path,
            comment_path,
            pip_scale=args.pip_scale,
            slide_config=slide_config,
        )
        video_segments.append(segment)
        # Report segment duration.
        _LOG.info(f"{slide_num:03d}_slide.mp4 output ({segment_duration:.1f}s)")
    # Concatenate all segments.
    _LOG.info("Concatenating video segments...")
    final_video = concatenate_videoclips(video_segments)
    # Resize to target resolution if needed.
    if final_video.w != width or final_video.h != height:
        _LOG.info(
            f"Resizing video from {final_video.w}x{final_video.h} to {width}x{height}"
        )
        final_video = final_video.resized((width, height))
    # Determine quality settings.
    quality_settings = {
        "low": {"bitrate": "1000k"},
        "medium": {"bitrate": "2000k"},
        "high": {"bitrate": "4000k"},
    }
    bitrate = quality_settings[args.quality]["bitrate"]
    # Write final video.
    _LOG.info(f"Writing final video to: {out_file}")
    final_video.write_videofile(
        out_file,
        fps=args.fps,
        codec="libx264",
        audio_codec="aac",
        bitrate=bitrate,
    )
    # Clean up.
    final_video.close()
    for segment in video_segments:
        segment.close()
    _LOG.info(f"Video creation completed: {out_file}")
    # Log final statistics.
    total_duration = sum(segment.duration for segment in video_segments)
    _LOG.info(
        f"Final video: {len(slides)} slides, {total_duration:.1f} seconds total"
    )


def test_video_slowdown(video_path: str, target_duration: float) -> None:
    """
    Test function to verify video slowdown functionality.

    :param video_path: path to the video file to test
    :param target_duration: target duration in seconds
    """
    _LOG.info(f"Testing video slowdown for: {video_path}")
    _LOG.info(f"Target duration: {target_duration:.2f}s")
    # Load the video
    original_clip = VideoFileClip(video_path)
    _LOG.info(f"Original duration: {original_clip.duration:.2f}s")
    # Test the slowdown
    slowed_clip = _slow_video_to_duration(
        original_clip, target_duration, video_path
    )
    # Verify the result
    success = _verify_video_slowdown(
        original_clip, slowed_clip, target_duration, video_path
    )
    if success:
        _LOG.info("✅ Video slowdown test PASSED")
    else:
        _LOG.error("❌ Video slowdown test FAILED")
    # Clean up
    original_clip.close()
    slowed_clip.close()


def main():
    """
    Main entry point.
    """
    _main(_parse())


if __name__ == "__main__":
    main()
