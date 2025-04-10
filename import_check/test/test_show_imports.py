import json
import logging
from typing import Dict, List, Optional

import pytest

import helpers.hio as hio
import helpers.hunit_test as hunitest
import import_check.show_imports as ichshimp

_LOG = logging.getLogger(__name__)


@pytest.mark.slow()
class Test_show_imports(hunitest.TestCase):
    def create_io_dirs(self) -> None:
        dir_name = self.get_input_dir()
        hio.create_dir(dir_name, incremental=True)
        _LOG.debug("Creating dir_name=%s", dir_name)
        #
        dir_name = self.get_output_dir()
        hio.create_dir(dir_name, incremental=True)
        _LOG.debug("Creating dir_name=%s", dir_name)

    def execute_script(
        self,
        files: Dict[str, str],
        *,
        dirs: Optional[List[str]] = None,
        dependency_level: int = 0,
        directory_dependencies: bool = False,
        external_dependencies: bool = True,
        show_cycles: bool = False,
        output_format: str = "pdf",
        save_graph_source: bool = True,
        check_graph_source: bool = True,
    ) -> None:
        """
        Execute the script to retrieve dependencies.

        See `_show_dependencies` in `show_imports.py` for the description of the script parameters.

        :param files: files in the target module
        :param dirs: subdirectories in the target dir
        :param check_graph_source: if True, check the source file of the graph,
            otherwise check the output file itself
        """
        # Create a module for testing.
        self.create_io_dirs()
        in_dir = self.get_input_dir()
        if dirs is not None:
            # Create the files in the subdirectories.
            for dir_ in dirs:
                if dir_ != ".":
                    hio.create_dir(f"{in_dir}/{dir_}", False)
                for file_name, file_content in files.items():
                    hio.to_file(f"{in_dir}/{dir_}/{file_name}", file_content)
        else:
            # Create the files directly in the target dir.
            for file_name, file_content in files.items():
                hio.to_file(f"{in_dir}/{file_name}", file_content)
        # Execute the script.
        out_dir = self.get_output_dir()
        output_filename = f"{out_dir}/output.{output_format}"
        module_path = in_dir
        exclude_unimported_dirs = False
        script_output_filename = ichshimp._show_dependencies(
            module_path,
            dependency_level,
            directory_dependencies,
            external_dependencies,
            show_cycles,
            output_format,
            output_filename,
            save_graph_source=save_graph_source,
            exclude_unimported_dirs=exclude_unimported_dirs,
        )
        # Check the outcome.
        if check_graph_source:
            script_output = hio.from_file(f"{out_dir}/output")
            self.check_string(script_output, purify_text=True)
        else:
            script_output = hio.from_file(script_output_filename)
            # Transform the output from the script by removing the dependencies
            # from the client.
            purified_script_output = hunitest.purify_txt_from_client(
                script_output
            )
            purified_script_output = purified_script_output.replace(
                "$GIT_ROOT", ""
            )
            # Check the structured output to prevent errors due to serialization.
            structured_actual = json.loads(purified_script_output)
            #
            expected_filename = f"{out_dir}/test.{output_format}"
            expected = hio.from_json(expected_filename)
            self.assertDictEqual(expected, structured_actual)

    def test1(self) -> None:
        """
        Test writing the dependencies of a single module into a text file.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        output_format = "txt"
        save_graph_source = False
        check_graph_source = False
        self.execute_script(
            files,
            output_format=output_format,
            save_graph_source=save_graph_source,
            check_graph_source=check_graph_source,
        )

    def test2(self) -> None:
        """
        Test plotting the dependencies in a graph.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        self.execute_script(files)

    def test3(self) -> None:
        """
        Test the case when there are no files in the module.
        """
        # Prepare the inputs.
        files = {}
        files["__init__.py"] = ""
        # Run and check the outcome.
        self.execute_script(files)

    def test4(self) -> None:
        """
        Test the case when there are external dependencies in the module.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "import numpy\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        self.execute_script(files)

    def test5(self) -> None:
        """
        Test the case when there are subdirectories in the module.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "import numpy\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        dirs = [".", "subdir1", "subdir2"]
        # Run and check the outcome.
        self.execute_script(files, dirs=dirs)

    def test6(self) -> None:
        """
        Test the case when there are cyclic dependencies in the module.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = f"import {in_dir_name}.file2\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        self.execute_script(files)

    def test7(self) -> None:
        """
        Test removing external dependencies.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "import numpy\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        external_dependencies = False
        self.execute_script(files, external_dependencies=external_dependencies)

    def test8(self) -> None:
        """
        Test setting a maximum dependency level.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "import numpy\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        dirs = [".", "subdir1", "subdir2"]
        # Run and check the outcome.
        dependency_level = 2
        self.execute_script(
            files,
            dirs=dirs,
            dependency_level=dependency_level,
        )

    def test9(self) -> None:
        """
        Test showing directory dependencies.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "import numpy\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        dirs = [".", "subdir1", "subdir2"]
        # Run and check the outcome.
        directory_dependencies = True
        self.execute_script(
            files,
            dirs=dirs,
            directory_dependencies=directory_dependencies,
        )

    def test10(self) -> None:
        """
        Test when the input dir is not a module and contains submodules.

        Expected outcome: an error is raised.
        """
        # Prepare the inputs.
        files = {}
        files["file1.py"] = "import numpy\n"
        files["file2.py"] = "import subdir1.file1\n"
        files["__init__.py"] = ""
        dirs = ["subdir1", "subdir2"]
        # Run and check the outcome.
        with self.assertRaises(ichshimp.NotModuleError) as e:
            self.execute_script(files, dirs=dirs)
        act = str(e.exception)
        exp = (
            "The following dirs have to be modules (add `__init__.py`): "
            "['/app/import_check/test/outcomes/Test_show_imports.test10/input']"
        )
        self.assert_equal(act, exp, fuzzy_match=True)

    def test11(self) -> None:
        """
        Test showing only cyclic imports.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "import numpy\n"
        files[
            "file2.py"
        ] = f"import {in_dir_name}.file1\nimport {in_dir_name}.file3\n"
        files["file3.py"] = f"import {in_dir_name}.file2\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        show_cycles = True
        self.execute_script(
            files,
            show_cycles=show_cycles,
        )

    def test12(self) -> None:
        """
        Test showing only cyclic imports: no cyclic imports in the files.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = "import numpy\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["file3.py"] = f"import {in_dir_name}.file2\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        show_cycles = True
        self.execute_script(
            files,
            show_cycles=show_cycles,
        )

    def test13(self) -> None:
        """
        Test showing only cyclic imports: cyclic imports with > 2 files.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = f"import {in_dir_name}.file2\n"
        files["file2.py"] = f"import {in_dir_name}.file3\n"
        files["file3.py"] = f"import {in_dir_name}.file1\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        show_cycles = True
        self.execute_script(
            files,
            show_cycles=show_cycles,
        )

    def test14(self) -> None:
        """
        Test showing only cyclic imports: multiple separate import cycles.
        """
        # Prepare the inputs.
        in_dir_name = self.get_input_dir().split("/")[-1]
        files = {}
        files["file1.py"] = f"import {in_dir_name}.file2\n"
        files["file2.py"] = f"import {in_dir_name}.file1\n"
        files["file3.py"] = f"import {in_dir_name}.file4\n"
        files["file4.py"] = f"import {in_dir_name}.file3\n"
        files["__init__.py"] = ""
        # Run and check the outcome.
        show_cycles = True
        self.execute_script(
            files,
            show_cycles=show_cycles,
        )
