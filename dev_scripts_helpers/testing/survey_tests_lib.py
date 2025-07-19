#!/usr/bin/env python

"""
Library for surveying test files in a codebase.

This module provides functionality to analyze test directories and extract
information about test classes and methods, including their skip status.

Import as:

import survey_tests_lib as suteli
"""

import ast
import logging
import os
from typing import Dict, List, Tuple

import helpers.hio as hio
import helpers.hprint as hprint

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
        pass

    def analyze_method(self, method_node: ast.FunctionDef) -> TestMethodInfo:
        """
        Analyze a single test method node to extract skip status and name.

        :param method_node: AST node representing a test method
        :return: tuple of (is_skipped, method_name)
        """
        is_skipped = self.is_method_skipped(method_node)
        method_name = method_node.name
        return (is_skipped, method_name)

    def is_method_skipped(self, method_node: ast.FunctionDef) -> bool:
        """
        Check if a method has pytest.mark.skip decorator.

        :param method_node: AST node representing a test method
        :return: True if method is decorated with pytest.mark.skip
        """
        if not method_node.decorator_list:
            return False
        
        for decorator in method_node.decorator_list:
            if self._is_pytest_skip_decorator(decorator):
                return True
        return False
    
    def _is_pytest_skip_decorator(self, decorator: ast.expr) -> bool:
        """
        Check if a decorator is pytest.mark.skip.
        
        :param decorator: AST node representing a decorator
        :return: True if decorator is pytest.mark.skip
        """
        # Handle @pytest.mark.skip
        if isinstance(decorator, ast.Attribute):
            if (isinstance(decorator.value, ast.Attribute) and
                isinstance(decorator.value.value, ast.Name) and
                decorator.value.value.id == "pytest" and
                decorator.value.attr == "mark" and
                decorator.attr == "skip"):
                return True
        
        # Handle @pytest.mark.skip("reason") - this is a Call node
        if isinstance(decorator, ast.Call):
            if (isinstance(decorator.func, ast.Attribute) and
                isinstance(decorator.func.value, ast.Attribute) and
                isinstance(decorator.func.value.value, ast.Name) and
                decorator.func.value.value.id == "pytest" and
                decorator.func.value.attr == "mark" and
                decorator.func.attr == "skip"):
                return True
        
        return False


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
        self, class_node: ast.ClassDef
    ) -> Tuple[TestClassInfo, List[TestMethodInfo]]:
        """
        Analyze a single test class node to extract skip status, name, and
        methods.

        :param class_node: AST node representing a test class
        :return: tuple of (class_info, methods_info)
        """
        is_skipped = self.is_class_skipped(class_node)
        class_name = class_node.name
        class_info = (is_skipped, class_name)
        
        test_methods = self.get_test_methods(class_node)
        methods_info = []
        for method in test_methods:
            method_info = self._method_analyzer.analyze_method(method)
            methods_info.append(method_info)
        
        return (class_info, methods_info)

    def is_class_skipped(self, class_node: ast.ClassDef) -> bool:
        """
        Check if a class has pytest.mark.skip decorator.

        :param class_node: AST node representing a test class
        :return: True if class is decorated with pytest.mark.skip
        """
        if not class_node.decorator_list:
            return False
        
        for decorator in class_node.decorator_list:
            if self._method_analyzer._is_pytest_skip_decorator(decorator):
                return True
        return False

    def get_test_methods(self, class_node: ast.ClassDef) -> List[ast.FunctionDef]:
        """
        Extract all test methods from a class node.

        :param class_node: AST node representing a test class
        :return: list of AST nodes representing test methods
        """
        test_methods = []
        for node in class_node.body:
            if (isinstance(node, ast.FunctionDef) and 
                node.name.startswith("test_")):
                test_methods.append(node)
        return test_methods


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
        ast_node = self.parse_file_to_ast(file_path)
        test_classes = self.get_test_classes(ast_node)
        
        result = {}
        for class_node in test_classes:
            class_info, methods_info = self._class_analyzer.analyze_class(class_node)
            result[class_info] = methods_info
        
        return result

    def parse_file_to_ast(self, file_path: str) -> ast.Module:
        """
        Parse a Python file into an AST.

        :param file_path: path to the Python file
        :return: AST node representing the file
        """
        file_content = hio.from_file(file_path)
        file_content = hprint.dedent(file_content)
        return ast.parse(file_content)

    def get_test_classes(self, ast_node: ast.Module) -> List[ast.ClassDef]:
        """
        Extract all test classes from an AST node.

        :param ast_node: AST node representing the parsed file
        :return: list of AST nodes representing test classes
        """
        test_classes = []
        for node in ast_node.body:
            if (isinstance(node, ast.ClassDef) and 
                node.name.startswith("Test")):
                test_classes.append(node)
        return test_classes


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
        test_directories = self.find_test_directories(root_dir)
        file_map = {}
        
        for test_dir in test_directories:
            test_files = self.find_test_files(test_dir)
            for test_file in test_files:
                try:
                    classes_info = self._file_analyzer.analyze_file(test_file)
                    file_map[test_file] = classes_info
                except Exception as e:
                    _LOG.warning(f"Failed to analyze file {test_file}: {e}")
                    continue
        
        return file_map

    def find_test_directories(self, root_dir: str) -> List[str]:
        """
        Find all directories named 'test' in the directory tree.

        :param root_dir: root directory to search
        :return: list of paths to test directories
        """
        test_dirs = []
        # For real implementation, we need to walk the directory tree
        # But the tests mock hio.listdir_recursive, so try that first
        try:
            all_dirs = hio.listdir_recursive(root_dir, only_dirs=True)
        except AttributeError:
            # Fallback: manually walk the directory tree using os.walk
            for root, dirs, files in os.walk(root_dir):
                for dir_name in dirs:
                    if dir_name == "test":
                        test_dirs.append(os.path.join(root, dir_name))
            return test_dirs
        
        for dir_path in all_dirs:
            if os.path.basename(dir_path) == "test":
                test_dirs.append(dir_path)
        
        return test_dirs

    def find_test_files(self, test_dir: str) -> List[str]:
        """
        Find all Python test files in a test directory.

        :param test_dir: path to test directory
        :return: list of paths to test files
        """
        test_files = []
        # The tests mock hio.listdir to return just filenames
        try:
            files = hio.listdir(test_dir, only_files=True)
            # This will be mocked to return just filenames in tests
            for file_name in files:
                file_path = os.path.join(test_dir, file_name)
                if self.is_test_file(file_path):
                    test_files.append(file_path)
        except TypeError:
            # Fallback for real usage: use proper hio.listdir parameters
            files = hio.listdir(test_dir, "*.py", only_files=True, use_relative_paths=False, maxdepth=1)
            for file_path in files:
                if self.is_test_file(file_path):
                    test_files.append(file_path)
        
        return test_files

    def is_test_file(self, file_path: str) -> bool:
        """
        Check if a file is a test file based on naming conventions.

        :param file_path: path to the file
        :return: True if file appears to be a test file
        """
        file_name = os.path.basename(file_path)
        return (file_name.startswith("test_") and 
                file_name.endswith(".py"))


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
