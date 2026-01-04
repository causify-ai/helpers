import logging
import os

import dev_scripts_helpers.coding_tools.split_in_files as dshctsifi
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)



# #############################################################################
# Test_parse_file_content
# #############################################################################

class Test_parse_file_content(hunitest.TestCase):
    """
    Test parsing file content and extracting sections based on tags.
    """

    # TODO(ai_gp): Rename to test1, test2, ...
    def test_parse_file_content_with_common_section(self) -> None:
        """
        Test parsing file with <start_common> and multiple file sections.

        Expected input:
        ```
        <start_common>
        Common header
        <start:file1.txt>
        Content for file1
        <start:file2.txt>
        Content for file2
        ```

        Expected output:
        - common_section = "\\nCommon header\\n"
        - sections = {
            "file1.txt": "\\nContent for file1\\n",
            "file2.txt": "\\nContent for file2\\n"
          }
        """
        # Prepare inputs.
        content = """<start_common>
Common header
<start:file1.txt>
Content for file1
<start:file2.txt>
Content for file2
"""
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        expected_common = "\nCommon header\n"
        self.assert_equal(common_section, expected_common)
        expected_sections = {
            "file1.txt": ["\nContent for file1\n"],
            "file2.txt": ["\nContent for file2\n"],
        }
        self.assert_equal(str(sections), str(expected_sections))
        self.assertEqual(len(line_ranges), 2)
        self.assertEqual(common_line_range, (1, 3))

    def test_parse_file_content_without_common_section(self) -> None:
        """
        Test parsing file without <start_common> section.

        Expected input:
        ```
        <start:file1.txt>
        Content for file1
        <start:file2.txt>
        Content for file2
        ```

        Expected output:
        - common_section = ""
        - sections = {
            "file1.txt": "\\nContent for file1\\n",
            "file2.txt": "\\nContent for file2\\n"
          }
        """
        # Prepare inputs.
        content = """<start:file1.txt>
Content for file1
<start:file2.txt>
Content for file2
"""
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        self.assert_equal(common_section, "")
        expected_sections = {
            "file1.txt": ["\nContent for file1\n"],
            "file2.txt": ["\nContent for file2\n"],
        }
        self.assert_equal(str(sections), str(expected_sections))
        self.assertEqual(len(line_ranges), 2)
        self.assertEqual(common_line_range, None)

    def test_parse_file_content_single_file(self) -> None:
        """
        Test parsing file with single file section.

        Expected input:
        ```
        <start:output.txt>
        Single file content
        ```

        Expected output:
        - common_section = ""
        - sections = {"output.txt": "\\nSingle file content\\n"}
        """
        # Prepare inputs.
        content = """<start:output.txt>
Single file content
"""
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        self.assert_equal(common_section, "")
        expected_sections = {"output.txt": ["\nSingle file content\n"]}
        self.assert_equal(str(sections), str(expected_sections))
        self.assertEqual(len(line_ranges), 1)
        self.assertEqual(common_line_range, None)

    def test_parse_file_content_no_tags_raises_error(self) -> None:
        """
        Test that file without any tags raises assertion error.

        Expected input:
        ```
        Just plain text without any tags
        ```

        Expected: AssertionError
        """
        # Prepare inputs.
        content = "Just plain text without any tags\n"
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshctsifi._parse_file_content(content)

    def test_parse_file_content_only_common_tag_raises_error(self) -> None:
        """
        Test that file with only <start_common> and no file tags raises error.

        Expected input:
        ```
        <start_common>
        Common content only
        ```

        Expected: AssertionError
        """
        # Prepare inputs.
        content = """<start_common>
Common content only
"""
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshctsifi._parse_file_content(content)

    def test_parse_file_content_multiple_chunks_same_filename(self) -> None:
        """
        Test parsing file with multiple chunks for the same filename.

        Expected input:
        ```
        <start:output.txt>
        First chunk
        <start:output.txt>
        Second chunk
        <start:output.txt>
        Third chunk
        ```

        Expected output:
        - sections = {"output.txt": [chunk1, chunk2, chunk3]}
        - line_ranges = {"output.txt": [(1,2), (2,3), (3,4)]}
        """
        # Prepare inputs.
        content = """<start:output.txt>
First chunk
<start:output.txt>
Second chunk
<start:output.txt>
Third chunk
"""
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        self.assert_equal(common_section, "")
        self.assertEqual(len(sections), 1)
        self.assertIn("output.txt", sections)
        self.assertEqual(len(sections["output.txt"]), 3)
        self.assert_equal(sections["output.txt"][0], "\nFirst chunk\n")
        self.assert_equal(sections["output.txt"][1], "\nSecond chunk\n")
        self.assert_equal(sections["output.txt"][2], "\nThird chunk\n")
        self.assertEqual(len(line_ranges["output.txt"]), 3)

    def test_parse_file_content_mixed_multiple_and_single_chunks(self) -> None:
        """
        Test parsing with some files having multiple chunks, others single.

        Expected input:
        ```
        <start:file1.txt>
        File1 chunk1
        <start:file2.txt>
        File2 only chunk
        <start:file1.txt>
        File1 chunk2
        ```

        Expected output:
        - sections = {
            "file1.txt": [chunk1, chunk2],
            "file2.txt": [chunk]
          }
        """
        # Prepare inputs.
        content = """<start:file1.txt>
File1 chunk1
<start:file2.txt>
File2 only chunk
<start:file1.txt>
File1 chunk2
"""
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        self.assertEqual(len(sections), 2)
        self.assertEqual(len(sections["file1.txt"]), 2)
        self.assertEqual(len(sections["file2.txt"]), 1)
        self.assert_equal(sections["file1.txt"][0], "\nFile1 chunk1\n")
        self.assert_equal(sections["file1.txt"][1], "\nFile1 chunk2\n")
        self.assert_equal(sections["file2.txt"][0], "\nFile2 only chunk\n")


