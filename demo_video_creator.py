#!/usr/bin/env python3

"""
Demo script to test video creation functionality without requiring moviepy.
This creates placeholder slide images to demonstrate the slide extraction logic.
"""

import os
import tempfile
from PIL import Image, ImageDraw, ImageFont


def create_demo_slides():
    """Create demo slide images to show the concept."""
    temp_dir = tempfile.mkdtemp()
    print(f"Creating demo slides in: {temp_dir}")
    
    # Create two demo slides
    for i in [1, 2]:
        slide_path = os.path.join(temp_dir, f"slide_{i}.png")
        create_slide_image(f"Slide {i}\nPresentation Content", slide_path)
        print(f"Created: {slide_path}")
    
    return temp_dir


def create_slide_image(text: str, output_path: str):
    """Create a slide image with text."""
    width, height = 1920, 1080
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a decent font
    try:
        font = ImageFont.truetype("arial.ttf", 72)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 72)
        except:
            font = ImageFont.load_default()
    
    # Calculate text position (centered)
    lines = text.split('\n')
    line_height = 80
    total_height = len(lines) * line_height
    start_y = (height - total_height) // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = start_y + i * line_height
        draw.text((x, y), line, fill='black', font=font)
    
    # Add a border
    draw.rectangle([50, 50, width-50, height-50], outline='blue', width=5)
    
    # Add corner labels for PiP positioning
    corner_font = ImageFont.load_default()
    draw.text((60, 60), "PiP Position", fill='red', font=corner_font)
    
    # Save image
    image.save(output_path)
    print(f"Slide saved: {output_path}")


def main():
    """Demo the slide creation functionality."""
    print("=== Video Creator Demo ===")
    print("This demonstrates the slide creation part of the video script.")
    print()
    
    # Create demo slides
    temp_dir = create_demo_slides()
    
    print()
    print("Demo slides created successfully!")
    print(f"Check the images in: {temp_dir}")
    print()
    print("To run the full video script:")
    print("1. Install requirements: pip install -r requirements_video.txt")
    print("2. Run: python create_presentation_video.py")
    print()
    print("The full script will:")
    print("- Extract slides from presentation.ppt (or create placeholders)")
    print("- Create video with slide 1 (5s) + comment1.mp4 PiP") 
    print("- Add demo1.mp4 + comment2.mp4 PiP")
    print("- Add slide 2 + comment3.mp4 PiP")
    print("- Output: presentation_with_pip.mp4")


if __name__ == "__main__":
    main()