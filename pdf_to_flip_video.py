#!/usr/bin/env python3
"""
pdf_to_flip_video.py  (MoviePy 2.1.2 compatible)
------------------------------------------------
Create a movie from a PDF that looks like turning pages.

Requirements (macOS):
1) Homebrew tools:
   - brew install poppler
   - (optional) brew install ffmpeg   # system ffmpeg is faster; MoviePy can download one too.

2) Python packages:
   pip install pdf2image moviepy pillow

Usage:
  python pdf_to_flip_video.py /path/to/file.pdf --out out.mp4 --fps 30 --page-duration 2.0 --transition 0.5 --style crossfade
  python pdf_to_flip_video.py /path/to/file.pdf --out out.mp4 --style slide --transition 0.6

Notes:
- "crossfade" dissolves between pages (implemented with ImageSequenceClip for MoviePy 2.x).
- "slide" animates the next page sliding in from the right (book-like).
- No audio track is added.
Tested with MoviePy 2.1.2 import paths and "with_*" APIs.
"""

import argparse
import logging
import os
import sys
from typing import List, Tuple

from pdf2image import convert_from_path
from PIL import Image
import numpy as np

# MoviePy v2.x
from moviepy import ImageClip, ImageSequenceClip, CompositeVideoClip, concatenate_videoclips

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

def pdf_to_images(pdf_path: str, *, dpi: int = 200) -> List[Image.Image]:
    """Convert PDF pages to a list of PIL Images."""
    images = convert_from_path(pdf_path, dpi=dpi)
    return images

def ensure_even_dimensions(w: int, h: int) -> Tuple[int, int]:
    """Some encoders prefer even dimensions. If odd, add one pixel."""
    if w % 2 != 0: w += 1
    if h % 2 != 0: h += 1
    return w, h

def _crossfade_sequence(prev_img: Image.Image, next_img: Image.Image, dur: float, fps: int) -> ImageSequenceClip:
    """Create an ImageSequenceClip that linearly crossfades from prev_img to next_img over dur seconds."""
    base_w, base_h = prev_img.size
    # Ensure same size
    if next_img.size != (base_w, base_h):
        next_img = next_img.resize((base_w, base_h), Image.LANCZOS)

    n = max(1, int(round(dur * fps)))
    prev_arr = np.array(prev_img).astype(np.float32)
    next_arr = np.array(next_img).astype(np.float32)

    # If images are grayscale, expand to 3 channels
    if prev_arr.ndim == 2:
        prev_arr = np.stack([prev_arr]*3, axis=-1)
    if next_arr.ndim == 2:
        next_arr = np.stack([next_arr]*3, axis=-1)

    frames = []
    for i in range(n):
        a = (i + 1) / n  # 0->1
        frame = (1.0 - a) * prev_arr + a * next_arr
        frames.append(np.clip(frame, 0, 255).astype(np.uint8))

    return ImageSequenceClip(frames, fps=fps)

def _make_crossfade_video(images: List[Image.Image], page_duration: float, crossfade: float, fps: int, out_path: str):
    """Create a video with crossfade transitions between pages (MoviePy 2.x safe)."""
    if crossfade < 0:
        crossfade = 0.0
    base_w, base_h = images[0].size
    base_w, base_h = ensure_even_dimensions(base_w, base_h)

    # Normalize image sizes
    norm = []
    for img in images:
        if img.size != (base_w, base_h):
            img = img.resize((base_w, base_h), Image.LANCZOS)
        norm.append(img)

    clips = []
    # First page hold
    first = ImageClip(np.array(norm[0])).with_duration(page_duration)
    clips.append(first)

    # For each subsequent page, append transition + page hold
    for i in range(1, len(norm)):
        trans = _crossfade_sequence(norm[i-1], norm[i], crossfade, fps) if crossfade > 0 else None
        hold = ImageClip(np.array(norm[i])).with_duration(page_duration)
        if trans is not None:
            clips.extend([trans, hold])
        else:
            clips.append(hold)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(out_path, fps=fps, audio=False, codec="libx264", preset="medium")

def _slide_transition_clip(prev_img: Image.Image, next_img: Image.Image, dur: float):
    """Return a CompositeVideoClip that slides next_img from right -> left over prev_img (MoviePy 2.x API)."""
    base_w, base_h = prev_img.size
    base_w, base_h = ensure_even_dimensions(base_w, base_h)

    if next_img.size != (base_w, base_h):
        next_img = next_img.resize((base_w, base_h), Image.LANCZOS)

    prev_clip = ImageClip(np.array(prev_img)).with_duration(dur)
    next_clip = ImageClip(np.array(next_img)).with_duration(dur)

    def next_pos(t):
        x = base_w * (1 - t / dur)
        return (x, 0)

    def prev_pos(t):
        x = -base_w * 0.1 * (t / dur)
        return (x, 0)

    moving_next = next_clip.with_position(next_pos)
    sliding_prev = prev_clip.with_position(prev_pos)

    comp = CompositeVideoClip([sliding_prev, moving_next], size=(base_w, base_h)).with_duration(dur)
    return comp

def _make_slide_video(images: List[Image.Image], page_duration: float, transition: float, fps: int, out_path: str):
    """Create a video where each next page slides in from the right (book-like)."""
    base_w, base_h = images[0].size
    base_w, base_h = ensure_even_dimensions(base_w, base_h)

    # Normalize images
    norm = []
    for img in images:
        if img.size != (base_w, base_h):
            img = img.resize((base_w, base_h), Image.LANCZOS)
        norm.append(img)

    clips = []
    # First page hold
    first = ImageClip(np.array(norm[0])).with_duration(page_duration)
    clips.append(first)

    for i in range(1, len(norm)):
        hold = ImageClip(np.array(norm[i])).with_duration(page_duration)
        trans = _slide_transition_clip(norm[i-1], norm[i], transition)
        clips.extend([trans, hold])

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(out_path, fps=fps, audio=False, codec="libx264", preset="medium")

def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(description="Create a 'turning pages' video from a PDF (MoviePy 2.1.2 compatible).")
    hparser.add_verbosity_arg(parser)
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--out", default="out.mp4", help="Output video path (e.g., out.mp4)")
    parser.add_argument("--dpi", type=int, default=200, help="DPI for rasterizing PDF pages (higher = sharper, slower)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for the output video")
    parser.add_argument("--page-duration", type=float, default=2.0, help="Seconds each page is fully visible")
    parser.add_argument("--transition", type=float, default=0.6, help="Transition duration in seconds")
    parser.add_argument("--style", choices=["crossfade", "slide"], default="crossfade", help="Transition style")
    args = parser.parse_args()
    return args


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to create PDF flip video.
    
    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)

    hdbg.dassert_file_exists(args.pdf)

    images = pdf_to_images(args.pdf, dpi=args.dpi)
    hdbg.dassert(len(images) > 0, "No pages found in PDF")

    # Ensure even dimensions on the first image (others are normalized later).
    w, h = images[0].size
    w, h = ensure_even_dimensions(w, h)
    if images[0].size != (w, h):
        images[0] = images[0].resize((w, h), Image.LANCZOS)

    if args.style == "crossfade":
        _make_crossfade_video(images, page_duration=args.page_duration, crossfade=args.transition, fps=args.fps, out_path=args.out)
    else:
        _make_slide_video(images, page_duration=args.page_duration, transition=args.transition, fps=args.fps, out_path=args.out)

    _LOG.info(f"Done! Wrote: {args.out}")


def main():
    """Main entry point."""
    _main(_parse())

if __name__ == "__main__":
    main()
