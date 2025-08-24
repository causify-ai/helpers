#!/usr/bin/env python3

"""
Script to create a video from PDF slides and video clips with picture-in-picture.

This script:
1. Extracts the first page from presentation.pdf as an image
2. Creates a video with:
   - PDF page for 3 seconds with comment1.mp4 as picture-in-picture

Requirements:
- moviepy
- PyMuPDF (fitz) or Pillow (for PDF processing)
- Pillow (for image processing)
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from moviepy import (
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from PIL import Image
import tempfile

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


class PresentationVideoCreator:
    """Creates videos from PowerPoint presentations and video clips."""
    
    def __init__(self, presentation_path: str = "videos/presentation.pdf"):
        self.presentation_path = presentation_path
        self.temp_dir = tempfile.mkdtemp()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup_temp_files()
    
    def _cleanup_temp_files(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def extract_slides_as_images(self) -> List[str]:
        """
        Extract slides from PDF presentation as PNG images.
        
        Returns:
            List of paths to extracted slide images
        """
        hdbg.dassert_file_exists(self.presentation_path)
        
        import fitz  # PyMuPDF
        
        # Open PDF
        pdf_document = fitz.open(self.presentation_path)
        
        slide_paths = []
        num_pages = min(5, pdf_document.page_count)  # Extract up to 5 slides
        
        for page_num in range(num_pages):
            page = pdf_document[page_num]
            
            # Render page as high-resolution image
            mat = fitz.Matrix(3.0, 3.0)  # 3x resolution for high quality
            pix = page.get_pixmap(matrix=mat)
            
            # Save as PNG
            slide_path = os.path.join(self.temp_dir, f"slide_{page_num + 1}.png")
            pix.save(slide_path)
            slide_paths.append(slide_path)
        
        pdf_document.close()
        return slide_paths
            
    def create_pip_video(self, main_clip: VideoFileClip, pip_video_path: str, 
                        pip_position: Tuple[str, str] = ('right', 'bottom'),
                        pip_size: Tuple[int, int] = (320, 240)) -> CompositeVideoClip:
        """
        Create picture-in-picture video.
        
        Args:
            main_clip: Main video clip
            pip_video_path: Path to picture-in-picture video
            pip_position: Position of PiP ('left'/'right', 'top'/'bottom')  
            pip_size: Size of PiP video (width, height)
            
        Returns:
            Composite video with picture-in-picture
        """
        # Load and resize PiP video
        pip_clip = VideoFileClip(pip_video_path)
        pip_clip = pip_clip.resized(pip_size)
        
        # Handle duration mismatch - use the shorter duration to avoid index errors
        target_duration = min(main_clip.duration, pip_clip.duration)
        main_clip = main_clip.with_duration(target_duration)
        pip_clip = pip_clip.with_duration(target_duration)
        
        # Position PiP video
        margin = 20
        if pip_position[0] == 'right':
            x_pos = main_clip.w - pip_size[0] - margin
        else:  # left
            x_pos = margin
            
        if pip_position[1] == 'top':
            y_pos = margin
        else:  # bottom
            y_pos = main_clip.h - pip_size[1] - margin
        
        pip_clip = pip_clip.with_position((x_pos, y_pos))
        
        # Create composite
        return CompositeVideoClip([main_clip, pip_clip])
    
    def create_slide_segment(self, slide_path: str, pip_video_path: str, duration: int = 2) -> CompositeVideoClip:
        """
        Create a slide segment with picture-in-picture.
        
        Args:
            slide_path: Path to slide image
            pip_video_path: Path to PiP video
            duration: Duration in seconds for the slide
            
        Returns:
            Composite video clip with slide and PiP
        """
        slide_clip = ImageClip(slide_path).with_duration(duration)
        return self.create_pip_video(slide_clip, pip_video_path)
    
    def create_video_segment(self, video_path: str, pip_video_path: str) -> CompositeVideoClip:
        """
        Create a video segment with picture-in-picture.
        
        Args:
            video_path: Path to main video
            pip_video_path: Path to PiP video
            
        Returns:
            Composite video clip with main video and PiP
        """
        main_clip = VideoFileClip(video_path)
        return self.create_pip_video(main_clip, pip_video_path)
    
    def create_final_video(self, output_path: str = "final_presentation_video.mp4"):
        """
        Create the final video according to specifications from instr.md.
        
        Args:
            output_path: Path for output video file
        """
        _LOG.info("Starting video creation process...")
        
        # Extract slides
        _LOG.info("Extracting slides...")
        slide_paths = self.extract_slides_as_images()
        
        if len(slide_paths) < 5:
            _LOG.error(f"Need at least 5 slides, found {len(slide_paths)}")
            return
        
        video_clips = []
        
        # Define video sequences according to instr.md
        sequences = [
            # (slide_index, slide_pip_video, main_video, main_pip_video)
            (0, "videos/comment1.mp4", "videos/Causify_Capital_Markets.mp4", "videos/comment2.mp4"),
            (1, "videos/comment3.mp4", "videos/Causify_KaizenFlow.mp4", "videos/comment2.mp4"),
            (2, "videos/comment1.mp4", "videos/Causify_Portfolio_construction.mp4", "videos/comment2.mp4"),
            (3, "videos/comment1.mp4", "videos/Causify_Trading_Strategy_Dashboard.mp4", "videos/comment2.mp4"),
            (4, "videos/comment1.mp4", "videos/Causify_Trading_Strategy_Dashboard.mp4", "videos/comment2.mp4"),
        ]
        
        # Create all video segments
        for i, (slide_idx, slide_pip, main_video, main_pip) in enumerate(sequences, 1):
            # print(f"Creating slide {i} segment...")
            # slide_segment = self.create_slide_segment(slide_paths[slide_idx], slide_pip)
            # video_clips.append(slide_segment)
            
            _LOG.debug(f"Adding main video {i} segment...")  
            video_segment = self.create_video_segment(main_video, main_pip)
            video_clips.append(video_segment)
        
        # Concatenate all clips
        _LOG.info("Concatenating video segments...")
        final_video = concatenate_videoclips(video_clips)
        
        # Write final video
        _LOG.info(f"Writing final video to {output_path}...")
        try:
            final_video.write_videofile(
                output_path,
                #fps=24,
                fps=6,
                codec='libx264',
                audio_codec='aac'
            )
        except Exception as e:
            _LOG.error(f"Error writing video with libx264/aac: {e}")
            _LOG.info("Trying with default codecs...")
            try:
                final_video.write_videofile(output_path, fps=24)
            except Exception as e2:
                _LOG.error(f"Error writing video with default codecs: {e2}")
                raise
        
        # Clean up
        final_video.close()
        for clip in video_clips:
            clip.close()
        
        _LOG.info(f"Video creation completed: {output_path}")


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Create a video from PDF slides and video clips with picture-in-picture"
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--presentation",
        default="videos/presentation.pdf",
        help="Path to PDF presentation file"
    )
    parser.add_argument(
        "--output",
        default="presentation_with_pip.mp4",
        help="Output video file path"
    )
    args = parser.parse_args()
    return args


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to create the presentation video.
    
    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    with PresentationVideoCreator(args.presentation) as creator:
        creator.create_final_video(args.output)


def main():
    """Main entry point."""
    _main(_parse())


if __name__ == "__main__":
    main()
