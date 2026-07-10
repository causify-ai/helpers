import hashlib
import logging
import os
from typing import List
from unittest import mock

import pytest

import dev_scripts_helpers.documentation.piper_markdown_reader as dshdpmare
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__extract_markdown_section
# #############################################################################


class Test__extract_markdown_section(hunitest.TestCase):
    """
    Test _extract_markdown_section function.
    """

    def _create_input_file(self) -> str:
        """
        Create a test markdown input file and return its path.

        :return: path to created input file
        """
        content = """
        # Introduction

        This is the introduction section.

        ## Background

        Some background information.

        # Methods

        ## Data Collection

        How we collected data.

        ### Sampling Strategy

        Details about sampling.

        # Results

        Our findings.
        """
        content = hprint.dedent(content)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, content)
        return in_file

    def test1(self) -> None:
        """
        Test extracting section between two headers.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Methods

        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(
            in_file, "# Methods", "# Results"
        )
        # Check outputs.
        self.assert_equal(result, expected)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level (implicit end).
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Methods

        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(in_file, "# Methods", "")
        # Check outputs.
        self.assert_equal(result, expected)

    def test3(self) -> None:
        """
        Test error when start header not found.
        """
        in_file = self._create_input_file()
        with self.assertRaises(Exception):
            dshdpmare._extract_markdown_section(in_file, "# Nonexistent", "")

    def test4(self) -> None:
        """
        Test extracting with partial header match.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Results
        Our findings
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(in_file, "Results", "")
        # Check outputs.
        self.assert_equal(result, expected)

    def test5(self) -> None:
        """
        Test extracting from header to end of file using "END" special value.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Methods

        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling

        # Results
        Our findings
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(in_file, "# Methods", "END")
        # Check outputs.
        self.assert_equal(result, expected)

    def test6(self) -> None:
        """
        Test extracting with "END" from nested header to file end.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs - should include everything from "Data Collection" to end.
        expected = """
        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling

        # Results
        Our findings
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(
            in_file, "Data Collection", "END"
        )
        # Check outputs.
        self.assert_equal(result, expected)

    @pytest.mark.slow
    def test7(self) -> None:
        """
        Test that intermediate file is created.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Run test.
        dshdpmare._extract_markdown_section(in_file, "# Methods", "# Results")
        # Check outputs.
        tmp_file = dshdpmare._TMP_EXTRACT_FILE
        self.assertTrue(
            os.path.exists(tmp_file),
            f"Intermediate file {tmp_file} was not created",
        )


# #############################################################################
# Test__read_markdown_file
# #############################################################################


class Test__read_markdown_file(hunitest.TestCase):
    """
    Test the _read_markdown_file() function.
    """

    def test1(self) -> None:
        """
        Test reading an existing markdown file returns its content.
        """
        # Prepare inputs.
        content = "# Title\n\nSome text.\n"
        file_path = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(file_path, content)
        # Prepare outputs.
        expected = content
        # Run test.
        actual = dshdpmare._read_markdown_file(file_path)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test reading a nonexistent file raises an assertion error.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "missing.md")
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdpmare._read_markdown_file(file_path)


# #############################################################################
# Test__split_by_first_level_bullets
# #############################################################################


