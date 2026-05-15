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
from typing import Dict

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_DEFAULT_SPEED = 1.0
_DEFAULT_VOICE = "en_US-joe-medium"
_SPEED_STEP = 0.1
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


def _split_by_first_level_bullets(text: str) -> list:
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


def _chunk_text_by_length(text: str, *, max_length: int) -> list:
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


def _get_chunk_filename(chunk: str, *, chunk_idx: int) -> str:
    """
    Generate output filename for a chunk based on its SHA1 hash.

    Format: tmp.piper.chunk<idx>.<sha1_hash>.wav

    :param chunk: chunk text content
    :param chunk_idx: chunk index (1-based)
    :return: filename for the chunk audio file
    """
    sha1_hash = hashlib.sha1(chunk.encode()).hexdigest()
    filename = f"tmp.piper.chunk{chunk_idx}.{sha1_hash}.wav"
    _LOG.debug("Chunk %d hash: %s, filename: %s", chunk_idx, sha1_hash, filename)
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
) -> bool:
    """
    Generate audio from text using Piper TTS.

    :param text: text to synthesize
    :param voice: voice identifier
    :param speed: speech speed
    :param output_file: path to output audio file
    :return: True if successful, False otherwise
    """
    try:
        _LOG.debug("Starting audio generation: voice=%s, speed=%.2f", voice, speed)
        voice_path = _get_voice_path(voice)
        if not os.path.exists(voice_path):
            voices_dir = os.path.dirname(voice_path)
            _LOG.error(
                "Voice model '%s' not found at %s",
                voice,
                voice_path,
            )
            _LOG.error(
                "Download voice models to %s",
                voices_dir,
            )
            return False
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
        if process.returncode != 0:
            _LOG.error("Piper failed: %s", stderr)
            return False
        file_size = os.path.getsize(output_file)
        _LOG.info("Generated audio file: %s (%d bytes)", output_file, file_size)
        return True
    except subprocess.TimeoutExpired:
        _LOG.error("Piper process timed out")
        return False
    except FileNotFoundError:
        _LOG.error("Piper command not found. Install with: pip install piper-tts")
        return False
    except Exception as e:
        _LOG.error("Failed to generate audio: %s", e)
        return False


def _apply_speed_with_ffmpeg(
    audio_file: str,
    *,
    speed: float,
) -> bool:
    """
    Apply speed adjustment to audio using ffmpeg atempo filter.

    :param audio_file: path to audio file to adjust
    :param speed: speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = 2x slower)
    :return: True if successful, False otherwise
    """
    try:
        if speed == 1.0:
            _LOG.debug("Speed is 1.0, skipping ffmpeg adjustment")
            return True
        _LOG.debug("Applying speed adjustment with ffmpeg: speed=%.2f", speed)
        temp_file = audio_file + ".tmp"
        cmd = [
            "ffmpeg",
            "-i", audio_file,
            "-filter:a", f"atempo={speed}",
            "-y",
            temp_file,
        ]
        _LOG.debug("Running ffmpeg: atempo=%.2f", speed)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        _, stderr = process.communicate(timeout=300)
        _LOG.debug("ffmpeg process completed with return code: %d", process.returncode)
        if process.returncode != 0:
            _LOG.error("ffmpeg speed adjustment failed: %s", stderr)
            return False
        import shutil
        shutil.move(temp_file, audio_file)
        file_size = os.path.getsize(audio_file)
        _LOG.info("Speed adjustment applied: %s at %.2fx (%d bytes)", audio_file, speed, file_size)
        return True
    except FileNotFoundError:
        _LOG.error("ffmpeg command not found. Install with: brew install ffmpeg")
        return False
    except subprocess.TimeoutExpired:
        _LOG.error("ffmpeg process timed out")
        return False
    except Exception as e:
        _LOG.error("Failed to apply speed adjustment: %s", e)
        return False


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
        "--no-play",
        action="store_true",
        help="Generate audio file without playing it",
    )
    parser.add_argument(
        "--max-length",
        action="store",
        type=int,
        default=_DEFAULT_MAX_LENGTH,
        help="Maximum text length per chunk (0 = no chunking)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _play_audio_with_controls(
    audio_files: list,
    *,
    chunks: list,
    initial_speed: float,
) -> None:
    """
    Play audio files in sequence with keyboard controls.

    :param audio_files: list of paths to audio files
    :param chunks: list of chunk text contents (formatted before cleaning)
    :param initial_speed: initial speech speed for display
    """
    _LOG.debug("Starting audio playback initialization for %d files", len(audio_files))
    try:
        import pygame
    except ImportError:
        _LOG.error("Pygame package not found. Install with: pip install pygame")
        return
    try:
        from pynput import keyboard
    except ImportError:
        _LOG.error("pynput package not found. Install with: pip install pynput")
        return
    _LOG.debug("Required packages imported successfully")
    for audio_file in audio_files:
        hdbg.dassert_file_exists(audio_file, "Audio file must exist")
    _LOG.debug("All %d audio files exist", len(audio_files))
    pygame.mixer.init()
    _LOG.debug("Pygame mixer initialized")
    playback_state: Dict[str, bool] = {"paused": False, "stopped": False}
    current_speed = [initial_speed]
    def _on_press(key) -> None:
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
                elif char == "+":
                    current_speed[0] += _SPEED_STEP
                    _LOG.info("Speed increased to %.2f", current_speed[0])
                elif char == "-":
                    current_speed[0] -= _SPEED_STEP
                    _LOG.info("Speed decreased to %.2f", current_speed[0])
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
        try:
            sound = pygame.mixer.Sound(audio_file)
            _LOG.debug("Sound loaded successfully")
        except Exception as e:
            _LOG.error("Failed to load audio file %s: %s", audio_file, e)
            continue
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
            audio_file = _get_chunk_filename(chunk, chunk_idx=i)
            if os.path.exists(audio_file):
                _LOG.info("Audio file already exists (cached): %s", audio_file)
            else:
                _LOG.info("Generating audio file: %s", audio_file)
                success = _generate_audio(
                    chunk,
                    voice=args.voice,
                    speed=1.0,
                    output_file=audio_file,
                )
                if not success:
                    _LOG.error("Failed to generate audio for chunk %d", i)
                    sys.exit(1)
                if args.speed != 1.0:
                    success = _apply_speed_with_ffmpeg(audio_file, speed=args.speed)
                    if not success:
                        _LOG.error("Failed to apply speed adjustment to chunk %d", i)
                        sys.exit(1)
            audio_files.append(audio_file)
        _LOG.info(
            "Generated audio with voice='%s' and speed=%.2f (%d chunks)",
            args.voice,
            args.speed,
            len(chunks),
        )
        if not args.no_play and audio_files:
            _LOG.debug("Starting audio playback of %d chunks", len(audio_files))
            _play_audio_with_controls(audio_files, chunks=chunk_originals, initial_speed=args.speed)
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
