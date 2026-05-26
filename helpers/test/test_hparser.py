import argparse
import os

import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hunit_test as hunitest


# #############################################################################
# Test_parse_limit_range
# #############################################################################


class Test_parse_limit_range(hunitest.TestCase):
    """
    Test parsing limit range strings.
    """

    def helper(self, limit_str: str, expected: tuple) -> None:
        """
        Test helper for `parse_limit_range()`.

        :param limit_str: Input range string
        :param expected: Expected output tuple
        """
        actual = hparser.parse_limit_range(limit_str)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test parsing valid range format.
        """
        limit_str = "1:5"
        expected = (1, 5)
        self.helper(limit_str, expected)

    def test2(self) -> None:
        """
        Test parsing range with same start and end.
        """
        limit_str = "3:3"
        expected = (3, 3)
        self.helper(limit_str, expected)

    def test3(self) -> None:
        """
        Test parsing range with larger numbers.
        """
        limit_str = "10:100"
        expected = (10, 100)
        self.helper(limit_str, expected)

    def test4(self) -> None:
        """
        Test that missing colon raises assertion error.
        """
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range("15")

    def test5(self) -> None:
        """
        Test that multiple colons raise assertion error.
        """
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range("1:2:3")

    def test6(self) -> None:
        """
        Test that non-integer start raises assertion error.
        """
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range("abc:5")

    def test7(self) -> None:
        """
        Test that non-integer end raises assertion error.
        """
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range("1:xyz")

    def test8(self) -> None:
        """
        Test that start index of 0 raises assertion error.
        """
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range("0:5")

    def test9(self) -> None:
        """
        Test that end index of 0 raises assertion error.
        """
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range("1:0")

    def test10(self) -> None:
        """
        Test that start greater than end raises assertion error.
        """
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range("5:3")


# #############################################################################
# Test_apply_limit_range
# #############################################################################


class Test_apply_limit_range(hunitest.TestCase):
    """
    Test applying limit ranges to items.
    """

    def helper(self, items, limit_range, expected, **kwargs) -> None:
        """
        Test helper for `apply_limit_range()`.

        :param items: Input items list
        :param limit_range: Range tuple to apply
        :param expected: Expected output
        :param kwargs: Additional keyword arguments
        """
        actual = hparser.apply_limit_range(items, limit_range, **kwargs)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that None limit range returns original items.
        """
        items = ["a", "b", "c", "d", "e"]
        expected = items
        self.helper(items, None, expected)

    def test2(self) -> None:
        """
        Test applying valid range to items.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (1, 3)
        expected = ["b", "c", "d"]
        self.helper(items, limit_range, expected)

    def test3(self) -> None:
        """
        Test applying range that selects single item.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (2, 2)
        expected = ["c"]
        self.helper(items, limit_range, expected)

    def test4(self) -> None:
        """
        Test applying range starting from first item.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (0, 1)
        expected = ["a", "b"]
        self.helper(items, limit_range, expected)

    def test5(self) -> None:
        """
        Test applying range ending at last item.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (3, 4)
        expected = ["d", "e"]
        self.helper(items, limit_range, expected)

    def test6(self) -> None:
        """
        Test that start index exceeding items length raises assertion error.
        """
        items = ["a", "b", "c"]
        limit_range = (5, 6)
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test7(self) -> None:
        """
        Test that end index exceeding items length raises assertion error.
        """
        items = ["a", "b", "c"]
        limit_range = (1, 5)
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test8(self) -> None:
        """
        Test that custom item name doesn't affect functionality.
        """
        items = [1, 2, 3, 4, 5]
        limit_range = (0, 2)
        expected = [1, 2, 3]
        self.helper(items, limit_range, expected, item_name="numbers")

    def test9(self) -> None:
        """
        Test applying limit range to empty list.
        """
        items = []
        limit_range = (0, 1)
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test10(self) -> None:
        """
        Test applying limit range to complex objects.
        """
        items = [{"id": i, "value": f"item{i}"} for i in range(10)]
        limit_range = (2, 4)
        expected = [
            {"id": 2, "value": "item2"},
            {"id": 3, "value": "item3"},
            {"id": 4, "value": "item4"},
        ]
        self.helper(items, limit_range, expected)


# #############################################################################
# Test_add_multi_file_args
# #############################################################################


