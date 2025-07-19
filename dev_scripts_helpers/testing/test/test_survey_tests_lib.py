#!/usr/bin/env python

"""
Unit tests for survey_tests_lib.py using test-driven approach.

Import as:

import test_survey_tests_lib as tsuteli
"""

import ast
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch

import helpers.hunit_test as hunitest
import survey_tests_lib as suteli


class TestTestMethodAnalyzer(hunitest.TestCase):
    """Test cases for TestMethodAnalyzer class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.analyzer = suteli.TestMethodAnalyzer()
    
    def test_analyze_method_not_skipped(self) -> None:
        """Test analyzing a non-skipped test method."""
        # Create AST node for: def test_something(self): pass
        method_code = "def test_something(self): pass"
        method_ast = ast.parse(method_code).body[0]
        
        expected = (False, "test_something")
        actual = self.analyzer.analyze_method(method_ast)
        
        self.assertEqual(actual, expected)
    
    def test_analyze_method_skipped_simple(self) -> None:
        """Test analyzing a test method with @pytest.mark.skip decorator."""
        # Create AST node for: @pytest.mark.skip\ndef test_something(self): pass
        method_code = """
@pytest.mark.skip
def test_something(self): pass
"""
        method_ast = ast.parse(method_code.strip()).body[0]
        
        expected = (True, "test_something")
        actual = self.analyzer.analyze_method(method_ast)
        
        self.assertEqual(actual, expected)
    
    def test_analyze_method_skipped_with_reason(self) -> None:
        """Test analyzing a test method with @pytest.mark.skip("reason") decorator."""
        # Create AST node for: @pytest.mark.skip("reason")\ndef test_something(self): pass
        method_code = """
@pytest.mark.skip("reason")
def test_something(self): pass
"""
        method_ast = ast.parse(method_code.strip()).body[0]
        
        expected = (True, "test_something")
        actual = self.analyzer.analyze_method(method_ast)
        
        self.assertEqual(actual, expected)
    
    def test_is_method_skipped_false(self) -> None:
        """Test is_method_skipped returns False for non-skipped method."""
        method_code = "def test_something(self): pass"
        method_ast = ast.parse(method_code).body[0]
        
        actual = self.analyzer.is_method_skipped(method_ast)
        
        self.assertFalse(actual)
    
    def test_is_method_skipped_true(self) -> None:
        """Test is_method_skipped returns True for skipped method."""
        method_code = """
@pytest.mark.skip
def test_something(self): pass
"""
        method_ast = ast.parse(method_code.strip()).body[0]
        
        actual = self.analyzer.is_method_skipped(method_ast)
        
        self.assertTrue(actual)


class TestTestClassAnalyzer(hunitest.TestCase):
    """Test cases for TestClassAnalyzer class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.method_analyzer = suteli.TestMethodAnalyzer()
        self.class_analyzer = suteli.TestClassAnalyzer(self.method_analyzer)
    
    def test_analyze_class_not_skipped(self) -> None:
        """Test analyzing a non-skipped test class."""
        class_code = """
class TestExample:
    def test_method1(self): pass
    def test_method2(self): pass
"""
        class_ast = ast.parse(class_code.strip()).body[0]
        
        class_info, methods_info = self.class_analyzer.analyze_class(class_ast)
        
        expected_class_info = (False, "TestExample")
        expected_methods_info = [
            (False, "test_method1"),
            (False, "test_method2")
        ]
        
        self.assertEqual(class_info, expected_class_info)
        self.assertEqual(methods_info, expected_methods_info)
    
    def test_analyze_class_skipped(self) -> None:
        """Test analyzing a skipped test class."""
        class_code = """
@pytest.mark.skip
class TestExample:
    def test_method1(self): pass
"""
        class_ast = ast.parse(class_code.strip()).body[0]
        
        class_info, methods_info = self.class_analyzer.analyze_class(class_ast)
        
        expected_class_info = (True, "TestExample")
        expected_methods_info = [(False, "test_method1")]
        
        self.assertEqual(class_info, expected_class_info)
        self.assertEqual(methods_info, expected_methods_info)
    
    def test_get_test_methods_filters_correctly(self) -> None:
        """Test get_test_methods only returns methods starting with 'test_'."""
        class_code = """
class TestExample:
    def test_method1(self): pass
    def helper_method(self): pass
    def test_method2(self): pass
    def setUp(self): pass
"""
        class_ast = ast.parse(class_code.strip()).body[0]
        
        test_methods = self.class_analyzer.get_test_methods(class_ast)
        method_names = [method.name for method in test_methods]
        
        expected_names = ["test_method1", "test_method2"]
        self.assertEqual(method_names, expected_names)
    
    def test_is_class_skipped_false(self) -> None:
        """Test is_class_skipped returns False for non-skipped class."""
        class_code = "class TestExample: pass"
        class_ast = ast.parse(class_code).body[0]
        
        actual = self.class_analyzer.is_class_skipped(class_ast)
        
        self.assertFalse(actual)
    
    def test_is_class_skipped_true(self) -> None:
        """Test is_class_skipped returns True for skipped class."""
        class_code = """
@pytest.mark.skip
class TestExample: pass
"""
        class_ast = ast.parse(class_code.strip()).body[0]
        
        actual = self.class_analyzer.is_class_skipped(class_ast)
        
        self.assertTrue(actual)