# #############################################################################
# Test_verify_all_content_saved
# #############################################################################

# NOTE: The _verify_all_content_saved() function does not exist in the
# implementation, so these tests are not implemented. The function may have
# been planned but was not implemented in the current version of the code.



# #############################################################################
# Test_split_file
# #############################################################################

class Test_split_file(hunitest.TestCase):
    """
    Test splitting input file into multiple output files.
    """

    def test_split_file_basic(self) -> None:
        """
        Test basic file splitting with two output files.

        Expected input file content:
        ```
        <start:output1.txt>
        Content for output1
        <start:output2.txt>
        Content for output2
        ```

        Expected output:
        - Two files created: output1.txt, output2.txt
        - output1.txt contains "Content for output1"
        - output2.txt contains "Content for output2"
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        content = """<start:output1.txt>
Content for output1
<start:output2.txt>
Content for output2
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        output1_file = os.path.join(scratch_dir, "output1.txt")
        output2_file = os.path.join(scratch_dir, "output2.txt")
        self.assertEqual(os.path.exists(output1_file), True)
        self.assertEqual(os.path.exists(output2_file), True)
        output1_content = hio.from_file(output1_file)
        output2_content = hio.from_file(output2_file)
        self.assert_equal(output1_content, "\nContent for output1\n")
        self.assert_equal(output2_content, "\nContent for output2\n")

    def test_split_file_with_common_section(self) -> None:
        """
        Test file splitting with common section prepended to all files.

        Expected input file content:
        ```
        <start_common>
        Common header
        <start:output1.txt>
        Content 1
        <start:output2.txt>
        Content 2
        ```

        Expected output:
        - Two files created with common header prepended
        - output1.txt contains "Common header\\nContent 1"
        - output2.txt contains "Common header\\nContent 2"
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        content = """<start_common>
Common header
<start:output1.txt>
Content 1
<start:output2.txt>
Content 2
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        output1_file = os.path.join(scratch_dir, "output1.txt")
        output2_file = os.path.join(scratch_dir, "output2.txt")
        output1_content = hio.from_file(output1_file)
        output2_content = hio.from_file(output2_file)
        expected1 = "\nCommon header\n\nContent 1\n"
        expected2 = "\nCommon header\n\nContent 2\n"
        self.assert_equal(output1_content, expected1)
        self.assert_equal(output2_content, expected2)

    def test_split_file_creates_output_directory(self) -> None:
        """
        Test that output directory is created if it doesn't exist.

        Expected input:
        - Input file with tags
        - output_dir that doesn't exist yet

        Expected output:
        - Output directory is created
        - Files are written to the new directory
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        output_dir = os.path.join(scratch_dir, "new_output_dir")
        content = """<start:test.txt>
