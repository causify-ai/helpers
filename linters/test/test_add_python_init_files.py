import logging
from typing import Dict, List

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.add_python_init_files as lapyinfi

_LOG = logging.getLogger(__name__)


class Test_add_python_init_files(hunitest.TestCase):
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
        file_path: str,
        expected: List[str],
    ) -> None:
        """
        Create the inputs, run the pipeline and check the results.

        :param files: input files to create
        :param dirs: dirs to create
        :param file_name: the name of the file to check
        :param expected: names of the dirs with missing inits
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
        # Check the outcome.
        exclude_unimported_dirs = False
        actual = lapyinfi._get_dirs_to_add_init(
            file_path,
            exclude_unimported_dirs=exclude_unimported_dirs,
        )
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test checking that no `__init__.py` files are missing.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir()
        dirs: List[str] = []
        files = {}
        files["file1.py"] = ""
        files["file2.py"] = ""
        files["__init__.py"] = ""
        # Run and check the outcome.
        file_path = f"{in_dir_name}/file1.py"
        expected: List[str] = []
        self.helper(files, dirs, file_path, expected)

    def test2(self) -> None:
        """
        Test checking the missing `__init__.py` files.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir()
        dirs: List[str] = []
        files = {}
        files["file1.py"] = ""
        files["file2.py"] = ""
        # Run and check the outcome.
        file_path = f"{in_dir_name}/file1.py"
        expected = [in_dir_name]
        self.helper(files, dirs, file_path, expected)

    def test3(self) -> None:
        """
        Test checking that no `__init__.py` files are missing: with subdirs.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir()
        dirs = ["subdir1", "subdir2"]
        files = {}
        for dir_ in dirs:
            files[f"{dir_}/__init__.py"] = ""
        files["subdir1/file1.py"] = ""
        files["subdir2/file1.py"] = ""
        files["__init__.py"] = ""
        # Run and check the outcome.
        file_path = f"{in_dir_name}/subdir2/file1.py"
        expected: List[str] = []
        self.helper(files, dirs, file_path, expected)

    def test4(self) -> None:
        """
        Test checking the missing `__init__.py` files: with subdirs.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir()
        dirs = ["subdir1", "subdir2"]
        files = {}
        files["subdir1/file1.py"] = ""
        files["subdir2/file1.py"] = ""
        files["__init__.py"] = ""
        files["subdir1/__init__.py"] = ""
        # Run and check the outcome.
        file_path = f"{in_dir_name}/subdir2/file1.py"
        expected = [f"{in_dir_name}/subdir2"]
        self.helper(files, dirs, file_path, expected)
