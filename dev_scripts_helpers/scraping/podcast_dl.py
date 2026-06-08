#!/usr/bin/env -S uv run

# /// script
# dependencies = ["requests", "beautifulsoup4", "tqdm"]
# ///

"""
Download and format podcast transcripts from various sources.

Default behavior runs download, format, and lint in sequence. Each step generates
a numbered file in the <OUTPUT>.md.tmp/ directory, and the final result is copied
to <OUTPUT>.md.

Actions:
- download: fetch transcript from a podcast site (01.download.txt)
- format: convert raw transcript to formatted markdown (02.format.txt)
- lint: run lint_txt.py on formatted markdown (03.lint.txt)

Examples:
# Default: download, format, and lint a Lex Fridman episode
> ./podcast_dl.py --type lexfridman --title lars-brownworth --output ./podcasts/lars-brownworth.md

# Download only
> ./podcast_dl.py -a download --type lexfridman --title lars-brownworth --output ./podcasts/lars-brownworth.md

# Download and format (skip linting)
> ./podcast_dl.py -a download -a format --type dwarkesh --title andrej-karpathy --output ./podcasts/andrej-karpathy.md
"""

# Architecture:
# - `PodcastDownloader`: Abstract base class defining interface for downloading
#   transcripts from different podcast sources
#   - Concrete implementations (`LexFridmanDownloader`, `DwarkeshDownloader`,
#     etc.) extract transcript and metadata from site-specific HTML.
# - `TranscriptParser`: Extracts structured content (title, chapters, dialogue)
#   from raw transcript text using regex patterns.
# - `MarkdownFormatter`: Converts parsed transcript data into formatted markdown
#   with chapter sections and speaker abbreviations.
# - `Factory`: Creates appropriate downloader instance based on podcast type.

# https://lexfridman.com/lars-brownworth-transcript
# https://www.dwarkesh.com/p/andrej-karpathy
# https://podscripts.co/podcasts/no-priors-artificial-intelligence-technology-startups/andrej-karpathy-on-code-agents-autoresearch-and-the-loopy-era-of-ai

# https://podcasttranscript.ai/library/andrej-karpathy-s-vision-of-software

import argparse
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import requests
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hlint as hlint
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hselect_action as hselacti

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_VALID_TYPES = [
    "lexfridman",
    "dwarkesh",
    "podcasttranscript_ai",
    "podscripts_co",
]

_VALID_ACTIONS = ["download", "format", "lint"]
_DEFAULT_ACTIONS = ["download", "format", "lint"]


