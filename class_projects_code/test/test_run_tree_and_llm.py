import logging
import os
import tempfile
import unittest.mock
from typing import List

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hsystem as hsystem

import run_tree_and_llm

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_limit_range
# #############################################################################


class Test_parse_limit_range(hunitest.TestCase):
    def test_valid_range(self) -> None:
        """
        Test valid range format like '1:5'.
        """
        # Test basic range.
        result = run_tree_and_llm._parse_limit_range("1:5")
        expected = (0, 4)  # Convert to 0-indexed
        self.assertEqual(result, expected)
        
    def test_single_number(self) -> None:
        """
        Test single number format like '3'.
        """
        result = run_tree_and_llm._parse_limit_range("3")
        expected = (2, 2)  # Convert to 0-indexed, single element
        self.assertEqual(result, expected)
        
    def test_large_range(self) -> None:
        """
        Test larger range values.
        """
        result = run_tree_and_llm._parse_limit_range("10:20")
        expected = (9, 19)
        self.assertEqual(result, expected)
        
    def test_invalid_format_no_colon(self) -> None:
        """
        Test invalid format without colon or number.
        """
        with self.assertRaises(ValueError):
            run_tree_and_llm._parse_limit_range("invalid")
            
    def test_invalid_format_empty_parts(self) -> None:
        """
        Test invalid format with empty parts like ':5' or '5:'.
        """
        with self.assertRaises(ValueError):
            run_tree_and_llm._parse_limit_range(":5")
        with self.assertRaises(ValueError):
            run_tree_and_llm._parse_limit_range("5:")
            
    def test_invalid_format_too_many_colons(self) -> None:
        """
        Test invalid format with multiple colons.
        """
        with self.assertRaises(ValueError):
            run_tree_and_llm._parse_limit_range("1:2:3")
            
    def test_invalid_range_start_greater_than_end(self) -> None:
        """
        Test invalid range where start is greater than end.
        """
        with self.assertRaises(ValueError):
            run_tree_and_llm._parse_limit_range("5:3")
            
    def test_zero_values(self) -> None:
        """
        Test zero values which should be invalid (1-indexed input).
        """
        with self.assertRaises(ValueError):
            run_tree_and_llm._parse_limit_range("0:5")
        with self.assertRaises(ValueError):
            run_tree_and_llm._parse_limit_range("1:0")


# #############################################################################
# Test_get_directories
# #############################################################################


class Test_get_directories(hunitest.TestCase):
    def setUp(self) -> None:
        """
        Set up test directories.
        """
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test directories
        self.test_dirs = ["dir1", "dir2", "dir3", "dir4", "dir5"]
        for dir_name in self.test_dirs:
            os.makedirs(os.path.join(self.temp_dir, dir_name))
            
        # Create a test file (should be ignored)
        with open(os.path.join(self.temp_dir, "test_file.txt"), "w") as f:
            f.write("test")
            
    def tearDown(self) -> None:
        """
        Clean up test directories.
        """
        hsystem.system(f"rm -rf {self.temp_dir}")
        
    def test_get_all_directories(self) -> None:
        """
        Test getting all directories without limit.
        """
        result = run_tree_and_llm._get_directories(self.temp_dir, None)
        expected_paths = [os.path.join(self.temp_dir, d) for d in self.test_dirs]
        self.assertEqual(sorted(result), sorted(expected_paths))
        
    def test_get_directories_with_range_limit(self) -> None:
        """
        Test getting directories with range limit.
        """
        limit_range = (1, 3)  # Should get 2nd and 3rd directories (0-indexed)
        result = run_tree_and_llm._get_directories(self.temp_dir, limit_range)
        # Sort to ensure consistent ordering
        all_dirs = sorted([os.path.join(self.temp_dir, d) for d in self.test_dirs])
        expected = all_dirs[1:4]  # Elements at index 1, 2, 3
        self.assertEqual(sorted(result), sorted(expected))
        
    def test_get_directories_with_single_element_limit(self) -> None:
        """
        Test getting single directory with limit.
        """
        limit_range = (2, 2)  # Should get 3rd directory (0-indexed)
        result = run_tree_and_llm._get_directories(self.temp_dir, limit_range)
        all_dirs = sorted([os.path.join(self.temp_dir, d) for d in self.test_dirs])
        expected = [all_dirs[2]]  # Element at index 2
        self.assertEqual(result, expected)
        
    def test_get_directories_limit_beyond_available(self) -> None:
        """
        Test limit range that extends beyond available directories.
        """
        limit_range = (3, 10)  # Beyond available directories
        result = run_tree_and_llm._get_directories(self.temp_dir, limit_range)
        all_dirs = sorted([os.path.join(self.temp_dir, d) for d in self.test_dirs])
        expected = all_dirs[3:]  # From index 3 to end
        self.assertEqual(sorted(result), sorted(expected))
        
    def test_get_directories_empty_directory(self) -> None:
        """
        Test with empty directory.
        """
        empty_dir = tempfile.mkdtemp()
        try:
            result = run_tree_and_llm._get_directories(empty_dir, None)
            self.assertEqual(result, [])
        finally:
            hsystem.system(f"rmdir {empty_dir}")
            
    def test_get_directories_nonexistent_path(self) -> None:
        """
        Test with nonexistent directory path.
        """
        nonexistent_path = "/nonexistent/path"
        with self.assertRaises(FileNotFoundError):
            run_tree_and_llm._get_directories(nonexistent_path, None)


