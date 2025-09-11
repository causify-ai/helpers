import logging
import os
import tempfile
from unittest.mock import patch

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import create_lesson_project as crcpro

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse
# #############################################################################


class Test_parse(hunitest.TestCase):
    def test_default_arguments(self) -> None:
        """
        Test parser with minimal required arguments.
        """
        # Prepare inputs.
        args = ["--in_file", "test_input.md", "--level", "medium"]
        # Run test.
        parser = crcpro._parse()
        parsed_args = parser.parse_args(args)
        # Check outputs.
        self.assert_equal(parsed_args.in_file, "test_input.md")
        self.assert_equal(parsed_args.level, "medium")
        self.assertIsNone(parsed_args.action)

    def test_level_argument_easy(self) -> None:
        """
        Test parser with level set to easy.
        """
        # Prepare inputs.
        args = ["--in_file", "test_input.md", "--level", "easy"]
        # Run test.
        parser = crcpro._parse()
        parsed_args = parser.parse_args(args)
        # Check outputs.
        self.assert_equal(parsed_args.level, "easy")

    def test_level_argument_hard(self) -> None:
        """
        Test parser with level set to hard.
        """
        # Prepare inputs.
        args = ["--in_file", "test_input.md", "--level", "hard"]
        # Run test.
        parser = crcpro._parse()
        parsed_args = parser.parse_args(args)
        # Check outputs.
        self.assert_equal(parsed_args.level, "hard")

    def test_output_file_argument(self) -> None:
        """
        Test parser with output file specified.
        """
        # Prepare inputs.
        args = ["--in_file", "test_input.md", "--level", "medium", "--output_file", "output.txt"]
        # Run test.
        parser = crcpro._parse()
        parsed_args = parser.parse_args(args)
        # Check outputs.
        self.assert_equal(parsed_args.output_file, "output.txt")

    def test_find_packages_action(self) -> None:
        """
        Test parser with find_packages action specified.
        """
        # Prepare inputs.
        args = ["--in_file", "test_input.md", "--level", "medium", "--action", "find_packages"]
        # Run test.
        parser = crcpro._parse()
        parsed_args = parser.parse_args(args)
        # Check outputs.
        self.assertIn("find_packages", parsed_args.action)


# #############################################################################
# Test_call_llm
# #############################################################################


class Test_call_llm(hunitest.TestCase):
    @patch('create_class_projects.hsystem.system_to_string')
    @patch('create_class_projects.hio.to_file')
    def test_basic_call(self, mock_to_file, mock_system_to_string) -> None:
        """
        Test basic LLM call with prompt and content.
        """
        # Prepare inputs.
        prompt = "Test prompt"
        content = "Test content"
        mock_system_to_string.return_value = (0, "  LLM response  ")
        # Run test.
        result = crcpro._call_llm(prompt, content)
        # Check outputs.
        self.assert_equal(result, "LLM response")
        mock_to_file.assert_called_once()
        mock_system_to_string.assert_called_once()
        # Verify the prompt was written correctly.
        call_args = mock_to_file.call_args[0]
        expected_full_prompt = f"{prompt}\n\n{content}"
        self.assert_equal(call_args[1], expected_full_prompt)

    @patch('create_class_projects.hsystem.system_to_string')
    @patch('create_class_projects.hio.to_file')
    def test_empty_content(self, mock_to_file, mock_system_to_string) -> None:
        """
        Test LLM call with empty content.
        """
        # Prepare inputs.
        prompt = "Test prompt"
        content = ""
        mock_system_to_string.return_value = (0, "Response")
        # Run test.
        result = crcpro._call_llm(prompt, content)
        # Check outputs.
        self.assert_equal(result, "Response")
        call_args = mock_to_file.call_args[0]
        expected_full_prompt = f"{prompt}\n\n{content}"
        self.assert_equal(call_args[1], expected_full_prompt)


# #############################################################################
# Test_action_create_project
# #############################################################################


class Test_action_create_project(hunitest.TestCase):
        
    @patch('create_class_projects._call_llm')
    def test_medium_level_default(self, mock_call_llm) -> None:
        """
        Test action with medium difficulty level (default).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_content = """
        # Test Lesson
        
        This is a test lesson about data science.
        
        ## Section 1
        Content about pandas.
        """
        test_content = hprint.dedent(test_content)
        input_file = os.path.join(scratch_dir, "test_input.md")
        output_file = os.path.join(scratch_dir, "test_output.txt")
        hio.to_file(input_file, test_content)
        
        mock_llm_response = "Generated projects content"
        mock_call_llm.return_value = mock_llm_response
        
        # Run test.
        crcpro._action_create_project(input_file, output_file, "medium")
        
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        result_content = hio.from_file(output_file)
        self.assertIn("# Class Projects", result_content)
        self.assertIn(mock_llm_response, result_content)
        
        # Verify LLM was called with correct prompt containing medium level.
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args[0]
        prompt = call_args[0]
        self.assertIn("The difficulty level should be medium", prompt)

    @patch('create_class_projects._call_llm')
    def test_easy_level(self, mock_call_llm) -> None:
        """
        Test action with easy difficulty level.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_content = """
        # Test Lesson
        Content for easy projects.
        """
        test_content = hprint.dedent(test_content)
        input_file = os.path.join(scratch_dir, "test_input.md")
        output_file = os.path.join(scratch_dir, "test_output.txt")
        hio.to_file(input_file, test_content)
        
        mock_llm_response = "Easy projects content"
        mock_call_llm.return_value = mock_llm_response
        
        # Run test.
        crcpro._action_create_project(input_file, output_file, "easy")
        
        # Check outputs.
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args[0]
        prompt = call_args[0]
        self.assertIn("The difficulty level should be easy", prompt)

    @patch('create_class_projects._call_llm')
    def test_hard_level(self, mock_call_llm) -> None:
        """
        Test action with hard difficulty level.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_content = """
        # Advanced Lesson
        Complex content for hard projects.
        """
        test_content = hprint.dedent(test_content)
        input_file = os.path.join(scratch_dir, "test_input.md")
        output_file = os.path.join(scratch_dir, "test_output.txt")
        hio.to_file(input_file, test_content)
        
        mock_llm_response = "Hard projects content"
        mock_call_llm.return_value = mock_llm_response
        
        # Run test.
        crcpro._action_create_project(input_file, output_file, "hard")
        
        # Check outputs.
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args[0]
        prompt = call_args[0]
        self.assertIn("The difficulty level should be hard", prompt)

    @patch('create_class_projects._call_llm')
    def test_no_output_file_uses_default_name(self, mock_call_llm) -> None:
        """
        Test action when output file is None, uses default naming.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_content = "# Test content"
        input_file = os.path.join(scratch_dir, "lesson.md")
        hio.to_file(input_file, test_content)
        
        mock_llm_response = "Projects content"
        mock_call_llm.return_value = mock_llm_response
        
        # Change working directory to scratch dir to test default naming.
        original_cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            # Run test.
            crcpro._action_create_project(input_file, None, "medium")
            
            # Check outputs.
            expected_output = "lesson.projects.txt"
            self.assertTrue(os.path.exists(expected_output))
        finally:
            # Restore original working directory.
            os.chdir(original_cwd)