class Test_add_multi_file_args(hunitest.TestCase):
    """
    Test adding multi-file arguments to parser.
    """

    def test1(self) -> None:
        """
        Test that correct arguments are added to parser.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        # Run test.
        hparser.add_multi_file_args(parser)
        namespace = parser.parse_args([])
        # Check outputs.
        self.assertTrue(hasattr(namespace, "files"))
        self.assertTrue(hasattr(namespace, "from_files"))
        self.assertTrue(hasattr(namespace, "input"))


# #############################################################################
# Test_parse_multi_file_args
# #############################################################################


class Test_parse_multi_file_args(hunitest.TestCase):
    """
    Test parsing multi-file arguments.
    """

    def _create_test_file(self, file_path: str, content: str = "test") -> None:
        """
        Create a test file with given content.
        """
        hio.create_dir(os.path.dirname(file_path), incremental=True)
        hio.to_file(file_path, content)

    def test1(self) -> None:
        """
        Test parsing comma-separated file list.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test files.
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        file3 = f"{scratch_dir}/file3.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        self._create_test_file(file3)
        # Create namespace with files argument.
        args = argparse.Namespace()
        args.files = f"{file1},{file2},{file3}"
        args.from_files = None
        args.input = None
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2, file3]
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test parsing file containing list of files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test files.
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        file3 = f"{scratch_dir}/file3.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        self._create_test_file(file3)
        # Create file list.
        list_file = f"{scratch_dir}/list.txt"
        content = f"{file1}\n{file2}\n{file3}\n"
        self._create_test_file(list_file, content)
        # Create namespace with from_files argument.
        args = argparse.Namespace()
        args.files = None
        args.from_files = list_file
        args.input = None
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2, file3]
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test parsing file with empty lines and comments.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test files.
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        # Create file list with empty lines and comments.
        list_file = f"{scratch_dir}/list.txt"
        content = f"""
        # This is a comment
        {file1}

        # Another comment
        {file2}

        """
        self._create_test_file(list_file, content)
        # Create namespace with from_files argument.
        args = argparse.Namespace()
        args.files = None
        args.from_files = list_file
        args.input = None
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2]
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test parsing repeated --input arguments.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test files.
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        # Create namespace with input argument.
        args = argparse.Namespace()
        args.files = None
        args.from_files = None
        args.input = [file1, file2]
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2]
        self.assert_equal(str(actual), str(expected))

    def test5(self) -> None:
        """
        Test that single -i/--input still works.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test file.
        file1 = f"{scratch_dir}/file1.txt"
        self._create_test_file(file1)
        # Create namespace with input argument (single file, not list).
        args = argparse.Namespace()
        args.files = None
        args.from_files = None
        args.input = file1
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1]
        self.assert_equal(str(actual), str(expected))

    def test6(self) -> None:
        """
        Test that non-existent files raise error.
        """
        # Prepare inputs.
        args = argparse.Namespace()
        args.files = "/nonexistent/file1.txt,/nonexistent/file2.txt"
        args.from_files = None
        args.input = None
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hparser.parse_multi_file_args(args)

    def test7(self) -> None:
        """
        Test empty file list handling.
        """
        # Prepare inputs.
        args = argparse.Namespace()
        args.files = None
        args.from_files = None
        args.input = None
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hparser.parse_multi_file_args(args)
        act = str(cm.exception)
        self.assertIn("No input files specified", act)


# #############################################################################
# Test_add_input_output_args
# #############################################################################


class Test_add_input_output_args(hunitest.TestCase):
    """
    Test the `add_input_output_args()` function.
    """

    def test1(self) -> None:
        """
        Test adding input/output arguments with defaults.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        # Run test.
        hparser.add_input_output_args(parser)
        args = parser.parse_args(["-i", "input.txt"])
        # Check outputs.
        self.assertEqual(args.input, "input.txt")
        self.assertIsNone(args.output)
        self.assertIsNone(args.input_files)
        self.assertIsNone(args.from_file)

    def test2(self) -> None:
        """
        Test parsing both input and output arguments.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        # Run test.
        args = parser.parse_args(["-i", "input.txt", "-o", "output.txt"])
        # Check outputs.
        self.assertEqual(args.input, "input.txt")
        self.assertEqual(args.output, "output.txt")

    def test3(self) -> None:
        """
        Test parsing --input_files argument.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        # Run test.
        args = parser.parse_args(["--input_files", "file1.txt,file2.txt"])
        # Check outputs. With nargs='+', input_files is now a list.
        self.assertEqual(args.input_files, ["file1.txt,file2.txt"])

    def test4(self) -> None:
        """
        Test parsing --from_file argument.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        # Run test.
        args = parser.parse_args(["--from_file", "files.txt"])
        # Check outputs.
        self.assertEqual(args.from_file, "files.txt")


# #############################################################################
# Test_parse_input_output_files
# #############################################################################


class Test_parse_input_output_files(hunitest.TestCase):
    """
    Test the `parse_input_output_files()` function.
    """

    def test1(self) -> None:
        """
        Test that None is returned when neither option is provided.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(["-i", "input.txt"])
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertIsNone(result)

    def test2(self) -> None:
        """
        Test parsing comma-separated file list.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(
            ["--input_files", "file1.txt,file2.txt,file3.txt"]
        )
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertEqual(result, expected)

    def test3(self) -> None:
        """
        Test parsing space-separated file list.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(
            ["--input_files", "file1.txt file2.txt file3.txt"]
        )
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertEqual(result, expected)

    def test4(self) -> None:
        """
        Test parsing mixed comma and space separators.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(
            ["--input_files", "file1.txt,file2.txt file3.txt"]
        )
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertEqual(result, expected)

    def test5(self) -> None:
        """
        Test parsing single file from --input_files.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(["--input_files", "single.txt"])
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertEqual(result, ["single.txt"])

    def test6(self) -> None:
        """
        Test parsing files from --from_file.
        """
        # Prepare inputs.
        out_dir = self.get_scratch_space()
        file_list_path = os.path.join(out_dir, "files.txt")
        with open(file_list_path, "w") as f:
            f.write("file1.txt\n")
            f.write("file2.txt\n")
            f.write("file3.txt\n")
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(["--from_file", file_list_path])
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertEqual(result, expected)

    def test7(self) -> None:
        """
        Test parsing files from --from_file with empty lines.
        """
        # Prepare inputs.
        out_dir = self.get_scratch_space()
        file_list_path = os.path.join(out_dir, "files.txt")
        with open(file_list_path, "w") as f:
            f.write("file1.txt\n")
            f.write("\n")
            f.write("file2.txt\n")
            f.write("  \n")
            f.write("file3.txt\n")
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(["--from_file", file_list_path])
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertEqual(result, expected)

    def test8(self) -> None:
        """
        Test that FileNotFoundError is raised for non-existent file.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(["--from_file", "/nonexistent/path/files.txt"])
        # Run test and check outputs.
        with self.assertRaises(FileNotFoundError):
            hparser.parse_input_output_files(args)

    def test9(self) -> None:
        """
        Test parsing multiple files passed as separate arguments (shell glob expansion).
        """
        # Prepare inputs. This simulates shell expansion: `--input_files *.md`
        # becomes multiple arguments: `--input_files file1.md file2.md file3.md`
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(
            ["--input_files", "file1.md", "file2.md", "file3.md"]
        )
        # Prepare outputs.
        expected = ["file1.md", "file2.md", "file3.md"]
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertEqual(result, expected)


# #############################################################################
# Test_parse_input_output_args
# #############################################################################


class Test_parse_input_output_args(hunitest.TestCase):
    """
    Test the `parse_input_output_args()` function.
    """

    def helper(self, args_list, expected_in, expected_out) -> None:
        """
        Test helper for `parse_input_output_args()`.

        :param args_list: Command-line arguments
        :param expected_in: Expected input file
        :param expected_out: Expected output file
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(
            parser, in_required=False, out_required=False
        )
        args = parser.parse_args(args_list)
        in_file, out_file = hparser.parse_input_output_args(args)
        self.assertEqual(in_file, expected_in)
        self.assertEqual(out_file, expected_out)

    def test1(self) -> None:
        """
        Test parsing with only input specified (output defaults to input).
        """
        args_list = ["-i", "input.txt"]
        expected_in = "input.txt"
        expected_out = "input.txt"
        self.helper(args_list, expected_in, expected_out)

    def test2(self) -> None:
        """
        Test parsing with both input and output specified.
        """
        args_list = ["-i", "input.txt", "-o", "output.txt"]
        expected_in = "input.txt"
        expected_out = "output.txt"
        self.helper(args_list, expected_in, expected_out)

    def test3(self) -> None:
        """
        Test parsing with stdin as input.
        """
        args_list = ["-i", "-", "-o", "output.txt"]
        expected_in = "-"
        expected_out = "output.txt"
        self.helper(args_list, expected_in, expected_out)

    def test4(self) -> None:
        """
        Test parsing with stdout as output.
        """
        args_list = ["-i", "input.txt", "-o", "-"]
        expected_in = "input.txt"
        expected_out = "-"
        self.helper(args_list, expected_in, expected_out)


