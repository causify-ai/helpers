import argparse
import os
from typing import Any, List, Optional, Tuple

import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hunit_test as hunitest


def _create_test_file(file_path: str, *, content: str = "test") -> None:
    """
    Create a test file with given content.
    """
    hio.create_dir(os.path.dirname(file_path), incremental=True)
    hio.to_file(file_path, content)


def _make_parser_with_input_output_args(
    in_required: bool, out_required: bool
) -> argparse.ArgumentParser:
    """
    Create an ArgumentParser with input/output arguments.
    """
    parser = argparse.ArgumentParser()
    hparser.add_input_output_args(
        parser, in_required=in_required, out_required=out_required
    )
    return parser


# #############################################################################
# Test_parse_limit_range
# #############################################################################


class Test_parse_limit_range(hunitest.TestCase):
    """
    Test parsing limit range strings.
    """

    def helper(self, limit_str: str, expected: Tuple) -> None:
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
        # Prepare inputs.
        limit_str = "1:5"
        # Prepare outputs.
        expected = (1, 5)
        # Run test.
        self.helper(limit_str, expected)

    def test2(self) -> None:
        """
        Test parsing range with same start and end.
        """
        # Prepare inputs.
        limit_str = "3:3"
        # Prepare outputs.
        expected = (3, 3)
        # Run test.
        self.helper(limit_str, expected)

    def test3(self) -> None:
        """
        Test parsing range with larger numbers.
        """
        # Prepare inputs.
        limit_str = "10:100"
        # Prepare outputs.
        expected = (10, 100)
        # Run test.
        self.helper(limit_str, expected)

    def test4(self) -> None:
        """
        Test that missing colon raises assertion error.
        """
        # Prepare inputs.
        limit_str = "15"
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test5(self) -> None:
        """
        Test that multiple colons raise assertion error.
        """
        # Prepare inputs.
        limit_str = "1:2:3"
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test6(self) -> None:
        """
        Test that non-integer start raises assertion error.
        """
        # Prepare inputs.
        limit_str = "abc:5"
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test7(self) -> None:
        """
        Test that non-integer end raises assertion error.
        """
        # Prepare inputs.
        limit_str = "1:xyz"
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test8(self) -> None:
        """
        Test that start index of 0 raises assertion error.
        """
        # Prepare inputs.
        limit_str = "0:5"
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test9(self) -> None:
        """
        Test that end index of 0 raises assertion error.
        """
        # Prepare inputs.
        limit_str = "1:0"
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test10(self) -> None:
        """
        Test that start greater than end raises assertion error.
        """
        # Prepare inputs.
        limit_str = "5:3"
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)


# #############################################################################
# Test_apply_limit_range
# #############################################################################