# #############################################################################
# PodcastDownloader
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
    def _extract_metadata(self, html: str) -> Tuple[str, str, str]:
        """
        Extract metadata from HTML (date, podcast title, guest name).

        :param html: the HTML content of the podcast page
        :return: tuple of (date, podcast_title, guest_name)
        """
        pass

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

    def _normalize_filename(
        self,
        *,
        date: str,
        podcast_title: str,
        guest_name: str = "",
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
            filename = f"{date_str}_{podcast_normalized}_{guest_normalized}.txt"
        else:
            filename = f"{date_str}_{podcast_normalized}.txt"
        return filename

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


# #############################################################################
# LexFridmanDownloader
# #############################################################################


class LexFridmanDownloader(PodcastDownloader):
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

    def _extract_metadata(self, html: str) -> Tuple[str, str, str]:
        """
        Extract metadata from lexfridman.com HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        # Try to find the title (usually in h1 or meta tags).
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Lex Fridman"
        # Try to find the date in meta tags.
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag and isinstance(date_tag, Tag):
            date = str(date_tag.get("content", "unknown"))
        else:
            date = "unknown"
        # Extract guest name from title (usually "Guest Name - Lex Fridman #...").
        guest_name = ""
        if " - Lex" in title:
            guest_name = title.split(" - Lex")[0].strip()
        return date, "lex-fridman", guest_name


# #############################################################################
# DwarkeshDownloader
# #############################################################################


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
        content: Any = soup.find("div", class_=re.compile(r"post", re.I))
        if not content:
            content = soup.find("article")
        if not content:
            hdbg.dfatal("Could not find transcript content in HTML")
        # Extract text, handling blockquotes and paragraphs.
        lines = []
        for elem in content.find_all(["p", "blockquote"]):
            text = elem.get_text(strip=True)
            if text and len(text) > 10:
                lines.append(text)
        transcript = "\n\n".join(lines)
        return transcript

    def _extract_metadata(self, html: str) -> Tuple[str, str, str]:
        """
        Extract metadata from dwarkesh.com HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        # Extract title from h1 or meta tags.
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Dwarkesh"
        # Extract date from meta tags or byline.
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag and isinstance(date_tag, Tag):
            date = str(date_tag.get("content", "unknown"))
        else:
            date = "unknown"
        guest_name = title if title != "Dwarkesh" else ""
        return date, "dwarkesh", guest_name


# #############################################################################
# PodcastTranscriptDownloader
# #############################################################################


class PodcastTranscriptDownloader(PodcastDownloader):
    """
    Download transcripts from podcasttranscript.ai.
    """

    def _get_url(self) -> str:
        """
        Get the podcasttranscript.ai transcript URL.

        :return: the full URL
        """
        return f"https://podcasttranscript.ai/library/{self._slug}"

    def _extract_transcript(self, html: str) -> str:
        """
        Extract transcript from podcasttranscript.ai HTML.

        :param html: the HTML content
        :return: transcript text
        """
        soup = BeautifulSoup(html, "html.parser")
        # Find transcript container.
        content: Any = soup.find(
            "div", class_=re.compile(r"transcript|content", re.I)
        )
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

    def _extract_metadata(self, html: str) -> Tuple[str, str, str]:
        """
        Extract metadata from podcasttranscript.ai HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("h1")
        title = (
            title_tag.get_text(strip=True) if title_tag else "Podcast Transcript"
        )
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag and isinstance(date_tag, Tag):
            date = str(date_tag.get("content", "unknown"))
        else:
            date = "unknown"
        return date, "podcast-transcript", title


# #############################################################################
# PodscriptsDownloader
# #############################################################################


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
        # Find transcript container.
        content: Any = soup.find("div", class_=re.compile(r"transcript", re.I))
        if not content:
            content = soup.find("main")
        if not content:
            hdbg.dfatal("Could not find transcript content in HTML")
        # Extract from single-sentence divs (podscripts.co format).
        lines = []
        for elem in content.find_all("div", class_="single-sentence"):
            text = elem.get_text(strip=True)
            if text:
                lines.append(text)
        # If no single-sentence divs, fall back to paragraphs/divs.
        if not lines:
            for elem in content.find_all(["p", "div"]):
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    lines.append(text)
        transcript = "\n".join(lines)
        return transcript

    def _extract_metadata(self, html: str) -> Tuple[str, str, str]:
        """
        Extract metadata from podscripts.co HTML.

        :param html: the HTML content
        :return: tuple of (date, podcast_title, guest_name)
        """
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Podscripts"
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
_SPEAKER_TIMESTAMP_ALT_PATTERN = (
    r"([A-Z][a-z]+(?: [A-Z][a-z]+)*)(\d{2}):(\d{2}):(\d{2})"
)
_CHAPTER_PATTERN = r"\(?(\d{1,2}):(\d{2})(?::\d{2})?\)?\s+(?:–|-)\s+([^0-9\(\)]*?)(?=\(?\d{1,2}:\d{2}|$)"


# #############################################################################
# Chapter
# #############################################################################


class Chapter:
    """
    Represents a chapter in the transcript.
    """

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
        # Test patterns with progress tracking.
        for pattern in tqdm(
            patterns,
            desc="Testing title patterns",
            unit="pattern",
        ):
            match = re.search(pattern, full_text)
            if match:
                title = match.group(1).strip()
                if len(title) > 3:
                    return title
        # Fall back to the first non-metadata line in the transcript.
        for line in tqdm(
            self.lines,
            desc="Searching for title in lines",
            unit="line",
        ):
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
        # Join transcript lines with progress tracking.
        full_text = " ".join(
            tqdm(
                self.lines,
                desc="Preparing chapter extraction",
                unit="line",
            )
        )
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
        # Parse chapter entries from the TOC with progress tracking.
        matches = list(re.finditer(_CHAPTER_PATTERN, toc_text))
        for match in tqdm(matches, desc="Extracting chapters", unit="chapter"):
            hours = match.group(1)
            minutes = match.group(2)
            title = match.group(3).strip()
            timestamp = f"{hours}:{minutes}"
            chapters.append(Chapter(timestamp=timestamp, title=title))
        return chapters

    def _extract_dialogue_line_format(self) -> List[DialogueLine]:
        """
        Extract dialogue from line-separated format: Speaker(HH:MM:SS)text.

        Matches lines with a speaker name, timestamp in parentheses, and dialogue
        text. Validates that speakers have exactly two capitalized name parts.

        :return: list of DialogueLine objects
        """
        dialogue_lines = []
        # Parse dialogue lines with progress bar to track processing.
        for line in tqdm(self.lines, desc="Extracting dialogue", unit="line"):
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
        # Find all speaker-timestamp matches in the concatenated text with progress.
        matches = list(
            tqdm(
                re.finditer(_SPEAKER_TIMESTAMP_ALT_PATTERN, full_text),
                desc="Finding dialogue matches",
                unit="match",
            )
        )
        # Extract dialogue text between each speaker marker with progress tracking.
        for i, match in enumerate(
            tqdm(
                matches,
                desc="Processing dialogue matches",
                unit="match",
            )
        ):
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

    def _extract_dialogue_podscripts_format(self) -> List[DialogueLine]:
        """
        Extract dialogue from podscripts.co format: Starting point is HH:MM:SS text.

        This format doesn't include speaker labels, so speakers are alternated
        as Speaker1, Speaker2, etc. based on chronological order.

        :return: list of DialogueLine objects
        """
        dialogue_lines = []
        full_text = " ".join(self.lines)
        # Match "Starting point is HH:MM:SS" followed by text.
        pattern = r"Starting point is (\d{2}):(\d{2}):(\d{2})(.+?)(?=Starting point is|$)"
        matches = list(
            tqdm(
                re.finditer(pattern, full_text, re.DOTALL),
                desc="Extracting podscripts dialogue",
                unit="match",
            )
        )
        # Generate generic speakers (Speaker1, Speaker2) alternating.
        speaker_names = ["Speaker1", "Speaker2"]
        for i, match in enumerate(
            tqdm(
                matches,
                desc="Processing podscripts dialogue",
                unit="match",
            )
        ):
            hours = match.group(1)
            minutes = match.group(2)
            seconds = match.group(3)
            timestamp = f"{hours}:{minutes}:{seconds}"
            text = match.group(4).strip()
            if text:
                speaker = speaker_names[i % 2]
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
        # Fall back to podscripts format (Starting point is HH:MM:SS text).
        if not dialogue_lines:
            dialogue_lines.extend(self._extract_dialogue_podscripts_format())
        # Sort dialogue lines by timestamp with progress tracking.
        dialogue_lines = list(
            tqdm(
                sorted(dialogue_lines, key=lambda d: d.seconds),
                desc="Sorting dialogue by timestamp",
                unit="line",
            )
        )
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
        parts = speaker.split()
        abbrev = "".join(p[0] for p in parts).upper()
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

        Creates a markdown document with title, source URL, chapter headers
        (inserted where dialogue timestamps align), and abbreviated speaker
        dialogue lines with bullet points.

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
        if url:
            output.append(f"- Link: {url}\n")
        # Insert chapter headers at appropriate dialogue positions.
        chapter_idx = 0
        for dialogue_line in dialogue:
            # Insert all chapters that should appear before this dialogue line.
            while (
                chapter_idx < len(chapters)
                and dialogue_line.seconds >= chapters[chapter_idx].seconds
            ):
                chapter = chapters[chapter_idx]
                output.append(f"\n## {chapter.title} ({chapter.timestamp})\n")
                chapter_idx += 1
            abbrev = self.speaker_abbrevs[dialogue_line.speaker]
            output.append(f"- {abbrev}: {dialogue_line.text}\n")
        return "".join(output)


# #############################################################################
# Factory
# #############################################################################


def _get_downloader(downloader_type: str, *, slug: str) -> PodcastDownloader:
    """
    Create a downloader instance based on the specified type.

    :param downloader_type: the downloader type (e.g., 'lexfridman')
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
        "lexfridman": LexFridmanDownloader,
        "dwarkesh": DwarkeshDownloader,
        "podcasttranscript_ai": PodcastTranscriptDownloader,
        "podscripts_co": PodscriptsDownloader,
    }
    downloader_class = downloader_map[downloader_type]
    return downloader_class(slug=slug)


