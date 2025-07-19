#!/usr/bin/env python

"""
Library for surveying test files in a codebase.

This module provides functionality to analyze test directories and extract
information about test classes and methods, including their skip status.

Import as:

import survey_tests_lib as suteli
"""

import logging
from typing import Dict, List, Tuple
from pathlib import Path

import helpers.hdbg as hdbg
import helpers.hio as hio

_LOG = logging.getLogger(__name__)

# #############################################################################
# Data structures
# #############################################################################

# Type aliases for the data structure
# file_map -> Tuple[is_skipped as bool, name of the test class] -> List[Tuple[is_skipped as bool, name of test methods]]
TestMethodInfo = Tuple[bool, str]  # (is_skipped, method_name)
TestClassInfo = Tuple[bool, str]   # (is_skipped, class_name)
TestFileMap = Dict[str, Dict[TestClassInfo, List[TestMethodInfo]]]


# #############################################################################
# Classes
# #############################################################################

class TestMethodAnalyzer:
    """
    Analyzes individual test methods to extract name and skip status.
    """
    
    def __init__(self) -> None:
        """Initialize the method analyzer."""
        pass
    
    def analyze_method(self, method_node) -> TestMethodInfo:
        """
        Analyze a single test method node to extract skip status and name.
        
        Args:
            method_node: AST node representing a test method
            
        Returns:
            Tuple of (is_skipped, method_name)
        """
        pass
    
    def is_method_skipped(self, method_node) -> bool:
        """
        Check if a method has pytest.mark.skip decorator.
        
        Args:
            method_node: AST node representing a test method
            
        Returns:
            True if method is decorated with pytest.mark.skip
        """
        pass


class TestClassAnalyzer:
    """
    Analyzes test classes to extract class information and contained methods.
    """
    
    def __init__(self, method_analyzer: TestMethodAnalyzer) -> None:
        """
        Initialize the class analyzer.
        
        Args:
            method_analyzer: Instance of TestMethodAnalyzer
        """
        self._method_analyzer = method_analyzer
    
    def analyze_class(self, class_node) -> Tuple[TestClassInfo, List[TestMethodInfo]]:
        """
        Analyze a single test class node to extract skip status, name, and methods.
        
        Args:
            class_node: AST node representing a test class
            
        Returns:
            Tuple of (class_info, methods_info)
        """
        pass
    
    def is_class_skipped(self, class_node) -> bool:
        """
        Check if a class has pytest.mark.skip decorator.
        
        Args:
            class_node: AST node representing a test class
            
        Returns:
            True if class is decorated with pytest.mark.skip
        """
        pass
    
    def get_test_methods(self, class_node) -> List:
        """
        Extract all test methods from a class node.
        
        Args:
            class_node: AST node representing a test class
            
        Returns:
            List of AST nodes representing test methods
        """
        pass


class TestFileAnalyzer:
    """
    Analyzes individual test files to extract all test classes and methods.
    """
    
    def __init__(self, class_analyzer: TestClassAnalyzer) -> None:
        """
        Initialize the file analyzer.
        
        Args:
            class_analyzer: Instance of TestClassAnalyzer
        """
        self._class_analyzer = class_analyzer
    
    def analyze_file(self, file_path: str) -> Dict[TestClassInfo, List[TestMethodInfo]]:
        """
        Analyze a single test file to extract all test classes and methods.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            Dictionary mapping test class info to list of method info
        """
        pass
    
    def parse_file_to_ast(self, file_path: str):
        """
        Parse a Python file into an AST.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            AST node representing the file
        """
        pass
    
    def get_test_classes(self, ast_node) -> List:
        """
        Extract all test classes from an AST node.
        
        Args:
            ast_node: AST node representing the parsed file
            
        Returns:
            List of AST nodes representing test classes
        """
        pass


class TestDirectorySurveyor:
    """
    Main class for surveying test directories and building the complete test map.
    """
    
    def __init__(self, file_analyzer: TestFileAnalyzer) -> None:
        """
        Initialize the directory surveyor.
        
        Args:
            file_analyzer: Instance of TestFileAnalyzer
        """
        self._file_analyzer = file_analyzer
    
    def survey_directory(self, root_dir: str = ".") -> TestFileMap:
        """
        Survey a directory tree to build complete test map.
        
        Args:
            root_dir: Root directory to start searching from
            
        Returns:
            Complete test file map
        """
        pass
    
    def find_test_directories(self, root_dir: str) -> List[str]:
        """
        Find all directories named 'test' in the directory tree.
        
        Args:
            root_dir: Root directory to search
            
        Returns:
            List of paths to test directories
        """
        pass
    
    def find_test_files(self, test_dir: str) -> List[str]:
        """
        Find all Python test files in a test directory.
        
        Args:
            test_dir: Path to test directory
            
        Returns:
            List of paths to test files
        """
        pass
    
    def is_test_file(self, file_path: str) -> bool:
        """
        Check if a file is a test file based on naming conventions.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file appears to be a test file
        """
        pass


# #############################################################################
# Factory functions
# #############################################################################

def create_test_surveyor() -> TestDirectorySurveyor:
    """
    Create a fully configured TestDirectorySurveyor instance.
    
    Returns:
        Configured TestDirectorySurveyor instance
    """
    method_analyzer = TestMethodAnalyzer()
    class_analyzer = TestClassAnalyzer(method_analyzer)
    file_analyzer = TestFileAnalyzer(class_analyzer)
    return TestDirectorySurveyor(file_analyzer)


def survey_tests(root_dir: str = ".") -> TestFileMap:
    """
    Convenience function to survey tests in a directory.
    
    Args:
        root_dir: Root directory to start searching from
        
    Returns:
        Complete test file map
    """
    surveyor = create_test_surveyor()
    return surveyor.survey_directory(root_dir)