# #############################################################################
# Test_check_llm_available
# #############################################################################


class Test_check_llm_available(hunitest.TestCase):
    @patch('create_class_projects.hsystem.system')
    def test_llm_available(self, mock_system) -> None:
        """
        Test check when llm command is available.
        """
        # Prepare inputs.
        mock_system.return_value = None
        # Run test.
        crcpro._check_llm_available()
        # Check outputs.
        mock_system.assert_called_once_with("which llm", suppress_output=True)

    @patch('create_class_projects.hsystem.system')
    def test_llm_not_available(self, mock_system) -> None:
        """
        Test check when llm command is not available.
        """
        # Prepare inputs.
        mock_system.side_effect = Exception("Command not found")
        # Run test and check exception.
        with self.assertRaises(Exception):
            crcpro._check_llm_available()


# #############################################################################
# Test_action_find_packages
# #############################################################################


class Test_action_find_packages(hunitest.TestCase):
    
    @patch('create_class_projects._call_llm')
    def test_basic_find_packages(self, mock_call_llm) -> None:
        """
        Test find_packages action with basic input.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_content = """
        # Machine Learning Lesson
        
        This lesson covers pandas, numpy, and scikit-learn.
        
        ## Data Processing
        Content about data manipulation with pandas.
        """
        test_content = hprint.dedent(test_content)
        input_file = os.path.join(scratch_dir, "test_input.md")
        output_file = os.path.join(scratch_dir, "test_packages.txt")
        hio.to_file(input_file, test_content)
        
        mock_llm_response = """
        - Package: pandas
        - Description: Data manipulation library
        - Website: https://pandas.pydata.org
        - Documentation: https://pandas.pydata.org/docs
        """
        mock_call_llm.return_value = mock_llm_response
        
        # Run test.
        crcpro._action_find_packages(input_file, output_file)
        
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        result_content = hio.from_file(output_file)
        self.assertIn("# Related Python Packages", result_content)
        self.assertIn(mock_llm_response, result_content)
        
        # Verify LLM was called with correct prompt.
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args[0]
        prompt = call_args[0]
        content = call_args[1]
        self.assertIn("college level data science professor", prompt)
        self.assertIn("5 Python", prompt)
        self.assertIn("free packages", prompt)
        self.assertIn("Package:", prompt)
        self.assertIn("Description:", prompt)
        self.assertIn("Website:", prompt)
        self.assertIn("Documentation:", prompt)
        self.assert_equal(content, test_content)

    @patch('create_class_projects._call_llm')
    def test_no_output_file_uses_default_name(self, mock_call_llm) -> None:
        """
        Test find_packages action when output file is None, uses default naming.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_content = "# Data Science Lesson"
        input_file = os.path.join(scratch_dir, "lesson.md")
        hio.to_file(input_file, test_content)
        
        mock_llm_response = "Package suggestions"
        mock_call_llm.return_value = mock_llm_response
        
        # Change working directory to scratch dir to test default naming.
        original_cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            # Run test.
            crcpro._action_find_packages(input_file, None)
            
            # Check outputs.
            expected_output = "lesson.packages.txt"
            self.assertTrue(os.path.exists(expected_output))
            result_content = hio.from_file(expected_output)
            self.assertIn("# Related Python Packages", result_content)
            self.assertIn(mock_llm_response, result_content)
        finally:
            # Restore original working directory.
            os.chdir(original_cwd)

    @patch('create_class_projects._call_llm')
    def test_empty_content_file(self, mock_call_llm) -> None:
        """
        Test find_packages action with empty content file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_content = ""
        input_file = os.path.join(scratch_dir, "empty.md")
        output_file = os.path.join(scratch_dir, "packages.txt")
        hio.to_file(input_file, test_content)
        
        mock_llm_response = "No relevant packages found"
        mock_call_llm.return_value = mock_llm_response
        
        # Run test.
        crcpro._action_find_packages(input_file, output_file)
        
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args[0]
        content = call_args[1]
        self.assert_equal(content, test_content)