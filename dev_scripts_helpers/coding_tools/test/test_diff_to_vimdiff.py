import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.coding_tools.diff_to_vimdiff as dscdtovi


class Test_load_file_list(hunitest.TestCase):

    def helper(self, content: str, expected: set) -> None:
        """
        Test helper for _load_file_list.

        :param content: Content to write to file list
        :param expected: Expected set of file paths
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_list = os.path.join(scratch_dir, "files.txt")
        hio.to_file(file_list, content)
        # Run test.
        result = dscdtovi._load_file_list(file_list)
        # Check outputs.
        self.assertEqual(result, expected)

    def test1(self) -> None:
        """
        Test loading a simple file list.
        """
        # Prepare inputs.
        content = "file1.py\nfile2.py\nfile3.txt"
        # Prepare outputs.
        expected = {"file1.py", "file2.py", "file3.txt"}
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test loading file list ignores empty lines.
        """
        # Prepare inputs.
        content = "file1.py\n\nfile2.py\n\n"
        # Prepare outputs.
        expected = {"file1.py", "file2.py"}
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test loading file list ignores comments.
        """
        # Prepare inputs.
        content = "# Comment\nfile1.py\n# Another comment\nfile2.py"
        # Prepare outputs.
        expected = {"file1.py", "file2.py"}
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test loading file list handles whitespace.
        """
        # Prepare inputs.
        content = "  file1.py  \n  file2.py  "
        # Prepare outputs.
        expected = {"file1.py", "file2.py"}
        # Run test.
        self.helper(content, expected)


class Test_path_matches_any(hunitest.TestCase):
    """
    Test _path_matches_any() function.
    """

    def helper(self, path: str, file_list: set, expected: bool) -> None:
        """
        Test helper for _path_matches_any.

        :param path: Path to test
        :param file_list: Set of file paths to match against
        :param expected: Expected result
        """
        # Run test.
        result = dscdtovi._path_matches_any(path, file_list)
        # Check outputs.
        self.assertEqual(result, expected)

    def test1(self) -> None:
        """
        Test exact path match.
        """
        # Prepare inputs.
        path = "file1.py"
        file_list = {"file1.py", "file2.py"}
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(path, file_list, expected)

    def test2(self) -> None:
        """
        Test when path doesn't match.
        """
        # Prepare inputs.
        path = "file3.py"
        file_list = {"file1.py", "file2.py"}
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(path, file_list, expected)

    def test3(self) -> None:
        """
        Test matching when path is a suffix.
        """
        # Prepare inputs.
        path = "/home/user/src/file1.py"
        file_list = {"file1.py"}
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(path, file_list, expected)

    def test4(self) -> None:
        """
        Test matching with subdirectories.
        """
        # Prepare inputs.
        path = "/home/user/src/subdir/file1.py"
        file_list = {"subdir/file1.py"}
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(path, file_list, expected)

    def test5(self) -> None:
        """
        Test matching directory paths.
        """
        # Prepare inputs.
        path = "/home/user/src/mydir/file.py"
        file_list = {"mydir/file.py"}
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(path, file_list, expected)


class Test_filter_diff_output(hunitest.TestCase):

    def helper(
        self,
        diff_content: str,
        file_list_content: str | None,
        expected: str,
    ) -> None:
        """
        Test helper for _filter_diff_output.

        :param diff_content: Content to write to diff file
        :param file_list_content: Content to write to file list (or None)
        :param expected: Expected filtered output
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        diff_file = os.path.join(scratch_dir, "diff.txt")
        hio.to_file(diff_file, diff_content)
        if file_list_content is not None:
            file_list = os.path.join(scratch_dir, "files.txt")
            hio.to_file(file_list, file_list_content)
        else:
            file_list = None
        # Run test.
        dscdtovi._filter_diff_output(diff_file, file_list)
        # Check outputs.
        result = hio.from_file(diff_file)
        self.assert_equal(result, expected)

    def test1(self) -> None:
        """
        Test filtering 'Only in' diff entries.
        """
        # Prepare inputs.
        diff_content = """
            Only in /dir1: file1.py
            Only in /dir1: file2.py
            Only in /dir1: file3.py
        """
        diff_content = hprint.dedent(diff_content)
        file_list_content = "file1.py\nfile2.py"
        # Prepare outputs.
        expected = """
            Only in /dir1: file1.py
            Only in /dir1: file2.py
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(diff_content, file_list_content, expected)

    def test2(self) -> None:
        """
        Test filtering 'Files ... differ' diff entries.
        """
        # Prepare inputs.
        diff_content = """
            Files /dir1/file1.py and /dir2/file1.py differ
            Files /dir1/file2.py and /dir2/file2.py differ
            Files /dir1/file3.py and /dir2/file3.py differ
        """
        diff_content = hprint.dedent(diff_content)
        file_list_content = "file1.py\nfile2.py"
        # Prepare outputs.
        expected = """
            Files /dir1/file1.py and /dir2/file1.py differ
            Files /dir1/file2.py and /dir2/file2.py differ
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(diff_content, file_list_content, expected)

    def test3(self) -> None:
        """
        Test filtering mixed diff entry types.
        """
        # Prepare inputs.
        diff_content = """
            Only in /dir1: file1.py
            Files /dir1/file2.py and /dir2/file2.py differ
            Only in /dir1: file3.py
        """
        diff_content = hprint.dedent(diff_content)
        file_list_content = "file1.py\nfile2.py"
        # Prepare outputs.
        expected = """
            Only in /dir1: file1.py
            Files /dir1/file2.py and /dir2/file2.py differ
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(diff_content, file_list_content, expected)

    def test4(self) -> None:
        """
        Test that filtering with None file_list does nothing.
        """
        # Prepare inputs.
        diff_content = "Only in /dir1: file1.py\nOnly in /dir1: file2.py"
        file_list_content = None
        # Prepare outputs.
        expected = diff_content
        # Run test.
        self.helper(diff_content, file_list_content, expected)

    def test5(self) -> None:
        """
        Test filtering an empty diff file.
        """
        # Prepare inputs.
        diff_content = ""
        file_list_content = "file1.py"
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(diff_content, file_list_content, expected)

    def test6(self) -> None:
        """
        Test filtering with subdirectory paths.
        """
        # Prepare inputs.
        diff_content = """
            Only in /dir1/src: subdir/file1.py
            Only in /dir1/src: other/file2.py
        """
        diff_content = hprint.dedent(diff_content)
        file_list_content = "subdir/file1.py"
        # Prepare outputs.
        expected = "Only in /dir1/src: subdir/file1.py"
        # Run test.
        self.helper(diff_content, file_list_content, expected)
