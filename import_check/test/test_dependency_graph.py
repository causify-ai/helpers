import os
import shutil
from pathlib import Path

import pytest

import import_check.dependency_graph as ichdegra


# TODO: use self.get_scratch_dir() and make this a function that is called
# by the needed test methods.
@pytest.fixture
def test_dir():
    """
    Create a temporary directory with test files and clean up after.

    Yields:
        Path: Path to the temporary directory.
    """
    # Create a temporary directory for test files.
    dir_path = Path("test_tmp")
    dir_path.mkdir(exist_ok=True)
    # TODO: Let's use hio.to_file
    # Create test files with specific imports.
    with open(dir_path / "module_a.py", "w") as f:
        f.write("# No imports\n")
    with open(dir_path / "module_b.py", "w") as f:
        f.write("import module_a\n")
    with open(dir_path / "module_c.py", "w") as f:
        f.write("import module_b\n")
    with open(dir_path / "module_d.py", "w") as f:
        f.write("import module_e\n")
    with open(dir_path / "module_e.py", "w") as f:
        f.write("import module_d\n")
    # Clean up the directory after test completion.
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


# #############################################################################
# TestDependencyGraph
# #############################################################################


# TODO: Derive from hunittest.TestCase
class TestDependencyGraph:

    def test_no_dependencies(self, test_dir: Path) -> None:
        """
        Verify a module with no imports has no dependencies.

        :param test_dir: Path to the test directory
        """
        # Initialize dependency graph and build it.
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        # Verify the module with no imports is reported correctly.
        # TODO: Use self.assert_in
        assert f"{test_dir}/module_a.py has no dependencies" in report

    def test_multiple_dependencies(self, test_dir: Path) -> None:
        """
        Verify modules with chained dependencies are reported correctly.

        :param test_dir: Path to the test directory
        """
        # Initialize dependency graph and build it.
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        # Verify chained dependencies are reported correctly.
        assert f"{test_dir}/module_c.py imports {test_dir}/module_b.py" in report
        assert f"{test_dir}/module_b.py imports {test_dir}/module_a.py" in report

    def test_circular_dependencies(self, test_dir: Path) -> None:
        """
        Verify cyclic dependencies are identified correctly.

        :param test_dir: Path to the test directory
        """
        # Initialize dependency graph and build it.
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        # Verify cyclic dependencies are identified.
        assert f"{test_dir}/module_d.py imports {test_dir}/module_e.py" in report
        assert f"{test_dir}/module_e.py imports {test_dir}/module_d.py" in report

    def test_dot_output(self, test_dir: Path) -> None:
        """
        Verify the DOT file is generated with correct format.

        :param test_dir: Path to the test directory
        """
        # Initialize dependency graph and build it.
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        output_file = "dependency_graph.dot"
        graph.get_dot_file(output_file)
        # Assert that the DOT file exists and has expected content.
        # TODO: use self.check_string
        assert os.path.exists(output_file)
        with open(output_file, "r") as f:
            content = f.read()
        assert "digraph" in content

    def test_syntax_error_handling(self, test_dir: Path) -> None:
        """
        Verify syntax errors in files are handled without crashing.

        :param test_dir: Path to the test directory
        """
        # Create a module with a syntax error.
        with open(test_dir / "module_invalid.py", "w") as f:
            f.write("def invalid_syntax()  # Missing colon\n")
        # Initialize dependency graph and build it.
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        # Verify that the graph is still correct.
        assert f"{test_dir}/module_a.py has no dependencies" in report

    def test_import_directory_only(self, test_dir: Path) -> None:
        """
        Verify importing only the directory name resolves to __init__.py.

        :param test_dir: Path to the test directory
        """
        # Create `__init__.py` in the test directory.
        with open(test_dir / "__init__.py", "w") as f:
            f.write("")
        # Create a module that imports the directory name.
        with open(test_dir / "module_f.py", "w") as f:
            f.write(f"import {test_dir.name}\n")
        # Initialize dependency graph and build it.
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        # Verify that the directory import is resolved to `__init__.py`.
        assert f"{test_dir}/module_f.py imports {test_dir}/__init__.py" in report

    def test_package_only_import(self) -> None:
        """
        Verify importing a package with only __init__.py adds a dependency.
        """
        # Prepare directory structure for the package.
        package_dir = Path("package_only_tmp")
        # TODO: use self.get_scratch_space and hio.to_file
        # TODO: use hio.create_dir
        # TODO: add a descrition of how the dir and files look like
        package_dir.mkdir(exist_ok=True)
        subdir = package_dir / "subpackage"
        subdir.mkdir(exist_ok=True)
        # Create `__init__.py` for the subdir.
        with open(subdir / "__init__.py", "w") as f:
            f.write("")
        # Create module that imports the package.
        with open(package_dir / "module_b.py", "w") as f:
            f.write("import subpackage\n")
        # TODO: No need for deleting.
        try:
            # Initialize dependency graph and build it.
            graph = ichdegra.DependencyGraph(str(package_dir))
            graph.build_graph()
            report = graph.get_text_report()
            # Verify the import of a subpackage is resolved as a dependency.
            assert (
                f"{package_dir}/module_b.py imports {package_dir}/subpackage/__init__.py"
                in report
            )
        finally:
            # Clean up package directory.
            shutil.rmtree(package_dir)

    def test_package_import(self) -> None:
        """
        Verify nested package imports resolve to __init__.py.
        """
        # Prepare nested package directory structure.
        package_dir = Path("package_tmp")
        package_dir.mkdir(exist_ok=True)
        subdir = package_dir / "subpackage"
        subdir.mkdir(exist_ok=True)
        subsubdir = subdir / "subsubpackage"
        subsubdir.mkdir(exist_ok=True)
        module_dir = subsubdir / "module_a"
        module_dir.mkdir(exist_ok=True)
        # Create `__init__.py` in each directory.
        with open(subdir / "__init__.py", "w") as f:
            f.write("")
        with open(subsubdir / "__init__.py", "w") as f:
            f.write("")
        with open(module_dir / "__init__.py", "w") as f:
            f.write("")
        # Create a module that imports the nested package.
        with open(package_dir / "module_b.py", "w") as f:
            f.write("import subpackage.subsubpackage.module_a\n")
        try:
            # Initialize dependency graph and build it.
            graph = ichdegra.DependencyGraph(str(package_dir))
            graph.build_graph()
            report = graph.get_text_report()
            # Verify the nested import is resolved as a dependency.
            assert (
                f"{package_dir}/module_b.py imports {package_dir}/subpackage/subsubpackage/module_a/__init__.py"
                in report
            )
        finally:
            # Clean up package directory.
            shutil.rmtree(package_dir)

    def test_unresolved_nested_import(self) -> None:
        """
        Verify unresolved nested imports result in no dependencies.
        """
        # Prepare directory structure where nested module is missing.
        package_dir = Path("unresolved_tmp")
        package_dir.mkdir(exist_ok=True)
        subdir = package_dir / "subpackage"
        subdir.mkdir(exist_ok=True)
        with open(subdir / "__init__.py", "w") as f:
            f.write("")
        # Create a module that imports a non-existent nested package.
        with open(package_dir / "module_b.py", "w") as f:
            f.write("import subpackage.subsubpackage.module_a\n")
        try:
            # Initialize dependency graph and build it.
            graph = ichdegra.DependencyGraph(str(package_dir))
            graph.build_graph()
            report = graph.get_text_report()
            # Verify no dependencies are reported for unresolved imports.
            assert f"{package_dir}/module_b.py has no dependencies" in report
        finally:
            # Clean up package directory.
            shutil.rmtree(package_dir)

    def test_show_cycles_filters_cyclic_dependencies(
        self, test_dir: Path
    ) -> None:
        """
        Verify show_cycles=True filters the graph to only cyclic dependencies.

        :param test_dir: Path to the test directory
        """
        # Create a module with no imports to ensure it's filtered out.
        with open(test_dir / "module_f.py", "w") as f:
            f.write("# No imports\n")
        # Build the graph with show_cycles=True to filter out everything but cycles.
        graph = ichdegra.DependencyGraph(str(test_dir), show_cycles=True)
        graph.build_graph()
        # Get the text report.
        report = graph.get_text_report()
        # Expected output: Only cyclic dependencies (module_d and module_e) should be shown.
        assert f"{test_dir}/module_d.py imports {test_dir}/module_e.py" in report
        assert f"{test_dir}/module_e.py imports {test_dir}/module_d.py" in report
        # Verify that non-cyclic `module_f` is not in the report.
        assert f"{test_dir}/module_f.py" not in report