class Test__split_by_first_level_bullets(hunitest.TestCase):
    """
    Test the _split_by_first_level_bullets() function.
    """

    def helper(self, text: str, expected: List[str]) -> None:
        """
        Test helper for _split_by_first_level_bullets().

        :param text: input text
        :param expected: expected list of sections
        """
        # Run test.
        actual = dshdpmare._split_by_first_level_bullets(text)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test text with no bullet points stays a single section.
        """
        # Prepare inputs.
        text = "Just some text.\nMore text."
        # Prepare outputs.
        expected = [text]
        # Run test.
        self.helper(text, expected)

    def test2(self) -> None:
        """
        Test text with multiple first-level bullets splits into sections.
        """
        # Prepare inputs.
        text = "Intro text.\n- First bullet.\n- Second bullet."
        # Prepare outputs.
        expected = ["Intro text.", "- First bullet.", "- Second bullet."]
        # Run test.
        self.helper(text, expected)

    def test3(self) -> None:
        """
        Test bullet continuation lines stay attached to their bullet.
        """
        # Prepare inputs.
        text = "- First bullet.\n  continued line.\n- Second bullet."
        # Prepare outputs.
        expected = [
            "- First bullet.\n  continued line.",
            "- Second bullet.",
        ]
        # Run test.
        self.helper(text, expected)

    def test4(self) -> None:
        """
        Test empty text returns a single empty section.
        """
        # Prepare inputs.
        text = ""
        # Prepare outputs.
        expected = [""]
        # Run test.
        self.helper(text, expected)

    def test5(self) -> None:
        """
        Test "*" bullets are also treated as first-level bullets.
        """
        # Prepare inputs.
        text = "* First bullet.\n* Second bullet."
        # Prepare outputs.
        expected = ["* First bullet.", "* Second bullet."]
        # Run test.
        self.helper(text, expected)


# #############################################################################
# Test__format_markdown
# #############################################################################


class Test__format_markdown(hunitest.TestCase):
    """
    Test the _format_markdown() function.
    """

    def helper(self, text: str, expected: str) -> None:
        """
        Test helper for _format_markdown().

        :param text: input markdown text
        :param expected: expected formatted text
        """
        # Run test.
        actual = dshdpmare._format_markdown(text)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test headers of different levels become period-terminated
        announcements.
        """
        # Prepare inputs.
        text = "# Title\n## Subtitle\n### Subsubtitle"
        # Prepare outputs.
        expected = "Title.\nSubtitle.\nSubsubtitle."
        # Run test.
        self.helper(text, expected)

    def test2(self) -> None:
        """
        Test bullet points become period-terminated sentences.
        """
        # Prepare inputs.
        text = "- First item\n* Second item"
        # Prepare outputs.
        expected = "First item.\nSecond item."
        # Run test.
        self.helper(text, expected)

    def test3(self) -> None:
        """
        Test blank lines are dropped from the output.
        """
        # Prepare inputs.
        text = "Line one.\n\nLine two."
        # Prepare outputs.
        expected = "Line one.\nLine two."
        # Run test.
        self.helper(text, expected)


# #############################################################################
# Test__clean_text
# #############################################################################


class Test__clean_text(hunitest.TestCase):
    """
    Test the _clean_text() function.
    """

    def helper(self, text: str, expected: str) -> None:
        """
        Test helper for _clean_text().

        :param text: input markdown text
        :param expected: expected cleaned text
        """
        # Run test.
        actual = dshdpmare._clean_text(text)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test bold and italic markers are stripped.
        """
        # Prepare inputs.
        text = "This is **bold** and *italic* and _also italic_ and __bold__."
        # Prepare outputs.
        expected = "This is bold and italic and also italic and bold."
        # Run test.
        self.helper(text, expected)

    def test2(self) -> None:
        """
        Test inline code markers and leading headers are stripped.
        """
        # Prepare inputs.
        text = "# Header\nUse `code` here."
        # Prepare outputs.
        expected = "Header\nUse code here."
        # Run test.
        self.helper(text, expected)

    def test3(self) -> None:
        """
        Test blank lines are dropped from the output.
        """
        # Prepare inputs.
        text = "Line one.\n\nLine two."
        # Prepare outputs.
        expected = "Line one.\nLine two."
        # Run test.
        self.helper(text, expected)


# #############################################################################
# Test__count_words
# #############################################################################


class Test__count_words(hunitest.TestCase):
    """
    Test the _count_words() function.
    """

    def test1(self) -> None:
        """
        Test counting words in a normal sentence.
        """
        # Prepare inputs.
        text = "This is a test sentence."
        # Prepare outputs.
        expected = 5
        # Run test.
        actual = dshdpmare._count_words(text)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test counting words in empty text returns zero.
        """
        # Prepare inputs.
        text = ""
        # Prepare outputs.
        expected = 0
        # Run test.
        actual = dshdpmare._count_words(text)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test__format_reading_time
