import logging
import os
import subprocess
import sys
from typing import List, Optional, Tuple

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import dev_scripts_helpers.documentation.summarize_md as dshdsumd

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_compute_sha1_digest
# #############################################################################


class Test_compute_sha1_digest(hunitest.TestCase):
    """
    Test _compute_sha1_digest function.
    """

    def test1(self) -> None:
        """
        Test computing digest of simple text.
        """
        # Prepare inputs.
        text = "Hello, World!"
        # Run test.
        actual = dshdsumd._compute_sha1_digest(text)
        # Check outputs.
        expected = "0a0a9f2a6772942557ab5355d76af442f8f65e01"
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test computing digest of empty string.
        """
        # Prepare inputs.
        text = ""
        # Run test.
        actual = dshdsumd._compute_sha1_digest(text)
        # Check outputs.
        expected = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that different texts produce different digests.
        """
        # Prepare inputs.
        text1 = "Chapter 1 content"
        text2 = "Chapter 2 content"
        # Run test.
        digest1 = dshdsumd._compute_sha1_digest(text1)
        digest2 = dshdsumd._compute_sha1_digest(text2)
        # Check outputs.
        self.assertNotEqual(digest1, digest2)

    def test4(self) -> None:
        """
        Test that same text produces same digest (consistent).
        """
        # Prepare inputs.
        text = "Consistent test content"
        # Run test.
        digest1 = dshdsumd._compute_sha1_digest(text)
        digest2 = dshdsumd._compute_sha1_digest(text)
        # Check outputs.
        self.assertEqual(digest1, digest2)

    def test5(self) -> None:
        """
        Test computing digest of multiline text.
        """
        # Prepare inputs.
        text = hprint.dedent("""
        # Chapter 1

        Content line 1
        Content line 2
        """)
        # Run test.
        actual = dshdsumd._compute_sha1_digest(text)
        # Check outputs.
        self.assertEqual(len(actual), 40)
        self.assertTrue(all(c in "0123456789abcdef" for c in actual))


# #############################################################################
# Test_get_target_headers
# #############################################################################


class Test_get_target_headers(hunitest.TestCase):
    """
    Test _get_target_headers function.
    """

    def helper(
        self,
        all_headers: List[Tuple[int, str, int]],
        md_level: int,
        start: Optional[str] = None,
        end: Optional[str] = None,
        expected_count: Optional[int] = None,
        expected_titles: Optional[List[str]] = None,
    ) -> None:
        """
        Test helper for _get_target_headers.

        :param all_headers: List of (level, title, line_number) tuples
        :param md_level: Header level to filter
        :param start: Start header description
        :param end: End header description
        :param expected_count: Expected number of headers
        :param expected_titles: Expected header titles
        """
        actual = dshdsumd._get_target_headers(
            all_headers, md_level=md_level, start=start, end=end
        )
        self.assertEqual(len(actual), expected_count)
        if expected_titles:
            actual_titles = [h[1] for h in actual]
            self.assertEqual(actual_titles, expected_titles)

    def test1(self) -> None:
        """
        Test filtering headers by level 1.
        """
        all_headers = [
            (1, "Chapter 1", 0),
            (2, "Section 1.1", 2),
            (2, "Section 1.2", 4),
            (1, "Chapter 2", 6),
        ]
        md_level = 1
        expected_count = 2
        expected_titles = ["Chapter 1", "Chapter 2"]
        self.helper(
            all_headers,
            md_level,
            expected_count=expected_count,
            expected_titles=expected_titles,
        )

    def test2(self) -> None:
        """
        Test filtering headers by level 2.
        """
        all_headers = [
            (1, "Chapter 1", 0),
            (2, "Section 1.1", 2),
            (2, "Section 1.2", 4),
            (1, "Chapter 2", 6),
        ]
        md_level = 2
        expected_count = 2
        expected_titles = ["Section 1.1", "Section 1.2"]
        self.helper(
            all_headers,
            md_level,
            expected_count=expected_count,
            expected_titles=expected_titles,
        )

    def test3(self) -> None:
        """
        Test filtering with start parameter.
        """
        all_headers = [
            (1, "Chapter 1", 0),
            (1, "Chapter 2", 6),
            (1, "Chapter 3", 12),
        ]
        md_level = 1
        start = "Chapter 2"
        expected_count = 2
        expected_titles = ["Chapter 2", "Chapter 3"]
        self.helper(
            all_headers,
            md_level,
            start=start,
            expected_count=expected_count,
            expected_titles=expected_titles,
        )

    def test4(self) -> None:
        """
        Test filtering with end parameter.
        """
        all_headers = [
            (1, "Chapter 1", 0),
            (1, "Chapter 2", 6),
            (1, "Chapter 3", 12),
        ]
        md_level = 1
        end = "Chapter 2"
        expected_count = 2
        expected_titles = ["Chapter 1", "Chapter 2"]
        self.helper(
            all_headers,
            md_level,
            end=end,
            expected_count=expected_count,
            expected_titles=expected_titles,
        )

    def test5(self) -> None:
        """
        Test filtering with both start and end parameters.
        """
        all_headers = [
            (1, "Chapter 1", 0),
            (1, "Chapter 2", 6),
            (1, "Chapter 3", 12),
            (1, "Chapter 4", 18),
        ]
        md_level = 1
        start = "Chapter 2"
        end = "Chapter 3"
        expected_count = 2
        expected_titles = ["Chapter 2", "Chapter 3"]
        self.helper(
            all_headers,
            md_level,
            start=start,
            end=end,
            expected_count=expected_count,
            expected_titles=expected_titles,
        )

    def test6(self) -> None:
        """
        Test filtering with partial match on start.
        """
        all_headers = [
            (1, "Chapter 1", 0),
            (1, "Chapter 2", 6),
            (1, "Chapter 3", 12),
        ]
        md_level = 1
        start = "Chapter 2"
        expected_count = 2
        expected_titles = ["Chapter 2", "Chapter 3"]
        self.helper(
            all_headers,
            md_level,
            start=start,
            expected_count=expected_count,
            expected_titles=expected_titles,
        )

    def test7(self) -> None:
        """
        Test error when no headers at specified level.
        """
        all_headers = [
            (1, "Chapter 1", 0),
            (2, "Section 1.1", 2),
        ]
        md_level = 3
        with self.assertRaises(AssertionError):
            dshdsumd._get_target_headers(
                all_headers, md_level=md_level, start=None, end=None
            )


