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

    NegativePrompt=
    Multi-line negative prompt
    Line 2
    ...

    Duration_in_secs=8

    File=reference_image.jpg
    ```

    :param file_path: path to the text file
    :return: list of scene dictionaries with keys: 'title', 'visuals', 'narration', 'negative_prompt', 'duration_in_secs', 'file'
    """
    hio.dassert_file_exists(file_path)
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
        _LOG.debug("Processing line %d: %s", line_num, line)
        line = line.rstrip()
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
    default_duration_seconds: int = 8,
    seed: Optional[int] = None,
    sample_count: int = 1
) -> str:
    """
    Generate a video for a single scene using Google Veo3.

    :param client: Google GenAI client
    :param scene: scene dictionary with visuals, narration, negative_prompt, duration_in_secs, file
    :param scene_index: index of the scene for output naming
    :param image_file: reference image file
    :param resolution: video resolution
    :param aspect_ratio: video aspect ratio
    :param default_duration_seconds: default duration if not specified in scene
    :param seed: seed for deterministic output
    :param sample_count: number of samples to generate
    :return: path to generated video file
    """
    title = scene['title']
    visuals = scene['visuals']
    narration = scene['narration']
    negative_prompt = scene.get('negative_prompt', '').strip()
    duration_seconds = scene['duration_in_secs']
    if default_duration_seconds is not None:
        duration_seconds = default_duration_seconds
    # Construct prompt combining visuals and narration.
    prompt_parts = []
    if visuals:
        prompt_parts.append(f"Visuals: {visuals}")
    if narration:
        prompt_parts.append(f"Narration: {narration}")
    hdbg.dassert(prompt_parts, "Scene '%s' has no visuals or narration", title)
    #
    prompt = ". ".join(prompt_parts)
    _LOG.info("Generating video for scene '%s' (duration: %ds): %s", title, duration_seconds, prompt[:100] + "..." if len(prompt) > 100 else prompt)
    # Configure video generation.
    config_kwargs = {
        'durationSeconds': duration_seconds,
        'resolution': resolution,
        'aspectRatio': aspect_ratio,
        'sampleCount': sample_count,
    }
    if negative_prompt:
        config_kwargs['negativePrompt'] = negative_prompt
        _LOG.debug("Using negative prompt for scene '%s': %s", title, negative_prompt)
    if seed is not None:
        config_kwargs['seed'] = seed
        _LOG.debug("Using seed %d for scene '%s'", seed, title)
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
    _LOG.info("Would save video as %s (generation currently disabled)", output_filename)
    return output_filename


def _generate_videos_from_scenes(
    client: genai.Client,
    scenes: List[Dict[str, str]],
    *,
    # TODO(ai): Make this mandatory.
    low_res: bool = False
) -> List[str]:
    """
    Generate videos for all scenes.

    :param client: Google GenAI client
    :param scenes: list of scene dictionaries
    :param low_res: whether to use low resolution settings for faster rendering
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
                resolution="480p",
                default_duration_seconds=4,
                seed=42,
                sample_count=1
            )
        else:
            output_file = _generate_video_for_scene(
                client,
                scene,
                i + 1,
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
    hdbg.dassert_lt(0, len(scenes), "No scenes found in input file: %s", args.in_file)
    # Generate videos for all scenes.
    generated_files = _generate_videos_from_scenes(
        client,
        scenes,
        low_res=args.low_res
    )
    #
    _LOG.info("Generated %d videos out of %d scenes", len(generated_files), len(scenes))
    for file_path in generated_files:
        _LOG.info("Generated: %s", file_path)


if __name__ == "__main__":
    _main(_parse())