Test content
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=output_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        self.assertEqual(os.path.exists(output_dir), True)
        output_file = os.path.join(output_dir, "test.txt")
        self.assertEqual(os.path.exists(output_file), True)

    def test_split_file_nonexistent_input_raises_error(self) -> None:
        """
        Test that nonexistent input file raises assertion error.

        Expected input:
        - Path to file that doesn't exist

        Expected: AssertionError
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        nonexistent_file = os.path.join(scratch_dir, "nonexistent.txt")
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshctsifi._split_file(
                nonexistent_file,
                output_dir=scratch_dir,
                dry_run=False,
                skip_verify=False,
                preserve_input=True,
                append=False,
            )

    def test_split_file_preserves_content_exactly(self) -> None:
        """
        Test that content is preserved exactly including whitespace.

        Expected input file content:
        ```
        <start:test.txt>
            Indented content
        Content with    spaces
        ```

        Expected output:
        - test.txt contains exact whitespace including indentation
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        content = """<start:test.txt>
    Indented content
Content with    spaces
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        output_file = os.path.join(scratch_dir, "test.txt")
        output_content = hio.from_file(output_file)
        expected = "\n    Indented content\nContent with    spaces\n"
        self.assert_equal(output_content, expected)

    def test_split_file_multiple_chunks_same_file(self) -> None:
        """
        Test splitting with multiple chunks for the same filename.

        Expected input file content:
        ```
        <start:output.txt>
        First chunk
        <start:output.txt>
        Second chunk
        ```

        Expected output:
        - Single output.txt file containing both chunks concatenated
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        content = """<start:output.txt>
First chunk
<start:output.txt>
Second chunk
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        output_file = os.path.join(scratch_dir, "output.txt")
        output_content = hio.from_file(output_file)
        expected = "\nFirst chunk\n\nSecond chunk\n"
        self.assert_equal(output_content, expected)

    def test_split_file_append_to_existing_file(self) -> None:
        """
        Test append mode with existing file.

        Expected workflow:
        1. Create existing output file with content
        2. Run split with append=True
        3. New content is appended to existing file
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        output_file = os.path.join(scratch_dir, "output.txt")
        # Create existing file.
        hio.to_file(output_file, "Existing content\n")
        content = """<start:output.txt>
New content
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=True,
        )
        # Check outputs.
        output_content = hio.from_file(output_file)
        expected = "Existing content\n\nNew content\n"
        self.assert_equal(output_content, expected)

    def test_split_file_append_to_nonexisting_file(self) -> None:
        """
        Test append mode when file doesn't exist creates new file.

        Expected workflow:
        1. No existing output file
        2. Run split with append=True
        3. New file is created with common section and content
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        content = """<start_common>
Common header
<start:output.txt>
New content
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=True,
        )
        # Check outputs.
        output_file = os.path.join(scratch_dir, "output.txt")
        output_content = hio.from_file(output_file)
        expected = "\nCommon header\n\nNew content\n"
        self.assert_equal(output_content, expected)

    def test_split_file_multiple_chunks_with_append(self) -> None:
        """
        Test multiple chunks with append mode.

        Expected workflow:
        1. Create existing file
        2. Run split with multiple chunks for same file and append=True
        3. All chunks are appended to existing file
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        output_file = os.path.join(scratch_dir, "output.txt")
        # Create existing file.
        hio.to_file(output_file, "Existing\n")
        content = """<start:output.txt>
Chunk 1
<start:output.txt>
Chunk 2
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=True,
        )
        # Check outputs.
        output_content = hio.from_file(output_file)
        expected = "Existing\n\nChunk 1\n\nChunk 2\n"
        self.assert_equal(output_content, expected)

    def test_split_file_append_with_common_section(self) -> None:
        """
        Test that common section is not appended when file exists.

        Expected workflow:
        1. Create existing file
        2. Run split with common section and append=True
        3. Common section is NOT added to existing file
        4. Only new content is appended
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        output_file = os.path.join(scratch_dir, "output.txt")
        # Create existing file.
        hio.to_file(output_file, "Existing\n")
        content = """<start_common>
Common header
<start:output.txt>
New content
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=True,
        )
        # Check outputs.
        output_content = hio.from_file(output_file)
        # Common section should NOT be in the output since file existed.
        expected = "Existing\n\nNew content\n"
        self.assert_equal(output_content, expected)



# #############################################################################
# TestSplitFileIntegration
# #############################################################################

class TestSplitFileIntegration(hunitest.TestCase):
    """
    Integration tests for the complete split_in_files workflow.
    """

    def test_end_to_end_basic_split(self) -> None:
        """
        Test complete workflow from input file to multiple output files.

        Expected workflow:
        1. Create input file with tags
        2. Run split operation
        3. Verify all output files created correctly
        4. Verify content integrity
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        content = """<start:module1.py>
def function1():
    return "Hello"
<start:module2.py>
def function2():
    return "World"
<start:readme.txt>
This is a readme file.
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        module1_file = os.path.join(scratch_dir, "module1.py")
        module2_file = os.path.join(scratch_dir, "module2.py")
        readme_file = os.path.join(scratch_dir, "readme.txt")
        self.assertEqual(os.path.exists(module1_file), True)
        self.assertEqual(os.path.exists(module2_file), True)
        self.assertEqual(os.path.exists(readme_file), True)
        module1_content = hio.from_file(module1_file)
        module2_content = hio.from_file(module2_file)
        readme_content = hio.from_file(readme_file)
        self.assert_equal(
            module1_content, '\ndef function1():\n    return "Hello"\n'
        )
        self.assert_equal(
            module2_content, '\ndef function2():\n    return "World"\n'
        )
        self.assert_equal(readme_content, "\nThis is a readme file.\n")

    def test_end_to_end_with_common_and_multiple_files(self) -> None:
        """
        Test workflow with common section and multiple output files.

        Expected workflow:
        1. Create input with <start_common> and 3+ file sections
        2. Run split operation
        3. Verify common section in all output files
        4. Verify unique content in each file
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        content = """<start_common>
# Common header
import logging
<start:file1.py>
def func1():
    pass
<start:file2.py>
def func2():
    pass
<start:file3.py>
def func3():
    pass
"""
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        file1 = os.path.join(scratch_dir, "file1.py")
        file2 = os.path.join(scratch_dir, "file2.py")
        file3 = os.path.join(scratch_dir, "file3.py")
        content1 = hio.from_file(file1)
        content2 = hio.from_file(file2)
        content3 = hio.from_file(file3)
        # Verify common section is in all files.
        common_part = "# Common header\nimport logging"
        self.assertIn(common_part, content1)
        self.assertIn(common_part, content2)
        self.assertIn(common_part, content3)
        # Verify unique content in each file.
        self.assertIn("def func1():", content1)
        self.assertIn("def func2():", content2)
        self.assertIn("def func3():", content3)

    def test_end_to_end_large_file(self) -> None:
        """
        Test handling of large file with many sections.

        Expected input:
        - File with 10+ sections
        - Each section with significant content

        Expected output:
        - All 10+ files created successfully
        - No data loss or corruption
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        # Generate content with 10 sections.
        sections = []
        for i in range(10):
            sections.append(f"<start:file{i}.txt>\n")
            sections.append(f"Content for file {i}\n")
            sections.append(f"Line 2 of file {i}\n")
            sections.append(f"Line 3 of file {i}\n")
        content = "".join(sections)
        hio.to_file(input_file, content)
        # Run test.
        dshctsifi._split_file(
            input_file,
            output_dir=scratch_dir,
            dry_run=False,
            skip_verify=False,
            preserve_input=True,
            append=False,
        )
        # Check outputs.
        for i in range(10):
            output_file = os.path.join(scratch_dir, f"file{i}.txt")
            self.assertEqual(os.path.exists(output_file), True)
            file_content = hio.from_file(output_file)
            expected_lines = [
                f"\nContent for file {i}\n",
                f"Line 2 of file {i}\n",
                f"Line 3 of file {i}\n",
            ]
            expected = "".join(expected_lines)
            self.assert_equal(file_content, expected)