# #############################################################################


class Test__format_reading_time(hunitest.TestCase):
    """
    Test the _format_reading_time() function.
    """

    def test1(self) -> None:
        """
        Test reading time under an hour is formatted in minutes.
        """
        # Prepare inputs.
        words = 300
        speed = 1.0
        # Prepare outputs.
        expected = "2.0m"
        # Run test.
        actual = dshdpmare._format_reading_time(words=words, speed=speed)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test reading time over an hour is formatted in hours.
        """
        # Prepare inputs.
        words = 150 * 60 * 2
        speed = 1.0
        # Prepare outputs.
        expected = "2.00h"
        # Run test.
        actual = dshdpmare._format_reading_time(words=words, speed=speed)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test higher speed reduces the reading time.
        """
        # Prepare inputs.
        words = 300
        speed = 2.0
        # Prepare outputs.
        expected = "1.0m"
        # Run test.
        actual = dshdpmare._format_reading_time(words=words, speed=speed)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test__chunk_text_by_length
# #############################################################################


class Test__chunk_text_by_length(hunitest.TestCase):
    """
    Test the _chunk_text_by_length() function.
    """

    def helper(self, text: str, max_length: int, expected: List[str]) -> None:
        """
        Test helper for _chunk_text_by_length().

        :param text: input text
        :param max_length: maximum length per chunk
        :param expected: expected list of chunks
        """
        # Run test.
        actual = dshdpmare._chunk_text_by_length(text, max_length=max_length)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test max_length of zero returns the text unchunked.
        """
        # Prepare inputs.
        text = "One. Two. Three."
        max_length = 0
        # Prepare outputs.
        expected = [text]
        # Run test.
        self.helper(text, max_length, expected)

    def test2(self) -> None:
        """
        Test sentences are packed together when they fit within
        max_length.
        """
        # Prepare inputs.
        text = "One. Two. Three."
        max_length = 100
        # Prepare outputs.
        expected = [text]
        # Run test.
        self.helper(text, max_length, expected)

    def test3(self) -> None:
        """
        Test sentences are split into separate chunks when they exceed
        max_length.
        """
        # Prepare inputs.
        text = "AAAAAAAAAA. BBBBBBBBBB."
        max_length = 12
        # Prepare outputs.
        expected = ["AAAAAAAAAA.", "BBBBBBBBBB."]
        # Run test.
        self.helper(text, max_length, expected)

    def test4(self) -> None:
        """
        Test a single sentence longer than max_length is broken into
        pieces.
        """
        # Prepare inputs.
        text = "A" * 25
        max_length = 10
        # Prepare outputs.
        expected = ["A" * 10, "A" * 10, "A" * 5]
        # Run test.
        self.helper(text, max_length, expected)


# #############################################################################
# Test__get_chunk_filename
# #############################################################################


class Test__get_chunk_filename(hunitest.TestCase):
    """
    Test the _get_chunk_filename() function.
    """

    def test1(self) -> None:
        """
        Test filename does not include a speed suffix at normal speed.
        """
        # Prepare inputs.
        chunk = "hello world"
        chunk_idx = 1
        speed = 1.0
        # Prepare outputs.
        sha1_hash = hashlib.sha1(chunk.encode()).hexdigest()
        expected = f"tmp.piper.chunk1.{sha1_hash}.wav"
        # Run test.
        actual = dshdpmare._get_chunk_filename(
            chunk, chunk_idx=chunk_idx, speed=speed
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test filename includes a speed suffix at non-default speed.
        """
        # Prepare inputs.
        chunk = "hello world"
        chunk_idx = 2
        speed = 1.5
        # Prepare outputs.
        sha1_hash = hashlib.sha1(chunk.encode()).hexdigest()
        expected = f"tmp.piper.chunk2.speed_1.5.{sha1_hash}.wav"
        # Run test.
        actual = dshdpmare._get_chunk_filename(
            chunk, chunk_idx=chunk_idx, speed=speed
        )
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test__get_voice_path
# #############################################################################


