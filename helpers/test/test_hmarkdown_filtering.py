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
    def test_numeric_range(self) -> None:
        """
        Test parsing numeric range.
        """
        # Prepare inputs.
        # Run test.
        start, end = hmarfilt._parse_range("1:10", 20)
        # Check outputs.
        self.assertEqual(start, 1)
        self.assertEqual(end, 10)

    def test_none_start(self) -> None:
        """
        Test range with None start.
        """
        # Run test.
        start, end = hmarfilt._parse_range("None:10", 20)
        # Check outputs.
        self.assertEqual(start, 1)
        self.assertEqual(end, 10)

    def test_none_end(self) -> None:
        """
        Test range with None end.
        """
        # Run test.
        start, end = hmarfilt._parse_range("1:None", 20)
        # Check outputs.
        self.assertEqual(start, 1)
        self.assertEqual(end, 21)

    def test_both_none(self) -> None:
        """
        Test range with both None.
        """
        # Run test.
        start, end = hmarfilt._parse_range("None:None", 20)
        # Check outputs.
        self.assertEqual(start, 1)
        self.assertEqual(end, 21)

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
        # Run test.
        start, end = hmarfilt._parse_range("NONE:none", 20)
        # Check outputs.
        self.assertEqual(start, 1)
        self.assertEqual(end, 21)


# #############################################################################
# Test_filter_by_lines1
# #############################################################################


class Test_filter_by_lines1(hunitest.TestCase):
    def test_basic_line_filtering(self) -> None:
        """
        Test basic line filtering functionality.
        """
        # Prepare inputs.
        test_content = """
        Line 1
        Line 2
        Line 3
        Line 4
        Line 5
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_lines(lines, "2:4")
        result_content = "\n".join(result_lines)
        # Check outputs.
        expected = "Line 2\nLine 3"
        self.assertEqual(result_content, expected)

    def test_line_filtering_with_none(self) -> None:
        """
        Test line filtering with None boundaries.
        """
        # Prepare inputs.
        test_content = """
        Line 1
        Line 2
        Line 3
        Line 4
        Line 5
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_lines(lines, "None:3")
        result_content = "\n".join(result_lines)
        # Check outputs.
        expected = "Line 1\nLine 2"
        self.assertEqual(result_content, expected)

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
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_lines(lines, "2:None")
        result_content = "\n".join(result_lines)
        # Check outputs.
        expected = "Line 2\nLine 3"
        self.assertEqual(result_content, expected)

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
            hmarfilt.filter_by_lines(lines, "3:1")


# #############################################################################
# Test_filter_by_slides1
# #############################################################################


class Test_filter_by_slides1(hunitest.TestCase):
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
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_slides(lines, "0:1")
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertIn("Slide 1", result_content)
        self.assertNotIn("Slide 2", result_content)

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
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_slides(lines, "0:None")
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertIn("Slide 1", result_content)
        self.assertIn("Slide 2", result_content)

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
        # Check outputs.
        with self.assertRaises(IndexError):
            hmarfilt.filter_by_slides(lines, "0:1")

    def test_slide_filtering_single_slide(self) -> None:
        """
        Test filtering a single slide when there's only one slide.
        """
        # Prepare inputs.
        test_content = """
        * Only Slide
        This is the only content.
        Additional content after the slide.
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_slides(lines, "0:2")
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertIn("Only Slide", result_content)
        self.assertIn("This is the only content.", result_content)

    def test_slide_end_boundary(self) -> None:
        """
        Test filtering to the end of slides.
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
        result_lines = hmarfilt.filter_by_slides(lines, "0:3")
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertIn("Slide 1", result_content)
        self.assertIn("Slide 2", result_content)


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
        Test edge cases for range parsing.
        """
        # Prepare inputs.
        # Run test.
        start, end = hmarfilt._parse_range("1:1", 1)
        # Check outputs.
        self.assertEqual(start, 1)
        self.assertEqual(end, 1)
        # Prepare inputs.
        # Run test.
        start, end = hmarfilt._parse_range("None:None", 1000)
        # Check outputs.
        self.assertEqual(start, 1)
        self.assertEqual(end, 1001)

    def test_filter_lines_single_line(self) -> None:
        """
        Test filtering a single line from text.
        """
        # Prepare inputs.
        test_content = "Single line content"
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_lines(lines, "1:1")
        result_content = "\n".join(result_lines)
        # Check outputs.
        self.assertEqual(result_content, "")

    def test_filter_lines_exact_range(self) -> None:
        """
        Test filtering with exact boundaries.
        """
        # Prepare inputs.
        test_content = """
        Line 1
        Line 2
        Line 3
        """
        test_content = hprint.dedent(test_content)
        lines = test_content.split("\n")
        # Run test.
        result_lines = hmarfilt.filter_by_lines(lines, "1:3")
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
