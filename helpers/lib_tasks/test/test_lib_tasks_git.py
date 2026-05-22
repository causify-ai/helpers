from typing import List

import pytest

import helpers.hgit as hgit
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_git as hltltagi
import helpers.lib_tasks.test.test_lib_tasks as httestlib

# pylint: disable=protected-access


# #############################################################################
# TestLibTasksGitCreatePatch1
# #############################################################################


@pytest.mark.slow(reason="Around 7s")
@pytest.mark.skipif(
    not hgit.is_in_amp_as_supermodule(),
    reason="Run only in amp as super-module",
)
class TestLibTasksGitCreatePatch1(hunitest.TestCase):
    """
    Test `git_patch_create()`.
    """

    @staticmethod
    def helper(
        modified: bool, branch: bool, last_commit: bool, files: str
    ) -> None:
        ctx = httestlib._build_mock_context_returning_ok()
        #
        mode = "tar"
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )
        #
        mode = "diff"
        hltltagi.git_patch_create(
            ctx, mode, modified, branch, last_commit, files
        )

    def test1(self) -> None:
        """
        Test modified files mode.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        files = ""
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test2(self) -> None:
        """
        Test branch mode.
        """
        # Prepare inputs.
        modified = False
        branch = True
        last_commit = False
        files = ""
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test3(self) -> None:
        """
        Test last commit mode.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = False
        branch = False
        last_commit = True
        files = ""
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test4(self) -> None:
        """
        Test with specific files.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        files = __file__
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test5(self) -> None:
        """
        Test with all flags False raises AssertionError.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        mode = "diff"
        modified = False
        branch = False
        last_commit = False
        files = __file__
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hltltagi.git_patch_create(
                ctx, mode, modified, branch, last_commit, files
            )
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '0'
        ==
        '1'
        Specify only one among --modified, --branch, --last-commit
        """
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# TestFilterGitFilesByType
# #############################################################################


class TestFilterGitFilesByType(hunitest.TestCase):
    """
    Test _filter_git_files_by_type() function.
    """

    def helper(
        self,
        files: List[str],
        file_types: List[str],
        expected: List[str],
    ) -> None:
        """
        Test helper for _filter_git_files_by_type.

        :param files: List of files to filter
        :param file_types: List of file extensions to include (e.g., ["py", "ipynb", "md"])
        :param expected: Expected filtered result
        """
        # Run test.
        result = hltltagi._filter_git_files_by_type(files, file_types)
        # Check outputs.
        self.assertEqual(result, expected)

    def test1(self) -> None:
        """
        Test filtering to include only Python files.
        """
        # Prepare inputs.
        files = ["foo.py", "bar.ipynb", "baz.md"]
        file_types = ["py"]
        # Prepare outputs.
        expected = ["foo.py"]
        # Run test.
        self.helper(files, file_types, expected)

    def test2(self) -> None:
        """
        Test filtering to include only Jupyter notebooks.
        """
        # Prepare inputs.
        files = ["foo.py", "bar.ipynb", "baz.md"]
        file_types = ["ipynb"]
        # Prepare outputs.
        expected = ["bar.ipynb"]
        # Run test.
        self.helper(files, file_types, expected)

    def test3(self) -> None:
        """
        Test filtering to include only Markdown files.
        """
        # Prepare inputs.
        files = ["foo.py", "bar.ipynb", "baz.md"]
        file_types = ["md"]
        # Prepare outputs.
        expected = ["baz.md"]
        # Run test.
        self.helper(files, file_types, expected)

    def test4(self) -> None:
        """
        Test filtering with multiple file types.
        """
        # Prepare inputs.
        files = ["foo.py", "bar.ipynb", "baz.md", "qux.txt"]
        file_types = ["py", "md"]
        # Prepare outputs.
        expected = ["foo.py", "baz.md"]
        # Run test.
        self.helper(files, file_types, expected)

    def test5(self) -> None:
        """
        Test filtering with all file types.
        """
        # Prepare inputs.
        files = ["foo.py", "bar.ipynb", "baz.md"]
        file_types = ["py", "ipynb", "md"]
        # Prepare outputs.
        expected = files
        # Run test.
        self.helper(files, file_types, expected)

    def test6(self) -> None:
        """
        Test filtering with empty file list.
        """
        # Prepare inputs.
        files: List[str] = []
        file_types = ["py", "ipynb"]
        # Prepare outputs.
        expected: List[str] = []
        # Run test.
        self.helper(files, file_types, expected)

    def test7(self) -> None:
        """
        Test filtering when no files match.
        """
        # Prepare inputs.
        files = ["foo.py", "bar.ipynb", "baz.md"]
        file_types: List[str] = []
        # Prepare outputs.
        expected = files
        # Run test.
        self.helper(files, file_types, expected)

    def test8(self) -> None:
        """
        Test that filtering preserves file order.
        """
        # Prepare inputs.
        files = ["c.py", "a.ipynb", "b.md", "d.py"]
        file_types = ["py", "md"]
        # Prepare outputs.
        expected = ["c.py", "b.md", "d.py"]
        # Run test.
        self.helper(files, file_types, expected)
