#!/usr/bin/env python

"""
Unit tests for survey_tests_lib.py using test-driven approach.

Import as:

import test_survey_tests_lib as tsuteli
"""

import ast
import os
import tempfile
import unittest
from unittest.mock import Mock, patch


import helpers.hunit_test as hunitest
import helpers.hio as hio
import dev_scripts_helpers.testing.survey_tests_lib as suteli
import helpers.hprint as hprint


# #############################################################################
# TestTestMethodAnalyzer
# #############################################################################



def get_ast(code: str) -> ast.AST:
    """
    Get the AST for a method.
    """
    code = hprint.dedent(code)
    return ast.parse(code).body[0]


class TestTestMethodAnalyzer(hunitest.TestCase):
    """
    Test cases for TestMethodAnalyzer class.
    """

    def test_analyze_method_not_skipped(self) -> None:
        """
        Test analyzing a non-skipped test method.
        """
        # Prepare inputs.
        code = """
        def test_something(self):
            pass
        """
        ast = get_ast(code)
        analyzer = suteli.TestMethodAnalyzer()
        # Run test.
        actual = analyzer.analyze_method(ast)
        # Check outputs.
        expected = (False, "test_something")
        self.assert_equal(str(actual), str(expected))

    def test_analyze_method_skipped_simple(self) -> None:
        """
        Test analyzing a test method with @pytest.mark.skip decorator.
        """
        # Prepare inputs.
        code = """
        @pytest.mark.skip
        def test_something(self):
            pass
        """
        ast = get_ast(code)
        analyzer = suteli.TestMethodAnalyzer()
        # Run test.
        actual = analyzer.analyze_method(ast)
        # Check outputs.
        expected = (True, "test_something")
        self.assert_equal(str(actual), str(expected))

    def test_analyze_method_skipped_with_reason(self) -> None:
        """
        Test analyzing a test method with @pytest.mark.skip("reason")
        decorator.
        """
        # Prepare inputs.
        code = """
        @pytest.mark.skip("reason")
        def test_something(self):
            pass
        """
        ast = get_ast(code)
        analyzer = suteli.TestMethodAnalyzer()
        # Run test.
        actual = analyzer.analyze_method(ast)
        # Check outputs.
        expected = (True, "test_something")
        self.assert_equal(str(actual), str(expected))

    def test_is_method_skipped_false(self) -> None:
        """
        Test is_method_skipped returns False for non-skipped method.
        """
        # Prepare inputs.
        code = """
        def test_something(self):
            pass
        """
        ast = get_ast(code)
        analyzer = suteli.TestMethodAnalyzer()
        # Run test.
        actual = analyzer.is_method_skipped(ast)
        # Check outputs.
        self.assertFalse(actual)

    def test_is_method_skipped_true(self) -> None:
        """
        Test is_method_skipped returns True for skipped method.
        """
        # Prepare inputs.
        code = """
        @pytest.mark.skip
        def test_something(self):
            pass
        """
        ast = get_ast(code)
        analyzer = suteli.TestMethodAnalyzer()
        # Run test.
        actual = analyzer.is_method_skipped(ast)
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# TestTestClassAnalyzer
# #############################################################################


