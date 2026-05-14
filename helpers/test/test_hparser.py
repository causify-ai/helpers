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
        self.helper("1:5", (1, 5))

    def test2(self) -> None:
        """
        Test parsing range with same start and end.
        """
        self.helper("3:3", (3, 3))

    def test3(self) -> None:
        """
        Test parsing range with larger numbers.
        """
        self.helper("10:100", (10, 100))

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
        parser = argparse.ArgumentParser()
        hparser.add_multi_file_args(parser)
        namespace = parser.parse_args([])
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
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        file3 = f"{scratch_dir}/file3.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        self._create_test_file(file3)
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
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        file3 = f"{scratch_dir}/file3.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        self._create_test_file(file3)
        list_file = f"{scratch_dir}/list.txt"
        content = f"{file1}\n{file2}\n{file3}\n"
        self._create_test_file(list_file, content)
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
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        list_file = f"{scratch_dir}/list.txt"
        content = f"""
        # This is a comment
        {file1}

        # Another comment
        {file2}

        """
        self._create_test_file(list_file, content)
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
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
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
        file1 = f"{scratch_dir}/file1.txt"
        self._create_test_file(file1)
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
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser)
        args = parser.parse_args(["-i", "input.txt"])
        self.assertEqual(args.input, "input.txt")
        self.assertIsNone(args.output)
        self.assertIsNone(args.input_files)
        self.assertIsNone(args.from_file)

    def test2(self) -> None:
        """
        Test parsing both input and output arguments.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["-i", "input.txt", "-o", "output.txt"])
        self.assertEqual(args.input, "input.txt")
        self.assertEqual(args.output, "output.txt")

    def test3(self) -> None:
        """
        Test parsing --input_files argument.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--input_files", "file1.txt,file2.txt"])
        self.assertEqual(args.input_files, "file1.txt,file2.txt")

    def test4(self) -> None:
        """
        Test parsing --from_file argument.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--from_file", "files.txt"])
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
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["-i", "input.txt"])
        result = hparser.parse_input_output_files(args)
        self.assertIsNone(result)

    def test2(self) -> None:
        """
        Test parsing comma-separated file list.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--input_files", "file1.txt,file2.txt,file3.txt"])
        result = hparser.parse_input_output_files(args)
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        self.assertEqual(result, expected)

    def test3(self) -> None:
        """
        Test parsing space-separated file list.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--input_files", "file1.txt file2.txt file3.txt"])
        result = hparser.parse_input_output_files(args)
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        self.assertEqual(result, expected)

    def test4(self) -> None:
        """
        Test parsing mixed comma and space separators.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--input_files", "file1.txt,file2.txt file3.txt"])
        result = hparser.parse_input_output_files(args)
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        self.assertEqual(result, expected)

    def test5(self) -> None:
        """
        Test parsing single file from --input_files.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--input_files", "single.txt"])
        result = hparser.parse_input_output_files(args)
        self.assertEqual(result, ["single.txt"])

    def test6(self) -> None:
        """
        Test parsing files from --from_file.
        """
        out_dir = self.get_scratch_space()
        file_list_path = os.path.join(out_dir, "files.txt")
        with open(file_list_path, "w") as f:
            f.write("file1.txt\n")
            f.write("file2.txt\n")
            f.write("file3.txt\n")
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--from_file", file_list_path])
        result = hparser.parse_input_output_files(args)
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        self.assertEqual(result, expected)

    def test7(self) -> None:
        """
        Test parsing files from --from_file with empty lines.
        """
        out_dir = self.get_scratch_space()
        file_list_path = os.path.join(out_dir, "files.txt")
        with open(file_list_path, "w") as f:
            f.write("file1.txt\n")
            f.write("\n")
            f.write("file2.txt\n")
            f.write("  \n")
            f.write("file3.txt\n")
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--from_file", file_list_path])
        result = hparser.parse_input_output_files(args)
        expected = ["file1.txt", "file2.txt", "file3.txt"]
        self.assertEqual(result, expected)

    def test8(self) -> None:
        """
        Test that FileNotFoundError is raised for non-existent file.
        """
        parser = argparse.ArgumentParser()
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(["--from_file", "/nonexistent/path/files.txt"])
        with self.assertRaises(FileNotFoundError):
            hparser.parse_input_output_files(args)


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
        hparser.add_input_output_args(parser, in_required=False, out_required=False)
        args = parser.parse_args(args_list)
        in_file, out_file = hparser.parse_input_output_args(args)
        self.assertEqual(in_file, expected_in)
        self.assertEqual(out_file, expected_out)

    def test1(self) -> None:
        """
        Test parsing with only input specified (output defaults to input).
        """
        self.helper(["-i", "input.txt"], "input.txt", "input.txt")

    def test2(self) -> None:
        """
        Test parsing with both input and output specified.
        """
        self.helper(["-i", "input.txt", "-o", "output.txt"], "input.txt", "output.txt")

    def test3(self) -> None:
        """
        Test parsing with stdin as input.
        """
        self.helper(["-i", "-", "-o", "output.txt"], "-", "output.txt")

    def test4(self) -> None:
        """
        Test parsing with stdout as output.
        """
        self.helper(["-i", "input.txt", "-o", "-"], "input.txt", "-")


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
        self.helper("line1\nline2\nline3", ["line1", "line2", "line3"])

    def test2(self) -> None:
        """
        Test reading an empty file.
        """
        self.helper("", [""])

    def test3(self) -> None:
        """
        Test reading file with trailing newline.
        """
        self.helper("line1\nline2\n", ["line1", "line2", ""])


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
        content = "line1\nline2\nline3"
        self.helper(content, content)

    def test2(self) -> None:
        """
        Test writing a list of strings to a file.
        """
        lines = ["line1", "line2", "line3"]
        expected = "line1\nline2\nline3"
        self.helper(lines, expected)

    def test3(self) -> None:
        """
        Test writing an empty list to a file.
        """
        lines: list = []
        self.helper(lines, "")

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
