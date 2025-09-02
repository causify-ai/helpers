import logging
import os
from unittest.mock import patch

import helpers.hunit_test as hunitest
import find_lesson_packages as flp

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_check_llm_available
# #############################################################################


class Test_check_llm_available(hunitest.TestCase):
    
    @patch('find_lesson_packages.hsystem.system')
    def test_llm_available(self, mock_system) -> None:
        """
        Test that _check_llm_available succeeds when llm command is found.
        """
        # Prepare inputs.
        # Mock hsystem.system to not raise exception (simulating llm found).
        mock_system.return_value = None
        # Run test.
        flp._check_llm_available()
        # Check outputs.
        # If no exception is raised, test passes.
        

    @patch('find_lesson_packages.hsystem.system')
    def test_llm_not_available(self, mock_system) -> None:
        """
        Test that _check_llm_available raises exception when llm command is not found.
        """
        # Prepare inputs.
        # Mock hsystem.system to raise exception (simulating llm not found).
        mock_system.side_effect = Exception("llm command not found")
        # Run test.
        with self.assertRaises(Exception):
            flp._check_llm_available()
        # Check outputs.
        # Exception should be raised.


# #############################################################################
# Test_call_llm
# #############################################################################


class Test_call_llm(hunitest.TestCase):
    
    @patch('find_lesson_packages.hsystem.system_to_string')
    @patch('find_lesson_packages.hio.to_file')
    def test_call_llm_success(self, mock_to_file, mock_system_to_string) -> None:
        """
        Test successful LLM call with expected prompt and content.
        """
        # Prepare inputs.
        prompt = "Test prompt"
        content = "Test content"
        expected_response = "Test response"
        # Mock system_to_string to return expected response.
        mock_system_to_string.return_value = (0, expected_response + "\n  ")
        mock_to_file.return_value = None
        # Run test.
        actual = flp._call_llm(prompt, content)
        # Check outputs.
        self.assert_equal(actual, expected_response)


# #############################################################################
# Test_find_packages
# #############################################################################


class Test_find_packages(hunitest.TestCase):
    
    def setUp(self) -> None:
        """
        Set up test environment.
        """
        # Create temporary directory for test files.
        self.temp_dir = self.get_scratch_space()
    
    @patch('find_lesson_packages._check_llm_available')
    @patch('find_lesson_packages._call_llm')
    def test_find_packages_with_output_file(self) -> None:
        """
        Test find_packages function with output file specified.
        """
        # Prepare inputs.
        input_content = """
        # Machine Learning Basics
        
        This lesson covers supervised learning algorithms.
        We will explore linear regression and decision trees.
        """
        input_file = os.path.join(self.temp_dir, "test_input.md")
        output_file = os.path.join(self.temp_dir, "test_output.txt")
        
        # Create input file.
        with open(input_file, 'w') as f:
            f.write(input_content)
        
        # Mock LLM response.
        mock_llm_response = """- Package: scikit-learn
- Description: Machine learning library
- Website: https://scikit-learn.org
- Documentation: https://scikit-learn.org/docs"""
        
        # Run test.
        with patch('find_lesson_packages._call_llm', return_value=mock_llm_response):
            result = flp.find_packages(input_file, output_file)
        
        # Check outputs.
        expected_result = """# Related Python Packages
- Package: scikit-learn
- Description: Machine learning library
- Website: https://scikit-learn.org
- Documentation: https://scikit-learn.org/docs

"""
        self.assert_equal(result, expected_result)
        
        # Check that output file was created with correct content.
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            file_content = f.read()
        self.assert_equal(file_content, expected_result)
    
    @patch('find_lesson_packages._check_llm_available')
    @patch('find_lesson_packages._call_llm')
    def test_find_packages_without_output_file(self) -> None:
        """
        Test find_packages function without output file specified.
        """
        # Prepare inputs.
        input_content = """
        # Data Analysis
        
        This lesson covers data visualization with matplotlib.
        """
        input_file = os.path.join(self.temp_dir, "test_input.md")
        
        # Create input file.
        with open(input_file, 'w') as f:
            f.write(input_content)
        
        # Mock LLM response.
        mock_llm_response = """- Package: matplotlib
- Description: Plotting library
- Website: https://matplotlib.org
- Documentation: https://matplotlib.org/docs"""
        
        # Run test.
        with patch('find_lesson_packages._call_llm', return_value=mock_llm_response):
            result = flp.find_packages(input_file)
        
        # Check outputs.
        expected_result = """# Related Python Packages
- Package: matplotlib
- Description: Plotting library
- Website: https://matplotlib.org
- Documentation: https://matplotlib.org/docs

"""
        self.assert_equal(result, expected_result)
    
    def test_find_packages_nonexistent_file(self) -> None:
        """
        Test find_packages function with nonexistent input file.
        """
        # Prepare inputs.
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.md")
        
        # Run test.
        with self.assertRaises(AssertionError):
            flp.find_packages(nonexistent_file)
        # Check outputs.
        # AssertionError should be raised due to file not existing.


# #############################################################################
# Test_parse
# #############################################################################


class Test_parse(hunitest.TestCase):
    
    def test_parse_required_args(self) -> None:
        """
        Test argument parser with required arguments.
        """
        # Prepare inputs.
        test_args = ["--in_file", "test.md"]
        
        # Run test.
        parser = flp._parse()
        args = parser.parse_args(test_args)
        
        # Check outputs.
        self.assert_equal(args.in_file, "test.md")
        self.assert_equal(args.output_file, None)
    
    def test_parse_all_args(self) -> None:
        """
        Test argument parser with all arguments.
        """
        # Prepare inputs.
        test_args = ["--in_file", "test.md", "--output_file", "output.txt", "-v", "DEBUG"]
        
        # Run test.
        parser = flp._parse()
        args = parser.parse_args(test_args)
        
        # Check outputs.
        self.assert_equal(args.in_file, "test.md")
        self.assert_equal(args.output_file, "output.txt")
        self.assert_equal(args.log_level, "DEBUG")