class TestTestClassAnalyzer(hunitest.TestCase):
    """
    Test cases for TestClassAnalyzer class.
    """

    def test_analyze_class_not_skipped(self) -> None:
        """
        Test analyzing a non-skipped test class.
        """
        # Prepare inputs.
        code = """
        class TestExample:
            def test_method1(self):
                pass
            def test_method2(self):
                pass
        """
        ast = get_ast(code)
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        # Run test.
        class_info, methods_info = class_analyzer.analyze_class(ast)
        # Check outputs.
        expected_class_info = (False, "TestExample")
        self.assert_equal(str(class_info), str(expected_class_info))
        expected_methods_info = [(False, "test_method1"), (False, "test_method2")]
        self.assert_equal(str(methods_info), str(expected_methods_info))

    def test_analyze_class_skipped(self) -> None:
        """
        Test analyzing a skipped test class.
        """
        # Prepare inputs.
        code = """
        @pytest.mark.skip
        class TestExample:
            def test_method1(self): pass
        """
        ast = get_ast(code)
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        # Run test.
        class_info, methods_info = class_analyzer.analyze_class(ast)
        # Check outputs.
        expected_class_info = (True, "TestExample")
        self.assert_equal(str(class_info), str(expected_class_info))
        expected_methods_info = [(False, "test_method1")]
        self.assert_equal(str(methods_info), str(expected_methods_info))

    def test_get_test_methods_filters_correctly(self) -> None:
        """
        Test get_test_methods only returns methods starting with 'test_'.
        """
        # Prepare inputs.
        code = """
        class TestExample:
            def test_method1(self):
                pass

            def helper_method(self):
                pass

            def test_method2(self):
                pass

            def setUp(self):
                pass
        """
        ast = get_ast(code)
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        # Run test.
        test_methods = class_analyzer.get_test_methods(ast)
        method_names = [method.name for method in test_methods]
        # Check outputs.
        expected_names = ["test_method1", "test_method2"]
        self.assert_equal(str(method_names), str(expected_names))

    def test_is_class_skipped_false(self) -> None:
        """
        Test is_class_skipped returns False for non-skipped class.
        """
        # Prepare inputs.
        code = """
        class TestExample:
            pass
        """
        ast = get_ast(code)
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        # Run test.
        actual = class_analyzer.is_class_skipped(ast)
        # Check outputs.
        self.assertFalse(actual)

    def test_is_class_skipped_true(self) -> None:
        """
        Test is_class_skipped returns True for skipped class.
        """
        # Prepare inputs.
        code = """
        @pytest.mark.skip
        class TestExample: pass
        """
        ast = get_ast(code)
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        # Run test.
        actual = class_analyzer.is_class_skipped(ast)
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# TestTestFileAnalyzer
# #############################################################################


class TestTestFileAnalyzer(hunitest.TestCase):
    """
    Test cases for TestFileAnalyzer class.
    """


    def test_analyze_file_single_class(self) -> None:
        """
        Test analyzing a file with a single test class.
        """
        # Prepare inputs.
        file_content = """
        import pytest

        # #############################################################################
        # TestExample
        # #############################################################################

        class TestExample:
            def test_method1(self):
                pass

            @pytest.mark.skip
            def test_method2(self):
                pass
        """
        # Run test.
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        file_name = os.path.join(
            self.get_scratch_space(),
            "temp.py")
        hio.to_file(file_name, file_content)
        result = file_analyzer.analyze_file(file_name)
        # Check outputs.
        expected = {
            (False, "TestExample"): [
                (False, "test_method1"),
                (True, "test_method2"),
            ]
        }
        self.assert_equal(str(result), str(expected))

    def test_analyze_file_multiple_classes(self) -> None:
        """
        Test analyzing a file with multiple test classes.
        """
        # Prepare inputs.
        file_content = """
        import pytest

        class TestFirst:
            def test_method1(self):
                pass


        @pytest.mark.skip
        class TestSecond:
            def test_method2(self):
                pass
        """
        # Run test.
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        file_name = os.path.join(
            self.get_scratch_space(),
            "temp.py")
        hio.to_file(file_name, file_content)
        result = file_analyzer.analyze_file(file_name)
        # Check outputs.
        expected = {
            (False, "TestFirst"): [(False, "test_method1")],
            (True, "TestSecond"): [(False, "test_method2")],
        }
        self.assert_equal(str(result), str(expected))

    def test_get_test_classes_filters_correctly(self) -> None:
        """
        Test get_test_classes only returns classes starting with 'Test'.
        """
        # Prepare inputs.
        file_content = """
        class TestFirst:
            pass

        class Helper:
            pass

        class TestSecond:
            pass

        class AnotherHelper:
            pass
        """
        file_content = hprint.dedent(file_content)
        ast_node = ast.parse(file_content)
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        # Run test.
        test_classes = file_analyzer.get_test_classes(ast_node)
        class_names = [cls.name for cls in test_classes]
        # Check outputs.
        expected_names = ["TestFirst", "TestSecond"]
        self.assert_equal(str(class_names), str(expected_names))

    def test_parse_file_to_ast_valid_file(self) -> None:
        """
        Test parse_file_to_ast with valid Python file.
        """
        # Prepare inputs.
        file_content = """
        class TestExample:
            pass
        """
        # Run test.
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        file_name = os.path.join(
            self.get_scratch_space(),
            "temp.py")
        hio.to_file(file_name, file_content)
        ast_node = file_analyzer.parse_file_to_ast(file_name)
        # Check outputs.
        self.assertIsInstance(ast_node, ast.Module)
        self.assert_equal(str(len(ast_node.body)), str(1))
        self.assertIsInstance(ast_node.body[0], ast.ClassDef)