class Test_apply_limit_range(hunitest.TestCase):
    """
    Test applying limit ranges to items.
    """

    def helper(
        self,
        items: List,
        limit_range: Optional[Tuple[int, int]],
        expected: List,
        **kwargs,
    ) -> None:
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
        # Prepare inputs.
        items = ["a", "b", "c", "d", "e"]
        limit_range = None
        # Prepare outputs.
        expected = items
        # Run test.
        self.helper(items, limit_range, expected)

    def test2(self) -> None:
        """
        Test applying valid range to items.
        """
        # Prepare inputs.
        items = ["a", "b", "c", "d", "e"]
        limit_range = (1, 3)
        # Prepare outputs.
        expected = ["b", "c", "d"]
        # Run test.
        self.helper(items, limit_range, expected)

    def test3(self) -> None:
        """
        Test applying range that selects single item.
        """
        # Prepare inputs.
        items = ["a", "b", "c", "d", "e"]
        limit_range = (2, 2)
        # Prepare outputs.
        expected = ["c"]
        # Run test.
        self.helper(items, limit_range, expected)

    def test4(self) -> None:
        """
        Test applying range starting from first item.
        """
        # Prepare inputs.
        items = ["a", "b", "c", "d", "e"]
        limit_range = (0, 1)
        # Prepare outputs.
        expected = ["a", "b"]
        # Run test.
        self.helper(items, limit_range, expected)

    def test5(self) -> None:
        """
        Test applying range ending at last item.
        """
        # Prepare inputs.
        items = ["a", "b", "c", "d", "e"]
        limit_range = (3, 4)
        # Prepare outputs.
        expected = ["d", "e"]
        # Run test.
        self.helper(items, limit_range, expected)

    def test6(self) -> None:
        """
        Test that start index exceeding items length raises assertion error.
        """
        # Prepare inputs.
        items = ["a", "b", "c"]
        limit_range = (5, 6)
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test7(self) -> None:
        """
        Test that end index exceeding items length raises assertion error.
        """
        # Prepare inputs.
        items = ["a", "b", "c"]
        limit_range = (1, 5)
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test8(self) -> None:
        """
        Test that custom item name doesn't affect functionality.
        """
        # Prepare inputs.
        items = [1, 2, 3, 4, 5]
        limit_range = (0, 2)
        item_name = "numbers"
        # Prepare outputs.
        expected = [1, 2, 3]
        # Run test.
        self.helper(items, limit_range, expected, item_name=item_name)

    def test9(self) -> None:
        """
        Test applying limit range to empty list.
        """
        # Prepare inputs.
        items = []
        limit_range = (0, 1)
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test10(self) -> None:
        """
        Test applying limit range to complex objects.
        """
        # Prepare inputs.
        items = [{"id": i, "value": f"item{i}"} for i in range(10)]
        limit_range = (2, 4)
        # Prepare outputs.
        expected = [
            {"id": 2, "value": "item2"},
            {"id": 3, "value": "item3"},
            {"id": 4, "value": "item4"},
        ]
        # Run test.
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
        args_list = []
        namespace = parser.parse_args(args_list)
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

    def _make_namespace_args(
        self,
        *,
        files: Optional[str] = None,
        from_files: Optional[str] = None,
        input_: Optional[Any] = None,
    ) -> "argparse.Namespace":
        """
        Build an `argparse.Namespace` with the three fields used by `parse_multi_file_args()`.
        """
        args = argparse.Namespace()
        args.files = files
        args.from_files = from_files
        args.input = input_
        return args

    def test1(self) -> None:
        """
        Test parsing comma-separated file list.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        file3 = f"{scratch_dir}/file3.txt"
        _create_test_file(file1)
        _create_test_file(file2)
        _create_test_file(file3)
        files_str = f"{file1},{file2},{file3}"
        args = self._make_namespace_args(files=files_str)
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Prepare outputs.
        expected = [file1, file2, file3]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test parsing file containing list of files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        file3 = f"{scratch_dir}/file3.txt"
        _create_test_file(file1)
        _create_test_file(file2)
        _create_test_file(file3)
        list_file = f"{scratch_dir}/list.txt"
        content = f"{file1}\n{file2}\n{file3}\n"
        _create_test_file(list_file, content=content)
        args = self._make_namespace_args(from_files=list_file)
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Prepare outputs.
        expected = [file1, file2, file3]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test parsing file with empty lines and comments.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        _create_test_file(file1)
        _create_test_file(file2)
        list_file = f"{scratch_dir}/list.txt"
        content = f"""
        # This is a comment
        {file1}

        # Another comment
        {file2}

        """
        _create_test_file(list_file, content=content)
        args = self._make_namespace_args(from_files=list_file)
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Prepare outputs.
        expected = [file1, file2]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test parsing repeated --input arguments.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        _create_test_file(file1)
        _create_test_file(file2)
        input_files = [file1, file2]
        args = self._make_namespace_args(input_=input_files)
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Prepare outputs.
        expected = [file1, file2]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test5(self) -> None:
        """
        Test that single -i/--input still works.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = f"{scratch_dir}/file1.txt"
        _create_test_file(file1)
        args = self._make_namespace_args(input_=file1)
        # Run test.
        actual = hparser.parse_multi_file_args(args)
        # Prepare outputs.
        expected = [file1]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test6(self) -> None:
        """
        Test that non-existent files raise error.
        """
        # Prepare inputs.
        file1 = "/nonexistent/file1.txt"
        file2 = "/nonexistent/file2.txt"
        files_str = f"{file1},{file2}"
        args = self._make_namespace_args(files=files_str)
        # Run test.
        with self.assertRaises(AssertionError):
            hparser.parse_multi_file_args(args)

    def test7(self) -> None:
        """
        Test empty file list handling.
        """
        # Prepare inputs.
        args = self._make_namespace_args()
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            hparser.parse_multi_file_args(args)
        # Check outputs.
        error_msg = str(cm.exception)
        self.assertIn("No input files specified", error_msg)


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
        hparser.add_input_output_args(parser)
        args_list = ["-i", "input.txt"]
        # Run test.
        args = parser.parse_args(args_list)
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
        in_required = False
        out_required = False
        hparser.add_input_output_args(
            parser, in_required=in_required, out_required=out_required
        )
        args_list = ["-i", "input.txt", "-o", "output.txt"]
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.input, "input.txt")
        self.assertEqual(args.output, "output.txt")

    def test3(self) -> None:
        """
        Test parsing --input_files argument.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        in_required = False
        out_required = False
        hparser.add_input_output_args(
            parser, in_required=in_required, out_required=out_required
        )
        args_list = ["--input_files", "file1.txt,file2.txt"]
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs. With nargs='+', input_files is now a list.
        expected = ["file1.txt,file2.txt"]
        self.assertEqual(args.input_files, expected)

    def test4(self) -> None:
        """
        Test parsing --from_file argument.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        in_required = False
        out_required = False
        hparser.add_input_output_args(
            parser, in_required=in_required, out_required=out_required
        )
        args_list = ["--from_file", "files.txt"]
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.from_file, "files.txt")


