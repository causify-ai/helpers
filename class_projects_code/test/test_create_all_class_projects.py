#!/usr/bin/env python3

"""
Unit tests for create_all_class_projects.py.

Import as:

import test.test_create_all_class_projects as ttcrallcpro
"""

import os
import unittest.mock as umock

import create_all_class_projects as gallproj
import helpers.hunit_test as hunitest


# #############################################################################
# Test_find_lesson_files
# #############################################################################


class Test_find_lesson_files(hunitest.TestCase):
    """
    Test the find_lesson_files function.
    """

    def test_empty_directory(self) -> None:
        """
        Test finding lesson files in an empty directory.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Run test.
        result = gallproj.find_lesson_files(scratch_dir)
        # Check outputs.
        expected = []
        self.assert_equal(str(result), str(expected))

    def test_directory_with_lesson_files(self) -> None:
        """
        Test finding lesson files in directory with multiple lesson files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create test files
        lesson_files = [
            "Lesson01-Introduction.txt",
            "Lesson02-Techniques.txt",
            "Lesson10-Advanced.txt",
        ]
        other_files = [
            "README.md",
            "notes.txt",
            "Lesson01.pdf",  # Not .txt extension
        ]
        for filename in lesson_files + other_files:
            file_path = os.path.join(scratch_dir, filename)
            with open(file_path, "w") as f:
                f.write("test content")
        # Run test.
        result = gallproj.find_lesson_files(scratch_dir)
        # Check outputs.
        expected = [
            os.path.join(scratch_dir, "Lesson01-Introduction.txt"),
            os.path.join(scratch_dir, "Lesson02-Techniques.txt"),
            os.path.join(scratch_dir, "Lesson10-Advanced.txt"),
        ]
        self.assert_equal(str(sorted(result)), str(sorted(expected)))

    def test_directory_with_no_lesson_files(self) -> None:
        """
        Test finding lesson files in directory with no lesson files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create non-lesson files
        other_files = ["README.md", "notes.txt", "chapter1.txt"]
        for filename in other_files:
            file_path = os.path.join(scratch_dir, filename)
            with open(file_path, "w") as f:
                f.write("test content")
        # Run test.
        result = gallproj.find_lesson_files(scratch_dir)
        # Check outputs.
        expected = []
        self.assert_equal(str(result), str(expected))

    def test_nonexistent_directory(self) -> None:
        """
        Test finding lesson files in nonexistent directory raises assertion.
        """
        # Prepare inputs.
        nonexistent_dir = "/path/that/does/not/exist"
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            gallproj.find_lesson_files(nonexistent_dir)


# #############################################################################
# Test_generate_summary
# #############################################################################


class Test_generate_summary(hunitest.TestCase):
    """
    Test the generate_summary function.
    """

    def test_generate_summary_without_library(self) -> None:
        """
        Test generating summary without using library flag.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, "Lesson01-Test.txt")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        # Create test input file
        with open(in_file, "w") as f:
            f.write("# Test Lesson\n\nThis is test content.")
        expected_out_file = os.path.join(output_dir, "Lesson01-Test.summary.txt")
        expected_cmd = (
            f"python create_markdown_summary.py --in_file {in_file} "
            f"--action summarize --out_file {expected_out_file} "
            f"--max_num_bullets 3"
        )
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 0
            # Run test.
            result = gallproj.generate_summary(in_file, output_dir, 3, False)
            # Check outputs.
            self.assert_equal(result, expected_out_file)
            mock_system.assert_called_once_with(expected_cmd)

    def test_generate_summary_with_library(self) -> None:
        """
        Test generating summary with library flag.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, "Lesson02-Advanced.txt")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        # Create test input file
        with open(in_file, "w") as f:
            f.write("# Advanced Lesson\n\nThis is advanced content.")
        expected_out_file = os.path.join(
            output_dir, "Lesson02-Advanced.summary.txt"
        )
        expected_cmd = (
            f"python create_markdown_summary.py --in_file {in_file} "
            f"--action summarize --out_file {expected_out_file} "
            f"--max_num_bullets 5 --use_library"
        )
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 0
            # Run test.
            result = gallproj.generate_summary(in_file, output_dir, 5, True)
            # Check outputs.
            self.assert_equal(result, expected_out_file)
            mock_system.assert_called_once_with(expected_cmd)

    def test_generate_summary_command_failure(self) -> None:
        """
        Test generating summary when command fails.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, "Lesson01-Test.txt")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        # Create test input file
        with open(in_file, "w") as f:
            f.write("# Test Lesson\n\nThis is test content.")
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 1  # Command failure
            # Run test and check outputs.
            with self.assertRaises(AssertionError):
                gallproj.generate_summary(in_file, output_dir, 3, False)