class Test__get_voice_path(hunitest.TestCase):
    """
    Test the _get_voice_path() function.
    """

    def test1(self) -> None:
        """
        Test the voice path is built under the piper voices directory.
        """
        # Prepare inputs.
        voice = "en_US-amy-medium"
        # Prepare outputs.
        expected = os.path.join(
            os.path.expanduser("~/.local/share/piper/voices"),
            "en_US-amy-medium.onnx",
        )
        # Run test.
        actual = dshdpmare._get_voice_path(voice)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test__generate_audio
# #############################################################################


class Test__generate_audio(hunitest.TestCase):
    """
    Test the _generate_audio() function.
    """

    def test1(self) -> None:
        """
        Test audio generation invokes piper via subprocess with the given
        text.
        """
        # Prepare inputs.
        text = "hello world"
        voice = "en_US-test-voice"
        speed = 1.0
        scratch_dir = self.get_scratch_space()
        voice_path = os.path.join(scratch_dir, f"{voice}.onnx")
        hio.to_file(voice_path, "fake voice model")
        output_file = os.path.join(scratch_dir, "output.wav")
        hio.to_file(output_file, "fake audio")
        mock_process = mock.MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        # Prepare outputs.
        expected_cmd = [
            "piper",
            "--model",
            voice_path,
            "--output_file",
            output_file,
        ]
        # Run test.
        with (
            mock.patch.object(
                dshdpmare, "_get_voice_path", return_value=voice_path
            ),
            mock.patch(
                "subprocess.Popen", return_value=mock_process
            ) as mock_popen,
        ):
            dshdpmare._generate_audio(
                text, voice=voice, speed=speed, output_file=output_file
            )
        # Check outputs.
        mock_process.communicate.assert_called_once_with(input=text, timeout=300)
        self.assertEqual(mock_popen.call_args.args[0], expected_cmd)

    def test2(self) -> None:
        """
        Test a nonzero piper return code raises an assertion error.
        """
        # Prepare inputs.
        text = "hello world"
        voice = "en_US-test-voice"
        speed = 1.0
        scratch_dir = self.get_scratch_space()
        voice_path = os.path.join(scratch_dir, f"{voice}.onnx")
        hio.to_file(voice_path, "fake voice model")
        output_file = os.path.join(scratch_dir, "output.wav")
        mock_process = mock.MagicMock()
        mock_process.communicate.return_value = ("", "piper error")
        mock_process.returncode = 1
        # Run test and check output.
        with (
            mock.patch.object(
                dshdpmare, "_get_voice_path", return_value=voice_path
            ),
            mock.patch("subprocess.Popen", return_value=mock_process),
        ):
            with self.assertRaises(AssertionError):
                dshdpmare._generate_audio(
                    text, voice=voice, speed=speed, output_file=output_file
                )


# #############################################################################
# Test__apply_speed_with_ffmpeg
# #############################################################################