# #############################################################################
# Test_parse_input_output_files
# #############################################################################


class Test_parse_input_output_files(hunitest.TestCase):
    """
    Test the `parse_input_output_files()` function.
    """

    def _make_io_parser_args(self, args_list: List[str]) -> "argparse.Namespace":
        """
        Create an ArgumentParser with input/output args and parse the given list.
        """
        parser = _make_parser_with_input_output_args(
            in_required=False, out_required=False
        )
        return parser.parse_args(args_list)

    def test1(self) -> None:
        """
        Test that None is returned when neither option is provided.
        """
        # Prepare inputs.
        args_list = ["-i", "input.txt"]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Check outputs.
        self.assertIsNone(result)

    def test2(self) -> None:
        """
        Test parsing comma-separated file list.
        """
        # Prepare inputs.
        args_list = ["--input_files", "file1.txt,file2.txt,file3.txt"]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Check outputs.
        self.assertEqual(result, expected)

    def test3(self) -> None:
        """
        Test parsing space-separated file list.
        """
        # Prepare inputs.
        args_list = ["--input_files", "file1.txt file2.txt file3.txt"]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Check outputs.
        self.assertEqual(result, expected)

    def test4(self) -> None:
        """
        Test parsing mixed comma and space separators.
        """
        # Prepare inputs.
        args_list = ["--input_files", "file1.txt,file2.txt file3.txt"]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Check outputs.
        self.assertEqual(result, expected)

    def test5(self) -> None:
        """
        Test parsing single file from --input_files.
        """
        # Prepare inputs.
        args_list = ["--input_files", "single.txt"]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Prepare outputs.
        expected = ["single.txt"]
        # Check outputs.
        self.assertEqual(result, expected)

    def test6(self) -> None:
        """
        Test parsing files from --from_file.
        """
        # Prepare inputs.
        out_dir = self.get_scratch_space()
        file_list_path = os.path.join(out_dir, "files.txt")
        content = "file1.txt\nfile2.txt\nfile3.txt\n"
        _create_test_file(file_list_path, content=content)
        args_list = ["--from_file", file_list_path]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Check outputs.
        self.assertEqual(result, expected)

    def test7(self) -> None:
        """
        Test parsing files from --from_file with empty lines.
        """
        # Prepare inputs.
        out_dir = self.get_scratch_space()
        file_list_path = os.path.join(out_dir, "files.txt")
        content = "file1.txt\n\nfile2.txt\n  \nfile3.txt\n"
        _create_test_file(file_list_path, content=content)
        args_list = ["--from_file", file_list_path]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Prepare outputs.
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        # Check outputs.
        self.assertEqual(result, expected)

    def test8(self) -> None:
        """
        Test that FileNotFoundError is raised for non-existent file.
        """
        # Prepare inputs.
        file_path = "/nonexistent/path/files.txt"
        args_list = ["--from_file", file_path]
        args = self._make_io_parser_args(args_list)
        # Run test.
        with self.assertRaises(FileNotFoundError):
            hparser.parse_input_output_files(args)

    def test9(self) -> None:
        """
        Test parsing multiple files passed as separate arguments (shell glob expansion).
        """
        # This simulates shell expansion: `--input_files *.md`
        # becomes multiple arguments: `--input_files file1.md file2.md file3.md`
        # Prepare inputs.
        args_list = ["--input_files", "file1.md", "file2.md", "file3.md"]
        args = self._make_io_parser_args(args_list)
        # Run test.
        result = hparser.parse_input_output_files(args)
        # Prepare outputs.
        expected = ["file1.md", "file2.md", "file3.md"]
        # Check outputs.
        self.assertEqual(result, expected)


