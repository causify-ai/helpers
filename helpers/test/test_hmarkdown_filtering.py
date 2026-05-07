import logging

import helpers.hmarkdown_filtering as hmarfilt
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_filter_by_header1
# #############################################################################


class Test_filter_by_header1(hunitest.TestCase):
    def test_basic_header_extraction(self) -> None:
        """
        Test basic header extraction functionality.
        """
        # Prepare inputs.
        test_content = """
        # Introduction
        This is the introduction section.
        Some content here.

        ## Section 1
        Content for section 1.

        # Conclusion
        Final thoughts here.
        """
        test_content = hprint.dedent(
            test_content, remove_lead_trail_empty_lines_=False
        )
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_header(lines, "Introduction")
        result_content = "\n".join(result_lines)
        # Check outputs.
        expected = """
        # Introduction
        This is the introduction section.
        Some content here.

        ## Section 1
        Content for section 1.
        """
        self.assert_equal(result_content, expected, dedent=True)

    def test_header_not_found(self) -> None:
        """
        Test behavior when header is not found.
        """
        # Prepare inputs.
        test_content = """
        # Introduction
        This is the introduction section.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        # Check outputs.
        with self.assertRaises(ValueError):
            hmarfilt.filter_by_header(lines, "NonExistent")


# #############################################################################
# Test_parse_range1
# #############################################################################


class Test_parse_range1(hunitest.TestCase):
    def helper(
        self, range_str: str, max_value: int, exp_start: int, exp_end: int
    ) -> None:
        """
        Test helper for _parse_range.

        :param range_str: range string to parse
        :param max_value: maximum value for end bounds
        :param exp_start: expected start value
        :param exp_end: expected end value
        """
        # Run test.
        start, end = hmarfilt._parse_range(range_str, max_value)
        # Check outputs.
        self.assertEqual(start, exp_start)
        self.assertEqual(end, exp_end)

    def test_numeric_range(self) -> None:
        """
        Test parsing numeric range (0-indexed).
        """
        # Prepare inputs.
        range_str = "0:10"
        max_value = 20
        exp_start = 0
        exp_end = 10
        # Run test.
        self.helper(range_str, max_value, exp_start, exp_end)

    def test_none_start(self) -> None:
        """
        Test range with None start (defaults to 0).
        """
        # Prepare inputs.
        range_str = "None:10"
        max_value = 20
        exp_start = 0
        exp_end = 10
        # Run test.
        self.helper(range_str, max_value, exp_start, exp_end)

    def test_none_end(self) -> None:
        """
        Test range with None end (defaults to max_value).
        """
        # Prepare inputs.
        range_str = "0:None"
        max_value = 20
        exp_start = 0
        exp_end = 20
        # Run test.
        self.helper(range_str, max_value, exp_start, exp_end)

    def test_both_none(self) -> None:
        """
        Test range with both None (0:max_value).
        """
        # Prepare inputs.
        range_str = "None:None"
        max_value = 20
        exp_start = 0
        exp_end = 20
        # Run test.
        self.helper(range_str, max_value, exp_start, exp_end)

    def test_invalid_range(self) -> None:
        """
        Test invalid range format.
        """
        # Run test.
        with self.assertRaises(AssertionError):
            hmarfilt._parse_range("invalid", 20)

    def test_case_insensitive_none(self) -> None:
        """
        Test case insensitive None parsing.
        """
        # Prepare inputs.
        range_str = "NONE:none"
        max_value = 20
        exp_start = 0
        exp_end = 20
        # Run test.
        self.helper(range_str, max_value, exp_start, exp_end)


# #############################################################################
# Test_filter_by_lines1
# #############################################################################


class Test_filter_by_lines1(hunitest.TestCase):
    def helper(self, test_content: str, filter_str: str, expected: str) -> None:
        """
        Test helper for filter_by_lines.

        :param test_content: multiline test content
        :param filter_str: range filter string (e.g., "1:3")
        :param expected: expected filtered output
        """
        # Prepare inputs.
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_lines(lines, filter_str)
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertEqual(result_content, expected)

    def test_basic_line_filtering(self) -> None:
        """
        Test basic line filtering functionality (0-indexed).
        """
        # Prepare inputs.
        test_content = """
        Line 1
        Line 2
        Line 3
        Line 4
        Line 5
        """
        filter_str = "1:3"
        expected = "Line 2\nLine 3"
        # Run test.
        self.helper(test_content, filter_str, expected)

    def test_line_filtering_with_none(self) -> None:
        """
        Test line filtering with None start (defaults to 0).
        """
        # Prepare inputs.
        test_content = """
        Line 1
        Line 2
        Line 3
        Line 4
        Line 5
        """
        filter_str = "None:2"
        expected = "Line 1\nLine 2"
        # Run test.
        self.helper(test_content, filter_str, expected)

    def test_line_filtering_to_end(self) -> None:
        """
        Test line filtering from start to end.
        """
        # Prepare inputs.
        test_content = """
        Line 1
        Line 2
        Line 3
        """
        filter_str = "1:None"
        expected = "Line 2\nLine 3"
        # Run test.
        self.helper(test_content, filter_str, expected)

    def test_invalid_range_order(self) -> None:
        """
        Test that start line <= end line is enforced.
        """
        # Prepare inputs.
        test_content = "Line 1\nLine 2\nLine 3"
        lines = test_content.split("\n")
        # Run test.
        # Check outputs.
        with self.assertRaises(AssertionError):
            hmarfilt.filter_by_lines(lines, "2:1")


# #############################################################################
# Test_filter_by_slides1
# #############################################################################


class Test_filter_by_slides1(hunitest.TestCase):
    def helper(self, test_content: str, filter_str: str, expected: str) -> None:
        """
        Test helper for filter_by_slides.

        :param test_content: multiline test content
        :param filter_str: range filter string (e.g., "0:1")
        :param expected: expected filtered output
        """
        # Prepare inputs.
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_slides(lines, filter_str)
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assert_equal(result_content, expected, dedent=True)

    def test_basic_slide_filtering(self) -> None:
        """
        Test basic slide filtering functionality.
        """
        # Prepare inputs.
        test_content = """
        # Header 1




        * Slide 1
        Content for slide 1.

        * Slide 2
        Content for slide 2.

        * Slide 3
        Content for slide 3.
        """
        filter_str = "0:1"
        expected = """
        * Slide 1
        Content for slide 1.

        """
        # Run test.
        self.helper(test_content, filter_str, expected)

    def test_slide_filtering_with_none_end(self) -> None:
        """
        Test slide filtering to the end.
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.

        * Slide 2
        Content 2.
        """
        filter_str = "0:None"
        expected = """
        * Slide 1
        Content 1.

        * Slide 2

        """
        # Run test.
        self.helper(test_content, filter_str, expected)

    def test_slide_filtering_invalid_range(self) -> None:
        """
        Test that invalid slide ranges raise errors.
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        # Check outputs.
        with self.assertRaises(AssertionError):
            hmarfilt.filter_by_slides(lines, "1:0")

    def test_slide_filtering_beyond_slides(self) -> None:
        """
        Test filtering with end beyond available slides.
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        # Check outputs.
        with self.assertRaises(AssertionError):
            hmarfilt.filter_by_slides(lines, "0:5")

    def test_no_slides_content(self) -> None:
        """
        Test behavior with content that has no slides.
        """
        # Prepare inputs.
        test_content = """
        # Header 1
        Just regular content without slides.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        # Check outputs (should fail validation since there are no slides).
        with self.assertRaises(AssertionError):
            hmarfilt.filter_by_slides(lines, "0:1")

    def test_slide_filtering_single_slide(self) -> None:
        """
        Test filtering a single slide when there's only one slide (0-indexed).
        """
        # Prepare inputs.
        test_content = """
        * Only Slide
        This is the only content.
        Additional content after the slide.
        """
        filter_str = "0:1"
        expected = """
        * Only Slide
        This is the only content.
        """
        # Run test.
        self.helper(test_content, filter_str, expected)

    def test_slide_end_boundary(self) -> None:
        """
        Test filtering to the end of slides (0-indexed).
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.

        * Slide 2
        Content 2.
        """
        filter_str = "0:2"
        expected = """
        * Slide 1
        Content 1.

        * Slide 2

        """
        # Run test.
        self.helper(test_content, filter_str, expected)


