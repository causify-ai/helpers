#!/usr/bin/env python3

import argparse
import glob
import logging
import os
import sys
from pathlib import Path

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

from moviepy import ImageSequenceClip

_LOG = logging.getLogger(__name__)


# TODO(ai): Make it private.
def convert_png_to_movie(in_dir: str, out_file: str, duration_per_slide: float = 5.0) -> None:
    """
    Convert PNG slides to MP4 movie.
    
    :param in_dir: directory containing PNG slides in format slide_*.png
    :param out_file: output MP4 file path
    :param duration_per_slide: duration in seconds for each slide
    """
    hdbg.dassert_dir_exists(in_dir)
    _LOG.debug(f"Converting PNG slides from {in_dir} to movie {out_file}")
    # Find all PNG slide files in the input directory.
    pattern = os.path.join(in_dir, "slide_*.png")
    slide_files = glob.glob(pattern)
    # Sort files to ensure proper order.
    slide_files.sort()
    if not slide_files:
        hdbg.dfatal(f"No slide files found matching pattern: {pattern}")
    _LOG.info(f"Found {len(slide_files)} slide files")
    # Log the first few and last few files for verification.
    for i, slide_file in enumerate(slide_files[:3]):
        _LOG.debug(f"Slide {i+1}: {os.path.basename(slide_file)}")
    if len(slide_files) > 6:
        _LOG.debug("...")
        for i, slide_file in enumerate(slide_files[-3:], len(slide_files)-2):
            _LOG.debug(f"Slide {i}: {os.path.basename(slide_file)}")
    # Create movie clip from image sequence.
    _LOG.info(f"Creating movie with {duration_per_slide} seconds per slide")
    # Calculate fps based on duration per slide.
    fps = 1.0 / duration_per_slide
    clip = ImageSequenceClip(slide_files, fps=fps)
    # Ensure output directory exists.
    output_dir = os.path.dirname(out_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    # Write the movie file.
    _LOG.info(f"Writing movie to: {out_file}")
    clip.write_videofile(out_file, fps=fps, codec='libx264')
    _LOG.info(f"Movie created successfully: {out_file}")
    # Log movie statistics.
    total_duration = len(slide_files) * duration_per_slide
    _LOG.info(f"Movie statistics: {len(slide_files)} slides, {total_duration} seconds total")


def main():
    """
    Main function to convert PNG slides to MP4 movie.
    """
    # TODO(ai): Move this in a _parse() function like in the script_template.py
    # Parse command line arguments.
    parser = argparse.ArgumentParser(
        description="Convert PNG slides to MP4 movie"
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--in_dir", 
        required=True,
        help="Input directory containing slide_*.png files"
    )
    # TODO(ai): Call this out_file
    parser.add_argument(
        "--out", 
        required=True,
        help="Output MP4 file path"
    )
    parser.add_argument(
        "--duration", 
        type=float,
        default=5.0,
        help="Duration per slide in seconds (default: 5.0)"
    )
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input directory.
    in_dir = args.in_dir
    hdbg.dassert_dir_exists(in_dir)
    # Validate output file extension.
    out_file = args.out
    # TODO(ai): Turn it into an assertion hdbg.dassert
    if not out_file.lower().endswith('.mp4'):
        _LOG.warning(f"Output file does not have .mp4 extension: {out_file}")
    _LOG.info(f"Converting slides from directory: {in_dir}")
    _LOG.info(f"Output movie file: {out_file}")
    _LOG.info(f"Duration per slide: {args.duration} seconds")
    # Convert PNG slides to movie.
    convert_png_to_movie(in_dir, out_file, args.duration)
    _LOG.info("Conversion complete!")


if __name__ == "__main__":
    main()