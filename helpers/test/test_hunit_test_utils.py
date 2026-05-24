import logging
import os
import pprint
import subprocess
from typing import Optional

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestUnitTestRenamer
# #############################################################################


class TestUnitTestRenamer(hunitest.TestCase):
    """
    Test class renaming functionality.
    """

    @staticmethod
    def helper() -> str:
        """
        Create file content.
        """
        content = """
        class TestCases(hunitest.TestCase):
            def test_assert_equal1(self) -> None:
                actual = "hello world"
                expected = actual
                self.assert_equal(actual, expected)

            def test_check_string1(self) -> None:
                actual = "hello world"
                self.check_string(actual)
        """
        content = hprint.dedent(content)
        return content

    def helper_rename(
        self, old_name: str, new_name: str, content: str
    ) -> str:
        """
        Test helper for class renaming.

        :param old_name: Original class name
        :param new_name: New class name
        :param content: Content to rename
        :return: Renamed content
        """
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer(old_name, new_name, root_dir)
        actual, _ = renamer._rename_class(content)
        return actual

    def test1(self) -> None:
        """
        Test renaming of existing class.
        """
        # Prepare inputs.
        content = self.helper()
        # Prepare outputs.
        expected = """
        class TestNewCase(hunitest.TestCase):
            def test_assert_equal1(self) -> None:
                actual = "hello world"
                expected = actual
                self.assert_equal(actual, expected)

            def test_check_string1(self) -> None:
                actual = "hello world"
                self.check_string(actual)
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_rename("TestCases", "TestNewCase", content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test renaming of non existing class.
        """
        # Prepare inputs.
        content = self.helper()
        # Prepare outputs.
        expected = content
        # Run test.
        actual = self.helper_rename("TestCase", "TestNewCase", content)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# TestPytestRenameMethod
# #############################################################################


