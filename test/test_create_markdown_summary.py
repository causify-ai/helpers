import logging
import tempfile
from typing import List, Tuple
from unittest import mock

import helpers.hunit_test as hunitest
import helpers.hmarkdown as hmarkdo

import create_markdown_summary as crmasu

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_sections_at_level
# #############################################################################


class Test_extract_sections_at_level(hunitest.TestCase):
    def test_basic_sections(self) -> None:
        """
        Test extracting sections at level 2.
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",  # line 1
            "",             # line 2
            "Intro text",   # line 3
            "",             # line 4
            "## Section 1.1",  # line 5
            "",                 # line 6
            "Content of section 1.1",  # line 7
            "",                         # line 8
            "## Section 1.2",          # line 9
            "",                         # line 10
            "Content of section 1.2",  # line 11
            "",                         # line 12
            "# Chapter 2",              # line 13
            "",                         # line 14
            "Chapter 2 intro",          # line 15
        ]
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        max_level = 2
        # Evaluate the function.
        result = crmasu._extract_sections_at_level(lines, header_list, max_level)
        # Check output.
        self.assertEqual(len(result), 2)
        start1, end1, content1, chunk1 = result[0]
        self.assertEqual(start1, 5)
        self.assertEqual(end1, 8)  # Should end before the next section
        self.assertIn("Section 1.1", content1)
        self.assertEqual(chunk1, 1)
        # Check second section.
        start2, end2, content2, chunk2 = result[1]
        self.assertEqual(start2, 9)
        self.assertEqual(end2, 12)  # Should end before the next chapter
        self.assertIn("Section 1.2", content2)
        self.assertEqual(chunk2, 2)

    def test_single_section(self) -> None:
        """
        Test extracting a single section.
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",       # line 1
            "",                  # line 2
            "## Section 1.1",   # line 3
            "",                  # line 4
            "Content here",      # line 5
        ]
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        max_level = 2
        # Evaluate the function.
        result = crmasu._extract_sections_at_level(lines, header_list, max_level)
        # Check output.
        self.assertEqual(len(result), 1)
        start, end, content, chunk = result[0]
        self.assertEqual(start, 3)
        self.assertEqual(end, 5)
        self.assertIn("Section 1.1", content)
        self.assertEqual(chunk, 1)


# #############################################################################
# Test_summarize_section_with_llm
# #############################################################################


class Test_summarize_section_with_llm(hunitest.TestCase):
    @mock.patch('create_markdown_summary.hsystem.system_to_string')
    @mock.patch('create_markdown_summary.hio.to_file')
    def test_summarize_basic(self, mock_to_file, mock_system_to_string) -> None:
        """
        Test basic LLM summarization functionality.
        """
        # Prepare inputs.
        content = "## Test Section\n\nThis is test content with details."
        max_num_bullets = 3
        # Mock LLM response.
        mock_system_to_string.return_value = (0, "- Summary point 1\n- Summary point 2")
        # Evaluate the function.
        result = crmasu._summarize_section_with_llm(content, max_num_bullets)
        # Check output.
        self.assertEqual(result, "- Summary point 1\n- Summary point 2")
        # Verify mocks were called correctly.
        mock_to_file.assert_called_once()
        mock_system_to_string.assert_called_once()
        call_args = mock_system_to_string.call_args[0][0]
        self.assertIn("llm -m gpt-4o-mini", call_args)
        self.assertIn("summarize it into up to 3 bullets", call_args)


# #############################################################################
# Test_create_output_structure
# #############################################################################


class Test_create_output_structure(hunitest.TestCase):
    def test_basic_structure(self) -> None:
        """
        Test creating output structure with summaries.
        """
        # Prepare inputs.
        lines = [
            "# Chapter 1",          # line 1
            "",                     # line 2
            "Intro text",           # line 3
            "",                     # line 4
            "## Section 1.1",      # line 5
            "",                     # line 6
            "Original content",     # line 7
            "",                     # line 8
        ]
        header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=2)
        sections = [
            (5, 8, "- Summary bullet point", 1)
        ]
        max_level = 2
        input_file = "test.md"
        # Evaluate the function.
        result = crmasu._create_output_structure(
            sections, header_list, max_level, input_file, lines
        )
        # Check output.
        self.assertIn("# Chapter 1", result)
        self.assertIn("Intro text", result)
        self.assertIn("## Section 1.1", result)
        self.assertIn("// From test.md: [5, 8]", result)
        self.assertIn("- Summary bullet point", result)
        # Original content should be replaced.
        self.assertNotIn("Original content", result)


# #############################################################################
# Test_validate_llm_availability
# #############################################################################


class Test_validate_llm_availability(hunitest.TestCase):
    @mock.patch('create_markdown_summary.hsystem.system')
    def test_llm_available(self, mock_system) -> None:
        """
        Test when LLM command is available.
        """
        # Mock successful command.
        mock_system.return_value = None
        # Evaluate the function - should not raise.
        crmasu._validate_llm_availability()
        # Verify correct command was called.
        mock_system.assert_called_once_with("which llm", suppress_output=True)

    @mock.patch('create_markdown_summary.hsystem.system')
    def test_llm_not_available(self, mock_system) -> None:
        """
        Test when LLM command is not available.
        """
        # Mock command failure.
        mock_system.side_effect = Exception("Command not found")
        # Evaluate the function - should raise.
        with self.assertRaises(Exception):
            crmasu._validate_llm_availability()


