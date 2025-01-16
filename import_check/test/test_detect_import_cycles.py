import logging
from typing import Dict, List, Union

import helpers.hio as hio
import helpers.hunit_test as hunitest
import import_check.detect_import_cycles as icdeimcy
import import_check.show_imports as ichshimp

_LOG = logging.getLogger(__name__)


class Test_detect_import_cycles(hunitest.TestCase):
    def create_io_dirs(self) -> None:
        dir_name = self.get_input_dir()
        hio.create_dir(dir_name, incremental=True)
        _LOG.debug("Creating dir_name=%s", dir_name)
        #
        dir_name = self.get_output_dir()
        hio.create_dir(dir_name, incremental=True)
        _LOG.debug("Creating dir_name=%s", dir_name)

    def helper(
        self,
        files: Dict[str, str],
        dirs: List[str],
        expected: Union[List[List[str]], str],
    ) -> None:
        """
        Create the inputs, run the pipeline and check the results.

        :param files: input files to create
        :param dirs: dirs to create
        :param expected: expected outcome
            - names of the dirs with import cycles, or
            - an error message if the test is expected to assert
        """
        # Create a module for testing.
        self.create_io_dirs()
        in_dir = self.get_input_dir()
        for dir_ in dirs:
            # Create the subdirectories.
            if dir_ != ".":
                hio.create_dir(f"{in_dir}/{dir_}", False)
        # Create the files.
        for file_name, file_content in files.items():
            hio.to_file(f"{in_dir}/{file_name}", file_content)
        #
        module_path = in_dir
        exclude_unimported_dirs = False
        if isinstance(expected, list):
            # Detect the cycles.
            actual = icdeimcy._check_import_cycles(
                module_path, exclude_unimported_dirs=exclude_unimported_dirs
            )
            # Check the outcome.
            self.assertEqual(actual, expected)
        else:
            # Confirm that the test asserts.
            with self.assertRaises(ichshimp.NotModuleError) as e:
                icdeimcy._check_import_cycles(
                    module_path, exclude_unimported_dirs=exclude_unimported_dirs
                )
            self.assert_equal(str(e.exception), expected, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test detecting import cycles.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs: List[str] = []
        files = {}
        files["file1.py"] = f"import {in_dir_name}.file2\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [["input.file1", "input.file2"]]
        self.helper(files, dirs, expected)

    def test2(self) -> None:
        """
        Test detecting import cycles: no cycles.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs: List[str] = []
        files = {}
        files["file1.py"] = "\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected: List[List[str]] = []
        self.helper(files, dirs, expected)

    def test3(self) -> None:
        """
        Test detecting import cycles: more than 2 files in a cycle.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs: List[str] = []
        files = {}
        files["file1.py"] = f"import {in_dir_name}.file2\n"
        files["file2.py"] = f"import {in_dir_name}.file3\n"
        files["file3.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [["input.file1", "input.file2", "input.file3"]]
        self.helper(files, dirs, expected)

    def test4(self) -> None:
        """
        Test detecting import cycles: multiple separate cycles.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs: List[str] = []
        files = {}
        files["file1.py"] = f"import {in_dir_name}.file2\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["file3.py"] = f"import {in_dir_name}.file4\n"
        files["file4.py"] = f"import {in_dir_name}.file3\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [
            ["input.file1", "input.file2"],
            ["input.file3", "input.file4"],
        ]
        self.helper(files, dirs, expected)

    def test5(self) -> None:
        """
        Test detecting cross-directory import cycles.

        The cycle is between the files that are located in different
        directories (on one level).
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1", "subdir2"]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/__init__.py"] = ""
        files["subdir1/file1.py"] = f"import {in_dir_name}.subdir2.file1\n"
        files["subdir2/file1.py"] = f"import {in_dir_name}.subdir1.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [
            ["input.subdir1.file1", "input.subdir2.file1"],
        ]
        self.helper(files, dirs, expected)

    def test6(self) -> None:
        """
        Test detecting cross-directory import cycles.

        The cycle is between the files that are located in different
        directories (on different levels).
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1", "subdir2", "subdir2/subdir3"]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/__init__.py"] = ""
        files[
            "subdir1/file1.py"
        ] = f"import {in_dir_name}.subdir2.subdir3.file1\n"
        files[
            "subdir2/subdir3/file1.py"
        ] = f"import {in_dir_name}.subdir1.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [
            ["input.subdir1.file1", "input.subdir2.subdir3.file1"],
        ]
        self.helper(files, dirs, expected)

    def test7(self) -> None:
        """
        Test detecting cross-directory import cycles.

        The cycle is between the files that are located in different
        directories (on different levels, more depth).
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = [
            "subdir1",
            "subdir1/subdir2",
            "subdir1/subdir2/subdir3",
            "subdir4",
            "subdir4/subdir5",
        ]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/__init__.py"] = ""
        files[
            "subdir1/subdir2/subdir3/file1.py"
        ] = f"import {in_dir_name}.subdir4.subdir5.file1\n"
        files[
            "subdir4/subdir5/file1.py"
        ] = f"import {in_dir_name}.subdir1.subdir2.subdir3.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [
            [
                "input.subdir1.subdir2.subdir3.file1",
                "input.subdir4.subdir5.file1",
            ],
        ]
        self.helper(files, dirs, expected)

    def test8(self) -> None:
        """
        Test detecting import cycles in parent-child dirs.

        The cycle is between the files that are located in different
        directories, where one is the parent of the other.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1"]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/__init__.py"] = ""
        files["file1.py"] = f"import {in_dir_name}.subdir1.file1\n"
        files["subdir1/file1.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [
            ["input.file1", "input.subdir1.file1"],
        ]
        self.helper(files, dirs, expected)

    def test9(self) -> None:
        """
        Test detecting import cycles: cycles in subdirs.

        Conditons:
            - Root input dir is a module
            - Files with import cycles are in subdirs
            - The subdirs with the files are not modules
        Expected outcome:
            - An error is raised
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1", "subdir2"]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/file1.py"] = f"import {in_dir_name}.{dir_}.file2\n"
            files[f"{dir_}/file2.py"] = f"import {in_dir_name}.{dir_}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = (
            "The following dirs have to be modules (add `__init__.py`): "
            "['/app/import_check/test/outcomes/Test_detect_import_cycles.test9/input/subdir1', "
            "'/app/import_check/test/outcomes/Test_detect_import_cycles.test9/input/subdir2']"
        )
        self.helper(files, dirs, expected)

    def test10(self) -> None:
        """
        Test detecting import cycles: cycles in subdirs.

        Conditons:
            - Root input dir is a module
            - Files with import cycles are in subdirs
            - The subdirs with the files are modules
            - There are no intermediate non-module subdirs
              between the root input dir and the subdirs with files
        Expected outcome:
            - The import cycles are detected
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1", "subdir2"]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/file1.py"] = f"import {in_dir_name}.{dir_}.file2\n"
            files[f"{dir_}/file2.py"] = f"import {in_dir_name}.{dir_}.file1\n"
            files[f"{dir_}/__init__.py"] = ""
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = [
            ["input.subdir1.file1", "input.subdir1.file2"],
            ["input.subdir2.file1", "input.subdir2.file2"],
        ]
        self.helper(files, dirs, expected)

    def test11(self) -> None:
        """
        Test detecting import cycles: cycles in subdirs.

        Conditons:
            - Root input dir is a module
            - Files with import cycles are in subdirs
            - The subdirs with the files are modules
            - There is an intermediate non-module subdir
              between the root input dir and the subdirs with files
        Expected outcome:
            - An error is raised
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1", "subdir1/subdir2"]
        files = {}
        files[
            "subdir1/subdir2/file1.py"
        ] = f"import {in_dir_name}.subdir1.subdir2.file2\n"
        files[
            "subdir1/subdir2/file2.py"
        ] = f"import {in_dir_name}.subdir1.subdir2.file1\n"
        files["subdir1/subdir2/__init__.py"] = ""
        files["__init__.py"] = ""
        # Run and check the outcome.
        expected = (
            "The following dirs have to be modules (add `__init__.py`): "
            "['/app/import_check/test/outcomes/Test_detect_import_cycles.test11/input/subdir1']"
        )
        self.helper(files, dirs, expected)

    def test12(self) -> None:
        """
        Test detecting import cycles: cycles in subdirs.

        Conditons:
            - Root input dir is not a module
            - Files with import cycles are in subdirs
            - The subdirs with the files are modules
            - There are no intermediate non-module subdirs
              between the root input dir and the subdirs with files
        Expected outcome:
            - An error is raised
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1", "subdir2"]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/file1.py"] = f"import {in_dir_name}.{dir_}.file2\n"
            files[f"{dir_}/file2.py"] = f"import {in_dir_name}.{dir_}.file1\n"
            files[f"{dir_}/__init__.py"] = ""
        # Run and check the outcome.
        expected = (
            "The following dirs have to be modules (add `__init__.py`): "
            "['/app/import_check/test/outcomes/Test_detect_import_cycles.test12/input']"
        )
        self.helper(files, dirs, expected)

    def test13(self) -> None:
        """
        Test detecting import cycles: cycles in subdirs.

        Conditons:
            - Root input dir is not a module
            - Files with import cycles are in subdirs
            - The subdirs with the files are modules
            - There is an intermediate non-module subdir
              between the root input dir and the subdirs with files
        Expected outcome:
            - An error is raised
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        dirs = ["subdir1", "subdir1/subdir2"]
        files = {}
        files[
            "subdir1/subdir2/file1.py"
        ] = f"import {in_dir_name}.subdir1.subdir2.file2\n"
        files[
            "subdir1/subdir2/file2.py"
        ] = f"import {in_dir_name}.subdir1.subdir2.file1\n"
        files["subdir1/subdir2/__init__.py"] = ""
        # Run and check the outcome.
        expected = (
            "The following dirs have to be modules (add `__init__.py`): "
            "['/app/import_check/test/outcomes/Test_detect_import_cycles.test13/input', "
            "'/app/import_check/test/outcomes/Test_detect_import_cycles.test13/input/subdir1']"
        )
        self.helper(files, dirs, expected)
