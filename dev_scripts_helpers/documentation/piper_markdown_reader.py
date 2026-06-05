#!/usr/bin/env -S uv run

# /// script
# dependencies = ["piper-tts", "pygame", "pynput", "tqdm"]
# ///

"""
Read a markdown file and play it using Piper text-to-speech with playback controls.

Examples:
> ./piper_markdown_reader.py --input README.md
> ./piper_markdown_reader.py --input README.md --speed 1.5 --voice en_US-joe-medium
> ./piper_markdown_reader.py --input README.md --speed 0.8 --voice en_US-amy-medium
> ./piper_markdown_reader.py --input README.md --md_start "Section 5" --md_end "END" --dry_run
"""

import argparse
import hashlib
import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown_select as hmarsele
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_DEFAULT_SPEED = 1.0
# _DEFAULT_VOICE = "en_US-joe-medium"
_DEFAULT_VOICE = "en_US-amy-medium"
_DEFAULT_MAX_LENGTH = 0
_TMP_EXTRACT_FILE = "tmp.piper_markdown_reader.extract.md"
_WORDS_PER_MINUTE = 150

# #############################################################################
# File I/O and Text Parsing
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


def _extract_markdown_section(
    file_path: str,
    md_start: str,
    md_end: str,
) -> str:
    """
    Extract a markdown section, write to tmp file, run lint_txt.py.

    Extracts lines between md_start and md_end headers, writes them to
    `tmp.piper_markdown_reader.extract.md`, runs `lint_txt.py -w 1000`
    to unroll bullet list breaks, and returns the processed content.

    :param file_path: path to markdown input file
    :param md_start: starting header (full "## Title" or partial "Title")
    :param md_end: ending header or None to auto-detect next same-level, or "END" to extract to end of file
    :return: processed content of the extracted section
    """
    # Read, process, write back file.
    lines = hseinout.from_file(file_path)
    extracted_lines = hmarsele.extract_text_from_markdown_lines(
        lines, md_start, md_end
    )
    extracted_content = "\n".join(extracted_lines)
    hio.to_file(_TMP_EXTRACT_FILE, extracted_content)
    _LOG.info("Extracted section written to '%s'", _TMP_EXTRACT_FILE)
    # Lint.
    _LOG.info("Linting ...")
    lint_script = hgit.find_file_in_git_tree("lint_txt.py")
    cmd = f"{lint_script} -i {_TMP_EXTRACT_FILE} -w 1000"
    hsystem.system(cmd)
    _LOG.info("Linting ... done")
    # Read back.
    processed_content = hio.from_file(_TMP_EXTRACT_FILE)
    return processed_content


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
    # Start new section at each first-level bullet point.
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


# #############################################################################
# Text Processing and Transformation
# #############################################################################


def _format_markdown(text: str) -> str:
    """
    Convert markdown formatting to spoken text format.

    :param text: markdown text with formatting
    :return: formatted text suitable for TTS
    """
    _LOG.debug("Starting markdown formatting")
    import re

    lines = []
    # Convert markdown to spoken text: headers become chapter announcements,
    # bullets get periods.
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("### "):
            line = line[4:].strip() + "."
        elif line.startswith("## "):
            line = line[3:].strip() + "."
        elif line.startswith("# "):
            line = line[2:].strip() + "."
        elif line.startswith("- ") or line.startswith("* "):
            bullet_text = re.sub(r"^[-*]\s+", "", line)
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
    # Remove markdown formatting markers: bold, italic, code, headers.
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            line = line.lstrip("#").strip()
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)
        line = re.sub(r"\*([^*]+)\*", r"\1", line)
        line = re.sub(r"_([^_]+)_", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        if line:
            lines.append(line)
    cleaned = "\n".join(lines)
    _LOG.debug(
        "Text cleanup complete: %d lines, %d characters",
        len(lines),
        len(cleaned),
    )
    return cleaned


def _count_words(text: str) -> int:
    """
    Count the number of words in text.

    :param text: text to count words from
    :return: number of words
    """
    words = text.split()
    return len(words)


def _format_reading_time(*, words: int, speed: float = 1.0) -> str:
    """
    Format word count as readable time, adjusted for speed.

    :param words: number of words
    :param speed: speech speed multiplier (1.0 = normal, 1.5 = 1.5x faster)
    :return: formatted time string (e.g., "32.8m" or "7.17h")
    """
    minutes = (words / _WORDS_PER_MINUTE) / speed
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.2f}h"


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
    # Greedily pack sentences: fit as many as possible per chunk, but break
    # sentences longer than max_length.
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


# #############################################################################
# Audio Generation Utilities
# #############################################################################


def _get_chunk_filename(
    chunk: str, *, chunk_idx: int, speed: float = 1.0
) -> str:
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
        filename = (
            f"tmp.piper.chunk{chunk_idx}.speed_{speed:.1f}.{sha1_hash}.wav"
        )
    else:
        filename = f"tmp.piper.chunk{chunk_idx}.{sha1_hash}.wav"
    _LOG.debug(
        "Chunk %d hash: %s, speed: %.2f, filename: %s",
        chunk_idx,
        sha1_hash,
        speed,
        filename,
    )
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
    _LOG.debug(
        "Piper process completed with return code: %d", process.returncode
    )
    hdbg.dassert_eq(
        process.returncode,
        0,
        "Piper command failed: %s",
        stderr,
    )
    file_size = os.path.getsize(output_file)
    _LOG.debug("Generated audio file: %s (%d bytes)", output_file, file_size)