# #############################################################################
# Test_parse_input_output_args
# #############################################################################


class Test_parse_input_output_args(hunitest.TestCase):
    """
    Test the `parse_input_output_args()` function.
    """

    def helper(
        self, args_list: List[str], expected_in: str, expected_out: str
    ) -> None:
        """
        Test helper for `parse_input_output_args()`.

        :param args_list: Command-line arguments
        :param expected_in: Expected input file
        :param expected_out: Expected output file
        """
        parser = _make_parser_with_input_output_args(
            in_required=False, out_required=False
        )
        args = parser.parse_args(args_list)
        in_file, out_file = hparser.parse_input_output_args(args)
        self.assertEqual(in_file, expected_in)
        self.assertEqual(out_file, expected_out)

    def test1(self) -> None:
        """
        Test parsing with only input specified (output defaults to input).
        """
        # Prepare inputs.
        args_list = ["-i", "input.txt"]
        # Prepare outputs.
        expected_in = "input.txt"
        expected_out = "input.txt"
        # Run test.
        self.helper(args_list, expected_in, expected_out)

    def test2(self) -> None:
        """
        Test parsing with both input and output specified.
        """
        # Prepare inputs.
        args_list = ["-i", "input.txt", "-o", "output.txt"]
        # Prepare outputs.
        expected_in = "input.txt"
        expected_out = "output.txt"
        # Run test.
        self.helper(args_list, expected_in, expected_out)

    def test3(self) -> None:
        """
        Test parsing with stdin as input.
        """
        # Prepare inputs.
        args_list = ["-i", "-", "-o", "output.txt"]
        # Prepare outputs.
        expected_in = "-"
        expected_out = "output.txt"
        # Run test.
        self.helper(args_list, expected_in, expected_out)

    def test4(self) -> None:
        """
        Test parsing with stdout as output.
        """
        # Prepare inputs.
        args_list = ["-i", "input.txt", "-o", "-"]
        # Prepare outputs.
        expected_in = "input.txt"
        expected_out = "-"
        # Run test.
        self.helper(args_list, expected_in, expected_out)


# #############################################################################
# Test_from_file
# #############################################################################


