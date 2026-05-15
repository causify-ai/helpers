#!/usr/bin/env -S uv run

# /// script
# dependencies = ["piper-tts", "pygame", "pynput"]
# ///

"""
Read a markdown file and play it using Piper text-to-speech with playback controls.

Examples:
  ./piper_markdown_reader.py --input README.md
  ./piper_markdown_reader.py --input README.md --speed 1.5 --voice en_US-joe-medium
  ./piper_markdown_reader.py --input README.md --speed 0.8 --voice en_US-amy-medium
"""

import argparse
import hashlib
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_DEFAULT_SPEED = 1.0
_DEFAULT_VOICE = "en_US-joe-medium"
_DEFAULT_MAX_LENGTH = 0

# #############################################################################
# Helper functions
# #############################################################################


def _read_markdown_file(file_path: str) -> str:
    """
    Read a markdown file and extract text content.

    :param file_path: path to the markdown file
    :return: text content from the markdown file
    """
    hdbg.dassert_file_exists(file_path, "Markdown file must exist")
    with open(file_path, "r") as f:
        content = f.read()
    return content


def _split_by_first_level_bullets(text: str) -> List[str]:
    """
    Split text into sections at first-level bullet points.

    First-level bullets are lines starting with "- " or "* " at the beginning
    (not indented).

    :param text: text to split
    :return: list of text sections
    """
    _LOG.debug("Splitting text by first-level bullet points")
    lines = text.split("\n")
    sections = []
    current_section = []
    for line in lines:
        if line.startswith("- ") or line.startswith("* "):
            if current_section:
                sections.append("\n".join(current_section))
                current_section = []
            current_section.append(line)
        else:
            current_section.append(line)
    if current_section:
        sections.append("\n".join(current_section))
    _LOG.debug("Split into %d sections at first-level bullets", len(sections))
    return sections


def _chunk_text_by_length(text: str, *, max_length: int) -> List[str]:
    """
    Chunk text by maximum length, respecting sentence boundaries.

    :param text: text to chunk
    :param max_length: maximum length per chunk
    :return: list of text chunks
    """
    _LOG.debug("Length-based chunking: max_length=%d", max_length)
    if max_length <= 0:
        return [text]
    chunks = []
    current_chunk = ""
    sentences = text.split(". ")
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_length:
            if current_chunk:
                chunks.append(current_chunk + ".")
                current_chunk = ""
            while len(sentence) > max_length:
                chunks.append(sentence[:max_length])
                sentence = sentence[max_length:].strip()
            current_chunk = sentence
        elif len(current_chunk) + len(sentence) + 2 <= max_length:
            if current_chunk:
                current_chunk += ". " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                chunks.append(current_chunk + ".")
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)
    _LOG.debug("Created %d length-based chunks", len(chunks))
    return chunks


def _format_markdown(text: str) -> str:
    """
    Convert markdown formatting to spoken text format.

    :param text: markdown text with formatting
    :return: formatted text suitable for TTS
    """
    _LOG.debug("Starting markdown formatting")
    import re
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("### "):
            line = "Sub sub chapter " + line[4:].strip() + "."
        elif line.startswith("## "):
            line = "Subchapter " + line[3:].strip() + "."
        elif line.startswith("# "):
            line = "Chapter " + line[2:].strip() + "."
        elif line.startswith("- ") or line.startswith("* "):
            bullet_text = re.sub(r'^[-*]\s+', '', line)
            line = bullet_text + "."
        if line:
            lines.append(line)
    formatted = "\n".join(lines)
    _LOG.debug("Markdown formatting complete: %d characters", len(formatted))
    return formatted


def _clean_text(text: str) -> str:
    """
    Clean markdown text for TTS synthesis.

    Removes bold, italic, and other markdown formatting markers.

    :param text: raw markdown text
    :return: cleaned text suitable for TTS
    """
    _LOG.debug("Starting text cleanup")
    import re
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            line = line.lstrip("#").strip()
        line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        line = re.sub(r'__([^_]+)__', r'\1', line)
        line = re.sub(r'\*([^*]+)\*', r'\1', line)
        line = re.sub(r'_([^_]+)_', r'\1', line)
        line = re.sub(r'`([^`]+)`', r'\1', line)
        if line:
            lines.append(line)
    cleaned = "\n".join(lines)
    _LOG.debug("Text cleanup complete: %d lines, %d characters", len(lines), len(cleaned))
    return cleaned


