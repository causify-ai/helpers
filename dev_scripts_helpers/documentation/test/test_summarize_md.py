import os
from typing import List, Optional, Tuple

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

import dev_scripts_helpers.documentation.summarize_md as dshdsumd


def _run_summarize_md_test(
    self,
    input_md: str,
    expected_output: str,
    md_level: int,
) -> None:
    """
    Run summarize_md.py script and verify output.

    :param self: Test case instance with get_scratch_space() and assert_equal()
    :param input_md: Input markdown content
    :param expected_output: Expected output from script
    :param md_level: Header level to process
    """
    scratch_dir = self.get_scratch_space()
    input_file = os.path.join(scratch_dir, "input.md")
    output_file = os.path.join(scratch_dir, "output.md")
    hio.to_file(input_file, input_md)
    script_path = hgit.find_file_in_git_tree("summarize_md.py")
    cmd = f"{script_path} -i {input_file} -o {output_file} --md_level {md_level} --test"
    hsystem.system(cmd)
    actual_output = hio.from_file(output_file)
    self.assert_equal(actual_output, expected_output)


# #############################################################################
# Test_compute_sha1_digest
# #############################################################################


class Test_compute_sha1_digest(hunitest.TestCase):
    """
    Test _compute_sha1_digest function.
    """

    def helper(self, text: str, expected_digest: str) -> None:
        """
        Test helper for _compute_sha1_digest.

        :param text: Input text to digest
        :param expected_digest: Expected SHA1 digest
        """
        actual = dshdsumd._compute_sha1_digest(text)
        self.assertEqual(actual, expected_digest)

    def test1(self) -> None:
        """
        Test computing digest of simple text.
        """
        # Prepare inputs.
        text = "Hello, World!"
        # Prepare outputs.
        expected = "0a0a9f2a6772942557ab5355d76af442f8f65e01"
        # Run test.
        self.helper(text, expected)

    def test2(self) -> None:
        """
        Test computing digest of empty string.
        """
        # Prepare inputs.
        text = ""
        # Prepare outputs.
        expected = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        # Run test.
        self.helper(text, expected)

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
        *,
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
            all_headers, md_level=md_level, md_start=start, md_end=end
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
                all_headers, md_level=md_level, md_start=None, md_end=None
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
# Test_summarize_md_py1
# #############################################################################


class Test_summarize_md_py1(hunitest.TestCase):
    """
    End-to-end tests for summarize_md.py with --test flag.
    """

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
        expected_output = hprint.dedent("""
        # Introduction

        SHA1: d2c8641d89ca8b43807392b0a77398410448acbf
        """)
        expected_output += "\n\n\n"
        # Run test.
        _run_summarize_md_test(self, input_md, expected_output, md_level=1)

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
        expected_output = hprint.dedent("""
        # Chapter 1

        SHA1: 74c7a2c6bbfea12d7c601a48c36d9aad7a9e3c7a


        # Chapter 2

        SHA1: 8f635be771fecdb7321b0f88c04609a8fe79dec8
        """)
        expected_output += "\n\n\n"
        # Run test.
        _run_summarize_md_test(self, input_md, expected_output, md_level=1)

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
        expected_output = hprint.dedent("""
        # Chapter 1

        SHA1: 92992a38d4c0056a87e0a303b7d62cada1da1784


        # Chapter 2

        SHA1: e0431757296c5f62cf74ac911fc8fed8abb37ec0
        """)
        expected_output += "\n\n\n"
        # Run test.
        _run_summarize_md_test(self, input_md, expected_output, md_level=1)

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
        expected_output = hprint.dedent("""
        # Chapter 1

        ## Section 1.1

        SHA1: f4191b95a8f8f799ee0a8c458e0538234217ab18


        ## Section 1.2

        SHA1: 91c1f10d6d9e5e36cd4949c4b39bef86d8d138c0
        """)
        expected_output += "\n\n\n"
        # Run test.
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)


# #############################################################################
# Test_summarize_md_py2
# #############################################################################