class Test__apply_speed_with_ffmpeg(hunitest.TestCase):
    """
    Test the _apply_speed_with_ffmpeg() function.
    """

    def test1(self) -> None:
        """
        Test speed of 1.0 skips the ffmpeg call entirely.
        """
        # Prepare inputs.
        input_file = "input.wav"
        output_file = "output.wav"
        speed = 1.0
        # Run test.
        with mock.patch("subprocess.Popen") as mock_popen:
            dshdpmare._apply_speed_with_ffmpeg(
                input_file, output_file=output_file, speed=speed
            )
        # Check outputs.
        mock_popen.assert_not_called()

    def test2(self) -> None:
        """
        Test a non-default speed invokes ffmpeg and updates the progress
        bar.
        """
        # Prepare inputs.
        input_file = "input.wav"
        speed = 1.5
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "output.wav")
        hio.to_file(output_file, "fake audio")
        progress_bar = mock.MagicMock()
        mock_process = mock.MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        # Prepare outputs.
        expected_cmd = [
            "ffmpeg",
            "-i",
            input_file,
            "-filter:a",
            "atempo=1.5",
            "-acodec",
            "pcm_s16le",
            "-y",
            output_file,
        ]
        # Run test.
        with mock.patch(
            "subprocess.Popen", return_value=mock_process
        ) as mock_popen:
            dshdpmare._apply_speed_with_ffmpeg(
                input_file,
                output_file=output_file,
                speed=speed,
                progress_bar=progress_bar,
            )
        # Check outputs.
        self.assertEqual(mock_popen.call_args.args[0], expected_cmd)
        progress_bar.update.assert_called_once_with(1)

    def test3(self) -> None:
        """
        Test a nonzero ffmpeg return code raises an assertion error.
        """
        # Prepare inputs.
        input_file = "input.wav"
        speed = 2.0
        output_file = os.path.join(self.get_scratch_space(), "output.wav")
        mock_process = mock.MagicMock()
        mock_process.communicate.return_value = ("", "ffmpeg error")
        mock_process.returncode = 1
        # Run test and check output.
        with mock.patch("subprocess.Popen", return_value=mock_process):
            with self.assertRaises(AssertionError):
                dshdpmare._apply_speed_with_ffmpeg(
                    input_file, output_file=output_file, speed=speed
                )


# #############################################################################
# Test__process_sections_to_chunks
# #############################################################################


class Test__process_sections_to_chunks(hunitest.TestCase):
    """
    Test the _process_sections_to_chunks() function.
    """

    def test1(self) -> None:
        """
        Test sections are formatted and cleaned without chunking by
        length.
        """
        # Prepare inputs.
        sections = ["# Title\nSome content.", "- A bullet point"]
        max_length = 0
        # Prepare outputs.
        expected_chunks = ["Title.\nSome content.", "A bullet point."]
        expected_originals = sections
        # Run test.
        chunks, chunk_originals = dshdpmare._process_sections_to_chunks(
            sections, max_length=max_length
        )
        # Check outputs.
        self.assert_equal(str(chunks), str(expected_chunks))
        self.assert_equal(str(chunk_originals), str(expected_originals))

    def test2(self) -> None:
        """
        Test blank sections are skipped.
        """
        # Prepare inputs.
        sections = ["", "   ", "# Title\nBody text."]
        max_length = 0
        # Prepare outputs.
        expected_chunks = ["Title.\nBody text."]
        expected_originals = ["# Title\nBody text."]
        # Run test.
        chunks, chunk_originals = dshdpmare._process_sections_to_chunks(
            sections, max_length=max_length
        )
        # Check outputs.
        self.assert_equal(str(chunks), str(expected_chunks))
        self.assert_equal(str(chunk_originals), str(expected_originals))

    def test3(self) -> None:
        """
        Test max_length triggers multiple chunks per section, each mapped
        to the same original section.
        """
        # Prepare inputs.
        sections = ["AAAAAAAAAA. BBBBBBBBBB."]
        max_length = 12
        # Prepare outputs.
        expected_chunks = ["AAAAAAAAAA.", "BBBBBBBBBB."]
        expected_originals = [sections[0], sections[0]]
        # Run test.
        chunks, chunk_originals = dshdpmare._process_sections_to_chunks(
            sections, max_length=max_length
        )
        # Check outputs.
        self.assert_equal(str(chunks), str(expected_chunks))
        self.assert_equal(str(chunk_originals), str(expected_originals))