# #############################################################################
# Test_generate_projects
# #############################################################################


class Test_generate_projects(hunitest.TestCase):
    """
    Test the generate_projects function.
    """

    def test_generate_projects_success(self) -> None:
        """
        Test generating projects successfully.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, "Lesson01-ML.txt")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        # Create test input file
        with open(in_file, "w") as f:
            f.write("# Machine Learning Lesson\n\nContent about ML.")
        expected_out_file = os.path.join(output_dir, "Lesson01-ML.projects.txt")
        expected_cmd = (
            f"python create_class_projects.py --in_file {in_file} "
            f"--action create_project --out_file {expected_out_file}"
        )
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 0
            # Run test.
            result = gallproj.generate_projects(in_file, output_dir)
            # Check outputs.
            self.assert_equal(result, expected_out_file)
            mock_system.assert_called_once_with(expected_cmd)

    def test_generate_projects_command_failure(self) -> None:
        """
        Test generating projects when command fails.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, "Lesson01-Test.txt")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        # Create test input file
        with open(in_file, "w") as f:
            f.write("# Test Lesson\n\nThis is test content.")
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 1  # Command failure
            # Run test and check outputs.
            with self.assertRaises(AssertionError):
                gallproj.generate_projects(in_file, output_dir)


# #############################################################################
# Test_process_all_lessons
# #############################################################################


class Test_process_all_lessons(hunitest.TestCase):
    """
    Test the process_all_lessons function.
    """

    def test_process_all_lessons_success(self) -> None:
        """
        Test processing all lesson files successfully.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_dir = os.path.join(scratch_dir, "input")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(input_dir, exist_ok=True)
        # Create test lesson files
        lesson_files = ["Lesson01-Basics.txt", "Lesson02-Advanced.txt"]
        for filename in lesson_files:
            file_path = os.path.join(input_dir, filename)
            with open(file_path, "w") as f:
                f.write(f"# {filename}\n\nContent for {filename}")
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 0
            # Run test.
            gallproj.process_all_lessons(input_dir, output_dir, 3, False)
            # Check outputs.
            # Should have called system twice for each file (summary + projects)
            expected_calls = 4  # 2 files * 2 commands each
            self.assert_equal(str(mock_system.call_count), str(expected_calls))
            # Check that output directory was created
            self.assertTrue(os.path.exists(output_dir))

    def test_process_all_lessons_no_files(self) -> None:
        """
        Test processing when no lesson files are found.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_dir = os.path.join(scratch_dir, "input")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(input_dir, exist_ok=True)
        # Create non-lesson files
        with open(os.path.join(input_dir, "readme.txt"), "w") as f:
            f.write("Not a lesson file")
        with umock.patch("helpers.hsystem.system") as mock_system:
            # Run test.
            gallproj.process_all_lessons(input_dir, output_dir, 3, False)
            # Check outputs.
            mock_system.assert_not_called()

    def test_process_all_lessons_with_failure(self) -> None:
        """
        Test processing when one of the commands fails.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_dir = os.path.join(scratch_dir, "input")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(input_dir, exist_ok=True)
        # Create test lesson file
        lesson_file = os.path.join(input_dir, "Lesson01-Test.txt")
        with open(lesson_file, "w") as f:
            f.write("# Test Lesson\n\nContent")
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 1  # Command failure
            # Run test and check outputs.
            with self.assertRaises(AssertionError):
                gallproj.process_all_lessons(input_dir, output_dir, 3, False)


# #############################################################################
# Test_main_integration
# #############################################################################


# Integration test that uses the actual command-line interface
class Test_main_integration(hunitest.TestCase):
    """
    Test the main function integration.
    """

    @umock.patch("sys.argv")
    def test_main_with_valid_args(self, mock_argv) -> None:
        """
        Test main function with valid arguments.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_dir = os.path.join(scratch_dir, "input")
        output_dir = os.path.join(scratch_dir, "output")
        os.makedirs(input_dir, exist_ok=True)
        # Mock command line arguments
        mock_argv.__getitem__.side_effect = lambda x: [
            "generate_all_projects.py",
            "--input_dir",
            input_dir,
            "--output_dir",
            output_dir,
            "--max_num_bullets",
            "5",
            "--use_library",
        ][x]
        mock_argv.__len__.return_value = 7
        # Create test lesson file
        lesson_file = os.path.join(input_dir, "Lesson01-Test.txt")
        with open(lesson_file, "w") as f:
            f.write("# Test Lesson\n\nContent")
        with umock.patch("helpers.hsystem.system") as mock_system:
            mock_system.return_value = 0
            # Run test.
            parser = gallproj._parse()
            gallproj._main(parser)
            # Check outputs.
            # Should have been called twice (summary + projects)
            self.assert_equal(str(mock_system.call_count), str(2))
