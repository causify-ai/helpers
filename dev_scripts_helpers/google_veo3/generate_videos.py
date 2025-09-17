#!/usr/bin/env python3

"""
Generate Google Veo3 videos from storyboard markdown files.

This script parses a markdown file containing scenes with visuals and narration
descriptions, then generates videos for each scene using the Google Veo3 API.

Example usage:
> generate_videos.py --in_file storyboard.txt --out_file video.mp4

Expected text format:
```
# Scene Title

Visuals=
Description of the visual scene
Line2
...
Line3

Narration=
Text that should be narrated
Line2
...
Line3

NegativePrompt=
Negative prompt for the video
Line2
...
Line3

Duration_in_secs=3

File=reference_image.jpg

# Another Scene
...
```
"""

import argparse
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import tqdm
from google import genai
from google.genai import types

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# Scene parsing
# #############################################################################


def _parse_markdown_scenes(file_path: str) -> List[Dict[str, str]]:
    """
    Parse markdown file and extract scenes with visuals, narration, and file references.

    :param file_path: path to the markdown file
    :return: list of scene dictionaries with 'title', 'visuals', 'narration', 'file' keys
    """
    # TODO(ai): Use dassert_file_exists.
    hdbg.dassert(os.path.isfile(file_path), "Markdown file does not exist:", file_path)
    #
    scenes = []
    current_scene = None
    #
    # TODO(ai): Use hio.from_file.
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # TODO(ai): Make sure that each tagged line such as visuals, narration
    # can be multiple lines
    for line in lines:
        line = line.strip()
        # Check for scene title (header level 1).
        if line.startswith('# ') and len(line) > 2:
            # Save previous scene if exists.
            if current_scene:
                scenes.append(current_scene)
            # Start new scene.
            title = line[2:].strip()
            current_scene = {
                'title': title,
                'visuals': '',
                'narration': '',
                'file': ''
            }
        elif current_scene and line.startswith('- Visuals:'):
            current_scene['visuals'] = line[10:].strip()
        elif current_scene and line.startswith('- Narration:'):
            current_scene['narration'] = line[12:].strip()
        elif current_scene and line.startswith('- File:'):
            current_scene['file'] = line[7:].strip()
    # Add last scene.
    if current_scene:
        scenes.append(current_scene)
    #
    _LOG.info("Parsed %d scenes from %s", len(scenes), file_path)
    return scenes


def _resolve_scene_file(scene: Dict[str, str], fallback_file: Optional[str]) -> Optional[str]:
    """
    Resolve the file reference for a scene, using fallback if scene file doesn't exist.

    :param scene: scene dictionary
    :param fallback_file: fallback file path to use if scene file is missing
    :return: resolved file path or None
    """
    scene_file = scene.get('file', '').strip()
    #
    # Check if scene has a specific file and it exists.
    if scene_file and os.path.isfile(scene_file):
        return scene_file
    #
    # Use fallback file if provided and exists.
    # TODO(ai): use dassert_file_exists to ensure that file exists.
    if fallback_file and os.path.isfile(fallback_file):
        _LOG.debug("Using fallback file %s for scene '%s'", fallback_file, scene['title'])
        return fallback_file
    #
    _LOG.warning("No valid file found for scene '%s'", scene['title'])
    return None


# #############################################################################
# Video generation
# #############################################################################