# #############################################################################
# Test__process_chunk_audio
# #############################################################################


class Test__process_chunk_audio(hunitest.TestCase):
    """
    Test the _process_chunk_audio() function.

    Chunk audio filenames are relative (no directory component), so each
    test changes into a fresh scratch directory for the duration of the
    call and restores the original working directory afterward.
    """

    def helper_chdir_to_scratch(self) -> str:
        """
        Change the working directory to a fresh scratch space.

        :return: path to the scratch directory
        """
        scratch_dir = self.get_scratch_space()
        os.chdir(scratch_dir)
        return scratch_dir

    def test1(self) -> None:
        """
        Test a new chunk at normal speed generates audio without calling
        ffmpeg.
        """
        # Prepare inputs.
        cwd = os.getcwd()
        self.helper_chdir_to_scratch()
        chunk_idx = 1
        chunk = "hello world"
        voice = "en_US-test-voice"
        speed = 1.0
        # Prepare outputs.
        expected = dshdpmare._get_chunk_filename(
            chunk, chunk_idx=chunk_idx, speed=1.0
        )
        # Run test.
        try:
            with (
                mock.patch.object(dshdpmare, "_generate_audio") as mock_generate,
                mock.patch.object(
                    dshdpmare, "_apply_speed_with_ffmpeg"
                ) as mock_ffmpeg,
            ):
                actual = dshdpmare._process_chunk_audio(
                    chunk_idx, chunk, voice=voice, speed=speed
                )
        finally:
            os.chdir(cwd)
        # Check outputs.
        self.assertEqual(actual, expected)
        mock_generate.assert_called_once()
        mock_ffmpeg.assert_not_called()

    def test2(self) -> None:
        """
        Test a non-default speed generates base audio then applies
        ffmpeg.
        """
        # Prepare inputs.
        cwd = os.getcwd()
        self.helper_chdir_to_scratch()
        chunk_idx = 2
        chunk = "hello again"
        voice = "en_US-test-voice"
        speed = 1.5
        # Prepare outputs.
        expected = dshdpmare._get_chunk_filename(
            chunk, chunk_idx=chunk_idx, speed=speed
        )
        # Run test.
        try:
            with (
                mock.patch.object(dshdpmare, "_generate_audio") as mock_generate,
                mock.patch.object(
                    dshdpmare, "_apply_speed_with_ffmpeg"
                ) as mock_ffmpeg,
            ):
                actual = dshdpmare._process_chunk_audio(
                    chunk_idx, chunk, voice=voice, speed=speed
                )
        finally:
            os.chdir(cwd)
        # Check outputs.
        self.assertEqual(actual, expected)
        mock_generate.assert_called_once()
        mock_ffmpeg.assert_called_once()

    def test3(self) -> None:
        """
        Test an already-cached speed-adjusted file skips regeneration.
        """
        # Prepare inputs.
        cwd = os.getcwd()
        scratch_dir = self.helper_chdir_to_scratch()
        chunk_idx = 3
        chunk = "cached chunk"
        voice = "en_US-test-voice"
        speed = 1.5
        final_audio_file = dshdpmare._get_chunk_filename(
            chunk, chunk_idx=chunk_idx, speed=speed
        )
        hio.to_file(os.path.join(scratch_dir, final_audio_file), "fake audio")
        progress_bar = mock.MagicMock()
        # Run test.
        try:
            with (
                mock.patch.object(dshdpmare, "_generate_audio") as mock_generate,
                mock.patch.object(
                    dshdpmare, "_apply_speed_with_ffmpeg"
                ) as mock_ffmpeg,
            ):
                actual = dshdpmare._process_chunk_audio(
                    chunk_idx,
                    chunk,
                    voice=voice,
                    speed=speed,
                    progress_bar=progress_bar,
                )
        finally:
            os.chdir(cwd)
        # Check outputs.
        self.assertEqual(actual, final_audio_file)
        mock_generate.assert_not_called()
        mock_ffmpeg.assert_not_called()
        progress_bar.update.assert_called_once_with(2)