class Test_summarize_md_py2(hunitest.TestCase):
    """
    End-to-end tests for intro text handling with --test flag.
    Tests introductory content between headers is properly summarized.
    """

    def test1(self) -> None:
        """
        Test intro text between level-1 and first level-2 header is digested.
        """
        input_md = """
        # Chapter 1

        This is intro text for chapter 1.
        It spans multiple lines.
        And should be summarized.

        ## Section 1.1

        Content of section 1.1.

        ## Section 1.2

        Content of section 1.2.
        """
        input_md = hprint.dedent(input_md)
        # When processing level 2:
        # - Writes "# Chapter 1"
        # - Digests the intro text
        # - Then processes level-2 sections
        expected_output = hprint.dedent("""
        # Chapter 1

        SHA1: d26404705e7e72e7008d7e2642a247a9b3c472a8


        ## Section 1.1

        SHA1: f4191b95a8f8f799ee0a8c458e0538234217ab18


        ## Section 1.2

        SHA1: 91c1f10d6d9e5e36cd4949c4b39bef86d8d138c0
        """)
        expected_output += "\n\n\n"
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)

    def test2(self) -> None:
        """
        Test multiple chapters each with intro text and sections.
        """
        input_md = """
        # Chapter 1

        Chapter 1 introduction text.

        ## Section 1.1

        Section 1.1 content.

        # Chapter 2

        Chapter 2 introduction text.

        ## Section 2.1

        Section 2.1 content.
        """
        input_md = hprint.dedent(input_md)
        # Each chapter intro text should be digested once,
        # then sections are processed
        expected_output = hprint.dedent("""
        # Chapter 1

        SHA1: 2d6d7de5765be418c0017d5174b585513524f8cc


        ## Section 1.1

        SHA1: c73efb3b75447b12aca56d7ee6b90cdc44553c3c


        # Chapter 2

        SHA1: a129523267e7d498f9f243d7d03a849fad250f74


        ## Section 2.1

        SHA1: d3d90ab03fa51c1bce835a9d923ce27ec1a7eb38
        """)
        expected_output += "\n\n\n"
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)

    def test3(self) -> None:
        """
        Test chapter with no intro text (section comes right after header).
        """
        input_md = """
        # Chapter 1

        ## Section 1.1

        Content of section 1.1.

        ## Section 1.2

        Content of section 1.2.
        """
        input_md = hprint.dedent(input_md)
        # No intro text, so only chapter header and sections are processed
        expected_output = hprint.dedent("""
        # Chapter 1

        ## Section 1.1

        SHA1: f4191b95a8f8f799ee0a8c458e0538234217ab18


        ## Section 1.2

        SHA1: 91c1f10d6d9e5e36cd4949c4b39bef86d8d138c0
        """)
        expected_output += "\n\n\n"
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)

    def test4(self) -> None:
        """
        Test intro text with empty lines is properly cleaned and digested.
        """
        input_md = """
        # Chapter 1


        Some intro text after empty lines.

        And more text.


        ## Section 1.1

        Section content.
        """
        input_md = hprint.dedent(input_md)
        expected_output = hprint.dedent("""
        # Chapter 1

        SHA1: 2d03205058a673bcd07f39fe2fc918194a3a7ade


        ## Section 1.1

        SHA1: 7f25ffa8e635f3aa77b14cbc9d26dfe73641a221
        """)
        expected_output += "\n\n\n"
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)


# #############################################################################
# Test_summarize_md_py3
# #############################################################################


class Test_summarize_md_py3(hunitest.TestCase):
    """
    End-to-end tests for complex markdown structures.
    Tests numbered chapters, KEY POINTS sections, and deeply nested headers.
    """

    def test1(self) -> None:
        """
        Test structure similar to prediction_machines with numbered chapters.
        """
        input_md = """
        # 1 Introduction

        Introduction text that will be summarized.

        ## KEY POINTS

        Some key points.

        # 2 Main Content

        Content intro text.

        ## First Section

        First section content.

        ## Second Section

        Second section content.
        """
        input_md = hprint.dedent(input_md)
        expected_output = hprint.dedent("""
        # 1 Introduction

        SHA1: e9ccdd9eaaa952a5a179edc5a17d7cc1c83fc83f


        ## KEY POINTS

        SHA1: ed315a7876b711e899ab8eb396815f5d1e0e3c96


        # 2 Main Content

        SHA1: f473f9e0a3fc76761463c167f51be105224e49ff


        ## First Section

        SHA1: fd7a577029429066bb098ff8037dfcbfc634241a


        ## Second Section

        SHA1: 6c45666378e200fb3c53577ea12882ea35d7919d
        """)
        expected_output += "\n\n\n"
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)

    def test2(self) -> None:
        """
        Test chapter with multiple sections and KEY POINTS section.
        """
        input_md = """
        # 3 Chapter Three

        Chapter intro explaining the chapter theme.

        ## Topic One

        Content about topic one.

        ## Topic Two

        Content about topic two.

        ## Topic Three

        Content about topic three.

        ## KEY POINTS

        Summary of key points.
        """
        input_md = hprint.dedent(input_md)
        expected_output = hprint.dedent("""
        # 3 Chapter Three

        SHA1: 5a0f26f035c37e68c553182c3077b017ac87dc67


        ## Topic One

        SHA1: 931e4afc80b14288fcf9ee2a59ec0cec97557fe4


        ## Topic Two

        SHA1: c2ab7f2ab43653f794dfe5ac6b47b39930932d65


        ## Topic Three

        SHA1: edd406b239587b4ed704130a3eec00ef0fa36565


        ## KEY POINTS

        SHA1: 3960b1496909e819509c8dc6e0cdc2109c4adaa3
        """)
        expected_output += "\n\n\n"
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)

    def test3(self) -> None:
        """
        Test that level-3 headers are included in level-2 section digests.
        """
        input_md = """
        # Chapter 1

        Chapter intro.

        ## Section 1.1

        Section intro.

        ### Subsection 1.1.1

        Subsection content.

        ### Subsection 1.1.2

        Another subsection.

        ## Section 1.2

        Section 1.2 content.
        """
        input_md = hprint.dedent(input_md)
        expected_output = hprint.dedent("""
        # Chapter 1

        SHA1: 8440ce0297a6edbda832f8a7cb330c3f4184a3fc


        ## Section 1.1

        SHA1: 7b719f2a08cb410a01a0a2e4b81af531bde6f046


        ## Section 1.2

        SHA1: 937a5f1dde998663d8abd3279cd0e6e3b27aa31f
        """)
        expected_output += "\n\n\n"
        _run_summarize_md_test(self, input_md, expected_output, md_level=2)
