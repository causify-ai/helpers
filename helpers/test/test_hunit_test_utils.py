import os

import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti


# #############################################################################
# TestUnitTestRenamer
# #############################################################################


class TestUnitTestRenamer(hunitest.TestCase):
    """
    Test class renaming functionality.
    """


# #############################################################################
# TestCases
# #############################################################################


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
        return content


# #############################################################################
# TestNewCase
# #############################################################################


    def test_rename_class1(self) -> None:
        """
        Test renaming of existing class.
        """
        content = self.helper()
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer("TestCases", "TestNewCase", root_dir)
        actual, _ = renamer._rename_class(content)
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
        self.assert_equal(actual, expected)

    def test_rename_class2(self) -> None:
        """
        Test renaming of non existing class.
        """
        content = self.helper()
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer("TestCase", "TestNewCase", root_dir)
        actual, _ = renamer._rename_class(content)
        # Check if the content of the file was not changed.
        self.assert_equal(actual, content)


# #############################################################################
# TestPytestRenameMethod
# #############################################################################


class TestPytestRenameMethod(hunitest.TestCase):
    """
    Test method renaming functionality.
    """


# #############################################################################
# TestCases
# #############################################################################


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
        return content


# #############################################################################
# TestCases
# #############################################################################


    def test_rename_method1(self) -> None:
        """
        Test renaming of existing method.
        """
        content = self.helper()
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer(
            "TestCases.test1", "TestCases.test_new", root_dir
        )
        actual, _ = renamer._rename_method(content)
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
        self.assert_equal(actual, expected)

    def test_rename_method2(self) -> None:
        """
        Test renaming of non existing method.
        """
        content = self.helper()
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer(
            "TestOtherCases.test5", "TestOtherCases.test6", root_dir
        )
        actual, _ = renamer._rename_method(content)
        # Check if the content of the file was not changed.
        self.assert_equal(actual, content)

    def test_rename_method3(self) -> None:
        """
        Test renaming of invalid method names.
        """
        self.helper()
        root_dir = os.getcwd()
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

    def test_rename_class_outcomes(self) -> None:
        """
        Rename outcome directory.
        """
        toy_test = "toyCmTask1279." + self._testMethodName
        # Create outcomes directory.
        test_path = os.path.join(toy_test, "test")
        # Create the toy outcomes.
        self.helper(toy_test)
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer(
            "TestCase", "TestRenamedCase", root_dir
        )
        renamer.rename_outcomes(
            test_path,
        )
        # Check if the dirs were renamed.
        outcomes_path = os.path.join(test_path, "outcomes")
        outcomes_dirs = os.listdir(outcomes_path)
        actual = sorted(
            [
                ent
                for ent in outcomes_dirs
                if os.path.isdir(os.path.join(outcomes_path, ent))
            ]
        )
        expected = [
            "TestCases.test_rename2",
            "TestRename.test_rename1",
            "TestRenamedCase.test_check_string1",
            "TestRenamedCase.test_rename",
            "TestRenamedCase.test_rename3",
        ]
        self.assertEqual(actual, expected)
        self._clean_up(toy_test)

    def test_rename_method_outcomes(self) -> None:
        """
        Rename outcome directory.
        """
        toy_test = "toyCmTask1279." + self._testMethodName
        # Create outcomes directory.
        test_path = os.path.join(toy_test, "test")
        # Create the toy outcomes.
        self.helper(toy_test)
        root_dir = os.getcwd()
        renamer = hunteuti.UnitTestRenamer(
            "TestCase.test_rename",
            "TestCase.test_method_renamed",
            root_dir,
        )
        renamer.rename_outcomes(
            test_path,
        )
        # Check if the dirs were renamed.
        outcomes_path = os.path.join(test_path, "outcomes")
        outcomes_dirs = os.listdir(outcomes_path)
        actual = sorted(
            [
                ent
                for ent in outcomes_dirs
                if os.path.isdir(os.path.join(outcomes_path, ent))
            ]
        )
        expected = [
            "TestCase.test_check_string1",
            "TestCase.test_method_renamed",
            "TestCase.test_rename3",
            "TestCases.test_rename2",
            "TestRename.test_rename1",
        ]
        self.assertEqual(actual, expected)
        self._clean_up(toy_test)


# #############################################################################
# Test_get_test_file_for_source
# #############################################################################