def _generate_video_for_scene(
    client: genai.Client,
    scene: Dict[str, str],
    scene_index: int,
    *,
    image_file: Optional[str] = None,
    duration_seconds: int = 8,
    resolution: str = "1080p",
    aspect_ratio: str = "16:9"
) -> Optional[str]:
    """
    Generate a video for a single scene using Google Veo3.

    :param client: Google GenAI client
    :param scene: scene dictionary with visuals and narration
    :param scene_index: index of the scene for output naming
    :param image_file: optional reference image file
    :param duration_seconds: video duration in seconds
    :param resolution: video resolution
    :param aspect_ratio: video aspect ratio
    :return: path to generated video file or None if failed
    """
    title = scene['title']
    visuals = scene['visuals']
    narration = scene['narration']
    #
    # Construct prompt combining visuals and narration.
    prompt_parts = []
    if visuals:
        prompt_parts.append(f"Visuals: {visuals}")
    if narration:
        prompt_parts.append(f"Narration: {narration}")
    # TODO(ai): Use assertion.
    if not prompt_parts:
        _LOG.warning("Scene '%s' has no visuals or narration, skipping", title)
        return None
    #
    prompt = ". ".join(prompt_parts)
    _LOG.info("Generating video for scene '%s': %s", title, prompt[:100] + "..." if len(prompt) > 100 else prompt)
    # Configure video generation.
    config = types.GenerateVideosConfig(
        durationSeconds=duration_seconds,
        resolution=resolution,
        aspectRatio=aspect_ratio,
        # TODO(ai): Add support for image reference if provided.
        # negativePrompt="loud music, modern buildings",
    )
    #
    # Start video generation operation.
    operation = client.models.generate_videos(
        model="veo-3.0-generate-001",
        prompt=prompt,
        config=config
    )
    #
    _LOG.info("Started operation %s for scene '%s'", operation.name, title)
    #
    # # Poll until completion.
    # while not operation.done:
    #     _LOG.debug("Waiting for video generation to complete for scene '%s'", title)
    #     time.sleep(10)
    #     operation = client.operations.get(operation.name)
    # #
    # # Download and save the generated video.
    # if operation.response and operation.response.generated_videos:
    #     generated_video = operation.response.generated_videos[0]
    #     client.files.download(file=generated_video.video)
    #     #
    #     # Save with scene-specific filename.
    #     output_filename = f"scene_{scene_index:03d}_{title.replace(' ', '_').replace('/', '_')}.mp4"
    #     generated_video.video.save(output_filename)
    #     _LOG.info("Video saved as %s", output_filename)
    #     return output_filename
    # else:
    #     _LOG.error("No video generated for scene '%s'", title)
    #     return None
        #


def _generate_videos_from_scenes(
    client: genai.Client,
    scenes: List[Dict[str, str]],
    *,
    fallback_image: Optional[str] = None,
    duration_seconds: int = 8
) -> List[str]:
    """
    Generate videos for all scenes.

    :param client: Google GenAI client
    :param scenes: list of scene dictionaries
    :param fallback_image: fallback image file for scenes without specific files
    :param duration_seconds: video duration in seconds
    :return: list of generated video file paths
    """
    generated_files = []
    #
    # Use progress bar for multiple scenes.
    for i, scene in enumerate(tqdm.tqdm(scenes, desc="Generating videos")):
        scene_file = _resolve_scene_file(scene, fallback_image)
        #
        output_file = _generate_video_for_scene(
            client,
            scene,
            i + 1,
            image_file=scene_file,
            duration_seconds=duration_seconds
        )
        #
        if output_file:
            generated_files.append(output_file)
    #
    return generated_files


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--in_file",
        required=True,
        help="Input markdown file containing scenes"
    )
    parser.add_argument(
        "--in_pic",
        help="Fallback inspiration image file for scenes without specific files"
    )
    parser.add_argument(
        "--out_file",
        help="Output file prefix (individual scene files will be generated)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=8,
        help="Video duration in seconds (default: 8)"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to generate videos from storyboard.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    #
    # Validate arguments.
    hdbg.dassert(os.path.isfile(args.in_file), "Input file does not exist:", args.in_file)
    if args.in_pic:
        hdbg.dassert(os.path.isfile(args.in_pic), "Input image file does not exist:", args.in_pic)
    #
    # Validate API key.
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    hdbg.dassert(api_key, "Environment variable GOOGLE_GENAI_API_KEY is not set")
    #
    # Initialize client.
    client = genai.Client(api_key=api_key)
    #
    # Test connection and Veo access.
    _LOG.info("Testing API connection...")
    client.models.generate_content(model="gemini-1.5-flash", contents="ping")
    _LOG.info("API connection successful")
    #
    model = client.models.get(model="veo-3.0-generate-001")
    _LOG.info("Veo model access confirmed: %s", model.name)
    #
    # Parse scenes from markdown.
    scenes = _parse_markdown_scenes(args.in_file)
    hdbg.dassert(len(scenes) > 0, "No scenes found in input file:", args.in_file)
    #
    # Generate videos for all scenes.
    generated_files = _generate_videos_from_scenes(
        client,
        scenes,
        fallback_image=args.in_pic,
        duration_seconds=args.duration
    )
    #
    _LOG.info("Generated %d videos out of %d scenes", len(generated_files), len(scenes))
    for file_path in generated_files:
        _LOG.info("Generated: %s", file_path)


if __name__ == "__main__":
    _main(_parse())