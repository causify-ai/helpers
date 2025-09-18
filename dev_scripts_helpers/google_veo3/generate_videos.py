#!/usr/bin/env python3

"""
Generate Google Veo3 videos from storyboard text files.

This script parses a text file containing scenes with visuals and narration
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
from pathlib import Path
from typing import Any, Dict, List, Optional

import tqdm
import google.genai as genai
import google.genai.types as genai_types

import helpers.hdbg as hdbg
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
    # Scene Title

    Visuals=
    Multi-line visual description
    Line 2
    ...

    Narration=
    Multi-line narration text
    Line 2
    ...

    NegativePrompt=
    Multi-line negative prompt
    Line 2
    ...

    Duration_in_secs=8

    File=reference_image.jpg

    :param file_path: path to the text file
    :return: list of scene dictionaries with keys: 'title', 'visuals', 'narration', 'negative_prompt', 'duration_in_secs', 'file'
    """
    hio.dassert_file_exists(file_path)
    #
    scenes = []
    current_scene = None
    current_field = None
    current_field_lines = []
    #
    content = hio.from_file(file_path)
    lines = content.splitlines(keepends=True)
    #
    for line_num, line in enumerate(lines, 1):
        _LOG.debug("Processing line %d: %s", line_num, line)
        original_line = line
        line = line.rstrip()
        #
        # Check for scene title (header level 1).
        if line.startswith('# ') and len(line) > 2:
            # Save current field content if exists.
            if current_scene and current_field and current_field_lines:
                current_scene[current_field] = '\n'.join(current_field_lines).strip()
            # Save previous scene if exists.
            if current_scene:
                scenes.append(current_scene)
            # Start new scene.
            title = line[2:].strip()
            current_scene = {
                'title': title,
                'visuals': '',
                'narration': '',
                'negative_prompt': '',
                'duration_in_secs': '',
                'file': ''
            }
            current_field = None
            current_field_lines = []
        elif current_scene:
            # Check for field markers.
            if line == 'Visuals=':
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                current_field = 'visuals'
                current_field_lines = []
            elif line == 'Narration=':
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                current_field = 'narration'
                current_field_lines = []
            elif line == 'NegativePrompt=':
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                current_field = 'negative_prompt'
                current_field_lines = []
            elif line.startswith('Duration_in_secs='):
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                value = line[17:].strip()
                value = int(value)
                current_scene['duration_in_secs'] = value
                current_field = None
                current_field_lines = []
            elif line.startswith('File='):
                # Save previous field if exists.
                if current_field and current_field_lines:
                    current_scene[current_field] = '\n'.join(current_field_lines).strip()
                current_scene['file'] = line[5:].strip()
                current_field = None
                current_field_lines = []
            elif current_field and line.strip():
                # Add line to current field content.
                current_field_lines.append(line)
            # Skip empty lines and lines that don't match any field.
    #
    # Save final field content if exists.
    if current_scene and current_field and current_field_lines:
        current_scene[current_field] = '\n'.join(current_field_lines).strip()
    # Add last scene.
    if current_scene:
        scenes.append(current_scene)
    #
    _LOG.info("Parsed %d scenes from %s", len(scenes), file_path)
    return scenes


# TODO(ai): Remove fallback_file.
def _resolve_scene_file(scene: Dict[str, Any], fallback_file: Optional[str]) -> str:
    """
    Resolve the file reference for a scene, using fallback if scene file doesn't exist.

    :param scene: scene dictionary
    :param fallback_file: fallback file path to use if scene file is missing
    :return: resolved file path or None
    """
    scene_file = scene.get('file', '').strip()
    # Check if scene has a specific file and it exists.
    if scene_file and Path(scene_file).is_file():
        return scene_file
    # Use fallback file if provided and exists.
    if fallback_file and Path(fallback_file).is_file():
        _LOG.debug("Using fallback file %s for scene '%s'", fallback_file, scene['title'])
        return fallback_file
    #
    raise ValueError(f"No valid file found for scene '{scene['title']}'")


# #############################################################################
# Video generation
# #############################################################################


