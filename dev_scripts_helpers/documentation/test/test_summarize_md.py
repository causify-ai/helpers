import logging
from typing import List, Optional

import helpers.hmarkdown_headers as hmarhead
import helpers.hunit_test as hunitest

import dev_scripts_helpers.documentation.summarize_md as dshdsumd

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_get_target_headers
# #############################################################################


class Test_get_target_headers(hunitest.TestCase):
    """
    Test _get_target_headers function.
    """

    def helper(
        self,
        all_headers: hmarhead.HeaderList,
        md_level: int,
        start: Optional[str] = None,
        end: Optional[str] = None,
        expected_count: Optional[int] = None,
        expected_descriptions: Optional[List[str]] = None,
    ) -> None:
        """
        Test helper for _get_target_headers.

        :param all_headers: List of all headers
        :param md_level: Header level to filter
        :param start: Start header description
        :param end: End header description
        :param expected_count: Expected number of headers
        :param expected_descriptions: Expected header descriptions
        """
        # Run test.
        actual = dshdsumd._get_target_headers(
            all_headers, md_level=md_level, start=start, end=end
        )
        # Check outputs.
        self.assertEqual(len(actual), expected_count)
        if expected_descriptions:
            actual_descriptions = [h.description for h in actual]
            self.assertEqual(actual_descriptions, expected_descriptions)

    def test1(self) -> None:
        """
        Test filtering headers by level 1.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(
                level=2, description="Section 1.1", line_number=3
            ),
            hmarhead.HeaderInfo(
                level=2, description="Section 1.2", line_number=5
            ),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
        ]
        md_level = 1
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 1", "Chapter 2"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test2(self) -> None:
        """
        Test filtering headers by level 2.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(
                level=2, description="Section 1.1", line_number=3
            ),
            hmarhead.HeaderInfo(
                level=2, description="Section 1.2", line_number=5
            ),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
        ]
        md_level = 2
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Section 1.1", "Section 1.2"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test3(self) -> None:
        """
        Test filtering with start parameter.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(
                level=1, description="Chapter 3", line_number=13
            ),
        ]
        md_level = 1
        start = "Chapter 2"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 2", "Chapter 3"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            start=start,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test4(self) -> None:
        """
        Test filtering with end parameter.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(
                level=1, description="Chapter 3", line_number=13
            ),
        ]
        md_level = 1
        end = "Chapter 2"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 1", "Chapter 2"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            end=end,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test5(self) -> None:
        """
        Test filtering with both start and end parameters.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(
                level=1, description="Chapter 3", line_number=13
            ),
            hmarhead.HeaderInfo(
                level=1, description="Chapter 4", line_number=19
            ),
        ]
        md_level = 1
        start = "Chapter 2"
        end = "Chapter 3"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 2", "Chapter 3"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            start=start,
            end=end,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test6(self) -> None:
        """
        Test filtering with partial match on start.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(
                level=1, description="Chapter 3", line_number=13
            ),
        ]
        md_level = 1
        start = "Chapter 2"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 2", "Chapter 3"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            start=start,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test7(self) -> None:
        """
        Test error when no headers at specified level.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(
                level=2, description="Section 1.1", line_number=3
            ),
        ]
        md_level = 3
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            dshdsumd._get_target_headers(
                all_headers, md_level=md_level, start=None, end=None
            )
        actual = str(cm.exception)
        self.assertIn("No headers found at level 3", actual)


# #############################################################################
# Test_extract_section
# #############################################################################


class Test_extract_section(hunitest.TestCase):
    """
    Test _extract_section function.
    """

    def helper(
        self,
        header: hmarhead.HeaderInfo,
        all_headers: hmarhead.HeaderList,
        lines: List[str],
        md_level: int,
        expected: List[str],
    ) -> None:
        """
        Test helper for _extract_section.

        :param header: Header to extract section for
        :param all_headers: List of all headers
        :param lines: All lines in the markdown file
        :param md_level: Header level to extract
        :param expected: Expected extracted section
        """
        # Run test.
        actual = dshdsumd._extract_section(
            header, all_headers, lines, md_level=md_level
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting section with content until next header.
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 1", line_number=1
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=4),
        ]
        lines = [
            "# Chapter 1",
            "Content line 1",
            "Content line 2",
            "# Chapter 2",
            "Content line 3",
        ]
        md_level = 1
        # Prepare outputs.
        expected = [
            "# Chapter 1",
            "Content line 1",
            "Content line 2",
        ]
        # Run test.
        self.helper(header, all_headers, lines, md_level, expected)

    def test2(self) -> None:
        """
        Test extracting last section (no next header).
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 2", line_number=4
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=4),
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
        # Prepare outputs.
        expected = [
            "# Chapter 2",
            "Content 2a",
            "Content 2b",
        ]
        # Run test.
        self.helper(header, all_headers, lines, md_level, expected)

    def test3(self) -> None:
        """
        Test extracting section strips trailing empty lines.
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 1", line_number=1
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=6),
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
        # Prepare outputs.
        expected = [
            "# Chapter 1",
            "Content",
        ]
        # Run test.
        self.helper(header, all_headers, lines, md_level, expected)

    def test4(self) -> None:
        """
        Test extracting section respects nested headers.
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 1", line_number=1
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(
                level=2, description="Section 1.1", line_number=3
            ),
            hmarhead.HeaderInfo(
                level=2, description="Section 1.2", line_number=5
            ),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
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
        # Prepare outputs.
        expected = [
            "# Chapter 1",
            "",
            "## Section 1.1",
            "Content 1.1",
            "## Section 1.2",
            "Content 1.2",
        ]
        # Run test.
        self.helper(header, all_headers, lines, md_level, expected)
