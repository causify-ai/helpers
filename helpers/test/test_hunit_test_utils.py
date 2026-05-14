import os

import helpers.hio as hio
import helpers.hprint as hprint
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

    def test1(self) -> None:
        """
        Test renaming of existing class.
        """
        # Prepare inputs.
        content = self.helper()
        root_dir = os.getcwd()
        # Run test.
        renamer = hunteuti.UnitTestRenamer("TestCases", "TestNewCase", root_dir)
        actual, _ = renamer._rename_class(content)
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
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test renaming of non existing class.
        """
        # Prepare inputs.
        content = self.helper()
        root_dir = os.getcwd()
        # Run test.
        renamer = hunteuti.UnitTestRenamer("TestCase", "TestNewCase", root_dir)
        actual, _ = renamer._rename_class(content)
        # Check outputs.
        self.assert_equal(actual, content)


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

    def test1(self) -> None:
        """
        Test renaming of existing method.
        """
        # Prepare inputs.
        content = self.helper()
        root_dir = os.getcwd()
        # Run test.
        renamer = hunteuti.UnitTestRenamer(
            "TestCases.test1", "TestCases.test_new", root_dir
        )
        actual, _ = renamer._rename_method(content)
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
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test renaming of non existing method.
        """
        # Prepare inputs.
        content = self.helper()
        root_dir = os.getcwd()
        # Run test.
        renamer = hunteuti.UnitTestRenamer(
            "TestOtherCases.test5", "TestOtherCases.test6", root_dir
        )
        actual, _ = renamer._rename_method(content)
        # Check outputs.
        self.assert_equal(actual, content)

    def test3(self) -> None:
        """
        Test renaming of invalid method names.
        """
        # Prepare inputs.
        root_dir = os.getcwd()
        self.helper()
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

    def test1(self) -> None:
        """
        Rename outcome directory.
        """
        # Prepare inputs.
        toy_test = "toyCmTask1279." + self._testMethodName
        test_path = os.path.join(toy_test, "test")
        self.helper(toy_test)
        root_dir = os.getcwd()
        # Run test.
        renamer = hunteuti.UnitTestRenamer(
            "TestCase", "TestRenamedCase", root_dir
        )
        renamer.rename_outcomes(test_path)
        # Prepare outputs.
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
        # Run test.
        renamer = hunteuti.UnitTestRenamer(
            "TestCase.test_rename",
            "TestCase.test_method_renamed",
            root_dir,
        )
        renamer.rename_outcomes(test_path)
        # Prepare outputs.
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

    def test1(self) -> None:
        """
        Source file with existing test file returns the test path.
        """
        # Prepare inputs.
        file_path = "helpers/hdbg.py"
        # Prepare outputs.
        expected = "helpers/test/test_hdbg.py"
        # Run test.
        actual = hunteuti.get_test_file_for_source(file_path)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Source file without test file returns None.
        """
        # Prepare inputs.
        file_path = "tasks.py"
        # Run test.
        actual = hunteuti.get_test_file_for_source(file_path)
        # Check outputs.
        self.assertIsNone(actual)

    def test3(self) -> None:
        """
        Test file as input returns None.
        """
        # Prepare inputs.
        file_path = "helpers/test/test_hdbg.py"
        # Run test.
        actual = hunteuti.get_test_file_for_source(file_path)
        # Check outputs.
        self.assertIsNone(actual)


# #############################################################################
# TestIsTestFile
# #############################################################################


class TestIsTestFile(hunitest.TestCase):
    """
    Test test file detection.
    """

    def test1(self) -> None:
        """
        Path containing /test/ is detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/test/test_hdbg.py"
        # Run test.
        actual = hunteuti.is_test_file(file_path)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Basename starting with test_ is detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/test_hdbg.py"
        # Run test.
        actual = hunteuti.is_test_file(file_path)
        # Check outputs.
        self.assertTrue(actual)

    def test3(self) -> None:
        """
        Basename ending with _test.py is detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/hdbg_test.py"
        # Run test.
        actual = hunteuti.is_test_file(file_path)
        # Check outputs.
        self.assertTrue(actual)

    def test4(self) -> None:
        """
        Source file path is not detected as test file.
        """
        # Prepare inputs.
        file_path = "helpers/hdbg.py"
        # Run test.
        actual = hunteuti.is_test_file(file_path)
        # Check outputs.
        self.assertFalse(actual)

    def test5(self) -> None:
        """
        Path with /test/ anywhere is detected as test file.
        """
        # Prepare inputs.
        file_path = "dev_scripts_helpers/scraping/test/__init__.py"
        # Run test.
        actual = hunteuti.is_test_file(file_path)
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# TestGetTestFilesForSources
# #############################################################################


class TestGetTestFilesForSources(hunitest.TestCase):
    """
    Test mapping lists of source files to test files.
    """

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
        actual = hunteuti.get_test_files_for_sources(files)
        # Check outputs.
        self.assertEqual(sorted(actual), sorted(expected))

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
        actual = hunteuti.get_test_files_for_sources(files)
        # Check outputs.
        self.assertEqual(actual, expected)

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
        actual = hunteuti.get_test_files_for_sources(files)
        # Check outputs.
        self.assertEqual(sorted(actual), sorted(expected))

    def test4(self) -> None:
        """
        Source file without test file is skipped.
        """
        # Prepare inputs.
        files = ["tasks.py"]
        # Prepare outputs.
        expected = []
        # Run test.
        actual = hunteuti.get_test_files_for_sources(files)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Empty input returns empty list.
        """
        # Prepare inputs.
        files = []
        # Prepare outputs.
        expected = []
        # Run test.
        actual = hunteuti.get_test_files_for_sources(files)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# TestGetParentDirs
# #############################################################################


class TestGetParentDirs(hunitest.TestCase):
    """
    Test extracting minimal parent directories from file list.
    """

    def test1(self) -> None:
        """
        Single file returns its parent directory.
        """
        # Prepare inputs.
        files = ["helpers/hdbg.py"]
        # Prepare outputs.
        expected = ["helpers"]
        # Run test.
        actual = hunteuti.get_parent_dirs(files)
        # Check outputs.
        self.assertEqual(actual, expected)

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
        actual = hunteuti.get_parent_dirs(files)
        # Check outputs.
        self.assertEqual(actual, expected)

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
        actual = hunteuti.get_parent_dirs(files)
        # Check outputs.
        self.assertEqual(sorted(actual), sorted(expected))

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
        actual = hunteuti.get_parent_dirs(files)
        # Check outputs.
        self.assertEqual(sorted(actual), sorted(expected))

    def test5(self) -> None:
        """
        Empty file list returns empty directory list.
        """
        # Prepare inputs.
        files = []
        # Prepare outputs.
        expected = []
        # Run test.
        actual = hunteuti.get_parent_dirs(files)
        # Check outputs.
        self.assertEqual(actual, expected)

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
        actual = hunteuti.get_parent_dirs(files)
        # Check outputs.
        self.assertEqual(actual, expected)