class TestTestFileAnalyzer(hunitest.TestCase):
    """Test cases for TestFileAnalyzer class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.method_analyzer = suteli.TestMethodAnalyzer()
        self.class_analyzer = suteli.TestClassAnalyzer(self.method_analyzer)
        self.file_analyzer = suteli.TestFileAnalyzer(self.class_analyzer)
    
    def test_analyze_file_single_class(self) -> None:
        """Test analyzing a file with a single test class."""
        file_content = '''
import pytest

class TestExample:
    def test_method1(self): pass
    
    @pytest.mark.skip
    def test_method2(self): pass
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(file_content)
            f.flush()
            
            result = self.file_analyzer.analyze_file(f.name)
            
        expected = {
            (False, "TestExample"): [
                (False, "test_method1"),
                (True, "test_method2")
            ]
        }
        
        self.assertEqual(result, expected)
    
    def test_analyze_file_multiple_classes(self) -> None:
        """Test analyzing a file with multiple test classes."""
        file_content = '''
import pytest

class TestFirst:
    def test_method1(self): pass

@pytest.mark.skip
class TestSecond:
    def test_method2(self): pass
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(file_content)
            f.flush()
            
            result = self.file_analyzer.analyze_file(f.name)
            
        expected = {
            (False, "TestFirst"): [(False, "test_method1")],
            (True, "TestSecond"): [(False, "test_method2")]
        }
        
        self.assertEqual(result, expected)
    
    def test_get_test_classes_filters_correctly(self) -> None:
        """Test get_test_classes only returns classes starting with 'Test'."""
        file_content = '''
class TestFirst: pass
class Helper: pass
class TestSecond: pass
class AnotherHelper: pass
'''
        ast_node = ast.parse(file_content)
        
        test_classes = self.file_analyzer.get_test_classes(ast_node)
        class_names = [cls.name for cls in test_classes]
        
        expected_names = ["TestFirst", "TestSecond"]
        self.assertEqual(class_names, expected_names)
    
    def test_parse_file_to_ast_valid_file(self) -> None:
        """Test parse_file_to_ast with valid Python file."""
        file_content = "class TestExample: pass"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(file_content)
            f.flush()
            
            ast_node = self.file_analyzer.parse_file_to_ast(f.name)
            
        self.assertIsInstance(ast_node, ast.Module)
        self.assertEqual(len(ast_node.body), 1)
        self.assertIsInstance(ast_node.body[0], ast.ClassDef)


class TestTestDirectorySurveyor(hunitest.TestCase):
    """Test cases for TestDirectorySurveyor class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.method_analyzer = suteli.TestMethodAnalyzer()
        self.class_analyzer = suteli.TestClassAnalyzer(self.method_analyzer)
        self.file_analyzer = suteli.TestFileAnalyzer(self.class_analyzer)
        self.surveyor = suteli.TestDirectorySurveyor(self.file_analyzer)
    
    def test_is_test_file_true_cases(self) -> None:
        """Test is_test_file returns True for test files."""
        test_cases = [
            "test_example.py",
            "test_something_else.py",
            "/path/to/test_file.py"
        ]
        
        for file_path in test_cases:
            with self.subTest(file_path=file_path):
                self.assertTrue(self.surveyor.is_test_file(file_path))
    
    def test_is_test_file_false_cases(self) -> None:
        """Test is_test_file returns False for non-test files."""
        test_cases = [
            "example.py",
            "something_test.py",  # Should start with test_
            "test_file.txt",      # Should be .py
            "__init__.py",
            "conftest.py"
        ]
        
        for file_path in test_cases:
            with self.subTest(file_path=file_path):
                self.assertFalse(self.surveyor.is_test_file(file_path))
    
    @patch('survey_tests_lib.hio')
    def test_find_test_directories(self, mock_hio) -> None:
        """Test find_test_directories finds directories named 'test'."""
        # Mock the directory structure
        mock_hio.listdir_recursive.return_value = [
            "/root/test",
            "/root/src/test", 
            "/root/lib/helpers/test",
            "/root/docs",
            "/root/src/main"
        ]
        
        result = self.surveyor.find_test_directories("/root")
        
        expected = [
            "/root/test",
            "/root/src/test",
            "/root/lib/helpers/test"
        ]
        
        self.assertEqual(result, expected)
    
    @patch('survey_tests_lib.hio')
    def test_find_test_files(self, mock_hio) -> None:
        """Test find_test_files finds Python test files."""
        # Mock files in test directory
        mock_hio.listdir.return_value = [
            "test_example.py",
            "test_another.py", 
            "helper.py",
            "__init__.py",
            "conftest.py"
        ]
        
        result = self.surveyor.find_test_files("/path/to/test")
        
        expected = [
            "/path/to/test/test_example.py",
            "/path/to/test/test_another.py"
        ]
        
        self.assertEqual(result, expected)


class TestFactoryFunctions(hunitest.TestCase):
    """Test cases for factory functions."""
    
    def test_create_test_surveyor(self) -> None:
        """Test create_test_surveyor creates proper instance."""
        surveyor = suteli.create_test_surveyor()
        
        self.assertIsInstance(surveyor, suteli.TestDirectorySurveyor)
        self.assertIsInstance(surveyor._file_analyzer, suteli.TestFileAnalyzer)
        self.assertIsInstance(surveyor._file_analyzer._class_analyzer, suteli.TestClassAnalyzer)
        self.assertIsInstance(surveyor._file_analyzer._class_analyzer._method_analyzer, suteli.TestMethodAnalyzer)
    
    @patch('survey_tests_lib.create_test_surveyor')
    def test_survey_tests_convenience_function(self, mock_create_surveyor) -> None:
        """Test survey_tests convenience function."""
        mock_surveyor = Mock()
        mock_surveyor.survey_directory.return_value = {"test_result": "data"}
        mock_create_surveyor.return_value = mock_surveyor
        
        result = suteli.survey_tests("/some/path")
        
        mock_create_surveyor.assert_called_once()
        mock_surveyor.survey_directory.assert_called_once_with("/some/path")
        self.assertEqual(result, {"test_result": "data"})


if __name__ == "__main__":
    unittest.main()