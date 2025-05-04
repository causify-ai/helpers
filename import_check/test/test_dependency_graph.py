# Standard library imports
import os
import shutil
from pathlib import Path

# Third-party imports
import pytest

# Local imports
from import_check.dependency_graph import DependencyGraph


@pytest.fixture
def test_dir():
    """
    Create a temporary directory with test files and clean up after.

    Yields:
        Path: Path to the temporary directory.
    """
    dir_path = Path("test_tmp")
    dir_path.mkdir(exist_ok=True)
    # Create test files with specific imports
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
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


# #############################################################################
# TestDependencyGraph
# #############################################################################


class TestDependencyGraph:

    def test_no_dependencies(self, test_dir: Path) -> None:
        """
        Verify a module with no imports has no dependencies.
        """
        graph = DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        assert f"{test_dir}/module_a.py has no dependencies" in report

    def test_multiple_dependencies(self, test_dir: Path) -> None:
        """
        Verify modules with chained dependencies are reported correctly.
        """
        graph = DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        assert f"{test_dir}/module_c.py imports {test_dir}/module_b.py" in report
        assert f"{test_dir}/module_b.py imports {test_dir}/module_a.py" in report

    def test_circular_dependencies(self, test_dir: Path) -> None:
        """
        Verify cyclic dependencies are identified correctly.
        """
        graph = DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        assert f"{test_dir}/module_d.py imports {test_dir}/module_e.py" in report
        assert f"{test_dir}/module_e.py imports {test_dir}/module_d.py" in report

    def test_dot_output(self, test_dir: Path) -> None:
        """
        Verify the DOT file is generated with correct format.
        """
        graph = DependencyGraph(str(test_dir))
        graph.build_graph()
        output_file = "dependency_graph.dot"
        graph.get_dot_file(output_file)
        assert os.path.exists(output_file)
        with open(output_file, "r") as f:
            content = f.read()
        assert "digraph" in content

    def test_syntax_error_handling(self, test_dir: Path) -> None:
        """
        Verify syntax errors in files are handled without crashing.
        """
        with open(test_dir / "module_invalid.py", "w") as f:
            f.write("def invalid_syntax()  # Missing colon\n")
        graph = DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        assert f"{test_dir}/module_a.py has no dependencies" in report

    def test_import_directory_only(self, test_dir: Path) -> None:
        """
        Verify importing only the directory name resolves to __init__.py.
        """
        # Create __init__.py in the test directory
        with open(test_dir / "__init__.py", "w") as f:
            f.write("")
        # Create a module that imports the directory name
        with open(test_dir / "module_f.py", "w") as f:
            f.write(f"import {test_dir.name}\n")
        graph = DependencyGraph(str(test_dir))
        graph.build_graph()
        report = graph.get_text_report()
        assert f"{test_dir}/module_f.py imports {test_dir}/__init__.py" in report

    def test_package_only_import(self) -> None:
        """
        Verify importing a package with only __init__.py adds a dependency.
        """
        package_dir = Path("package_only_tmp")
        package_dir.mkdir(exist_ok=True)
        subdir = package_dir / "subpackage"
        subdir.mkdir(exist_ok=True)
        with open(subdir / "__init__.py", "w") as f:
            f.write("")
        with open(package_dir / "module_b.py", "w") as f:
            f.write("import subpackage\n")
        try:
            graph = DependencyGraph(str(package_dir))
            graph.build_graph()
            report = graph.get_text_report()
            assert (
                f"{package_dir}/module_b.py imports {package_dir}/subpackage/__init__.py"
                in report
            )
        finally:
            shutil.rmtree(package_dir)

    def test_package_import(self) -> None:
        """
        Verify nested package imports resolve to __init__.py.
        """
        package_dir = Path("package_tmp")
        package_dir.mkdir(exist_ok=True)
        subdir = package_dir / "subpackage"
        subdir.mkdir(exist_ok=True)
        subsubdir = subdir / "subsubpackage"
        subsubdir.mkdir(exist_ok=True)
        module_dir = subsubdir / "module_a"
        module_dir.mkdir(exist_ok=True)
        with open(subdir / "__init__.py", "w") as f:
            f.write("")
        with open(subsubdir / "__init__.py", "w") as f:
            f.write("")
        with open(module_dir / "__init__.py", "w") as f:
            f.write("")
        with open(package_dir / "module_b.py", "w") as f:
            f.write("import subpackage.subsubpackage.module_a\n")
        try:
            graph = DependencyGraph(str(package_dir))
            graph.build_graph()
            report = graph.get_text_report()
            assert (
                f"{package_dir}/module_b.py imports {package_dir}/subpackage/subsubpackage/module_a/__init__.py"
                in report
            )
        finally:
            shutil.rmtree(package_dir)

    def test_unresolved_nested_import(self) -> None:
        """
        Verify unresolved nested imports result in no dependencies.
        """
        package_dir = Path("unresolved_tmp")
        package_dir.mkdir(exist_ok=True)
        subdir = package_dir / "subpackage"
        subdir.mkdir(exist_ok=True)
        with open(subdir / "__init__.py", "w") as f:
            f.write("")
        with open(package_dir / "module_b.py", "w") as f:
            f.write("import subpackage.subsubpackage.module_a\n")
        try:
            graph = DependencyGraph(str(package_dir))
            graph.build_graph()
            report = graph.get_text_report()
            assert f"{package_dir}/module_b.py has no dependencies" in report
        finally:
            shutil.rmtree(package_dir)

    def test_show_cycles_filters_cyclic_dependencies(
        self, test_dir: Path
    ) -> None:
        """
        Verify show_cycles=True filters the graph to only cyclic dependencies.
        """
        # Create a module with no imports to ensure it's filtered out
        with open(test_dir / "module_f.py", "w") as f:
            f.write("# No imports\n")
        # Build the graph with show_cycles=True
        graph = DependencyGraph(str(test_dir), show_cycles=True)
        graph.build_graph()
        # Get the text report
        report = graph.get_text_report()
        # Expected output: Only cyclic dependencies (module_d and module_e) should be shown
        assert f"{test_dir}/module_d.py imports {test_dir}/module_e.py" in report
        assert f"{test_dir}/module_e.py imports {test_dir}/module_d.py" in report
        # Verify that non-cyclic module_f is not in the report
        assert f"{test_dir}/module_f.py" not in report
