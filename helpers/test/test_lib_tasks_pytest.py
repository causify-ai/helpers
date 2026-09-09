"""
Import as:

import helpers.test.test_lib_tasks_pytest as hltltapyt
"""

import os
import tempfile

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.lib_tasks.lib_tasks_pytest as hltltapy
import helpers.test.test_case as hvtc


class TestPytestRunClass(hvtc.TestCase):
    """Tests for pytest_run_class task."""

    def test_find_existing_class(self) -> None:
        """Test that pytest_run_class finds an existing class."""
        # Create a temporary test file.
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_example.py")
            hio.to_file(
                test_file,
                'import unittest\n\nclass TestExample1(unittest.TestCase):\n    def test_one(self):\n        pass\n',
            )
            # Create a test dir structure.
            test_dir = os.path.join(tmpdir, "test")
            os.makedirs(test_dir)
            hio.to_file(
                os.path.join(test_dir, "__init__.py"),
                "",
            )
            hio.to_file(
                os.path.join(test_dir, "test_example.py"),
                'import unittest\n\nclass TestExample1(unittest.TestCase):\n    def test_one(self):\n        pass\n',
            )
            # Find the class.
            import helpers.lib_tasks.lib_tasks_find as hltlafin

            file_names = hltlafin._find_test_files(test_dir)
            result = hltlafin._find_test_class("TestExample1", file_names, exact_match=True)
            self.assertLen(result, 1)
            self.assertIn("TestExample1", result[0])

    def test_find_nonexistent_class(self) -> None:
        """Test that pytest_run_class handles missing class."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test")
            os.makedirs(test_dir)
            hio.to_file(
                os.path.join(test_dir, "__init__.py"),
                "",
            )
            hio.to_file(
                os.path.join(test_dir, "test_example.py"),
                'import unittest\n\nclass TestExample1(unittest.TestCase):\n    def test_one(self):\n        pass\n',
            )
            import helpers.lib_tasks.lib_tasks_find as hltlafin

            file_names = hltlafin._find_test_files(test_dir)
            result = hltlafin._find_test_class(
                "TestNonexistent", file_names, exact_match=True
            )
            self.assertLen(result, 0)

    def test_ambiguous_class(self) -> None:
        """Test that pytest_run_class handles ambiguous class names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test")
            os.makedirs(test_dir)
            hio.to_file(
                os.path.join(test_dir, "__init__.py"),
                "",
            )
            hio.to_file(
                os.path.join(test_dir, "test_example.py"),
                'import unittest\n\nclass TestExample1(unittest.TestCase):\n    def test_one(self):\n        pass\n\nclass TestExample2(unittest.TestCase):\n    def test_two(self):\n        pass\n',
            )
            import helpers.lib_tasks.lib_tasks_find as hltlafin

            file_names = hltlafin._find_test_files(test_dir)
            # Non-exact match should find both.
            result = hltlafin._find_test_class("TestExample", file_names, exact_match=False)
            self.assertLen(result, 2)
