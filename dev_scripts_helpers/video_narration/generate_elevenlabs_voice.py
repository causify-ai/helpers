#!/usr/bin/env python3
"""
Generate ElevenLabs voice files from markdown slides.

# Generate voice files for slides:
> generate_elevenlabs_voice.py \
    --in_file slides.md \
    --out_dir output_voices \
    --limit "0:2"

Environment:
  ELEVENLABS_API_KEY  Your ElevenLabs API key.
"""

import argparse
import logging
import os
from typing import List, Optional, Tuple

import requests
import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown_slides as hmarslid
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# ElevenLabs API configuration.
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
TIMEOUT_IN_SECS = 30
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID (Rachel).


def _get_elevenlabs_api_key() -> str:
    """
    Get ElevenLabs API key from environment variable.

    :return: API key
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    hdbg.dassert(
        api_key,
        "ELEVENLABS_API_KEY environment variable not set",
    )
    return api_key


def _extract_slide_content(slide_lines: List[str]) -> str:
    """
    Extract the text content from a slide, removing the title marker.

    :param slide_lines: lines of the slide
    :return: cleaned text content for voice generation
    """
    hdbg.dassert_isinstance(slide_lines, list)
    # Remove the slide title marker and get clean text.
    content_lines = []
    for line in slide_lines:
        if line.startswith("* "):
            # Remove the slide marker and use as title.
            title = line[2:].strip()
            if title:
                content_lines.append(title)
        elif line.strip():
            # Add non-empty content lines.
            content_lines.append(line.strip())
    # Join all content with spaces.
    return " ".join(content_lines)


def _generate_voice_for_text(
    text: str,
    output_file: str,
    voice_id: str = DEFAULT_VOICE_ID,
) -> None:
    """
    Generate voice using ElevenLabs API for the given text.

    :param text: text to convert to speech
    :param output_file: path to save the generated audio file
    :param voice_id: ElevenLabs voice ID to use
    """
    hdbg.dassert_isinstance(text, str)
    hdbg.dassert_isinstance(output_file, str)
    hdbg.dassert(text.strip(), "Text cannot be empty")
    # Get API key.
    api_key = _get_elevenlabs_api_key()
    # Prepare API request.
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
        },
    }
    _LOG.debug("Making ElevenLabs API request for text: %s", text[:50])
    # Make API request.
    response = requests.post(
        url,
        json=data,
        headers=headers,
        timeout=TIMEOUT_IN_SECS,
    )
    hdbg.dassert_eq(
        response.status_code,
        200,
        "ElevenLabs API request failed with status %s: %s",
        response.status_code,
        response.text,
    )
    # Save audio content to file.
    with open(output_file, "wb") as f:
        f.write(response.content)
    _LOG.info("Generated voice file: %s", output_file)


def _process_slides(
    in_file: str,
    out_dir: str,
    limit_range: Optional[Tuple[int, int]] = None,
) -> None:
    """
    Process markdown slides and generate voice files.

    :param in_file: path to input markdown file with slides
    :param out_dir: output directory for generated voice files
    :param limit_range: optional range limiting (start, end) indices
    """
    hdbg.dassert_isinstance(in_file, str)
    hdbg.dassert_isinstance(out_dir, str)
    # Ensure output directory exists.
    hio.create_dir(out_dir, incremental=True)
    # Read input file.
    _LOG.info("Reading slides from: %s", in_file)
    content = hio.from_file(in_file)
    lines = content.splitlines()
    # Extract slides from markdown.
    header_list, _ = hmarslid.extract_slides_from_markdown(lines)
    _LOG.info("Found %s slides in input file", len(header_list))
    # Apply limit range if specified.
    slides_to_process = hparser.apply_limit_range(
        header_list,
        limit_range,
        item_name="slides",
    )
    # Process each slide.
    for i, header_info in enumerate(
        tqdm.tqdm(slides_to_process, desc="Processing slides")
    ):
        slide_number = i + 1
        slide_title = header_info.description
        slide_line_number = header_info.line_number
        _LOG.debug(
            "Processing slide %s: %s (line %s)",
            slide_number,
            slide_title,
            slide_line_number,
        )
        # Extract slide content from the original lines.
        # Find the slide content by looking from the current line to the next slide or end.
        slide_lines = []
        start_line = slide_line_number - 1  # Convert to 0-indexed.
        # Find the end of this slide (next slide or end of file).
        end_line = len(lines)
        if i + 1 < len(header_list):
            # Next slide exists.
            next_header = header_list[header_list.index(header_info) + 1]
            end_line = next_header.line_number - 1  # Convert to 0-indexed.
        # Extract slide content.
        slide_lines = lines[start_line:end_line]
        # Extract text content from slide.
        slide_text = _extract_slide_content(slide_lines)
        if not slide_text.strip():
            _LOG.warning("Slide %s has no content, skipping", slide_number)
            continue
        # Generate output filename.
        output_filename = f"slide{slide_number}.mp3"
        output_file = os.path.join(out_dir, output_filename)
        # Generate voice for this slide.
        _generate_voice_for_text(slide_text, output_file)
    _LOG.info("Completed processing %s slides", len(slides_to_process))


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--in_file",
        action="store",
        required=True,
        type=str,
        help="Input markdown file with slides",
    )
    parser.add_argument(
        "--out_dir",
        action="store",
        required=True,
        type=str,
        help="Output directory for generated voice files",
    )
    parser = hparser.add_verbosity_arg(parser)
    parser = hparser.add_limit_range_arg(parser)
    return parser.parse_args()


def _main(args: argparse.Namespace) -> None:
    """
    Main function.

    :param args: parsed arguments
    """
    hdbg.init_logger(verbosity=args.log_level)
    # Parse limit range.
    limit_range = hparser.parse_limit_range_args(args)
    # Process slides.
    _process_slides(
        args.in_file,
        args.out_dir,
        limit_range=limit_range,
    )


if __name__ == "__main__":
    _main(_parse())