def _get_chunk_filename(chunk: str, *, chunk_idx: int, speed: float = 1.0) -> str:
    """
    Generate output filename for a chunk based on its SHA1 hash.

    Format: tmp.piper.chunk<idx>[.speed_X.X].<sha1_hash>.wav

    :param chunk: chunk text content
    :param chunk_idx: chunk index (1-based)
    :param speed: speech speed (1.0 = no speed suffix)
    :return: filename for the chunk audio file
    """
    sha1_hash = hashlib.sha1(chunk.encode()).hexdigest()
    if speed != 1.0:
        filename = f"tmp.piper.chunk{chunk_idx}.speed_{speed:.1f}.{sha1_hash}.wav"
    else:
        filename = f"tmp.piper.chunk{chunk_idx}.{sha1_hash}.wav"
    _LOG.debug("Chunk %d hash: %s, speed: %.2f, filename: %s", chunk_idx, sha1_hash, speed, filename)
    return filename


def _get_voice_path(voice: str) -> str:
    """
    Get the full path to a voice model file.

    :param voice: voice identifier
    :return: full path to the voice model
    """
    voices_dir = os.path.expanduser("~/.local/share/piper/voices")
    voice_file = os.path.join(voices_dir, f"{voice}.onnx")
    _LOG.debug("Voice path for '%s': %s", voice, voice_file)
    return voice_file


def _generate_audio(
    text: str,
    *,
    voice: str,
    speed: float,
    output_file: str,
) -> None:
    """
    Generate audio from text using Piper TTS.

    :param text: text to synthesize
    :param voice: voice identifier
    :param speed: speech speed
    :param output_file: path to output audio file
    """
    _LOG.debug("Starting audio generation: voice=%s, speed=%.2f", voice, speed)
    voice_path = _get_voice_path(voice)
    hdbg.dassert_file_exists(voice_path, "Voice model must exist")
    _LOG.debug("Voice model found: %s", voice_path)
    cmd = [
        "piper",
        "--model",
        voice_path,
        "--output_file",
        output_file,
    ]
    _LOG.debug("Running piper command: %s", " ".join(cmd[:4]))
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _LOG.debug("Sending %d characters to piper...", len(text))
    _, stderr = process.communicate(input=text, timeout=300)
    _LOG.debug("Piper process completed with return code: %d", process.returncode)
    hdbg.dassert_eq(
        process.returncode,
        0,
        "Piper command failed: %s",
        stderr,
    )
    file_size = os.path.getsize(output_file)
    _LOG.info("Generated audio file: %s (%d bytes)", output_file, file_size)


