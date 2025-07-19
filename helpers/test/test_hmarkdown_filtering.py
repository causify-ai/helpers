import logging
import os

import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
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
        # Prepare test markdown content.
        test_content = """
        # Introduction
        This is the introduction section.
        Some content here.

        ## Section 1
        Content for section 1.

        # Conclusion  
        Final thoughts here.
        """
        test_content = hmarkdo.dedent(test_content, remove_lead_trail_empty_lines_=False)
        # Create temporary file.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        # Test function.
        result_file = hmarkdo.filter_by_header(input_file, "Introduction", "test_prefix")
        # Verify result.
        self.assertTrue(os.path.exists(result_file))
        result_content = hio.from_file(result_file)
        expected = """# Introduction
        This is the introduction section.
        Some content here.

        ## Section 1
        Content for section 1.
        """
        self.assert_equal(result_content, expected)

    def test_header_not_found(self) -> None:
        """
        Test behavior when header is not found.
        """
        test_content = """# Introduction
This is the introduction section.
"""
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        with self.assertRaises(ValueError):
            hmarkfil.filter_by_header(input_file, "NonExistent", "test_prefix")


# #############################################################################
# Test_parse_range1
# #############################################################################


class Test_parse_range1(hunitest.TestCase):
    def test_numeric_range(self) -> None:
        """
        Test parsing numeric range.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        start, end = hmarkfil._parse_range("1:10", 20)
        self.assertEqual(start, 1)
        self.assertEqual(end, 10)

    def test_none_start(self) -> None:
        """
        Test range with None start.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        start, end = hmarkfil._parse_range("None:10", 20)
        self.assertEqual(start, 1)
        self.assertEqual(end, 10)

    def test_none_end(self) -> None:
        """
        Test range with None end.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        start, end = hmarkfil._parse_range("1:None", 20)
        self.assertEqual(start, 1)
        self.assertEqual(end, 21)

    def test_both_none(self) -> None:
        """
        Test range with both None.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        start, end = hmarkfil._parse_range("None:None", 20)
        self.assertEqual(start, 1)
        self.assertEqual(end, 21)

    def test_invalid_range(self) -> None:
        """
        Test invalid range format.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        with self.assertRaises(AssertionError):
            hmarkfil._parse_range("invalid", 20)

    def test_case_insensitive_none(self) -> None:
        """
        Test case insensitive None parsing.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        start, end = hmarkfil._parse_range("NONE:none", 20)
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
        test_content = """Line 1
Line 2
Line 3
Line 4
Line 5"""
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.txt")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_lines(input_file, "2:4", "test_prefix")
        
        self.assertTrue(os.path.exists(result_file))
        result_content = hio.from_file(result_file)
        expected = "Line 2\nLine 3"
        self.assertEqual(result_content, expected)

    def test_line_filtering_with_none(self) -> None:
        """
        Test line filtering with None boundaries.
        """
        test_content = """Line 1
Line 2
Line 3
Line 4
Line 5"""
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.txt")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_lines(input_file, "None:3", "test_prefix")
        
        result_content = hio.from_file(result_file)
        expected = "Line 1\nLine 2"
        self.assertEqual(result_content, expected)

    def test_line_filtering_to_end(self) -> None:
        """
        Test line filtering from start to end.
        """
        test_content = """Line 1
Line 2
Line 3"""
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.txt")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_lines(input_file, "2:None", "test_prefix")
        
        result_content = hio.from_file(result_file)
        expected = "Line 2\nLine 3"
        self.assertEqual(result_content, expected)

    def test_invalid_range_order(self) -> None:
        """
        Test that start line <= end line is enforced.
        """
        test_content = "Line 1\nLine 2\nLine 3"
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.txt")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        with self.assertRaises(AssertionError):
            hmarkfil.filter_by_lines(input_file, "3:1", "test_prefix")


# #############################################################################
# Test_filter_by_slides1
# #############################################################################


