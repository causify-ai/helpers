#!/usr/bin/env -S uv run

# /// script
# dependencies = ["requests", "beautifulsoup4"]
# ///

"""
Download and format podcast transcripts from various sources.

Supports three actions:
- download: fetch transcript from a podcast site
- format: convert raw transcript to formatted markdown
- all: download and format in one step (auto-derives URL)

Examples:
# Download a Lex Fridman episode
> ./podcast_dl.py --action download --type lexfriedman --title lars-brownworth --output_dir ./transcripts

# Format a transcript
> ./podcast_dl.py --action format --transcript podcast.txt --url https://example.com --output podcast.md

# Download and format in one step
> ./podcast_dl.py --action all --type dwarkesh --title andrej-karpathy --output_dir ./transcripts
"""

# Architecture:
# - `PodcastDownloader`: Abstract base class defining interface for downloading
#   transcripts from different podcast sources
#   - Concrete implementations (`LexFriedmanDownloader`, `DwarkeshDownloader`,
#     etc.) extract transcript and metadata from site-specific HTML.
# - `TranscriptParser`: Extracts structured content (title, chapters, dialogue)
#   from raw transcript text using regex patterns.
# - `MarkdownFormatter`: Converts parsed transcript data into formatted markdown
#   with chapter sections and speaker abbreviations.
# - `Factory`: Creates appropriate downloader instance based on podcast type.

import argparse
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_VALID_TYPES = [
    "lexfriedman",
    "dwarkesh",
    "podcasttranscript_ai",
    "podscripts_co",
]

_VALID_ACTIONS = ["download", "format", "all"]
_DEFAULT_ACTIONS = ["all"]


# #############################################################################
# Base Downloader Class
# #############################################################################


