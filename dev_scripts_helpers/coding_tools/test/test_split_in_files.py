import logging
import os

import dev_scripts_helpers.coding_tools.split_in_files as dshctsifi
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# #############################################################################
# Test_parse_file_content
# #############################################################################


class Test_parse_file_content(hunitest.TestCase):
    """
    Test parsing file content and extracting sections based on tags.
    """

    def test1(self) -> None:
        """
        Test parsing file with <start_common> and multiple file sections.
        """
        # Prepare inputs.
        content = """
        <start_common>
        Common header
        <start:file1.txt>
        Content for file1
        <start:file2.txt>
        Content for file2
        """
        content = hprint.dedent(content)
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        expected_common = "\nCommon header\n"
        self.assert_equal(common_section, expected_common)
        expected_sections = {
            "file1.txt": "\nContent for file1\n",
            "file2.txt": "\nContent for file2\n",
        }
        self.assert_equal(str(sections), str(expected_sections))
        self.assertEqual(len(line_ranges), 2)
        self.assertEqual(common_line_range, (1, 3))

    def test2(self) -> None:
        """
        Test parsing file without <start_common> section.
        """
        # Prepare inputs.
        content = """
        <start:file1.txt>
        Content for file1
        <start:file2.txt>
        Content for file2
        """
        content = hprint.dedent(content)
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        self.assert_equal(common_section, "")
        expected_sections = {
            "file1.txt": "\nContent for file1\n",
            "file2.txt": "\nContent for file2\n",
        }
        self.assert_equal(str(sections), str(expected_sections))
        self.assertEqual(len(line_ranges), 2)
        self.assertEqual(common_line_range, None)

    def test3(self) -> None:
        """
        Test parsing file with single file section.
        """
        # Prepare inputs.
        content = """
        <start:output.txt>
        Single file content
        """
        content = hprint.dedent(content)
        # Run test.
        common_section, sections, line_ranges, common_line_range = (
            dshctsifi._parse_file_content(content)
        )
        # Check outputs.
        self.assert_equal(common_section, "")
        expected_sections = {"output.txt": "\nSingle file content\n"}
        self.assert_equal(str(sections), str(expected_sections))
        self.assertEqual(len(line_ranges), 1)
        self.assertEqual(common_line_range, None)


# #############################################################################
# Test_split_file
# #############################################################################


class Test_split_file(hunitest.TestCase):
    """
    Test splitting input file into multiple output files.
    """

    def _create_input_file_for_split(
        self,
        content: str,
        filename: str = "input.txt",
        output_dir: str = None,
    ) -> tuple:
        """
        Create an input file with dedented content in scratch space.

        :param content: Raw content string (will be dedented)
        :param filename: Name of input file
        :param output_dir: Optional custom output directory path
        :return: Tuple of (input_file_path, output_directory_path)
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        if output_dir is None:
            output_dir = scratch_dir
        input_file = os.path.join(scratch_dir, filename)
        content = hprint.dedent(content)
        # Run.
        hio.to_file(input_file, content)
        # Check outputs.
        return input_file, output_dir

    def _run_split_file(
        self,
        input_file: str,
        output_dir: str,
        dry_run: bool = False,
        skip_verify: bool = False,
        preserve_input: bool = True,
    ) -> None:
        """
        Run _split_file with standard test parameters.

        :param input_file: Path to input file
        :param output_dir: Output directory path
        :param dry_run: Whether to do dry run
        :param skip_verify: Whether to skip verification
        :param preserve_input: Whether to preserve input file
        """
        # Run.
        dshctsifi._split_file(
            input_file,
            output_dir=output_dir,
            dry_run=dry_run,
            skip_verify=skip_verify,
            preserve_input=preserve_input,
        )

    def test1(self) -> None:
        """
        Test basic file splitting with two output files.
        """
        # Prepare inputs.
        content = """
        <start:output1.txt>
        Content for output1
        <start:output2.txt>
        Content for output2
        """
        input_file, output_dir = self._create_input_file_for_split(content)
        # Run test.
        self._run_split_file(input_file, output_dir)
        # Check outputs.
        output1_file = os.path.join(output_dir, "output1.txt")
        output2_file = os.path.join(output_dir, "output2.txt")
        self.assertEqual(os.path.exists(output1_file), True)
        self.assertEqual(os.path.exists(output2_file), True)
        output1_content = hio.from_file(output1_file)
        output2_content = hio.from_file(output2_file)
        self.assert_equal(output1_content, "\nContent for output1\n")
        self.assert_equal(output2_content, "\nContent for output2\n")

    def test2(self) -> None:
        """
        Test file splitting with common section prepended to all files.
        """
        # Prepare inputs.
        content = """
        <start_common>
        Common header
        <start:output1.txt>
        Content 1
        <start:output2.txt>
        Content 2
        """
        input_file, output_dir = self._create_input_file_for_split(content)
        # Run test.
        self._run_split_file(input_file, output_dir)
        # Check outputs.
        output1_file = os.path.join(output_dir, "output1.txt")
        output2_file = os.path.join(output_dir, "output2.txt")
        output1_content = hio.from_file(output1_file)
        output2_content = hio.from_file(output2_file)
        expected1 = "\nCommon header\n\nContent 1\n"
        expected2 = "\nCommon header\n\nContent 2\n"
        self.assert_equal(output1_content, expected1)
        self.assert_equal(output2_content, expected2)

    def test3(self) -> None:
        """
        Test that output directory is created if it doesn't exist.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        custom_output_dir = os.path.join(scratch_dir, "new_output_dir")
        content = """
        <start:test.txt>
        Test content
        """
        input_file, _ = self._create_input_file_for_split(
            content, output_dir=custom_output_dir
        )
        # Run test.
        self._run_split_file(input_file, custom_output_dir)
        # Check outputs.
        self.assertEqual(os.path.exists(custom_output_dir), True)
        output_file = os.path.join(custom_output_dir, "test.txt")
        self.assertEqual(os.path.exists(output_file), True)

    def test4(self) -> None:
        """
        Test that content is preserved exactly including whitespace.
        """
        # Prepare inputs.
        content = """
        <start:test.txt>
            Indented content
        Content with    spaces
        """
        input_file, output_dir = self._create_input_file_for_split(content)
        # Run test.
        self._run_split_file(input_file, output_dir)
        # Check outputs.
        output_file = os.path.join(output_dir, "test.txt")
        output_content = hio.from_file(output_file)
        expected = "\n    Indented content\nContent with    spaces\n"
        self.assert_equal(output_content, expected)


