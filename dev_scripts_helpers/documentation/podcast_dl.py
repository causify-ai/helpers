#!/usr/bin/env -S uv run

# /// script
# dependencies = ["requests", "beautifulsoup4"]
# ///

"""
Download podcast transcripts from various sources.

Examples:
# Download a Lex Fridman episode
> ./podcast_dl.py --type lexfriedman --title lars-brownworth --output_dir ./transcripts

# Download a Dwarkesh episode
> ./podcast_dl.py --type dwarkesh --title andrej-karpathy

# Download from PodcastTranscript.ai
> ./podcast_dl.py --type podcasttranscript_ai --title andrej-karpathy-s-vision-of-software

# Download from Podscripts
> ./podcast_dl.py --type podscripts_co --title andrej-karpathy-on-code-agents-autoresearch-and-the-loopy-era-of-ai
"""

import argparse
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

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

        :param date: the episode date (will be parsed for YYYY-MM-DD format)
        :param podcast_title: the podcast name
        :param guest_name: optional guest name
        :return: normalized filename
        """
        # Extract YYYY-MM-DD format from date string.
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", date)
        if date_match:
            date_str = date_match.group()
        else:
            date_str = "unknown-date"
        # Normalize podcast title to lowercase with hyphens.
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

        :param text: the text to slugify
        :return: slugified text
        """
        # Convert to lowercase and replace spaces with hyphens.
        text = text.lower()
        text = re.sub(r"\s+", "-", text)
        # Remove non-alphanumeric chars except hyphens.
        text = re.sub(r"[^a-z0-9-]", "", text)
        # Remove consecutive hyphens.
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
        # Extract guest name from title (usually "Guest Name - Lex Fridman #...")
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
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--type",
        action="store",
        required=True,
        choices=_VALID_TYPES,
        help="The podcast source type",
    )
    parser.add_argument(
        "--title",
        action="store",
        required=True,
        help="The podcast slug/identifier (e.g., lars-brownworth)",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        default=".",
        help="Output directory for the transcript file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate output directory.
    hio.create_dir(args.output_dir, incremental=True)
    # Create downloader and fetch transcript.
    downloader = _get_downloader(args.type, slug=args.title)
    _LOG.info("Downloading transcript from: %s", args.type)
    transcript, output_filename = downloader.download()
    # Write transcript to file.
    output_path = f"{args.output_dir}/{output_filename}"
    _LOG.info("Writing transcript to: %s", output_path)
    with open(output_path, "w") as f:
        f.write(transcript)
    _LOG.info("Transcript saved successfully")


if __name__ == "__main__":
    _main(_parse())