# #############################################################################
# Test_from_file
# #############################################################################


class Test_from_file(hunitest.TestCase):
    """
    Test the `from_file()` function.
    """

    def helper(self, content: str, expected: list) -> None:
        """
        Test helper for `from_file()`.

        :param content: File content to write
        :param expected: Expected lines returned
        """
        out_dir = self.get_scratch_space()
        file_path = os.path.join(out_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write(content)
        lines = hparser.from_file(file_path)
        self.assertEqual(lines, expected)

    def test1(self) -> None:
        """
        Test reading content from a file.
        """
        content = "line1\nline2\nline3"
        expected = ["line1", "line2", "line3"]
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test reading an empty file.
        """
        content = ""
        expected = [""]
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test reading file with trailing newline.
        """
        content = "line1\nline2\n"
        expected = ["line1", "line2", ""]
        self.helper(content, expected)


# #############################################################################
# Test_to_file
# #############################################################################


class Test_to_file(hunitest.TestCase):
    """
    Test the `to_file()` function.
    """

    def helper(self, input_data, expected_content: str) -> None:
        """
        Test helper for `to_file()`.

        :param input_data: Data to write to file
        :param expected_content: Expected file content
        """
        out_dir = self.get_scratch_space()
        file_path = os.path.join(out_dir, "output.txt")
        hparser.to_file(input_data, file_path)
        with open(file_path, "r") as f:
            written = f.read()
        self.assertEqual(written, expected_content)

    def test1(self) -> None:
        """
        Test writing a string to a file.
        """
        input_data = "line1\nline2\nline3"
        expected_content = "line1\nline2\nline3"
        self.helper(input_data, expected_content)

    def test2(self) -> None:
        """
        Test writing a list of strings to a file.
        """
        input_data = ["line1", "line2", "line3"]
        expected_content = "line1\nline2\nline3"
        self.helper(input_data, expected_content)

    def test3(self) -> None:
        """
        Test writing an empty list to a file.
        """
        input_data: list = []
        expected_content = ""
        self.helper(input_data, expected_content)

    def test4(self) -> None:
        """
        Test that writing to file overwrites existing content.
        """
        out_dir = self.get_scratch_space()
        file_path = os.path.join(out_dir, "output.txt")
        hparser.to_file("old content", file_path)
        hparser.to_file("new content", file_path)
        with open(file_path, "r") as f:
            written = f.read()
        self.assertEqual(written, "new content")


# #############################################################################
# Test_extract_rule_from_file
# #############################################################################


class Test_extract_rule_from_file(hunitest.TestCase):
    """
    Test extracting rules from markdown rule files.
    """

    def helper_create_rule_file(self) -> str:
        """
        Create a test rule file with multiple sections at different levels.

        :return: path to the created rule file
        """
        out_dir = self.get_scratch_space()
        file_path = os.path.join(out_dir, "rules.md")
        content = """- Document intro

# Level 1 Section

- Level 1 content line 1
- Level 1 content line 2

## Level 1.1 Subsection

- Level 1.1 content line 1
- Level 1.1 content line 2

## Level 1.2 Subsection

- Level 1.2 content

# Another Level 1 Section

- Another level 1 content
"""
        hparser.to_file(content, file_path)
        return file_path

    def test1(self) -> None:
        """
        Test extracting entire file when no line number is provided.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = file_path
        actual = hparser.extract_rule_from_file(rule_spec)
        # The content should be the full file.
        expected = hio.from_file(file_path)
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test extracting level-1 header section (line 3).
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3"
        actual = hparser.extract_rule_from_file(rule_spec)
        # Should extract from line 3 until the next level-1 header (line 13).
        expected = """# Level 1 Section

- Level 1 content line 1
- Level 1 content line 2

## Level 1.1 Subsection

- Level 1.1 content line 1
- Level 1.1 content line 2

## Level 1.2 Subsection

- Level 1.2 content"""
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test extracting level-2 header section stops at next level-2 or level-1.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:8"
        actual = hparser.extract_rule_from_file(rule_spec)
        # Should extract from line 8 (level-2 header) to next level-2 header
        # (line 13).
        expected = """## Level 1.1 Subsection

- Level 1.1 content line 1
- Level 1.1 content line 2"""
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test extracting with section name validation (matching).
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3:# Level 1 Section"
        actual = hparser.extract_rule_from_file(rule_spec)
        # Same as test2 since the name matches.
        expected = """# Level 1 Section

- Level 1 content line 1
- Level 1 content line 2

## Level 1.1 Subsection

- Level 1.1 content line 1
- Level 1.1 content line 2

## Level 1.2 Subsection

- Level 1.2 content"""
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test that section name mismatch raises ValueError.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3:# Different Name"
        with self.assertRaises(ValueError):
            hparser.extract_rule_from_file(rule_spec)

    def test6(self) -> None:
        """
        Test that non-header line raises ValueError.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:4"  # This is "- Level 1 content line 1", not a header.
        with self.assertRaises(ValueError):
            hparser.extract_rule_from_file(rule_spec)

    def test7(self) -> None:
        """
        Test that invalid line number raises error.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:999"  # Out of range.
        with self.assertRaises(AssertionError):
            hparser.extract_rule_from_file(rule_spec)

    def test8(self) -> None:
        """
        Test that non-existent file raises error.
        """
        rule_spec = "/nonexistent/path/to/file.md"
        with self.assertRaises(AssertionError):
            hparser.extract_rule_from_file(rule_spec)


# #############################################################################
# Test_add_file_type_filter_args
# #############################################################################

# TODO(ai_gp): /factor_out


class Test_add_file_type_filter_args(hunitest.TestCase):
    """
    Test adding file type filter arguments to parser.
    """

    def test1(self) -> None:
        """
        Test that correct arguments are added to parser.
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args([])
        self.assertTrue(hasattr(args, "file_types"))
        self.assertTrue(hasattr(args, "skip_file_types"))
        self.assertEqual(args.file_types, "py,ipynb")
        self.assertEqual(args.skip_file_types, "")

    def test2(self) -> None:
        """
        Test custom default for file_types.
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser, file_types_default="py,md")
        args = parser.parse_args([])
        self.assertEqual(args.file_types, "py,md")


# #############################################################################
# Test_parse_file_type_filter_args
# #############################################################################


class Test_parse_file_type_filter_args(hunitest.TestCase):
    """
    Test parsing file type filter arguments.
    """

    def test1(self) -> None:
        """
        Test parsing default file types (py,ipynb).
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args([])
        actual = hparser.parse_file_type_filter_args(args)
        expected = ["py", "ipynb"]
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test parsing custom file types with --file_types.
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args(["--file_types", "py,md,txt"])
        actual = hparser.parse_file_type_filter_args(args)
        expected = ["py", "md", "txt"]
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test parsing with whitespace in comma-separated list.
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args(["--file_types", "py , ipynb , md"])
        actual = hparser.parse_file_type_filter_args(args)
        expected = ["py", "ipynb", "md"]
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test parsing with skip_file_types to exclude extensions.
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args(
            ["--file_types", "py,ipynb,md,txt", "--skip_file_types", "txt"]
        )
        actual = hparser.parse_file_type_filter_args(args)
        expected = ["py", "ipynb", "md"]
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test parsing with multiple skip_file_types.
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args(
            [
                "--file_types",
                "py,ipynb,md,txt",
                "--skip_file_types",
                "txt,md",
            ]
        )
        actual = hparser.parse_file_type_filter_args(args)
        expected = ["py", "ipynb"]
        self.assertEqual(actual, expected)

    def test6(self) -> None:
        """
        Test parsing with empty file_types (should result in empty list).
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args(["--file_types", ""])
        actual = hparser.parse_file_type_filter_args(args)
        expected: list = []
        self.assertEqual(actual, expected)

    def test7(self) -> None:
        """
        Test parsing with skip_file_types that skips all file types.
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser)
        args = parser.parse_args(
            ["--file_types", "py,ipynb", "--skip_file_types", "py,ipynb"]
        )
        actual = hparser.parse_file_type_filter_args(args)
        expected: list = []
        self.assertEqual(actual, expected)
