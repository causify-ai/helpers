#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pyyaml"]
# ///

"""
Format podcast transcripts into clean markdown with chapters and speaker dialogue.

Converts raw podcast transcripts from podcast_dl.py into structured markdown with:
- Episode title and original link
- Chapters with timestamps
- Speaker dialogue with abbreviations
- All artifacts removed

Examples:
> ./transcript_formatter.py --transcript /tmp/2026-02-12_lex-fridman.txt \\
        --url https://lexfridman.com/peter-steinberger-transcript/ \\
        --output peter-steinberger.md

> ./transcript_formatter.py --transcript podcast.txt --output podcast.md --run_lint
"""

import argparse
import logging
import re
from typing import Dict, List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# Pattern for speaker name and timestamp: "Speaker Name(HH:MM:SS)" or "Speaker NameHH:MM:SS"
_SPEAKER_TIMESTAMP_PATTERN = r"^([A-Za-z\s\.]+)\((\d{2}):(\d{2}):(\d{2})\)"
# Alternative pattern for formats without parentheses: "Speaker NameHH:MM:SS"
_SPEAKER_TIMESTAMP_ALT_PATTERN = (
    r"([A-Z][a-z]+(?: [A-Z][a-z]+)*)(\d{2}):(\d{2}):(\d{2})"
)
# Pattern for chapter in TOC: "H:MM – Chapter Title" or "(HH:MM:SS) – Chapter Title"
# Handles both formats with and without parentheses and seconds
_CHAPTER_PATTERN = r"\(?(\d{1,2}):(\d{2})(?::\d{2})?\)?\s+(?:–|-)\s+([^0-9\(\)]*?)(?=\(?\d{1,2}:\d{2}|$)"


# #############################################################################
# Chapter
# #############################################################################


class Chapter:
    """
    Represents a chapter in the transcript.
    """

    # TODO(ai_gp): make it static
    def _parse_timestamp(self, timestamp: str) -> int:
        """
        Convert timestamp string to seconds.

        :param timestamp: time in H:MM or HH:MM format
        :return: time in seconds
        """
        parts = timestamp.split(":")
        hdbg.dassert_eq(
            len(parts),
            2,
            "Invalid timestamp format: %s",
            timestamp,
        )
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours * 3600 + minutes * 60

    def __init__(self, *, timestamp: str, title: str) -> None:
        """
        Initialize a chapter.

        :param timestamp: chapter time in HH:MM or H:MM format
        :param title: chapter title
        """
        self.timestamp = timestamp
        self.title = title
        self.seconds = self._parse_timestamp(timestamp)


# #############################################################################
# DialogueLine
# #############################################################################


class DialogueLine:
    """
    Represents a single speaker's dialogue.
    """

    # TODO(ai_gp): make it static
    def _parse_timestamp(self, timestamp: str) -> int:
        """
        Convert HH:MM:SS to seconds.

        :param timestamp: time in HH:MM:SS format
        :return: time in seconds
        """
        parts = timestamp.split(":")
        hdbg.dassert_eq(
            len(parts),
            3,
            "Invalid timestamp format: %s",
            timestamp,
        )
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    def __init__(self, *, speaker: str, timestamp: str, text: str) -> None:
        """
        Initialize a dialogue line.

        :param speaker: speaker name
        :param timestamp: time in HH:MM:SS format
        :param text: dialogue text
        """
        self.speaker = speaker
        self.timestamp = timestamp
        self.text = text
        self.seconds = self._parse_timestamp(timestamp)


# #############################################################################
# TranscriptParser
# #############################################################################


