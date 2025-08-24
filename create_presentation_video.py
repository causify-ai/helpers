#!/usr/bin/env python3

"""
Create a composite presentation video from slide MP4 files with PIP overlays.

This script processes MP4 files in a directory to create a concatenated video
with picture-in-picture overlays. For each slide_XYZ.mp4 file, it can include:
- pip_XYZ.mp4 as a centered PIP overlay
- comment_XYZ.mp4 as a bottom-right PIP overlay

Examples:
# Basic usage
> create_presentation_video.py --in_dir ./videos --out_file final.mp4
    
# With custom video settings
> create_presentation_video.py --in_dir ./videos --out_file final.mp4 --resolution 1920x1080 --quality high

Import as:
    import create_presentation_video as cpv
"""

import argparse
import glob
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from moviepy import CompositeVideoClip, VideoFileClip, concatenate_videoclips

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse_slide_range(slide_range: str) -> List[int]:
    """
    Parse slide range specification into list of slide numbers.
    
    :param slide_range: range specification like "001-003", "001,005", "001-003,005-007"
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
    in_dir: str, slide_range: Optional[str] = None
) -> List[Tuple[int, str]]:
    """
    Discover slide_*.mp4 files in the directory, optionally filtered by range.
    
    :param in_dir: input directory to search
    :param slide_range: optional range specification like "001-003"
    :return: list of (slide_number, file_path) tuples sorted by slide number
    """
    hdbg.dassert_dir_exists(in_dir)
    if slide_range:
        # Parse requested slide numbers
        requested_slides = _parse_slide_range(slide_range)
        slides = []
        for slide_num in requested_slides:
            slide_file = os.path.join(in_dir, f"slide_{slide_num:03d}.mp4")
            if os.path.exists(slide_file):
                slides.append((slide_num, slide_file))
            else:
                _LOG.warning(f"Slide file not found: slide_{slide_num:03d}.mp4")
    else:
        # Discover all slides
        pattern = os.path.join(in_dir, "slide_*.mp4")
        slide_files = glob.glob(pattern)
        # Extract slide numbers and sort.
        slides = []
        for file_path in slide_files:
            filename = os.path.basename(file_path)
            match = re.match(r"slide_(\d+)\.mp4", filename)
            if match:
                slide_num = int(match.group(1))
                slides.append((slide_num, file_path))
        # Sort by slide number.
        slides.sort(key=lambda x: x[0])
    _LOG.debug(f"Found {len(slides)} slide files")
    return slides


def _find_companion_files(
    in_dir: str, slide_num: int
) -> Tuple[Optional[str], Optional[str]]:
    """
    Find pip and comment files for a given slide number.
    
    :param in_dir: input directory to search
    :param slide_num: slide number to find companions for
    :return: (pip_file_path, comment_file_path) tuple, None if not found
    """
    pip_file = os.path.join(in_dir, f"pip_{slide_num:03d}.mp4")
    comment_file = os.path.join(in_dir, f"comment_{slide_num:03d}.mp4")
    # Check if files exist.
    pip_path = pip_file if os.path.exists(pip_file) else None
    comment_path = comment_file if os.path.exists(comment_file) else None
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
    from moviepy import ImageClip
    last_frame = video_clip.get_frame(video_clip.duration - 0.01)
    freeze_duration = target_duration - video_clip.duration
    freeze_clip = ImageClip(last_frame, duration=freeze_duration)
    # Concatenate original video with frozen frame.
    extended_clip = concatenate_videoclips([video_clip, freeze_clip])
    return extended_clip


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
    slides: List[Tuple[int, str]], in_dir: str
) -> None:
    """
    Print detailed plan of videos to process with durations.
    
    :param slides: list of (slide_number, slide_path) tuples
    :param in_dir: input directory
    """
    _LOG.info("Processing Plan:")
    _LOG.info("=================")
    for slide_num, slide_path in slides:
        # Get slide duration
        slide_duration = _get_video_duration(slide_path)
        _LOG.info(f"slide_{slide_num:03d}.mp4 ({slide_duration:.1f}s)")
        # Check for pip file
        pip_path, comment_path = _find_companion_files(in_dir, slide_num)
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
) -> Tuple[VideoFileClip, float]:
    """
    Create a composite video segment for one slide.
    
    :param slide_path: path to main slide video
    :param pip_path: path to pip video (optional)
    :param comment_path: path to comment video (optional)
    :param pip_scale: scale factor for PIP overlays
    :return: tuple of (composite video clip, final duration)
    """
    # Load main slide video.
    main_clip = VideoFileClip(slide_path)
    clips = [main_clip]
    # Determine target duration (longest of all videos).
    target_duration = main_clip.duration
    pip_clip = None
    comment_clip = None
    # Load optional clips and find max duration.
    if pip_path:
        pip_clip = VideoFileClip(pip_path)
        target_duration = max(target_duration, pip_clip.duration)
    if comment_path:
        comment_clip = VideoFileClip(comment_path)
        target_duration = max(target_duration, comment_clip.duration)
    # Extend all clips to target duration.
    main_clip = _extend_video_with_freeze(main_clip, target_duration)
    clips[0] = main_clip
    # Add PIP overlay (center position).
    if pip_clip:
        pip_clip = _extend_video_with_freeze(pip_clip, target_duration)
        pip_overlay = _create_pip_overlay(
            pip_clip, main_clip.w, main_clip.h, "center", pip_scale
        )
        clips.append(pip_overlay)
    # Add comment overlay (bottom-right position).
    if comment_clip:
        comment_clip = _extend_video_with_freeze(comment_clip, target_duration)
        comment_overlay = _create_pip_overlay(
            comment_clip, main_clip.w, main_clip.h, "bottom-right", pip_scale
        )
        clips.append(comment_overlay)
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
        required=True,
        help="Input directory containing slide_*.mp4, pip_*.mp4, and comment_*.mp4 files",
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
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to create the presentation video.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input directory.
    in_dir = args.in_dir
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
        hdbg.dfatal(f"Invalid resolution format: {args.resolution}. Use WIDTHxHEIGHT format")
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
    # Discover slide files.
    slides = _discover_slide_files(in_dir, args.slides)
    if not slides:
        if args.slides:
            hdbg.dfatal(f"No matching slide files found for range: {args.slides}")
        else:
            hdbg.dfatal(f"No slide_*.mp4 files found in directory: {in_dir}")
    _LOG.info(f"Found {len(slides)} slides to process")
    # Print processing plan.
    _print_processing_plan(slides, in_dir)
    # Create video segments for each slide.
    video_segments = []
    for slide_num, slide_path in slides:
        _LOG.info(f"Processing slide {slide_num:03d}: {os.path.basename(slide_path)}")
        # Find companion files.
        pip_path, comment_path = _find_companion_files(in_dir, slide_num)
        if pip_path:
            _LOG.debug(f"  Found PIP: {os.path.basename(pip_path)}")
        if comment_path:
            _LOG.debug(f"  Found comment: {os.path.basename(comment_path)}")
        # Create composite segment.
        segment, segment_duration = _create_slide_segment(
            slide_path, pip_path, comment_path, pip_scale=args.pip_scale
        )
        video_segments.append(segment)
        # Report segment duration.
        _LOG.info(f"slide_{slide_num:03d}.mp4 output ({segment_duration:.1f}s)")
    # Concatenate all segments.
    _LOG.info("Concatenating video segments...")
    final_video = concatenate_videoclips(video_segments)
    # Resize to target resolution if needed.
    if final_video.w != width or final_video.h != height:
        _LOG.info(f"Resizing video from {final_video.w}x{final_video.h} to {width}x{height}")
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
    _LOG.info(f"Final video: {len(slides)} slides, {total_duration:.1f} seconds total")


def main():
    """
    Main entry point.
    """
    _main(_parse())


if __name__ == "__main__":
    main()