def _apply_speed_with_ffmpeg(
    input_file: str,
    *,
    output_file: str,
    speed: float,
    progress_bar: Optional[Any] = None,
) -> None:
    """
    Apply speed adjustment to audio using ffmpeg atempo filter.

    :param input_file: path to input audio file
    :param output_file: path to output audio file
    :param speed: speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = 2x slower)
    :param progress_bar: optional tqdm progress bar to update
    """
    if speed == 1.0:
        _LOG.debug("Speed is 1.0, skipping ffmpeg adjustment")
        return
    _LOG.debug("Applying speed adjustment with ffmpeg: speed=%.2f", speed)
    cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-filter:a",
        f"atempo={speed}",
        "-acodec",
        "pcm_s16le",
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
    if progress_bar:
        progress_bar.update(1)
    _LOG.debug(
        "ffmpeg process completed with return code: %d", process.returncode
    )
    hdbg.dassert_eq(
        process.returncode,
        0,
        "ffmpeg speed adjustment failed: %s",
        stderr,
    )
    file_size = os.path.getsize(output_file)
    _LOG.debug(
        "Speed adjustment applied: %s at %.2fx (%d bytes)",
        output_file,
        speed,
        file_size,
    )


# #############################################################################
# Chunk Processing and Orchestration
# #############################################################################


def _process_sections_to_chunks(
    sections: List[str],
    *,
    max_length: int,
) -> Tuple[List[str], List[str]]:
    """
    Convert markdown sections into text chunks with their original sections.

    :param sections: list of markdown sections
    :param max_length: maximum text length per chunk (0 = no chunking)
    :return: (chunks, chunk_originals) where each chunk has a corresponding original
    """
    chunks = []
    chunk_originals = []
    # Each section flows through:
    # - format markdown syntax
    # - strip formatting
    # - split by max_length.
    # Store cleaned chunks and unmodified original sections for later display.
    for section_idx, section in enumerate(sections, 1):
        section = section.strip()
        if not section:
            continue
        _LOG.debug(
            "Processing section %d: %d characters", section_idx, len(section)
        )
        original_section = section
        formatted_section = _format_markdown(section)
        _LOG.debug(
            "Formatted section %d: %d characters",
            section_idx,
            len(formatted_section),
        )
        cleaned_section = _clean_text(formatted_section)
        _LOG.debug(
            "Cleaned section %d: %d characters",
            section_idx,
            len(cleaned_section),
        )
        if max_length > 0:
            section_chunks = _chunk_text_by_length(
                cleaned_section, max_length=max_length
            )
            for chunk in section_chunks:
                chunks.append(chunk)
                chunk_originals.append(original_section)
        else:
            chunks.append(cleaned_section)
            chunk_originals.append(original_section)
    return chunks, chunk_originals


def _process_chunk_audio(
    chunk_idx: int,
    chunk: str,
    *,
    voice: str,
    speed: float,
    progress_bar: Optional[Any] = None,
) -> str:
    """
    Generate audio for a chunk with speed adjustment and caching.

    :param chunk_idx: chunk index (1-based)
    :param chunk: chunk text content
    :param voice: voice identifier
    :param speed: speech speed
    :param progress_bar: optional tqdm progress bar to update
    :return: path to final audio file
    """
    _LOG.debug(
        "Processing chunk %d of %d (%d characters)",
        chunk_idx,
        chunk_idx,
        len(chunk),
    )
    _LOG.debug("Chunk %d content:\n%s\n---", chunk_idx, chunk)
    base_audio_file = _get_chunk_filename(chunk, chunk_idx=chunk_idx, speed=1.0)
    final_audio_file = _get_chunk_filename(
        chunk, chunk_idx=chunk_idx, speed=speed
    )
    # Cache strategy: store base audio (speed=1.0) once, then apply speed via
    # ffmpeg (cheaper than re-synthesizing).
    # This saves TTS calls when speed changes but content stays the same.
    if os.path.exists(final_audio_file):
        _LOG.debug(
            "Speed-adjusted audio file already exists (cached): %s",
            final_audio_file,
        )
        if progress_bar:
            progress_bar.update(2 if speed != 1.0 else 1)
        return final_audio_file
    if not os.path.exists(base_audio_file):
        _LOG.debug("Generating audio file: %s", base_audio_file)
        _generate_audio(
            chunk,
            voice=voice,
            speed=1.0,
            output_file=base_audio_file,
        )
    else:
        _LOG.debug("Audio file already exists (cached): %s", base_audio_file)
    if progress_bar:
        progress_bar.update(1)
    if speed != 1.0:
        _LOG.debug("Applying speed adjustment: %.2f", speed)
        _apply_speed_with_ffmpeg(
            base_audio_file,
            output_file=final_audio_file,
            speed=speed,
            progress_bar=progress_bar,
        )
        return final_audio_file
    if progress_bar:
        progress_bar.update(1)
    return base_audio_file