class TestPytestRenameMethod(hunitest.TestCase):
    """
    Test method renaming functionality.
    """

    @staticmethod
    def helper() -> str:
        """
        Create file content.
        """
        content = """
        class TestCases(hunitest.TestCase):
            def test1(self) -> None:
                actual = "hello world"
                expected = actual
                self.assert_equal(actual, expected)

            def test10(self) -> None:
                actual = "hello world"
                self.check_string(actual)


        # #############################################################################
        # TestOtherCases
        # #############################################################################


        class TestOtherCases(hunitest.TestCase):
            def test1(self) -> None:
                actual = "hello world"
                expected = actual
                self.assert_equal(actual, expected)

            def test10(self) -> None:
                actual = "hello world"
                self.check_string(actual)
        """
        content = hprint.dedent(content)
        return content

    def helper_rename_method(
        self, old_name: str, new_name: str, content: str
    ) -> str:
        """
        Test helper for method renaming.

        :param old_name: Original method name
        :param new_name: New method name
        :param content: Content to rename
        :return: Renamed content
        """
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer(old_name, new_name, root_dir)
        actual, _ = renamer._rename_method(content)
        return actual

    def test1(self) -> None:
        """
        Test renaming of existing method.
        """
        # Prepare inputs.
        content = self.helper()
        # Prepare outputs.
        expected = """
        class TestCases(hunitest.TestCase):
            def test_new(self) -> None:
                actual = "hello world"
                expected = actual
                self.assert_equal(actual, expected)

            def test10(self) -> None:
                actual = "hello world"
                self.check_string(actual)


        # #############################################################################
        # TestOtherCases
        # #############################################################################


        class TestOtherCases(hunitest.TestCase):
            def test1(self) -> None:
                actual = "hello world"
                expected = actual
                self.assert_equal(actual, expected)

            def test10(self) -> None:
                actual = "hello world"
                self.check_string(actual)
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_rename_method(
            "TestCases.test1", "TestCases.test_new", content
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test renaming of non existing method.
        """
        # Prepare inputs.
        content = self.helper()
        # Prepare outputs.
        expected = content
        # Run test.
        actual = self.helper_rename_method(
            "TestOtherCases.test5", "TestOtherCases.test6", content
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test renaming of invalid method names.
        """
        # Prepare inputs.
        root_dir = os.getcwd()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hunteuti.UnitTestRenamer(
                "TestCases.test10", "TestOtherCases.test6", root_dir
            )


# #############################################################################
# TestPytestRenameOutcomes
# #############################################################################


class TestPytestRenameOutcomes(hunitest.TestCase):
    """
    Test golden outcomes directory renaming.
    """

    @staticmethod
    def helper(toy_test: str) -> None:
        """
        Create the temporary outcome to rename.

        :param toy_test: the name of the toy directory
        """
        outcomes_paths = [
            "TestCase.test_check_string1",
            "TestCase.test_rename",
            "TestCase.test_rename3",
            "TestCases.test_rename2",
            "TestRename.test_rename1",
        ]
        for path in outcomes_paths:
            outcomes_dir = os.path.join(toy_test, "test/outcomes", path)
            hio.create_dir(outcomes_dir, incremental=False)
            hio.to_file(f"{outcomes_dir}/test.txt", "Test files.")
        cmd = f"git add {toy_test}/"
        hsystem.system(cmd, abort_on_error=False, suppress_output=False)

    def _clean_up(self, toy_test: str) -> None:
        """
        Remove temporary test directory.

        :param toy_test: the name of the toy directory
        """
        cmd = f"git reset {toy_test}/ && rm -rf {toy_test}/"
        hsystem.system(cmd, abort_on_error=False, suppress_output=False)

    def _get_sorted_outcome_dirs(self, test_path: str) -> list:
        """
        Return sorted list of subdirectories inside the outcomes directory.

        :param test_path: Base test directory path
        :return: Sorted list of outcome directory names
        """
        outcomes_path = os.path.join(test_path, "outcomes")
        outcomes_dirs = os.listdir(outcomes_path)
        return sorted(
            ent
            for ent in outcomes_dirs
            if os.path.isdir(os.path.join(outcomes_path, ent))
        )

    def test1(self) -> None:
        """
        Rename outcome directory.
        """
        # Prepare inputs.
        toy_test = "toyCmTask1279." + self._testMethodName
        test_path = os.path.join(toy_test, "test")
        self.helper(toy_test)
        root_dir = os.getcwd()
        # Prepare outputs.
        expected = [
            "TestCases.test_rename2",
            "TestRename.test_rename1",
            "TestRenamedCase.test_check_string1",
            "TestRenamedCase.test_rename",
            "TestRenamedCase.test_rename3",
        ]
        # Run test.
        renamer = hunteuti.UnitTestRenamer(
            "TestCase", "TestRenamedCase", root_dir
        )
        renamer.rename_outcomes(test_path)
        actual = self._get_sorted_outcome_dirs(test_path)
        # Check outputs.
        self.assertEqual(actual, expected)
        self._clean_up(toy_test)

    def test2(self) -> None:
        """
        Rename outcome directory.
        """
        # Prepare inputs.
        toy_test = "toyCmTask1279." + self._testMethodName
        test_path = os.path.join(toy_test, "test")
        self.helper(toy_test)
        root_dir = os.getcwd()
        # Prepare outputs.
        expected = [
            "TestCase.test_check_string1",
            "TestCase.test_method_renamed",
            "TestCase.test_rename3",
            "TestCases.test_rename2",
            "TestRename.test_rename1",
        ]
        # Run test.
        renamer = hunteuti.UnitTestRenamer(
            "TestCase.test_rename",
            "TestCase.test_method_renamed",
            root_dir,
        )
        renamer.rename_outcomes(test_path)
        actual = self._get_sorted_outcome_dirs(test_path)
        # Check outputs.
        self.assertEqual(actual, expected)
        self._clean_up(toy_test)


# #############################################################################
# Test_get_test_file_for_source
# #############################################################################


class Test_get_test_file_for_source(hunitest.TestCase):
    """
    Test mapping source files to test files.
    """

    def helper(self, file_path: str, expected: Optional[str]) -> None:
        """
        Test helper for get_test_file_for_source.

        :param file_path: Source file path to check
        :param expected: Expected test file path
        """
        # Run test.
        actual = hunteuti.get_test_file_for_source(file_path)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Source file with existing test file returns the test path.
        """
        # Prepare inputs.
        file_path = "helpers/hdbg.py"
        # Prepare outputs.
        expected = "helpers/test/test_hdbg.py"
        # Run test.
        self.helper(file_path, expected)

    def test2(self) -> None:
        """
        Source file without test file returns None.
        """
        # Prepare inputs.
        file_path = "tasks.py"
        # Prepare outputs.
        expected = None
        # Run test.
        self.helper(file_path, expected)

    def test3(self) -> None:
        """
        Test file as input returns None.
        """
        # Prepare inputs.
        file_path = "helpers/test/test_hdbg.py"
        # Prepare outputs.
        expected = None
        # Run test.
        self.helper(file_path, expected)


# #############################################################################
# Test_is_test_file
# #############################################################################


class Test_is_test_file(hunitest.TestCase):
    """
    Test test file detection.
    """

    def helper(self, file_path: str, expected: bool) -> None:
        """
        Test helper for is_test_file.

        :param file_path: File path to check
        :param expected: Whether it should be detected as test file
        """
        # Run test.
        actual = hunteuti.is_test_file(file_path)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Path containing /test/ is detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/test/test_hdbg.py"
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(file_path, expected)

    def test2(self) -> None:
        """
        Basename starting with test_ is detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/test_hdbg.py"
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(file_path, expected)

    def test3(self) -> None:
        """
        Basename ending with _test.py is detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/hdbg_test.py"
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(file_path, expected)

    def test4(self) -> None:
        """
        Source file path is not detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/hdbg.py"
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(file_path, expected)

    def test5(self) -> None:
        """
        Path with /test/ anywhere is detected as test file.
        """
        # Prepare inputs.
        file_path = "dev_scripts_helpers/scraping/test/__init__.py"
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(file_path, expected)


# #############################################################################
# Test_get_test_files_for_sources
# #############################################################################


class Test_get_test_files_for_sources(hunitest.TestCase):
    """
    Test mapping lists of source files to test files.
    """

    def helper(self, files: list, expected: list, *, sort_result: bool = False) -> None:
        """
        Test helper for get_test_files_for_sources.

        :param files: Input file list
        :param expected: Expected test file list
        :param sort_result: Whether to sort before comparing
        """
        # Run test.
        actual = hunteuti.get_test_files_for_sources(files)
        # Check outputs.
        if sort_result:
            self.assertEqual(sorted(actual), sorted(expected))
        else:
            self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Mixed source and test files returns only matched test files.
        """
        # Prepare inputs.
        files = [
            "helpers/hdbg.py",
            "helpers/test/test_hdbg.py",
            "helpers/hio.py",
        ]
        # Prepare outputs.
        expected = [
            "helpers/test/test_hdbg.py",
            "helpers/test/test_hio.py",
        ]
        # Run test.
        self.helper(files, expected, sort_result=True)

    def test2(self) -> None:
        """
        Only test files as input returns empty list.
        """
        # Prepare inputs.
        files = [
            "helpers/test/test_hdbg.py",
            "helpers/test/test_hio.py",
        ]
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(files, expected)

    def test3(self) -> None:
        """
        Source files with existing tests return matching test files.
        """
        # Prepare inputs.
        files = [
            "helpers/hdbg.py",
            "helpers/hio.py",
        ]
        # Prepare outputs.
        expected = [
            "helpers/test/test_hdbg.py",
            "helpers/test/test_hio.py",
        ]
        # Run test.
        self.helper(files, expected, sort_result=True)

    def test4(self) -> None:
        """
        Source file without test file is skipped.
        """
        # Prepare inputs.
        files = ["tasks.py"]
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(files, expected)

    def test5(self) -> None:
        """
        Empty input returns empty list.
        """
        # Prepare inputs.
        files = []
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(files, expected)


# #############################################################################
# Test_get_parent_dirs
# #############################################################################


class Test_get_parent_dirs(hunitest.TestCase):
    """
    Test extracting minimal parent directories from file list.
    """

    def helper(self, files: list, expected: list, sort_result: bool = False) -> None:
        """
        Test helper for get_parent_dirs.

        :param files: Input file list
        :param expected: Expected parent directory list
        :param sort_result: Whether to sort before comparing
        """
        # Run test.
        actual = hunteuti.get_parent_dirs(files)
        # Check outputs.
        if sort_result:
            self.assertEqual(sorted(actual), sorted(expected))
        else:
            self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Single file returns its parent directory.
        """
        # Prepare inputs.
        files = ["helpers/hdbg.py"]
        # Prepare outputs.
        expected = ["helpers"]
        # Run test.
        self.helper(files, expected)

    def test2(self) -> None:
        """
        Multiple files in same directory return that directory once.
        """
        # Prepare inputs.
        files = [
            "helpers/hdbg.py",
            "helpers/hio.py",
        ]
        # Prepare outputs.
        expected = ["helpers"]
        # Run test.
        self.helper(files, expected)

    def test3(self) -> None:
        """
        Files in different directories return all distinct dirs.
        """
        # Prepare inputs.
        files = [
            "dev_scripts_helpers/scraping/process_hn_article.py",
            "helpers/hgit.py",
            "helpers/lib_tasks_utils.py",
        ]
        # Prepare outputs.
        expected = [
            "dev_scripts_helpers/scraping",
            "helpers",
        ]
        # Run test.
        self.helper(files, expected, sort_result=True)

    def test4(self) -> None:
        """
        Nested directories are deduplicated to keep only parent.
        """
        # Prepare inputs.
        files = [
            "dev_scripts_helpers/scraping/process_hn_article.py",
            "dev_scripts_helpers/scraping/test/__init__.py",
            "helpers/hgit.py",
            "helpers/lib_tasks_utils.py",
        ]
        # Prepare outputs.
        expected = [
            "dev_scripts_helpers/scraping",
            "helpers",
        ]
        # Run test.
        self.helper(files, expected, sort_result=True)

    def test5(self) -> None:
        """
        Empty file list returns empty directory list.
        """
        # Prepare inputs.
        files = []
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(files, expected)

    def test6(self) -> None:
        """
        Files at root level are handled correctly.
        """
        # Prepare inputs.
        files = [
            "tasks.py",
            "pyproject.toml",
        ]
        # Prepare outputs.
        expected = ["."]
        # Run test.
        self.helper(files, expected)


# #############################################################################
# Test_capture_system_calls
# #############################################################################


class Test_capture_system_calls(hunitest.TestCase):
    """
    Test system call capture functionality.
    """

    def test1(self) -> None:
        """
        Capture single subprocess.run() call.
        """
        # Prepare outputs.
        expected = """
        [{'args': (['echo', 'hello'],),
          'function': 'subprocess.run',
          'kwargs': {'check': False}}]
        """
        expected = hprint.dedent(expected)
        # Run test.
        with hunteuti.capture_system_calls() as invocations:
            subprocess.run(["echo", "hello"], check=False)
        actual = pprint.pformat(invocations)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Capture hsystem.system() call.
        """
        # Prepare outputs.
        expected = """
        [{'args': ('echo hello',),
          'function': 'hsystem.system',
          'kwargs': {'suppress_output': True}}]
        """
        expected = hprint.dedent(expected)
        # Run test.
        with hunteuti.capture_system_calls() as invocations:
            hsystem.system("echo hello", suppress_output=True)
        actual = pprint.pformat(invocations)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Capture hsystem.system_to_string() call.
        """
        # Prepare outputs.
        expected = """
        [{'args': ('echo test',),
          'function': 'hsystem.system_to_string',
          'kwargs': {'suppress_output': True}}]
        """
        expected = hprint.dedent(expected)
        # Run test.
        with hunteuti.capture_system_calls() as invocations:
            hsystem.system_to_string("echo test", suppress_output=True)
        actual = pprint.pformat(invocations)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Capture multiple system calls.
        """
        # Prepare outputs.
        expected = """
        [{'args': ('echo hello',),
          'function': 'hsystem.system',
          'kwargs': {'suppress_output': True}},
         {'args': ('echo world',),
          'function': 'hsystem.system_to_string',
          'kwargs': {'suppress_output': True}}]
        """
        expected = hprint.dedent(expected)
        # Run test.
        with hunteuti.capture_system_calls() as invocations:
            hsystem.system("echo hello", suppress_output=True)
            hsystem.system_to_string("echo world", suppress_output=True)
        actual = pprint.pformat(invocations)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Capture with side_effect exception.
        """
        # Prepare outputs.
        expected_exception = RuntimeError
        # Run test and check output.
        with self.assertRaises(expected_exception):
            with hunteuti.capture_system_calls(
                side_effect=RuntimeError("Test error")
            ):
                hsystem.system("echo test", suppress_output=True)

    def test6(self) -> None:
        """
        Compare captured invocations with expected string representation.
        """
        # Prepare outputs.
        expected_invocations_str = (
            "[{'args': ('echo test',),\n"
            "  'function': 'hsystem.system',\n"
            "  'kwargs': {'suppress_output': True}}]"
        )
        # Run test.
        with hunteuti.capture_system_calls() as invocations:
            hsystem.system("echo test", suppress_output=True)
        # Check outputs.
        hunteuti.assert_invocations(
            self, invocations, expected_invocations_str
        )

    def test7(self) -> None:
        """
        Assert invocations with multiple calls.
        """
        # Prepare outputs.
        expected_invocations_str = (
            "[{'args': ('echo hello',),\n"
            "  'function': 'hsystem.system',\n"
            "  'kwargs': {'suppress_output': True}},\n"
            " {'args': ('echo world',),\n"
            "  'function': 'hsystem.system',\n"
            "  'kwargs': {'suppress_output': True}}]"
        )
        # Run test.
        with hunteuti.capture_system_calls() as invocations:
            hsystem.system("echo hello", suppress_output=True)
            hsystem.system("echo world", suppress_output=True)
        # Check outputs.
        hunteuti.assert_invocations(self, invocations, expected_invocations_str)

    def test8(self) -> None:
        """
        Assert empty invocations list.
        """
        # Prepare outputs.
        expected_num_invocations = 0
        # Run test.
        with hunteuti.capture_system_calls() as invocations:
            pass
        # Check outputs.
        self.assertEqual(len(invocations), expected_num_invocations)