# #############################################################################
# Test__handle_final_output
# #############################################################################


class Test__handle_final_output(hunitest.TestCase):
    """
    Test the _handle_final_output() function.
    """

    def test1(self) -> None:
        """
        Test no_play=True lists the audio files without playing them.
        """
        # Prepare inputs.
        audio_files = ["a.wav", "b.wav"]
        chunks = ["chunk a", "chunk b"]
        no_play = True
        # Run test.
        with mock.patch.object(
            dshdpmare, "_play_audio_with_controls"
        ) as mock_play:
            dshdpmare._handle_final_output(audio_files, chunks, no_play=no_play)
        # Check outputs.
        mock_play.assert_not_called()

    def test2(self) -> None:
        """
        Test no_play=False plays the audio files.
        """
        # Prepare inputs.
        audio_files = ["a.wav", "b.wav"]
        chunks = ["chunk a", "chunk b"]
        no_play = False
        # Run test.
        with mock.patch.object(
            dshdpmare, "_play_audio_with_controls"
        ) as mock_play:
            dshdpmare._handle_final_output(audio_files, chunks, no_play=no_play)
        # Check outputs.
        mock_play.assert_called_once_with(audio_files, chunks=chunks)

    def test3(self) -> None:
        """
        Test an empty audio file list does not attempt playback.
        """
        # Prepare inputs.
        audio_files: List[str] = []
        chunks: List[str] = []
        no_play = False
        # Run test.
        with mock.patch.object(
            dshdpmare, "_play_audio_with_controls"
        ) as mock_play:
            dshdpmare._handle_final_output(audio_files, chunks, no_play=no_play)
        # Check outputs.
        mock_play.assert_not_called()


# #############################################################################
# Test__parse
# #############################################################################


class Test__parse(hunitest.TestCase):
    """
    Test the _parse() function.
    """

    def test1(self) -> None:
        """
        Test default argument values when only --input is provided.
        """
        # Prepare inputs.
        parser = dshdpmare._parse()
        argv = ["piper_markdown_reader.py", "--input", "README.md"]
        # Prepare outputs.
        expected_speed = dshdpmare._DEFAULT_SPEED
        expected_voice = dshdpmare._DEFAULT_VOICE
        expected_max_length = dshdpmare._DEFAULT_MAX_LENGTH
        # Run test.
        with mock.patch("sys.argv", argv):
            args = parser.parse_args()
        # Check outputs.
        self.assertEqual(args.input, "README.md")
        self.assertEqual(args.speed, expected_speed)
        self.assertEqual(args.voice, expected_voice)
        self.assertEqual(args.max_length, expected_max_length)
        self.assertFalse(args.no_play)
        self.assertFalse(args.dry_run)

    def test2(self) -> None:
        """
        Test overriding speed, voice, and max_length on the command line.
        """
        # Prepare inputs.
        parser = dshdpmare._parse()
        argv = [
            "piper_markdown_reader.py",
            "--input",
            "README.md",
            "--speed",
            "1.5",
            "--voice",
            "en_US-joe-medium",
            "--max_length",
            "500",
            "--no_play",
            "--dry_run",
        ]
        # Run test.
        with mock.patch("sys.argv", argv):
            args = parser.parse_args()
        # Check outputs.
        self.assertEqual(args.speed, 1.5)
        self.assertEqual(args.voice, "en_US-joe-medium")
        self.assertEqual(args.max_length, 500)
        self.assertTrue(args.no_play)
        self.assertTrue(args.dry_run)


# #############################################################################
# Test__main
# #############################################################################