def _generate_video_for_scene(
    client: genai.Client,
    scene: Dict[str, str],
    scene_index: int,
    *,
    image_file: str,
    resolution: str = "1080p",
    aspect_ratio: str = "16:9"
) -> str:
    """
    Generate a video for a single scene using Google Veo3.

    :param client: Google GenAI client
    :param scene: scene dictionary with visuals, narration, negative_prompt, duration_in_secs, file
    :param scene_index: index of the scene for output naming
    :param image_file: reference image file
    :param resolution: video resolution
    :param aspect_ratio: video aspect ratio
    :return: path to generated video file
    """
    title = scene['title']
    visuals = scene['visuals']
    narration = scene['narration']
    negative_prompt = scene.get('negative_prompt', '').strip()
    duration_seconds= scene.get('duration_in_secs', '').strip()
    #
    # Parse duration from scene.
    #
    # Construct prompt combining visuals and narration.
    prompt_parts = []
    if visuals:
        prompt_parts.append(f"Visuals: {visuals}")
    if narration:
        prompt_parts.append(f"Narration: {narration}")
    # TODO(ai): Use "%s, title" for all dassert
    hdbg.dassert(prompt_parts, f"Scene '{title}' has no visuals or narration")
    #
    prompt = ". ".join(prompt_parts)
    _LOG.info("Generating video for scene '%s' (duration: %ds): %s", title, duration_seconds, prompt[:100] + "..." if len(prompt) > 100 else prompt)
    #
    # Configure video generation.
    config_kwargs = {
        'durationSeconds': duration_seconds,
        'resolution': resolution,
        'aspectRatio': aspect_ratio,
    }
    if negative_prompt:
        config_kwargs['negativePrompt'] = negative_prompt
        _LOG.debug("Using negative prompt for scene '%s': %s", title, negative_prompt)
    #
    config = genai_types.GenerateVideosConfig(**config_kwargs)
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
    # For now, return a placeholder filename since the actual video generation is commented out
    output_filename = f"scene_{scene_index:03d}_{title.replace(' ', '_').replace('/', '_')}.mp4"
    # TODO(ai): Use %s, output_filename
    _LOG.info("Would save video as %s (generation currently disabled)", output_filename)
    return output_filename


def _generate_videos_from_scenes(
    client: genai.Client,
    scenes: List[Dict[str, str]]
) -> List[str]:
    """
    Generate videos for all scenes.

    :param client: Google GenAI client
    :param scenes: list of scene dictionaries
    :return: list of generated video file paths
    """
    generated_files = []
    # Use progress bar for multiple scenes.
    for i, scene in enumerate(tqdm.tqdm(scenes, desc="Generating videos")):
        scene_file = _resolve_scene_file(scene, None)
        #
        output_file = _generate_video_for_scene(
            client,
            scene,
            i + 1,
            image_file=scene_file
        )
        #
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
        help="Input text file containing scenes"
    )
    parser.add_argument(
        "--out_file",
        help="Output file prefix (individual scene files will be generated)"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to generate videos from storyboard.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    hio.dassert_file_exists(args.in_file)
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
    model = client.models.get(model="veo-3.0-generate-001")
    _LOG.info("Veo model access confirmed: %s", model.name)
    # Parse scenes from markdown.
    scenes = _parse_markdown_scenes(args.in_file)
    hdbg.dassert(len(scenes) > 0, "No scenes found in input file: %s", args.in_file)
    # Generate videos for all scenes.
    # TODO(ai): Add a command line option --low_res that uses the following parameters
            duration_seconds=4,      # shorter duration → faster render
        resolution="480p",       # lower resolution → faster render
        aspect_ratio="16:9",
        seed=42,                 # <— key to deterministic output
        sample_count=1,          # only 1 sample for speed
    instead of parameters for high resolution

    generated_files = _generate_videos_from_scenes(
        client,
        scenes
    )
    #
    _LOG.info("Generated %d videos out of %d scenes", len(generated_files), len(scenes))
    for file_path in generated_files:
        _LOG.info("Generated: %s", file_path)


if __name__ == "__main__":
    _main(_parse())