# #############################################################################
# Test_action_preview_chunks
# #############################################################################


class Test_action_preview_chunks(hunitest.TestCase):
    @mock.patch('create_markdown_summary.hparser.write_file')
    @mock.patch('create_markdown_summary.hparser.read_file')
    def test_preview_chunks_basic(self, mock_read_file, mock_write_file) -> None:
        """
        Test preview_chunks action with basic markdown.
        """
        # Prepare inputs.
        mock_read_file.return_value = [
            "# Chapter 1",
            "",
            "## Section 1.1",
            "Content here",
            "",
            "## Section 1.2", 
            "More content",
        ]
        input_file = "test.md"
        output_file = "test_preview.md"
        max_level = 2
        # Evaluate the function.
        crmasu._action_preview_chunks(input_file, output_file, max_level)
        # Check that write_file was called.
        mock_write_file.assert_called_once()
        written_content = mock_write_file.call_args[0][0]
        # Check output contains expected markers.
        self.assertIn("start chunk 1", written_content)
        self.assertIn("end chunk 1", written_content)
        self.assertIn("start chunk 2", written_content)
        self.assertIn("end chunk 2", written_content)
        self.assertIn("Section 1.1", written_content)
        self.assertIn("Section 1.2", written_content)


# #############################################################################
# Test_action_check_output
# #############################################################################


class Test_action_check_output(hunitest.TestCase):
    @mock.patch('create_markdown_summary.hsystem.system')
    @mock.patch('create_markdown_summary.hparser.write_file')
    @mock.patch('create_markdown_summary.hparser.read_file')
    def test_check_output_basic(self, mock_read_file, mock_write_file, mock_system) -> None:
        """
        Test check_output action with matching structures.
        """
        # Prepare inputs.
        input_lines = [
            "# Chapter 1",
            "## Section 1.1",
            "Content",
        ]
        output_lines = [
            "# Chapter 1", 
            "## Section 1.1",
            "// From test.md: [2, 3]",
            "- Summary",
        ]
        mock_read_file.side_effect = [input_lines, output_lines]
        input_file = "test.md"
        output_file = "test_output.md"
        max_level = 2
        # Evaluate the function.
        try:
            crmasu._action_check_output(input_file, output_file, max_level)
        except Exception:
            # Should not raise even if structures differ.
            pass
        # Check that temporary files were written.
        self.assertEqual(mock_write_file.call_count, 2)
        # Check that sdiff command was called.
        mock_system.assert_called_once()
        call_args = mock_system.call_args[0][0]
        self.assertIn("sdiff", call_args)
        self.assertIn("tmp.headers_in.md", call_args)
        self.assertIn("tmp.headers_out.md", call_args)


# #############################################################################
# Integration Tests
# #############################################################################


class Test_integration(hunitest.TestCase):
    def test_end_to_end_preview_chunks(self) -> None:
        """
        Test end-to-end preview_chunks functionality.
        """
        # Create temporary markdown file.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as input_f:
            input_f.write("""# Chapter 1

## Section 1.1
Content of section 1.1

## Section 1.2  
Content of section 1.2
""")
            input_file = input_f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as output_f:
            output_file = output_f.name
        
        try:
            # Test preview_chunks.
            crmasu._action_preview_chunks(input_file, output_file, 2)
            
            # Read the output file.
            with open(output_file, 'r') as f:
                output_content = f.read()
                
            self.assertIn("start chunk 1", output_content)
            self.assertIn("end chunk 1", output_content)
            self.assertIn("Section 1.1", output_content)
        finally:
            import os
            os.unlink(input_file)
            os.unlink(output_file)

    @mock.patch('create_markdown_summary.hsystem.system_to_string')
    @mock.patch('create_markdown_summary._validate_llm_availability')
    def test_end_to_end_summarize(self, mock_validate_llm, mock_system_to_string) -> None:
        """
        Test end-to-end summarize functionality.
        """
        # Mock LLM availability and response.
        mock_validate_llm.return_value = None
        mock_system_to_string.return_value = (0, "- Test summary point")
        
        # Create temporary files.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as input_f:
            input_f.write("""# Chapter 1

## Section 1.1
This is content that will be summarized.
""")
            input_file = input_f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as output_f:
            output_file = output_f.name
        
        try:
            # Test summarize action.
            crmasu._action_summarize(input_file, output_file, 2, 3)
            
            # Read the output file.
            with open(output_file, 'r') as f:
                output_content = f.read()
            
            # Check expected content.
            self.assertIn("# Chapter 1", output_content)
            self.assertIn("## Section 1.1", output_content)
            self.assertIn("// From", output_content)
            self.assertIn("- Test summary point", output_content)
            
        finally:
            import os
            os.unlink(input_file)
            os.unlink(output_file)