# #############################################################################
# Test_additional_edge_cases1
# #############################################################################


class Test_additional_edge_cases1(hunitest.TestCase):
    def test_filter_by_header_with_subsection(self) -> None:
        """
        Test extracting a subsection header.
        """
        # Prepare inputs.
        test_content = """
        # Introduction
        This is the introduction.

        ## Subsection 1
        Content for subsection 1.

        ## Subsection 2
        Content for subsection 2.

        # Conclusion
        Final thoughts.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_header(lines, "Subsection 1")
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertIn("## Subsection 1", result_content)
        self.assertIn("Content for subsection 1.", result_content)

    def test_parse_range_edge_cases(self) -> None:
        """
        Test edge cases for range parsing (0-indexed).
        """
        # Run test.
        start, end = hmarfilt._parse_range("0:0", 1)
        # Check outputs.
        self.assertEqual(start, 0)
        self.assertEqual(end, 0)
        # Run test.
        start, end = hmarfilt._parse_range("None:None", 1000)
        # Check outputs.
        self.assertEqual(start, 0)
        self.assertEqual(end, 1000)

    def test_filter_lines_single_line(self) -> None:
        """
        Test filtering with empty range (0:0).
        """
        # Prepare inputs.
        test_content = "Single line content"
        lines = test_content.split("\n")
        # Run test (0:0 = empty range).
        result_lines = hmarfilt.filter_by_lines(lines, "0:0")
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertEqual(result_content, "")

    def test_filter_lines_exact_range(self) -> None:
        """
        Test filtering with exact boundaries (0-indexed).
        """
        # Prepare inputs.
        test_content = """
        Line 1
        Line 2
        Line 3
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test (0:2 = indices 0 and 1 = Line 1 and Line 2).
        result_lines = hmarfilt.filter_by_lines(lines, "0:2")
        result_content = "\n".join(result_lines)
        # Check outputs.
        expected = "Line 1\nLine 2"
        self.assertEqual(result_content, expected)

    def test_parse_range_invalid_formats(self) -> None:
        """
        Test various invalid range formats.
        """
        # Run test.
        with self.assertRaises(AssertionError):
            hmarfilt._parse_range("5", 10)
        # Run test.
        with self.assertRaises(AssertionError):
            hmarfilt._parse_range("", 10)
        # Run test.
        with self.assertRaises(ValueError):
            hmarfilt._parse_range("1:2:3", 10)