class Test_filter_by_slides1(hunitest.TestCase):
    def test_basic_slide_filtering(self) -> None:
        """
        Test basic slide filtering functionality.
        """
        test_content = """# Header 1

* Slide 1
Content for slide 1.

* Slide 2
Content for slide 2.

* Slide 3
Content for slide 3."""
        
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_slides(input_file, "0:1", "test_prefix")
        
        self.assertTrue(os.path.exists(result_file))
        result_content = hio.from_file(result_file)
        # The result should contain the first slide only (0-based indexing)
        self.assertIn("Slide 1", result_content)
        self.assertNotIn("Slide 2", result_content)

    def test_slide_filtering_with_none_end(self) -> None:
        """
        Test slide filtering to the end.
        """
        test_content = """* Slide 1
Content 1.

* Slide 2  
Content 2."""
        
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_slides(input_file, "0:None", "test_prefix")
        
        result_content = hio.from_file(result_file)
        self.assertIn("Slide 1", result_content)
        self.assertIn("Slide 2", result_content)

    def test_slide_filtering_invalid_range(self) -> None:
        """
        Test that invalid slide ranges raise errors.
        """
        test_content = """* Slide 1
Content 1."""
        
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        with self.assertRaises(AssertionError):
            hmarkfil.filter_by_slides(input_file, "1:0", "test_prefix")

    def test_slide_filtering_beyond_slides(self) -> None:
        """
        Test filtering with end beyond available slides.
        """
        test_content = """* Slide 1
Content 1."""
        
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        with self.assertRaises(AssertionError):
            hmarkfil.filter_by_slides(input_file, "0:5", "test_prefix")

    def test_no_slides_content(self) -> None:
        """
        Test behavior with content that has no slides.
        """
        test_content = """# Header 1
Just regular content without slides."""
        
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        # This should handle the case where there are no slides
        # The function raises IndexError when trying to access slides that don't exist
        with self.assertRaises(IndexError):
            # This should fail since there are no slides but we're trying to access slide 0
            hmarkfil.filter_by_slides(input_file, "0:1", "test_prefix")

    def test_slide_filtering_single_slide(self) -> None:
        """
        Test filtering a single slide when there's only one slide.
        """
        test_content = """* Only Slide
This is the only content.
Additional content after the slide."""
        
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        # For 1 slide at index 0, end_slide of 2 means "to end of file" 
        result_file = hmarkfil.filter_by_slides(input_file, "0:2", "test_prefix")
        
        result_content = hio.from_file(result_file)
        self.assertIn("Only Slide", result_content)
        self.assertIn("This is the only content.", result_content)
        # Due to the current implementation, this should include content up to (but not including) the last line

    def test_slide_end_boundary(self) -> None:
        """
        Test filtering to the end of slides.
        """
        test_content = """* Slide 1
Content 1.

* Slide 2
Content 2."""
        
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        # Test filtering with end equal to number of slides + 1 (should include all slides to end)
        # For 2 slides (indices 0, 1), end_slide of 3 means "to end of file"
        result_file = hmarkfil.filter_by_slides(input_file, "0:3", "test_prefix")
        
        result_content = hio.from_file(result_file)
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
        test_content = """# Introduction
This is the introduction.

## Subsection 1
Content for subsection 1.

## Subsection 2
Content for subsection 2.

# Conclusion
Final thoughts.
"""
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.md")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_header(input_file, "Subsection 1", "test_prefix")
        
        result_content = hio.from_file(result_file)
        self.assertIn("## Subsection 1", result_content)
        self.assertIn("Content for subsection 1.", result_content)

    def test_parse_range_edge_cases(self) -> None:
        """
        Test edge cases for range parsing.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        
        # Test with single line file
        start, end = hmarkfil._parse_range("1:1", 1)
        self.assertEqual(start, 1)
        self.assertEqual(end, 1)
        
        # Test with large max value
        start, end = hmarkfil._parse_range("None:None", 1000)
        self.assertEqual(start, 1)
        self.assertEqual(end, 1001)

    def test_filter_lines_single_line(self) -> None:
        """
        Test filtering a single line from file.
        """
        test_content = "Single line content"
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.txt")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_lines(input_file, "1:1", "test_prefix")
        
        result_content = hio.from_file(result_file)
        self.assertEqual(result_content, "")  # Should be empty since range is [1:1) exclusive end

    def test_filter_lines_exact_range(self) -> None:
        """
        Test filtering with exact boundaries.
        """
        test_content = """Line 1
Line 2
Line 3"""
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_input.txt")
        hio.to_file(input_file, test_content)
        
        import helpers.hmarkdown_filtering as hmarkfil
        result_file = hmarkfil.filter_by_lines(input_file, "1:3", "test_prefix")
        
        result_content = hio.from_file(result_file)
        expected = "Line 1\nLine 2"
        self.assertEqual(result_content, expected)

    def test_parse_range_invalid_formats(self) -> None:
        """
        Test various invalid range formats.
        """
        import helpers.hmarkdown_filtering as hmarkfil
        
        # Test missing colon
        with self.assertRaises(AssertionError):
            hmarkfil._parse_range("5", 10)
            
        # Test empty string
        with self.assertRaises(AssertionError):
            hmarkfil._parse_range("", 10)
            
        # Test too many colons - this actually causes a ValueError when trying to parse "1:2" as int
        with self.assertRaises(ValueError):
            hmarkfil._parse_range("1:2:3", 10)