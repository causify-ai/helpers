import argparse
import os

import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hunit_test as hunitest

# #############################################################################
# TestParseLimitRange
# #############################################################################


class TestParseLimitRange(hunitest.TestCase):

    def test_parse_limit_range_valid1(self) -> None:
        """
        Test parsing valid range format.
        """
        limit_str = "1:5"
        expected = (1, 5)
        actual = hparser.parse_limit_range(limit_str)
        self.assertEqual(actual, expected)

    def test_parse_limit_range_valid2(self) -> None:
        """
        Test parsing valid range format with same start and end.
        """
        limit_str = "3:3"
        expected = (3, 3)
        actual = hparser.parse_limit_range(limit_str)
        self.assertEqual(actual, expected)

    def test_parse_limit_range_valid3(self) -> None:
        """
        Test parsing valid range format with larger numbers.
        """
        limit_str = "10:100"
        expected = (10, 100)
        actual = hparser.parse_limit_range(limit_str)
        self.assertEqual(actual, expected)

    def test_parse_limit_range_no_colon(self) -> None:
        """
        Test that missing colon raises assertion error.
        """
        limit_str = "15"
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test_parse_limit_range_multiple_colons(self) -> None:
        """
        Test that multiple colons raise assertion error.
        """
        limit_str = "1:2:3"
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test_parse_limit_range_invalid_start(self) -> None:
        """
        Test that non-integer start raises fatal error.
        """
        limit_str = "abc:5"
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test_parse_limit_range_invalid_end(self) -> None:
        """
        Test that non-integer end raises fatal error.
        """
        limit_str = "1:xyz"
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test_parse_limit_range_start_zero(self) -> None:
        """
        Test that start index of 0 raises assertion error.
        """
        limit_str = "0:5"
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test_parse_limit_range_end_zero(self) -> None:
        """
        Test that end index of 0 raises assertion error.
        """
        limit_str = "1:0"
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)

    def test_parse_limit_range_start_greater_than_end(self) -> None:
        """
        Test that start greater than end raises assertion error.
        """
        limit_str = "5:3"
        with self.assertRaises(AssertionError):
            hparser.parse_limit_range(limit_str)


# #############################################################################
# TestApplyLimitRange
# #############################################################################


