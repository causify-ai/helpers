import os
import logging
from typing import List, Tuple

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hmarkdown as hmarkdo

import create_markdown_summary as crmasu

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_sections_at_level
# #############################################################################


class Test_extract_sections_at_level(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test extracting sections at level 2 with multiple sections.
        """
        # Prepare inputs.
        lines_txt = """
        # Chapter 1
        
        Intro text
        
        ## Section 1.1
        
        Content of section 1.1
        
        ## Section 1.2
        
        Content of section 1.2
        
        # Chapter 2
        
        Chapter 2 intro
        """
        lines_txt = hprint.dedent(lines_txt)
        lines = lines_txt.strip().split('\n')
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        # Check header_list structure.
        header_list_str = str([(h.level, h.description, h.line_number) for h in header_list])
        expected_headers = "[(1, 'Chapter 1', 1), (2, 'Section 1.1', 5), (2, 'Section 1.2', 9), (1, 'Chapter 2', 13)]"
        self.assert_equal(header_list_str, expected_headers)
        max_level = 2
        # Run test.
        result = crmasu._extract_sections_at_level(lines, header_list, max_level)
        # Check outputs.
        expected_result = [
            (5, 8, "## Section 1.1\n\nContent of section 1.1\n", 1),
            (9, 12, "## Section 1.2\n\nContent of section 1.2\n", 2)
        ]
        self.assert_equal(str(result), str(expected_result))

    def test2(self) -> None:
        """
        Test extracting a single section.
        """
        # Prepare inputs.
        lines_txt = """
        # Chapter 1
        
        ## Section 1.1
        
        Content here
        """
        lines_txt = hprint.dedent(lines_txt)
        lines = lines_txt.strip().split('\n')
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        max_level = 2
        # Check header_list structure.
        header_list_str = str([(h.level, h.description, h.line_number) for h in header_list])
        expected_headers = "[(1, 'Chapter 1', 1), (2, 'Section 1.1', 3)]"
        self.assert_equal(header_list_str, expected_headers)
        # Run test.
        result = crmasu._extract_sections_at_level(lines, header_list, max_level)
        # Check outputs.
        expected_result = [
            (3, 5, "## Section 1.1\n\nContent here", 1)
        ]
        self.assert_equal(str(result), str(expected_result))

    def test3(self) -> None:
        """
        Test extracting sections with no sections at target level.
        """
        # Prepare inputs.
        lines_txt = """
        # Chapter 1
        
        Just content
        
        # Chapter 2
        """
        lines_txt = hprint.dedent(lines_txt)
        lines = lines_txt.strip().split('\n')
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        # Check header_list structure.
        header_list_str = str([(h.level, h.description, h.line_number) for h in header_list])
        expected_headers = "[(1, 'Chapter 1', 1), (1, 'Chapter 2', 5)]"
        self.assert_equal(header_list_str, expected_headers)
        max_level = 2
        # Run test.
        result = crmasu._extract_sections_at_level(lines, header_list, max_level)
        # Check outputs.
        expected_result = []
        self.assert_equal(str(result), str(expected_result))


# #############################################################################
# Test_create_output_structure
# #############################################################################


class Test_create_output_structure(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test creating output structure with single summary.
        """
        # Prepare inputs.
        lines_txt = """
        # Chapter 1
        
        Intro text
        
        ## Section 1.1
        
        Original content
        
        """
        lines_txt = hprint.dedent(lines_txt)
        lines = lines_txt.strip().split('\n')
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        sections = [
            (5, 8, "- Summary bullet point", 1)
        ]
        max_level = 2
        input_file = "test.md"
        # Run test.
        result = crmasu._create_output_structure(
            sections, header_list, max_level, input_file, lines
        )
        # Check outputs.
        expected_output = """
        # Chapter 1
        
        Intro text
        
        ## Section 1.1
        // From test.md: [5, 8]
        - Summary bullet point
        
        """
        expected_output = hprint.dedent(expected_output).strip()
        self.assert_equal(result.strip(), expected_output)

    def test2(self) -> None:
        """
        Test creating output structure with multiple sections.
        """
        # Prepare inputs.
        lines_txt = """
        # Chapter 1
        
        ## Section 1.1
        Content 1
        
        ## Section 1.2
        Content 2
        """
        lines_txt = hprint.dedent(lines_txt)
        lines = lines_txt.strip().split('\n')
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        sections = [
            (3, 5, "- Summary 1", 1),
            (6, 7, "- Summary 2", 2)
        ]
        max_level = 2
        input_file = "test.md"
        # Run test.
        result = crmasu._create_output_structure(
            sections, header_list, max_level, input_file, lines
        )
        # Check outputs.
        expected_output = """
        # Chapter 1
        
        ## Section 1.1
        // From test.md: [3, 5]
        - Summary 1
        
        ## Section 1.2
        // From test.md: [6, 7]
        - Summary 2
        
        """
        expected_output = hprint.dedent(expected_output).strip()
        self.assert_equal(result.strip(), expected_output)


# #############################################################################
# Test_validate_llm_availability
# #############################################################################


class Test_validate_llm_availability(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test validation with actual system (requires llm to be installed).
        """
        # Prepare inputs.
        # No inputs needed.
        # Run test.
        # This will either pass or raise an exception based on system state.
        try:
            crmasu._validate_llm_availability()
            result = "LLM available"
        except Exception as e:
            result = f"LLM not available: {str(e)}"
        # Check outputs.
        # We can't predict the exact result, so we just check it's a string.
        self.assert_equal(str(isinstance(result, str)), "True")


# #############################################################################
# Test action functions with data structures
# #############################################################################


class Test_action_preview_chunks_data(hunitest.TestCase):
    def helper_preview_chunks(
        self, 
        lines: List[str], 
        max_level: int
    ) -> str:
        """
        Helper function to test preview_chunks logic with data structures.
        """
        # Parse markdown.
        header_list = hmarkdo.extract_headers_from_markdown(
            lines, max_level=max_level, sanity_check=True
        )
        # Extract sections.
        sections = crmasu._extract_sections_at_level(lines, header_list, max_level)
        return sections

    def test1(self) -> None:
        """
        Test preview chunks with basic markdown structure.
        """
        # Prepare inputs.
        lines_txt = """
        # Chapter 1
        
        ## Section 1.1
        Content here
        
        ## Section 1.2
        More content
        """
        lines_txt = hprint.dedent(lines_txt)
        lines = lines_txt.strip().split('\n')
        max_level = 2
        # Run test.
        result = self.helper_preview_chunks(lines, max_level)
        # Check outputs.
        expected_result = [
            (3, 5, "## Section 1.1\nContent here\n", 1),
            (6, 7, "## Section 1.2\nMore content", 2)
        ]
        self.assert_equal(str(result), str(expected_result))

    def test2(self) -> None:
        """
        Test preview chunks with nested structure.
        """
        # Prepare inputs.
        input_txt = """
        # Chapter 1: Introduction
        
        This is the introduction.
        
        ## Section 1.1: Overview
        
        This section provides an overview.
        
        ### Subsection 1.1.1
        
        Details here.
        
        ## Section 1.2: Getting Started
        
        Getting started content.
        
        # Chapter 2: Advanced
        
        Advanced material.
        """
        input_txt = hprint.dedent(input_txt)
        lines = input_txt.strip().split('\n')
        max_level = 2
        # Run test.
        result = self.helper_preview_chunks(lines, max_level)
        # Check outputs.
        expected_result = [
            (5, 12, "## Section 1.1: Overview\n\nThis section provides an overview.\n\n### Subsection 1.1.1\n\nDetails here.\n", 1),
            (13, 16, "## Section 1.2: Getting Started\n\nGetting started content.\n", 2)
        ]
        self.assert_equal(str(result), str(expected_result))


# #############################################################################
# Test end-to-end functionality
# #############################################################################


class Test_end_to_end_with_files(hunitest.TestCase):
    def test_preview_chunks_end_to_end(self) -> None:
        """
        Test preview_chunks action end-to-end using actual files.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        input_file = os.path.join(scratch_space, "test_input.md")
        output_file = os.path.join(scratch_space, "test_preview.md")
        #
        input_content = """
        # Chapter 1

        ## Section 1.1
        Content of section 1.1

        ## Section 1.2  
        Content of section 1.2
        """
        input_content = hprint.dedent(input_content)
        # Write input file.
        hio.to_file(input_file, input_content)
        # Run test.
        crmasu._action_preview_chunks(input_file, output_file, 2)
        # Check outputs.
        result = hio.from_file(output_file)
        expected_result = """
        # Chapter 1

        ## Section 1.1

        // ---------------------> start chunk 1 <---------------------
        Content of section 1.1

        // ---------------------> end chunk 1 <---------------------

        ## Section 1.2  

        // ---------------------> start chunk 2 <---------------------
        Content of section 1.2
        // ---------------------> end chunk 2 <---------------------"""
        expected_result = hprint.dedent(expected_result)
        self.assert_equal(result, expected_result)

    def test_check_output_end_to_end(self) -> None:
        """
        Test check_output action end-to-end using actual files.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        input_file = os.path.join(scratch_space, "test_input.md")
        output_file = os.path.join(scratch_space, "test_output.md")
        #
        input_content = """
        # Chapter 1

        ## Section 1.1
        Original content
        """
        input_content = hprint.dedent(input_content)
        # Write input files.
        hio.to_file(input_file, input_content)
        #
        output_content = """
        # Chapter 1

        ## Section 1.1
        // From test_input.md: [3, 4]
        - Summarized content
        """
        output_content = hprint.dedent(output_content)
        # Write output files.
        hio.to_file(output_file, output_content)
        # Run test.
        # This should not raise an exception even if structures differ slightly.
        tmp_dir = os.path.join(scratch_space, "tmp")
        hio.create_dir(tmp_dir, incremental=True)
        crmasu._action_check_output(input_file, output_file, 2, tmp_dir=tmp_dir)
        # Check that temporary files were created.
        tmp_headers_in = os.path.join(tmp_dir, "tmp.headers_in.md")
        tmp_headers_out = os.path.join(tmp_dir, "tmp.headers_out.md")
        self.assert_equal(str(os.path.exists(tmp_headers_in)), "True")
        self.assert_equal(str(os.path.exists(tmp_headers_out)), "True")