# #############################################################################
# Test_filter_by_name1
# #############################################################################


class Test_filter_by_name1(hunitest.TestCase):
    def helper(
        self, test_content: str, filter_name: str, num_slides: int, expected: str
    ) -> None:
        """
        Test helper for filter_by_name.

        :param test_content: multiline test content
        :param filter_name: slide name to filter by
        :param num_slides: number of slides to keep
        :param expected: expected filtered output
        """
        # Prepare inputs.
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_name(lines, filter_name, num_slides=num_slides)
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assert_equal(result_content, expected, dedent=True)

    def test_basic_name_filtering(self) -> None:
        """
        Test basic slide name filtering functionality.
        """
        # Prepare inputs.
        test_content = """
        * Introduction
        Content for introduction.

        * Main Topic
        Content for main topic.

        * Conclusion
        Content for conclusion.
        """
        filter_name = "Main Topic"
        num_slides = 1
        expected = """
        * Main Topic
        Content for main topic.

        """
        # Run test.
        self.helper(test_content, filter_name, num_slides, expected)

    def test_partial_name_matching(self) -> None:
        """
        Test partial name matching (case-sensitive).
        """
        # Prepare inputs.
        test_content = """
        * Introduction
        Content 1.

        * Advanced Topics
        Content 2.

        * Conclusion
        Content 3.
        """
        filter_name = "Topics"
        num_slides = 1
        expected = """
        * Advanced Topics
        Content 2.

        """
        # Run test.
        self.helper(test_content, filter_name, num_slides, expected)

    def test_multiple_slides_after_match(self) -> None:
        """
        Test keeping multiple slides after match (including matched slide).
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.

        * Slide 2
        Content 2.

        * Slide 3
        Content 3.

        * Slide 4
        Content 4.
        """
        filter_name = "Slide 2"
        num_slides = 3
        expected = """
        * Slide 2
        Content 2.

        * Slide 3
        Content 3.

        * Slide 4

        """
        # Run test.
        self.helper(test_content, filter_name, num_slides, expected)

    def test_no_matching_slides(self) -> None:
        """
        Test error when no slides match the name.
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.

        * Slide 2
        Content 2.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            hmarfilt.filter_by_name(lines, "NonExistent", num_slides=1)
        # Check outputs.
        self.assertIn("No slides found matching", str(cm.exception))

    def test_multiple_matching_slides(self) -> None:
        """
        Test error when multiple slides match the name.
        """
        # Prepare inputs.
        test_content = """
        * Introduction Topic
        Content 1.

        * Main Topic
        Content 2.

        * Conclusion
        Content 3.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test (both "Introduction Topic" and "Main Topic" contain "Topic").
        with self.assertRaises(AssertionError) as cm:
            hmarfilt.filter_by_name(lines, "Topic", num_slides=1)
        # Check outputs.
        self.assertIn("Multiple slides match", str(cm.exception))

    def test_case_sensitive_matching(self) -> None:
        """
        Test that matching is case-sensitive.
        """
        # Prepare inputs.
        test_content = """
        * Introduction
        Content 1.

        * Advanced Topics
        Content 2.

        * Conclusion
        Content 3.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test (lowercase "advanced" should NOT match "Advanced Topics").
        with self.assertRaises(AssertionError):
            hmarfilt.filter_by_name(lines, "advanced", num_slides=1)

    def test_match_at_end_of_slides(self) -> None:
        """
        Test matching slide at the end (no slides after it).
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.

        * Last Slide
        Content last.
        """
        filter_name = "Last Slide"
        num_slides = 5
        expected = """
        * Last Slide

        """
        # Run test.
        self.helper(test_content, filter_name, num_slides, expected)

    def test_num_slides_default(self) -> None:
        """
        Test default num_slides value (should be 5).
        """
        # Prepare inputs.
        test_content = """
        * Slide 1
        Content 1.

        * Slide 2
        Content 2.

        * Slide 3
        Content 3.

        * Slide 4
        Content 4.

        * Slide 5
        Content 5.

        * Slide 6
        Content 6.
        """
        filter_name = "Slide 1"
        num_slides = 5
        expected = """
        * Slide 1
        Content 1.

        * Slide 2
        Content 2.

        * Slide 3
        Content 3.

        * Slide 4
        Content 4.

        * Slide 5
        Content 5.

        """
        # Run test.
        self.helper(test_content, filter_name, num_slides, expected)