class TestApplyLimitRange(hunitest.TestCase):

    def test_apply_limit_range_no_limit(self) -> None:
        """
        Test that None limit range returns original items.
        """
        items = ["a", "b", "c", "d", "e"]
        actual = hparser.apply_limit_range(items, None)
        self.assertEqual(actual, items)

    def test_apply_limit_range_valid_range(self) -> None:
        """
        Test applying valid range to items.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (1, 3)
        expected = ["b", "c", "d"]  # 0-indexed, inclusive
        actual = hparser.apply_limit_range(items, limit_range)
        self.assertEqual(actual, expected)

    def test_apply_limit_range_single_item(self) -> None:
        """
        Test applying range that selects single item.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (2, 2)
        expected = ["c"]
        actual = hparser.apply_limit_range(items, limit_range)
        self.assertEqual(actual, expected)

    def test_apply_limit_range_first_item(self) -> None:
        """
        Test applying range starting from first item.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (0, 1)
        expected = ["a", "b"]
        actual = hparser.apply_limit_range(items, limit_range)
        self.assertEqual(actual, expected)

    def test_apply_limit_range_last_item(self) -> None:
        """
        Test applying range ending at last item.
        """
        items = ["a", "b", "c", "d", "e"]
        limit_range = (3, 4)
        expected = ["d", "e"]
        actual = hparser.apply_limit_range(items, limit_range)
        self.assertEqual(actual, expected)

    def test_apply_limit_range_start_exceeds_length(self) -> None:
        """
        Test that start index exceeding items length raises assertion error.
        """
        items = ["a", "b", "c"]
        limit_range = (5, 6)
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test_apply_limit_range_end_exceeds_length(self) -> None:
        """
        Test that end index exceeding items length raises assertion error.
        """
        items = ["a", "b", "c"]
        limit_range = (1, 5)
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test_apply_limit_range_custom_item_name(self) -> None:
        """
        Test that custom item name doesn't affect functionality.
        """
        items = [1, 2, 3, 4, 5]
        limit_range = (0, 2)
        expected = [1, 2, 3]
        actual = hparser.apply_limit_range(
            items, limit_range, item_name="numbers"
        )
        self.assertEqual(actual, expected)

    def test_apply_limit_range_empty_list(self) -> None:
        """
        Test applying limit range to empty list.
        """
        items = []
        limit_range = (0, 1)
        with self.assertRaises(AssertionError):
            hparser.apply_limit_range(items, limit_range)

    def test_apply_limit_range_complex_objects(self) -> None:
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
        actual = hparser.apply_limit_range(items, limit_range)
        self.assertEqual(actual, expected)


# #############################################################################
# Test_add_multi_file_args
# #############################################################################


class Test_add_multi_file_args(hunitest.TestCase):
    def test_adds_correct_arguments(self) -> None:
        """
        Test that add_multi_file_args adds the correct arguments to parser.
        """
        # Prepare inputs.
        parser = argparse.ArgumentParser()
        # Run function.
        hparser.add_multi_file_args(parser)
        # Check that the arguments were added.
        namespace = parser.parse_args([])
        self.assertTrue(hasattr(namespace, "files"))
        self.assertTrue(hasattr(namespace, "from_files"))
        self.assertTrue(hasattr(namespace, "file_name"))


# #############################################################################
# Test_parse_multi_file_args
# #############################################################################


class Test_parse_multi_file_args(hunitest.TestCase):
    def test_files_comma_separated(self) -> None:
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
        args.file_name = None
        args.in_file_name = None
        # Run function.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2, file3]
        self.assert_equal(str(actual), str(expected))

    def test_from_files(self) -> None:
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
        args.file_name = None
        args.in_file_name = None
        # Run function.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2, file3]
        self.assert_equal(str(actual), str(expected))

    def test_from_files_with_empty_lines(self) -> None:
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
        args.file_name = None
        args.in_file_name = None
        # Run function.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2]
        self.assert_equal(str(actual), str(expected))

    def test_file_name_multiple(self) -> None:
        """
        Test parsing repeated --file_name arguments.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test files.
        file1 = f"{scratch_dir}/file1.txt"
        file2 = f"{scratch_dir}/file2.txt"
        self._create_test_file(file1)
        self._create_test_file(file2)
        # Create namespace with file_name argument.
        args = argparse.Namespace()
        args.files = None
        args.from_files = None
        args.file_name = [file1, file2]
        args.in_file_name = None
        # Run function.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1, file2]
        self.assert_equal(str(actual), str(expected))

    def test_backward_compatibility_single_file(self) -> None:
        """
        Test that single -i/--in_file_name still works.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test file.
        file1 = f"{scratch_dir}/file1.txt"
        self._create_test_file(file1)
        # Create namespace with in_file_name argument.
        args = argparse.Namespace()
        args.files = None
        args.from_files = None
        args.file_name = None
        args.in_file_name = file1
        # Run function.
        actual = hparser.parse_multi_file_args(args)
        # Check outputs.
        expected = [file1]
        self.assert_equal(str(actual), str(expected))

    def test_file_validation(self) -> None:
        """
        Test that non-existent files raise error.
        """
        # Create namespace with non-existent file.
        args = argparse.Namespace()
        args.files = "/nonexistent/file1.txt,/nonexistent/file2.txt"
        args.from_files = None
        args.file_name = None
        args.in_file_name = None
        # Run function and check that it raises error.
        with self.assertRaises(AssertionError):
            hparser.parse_multi_file_args(args)

    def test_empty_file_list(self) -> None:
        """
        Test empty file list handling.
        """
        # Prepare inputs.

        # Create namespace with no files.
        args = argparse.Namespace()
        args.files = None
        args.from_files = None
        args.file_name = None
        args.in_file_name = None
        # Run function and check that it raises error.
        with self.assertRaises(AssertionError) as cm:
            hparser.parse_multi_file_args(args)
        # Check the error message.
        act = str(cm.exception)
        self.assertIn("No input files specified", act)

    # Helper method.
    def _create_test_file(self, file_path: str, content: str = "test") -> None:
        """
        Create a test file with given content.
        """
        hio.create_dir(os.path.dirname(file_path), incremental=True)
        hio.to_file(file_path, content)