class Test_from_file(hunitest.TestCase):
    """
    Test the `from_file()` function.
    """

    def helper(self, content: str, expected: List[str]) -> None:
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
        # Prepare inputs.
        content = "line1\nline2\nline3"
        # Prepare outputs.
        expected = ["line1", "line2", "line3"]
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test reading an empty file.
        """
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected = [""]
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test reading file with trailing newline.
        """
        # Prepare inputs.
        content = "line1\nline2\n"
        # Prepare outputs.
        expected = ["line1", "line2", ""]
        # Run test.
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
        # Prepare inputs.
        input_data = "line1\nline2\nline3"
        # Prepare outputs.
        expected_content = "line1\nline2\nline3"
        # Run test.
        self.helper(input_data, expected_content)

    def test2(self) -> None:
        """
        Test writing a list of strings to a file.
        """
        # Prepare inputs.
        input_data = ["line1", "line2", "line3"]
        # Prepare outputs.
        expected_content = "line1\nline2\nline3"
        # Run test.
        self.helper(input_data, expected_content)

    def test3(self) -> None:
        """
        Test writing an empty list to a file.
        """
        # Prepare inputs.
        input_data: List = []
        # Prepare outputs.
        expected_content = ""
        # Run test.
        self.helper(input_data, expected_content)

    def test4(self) -> None:
        """
        Test that writing to file overwrites existing content.
        """
        # Prepare inputs.
        out_dir = self.get_scratch_space()
        file_path = os.path.join(out_dir, "output.txt")
        old_content = "old content"
        new_content = "new content"
        hparser.to_file(old_content, file_path)
        hparser.to_file(new_content, file_path)
        # Run test.
        with open(file_path, "r") as f:
            written = f.read()
        # Check outputs.
        self.assertEqual(written, new_content)


# #############################################################################
# Test_add_file_type_filter_args
# #############################################################################


class Test_add_file_type_filter_args(hunitest.TestCase):
    """
    Test adding file type filter arguments to parser.
    """

    def test1(self) -> None:
        """
        Test that correct arguments are added to parser.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        file_types_default = "py,ipynb"
        hparser.add_file_type_filter_args(
            parser, file_types_default=file_types_default
        )
        args_list = []
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertTrue(hasattr(args, "file_types"))
        self.assertTrue(hasattr(args, "skip_file_types"))
        self.assertEqual(args.file_types, file_types_default)
        self.assertEqual(args.skip_file_types, "")

    def test2(self) -> None:
        """
        Test custom default for file_types.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        file_types_default = "py,md"
        hparser.add_file_type_filter_args(
            parser, file_types_default=file_types_default
        )
        args_list = []
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.file_types, file_types_default)


# #############################################################################
# Test_parse_file_type_filter_args
# #############################################################################


