import os
from unittest import mock

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.extract_gdoc_map as dshdexgm


# #############################################################################
# Test_extract_doc_info
# #############################################################################


class Test_extract_doc_info(hunitest.TestCase):
    """
    Test the `_extract_doc_info()` function.
    """

    def helper(self, content: str, expected_doc_id: str) -> None:
        """
        Test helper for `_extract_doc_info()`.

        :param content: File content to write
        :param expected_doc_id: Expected doc_id in tuple result
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "doc.gdoc")
        hio.to_file(file_path, content)
        # Prepare outputs.
        expected = (file_path, expected_doc_id)
        # Run test.
        actual = dshdexgm._extract_doc_info(file_path)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test happy path: valid JSON with a `doc_id`.
        """
        # Prepare inputs.
        content = '{"doc_id": "abc123", "resource_id": "x"}'
        # Prepare outputs.
        expected_doc_id = "abc123"
        # Run test.
        self.helper(content, expected_doc_id)

    def test2(self) -> None:
        """
        Test edge case: invalid JSON content returns an empty `doc_id`.
        """
        # Prepare inputs.
        content = "not json"
        # Prepare outputs.
        expected_doc_id = ""
        # Run test.
        self.helper(content, expected_doc_id)

    def test3(self) -> None:
        """
        Test edge case: valid JSON without a `doc_id` key.
        """
        # Prepare inputs.
        content = '{"resource_id": "x"}'
        # Prepare outputs.
        expected_doc_id = ""
        # Run test.
        self.helper(content, expected_doc_id)


# #############################################################################
# Test_find_gdoc_files
# #############################################################################


class Test_find_gdoc_files(hunitest.TestCase):
    """
    Test the `_find_gdoc_files()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: finds only `.gdoc` files, ignoring other extensions.
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        gdoc_file = os.path.join(input_dir, "a.gdoc")
        other_file = os.path.join(input_dir, "b.txt")
        hio.to_file(gdoc_file, "{}")
        hio.to_file(other_file, "text")
        # Prepare outputs.
        expected = [gdoc_file]
        # Run test.
        actual = dshdexgm._find_gdoc_files(input_dir)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test edge case: empty directory returns an empty list.
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        # Prepare outputs.
        expected: list = []
        # Run test.
        actual = dshdexgm._find_gdoc_files(input_dir)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_generate_doc_links_full_path
# #############################################################################


class Test_generate_doc_links_full_path(hunitest.TestCase):
    """
    Test the `_generate_doc_links_full_path()` function.
    """

    def helper(self, file_path_rel: str, content: str, expected: str) -> None:
        """
        Test helper for `_generate_doc_links_full_path()`.

        :param file_path_rel: Relative file path (including filename)
        :param content: Content to write to file
        :param expected: Expected output string
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        file_path = os.path.join(input_dir, file_path_rel)
        hio.to_file(file_path, content)
        gdoc_files = [file_path]
        # Run test.
        actual = dshdexgm._generate_doc_links_full_path(gdoc_files, input_dir)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test happy path: builds a single markdown link with the full
        relative path in the link text.
        """
        # Prepare inputs.
        file_path_rel = "sub/my_doc.gdoc"
        content = '{"doc_id": "abc123"}'
        # Prepare outputs.
        expected = (
            "- [sub/my_doc.gdoc/my_doc]"
            "(https://docs.google.com/document/d/abc123)"
        )
        # Run test.
        self.helper(file_path_rel, content, expected)

    def test2(self) -> None:
        """
        Test edge case: files without a `doc_id` are skipped.
        """
        # Prepare inputs.
        file_path_rel = "my_doc.gdoc"
        content = "{}"
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(file_path_rel, content, expected)


# #############################################################################
# Test_generate_doc_links_default
# #############################################################################


class Test_generate_doc_links_default(hunitest.TestCase):
    """
    Test the `_generate_doc_links_default()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: builds a bullet with the path and an indented
        sub-bullet with the link.
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        file_path = os.path.join(input_dir, "sub", "my_doc.gdoc")
        hio.to_file(file_path, '{"doc_id": "abc123"}')
        gdoc_files = [file_path]
        # Prepare outputs.
        expected = """
            - sub/my_doc.gdoc
              - [my_doc](https://docs.google.com/document/d/abc123)
            """
        expected = hprint.dedent(expected)
        # Run test.
        actual = dshdexgm._generate_doc_links_default(gdoc_files, input_dir)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_generate_doc_links
# #############################################################################


class Test_generate_doc_links(hunitest.TestCase):
    """
    Test the `_generate_doc_links()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: `full_path` style delegates to
        `_generate_doc_links_full_path()`.
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        file_path = os.path.join(input_dir, "my_doc.gdoc")
        hio.to_file(file_path, '{"doc_id": "abc123"}')
        gdoc_files = [file_path]
        # Prepare outputs.
        expected = (
            "- [my_doc.gdoc/my_doc]"
            "(https://docs.google.com/document/d/abc123)"
        )
        # Run test.
        actual = dshdexgm._generate_doc_links(
            gdoc_files, input_dir, style="full_path"
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test edge case: an invalid style raises an assertion error.
        """
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdexgm._generate_doc_links([], ".", style="invalid")


# #############################################################################
# Test_extract_gdoc_map
# #############################################################################


class Test_extract_gdoc_map(hunitest.TestCase):
    """
    Test the `extract_gdoc_map()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: writes the generated content to an output file.
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        file_path = os.path.join(input_dir, "my_doc.gdoc")
        hio.to_file(file_path, '{"doc_id": "abc123"}')
        output_file = os.path.join(input_dir, "out.md")
        # Prepare outputs.
        expected = """
        - my_doc.gdoc
          - [my_doc](https://docs.google.com/document/d/abc123)
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = dshdexgm.extract_gdoc_map(input_dir, output_file=output_file)
        # Check outputs.
        self.assert_equal(actual, expected)
        actual_file_content = hio.from_file(output_file)
        self.assert_equal(actual_file_content, expected)

    def test2(self) -> None:
        """
        Test edge case: no `.gdoc` files found returns an empty string.
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        # Prepare outputs.
        expected = ""
        # Run test.
        actual = dshdexgm.extract_gdoc_map(input_dir)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_extract_gdoc_map_py
# #############################################################################


class Test_extract_gdoc_map_py(hunitest.TestCase):
    """
    End-to-end tests for the `extract_gdoc_map.py` executable.
    """

    def _run_main(self, argv: list) -> None:
        """
        Run `dshdexgm._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshdexgm._parse()
        with mock.patch("sys.argv", argv):
            dshdexgm._main(parser)

    def test1(self) -> None:
        """
        Test happy path: `--style full_path` writes links to the output
        file.
        """
        # Prepare inputs.
        input_dir = self.get_scratch_space()
        file_path = os.path.join(input_dir, "my_doc.gdoc")
        hio.to_file(file_path, '{"doc_id": "abc123"}')
        output_file = os.path.join(input_dir, "out.md")
        argv = [
            "extract_gdoc_map.py",
            "--input_dir",
            input_dir,
            "--output_file",
            output_file,
            "--style",
            "full_path",
        ]
        # Prepare outputs.
        expected = (
            "- [my_doc.gdoc/my_doc]"
            "(https://docs.google.com/document/d/abc123)"
        )
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = hio.from_file(output_file)
        self.assert_equal(actual, expected)
