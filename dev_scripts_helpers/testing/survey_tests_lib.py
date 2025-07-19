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

_LOG = logging.getLogger(__name__)

# #############################################################################
# Data structures
# #############################################################################

# Type aliases for the data structure
# file_map -> Tuple[is_skipped as bool, name of the test class] -> List[Tuple[is_skipped as bool, name of test methods]]
TestMethodInfo = Tuple[bool, str]  # (is_skipped, method_name)
TestClassInfo = Tuple[bool, str]  # (is_skipped, class_name)
TestFileMap = Dict[str, Dict[TestClassInfo, List[TestMethodInfo]]]


# #############################################################################
# TestMethodAnalyzer
# #############################################################################


# TODO(ai): Rename this to UnitTestMethodAnalyzer.
class TestMethodAnalyzer:
    """
    Analyzes individual test methods to extract name and skip status.
    """

    def __init__(self) -> None:
        """
        Initialize the method analyzer.
        """

    def analyze_method(self, method_node) -> TestMethodInfo:
        """
        Analyze a single test method node to extract skip status and name.

        :param method_node: AST node representing a test method
        :return: tuple of (is_skipped, method_name)
        """

    def is_method_skipped(self, method_node) -> bool:
        """
        Check if a method has pytest.mark.skip decorator.

        :param method_node: AST node representing a test method
        :return: True if method is decorated with pytest.mark.skip
        """


# #############################################################################
# TestClassAnalyzer
# #############################################################################


# TODO(ai): Rename this to UnitTestClassAnalyzer.
class TestClassAnalyzer:
    """
    Analyzes test classes to extract class information and contained methods.
    """

    def __init__(self, method_analyzer: TestMethodAnalyzer) -> None:
        """
        Initialize the class analyzer.

        :param method_analyzer: instance of TestMethodAnalyzer
        """
        self._method_analyzer = method_analyzer

    def analyze_class(
        self, class_node
    ) -> Tuple[TestClassInfo, List[TestMethodInfo]]:
        """
        Analyze a single test class node to extract skip status, name, and
        methods.

        :param class_node: AST node representing a test class
        :return: tuple of (class_info, methods_info)
        """

    def is_class_skipped(self, class_node) -> bool:
        """
        Check if a class has pytest.mark.skip decorator.

        :param class_node: AST node representing a test class
        :return: True if class is decorated with pytest.mark.skip
        """

    def get_test_methods(self, class_node) -> List:
        """
        Extract all test methods from a class node.

        :param class_node: AST node representing a test class
        :return: list of AST nodes representing test methods
        """


# #############################################################################
# TestFileAnalyzer
# #############################################################################


# TODO(ai): Rename this to UnitTestFileAnalyzer.
class TestFileAnalyzer:
    """
    Analyzes individual test files to extract all test classes and methods.
    """

    def __init__(self, class_analyzer: TestClassAnalyzer) -> None:
        """
        Initialize the file analyzer.

        :param class_analyzer: instance of TestClassAnalyzer
        """
        self._class_analyzer = class_analyzer

    def analyze_file(
        self, file_path: str
    ) -> Dict[TestClassInfo, List[TestMethodInfo]]:
        """
        Analyze a single test file to extract all test classes and methods.

        :param file_path: path to the test file
        :return: dictionary mapping test class info to list of method info
        """

    def parse_file_to_ast(self, file_path: str):
        """
        Parse a Python file into an AST.

        :param file_path: path to the Python file
        :return: AST node representing the file
        """

    def get_test_classes(self, ast_node) -> List:
        """
        Extract all test classes from an AST node.

        :param ast_node: AST node representing the parsed file
        :return: list of AST nodes representing test classes
        """


# #############################################################################
# TestDirectorySurveyor
# #############################################################################


# TODO(ai): Rename this to UnitTestDirectorySurveyor.
class TestDirectorySurveyor:
    """
    Main class for surveying test directories and building the complete test
    map.
    """

    def __init__(self, file_analyzer: TestFileAnalyzer) -> None:
        """
        Initialize the directory surveyor.

        :param file_analyzer: instance of TestFileAnalyzer
        """
        self._file_analyzer = file_analyzer

    def survey_directory(self, root_dir: str = ".") -> TestFileMap:
        """
        Survey a directory tree to build complete test map.

        :param root_dir: root directory to start searching from
        :return: complete test file map
        """

    def find_test_directories(self, root_dir: str) -> List[str]:
        """
        Find all directories named 'test' in the directory tree.

        :param root_dir: root directory to search
        :return: list of paths to test directories
        """

    def find_test_files(self, test_dir: str) -> List[str]:
        """
        Find all Python test files in a test directory.

        :param test_dir: path to test directory
        :return: list of paths to test files
        """

    def is_test_file(self, file_path: str) -> bool:
        """
        Check if a file is a test file based on naming conventions.

        :param file_path: path to the file
        :return: True if file appears to be a test file
        """


# #############################################################################
# Factory functions
# #############################################################################


def create_test_surveyor() -> TestDirectorySurveyor:
    """
    Create a fully configured TestDirectorySurveyor instance.

    :return: configured TestDirectorySurveyor instance
    """
    method_analyzer = TestMethodAnalyzer()
    class_analyzer = TestClassAnalyzer(method_analyzer)
    file_analyzer = TestFileAnalyzer(class_analyzer)
    return TestDirectorySurveyor(file_analyzer)


def survey_tests(root_dir: str = ".") -> TestFileMap:
    """
    Convenience function to survey tests in a directory.

    :param root_dir: root directory to start searching from
    :return: complete test file map
    """
    surveyor = create_test_surveyor()
    return surveyor.survey_directory(root_dir)