class Test_parse_file_type_filter_args(hunitest.TestCase):
    """
    Test parsing file type filter arguments and filtering files.
    """

    def helper(
        self,
        parse_args_list: List[str],
        files: List[str],
        expected: List[str],
    ) -> None:
        """
        Test helper for `parse_file_type_filter_args()`.

        :param parse_args_list: Arguments to pass to parse_args
        :param files: List of files to filter
        :param expected: Expected filtered files
        """
        parser = argparse.ArgumentParser()
        hparser.add_file_type_filter_args(parser, file_types_default="py,ipynb")
        args = parser.parse_args(parse_args_list)
        actual = hparser.parse_file_type_filter_args(args, files)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test filtering files with default file types (py,ipynb).
        """
        # Prepare inputs.
        parse_args_list = []
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb"]
        # Run test.
        self.helper(parse_args_list, files, expected)

    def test2(self) -> None:
        """
        Test filtering files with custom file types.
        """
        # Prepare inputs.
        parse_args_list = ["--file_types", "py,md,txt"]
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        # Prepare outputs.
        expected = ["file1.py", "file3.md", "file4.txt"]
        # Run test.
        self.helper(parse_args_list, files, expected)

    def test3(self) -> None:
        """
        Test filtering with whitespace in comma-separated list.
        """
        # Prepare inputs.
        parse_args_list = ["--file_types", "py , ipynb , md"]
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb", "file3.md"]
        # Run test.
        self.helper(parse_args_list, files, expected)

    def test4(self) -> None:
        """
        Test filtering with skip_file_types to exclude extensions.
        """
        # Prepare inputs.
        parse_args_list = ["--skip_file_types", "txt"]
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb", "file3.md"]
        # Run test.
        self.helper(parse_args_list, files, expected)

    def test5(self) -> None:
        """
        Test filtering with multiple skip_file_types.
        """
        # Prepare inputs.
        parse_args_list = ["--skip_file_types", "txt,md"]
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb"]
        # Run test.
        self.helper(parse_args_list, files, expected)

    def test6(self) -> None:
        """
        Test filtering that excludes all file types with skip.
        """
        # Prepare inputs.
        parse_args_list = ["--skip_file_types", "py,ipynb,md,txt"]
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        # Prepare outputs.
        expected: List = []
        # Run test.
        self.helper(parse_args_list, files, expected)


# #############################################################################
# Test_filter_files_by_extensions
# #############################################################################


class Test_filter_files_by_extensions(hunitest.TestCase):
    """
    Test filtering files by their extensions.
    """

    def helper(
        self,
        files: List[str],
        file_types_str: str,
        skip_file_types_str: str,
        expected: List[str],
    ) -> None:
        """
        Test helper for `filter_files_by_extensions()`.

        :param files: List of files to filter
        :param file_types_str: Comma-separated file types to include
        :param skip_file_types_str: Comma-separated file types to skip
        :param expected: Expected filtered files
        """
        actual = hparser.filter_files_by_extensions(
            files,
            file_types_str,
            skip_file_types_str,
        )
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test filtering with no filters (empty strings) returns all files.
        """
        # Prepare inputs.
        files = ["file1.py", "file2.ipynb", "file3.md"]
        file_types_str = ""
        skip_file_types_str = ""
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb", "file3.md"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test2(self) -> None:
        """
        Test filtering with file_types to include only specific extensions.
        """
        # Prepare inputs.
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        file_types_str = "py,ipynb"
        skip_file_types_str = ""
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test3(self) -> None:
        """
        Test filtering with skip_file_types to exclude specific extensions.
        """
        # Prepare inputs.
        files = ["file1.py", "file2.ipynb", "file3.md", "file4.txt"]
        file_types_str = ""
        skip_file_types_str = "txt,md"
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test4(self) -> None:
        """
        Test filtering with single file type.
        """
        # Prepare inputs.
        files = ["file1.py", "file2.ipynb", "file3.md"]
        file_types_str = "py"
        skip_file_types_str = ""
        # Prepare outputs.
        expected = ["file1.py"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test5(self) -> None:
        """
        Test filtering with files that have no extension (no dot).
        """
        # Prepare inputs.
        files = ["file1", "file2.py", "file3.ipynb"]
        file_types_str = "py"
        skip_file_types_str = ""
        # Prepare outputs.
        expected = ["file2.py"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test6(self) -> None:
        """
        Test filtering with whitespace in extension list.
        """
        # Prepare inputs.
        files = ["file1.py", "file2.ipynb", "file3.md"]
        file_types_str = "py , ipynb"
        skip_file_types_str = ""
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test7(self) -> None:
        """
        Test filtering with skip_file_types and multiple extensions.
        """
        # Prepare inputs.
        files = [
            "file1.py",
            "file2.ipynb",
            "file3.md",
            "file4.txt",
            "file5.log",
        ]
        file_types_str = ""
        skip_file_types_str = "txt,log,md"
        # Prepare outputs.
        expected = ["file1.py", "file2.ipynb"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test8(self) -> None:
        """
        Test filtering that results in empty list.
        """
        # Prepare inputs.
        files = ["file1.py", "file2.ipynb"]
        file_types_str = "md,txt"
        skip_file_types_str = ""
        # Prepare outputs.
        expected: List = []
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test9(self) -> None:
        """
        Test filtering preserves file order.
        """
        # Prepare inputs.
        files = ["z.py", "a.ipynb", "m.py", "b.ipynb", "c.py"]
        file_types_str = "py"
        skip_file_types_str = ""
        # Prepare outputs.
        expected = ["z.py", "m.py", "c.py"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)

    def test10(self) -> None:
        """
        Test filtering with complex path names.
        """
        # Prepare inputs.
        files = [
            "path/to/file1.py",
            "another/path/file2.ipynb",
            "file3.md",
        ]
        file_types_str = "py,ipynb"
        skip_file_types_str = ""
        # Prepare outputs.
        expected = ["path/to/file1.py", "another/path/file2.ipynb"]
        # Run test.
        self.helper(files, file_types_str, skip_file_types_str, expected)
