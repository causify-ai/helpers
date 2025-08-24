#!/usr/bin/env python3

"""
Convert individual PNG files to separate MP4 movies using moviepy.

This script takes a directory containing PNG files and creates individual movies
from each PNG file, with each movie displaying the single image for a specified
duration.

Examples:
# Convert all PNG files in a directory to individual movies
> convert_png_to_movie.py --in_dir ./slides --duration 3.0

# Convert specific PNG files
> convert_png_to_movie.py --in_dir ./images --files "image1.png,image2.png"
"""

import argparse
import glob
import logging
import os

from moviepy import ImageClip

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _convert_png_to_movie(
    png_file: str, out_file: str, *, duration: float = 5.0
) -> None:
    """
    Convert a single PNG file to an MP4 movie.

    :param png_file: path to PNG file to convert
    :param out_file: output MP4 file path
    :param duration: duration in seconds to display the image
    """
    hdbg.dassert_file_exists(png_file)
    _LOG.debug(f"Converting PNG file {png_file} to movie {out_file}")
    # Create movie clip from single image.
    _LOG.debug(f"Creating movie with {duration} seconds duration")
    clip = ImageClip(png_file, duration=duration)
    # Ensure output directory exists.
    output_dir = os.path.dirname(out_file)
    if output_dir:
        hio.create_dir(output_dir, incremental=True)
    # Write the movie file.
    _LOG.info(f"Writing movie to: {out_file}")
    clip.write_videofile(out_file, fps=24, codec="libx264")
    _LOG.info(f"Movie created successfully: {out_file}")
    # Log movie statistics.
    _LOG.info(f"Movie statistics: {duration} seconds duration")


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
        help="Input directory containing PNG files",
    )
    parser.add_argument(
        "--out_dir",
        help="Output directory for movies (default: same as input directory)",
    )
    parser.add_argument(
        "--files",
        help="Comma-separated list of specific PNG files to convert (optional)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Duration per movie in seconds (default: 5.0)",
    )
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to convert PNG files to individual MP4 movies.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input directory.
    in_dir = args.in_dir
    hdbg.dassert_dir_exists(in_dir)
    # Determine output directory.
    out_dir = args.out_dir if args.out_dir else in_dir
    hio.create_dir(out_dir, incremental=True)
    # Find PNG files to convert.
    if args.files:
        # Convert specific files.
        file_list = [f.strip() for f in args.files.split(",")]
        png_files = [os.path.join(in_dir, f) for f in file_list]
        # Validate each file exists.
        for png_file in png_files:
            hdbg.dassert_file_exists(png_file)
    else:
        # Find all PNG files in the directory.
        pattern = os.path.join(in_dir, "*.png")
        png_files = glob.glob(pattern)
        png_files.sort()
    # Check if any PNG files were found.
    if not png_files:
        hdbg.dfatal(f"No PNG files found in directory: {in_dir}")
    _LOG.info(f"Found {len(png_files)} PNG files to convert")
    _LOG.info(f"Input directory: {in_dir}")
    _LOG.info(f"Output directory: {out_dir}")
    _LOG.info(f"Duration per movie: {args.duration} seconds")
    # Convert each PNG file to a movie.
    for png_file in png_files:
        # Generate output file name.
        png_basename = os.path.splitext(os.path.basename(png_file))[0]
        out_file = os.path.join(out_dir, f"{png_basename}.mp4")
        _LOG.info(f"Converting: {os.path.basename(png_file)} -> {os.path.basename(out_file)}")
        # Convert PNG to movie.
        _convert_png_to_movie(png_file, out_file, duration=args.duration)
    _LOG.info(f"Conversion complete! Created {len(png_files)} movies in {out_dir}")


def main():
    """
    Main entry point.
    """
    _main(_parse())


if __name__ == "__main__":
    main()