# #############################################################################
# Playback and Output
# #############################################################################


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
    _LOG.debug(
        "Starting audio playback initialization for %d files", len(audio_files)
    )
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
    total_chunks = len(audio_files)
    # Play sequentially, polling at 100ms to check pause/stop state while audio
    # plays. Pygame mixer pause/unpause affects all channels, synchronized with
    # keyboard input.
    for chunk_idx, (audio_file, chunk) in enumerate(zip(audio_files, chunks), 1):
        if playback_state["stopped"]:
            break
        if (chunk_idx - 1) % 10 == 0 and chunk_idx > 1:
            os.system("clear" if os.name != "nt" else "cls")
        print(f"{chunk_idx}/{total_chunks}")
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


def _handle_final_output(
    audio_files: List[str],
    chunks: List[str],
    *,
    no_play: bool,
) -> None:
    """
    Handle final output: play audio or list saved files.

    :param audio_files: list of audio file paths
    :param chunks: list of chunk text contents for display
    :param no_play: if True, list files instead of playing
    """
    if not no_play and audio_files:
        _LOG.debug("Starting audio playback of %d chunks", len(audio_files))
        _play_audio_with_controls(audio_files, chunks=chunks)
        _LOG.debug("Playback complete")
    if no_play:
        _LOG.info("Audio files saved:")
        for audio_file in audio_files:
            _LOG.info("  %s", audio_file)


# #############################################################################
# CLI and Entry Point
# #############################################################################


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
        "--dry_run",
        action="store_true",
        help="Print chunks without generating audio",
    )
    parser.add_argument(
        "--max_length",
        action="store",
        type=int,
        default=_DEFAULT_MAX_LENGTH,
        help="Maximum text length per chunk (0 = no chunking)",
    )
    hparser.add_verbosity_arg(parser)
    hmarsele.add_select_arg(parser, required=False)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the markdown reader.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.debug(
        "Arguments parsed: input=%s, speed=%.2f, voice=%s, no_play=%s, dry_run=%s, max_length=%d",
        args.input,
        args.speed,
        args.voice,
        args.no_play,
        args.dry_run,
        args.max_length,
    )
    hdbg.dassert(
        args.input,
        "Input file path is required",
    )
    _LOG.debug("Validations passed")
    if args.select:
        md_start, md_end = hmarsele.parse_select_arg(args.select)
        content = _extract_markdown_section(args.input, md_start, md_end)
        _LOG.info("Extracted section '%s' from %s", md_start, args.input)
    else:
        content = _read_markdown_file(args.input)
        _LOG.info("Read markdown file: %s", args.input)
    _LOG.debug("Content length: %d characters", len(content))
    sections = _split_by_first_level_bullets(content)
    _LOG.info(
        "Split into %d sections at first-level bullet points", len(sections)
    )
    chunks, chunk_originals = _process_sections_to_chunks(
        sections,
        max_length=args.max_length,
    )
    # Calculate reading time estimate
    total_words = sum(_count_words(chunk) for chunk in chunks)
    reading_time = _format_reading_time(words=total_words, speed=args.speed)
    reading_time_normal = _format_reading_time(words=total_words, speed=1.0)
    conversion_start_time = time.time()
    _LOG.info(
        "=== CONVERSION START ===: %d chunks, %d words, reading time: %s (normal speed: %s)",
        len(chunks),
        total_words,
        reading_time,
        reading_time_normal,
    )
    if args.dry_run:
        _LOG.info("Dry-run mode: printing chunks without audio generation")
        for i, chunk in enumerate(chunks, 1):
            _LOG.debug("Chunk %d:\n%s", i, chunk)
        conversion_elapsed = time.time() - conversion_start_time
        _LOG.info(
            "=== CONVERSION END ===: %d chunks processed in %.2f seconds",
            len(chunks),
            conversion_elapsed,
        )
        return
    # Pipeline:
    # - read
    # - split by bullets
    # - format/clean/length-chunk
    # - synthesize with cache
    # - play.
    audio_files = []
    total_work = len(chunks) * (2 if args.speed != 1.0 else 1)
    with tqdm(
        total=total_work, desc="Processing chunks", unit="step"
    ) as progress_bar:
        for i in range(len(chunks)):
            chunk = chunks[i]
            audio_file = _process_chunk_audio(
                i + 1,
                chunk,
                voice=args.voice,
                speed=args.speed,
                progress_bar=progress_bar,
            )
            audio_files.append(audio_file)
    conversion_elapsed = time.time() - conversion_start_time
    _LOG.debug(
        "=== CONVERSION END ===: Generated audio with voice='%s' and speed=%.2f (%d chunks in %.2f seconds)",
        args.voice,
        args.speed,
        len(chunks),
        conversion_elapsed,
    )
    if not args.no_play and audio_files:
        input("Are you ready to start? Press Enter to continue...")
    _handle_final_output(audio_files, chunk_originals, no_play=args.no_play)


if __name__ == "__main__":
    _main(_parse())