# #############################################################################
# TestTestDirectorySurveyor
# #############################################################################


class TestTestDirectorySurveyor(hunitest.TestCase):
    """
    Test cases for TestDirectorySurveyor class.
    """


    def test_is_test_file_true_cases(self) -> None:
        """
        Test is_test_file returns True for test files.
        """
        # Prepare inputs.
        test_cases = [
            "test_example.py",
            "test_something_else.py",
            "/path/to/test_file.py",
        ]
        # Run test.
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        surveyor = suteli.TestDirectorySurveyor(file_analyzer)
        for file_path in test_cases:
            with self.subTest(file_path=file_path):
                # Check outputs.
                self.assertTrue(surveyor.is_test_file(file_path))

    def test_is_test_file_false_cases(self) -> None:
        """
        Test is_test_file returns False for non-test files.
        """
        # Prepare inputs.
        test_cases = [
            "example.py",
            "something_test.py",  # Should start with test_
            "test_file.txt",  # Should be .py
            "__init__.py",
            "conftest.py",
        ]
        # Run test.
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        surveyor = suteli.TestDirectorySurveyor(file_analyzer)
        for file_path in test_cases:
            with self.subTest(file_path=file_path):
                # Check outputs.
                self.assertFalse(surveyor.is_test_file(file_path))

    @patch("dev_scripts_helpers.testing.survey_tests_lib.hio")
    def test_find_test_directories(self, mock_hio) -> None:
        """
        Test find_test_directories finds directories named 'test'.
        """
        # Prepare inputs.
        mock_hio.listdir_recursive.return_value = [
            "/root/test",
            "/root/src/test",
            "/root/lib/helpers/test",
            "/root/docs",
            "/root/src/main",
        ]
        # Run test.
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        surveyor = suteli.TestDirectorySurveyor(file_analyzer)
        result = surveyor.find_test_directories("/root")
        # Check outputs.
        expected = ["/root/test", "/root/src/test", "/root/lib/helpers/test"]
        self.assert_equal(str(result), str(expected))

    @patch("dev_scripts_helpers.testing.survey_tests_lib.hio")
    def test_find_test_files(self, mock_hio) -> None:
        """
        Test find_test_files finds Python test files.
        """
        # Prepare inputs.
        mock_hio.listdir.return_value = [
            "test_example.py",
            "test_another.py",
            "helper.py",
            "__init__.py",
            "conftest.py",
        ]
        # Run test.
        method_analyzer = suteli.TestMethodAnalyzer()
        class_analyzer = suteli.TestClassAnalyzer(method_analyzer)
        file_analyzer = suteli.TestFileAnalyzer(class_analyzer)
        surveyor = suteli.TestDirectorySurveyor(file_analyzer)
        result = surveyor.find_test_files("/path/to/test")
        # Check outputs.
        expected = [
            "/path/to/test/test_example.py",
            "/path/to/test/test_another.py",
        ]
        self.assert_equal(str(result), str(expected))


# #############################################################################
# TestFactoryFunctions
# #############################################################################


class TestFactoryFunctions(hunitest.TestCase):
    """
    Test cases for factory functions.
    """

    def test_create_test_surveyor(self) -> None:
        """
        Test create_test_surveyor creates proper instance.
        """
        # Run test.
        surveyor = suteli.create_test_surveyor()
        # Check outputs.
        self.assertIsInstance(surveyor, suteli.TestDirectorySurveyor)
        self.assertIsInstance(surveyor._file_analyzer, suteli.TestFileAnalyzer)
        self.assertIsInstance(
            surveyor._file_analyzer._class_analyzer, suteli.TestClassAnalyzer
        )
        self.assertIsInstance(
            surveyor._file_analyzer._class_analyzer._method_analyzer,
            suteli.TestMethodAnalyzer,
        )

    @patch("dev_scripts_helpers.testing.survey_tests_lib.create_test_surveyor")
    def test_survey_tests_convenience_function(
        self, mock_create_surveyor
    ) -> None:
        """
        Test survey_tests convenience function.
        """
        # Prepare inputs.
        mock_surveyor = Mock()
        mock_surveyor.survey_directory.return_value = {"test_result": "data"}
        mock_create_surveyor.return_value = mock_surveyor
        # Run test.
        result = suteli.survey_tests("/some/path")
        # Check outputs.
        mock_create_surveyor.assert_called_once()
        mock_surveyor.survey_directory.assert_called_once_with("/some/path")
        self.assert_equal(str(result), str({"test_result": "data"}))
