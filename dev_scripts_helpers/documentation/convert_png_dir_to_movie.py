#!/usr/bin/env python

"""
Convert a directory of PNG frame images into a video (MP4) or GIF.

Usage:
# Create an MP4 video with default output file (video.mp4 in input_dir).
> convert_to_movie.py --input_dir video_frames

# Create an MP4 video from frames in a directory with custom output.
> convert_to_movie.py --input_dir video_frames --output_file output.mp4

# Create a GIF from frames in a directory.
> convert_to_movie.py --input_dir video_frames --output_file output.gif

# Specify custom frame rate (default is 2 fps).
> convert_to_movie.py --input_dir video_frames --output_file output.mp4 --fps 5
"""

import argparse
import glob
import logging
import os
from typing import List

import imageio

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# Default frames per second for video/gif creation.
_DEFAULT_FPS = 2


# #############################################################################


def _get_frame_files(input_dir: str) -> List[str]:
    """
    Get all PNG frame files from the input directory sorted by name.

    :param input_dir: path to directory containing frame images
    :return: sorted list of frame file paths
    """
    hdbg.dassert_dir_exists(input_dir)
    # Get all PNG files from the directory.
    frame_pattern = os.path.join(input_dir, "*.png")
    frame_files = glob.glob(frame_pattern)
    # Sort frame files by name to ensure correct order.
    frame_files = sorted(frame_files)
    hdbg.dassert_lte(
        1,
        len(frame_files),
        "No PNG frame files found in directory:",
        input_dir,
    )
    _LOG.info("Found %d frame files in '%s'", len(frame_files), input_dir)
    return frame_files


def _load_frames(frame_files: List[str]) -> List:
    """
    Load all frame images from file paths.

    :param frame_files: list of frame file paths
    :return: list of loaded image arrays
    """
    frames = []
    _LOG.info("Loading %d frames", len(frame_files))
    for frame_file in frame_files:
        frame = imageio.imread(frame_file)
        frames.append(frame)
    _LOG.debug("Loaded all frames successfully")
    return frames


def _create_mp4(
    frames: List,
    output_file: str,
    *,
    fps: int = _DEFAULT_FPS,
) -> None:
    """
    Create an MP4 video from frames.

    :param frames: list of frame images
    :param output_file: path to output MP4 file
    :param fps: frames per second for the video
    """
    _LOG.info("Creating MP4 video with fps=%d", fps)
    # Create the directory for the output file if it doesn't exist.
    output_dir = os.path.dirname(output_file)
    if output_dir:
        hio.create_dir(output_dir, incremental=True)
    # Save frames as MP4 using libx264 codec.
    imageio.mimsave(output_file, frames, fps=fps, codec="libx264")
    duration = len(frames) / fps
    _LOG.info("Video created successfully: '%s'", output_file)
    _LOG.info("Video duration: %.1f seconds", duration)
    _LOG.info("Frame rate: %d fps", fps)


def _create_gif(
    frames: List,
    output_file: str,
    *,
    fps: int = _DEFAULT_FPS,
) -> None:
    """
    Create a GIF from frames.

    :param frames: list of frame images
    :param output_file: path to output GIF file
    :param fps: frames per second for the GIF
    """
    _LOG.info("Creating GIF with fps=%d", fps)
    # Create the directory for the output file if it doesn't exist.
    output_dir = os.path.dirname(output_file)
    if output_dir:
        hio.create_dir(output_dir, incremental=True)
    # Calculate duration per frame in seconds.
    duration_per_frame = 1.0 / fps
    # Save frames as GIF.
    imageio.mimsave(output_file, frames, duration=duration_per_frame)
    total_duration = len(frames) / fps
    _LOG.info("GIF created successfully: '%s'", output_file)
    _LOG.info("GIF duration: %.1f seconds", total_duration)
    _LOG.info("Frame rate: %d fps", fps)


def _generate_video_url(output_file: str) -> str:
    """
    Generate URL to open the video using open_mp4.html viewer.

    :param output_file: absolute path to the output video file
    :return: URL string to open in browser
    """
    # Get the repo root directory.
    repo_root = hgit.get_client_root(super_module=True)
    # Convert output_file to absolute path.
    output_file_abs = os.path.abspath(output_file)
    # Validate that the video file exists.
    hdbg.dassert_file_exists(output_file_abs)
    # Construct path to open_mp4.html.
    html_viewer_path = os.path.join(
        repo_root,
        "helpers_root",
        "dev_scripts_helpers",
        "documentation",
        "open_mp4.html",
    )
    # Validate that the HTML viewer exists.
    hdbg.dassert_file_exists(html_viewer_path)
    # Calculate relative path from HTML viewer directory to video file.
    html_viewer_dir = os.path.dirname(html_viewer_path)
    video_rel_path = os.path.relpath(output_file_abs, html_viewer_dir)
    # Construct the file:// URL with relative video path as src parameter.
    url = f"file://{html_viewer_path}?src={video_rel_path}"
    return url


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing PNG frame files",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        required=False,
        default=None,
        help="Path to output file (either .mp4 or .gif). If not specified, uses video.mp4 in the input directory.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=_DEFAULT_FPS,
        help="Frames per second for the output video/gif (default: %(default)s)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info(hprint.func_signature_to_str())
    # Validate arguments.
    input_dir = args.input_dir
    output_file = args.output_file
    fps = args.fps
    hdbg.dassert_lte(
        1,
        fps,
        "FPS must be at least 1:",
        fps,
    )
    # If output_file is not specified, use default video.mp4 in input_dir.
    if output_file is None:
        output_file = os.path.join(input_dir, "video.mp4")
        _LOG.info("No output file specified, using default: '%s'", output_file)
    # Determine output format from file extension.
    output_ext = os.path.splitext(output_file)[1].lower()
    hdbg.dassert_in(
        output_ext,
        [".mp4", ".gif"],
        "Output file must be either .mp4 or .gif:",
        output_file,
    )
    # Get frame files from input directory.
    frame_files = _get_frame_files(input_dir)
    # Load all frames.
    frames = _load_frames(frame_files)
    # Create output based on extension.
    if output_ext == ".mp4":
        _create_mp4(frames, output_file, fps=fps)
    elif output_ext == ".gif":
        _create_gif(frames, output_file, fps=fps)
    _LOG.info("Conversion completed successfully")
    # Generate and print URL to open the video in browser.
    if output_ext == ".mp4":
        video_url = _generate_video_url(output_file)
        _LOG.info("Open video in browser: %s", video_url)


if __name__ == "__main__":
    _main(_parse())
