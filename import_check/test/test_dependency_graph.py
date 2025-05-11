import os
import pathlib as path  # Updated import style

import helpers.hio as hio
import helpers.hunit_test as hunitest
import import_check.dependency_graph as ichdegra


# #############################################################################
# TestDependencyGraph
# #############################################################################


# #############################################################################
# TestDependencyGraph
# #############################################################################
# TODO: class TestDependencyGraph(hunitest.TestCase):
class TestDependencyGraph(hunitest.TestCase):
    # TODO: use self.get_scratch_dir() and make this a function that is called
    def get_test_dir(self) -> path.Path:
        """
        Create a temporary directory with test files.

        :return: Path to the temporary directory.
        """
        # Prepare directory.
        dir_path = path.Path(self.get_scratch_space())
        # Create test files.
        hio.create_dir(dir_path, incremental=True)
        hio.to_file(str(dir_path / "module_a.py"), "# No imports\n")
        hio.to_file(str(dir_path / "module_b.py"), "import module_a\n")
        hio.to_file(str(dir_path / "module_c.py"), "import module_b\n")
        hio.to_file(str(dir_path / "module_d.py"), "import module_e\n")
        hio.to_file(str(dir_path / "module_e.py"), "import module_d\n")
        return dir_path

    def test_no_dependencies(self) -> None:
        """
        Verify a module with no imports has no dependencies.
        """
        # Prepare inputs
        test_dir = self.get_test_dir()
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        # Run.
        report = graph.get_text_report()
        # TODO: Use self.assert_in
        # Check.
        self.assertIn("tmp.scratch/module_a.py has no dependencies", report)

    def test_multiple_dependencies(self) -> None:
        """
        Verify modules with chained dependencies are reported correctly.
        """
        # Prepare inputs.
        test_dir = self.get_test_dir()
        graph = ichdegra.DependencyGraph(str(test_dir))
        # Run.
        graph.build_graph()
        report = graph.get_text_report()
        # Check.
        self.assertIn(
            "tmp.scratch/module_c.py imports tmp.scratch/module_b.py", report
        )
        self.assertIn(
            "tmp.scratch/module_b.py imports tmp.scratch/module_a.py", report
        )

    def test_circular_dependencies(self) -> None:
        """
        Verify cyclic dependencies are identified correctly.
        """
        # Prepare inputs.
        test_dir = self.get_test_dir()
        graph = ichdegra.DependencyGraph(str(test_dir))
        # Run.
        graph.build_graph()
        report = graph.get_text_report()
        # Check.
        self.assertIn(
            "tmp.scratch/module_d.py imports tmp.scratch/module_e.py", report
        )
        self.assertIn(
            "tmp.scratch/module_e.py imports tmp.scratch/module_d.py", report
        )

    def test_dot_output(self) -> None:
        """
        Verify the DOT file is generated with correct format.
        """
        # Prepare inputs.
        test_dir = self.get_test_dir()
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()
        # Run.
        scratch_dir = path.Path(self.get_scratch_space())
        output_file = scratch_dir / "dependency_graph.dot"
        graph.get_dot_file(str(output_file))
        # TODO: use self.check_string
        # Check.
        # Verify the DOT file content matches the expected golden outcome.
        content = hio.from_file(str(output_file), encoding="utf-8")
        self.check_string(content)

    
    def test_dot_output(self) -> None:
        """
        Verify that the DependencyGraph generates a DOT file with the correct format,
        representing module dependencies as a directed graph.
        """
        # Prepare inputs: Create a temporary directory with test files and initialize graph.
        test_dir = self.get_test_dir()
        graph = ichdegra.DependencyGraph(str(test_dir))
        graph.build_graph()

        # Run: Generate the DOT file in a temporary scratch space.
        scratch_dir = path.Path(self.get_scratch_space())
        output_file = scratch_dir / "dependency_graph.dot"
        graph.get_dot_file(str(output_file))

        # Check: Verify the DOT file content matches the expected golden outcome.
        content = hio.from_file(str(output_file), encoding="utf-8")
        self.check_string(content)


    def test_syntax_error_handling(self) -> None:
        """
        Verify syntax errors in files are handled without crashing.
        """
        # Prepare inputs.
        test_dir = self.get_test_dir()
        hio.to_file(
            str(test_dir / "module_invalid.py"),
            "def invalid_syntax()  # Missing colon\n",
        )
        graph = ichdegra.DependencyGraph(str(test_dir))
        # Run.
        graph.build_graph()
        report = graph.get_text_report()
        # Check.
        self.assertIn("tmp.scratch/module_a.py has no dependencies", report)

    def test_import_directory_only(self) -> None:
        """
        Verify importing only the directory name resolves to __init__.py.
        """
        # Prepare inputs.
        test_dir = self.get_test_dir()
        init_path = test_dir / "__init__.py"
        hio.to_file(str(init_path), "")
        hio.to_file(str(test_dir / "module_f.py"), f"import {test_dir.name}")
        graph = ichdegra.DependencyGraph(str(test_dir))
        # Run.
        graph.build_graph()
        report = graph.get_text_report()
        # Check.
        self.assertIn(
            "tmp.scratch/module_f.py imports tmp.scratch/__init__.py", report
        )

    def test_package_only_import(self) -> None:
        """
        Verify importing a package with only __init__.py adds a dependency.
        """
        # TODO: use self.get_scratch_space and hio.to_file
        # TODO: use hio.create_dir
        # TODO: add a descrition of how the dir and files look like
        # Prepare inputs.
        package_dir = path.Path(self.get_scratch_space())
        subdir = package_dir / "subpackage"
        hio.create_dir(subdir, incremental=True)
        hio.to_file(str(subdir / "__init__.py"), "")
        hio.to_file(str(package_dir / "module_b.py"), "import subpackage")
        # Directory structure:
        # tmp.scratch/
        #   subpackage/
        #     __init__.py
        #   module_b.py
        # Run.
        graph = ichdegra.DependencyGraph(str(package_dir))
        graph.build_graph()
        report = graph.get_text_report()
        # Check.
        self.assertIn(
            "tmp.scratch/module_b.py imports tmp.scratch/subpackage/__init__.py",
            report,
        )

    def test_package_import(self) -> None:
        """
        Verify nested package imports resolve to __init__.py.
        """
        # Prepare inputs.
        package_dir = path.Path(self.get_scratch_space())
        subdir = package_dir / "subpackage"
        subsubdir = subdir / "subsubpackage"
        module_dir = subsubdir / "module_a"
        hio.create_dir(subdir, incremental=True)
        hio.create_dir(subsubdir, incremental=True)
        hio.create_dir(module_dir, incremental=True)
        hio.to_file(str(subdir / "__init__.py"), "")
        hio.to_file(str(subsubdir / "__init__.py"), "")
        hio.to_file(str(module_dir / "__init__.py"), "")
        hio.to_file(
            str(package_dir / "module_b.py"),
            "import subpackage.subsubpackage.module_a",
        )
        # Directory structure:
        # tmp.scratch/
        #   subpackage/
        #     __init__.py
        #     subsubpackage/
        #       __init__.py
        #       module_a/
        #         __init__.py
        #   module_b.py
        # Run.
        graph = ichdegra.DependencyGraph(str(package_dir))
        graph.build_graph()
        # Check.
        report = graph.get_text_report()
        self.assertIn(
            "tmp.scratch/module_b.py imports "
            "tmp.scratch/subpackage/subsubpackage/module_a/__init__.py",
            report,
        )

    def test_unresolved_nested_import(self) -> None:
        """
        Verify unresolved nested imports result in no dependencies.
        """
        # Prepare inputs.
        package_dir = path.Path(self.get_scratch_space())
        subdir = package_dir / "subpackage"
        hio.create_dir(subdir, incremental=True)
        hio.to_file(str(subdir / "__init__.py"), "")
        hio.to_file(
            str(package_dir / "module_b.py"),
            "import subpackage.subsubpackage.module_a",
        )
        # Directory structure:
        # tmp.scratch/
        #   subpackage/
        #     __init__.py
        #   module_b.py
        # Run.
        graph = ichdegra.DependencyGraph(str(package_dir))
        graph.build_graph()
        report = graph.get_text_report()
        # Check.
        self.assertIn("tmp.scratch/module_b.py has no dependencies", report)

    def test_show_cycles_filters_cyclic_dependencies(self) -> None:
        """
        Verify show_cycles=True filters the graph to only cyclic dependencies.
        """
        # Prepare inputs.
        test_dir = self.get_test_dir()
        hio.to_file(str(test_dir / "module_f.py"), "# No imports")
        graph = ichdegra.DependencyGraph(str(test_dir), show_cycles=True)
        # Run.
        graph.build_graph()
        report = graph.get_text_report()
        # Check.
        self.assertIn(
            "tmp.scratch/module_d.py imports tmp.scratch/module_e.py", report
        )
        self.assertIn(
            "tmp.scratch/module_e.py imports tmp.scratch/module_d.py", report
        )
        self.assertFalse("tmp.scratch/module_f.py" in report)