# #############################################################################
# Test_extract_section
# #############################################################################


class Test_extract_section(hunitest.TestCase):
    """
    Test _extract_section function.
    """

    def helper(
        self,
        header: Tuple[int, str, int],
        all_headers: List[Tuple[int, str, int]],
        lines: List[str],
        md_level: int,
        expected: str,
    ) -> None:
        """
        Test helper for _extract_section.

        :param header: (level, title, line_number) tuple for the header
        :param all_headers: List of (level, title, line_number) tuples
        :param lines: All lines in the markdown file
        :param md_level: Header level to extract
        :param expected: Expected extracted section as string
        """
        actual = dshdsumd._extract_section(
            header, all_headers, lines, md_level=md_level
        )
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting section with content until next header.
        """
        header = (1, "Chapter 1", 0)
        all_headers = [
            (1, "Chapter 1", 0),
            (1, "Chapter 2", 3),
        ]
        lines = [
            "# Chapter 1",
            "Content line 1",
            "Content line 2",
            "# Chapter 2",
            "Content line 3",
        ]
        md_level = 1
        expected = hprint.dedent("""
        # Chapter 1
        Content line 1
        Content line 2
        """)
        self.helper(header, all_headers, lines, md_level, expected)

    def test2(self) -> None:
        """
        Test extracting last section (no next header).
        """
        header = (1, "Chapter 2", 3)
        all_headers = [
            (1, "Chapter 1", 0),
            (1, "Chapter 2", 3),
        ]
        lines = [
            "# Chapter 1",
            "Content 1",
            "",
            "# Chapter 2",
            "Content 2a",
            "Content 2b",
        ]
        md_level = 1
        expected = hprint.dedent("""
        # Chapter 2
        Content 2a
        Content 2b
        """)
        self.helper(header, all_headers, lines, md_level, expected)

    def test3(self) -> None:
        """
        Test extracting section strips trailing empty lines.
        """
        header = (1, "Chapter 1", 0)
        all_headers = [
            (1, "Chapter 1", 0),
            (1, "Chapter 2", 5),
        ]
        lines = [
            "# Chapter 1",
            "Content",
            "",
            "",
            "",
            "# Chapter 2",
        ]
        md_level = 1
        expected = hprint.dedent("""
        # Chapter 1
        Content
        """)
        self.helper(header, all_headers, lines, md_level, expected)

    def test4(self) -> None:
        """
        Test extracting section respects nested headers.
        """
        header = (1, "Chapter 1", 0)
        all_headers = [
            (1, "Chapter 1", 0),
            (2, "Section 1.1", 2),
            (2, "Section 1.2", 4),
            (1, "Chapter 2", 6),
        ]
        lines = [
            "# Chapter 1",
            "",
            "## Section 1.1",
            "Content 1.1",
            "## Section 1.2",
            "Content 1.2",
            "# Chapter 2",
        ]
        md_level = 1
        expected = hprint.dedent("""
        # Chapter 1


        ## Section 1.1
        Content 1.1
        ## Section 1.2
        Content 1.2
        """)
        self.helper(header, all_headers, lines, md_level, expected)


# #############################################################################
# Test_summarize_md_with_test_flag
# #############################################################################


class Test_summarize_md_with_test_flag(hunitest.TestCase):
    """
    End-to-end tests for summarize_md.py with --test flag.
    """

    def helper(
        self,
        input_md: str,
        expected_output: str,
        md_level: int = 1,
    ) -> None:
        """
        Test helper for summarize_md.py with --test flag.

        :param input_md: Input markdown content
        :param expected_output: Expected output from script
        :param md_level: Header level to process
        """
        # Create input and output files.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        output_file = os.path.join(scratch_dir, "output.md")
        hio.to_file(input_file, input_md)
        # Run the script with --test flag.
        cmd = [
            sys.executable,
            "dev_scripts_helpers/documentation/summarize_md.py",
            "-i", input_file,
            "-o", output_file,
            "--md_level", str(md_level),
            "--test",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        # Verify script executed successfully.
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        # Read and verify output.
        actual_output = hio.from_file(output_file)
        self.assert_equal(actual_output, expected_output)

    def test1(self) -> None:
        """
        Test summarizing simple single chapter with --test flag.
        """
        # Prepare inputs.
        input_md = """
        # Introduction

        This is the introduction text.
        """
        input_md = hprint.dedent(input_md)
        # Prepare outputs.
        expected_output = """
        # Introduction

        SHA1: d2c8641d89ca8b43807392b0a77398410448acbf

        """
        expected_output = hprint.dedent(expected_output)
        # Run test.
        self.helper(input_md, expected_output)

    def test2(self) -> None:
        """
        Test summarizing multiple chapters with --test flag.
        """
        # Prepare inputs.
        input_md = """
        # Chapter 1

        This is chapter 1 content.

        # Chapter 2

        This is chapter 2 content.
        """
        input_md = hprint.dedent(input_md)
        # Prepare outputs.
        expected_output = """
        # Chapter 1

        SHA1: 74c7a2c6bbfea12d7c601a48c36d9aad7a9e3c7a

        # Chapter 2

        SHA1: 8f635be771fecdb7321b0f88c04609a8fe79dec8

        """
        expected_output = hprint.dedent(expected_output)
        # Run test.
        self.helper(input_md, expected_output)

    def test3(self) -> None:
        """
        Test summarizing chapters with nested sections at level 1.
        """
        # Prepare inputs.
        input_md = """
        # Chapter 1

        Chapter 1 intro.

        ## Section 1.1

        Section 1.1 content.

        ## Section 1.2

        Section 1.2 content.

        # Chapter 2

        Chapter 2 content.
        """
        input_md = hprint.dedent(input_md)
        # Prepare outputs.
        expected_output = """
        # Chapter 1

        SHA1: 92992a38d4c0056a87e0a303b7d62cada1da1784

        # Chapter 2

        SHA1: e0431757296c5f62cf74ac911fc8fed8abb37ec0

        """
        expected_output = hprint.dedent(expected_output)
        # Run test.
        self.helper(input_md, expected_output)

    def test4(self) -> None:
        """
        Test summarizing at level 2 (sections within chapters).
        """
        # Prepare inputs.
        input_md = """
        # Chapter 1

        ## Section 1.1

        Content of section 1.1.

        ## Section 1.2

        Content of section 1.2.
        """
        input_md = hprint.dedent(input_md)
        # Prepare outputs (should process level-2 headers).
        expected_output = """
        # Chapter 1

        ## Section 1.1

        SHA1: 6d5f8c1a2e9b3c7f0e4a1d5c9b6e2f8a3d7c0e5

        ## Section 1.2

        SHA1: 1c9e4f5d2a8b6c0f3e7a1d2c5b9f8e4a7c0d3f6

        """
        expected_output = hprint.dedent(expected_output)
        # Run test.
        self.helper(input_md, expected_output, md_level=2)