# #############################################################################
# TestSplitFileIntegration
# #############################################################################


class TestSplitFileIntegration(hunitest.TestCase):
    """
    Integration tests for the complete split_in_files workflow.
    """

    def _create_input_file_for_split(
        self,
        content: str,
        filename: str = "input.txt",
        output_dir: str = None,
    ) -> tuple:
        """
        Create an input file with dedented content in scratch space.

        :param content: Raw content string (will be dedented)
        :param filename: Name of input file
        :param output_dir: Optional custom output directory path
        :return: Tuple of (input_file_path, output_directory_path)
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        if output_dir is None:
            output_dir = scratch_dir
        input_file = os.path.join(scratch_dir, filename)
        content = hprint.dedent(content)
        # Run.
        hio.to_file(input_file, content)
        # Check outputs.
        return input_file, output_dir

    def _run_split_file(
        self,
        input_file: str,
        output_dir: str,
        dry_run: bool = False,
        skip_verify: bool = False,
        preserve_input: bool = True,
    ) -> None:
        """
        Run _split_file with standard test parameters.

        :param input_file: Path to input file
        :param output_dir: Output directory path
        :param dry_run: Whether to do dry run
        :param skip_verify: Whether to skip verification
        :param preserve_input: Whether to preserve input file
        """
        # Run.
        dshctsifi._split_file(
            input_file,
            output_dir=output_dir,
            dry_run=dry_run,
            skip_verify=skip_verify,
            preserve_input=preserve_input,
        )

    def test1(self) -> None:
        """
        Test complete workflow from input file to multiple output files.

        Expected workflow:
        1. Create input file with tags
        2. Run split operation
        3. Verify all output files created correctly
        4. Verify content integrity
        """
        # Prepare inputs.
        content = """
        <start:module1.py>
        def function1():
            return "Hello"
        <start:module2.py>
        def function2():
            return "World"
        <start:readme.txt>
        This is a readme file.
        """
        input_file, output_dir = self._create_input_file_for_split(content)
        # Run test.
        self._run_split_file(input_file, output_dir)
        # Check outputs.
        module1_file = os.path.join(output_dir, "module1.py")
        module2_file = os.path.join(output_dir, "module2.py")
        readme_file = os.path.join(output_dir, "readme.txt")
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

    def test2(self) -> None:
        """
        Test workflow with common section and multiple output files.

        Expected workflow:
        1. Create input with <start_common> and 3+ file sections
        2. Run split operation
        3. Verify common section in all output files
        4. Verify unique content in each file
        """
        # Prepare inputs.
        content = """
        <start_common>
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
        input_file, output_dir = self._create_input_file_for_split(content)
        # Run test.
        self._run_split_file(input_file, output_dir)
        # Check outputs.
        file1 = os.path.join(output_dir, "file1.py")
        file2 = os.path.join(output_dir, "file2.py")
        file3 = os.path.join(output_dir, "file3.py")
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

    def test3(self) -> None:
        """
        Test handling of large file with many sections.
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
        output_dir = scratch_dir
        # Run test.
        self._run_split_file(input_file, output_dir)
        # Check outputs.
        for i in range(10):
            output_file = os.path.join(output_dir, f"file{i}.txt")
            self.assertEqual(os.path.exists(output_file), True)
            file_content = hio.from_file(output_file)
            expected_lines = [
                f"\nContent for file {i}\n",
                f"Line 2 of file {i}\n",
                f"Line 3 of file {i}\n",
            ]
            expected = "".join(expected_lines)
            self.assert_equal(file_content, expected)