class PodcastDownloader(ABC):
    """
    Abstract base class for podcast transcript downloaders.
    """

    def __init__(self, *, slug: str) -> None:
        """
        Initialize the downloader with a podcast slug.

        :param slug: the podcast identifier/slug
        :raises AssertionError: if slug is empty
        """
        hdbg.dassert_ne(slug, "", "Slug cannot be empty")
        self._slug = slug
        self._session = requests.Session()

    @abstractmethod
    def _get_url(self) -> str:
        """
        Get the full URL for the podcast.

        :return: the podcast URL
        """
        pass

    @abstractmethod
    def _extract_transcript(self, html: str) -> str:
        """
        Extract transcript text from HTML content.

        :param html: the HTML content of the podcast page
        :return: the extracted transcript text
        """
        pass

    @abstractmethod
    def _extract_metadata(
        self, html: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Extract metadata from HTML (date, podcast title, guest name).

        :param html: the HTML content of the podcast page
        :return: tuple of (date, podcast_title, guest_name)
        """
        pass

    def download(self) -> Tuple[str, str]:
        """
        Download the podcast transcript.

        :return: tuple of (transcript_text, output_filename)
        """
        url = self._get_url()
        _LOG.info("Fetching transcript from: %s", url)
        response = self._session.get(url, timeout=30)
        response.raise_for_status()
        html = response.text
        transcript = self._extract_transcript(html)
        hdbg.dassert_ne(
            transcript,
            "",
            "Failed to extract transcript from HTML",
        )
        date, podcast_title, guest_name = self._extract_metadata(html)
        output_filename = self._normalize_filename(
            date=date,
            podcast_title=podcast_title,
            guest_name=guest_name,
        )
        return transcript, output_filename

    def _normalize_filename(
        self,
        *,
        date: str,
        podcast_title: str,
        guest_name: Optional[str] = None,
    ) -> str:
        """
        Create normalized output filename: YYYY-MM-DD_podcast-title_guest.txt.

        Extracts a parseable date and slugifies podcast/guest names to create
        consistent, filesystem-friendly filenames.

        :param date: the episode date (will be parsed for YYYY-MM-DD format)
        :param podcast_title: the podcast name
        :param guest_name: optional guest name
        :return: normalized filename (e.g., "2024-05-15_lex-fridman_andrej-karpathy.txt")
        """
        # Extract YYYY-MM-DD format from date string; fall back if not found.
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", date)
        if date_match:
            date_str = date_match.group()
        else:
            date_str = "unknown-date"
        # Normalize podcast title and guest name to lowercase slug format.
        podcast_normalized = self._slugify(podcast_title)
        if guest_name:
            guest_normalized = self._slugify(guest_name)
            filename = (
                f"{date_str}_{podcast_normalized}_{guest_normalized}.txt"
            )
        else:
            filename = f"{date_str}_{podcast_normalized}.txt"
        return filename

    @staticmethod
    def _slugify(text: str) -> str:
        """
        Convert text to lowercase slug format (spaces to hyphens).

        Creates filesystem-safe strings by lowercasing, converting whitespace
        to hyphens, removing special characters, and cleaning up duplicates.

        :param text: the text to slugify
        :return: slugified text (e.g., "Andrej Karpathy" -> "andrej-karpathy")
        """
        # Convert to lowercase and normalize whitespace to single hyphens.
        text = text.lower()
        text = re.sub(r"\s+", "-", text)
        # Remove non-alphanumeric characters except hyphens.
        text = re.sub(r"[^a-z0-9-]", "", text)
        # Collapse consecutive hyphens and strip leading/trailing hyphens.
        text = re.sub(r"-+", "-", text)
        text = text.strip("-")
        return text


# #############################################################################
# Concrete Downloader Implementations
# #############################################################################


class LexFriedmanDownloader(PodcastDownloader):
    """
    Download transcripts from lexfridman.com.
    """

    def _get_url(self) -> str:
        """
        Get the lexfridman.com transcript URL.

        :return: the full URL
        """
        return f"https://lexfridman.com/{self._slug}-transcript"

    def _extract_transcript(self, html: str) -> str:
        """
        Extract transcript from lexfridman.com HTML.

        :param html: the HTML content
        :return: transcript text
        """
        soup = BeautifulSoup(html, "html.parser")
        # Lex Fridman stores transcript in article or content div.
        content: Any = soup.find("article")
        if not content:
            content = soup.find(
                "div", class_=re.compile(r"content|transcript", re.I)
            )
        if not content:
            hdbg.dfatal("Could not find transcript content in HTML")
        # Extract all text from paragraphs and divs.
        lines = []
        for elem in content.find_all(["p", "div"]):
            text = elem.get_text(strip=True)
            if text:
                lines.append(text)
        transcript = "\n\n".join(lines)
        return transcript

    def _extract_metadata(
        self, html: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Extract metadata from lexfridman.com HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        # Try to find the title (usually in h1 or meta tags).
        title_tag = soup.find("h1")
        title = (
            title_tag.get_text(strip=True)
            if title_tag
            else "Lex Fridman"
        )
        # Try to find the date in meta tags.
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag and isinstance(date_tag, Tag):
            date = str(date_tag.get("content", "unknown"))
        else:
            date = "unknown"
        # Extract guest name from title (usually "Guest Name - Lex Fridman #...").
        guest_name = None
        if " - Lex" in title:
            guest_name = title.split(" - Lex")[0].strip()
        return date, "lex-fridman", guest_name


class DwarkeshDownloader(PodcastDownloader):
    """
    Download transcripts from dwarkesh.com.
    """

    def _get_url(self) -> str:
        """
        Get the dwarkesh.com transcript URL.

        :return: the full URL
        """
        return f"https://www.dwarkesh.com/p/{self._slug}"

    def _extract_transcript(self, html: str) -> str:
        """
        Extract transcript from dwarkesh.com HTML.

        :param html: the HTML content
        :return: transcript text
        """
        soup = BeautifulSoup(html, "html.parser")
        # Dwarkesh stores content in post-related divs.
        content: Any = soup.find("div", class_=re.compile(
            r"post", re.I
        ))
        if not content:
            content = soup.find("article")
        if not content:
            hdbg.dfatal("Could not find transcript content in HTML")
        # Extract text, handling blockquotes and paragraphs.
        lines = []
        for elem in content.find_all(["p", "blockquote", "div"]):
            text = elem.get_text(strip=True)
            if text and len(text) > 10:
                lines.append(text)
        transcript = "\n\n".join(lines)
        return transcript

    def _extract_metadata(
        self, html: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Extract metadata from dwarkesh.com HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        # Extract title from h1 or meta tags.
        title_tag = soup.find("h1")
        title = (
            title_tag.get_text(strip=True)
            if title_tag
            else "Dwarkesh"
        )
        # Extract date from meta tags or byline.
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag and isinstance(date_tag, Tag):
            date = str(date_tag.get("content", "unknown"))
        else:
            date = "unknown"
        guest_name = title if title != "Dwarkesh" else None
        return date, "dwarkesh", guest_name


class PodcastTranscriptDownloader(PodcastDownloader):
    """
    Download transcripts from podcasttranscript.ai.
    """

    def _get_url(self) -> str:
        """
        Get the podcasttranscript.ai transcript URL.

        :return: the full URL
        """
        return (
            f"https://podcasttranscript.ai/library/{self._slug}"
        )

    def _extract_transcript(self, html: str) -> str:
        """
        Extract transcript from podcasttranscript.ai HTML.

        :param html: the HTML content
        :return: transcript text
        """
        soup = BeautifulSoup(html, "html.parser")
        # Find transcript container.
        content: Any = soup.find("div", class_=re.compile(
            r"transcript|content", re.I
        ))
        if not content:
            content = soup.find("main")
        if not content:
            hdbg.dfatal("Could not find transcript content in HTML")
        # Extract lines from paragraphs and divs.
        lines = []
        for elem in content.find_all(["p", "div"]):
            text = elem.get_text(strip=True)
            if text:
                lines.append(text)
        transcript = "\n\n".join(lines)
        return transcript

    def _extract_metadata(
        self, html: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Extract metadata from podcasttranscript.ai HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("h1")
        title = (
            title_tag.get_text(strip=True)
            if title_tag
            else "Podcast Transcript"
        )
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag and isinstance(date_tag, Tag):
            date = str(date_tag.get("content", "unknown"))
        else:
            date = "unknown"
        return date, "podcast-transcript", title


class PodscriptsDownloader(PodcastDownloader):
    """
    Download transcripts from podscripts.co.
    """

    def _get_url(self) -> str:
        """
        Get the podscripts.co transcript URL.

        :return: the full URL
        """
        # Slug includes category: category/episode-slug
        return f"https://podscripts.co/podcasts/{self._slug}"

    def _extract_transcript(self, html: str) -> str:
        """
        Extract transcript from podscripts.co HTML.

        :param html: the HTML content
        :return: transcript text
        """
        soup = BeautifulSoup(html, "html.parser")
        # Find main transcript content.
        content: Any = soup.find("div", class_=re.compile(
            r"transcript|script|content", re.I
        ))
        if not content:
            content = soup.find("main")
        if not content:
            hdbg.dfatal("Could not find transcript content in HTML")
        # Extract transcript lines.
        lines = []
        for elem in content.find_all(["p", "div"]):
            text = elem.get_text(strip=True)
            if text:
                lines.append(text)
        transcript = "\n\n".join(lines)
        return transcript

    def _extract_metadata(
        self, html: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Extract metadata from podscripts.co HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("h1")
        title = (
            title_tag.get_text(strip=True)
            if title_tag
            else "Podscripts"
        )
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag and isinstance(date_tag, Tag):
            date = str(date_tag.get("content", "unknown"))
        else:
            date = "unknown"
        return date, "podscripts", title


# #############################################################################
# Transcript Formatting Constants
# #############################################################################

_SPEAKER_TIMESTAMP_PATTERN = r"^([A-Za-z\s\.]+)\((\d{2}):(\d{2}):(\d{2})\)"
_SPEAKER_TIMESTAMP_ALT_PATTERN = r"([A-Z][a-z]+(?: [A-Z][a-z]+)*)(\d{2}):(\d{2}):(\d{2})"
_CHAPTER_PATTERN = r"\(?(\d{1,2}):(\d{2})(?::\d{2})?\)?\s+(?:–|-)\s+([^0-9\(\)]*?)(?=\(?\d{1,2}:\d{2}|$)"


# #############################################################################
# Transcript Formatting Classes
# #############################################################################


class Chapter:
    """
    Represents a chapter in the transcript.
    """

    def __init__(self, *, timestamp: str, title: str) -> None:
        """
        Initialize a chapter.

        :param timestamp: chapter time in HH:MM or H:MM format
        :param title: chapter title
        """
        self.timestamp = timestamp
        self.title = title
        self.seconds = self._parse_timestamp(timestamp)

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


class DialogueLine:
    """
    Represents a single speaker's dialogue.
    """

    def __init__(
        self, *, speaker: str, timestamp: str, text: str
    ) -> None:
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

        Tries multiple strategies: pattern matching for common formats, then
        falls back to the first non-empty, non-metadata line. Returns a generic
        default if no title is found.

        :return: episode title
        """
        full_text = " ".join(self.lines)
        # Try multiple regex patterns that commonly appear in transcripts.
        patterns = [
            r'"([^"]+)".*?explains',
            r"[—-]\s*([^\"]+?)\s*\"",
            r"This is a transcript of.*?with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                title = match.group(1).strip()
                if len(title) > 3:
                    return title
        # Fall back to the first non-metadata line in the transcript.
        for line in self.lines:
            line = line.strip()
            if line and not line.startswith(("The timestamps", "Playback", "×")):
                return line
        return "Podcast Transcript"

    def extract_chapters(self) -> List[Chapter]:
        """
        Extract chapters from transcript table of contents.

        Searches for a Table of Contents or Timestamps section, then parses
        timestamps and chapter titles using the _CHAPTER_PATTERN regex.

        :return: list of Chapter objects (empty list if no TOC found)
        """
        chapters = []
        full_text = " ".join(self.lines)
        # Find the TOC/Timestamps section bounded by common headers.
        toc_match = re.search(
            r"(?:Table of Contents|Timestamps)(.*?)(?:Episode|Transcript|$)",
            full_text,
            re.IGNORECASE,
        )
        if toc_match:
            toc_text = toc_match.group(1)
        else:
            toc_text = ""
        # Parse chapter entries from the TOC using the chapter pattern.
        for match in re.finditer(_CHAPTER_PATTERN, toc_text):
            hours = match.group(1)
            minutes = match.group(2)
            title = match.group(3).strip()
            timestamp = f"{hours}:{minutes}"
            chapters.append(Chapter(timestamp=timestamp, title=title))
        return chapters

    def extract_dialogue(self) -> List[DialogueLine]:
        """
        Extract all dialogue lines from transcript.

        Tries the line-separated format first, then falls back to concatenated
        format if needed. Results are sorted by timestamp for proper playback order.

        :return: list of DialogueLine objects, sorted by timestamp (seconds)
        """
        dialogue_lines = []
        # Try parsing line-separated format (Speaker(HH:MM:SS)text).
        dialogue_lines.extend(self._extract_dialogue_line_format())
        # Fall back to concatenated format if no lines were found.
        if not dialogue_lines:
            dialogue_lines.extend(self._extract_dialogue_concat_format())
        dialogue_lines.sort(key=lambda d: d.seconds)
        return dialogue_lines

    def _extract_dialogue_line_format(self) -> List[DialogueLine]:
        """
        Extract dialogue from line-separated format: Speaker(HH:MM:SS)text.

        Matches lines with a speaker name, timestamp in parentheses, and dialogue
        text. Validates that speakers have exactly two capitalized name parts.

        :return: list of DialogueLine objects
        """
        dialogue_lines = []
        for line in self.lines:
            line = line.strip()
            if not line:
                continue
            match = re.match(_SPEAKER_TIMESTAMP_PATTERN, line)
            if match:
                speaker = match.group(1).strip()
                hours = match.group(2)
                minutes = match.group(3)
                seconds = match.group(4)
                timestamp = f"{hours}:{minutes}:{seconds}"
                text_start = match.end()
                text = line[text_start:].strip()
                # Validate speaker name: exactly 2 words, each capitalized.
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

        Matches speaker-timestamp pairs and extracts text between consecutive
        matches. Used as a fallback when line-separated format is not found.

        :return: list of DialogueLine objects
        """
        dialogue_lines = []
        full_text = " ".join(self.lines)
        # Find all speaker-timestamp matches in the concatenated text.
        matches = list(
            re.finditer(_SPEAKER_TIMESTAMP_ALT_PATTERN, full_text)
        )
        # Extract dialogue text between each speaker marker and the next.
        for i, match in enumerate(matches):
            speaker = match.group(1).strip()
            hours = match.group(2)
            minutes = match.group(3)
            seconds = match.group(4)
            timestamp = f"{hours}:{minutes}:{seconds}"
            text_start = match.end()
            if i + 1 < len(matches):
                text_end = matches[i + 1].start()
                text = full_text[text_start:text_end].strip()
            else:
                text = full_text[text_start:].strip()
            if text:
                dialogue_lines.append(
                    DialogueLine(
                        speaker=speaker,
                        timestamp=timestamp,
                        text=text,
                    )
                )
        return dialogue_lines


class MarkdownFormatter:
    """
    Format transcript data into markdown.
    """

    def __init__(self) -> None:
        """
        Initialize the formatter.
        """
        self.speaker_abbrevs: Dict[str, str] = {}

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

        Creates a markdown document with title, source URL, chapter headers
        (inserted where dialogue timestamps align), and abbreviated speaker
        dialogue lines.

        :param title: episode title
        :param url: original URL
        :param chapters: list of chapters (sorted by timestamp)
        :param dialogue: list of dialogue lines (sorted by timestamp)
        :return: formatted markdown string
        """
        # Build speaker abbreviation map first.
        for line in dialogue:
            self._add_speaker(line.speaker)
        output = []
        output.append(f"# {title}\n")
        output.append(f"// Link: {url}\n")
        # Insert chapter headers at appropriate dialogue positions.
        chapter_idx = 0
        for dialogue_line in dialogue:
            if chapter_idx < len(chapters):
                chapter = chapters[chapter_idx]
                if dialogue_line.seconds >= chapter.seconds:
                    output.append(
                        f"\n## {chapter.title} ({chapter.timestamp})\n"
                    )
                    chapter_idx += 1
            abbrev = self.speaker_abbrevs[dialogue_line.speaker]
            output.append(f"{abbrev}: {dialogue_line.text}\n")
        return "".join(output)

    def _add_speaker(self, speaker: str) -> None:
        """
        Add speaker to abbreviation map.

        :param speaker: full speaker name
        """
        if speaker in self.speaker_abbrevs:
            return
        parts = speaker.split()
        abbrev = "".join(p[0] for p in parts).upper()
        if not abbrev:
            abbrev = speaker[:2].upper()
        self.speaker_abbrevs[speaker] = abbrev


# #############################################################################
# Factory
# #############################################################################


def _get_downloader(
    downloader_type: str, *, slug: str
) -> PodcastDownloader:
    """
    Create a downloader instance based on the specified type.

    :param downloader_type: the downloader type (e.g., 'lexfriedman')
    :param slug: the podcast slug
    :return: PodcastDownloader instance
    """
    hdbg.dassert_in(
        downloader_type,
        _VALID_TYPES,
        "Invalid downloader type: %s. Valid types: %s",
        downloader_type,
        ", ".join(_VALID_TYPES),
    )
    downloader_map = {
        "lexfriedman": LexFriedmanDownloader,
        "dwarkesh": DwarkeshDownloader,
        "podcasttranscript_ai": PodcastTranscriptDownloader,
        "podscripts_co": PodscriptsDownloader,
    }
    downloader_class = downloader_map[downloader_type]
    return downloader_class(slug=slug)


# #############################################################################
# Script
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: configured ArgumentParser with all action-specific options
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    parser.add_argument(
        "--type",
        action="store",
        default=None,
        choices=_VALID_TYPES,
        help="The podcast source type (required for download/all)",
    )
    parser.add_argument(
        "--title",
        action="store",
        default=None,
        help="The podcast slug/identifier (required for download/all)",
    )
    parser.add_argument(
        "--transcript",
        action="store",
        default=None,
        help="Path to raw transcript file (required for format)",
    )
    parser.add_argument(
        "--url",
        action="store",
        default=None,
        help="Original podcast URL (required for format, auto-derived for all)",
    )
    parser.add_argument(
        "--output",
        action="store",
        default=None,
        help="Output markdown file path (required for format/all)",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        default=".",
        help="Output directory for transcript files",
    )
    parser.add_argument(
        "--run_lint",
        action="store_true",
        help="Run lint_txt.py on formatted output",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _run_download(args: argparse.Namespace) -> None:
    """
    Download transcript from a podcast source and save to disk.

    :param args: parsed command-line arguments with type, title, output_dir
    :raises AssertionError: if required args (type, title) are missing
    """
    hdbg.dassert_is_not(
        args.type,
        None,
        "--type is required for download action",
    )
    hdbg.dassert_is_not(
        args.title,
        None,
        "--title is required for download action",
    )
    hio.create_dir(args.output_dir, incremental=True)
    downloader = _get_downloader(args.type, slug=args.title)
    _LOG.info("Downloading transcript from: %s", args.type)
    transcript, output_filename = downloader.download()
    output_path = f"{args.output_dir}/{output_filename}"
    _LOG.info("Writing transcript to: %s", output_path)
    hio.to_file(output_path, transcript)
    _LOG.info("Transcript saved successfully")


def _run_format(args: argparse.Namespace) -> None:
    """
    Parse a raw transcript and format it as markdown with chapters and speakers.

    :param args: parsed command-line arguments with transcript, url, output
    :raises AssertionError: if required args (transcript, url, output) are missing
    """
    hdbg.dassert_is_not(
        args.transcript,
        None,
        "--transcript is required for format action",
    )
    hdbg.dassert_is_not(
        args.url,
        None,
        "--url is required for format action",
    )
    hdbg.dassert_is_not(
        args.output,
        None,
        "--output is required for format action",
    )
    _LOG.info("Reading transcript from: %s", args.transcript)
    hdbg.dassert_file_exists(args.transcript)
    transcript_text = hio.from_file(args.transcript)
    _LOG.info("Parsing transcript")
    parser_obj = TranscriptParser(transcript_text=transcript_text)
    title = parser_obj.extract_title()
    _LOG.debug("Extracted title: %s", title)
    chapters = parser_obj.extract_chapters()
    _LOG.info("Extracted %d chapters", len(chapters))
    dialogue = parser_obj.extract_dialogue()
    _LOG.info("Extracted %d dialogue lines", len(dialogue))
    _LOG.info("Formatting as markdown")
    formatter = MarkdownFormatter()
    markdown = formatter.format(
        title=title, url=args.url, chapters=chapters, dialogue=dialogue
    )
    _LOG.info("Writing markdown to: %s", args.output)
    hio.to_file(args.output, markdown)
    _LOG.info("Markdown file created successfully")
    if args.run_lint:
        _LOG.info("Running lint_txt.py on output")
        cmd = f"lint_txt.py -i {args.output}"
        hsystem.system(cmd)
        _LOG.info("Linting complete")


def _run_download_and_format(args: argparse.Namespace) -> None:
    """
    Download a podcast transcript and immediately format it as markdown.

    Combines download and format actions in a single operation, deriving the URL
    from the downloader instance. Saves both raw and formatted files to disk.

    :param args: parsed command-line arguments with type, title, output, output_dir
    :raises AssertionError: if required args (type, title, output) are missing
    """
    hdbg.dassert_is_not(
        args.type,
        None,
        "--type is required for all action",
    )
    hdbg.dassert_is_not(
        args.title,
        None,
        "--title is required for all action",
    )
    hdbg.dassert_is_not(
        args.output,
        None,
        "--output is required for all action",
    )
    hio.create_dir(args.output_dir, incremental=True)
    downloader = _get_downloader(args.type, slug=args.title)
    _LOG.info("Downloading transcript from: %s", args.type)
    transcript, output_filename = downloader.download()
    url = downloader._get_url()
    raw_path = f"{args.output_dir}/{output_filename}"
    _LOG.info("Writing raw transcript to: %s", raw_path)
    hio.to_file(raw_path, transcript)
    _LOG.info("Parsing transcript")
    parser_obj = TranscriptParser(transcript_text=transcript)
    title = parser_obj.extract_title()
    _LOG.debug("Extracted title: %s", title)
    chapters = parser_obj.extract_chapters()
    _LOG.info("Extracted %d chapters", len(chapters))
    dialogue = parser_obj.extract_dialogue()
    _LOG.info("Extracted %d dialogue lines", len(dialogue))
    _LOG.info("Formatting as markdown")
    formatter = MarkdownFormatter()
    markdown = formatter.format(
        title=title, url=url, chapters=chapters, dialogue=dialogue
    )
    _LOG.info("Writing markdown to: %s", args.output)
    hio.to_file(args.output, markdown)
    _LOG.info("Markdown file created successfully")
    if args.run_lint:
        _LOG.info("Running lint_txt.py on output")
        cmd = f"lint_txt.py -i {args.output}"
        hsystem.system(cmd)
        _LOG.info("Linting complete")


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point: parse arguments, select actions, and execute.

    :param parser: the configured ArgumentParser instance
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Select which action(s) to run; defaults to 'all' if none specified.
    actions = hparser.select_actions(
        args, _VALID_ACTIONS, _DEFAULT_ACTIONS
    )
    _LOG.info(
        hparser.actions_to_string(actions, _VALID_ACTIONS, add_frame=True)
    )
    # Execute each selected action in sequence.
    for action in actions:
        if action == "download":
            _run_download(args)
        elif action == "format":
            _run_format(args)
        elif action == "all":
            _run_download_and_format(args)


if __name__ == "__main__":
    _main(_parse())