def _apply_speed_with_ffmpeg(
    input_file: str,
    *,
    output_file: str,
    speed: float,
) -> None:
    """
    Apply speed adjustment to audio using ffmpeg atempo filter.

    :param input_file: path to input audio file
    :param output_file: path to output audio file
    :param speed: speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = 2x slower)
    """
    if speed == 1.0:
        _LOG.debug("Speed is 1.0, skipping ffmpeg adjustment")
        return
    _LOG.debug("Applying speed adjustment with ffmpeg: speed=%.2f", speed)
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-filter:a", f"atempo={speed}",
        "-acodec", "pcm_s16le",
        "-y",
        output_file,
    ]
    _LOG.debug("Running ffmpeg command: %s", " ".join(cmd))
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _, stderr = process.communicate(timeout=300)
    _LOG.debug("ffmpeg process completed with return code: %d", process.returncode)
    hdbg.dassert_eq(
        process.returncode,
        0,
        "ffmpeg speed adjustment failed: %s",
        stderr,
    )
    file_size = os.path.getsize(output_file)
    _LOG.info("Speed adjustment applied: %s at %.2fx (%d bytes)", output_file, speed, file_size)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        action="store",
        required=True,
        help="Path to markdown file to read",
    )
    parser.add_argument(
        "--speed",
        action="store",
        type=float,
        default=_DEFAULT_SPEED,
        help=f"Speech speed (default: {_DEFAULT_SPEED})",
    )
    parser.add_argument(
        "--voice",
        action="store",
        default=_DEFAULT_VOICE,
        help=f"Piper voice identifier (default: {_DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--no_play",
        action="store_true",
        help="Generate audio file without playing it",
    )
    parser.add_argument(
        "--max_length",
        action="store",
        type=int,
        default=_DEFAULT_MAX_LENGTH,
        help="Maximum text length per chunk (0 = no chunking)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _play_audio_with_controls(
    audio_files: List[str],
    *,
    chunks: List[str],
) -> None:
    """
    Play audio files in sequence with keyboard controls.

    :param audio_files: list of paths to audio files
    :param chunks: list of chunk text contents (formatted before cleaning)
    """
    _LOG.debug("Starting audio playback initialization for %d files", len(audio_files))
    import pygame
    from pynput import keyboard
    _LOG.debug("Required packages imported successfully")
    for audio_file in audio_files:
        hdbg.dassert_file_exists(audio_file, "Audio file must exist")
    _LOG.debug("All %d audio files exist", len(audio_files))
    pygame.mixer.init()
    _LOG.debug("Pygame mixer initialized")
    playback_state: Dict[str, bool] = {"paused": False, "stopped": False}
    def _on_press(key: Any) -> None:
        try:
            if hasattr(key, "char"):
                char = getattr(key, "char", None)
                if char == "p":
                    playback_state["paused"] = not playback_state["paused"]
                    _LOG.info(
                        "Playback %s",
                        "paused" if playback_state["paused"] else "resumed",
                    )
                elif char == "s":
                    playback_state["stopped"] = True
                    _LOG.info("Playback stopped")
        except (AttributeError, TypeError):
            pass
    _LOG.debug("Keyboard listener setup complete")
    listener = keyboard.Listener(on_press=_on_press)
    _LOG.debug("Creating keyboard listener")
    listener.start()
    _LOG.debug("Keyboard listener started")
    os.system("clear" if os.name != "nt" else "cls")
    for audio_file, chunk in zip(audio_files, chunks):
        if playback_state["stopped"]:
            break
        print(chunk)
        sound = pygame.mixer.Sound(audio_file)
        _LOG.debug("Sound loaded successfully")
        channel = sound.play()
        while channel.get_busy() and not playback_state["stopped"]:
            if playback_state["paused"]:
                pygame.mixer.pause()
            else:
                pygame.mixer.unpause()
            pygame.time.wait(100)
    _LOG.debug("Playback loop finished")
    listener.stop()
    pygame.mixer.stop()


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the markdown reader.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.debug(
        "Arguments parsed: input=%s, speed=%.2f, voice=%s, no_play=%s, max_length=%d",
        args.input,
        args.speed,
        args.voice,
        args.no_play,
        args.max_length,
    )
    hdbg.dassert(
        args.input,
        "Input file path is required",
    )
    _LOG.debug("Validations passed")
    content = _read_markdown_file(args.input)
    _LOG.info("Read markdown file: %s", args.input)
    _LOG.debug("Content length: %d characters", len(content))
    sections = _split_by_first_level_bullets(content)
    _LOG.info("Split into %d sections at first-level bullet points", len(sections))
    chunks = []
    chunk_originals = []
    for section_idx, section in enumerate(sections, 1):
        section = section.strip()
        if not section:
            continue
        _LOG.debug("Processing section %d: %d characters", section_idx, len(section))
        original_section = section
        formatted_section = _format_markdown(section)
        _LOG.debug("Formatted section %d: %d characters", section_idx, len(formatted_section))
        cleaned_section = _clean_text(formatted_section)
        _LOG.debug("Cleaned section %d: %d characters", section_idx, len(cleaned_section))
        if args.max_length > 0:
            section_chunks = _chunk_text_by_length(cleaned_section, max_length=args.max_length)
            for chunk in section_chunks:
                chunks.append(chunk)
                chunk_originals.append(original_section)
        else:
            chunks.append(cleaned_section)
            chunk_originals.append(original_section)
    audio_files = []
    try:
        for i, chunk in enumerate(chunks, 1):
            _LOG.info("Processing chunk %d of %d (%d characters)", i, len(chunks), len(chunk))
            _LOG.info("Chunk %d content:\n%s\n---", i, chunk)
            base_audio_file = _get_chunk_filename(chunk, chunk_idx=i, speed=1.0)
            final_audio_file = _get_chunk_filename(chunk, chunk_idx=i, speed=args.speed)
            if os.path.exists(final_audio_file):
                _LOG.info("Speed-adjusted audio file already exists (cached): %s", final_audio_file)
                audio_files.append(final_audio_file)
                continue
            if not os.path.exists(base_audio_file):
                _LOG.info("Generating audio file: %s", base_audio_file)
                _generate_audio(
                    chunk,
                    voice=args.voice,
                    speed=1.0,
                    output_file=base_audio_file,
                )
            else:
                _LOG.info("Audio file already exists (cached): %s", base_audio_file)
            if args.speed != 1.0:
                _LOG.info("Applying speed adjustment: %.2f", args.speed)
                _apply_speed_with_ffmpeg(
                    base_audio_file,
                    output_file=final_audio_file,
                    speed=args.speed,
                )
                audio_files.append(final_audio_file)
            else:
                audio_files.append(base_audio_file)
        _LOG.info(
            "Generated audio with voice='%s' and speed=%.2f (%d chunks)",
            args.voice,
            args.speed,
            len(chunks),
        )
        if not args.no_play and audio_files:
            _LOG.debug("Starting audio playback of %d chunks", len(audio_files))
            _play_audio_with_controls(audio_files, chunks=chunk_originals)
            _LOG.debug("Playback complete")
        if args.no_play:
            _LOG.info("Audio files saved:")
            for audio_file in audio_files:
                _LOG.info("  %s", audio_file)
    except Exception as e:
        _LOG.error("Error during processing: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    _main(_parse())