class Test_get_test_file_for_source(hunitest.TestCase):
    """
    Test mapping source files to test files.
    """

    def test1(self) -> None:
        """
        Source file with existing test file returns the test path.
        """
        actual = hunteuti.get_test_file_for_source("helpers/hdbg.py")
        expected = "helpers/test/test_hdbg.py"
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Source file without test file returns None.
        """
        actual = hunteuti.get_test_file_for_source("tasks.py")
        self.assertIsNone(actual)

    def test3(self) -> None:
        """
        Test file as input returns None.
        """
        actual = hunteuti.get_test_file_for_source("helpers/test/test_hdbg.py")
        self.assertIsNone(actual)


# #############################################################################
# TestIsTestFile
# #############################################################################


class TestIsTestFile(hunitest.TestCase):
    """
    Test test file detection.
    """

    def test_path_with_test_dir(self) -> None:
        """
        Path containing /test/ is detected as test file.
        """
        actual = hunteuti.is_test_file("helpers/test/test_hdbg.py")
        self.assertTrue(actual)

    def test_path_with_test_prefix(self) -> None:
        """
        Basename starting with test_ is detected as test file.
        """
        actual = hunteuti.is_test_file("helpers/test_hdbg.py")
        self.assertTrue(actual)

    def test_path_with_test_suffix(self) -> None:
        """
        Basename ending with _test.py is detected as test file.
        """
        actual = hunteuti.is_test_file("helpers/hdbg_test.py")
        self.assertTrue(actual)

    def test_source_file(self) -> None:
        """
        Source file path is not detected as test file.
        """
        actual = hunteuti.is_test_file("helpers/hdbg.py")
        self.assertFalse(actual)

    def test_nested_path_with_test(self) -> None:
        """
        Path with /test/ anywhere is detected as test file.
        """
        actual = hunteuti.is_test_file(
            "dev_scripts_helpers/scraping/test/__init__.py"
        )
        self.assertTrue(actual)


# #############################################################################
# TestGetTestFilesForSources
# #############################################################################


class TestGetTestFilesForSources(hunitest.TestCase):
    """
    Test mapping lists of source files to test files.
    """

    def test_mixed_files(self) -> None:
        """
        Mixed source and test files returns only matched test files.
        """
        files = [
            "helpers/hdbg.py",
            "helpers/test/test_hdbg.py",
            "helpers/hio.py",
        ]
        actual = hunteuti.get_test_files_for_sources(files)
        expected = [
            "helpers/test/test_hdbg.py",
            "helpers/test/test_hio.py",
        ]
        self.assertEqual(sorted(actual), sorted(expected))

    def test_only_test_files(self) -> None:
        """
        Only test files as input returns empty list.
        """
        files = [
            "helpers/test/test_hdbg.py",
            "helpers/test/test_hio.py",
        ]
        actual = hunteuti.get_test_files_for_sources(files)
        expected = []
        self.assertEqual(actual, expected)

    def test_only_source_files_with_tests(self) -> None:
        """
        Source files with existing tests return matching test files.
        """
        files = [
            "helpers/hdbg.py",
            "helpers/hio.py",
        ]
        actual = hunteuti.get_test_files_for_sources(files)
        expected = [
            "helpers/test/test_hdbg.py",
            "helpers/test/test_hio.py",
        ]
        self.assertEqual(sorted(actual), sorted(expected))

    def test_source_without_test(self) -> None:
        """
        Source file without test file is skipped.
        """
        files = ["tasks.py"]
        actual = hunteuti.get_test_files_for_sources(files)
        expected = []
        self.assertEqual(actual, expected)

    def test_empty_list(self) -> None:
        """
        Empty input returns empty list.
        """
        files = []
        actual = hunteuti.get_test_files_for_sources(files)
        expected = []
        self.assertEqual(actual, expected)


# #############################################################################
# TestGetParentDirs
# #############################################################################


class TestGetParentDirs(hunitest.TestCase):
    """
    Test extracting minimal parent directories from file list.
    """

    def test_single_file(self) -> None:
        """
        Single file returns its parent directory.
        """
        files = ["helpers/hdbg.py"]
        actual = hunteuti.get_parent_dirs(files)
        expected = ["helpers"]
        self.assertEqual(actual, expected)

    def test_files_in_same_dir(self) -> None:
        """
        Multiple files in same directory return that directory once.
        """
        files = [
            "helpers/hdbg.py",
            "helpers/hio.py",
        ]
        actual = hunteuti.get_parent_dirs(files)
        expected = ["helpers"]
        self.assertEqual(actual, expected)

    def test_files_in_different_dirs(self) -> None:
        """
        Files in different directories return all distinct dirs.
        """
        files = [
            "dev_scripts_helpers/scraping/process_hn_article.py",
            "helpers/hgit.py",
            "helpers/lib_tasks_utils.py",
        ]
        actual = hunteuti.get_parent_dirs(files)
        expected = [
            "dev_scripts_helpers/scraping",
            "helpers",
        ]
        self.assertEqual(sorted(actual), sorted(expected))

    def test_nested_dirs_dedup(self) -> None:
        """
        Nested directories are deduplicated to keep only parent.
        """
        files = [
            "dev_scripts_helpers/scraping/process_hn_article.py",
            "dev_scripts_helpers/scraping/test/__init__.py",
            "helpers/hgit.py",
            "helpers/lib_tasks_utils.py",
        ]
        actual = hunteuti.get_parent_dirs(files)
        expected = [
            "dev_scripts_helpers/scraping",
            "helpers",
        ]
        self.assertEqual(sorted(actual), sorted(expected))

    def test_empty_list(self) -> None:
        """
        Empty file list returns empty directory list.
        """
        files = []
        actual = hunteuti.get_parent_dirs(files)
        expected = []
        self.assertEqual(actual, expected)

    def test_root_level_files(self) -> None:
        """
        Files at root level are handled correctly.
        """
        files = [
            "tasks.py",
            "pyproject.toml",
        ]
        actual = hunteuti.get_parent_dirs(files)
        expected = ["."]
        self.assertEqual(actual, expected)