# #############################################################################
# Test_main_argument_parsing
# #############################################################################


class Test_main_argument_parsing(hunitest.TestCase):
    def setUp(self) -> None:
        """
        Set up test directory.
        """
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "test_subdir"))
        
    def tearDown(self) -> None:
        """
        Clean up test directory.
        """
        hsystem.system(f"rm -rf {self.temp_dir}")
        
    @unittest.mock.patch('sys.argv')
    def test_parse_basic_arguments(self, mock_argv) -> None:
        """
        Test parsing basic required arguments.
        """
        mock_argv.__getitem__.side_effect = [
            "run_tree_and_llm.py",
            "--in_dir", self.temp_dir,
            "--out_dir", "/tmp/output"
        ]
        mock_argv.__len__.return_value = 5
        
        args = run_tree_and_llm._parse()
        self.assertEqual(args.in_dir, self.temp_dir)
        self.assertEqual(args.out_dir, "/tmp/output")
        
    @unittest.mock.patch('sys.argv')
    def test_parse_with_limit_argument(self, mock_argv) -> None:
        """
        Test parsing with limit argument.
        """
        mock_argv.__getitem__.side_effect = [
            "run_tree_and_llm.py",
            "--in_dir", self.temp_dir,
            "--out_dir", "/tmp/output",
            "--limit", "1:5"
        ]
        mock_argv.__len__.return_value = 7
        
        args = run_tree_and_llm._parse()
        self.assertEqual(args.limit, "1:5")
        
    @unittest.mock.patch('sys.argv')
    def test_parse_with_action_arguments(self, mock_argv) -> None:
        """
        Test parsing with action arguments.
        """
        mock_argv.__getitem__.side_effect = [
            "run_tree_and_llm.py",
            "--in_dir", self.temp_dir,
            "--out_dir", "/tmp/output",
            "--action", "tree"
        ]
        mock_argv.__len__.return_value = 7
        
        args = run_tree_and_llm._parse()
        self.assertEqual(args.action, ["tree"])


# #############################################################################
# Test_integration
# #############################################################################


class Test_integration(hunitest.TestCase):
    def setUp(self) -> None:
        """
        Set up test environment with directories and files.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.out_dir = tempfile.mkdtemp()
        
        # Create test directory structure
        test_subdir = os.path.join(self.temp_dir, "test_project")
        os.makedirs(test_subdir)
        
        # Add some test files
        with open(os.path.join(test_subdir, "README.md"), "w") as f:
            f.write("# Test Project\n\nThis is a test project.")
        with open(os.path.join(test_subdir, "main.py"), "w") as f:
            f.write("print('Hello, World!')")
            
    def tearDown(self) -> None:
        """
        Clean up test directories.
        """
        hsystem.system(f"rm -rf {self.temp_dir}")
        hsystem.system(f"rm -rf {self.out_dir}")
        
    @unittest.mock.patch('sys.argv')
    @unittest.mock.patch('run_tree_and_llm._run_llm_on_file')
    def test_end_to_end_tree_action_only(self, mock_llm, mock_argv) -> None:
        """
        Test end-to-end execution with tree action only.
        """
        # Mock arguments
        mock_argv.__getitem__.side_effect = [
            "run_tree_and_llm.py",
            "--in_dir", self.temp_dir,
            "--out_dir", self.out_dir,
            "--action", "tree"
        ]
        mock_argv.__len__.return_value = 7
        
        # Run the main function
        run_tree_and_llm._main()
        
        # Check that tree files were created
        expected_tree_file = os.path.join(
            self.out_dir, 
            f"tree_{os.path.basename(self.temp_dir)}_test_project.txt"
        )
        self.assertTrue(os.path.exists(expected_tree_file))
        
        # Check that LLM was not called since we only ran tree action
        mock_llm.assert_not_called()
        
    @unittest.mock.patch('sys.argv')
    def test_end_to_end_with_limit(self, mock_argv) -> None:
        """
        Test end-to-end execution with limit parameter.
        """
        # Create multiple subdirectories
        for i in range(3):
            subdir = os.path.join(self.temp_dir, f"project_{i}")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "file.txt"), "w") as f:
                f.write(f"Content {i}")
                
        mock_argv.__getitem__.side_effect = [
            "run_tree_and_llm.py",
            "--in_dir", self.temp_dir,
            "--out_dir", self.out_dir,
            "--limit", "1:2",
            "--action", "tree"
        ]
        mock_argv.__len__.return_value = 9
        
        # Run the main function
        run_tree_and_llm._main()
        
        # Check that only limited directories were processed
        tree_files = [f for f in os.listdir(self.out_dir) if f.startswith("tree_")]
        # Should have 2 files (directories 1 and 2, 0-indexed: project_0 and project_1)
        self.assertEqual(len(tree_files), 2)