# #############################################################################
# Script
# #############################################################################


def _get_temp_dir(output_path: str) -> str:
    """
    Derive the temporary directory path from the output file path.

    For example:
    - ./transcripts/podcast.md -> ./transcripts/podcast.md.tmp

    :param output_path: path to the output markdown file
    :return: path to the temporary directory for intermediate files
    """
    return f"{output_path}.tmp"


def _get_step_file(output_path: str, step_num: int, step_name: str) -> str:
    """
    Get the path to a step's output file in the tmp directory.

    For example:
    - output_path="./podcast.md", step_num=1, step_name="download"
      -> ./podcast.md.tmp/01.download.txt

    :param output_path: path to the final output markdown file
    :param step_num: step number (1-based)
    :param step_name: name of the step (download, format, lint)
    :return: path to the step's output file
    """
    temp_dir = _get_temp_dir(output_path)
    return f"{temp_dir}/{step_num:02d}.{step_name}.txt"


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: configured ArgumentParser with all action-specific options
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    parser.add_argument(
        "--type",
        action="store",
        default="",
        choices=_VALID_TYPES,
        help="The podcast source type (required for download/all)",
    )
    parser.add_argument(
        "--title",
        action="store",
        default="",
        help="The podcast slug/identifier (required for download/all)",
    )
    parser.add_argument(
        "--transcript",
        action="store",
        default="",
        help="Path to raw transcript file (required for format)",
    )
    parser.add_argument(
        "--url",
        action="store",
        default="",
        help="Original podcast URL (required for format, auto-derived for all)",
    )
    parser.add_argument(
        "--output",
        action="store",
        default="",
        help="Output markdown file path (required for download/format/all). Intermediate files saved to <OUTPUT>.tmp/",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _run_download(args: argparse.Namespace) -> None:
    """
    Download transcript from a podcast source and save to 01.download.txt.

    :param args: parsed command-line arguments with type, title, output
    :raises AssertionError: if required args (type, title, output) are missing
    """
    hdbg.dassert_ne(
        args.type,
        "",
        "--type is required for download action",
    )
    hdbg.dassert_ne(
        args.title,
        "",
        "--title is required for download action",
    )
    hdbg.dassert_ne(
        args.output,
        "",
        "--output is required for download action",
    )
    temp_dir = _get_temp_dir(args.output)
    hio.create_dir(temp_dir, incremental=True)
    hio.create_enclosing_dir(args.output, incremental=True)
    downloader = _get_downloader(args.type, slug=args.title)
    _LOG.info("Downloading transcript from: %s", args.type)
    transcript, _ = downloader.download()
    step_file = _get_step_file(args.output, 1, "download")
    _LOG.info("Writing raw transcript to: %s", step_file)
    hio.to_file(step_file, transcript)
    # Store the URL for use in the format step.
    url = downloader._get_url()
    url_file = _get_step_file(args.output, 0, "url")
    _LOG.info("Writing URL to: %s", url_file)
    hio.to_file(url_file, url)
    _LOG.info("Transcript downloaded successfully")


def _run_format(args: argparse.Namespace) -> None:
    """
    Parse raw transcript from 01.download.txt and format as markdown to 02.format.txt.

    :param args: parsed command-line arguments with output
    :raises AssertionError: if required arg (output) is missing
    """
    hdbg.dassert_ne(
        args.output,
        "",
        "--output is required for format action",
    )
    # Read from the download step's output
    download_file = _get_step_file(args.output, 1, "download")
    hdbg.dassert_file_exists(download_file)
    _LOG.info("Reading transcript from: %s", download_file)
    transcript_text = hio.from_file(download_file)
    # Try to read URL from download step; fall back to args.url or empty string.
    url = ""
    url_file = _get_step_file(args.output, 0, "url")
    if os.path.exists(url_file):
        url = hio.from_file(url_file).strip()
    if not url and args.url:
        url = args.url
    _LOG.info("Parsing transcript")
    parser_obj = TranscriptParser(transcript_text=transcript_text)
    # Track overall parsing progress with a progress bar.
    with tqdm(total=2, desc="Overall parsing", unit="step") as pbar:
        chapters = parser_obj.extract_chapters()
        _LOG.info("Extracted %d chapters", len(chapters))
        pbar.update(1)
        dialogue = parser_obj.extract_dialogue()
        _LOG.info("Extracted %d dialogue lines", len(dialogue))
        pbar.update(1)
    # Use default title instead of parsing from transcript.
    title = "Transcript"
    _LOG.info("Formatting as markdown")
    formatter = MarkdownFormatter()
    markdown = formatter.format(
        title=title, url=url, chapters=chapters, dialogue=dialogue
    )
    format_file = _get_step_file(args.output, 2, "format")
    _LOG.info("Writing formatted markdown to: %s", format_file)
    hio.to_file(format_file, markdown)
    _LOG.info("Format step completed successfully")


def _run_lint(args: argparse.Namespace) -> None:
    """
    Lint formatted markdown from 02.format.txt and save to 03.lint.txt.

    :param args: parsed command-line arguments with output
    :raises AssertionError: if required arg (output) is missing
    """
    hdbg.dassert_ne(
        args.output,
        "",
        "--output is required for lint action",
    )
    # Read from the format step's output
    format_file = _get_step_file(args.output, 2, "format")
    hdbg.dassert_file_exists(format_file)
    lint_file = _get_step_file(args.output, 3, "lint")
    _LOG.info("Linting markdown file: %s", format_file)
    # Copy to lint file and apply linting.
    hio.to_file(lint_file, hio.from_file(format_file))
    hlint.lint_file(lint_file)
    _LOG.info("Lint step completed successfully")


def _finalize_output(args: argparse.Namespace, last_step: int) -> None:
    """
    Copy the final output from the last step file to the output file.

    Determines which step file to copy based on the actions executed:
    - Step 1 (download): 01.download.txt
    - Step 2 (format): 02.format.txt
    - Step 3 (lint): 03.lint.txt

    :param args: parsed command-line arguments with output
    :param last_step: the number of the last step executed (1, 2, or 3)
    """
    step_names = {1: "download", 2: "format", 3: "lint"}
    source_file = _get_step_file(args.output, last_step, step_names[last_step])
    hdbg.dassert_file_exists(source_file)
    _LOG.info("Copying %s to final output: %s", source_file, args.output)
    import shutil

    shutil.copy(source_file, args.output)
    _LOG.info("Output file created successfully: %s", args.output)


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point: parse arguments, select actions, and execute.

    Default actions are download, format, and lint. Each action generates a
    numbered file in <OUTPUT>.md.tmp/, and the final result is copied to
    <OUTPUT>.md.

    :param parser: the configured ArgumentParser instance
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Select which action(s) to run; defaults to download, format, lint.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info(
        hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True)
    )
    # Track which step was last executed for finalization
    last_step = 0
    # Execute each selected action in sequence.
    for action in actions:
        if action == "download":
            _run_download(args)
            last_step = 1
        elif action == "format":
            _run_format(args)
            last_step = 2
        elif action == "lint":
            _run_lint(args)
            last_step = 3
    # Copy the final output file
    if last_step > 0:
        _finalize_output(args, last_step)


if __name__ == "__main__":
    _main(_parse())
