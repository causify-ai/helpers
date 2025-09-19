#!/usr/bin/env python3

"""
Generate Google Veo3 videos from storyboard text files.

This script parses a text file containing scenes with visuals and narration
descriptions, then generates videos for each scene using the Google Veo3 API.

Example usage:
> generate_videos.py --in_file storyboard.txt --out_file video.mp4
> generate_videos.py --in_file storyboard.txt --image_file reference.jpg

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
import base64
import logging
import mimetypes
import os
import pprint
import time
from typing import Dict, List, Optional

import tqdm
import google.genai as genai
import google.genai.types as genai_types

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# Scene parsing
# #############################################################################


def _parse_markdown_scenes(file_path: str) -> List[Dict[str, str]]:
    """
    Parse text file and extract scenes with visuals, narration, and file references.

    Expected format:
    ```
    # Scene Title

    Visuals=
    Multi-line visual description
    Line 2
    ...

    Narration=
    Multi-line narration text
    Line 2
    ...

    Negative_prompt=
    Multi-line negative prompt
    Line 2
    ...

    Duration_in_secs=8

    Image_file=reference_image.jpg
    ```

    :param file_path: path to the text file
    :return: list of scene dictionaries with keys (e.g., )'title', 'visuals',
        'narration')
    """
    hdbg.dassert_file_exists(file_path)
    #
    scenes = []
    current_scene = None
    current_field = None
    current_field_lines = []
    # Read file.
    content = hio.from_file(file_path)
    lines = content.splitlines(keepends=True)
    #
    for line_num, line in enumerate(lines, 1):
        _LOG.debug("Processing line %d: %s", line_num, line.strip("\n"))
        line = line.rstrip()
        # Check for scene title (header level 1).
        if line.startswith('# ') and len(line) > 2:
            # Save current field content if exists.
            if current_scene and current_field and current_field_lines:
                current_scene[current_field] = '\n'.join(current_field_lines).strip()
            # Save previous scene if exists.
            if current_scene:
                must_have_fields = ['title', 'visuals', 'narration', 'duration_in_secs', 'image_file']
                for field in must_have_fields:
                    hdbg.dassert_ne(current_scene[field], "", "Scene '%s' must have field '%s'", title, field)
                scenes.append(current_scene)
            # Start new scene.
            title = line[2:].strip()
            current_scene = {
                'title': title,
                'visuals': '',
                'narration': '',
                'negative_prompt': '',
                'duration_in_secs': '',
                'image_file': ''
            }
            current_field = None
            current_field_lines = []
        elif current_scene:
            # Check for field markers.
            if line == 'visuals=':
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                current_field = 'visuals'
                current_field_lines = []
            elif line == 'narration=':
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                current_field = 'narration'
                current_field_lines = []
            elif line == 'negative_prompt=':
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                current_field = 'negative_prompt'
                current_field_lines = []
            elif line.startswith('duration_in_secs='):
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                length = len('duration_in_secs=')
                value = line[length:].strip()
                value = int(value)
                current_scene['duration_in_secs'] = value
                current_field = None
                current_field_lines = []
            elif line.startswith('image_file='):
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                length = len('image_file=')
                current_scene['image_file'] = line[length:].strip()
                current_field = None
                current_field_lines = []
            elif current_field and line.strip():
                # Add line to current field content.
                current_field_lines.append(line)
            else:
                # Skip empty lines and lines that don't match any field.
                pass
    # Save final field content if exists.
    if current_scene and current_field and current_field_lines:
        current_scene[current_field] = '\n'.join(current_field_lines).strip()
    # Add last scene.
    if current_scene:
        scenes.append(current_scene)
    #
    _LOG.info("Parsed %d scenes from %s", len(scenes), file_path)
    _LOG.debug(hprint.frame("scenes"))
    _LOG.debug("\n%s", pprint.pformat(scenes))
    return scenes


# #############################################################################
# Video generation
# #############################################################################


def _generate_video_for_scene(
    client: genai.Client,
    scene: Dict[str, str],
    scene_index: int,
    *,
    resolution: str = "1080p",
    aspect_ratio: str = "16:9",
    default_duration_in_seconds: Optional[int] = None,
    image_file: Optional[str] = None,
    dry_run: bool = False
) -> str:
    """
    Generate a video for a single scene using Google Veo3.

    :param client: Google GenAI client
    :param scene: scene dictionary with visuals, narration, negative_prompt, duration_in_secs, file
    :param scene_index: index of the scene for output naming
    :param resolution: video resolution
    :param aspect_ratio: video aspect ratio
    :param default_duration_seconds: default duration if not specified in scene
    :param image_file: global reference image file (overrides scene-specific file)
    :param dry_run: if True, only print what would be executed
    :return: path to generated video file
    """
    _LOG.debug(hprint.func_signature_to_str())
    title = scene['title']
    visuals = scene['visuals']
    narration = scene['narration']
    negative_prompt = scene.get('negative_prompt', '').strip()
    duration_in_seconds = scene['duration_in_secs']
    if default_duration_in_seconds is not None:
        duration_in_seconds = default_duration_in_seconds
    hdbg.dassert_lte(1, duration_in_seconds)
    hdbg.dassert_lte(duration_in_seconds, 8)
    # Determine which image file to use (global overrides scene-specific).
    effective_image_file = scene["image_file"]
    # effective_image_file = image_file if image_file else scene.get('file', '').strip()
    # if effective_image_file:
    hdbg.dassert_file_exists(effective_image_file)
    #    _LOG.info("Using image file for scene '%s': %s", title, effective_image_file)
    # Construct prompt combining visuals and narration.
    prompt_parts = []
    prompt_parts.append("Style: Cartoon style playful")
    if visuals:
        prompt_parts.append(f"Visuals: {visuals}")
    if narration:
        prompt_parts.append(f"Narration: {narration}")
    hdbg.dassert(prompt_parts, "Scene '%s' has no visuals or narration", title)
    #
    prompt = ". ".join(prompt_parts)
    _LOG.info("Generating video for scene '%s' (duration: %ds): %s", title, duration_in_seconds, prompt[:100] + "..." if len(prompt) > 100 else prompt)
    # Configure video generation.
    config_kwargs = {
        'durationSeconds': duration_in_seconds,
        'resolution': resolution,
        'aspectRatio': aspect_ratio,
    }
    if negative_prompt:
        config_kwargs['negativePrompt'] = negative_prompt
        _LOG.debug("Using negative prompt for scene '%s': %s", title, negative_prompt)
    config = genai_types.GenerateVideosConfig(**config_kwargs)
    # Create output filename.
    output_filename = f"scene_{scene_index:03d}_{title.replace(' ', '_').replace('/', '_')}.mp4"
    _LOG.info("output filename='%s", output_filename)
    # Start video generation operation.
    _LOG.info("Create video with parameters:\n%s",
                  pprint.pformat(config_kwargs))
    generate_videos_kwargs = {
        "model": "veo-3.0-generate-001",
        "prompt": prompt,
        "config": config
    }
    _LOG.info("generate_videos_kwargs=\n%s",
                pprint.pformat(generate_videos_kwargs))
    if dry_run:
        _LOG.warning("DRY RUN: Skipping")
        return output_filename
    # Add image if available.
    if effective_image_file:
        # Read and encode image as base64
        with open(effective_image_file, 'rb') as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        # Determine mime type.
        mime_type, _ = mimetypes.guess_type(effective_image_file)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'  # Default fallback
        # Format image object for API.
        image_obj = {
            "imageBytes": image_base64,
            "mimeType": mime_type
        }
        generate_videos_kwargs["image"] = image_obj
        _LOG.info("Added image to video generation: %s (mime_type: %s)", effective_image_file, mime_type)
    #
    operation = client.models.generate_videos(**generate_videos_kwargs)
    operation_name = operation.name
    _LOG.info("Started operation '%s' for scene '%s'", operation_name, title)
    # Poll until completion.
    iters = 0
    period_in_secs = 5
    while not operation.done:
        _LOG.debug("Waiting for video generation to complete for scene '%s'", title)
        time.sleep(period_in_secs)
        iters += 1
        _LOG.info("Elapsed time: %d seconds", iters * period_in_secs)
        operation = client.operations.get(operation)
    # Download and save the generated video.
    if operation.response and operation.response.generated_videos:
        generated_video = operation.response.generated_videos[0]
        client.files.download(file=generated_video.video)
        # Save with scene-specific filename.
        generated_video.video.save(output_filename)
        _LOG.info("Video saved as '%s'", output_filename)
        return output_filename
    raise ValueError("No video generated for scene %d:'%s'", scene_index, title)


def _generate_videos_from_scenes(
    client: genai.Client,
    scenes: List[Dict[str, str]],
    low_res: bool,
    dry_run: bool,
    *,
    image_file: Optional[str] = None
) -> List[str]:
    """
    Generate videos for all scenes.

    :param client: Google GenAI client
    :param scenes: list of scene dictionaries
    :param low_res: whether to use low resolution settings for faster rendering
    :param dry_run: if True, only print what would be executed
    :param image_file: global reference image file to use for all scenes
    :return: list of generated video file paths
    """
    generated_files = []
    # Use progress bar for multiple scenes.
    for i, scene in enumerate(tqdm.tqdm(scenes, desc="Generating videos")):
        if low_res:
            output_file = _generate_video_for_scene(
                client,
                scene,
                i + 1,
                resolution="720p",
                default_duration_in_seconds=8,
                image_file=image_file,
                #seed=42,
                dry_run=dry_run
            )
        else:
            output_file = _generate_video_for_scene(
                client,
                scene,
                i + 1,
                image_file=image_file,
                dry_run=dry_run
            )
        #
        generated_files.append(output_file)
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
        help="Input text file containing scenes"
    )
    parser.add_argument(
        "--out_file",
        help="Output file prefix (individual scene files will be generated)"
    )
    parser.add_argument(
        "--low_res",
        action="store_true",
        help="Use low resolution settings for faster rendering (480p, 4s duration, seed=42)"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print what will be executed without calling Google Veo3 API"
    )
    # TODO(ai): Do not use this image but use the first image.
    parser.add_argument(
        "--image_file",
        help="Global image file to use as reference for all scenes (overrides scene-specific File= entries)"
    )
    hparser.add_verbosity_arg(parser)
    hparser.add_limit_range_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to generate videos from storyboard.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    hdbg.dassert_file_exists(args.in_file)
    if args.image_file:
        hdbg.dassert_file_exists(args.image_file)
    # Validate API key.
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    hdbg.dassert(api_key, "Environment variable GOOGLE_GENAI_API_KEY is not set")
    # Initialize client.
    client = genai.Client(api_key=api_key)
    # Test connection and Veo access.
    _LOG.info("Testing API connection...")
    client.models.generate_content(model="gemini-1.5-flash", contents="ping")
    _LOG.info("API connection successful")
    # Get Veo model.
    #model = client.models.get(model="veo-3.0-generate-001")
    model = client.models.get(model="veo-3.0-fast-generate-preview")
    # veo-3.0-fast-generate-001
    # veo-3.0-generate-preview
    # veo-3.0-fast-generate-preview
    _LOG.info("Veo model access confirmed: %s", model.name)
    # Parse scenes from markdown.
    scenes = _parse_markdown_scenes(args.in_file)
    hdbg.dassert_lt(0, len(scenes), "No scenes found in input file: %s", args.in_file)
    # Parse limit range from command line arguments.
    limit_range = hparser.parse_limit_range_args(args)
    # Apply limit range filtering to discovered scenes.
    scenes = hparser.apply_limit_range(scenes, limit_range, item_name="scenes")
    # Generate videos for all scenes.
    generated_files = _generate_videos_from_scenes(
        client,
        scenes,
        args.low_res,
        args.dry_run,
        image_file=args.image_file
    )
    #
    _LOG.info("Generated %d videos out of %d scenes", len(generated_files), len(scenes))
    for file_path in generated_files:
        _LOG.info("Generated: %s", file_path)


if __name__ == "__main__":
    _main(_parse())