class TranscriptParser:
    """
    Parse podcast transcripts and extract structured content.
    """

    def __init__(self, *, transcript_text: str) -> None:
        """
        Initialize parser with transcript text.

        :param transcript_text: the full transcript text
        """
        self.transcript_text = transcript_text
        self.lines = transcript_text.split("\n")

    def extract_title(self) -> str:
        """
        Extract episode title from transcript.

        :return: episode title
        """
        # Look for title patterns in the text.
        full_text = " ".join(self.lines)
        # Try to find episode description patterns (works for Dwarkesh/etc).
        patterns = [
            r'"([^"]+)".*?explains',  # Title in quotes before explains
            r"[—-]\s*([^\"]+?)\s*\"",  # Title before quote
            r"This is a transcript of.*?with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                title = match.group(1).strip()
                if len(title) > 3:
                    return title
        # Fall back to first non-empty line.
        for line in self.lines:
            line = line.strip()
            if line and not line.startswith(("The timestamps", "Playback", "×")):
                return line
        return "Podcast Transcript"

    def extract_chapters(self) -> List[Chapter]:
        """
        Extract chapters from transcript TOC.

        Handles both "Table of Contents" sections and "Timestamps" sections.

        :return: list of Chapter objects
        """
        chapters = []
        # Join all text to find chapters.
        full_text = " ".join(self.lines)
        # Look for "Timestamps" or "Table of Contents" section.
        toc_match = re.search(
            r"(?:Table of Contents|Timestamps)(.*?)(?:Episode|Transcript|$)",
            full_text,
            re.IGNORECASE,
        )
        if toc_match:
            toc_text = toc_match.group(1)
        else:
            toc_text = ""
        # Parse all chapters from the TOC text using regex.
        for match in re.finditer(_CHAPTER_PATTERN, toc_text):
            hours = match.group(1)
            minutes = match.group(2)
            title = match.group(3).strip()
            timestamp = f"{hours}:{minutes}"
            chapters.append(Chapter(timestamp=timestamp, title=title))
        return chapters

    def _extract_dialogue_line_format(self) -> List[DialogueLine]:
        """
        Extract dialogue from line-separated format: Speaker(HH:MM:SS)text.

        :return: list of DialogueLine objects
        """
        dialogue_lines = []
        for line in self.lines:
            line = line.strip()
            if not line:
                continue
            # Match speaker and timestamp pattern at start of line.
            match = re.match(_SPEAKER_TIMESTAMP_PATTERN, line)
            if match:
                speaker = match.group(1).strip()
                hours = match.group(2)
                minutes = match.group(3)
                seconds = match.group(4)
                timestamp = f"{hours}:{minutes}:{seconds}"
                # Extract dialogue text (rest of line after timestamp).
                text_start = match.end()
                text = line[text_start:].strip()
                # Only add if speaker looks like a real person name (has 2 words).
                speaker_words = speaker.split()
                if (
                    text
                    and len(speaker_words) == 2
                    and all(w[0].isupper() for w in speaker_words)
                ):
                    dialogue_lines.append(
                        DialogueLine(
                            speaker=speaker,
                            timestamp=timestamp,
                            text=text,
                        )
                    )
        return dialogue_lines

    def _extract_dialogue_concat_format(self) -> List[DialogueLine]:
        """
        Extract dialogue from concatenated format: SpeakerHH:MM:SStext.

        :return: list of DialogueLine objects
        """
        dialogue_lines = []
        # Join all text for concatenated format.
        full_text = " ".join(self.lines)
        # Find all matches of the pattern.
        matches = list(re.finditer(_SPEAKER_TIMESTAMP_ALT_PATTERN, full_text))
        # Extract dialogue between consecutive matches.
        for i, match in enumerate(matches):
            speaker = match.group(1).strip()
            hours = match.group(2)
            minutes = match.group(3)
            seconds = match.group(4)
            timestamp = f"{hours}:{minutes}:{seconds}"
            # Extract text from end of this match to start of next.
            text_start = match.end()
            if i + 1 < len(matches):
                text_end = matches[i + 1].start()
                text = full_text[text_start:text_end].strip()
            else:
                text = full_text[text_start:].strip()
            # Only add if speaker and text look valid.
            if text:
                dialogue_lines.append(
                    DialogueLine(
                        speaker=speaker,
                        timestamp=timestamp,
                        text=text,
                    )
                )
        return dialogue_lines

    def extract_dialogue(self) -> List[DialogueLine]:
        """
        Extract all dialogue lines from transcript.

        Handles both line-separated and concatenated formats with or without parentheses.

        :return: list of DialogueLine objects, sorted by timestamp
        """
        dialogue_lines = []
        # Try line-by-line parsing first (Lex Fridman format).
        dialogue_lines.extend(self._extract_dialogue_line_format())
        # If no dialogues found, try concatenated format (Dwarkesh format).
        if not dialogue_lines:
            dialogue_lines.extend(self._extract_dialogue_concat_format())
        # Sort by timestamp.
        dialogue_lines.sort(key=lambda d: d.seconds)
        return dialogue_lines


# #############################################################################
# MarkdownFormatter
# #############################################################################


class MarkdownFormatter:
    """
    Format transcript data into markdown.
    """

    def __init__(self) -> None:
        """
        Initialize the formatter.
        """
        self.speaker_abbrevs: Dict[str, str] = {}

    def _add_speaker(self, speaker: str) -> None:
        """
        Add speaker to abbreviation map.

        :param speaker: full speaker name
        """
        if speaker in self.speaker_abbrevs:
            return
        # Create abbreviation from initials.
        parts = speaker.split()
        abbrev = "".join(p[0] for p in parts).upper()
        # Fall back to first name if that doesn't work.
        if not abbrev:
            abbrev = speaker[:2].upper()
        self.speaker_abbrevs[speaker] = abbrev

    def format(
        self,
        *,
        title: str,
        url: str,
        chapters: List[Chapter],
        dialogue: List[DialogueLine],
    ) -> str:
        """
        Format transcript data into markdown.

        :param title: episode title
        :param url: original URL
        :param chapters: list of chapters
        :param dialogue: list of dialogue lines
        :return: formatted markdown string
        """
        # Build abbreviation map from all speakers.
        for line in dialogue:
            self._add_speaker(line.speaker)
        output = []
        # Add title.
        output.append(f"# {title}\n")
        # Add link.
        output.append(f"// Link: {url}\n")
        # Add dialogue with chapter headers.
        chapter_idx = 0
        for dialogue_line in dialogue:
            # Check if we should insert a chapter header.
            if chapter_idx < len(chapters):
                chapter = chapters[chapter_idx]
                if dialogue_line.seconds >= chapter.seconds:
                    # Insert chapter header.
                    output.append(
                        f"\n## {chapter.title} ({chapter.timestamp})\n"
                    )
                    chapter_idx += 1
            # Add dialogue line.
            abbrev = self.speaker_abbrevs[dialogue_line.speaker]
            output.append(f"{abbrev}: {dialogue_line.text}\n")
        return "".join(output)


# #############################################################################
# Script
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--transcript",
        action="store",
        required=True,
        help="Path to raw transcript file",
    )
    parser.add_argument(
        "--url",
        action="store",
        required=True,
        help="Original podcast URL",
    )
    parser.add_argument(
        "--output",
        action="store",
        required=True,
        help="Output markdown file path",
    )
    parser.add_argument(
        "--run_lint",
        action="store_true",
        help="Run lint_txt.py on output file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read transcript.
    _LOG.info("Reading transcript from: %s", args.transcript)
    hdbg.dassert_file_exists(args.transcript)
    with open(args.transcript, "r") as f:
        transcript_text = f.read()
    # Parse transcript.
    _LOG.info("Parsing transcript")
    parser_obj = TranscriptParser(transcript_text=transcript_text)
    title = parser_obj.extract_title()
    _LOG.debug("Extracted title: %s", title)
    chapters = parser_obj.extract_chapters()
    _LOG.info("Extracted %d chapters", len(chapters))
    dialogue = parser_obj.extract_dialogue()
    _LOG.info("Extracted %d dialogue lines", len(dialogue))
    # Format as markdown.
    _LOG.info("Formatting as markdown")
    formatter = MarkdownFormatter()
    markdown = formatter.format(
        title=title, url=args.url, chapters=chapters, dialogue=dialogue
    )
    # Write output.
    _LOG.info("Writing markdown to: %s", args.output)
    with open(args.output, "w") as f:
        f.write(markdown)
    _LOG.info("Markdown file created successfully")
    # Run lint if requested.
    if args.run_lint:
        _LOG.info("Running lint_txt.py on output")
        cmd = f"lint_txt.py -i {args.output}"
        hsystem.system(cmd)
        _LOG.info("Linting complete")


if __name__ == "__main__":
    _main(_parse())