class Test__main(hunitest.TestCase):
    """
    Test the _main() function in dry-run mode (no audio generation).
    """

    def test1(self) -> None:
        """
        Test --dry_run processes the file without generating audio.
        """
        # Prepare inputs.
        content = """
        Intro text.

        - First bullet point.
        - Second bullet point.
        """
        content = hprint.dedent(content)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, content)
        parser = dshdpmare._parse()
        argv = [
            "piper_markdown_reader.py",
            "--input",
            in_file,
            "--dry_run",
            "--no_play",
        ]
        # Run test.
        with (
            mock.patch.object(dshdpmare, "_generate_audio") as mock_generate,
            mock.patch("sys.argv", argv),
        ):
            dshdpmare._main(parser)
        # Check outputs.
        mock_generate.assert_not_called()

    def test2(self) -> None:
        """
        Test --select extracts a section instead of reading the whole
        file.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, "unused content")
        parser = dshdpmare._parse()
        argv = [
            "piper_markdown_reader.py",
            "--input",
            in_file,
            "--select",
            "# Methods:# Results",
            "--dry_run",
            "--no_play",
        ]
        extracted_content = "Intro text.\n- A bullet point."
        # Run test.
        with (
            mock.patch.object(
                dshdpmare,
                "_extract_markdown_section",
                return_value=extracted_content,
            ) as mock_extract,
            mock.patch.object(dshdpmare, "_generate_audio") as mock_generate,
            mock.patch("sys.argv", argv),
        ):
            dshdpmare._main(parser)
        # Check outputs.
        mock_extract.assert_called_once_with(in_file, "# Methods", "# Results")
        mock_generate.assert_not_called()


# #############################################################################
# Test_piper_markdown_reader_script
# #############################################################################


@pytest.mark.skip(reason="Requires piper-tts installation and voice models")
class Test_piper_markdown_reader_script(hunitest.TestCase):
    """
    Test piper_markdown_reader script CLI functionality.
    """

    def _create_input_file(self) -> None:
        """
        Create the test markdown input file.
        """
        content = """
        # Introduction

        This is the introduction section.

        # Methods

        ## Data Collection

        How we collected data.

        # Results

        Our findings.
        """
        content = hprint.dedent(content)
        in_file = os.path.join(self.get_input_dir(), "input.md")
        hio.to_file(in_file, content)

    def setUp(self) -> None:
        """
        Create test input file.
        """
        super().setUp()
        self._create_input_file()

    def _run_script(self, args: str = "") -> None:
        """
        Helper to run the script with given arguments.

        :param args: additional command line arguments
        """
        in_file = os.path.join(self.get_input_dir(), "input.md")
        script_path = hgit.find_file_in_git_tree("piper_markdown_reader.py")
        cmd = f"{script_path} --input {in_file} --no_play {args}"
        hsystem.system(cmd)

    def test1(self) -> None:
        """
        Test script runs with --md_start and --md_end arguments.
        """
        # Run test.
        self._run_script("--md_start '# Methods' --md_end '# Results'")

    def test2(self) -> None:
        """
        Test script runs with --md_start only (auto-detect end).
        """
        # Run test.
        self._run_script("--md_start '# Results'")

    def test3(self) -> None:
        """
        Test script runs with --md_start and --md_end 'END' (extract to file end).
        """
        # Run test.
        self._run_script("--md_start '# Methods' --md_end 'END'")

    def test4(self) -> None:
        """
        Test script runs without --md_start (full file).
        """
        # Run test.
        self._run_script("")

    @pytest.mark.slow
    def test5(self) -> None:
        """
        Test script creates intermediate file when --md_start provided.
        """
        # Run test.
        self._run_script("--md_start '# Methods' --md_end '# Results'")
        # Check outputs.
        tmp_file = dshdpmare._TMP_EXTRACT_FILE
        self.assertTrue(
            os.path.exists(tmp_file),
            f"Intermediate file {tmp_file} was not created",
        )
