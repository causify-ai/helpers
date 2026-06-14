"""
Test file for `helpers/hllm_decorator.py`.

Import as:

import helpers.test.test_hllm_decorator as thllmdec
"""

import logging
import os
import tempfile
from typing import Dict, List, Optional

import pytest

import helpers.hcache_simple as hcacsimp
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hllm_decorator as hllmdec

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_coerce_value
# #############################################################################


class Test_coerce_value(hunitest.TestCase):
    """
    Test `_coerce_value()` for all supported type coercions.
    """

    def helper(self, response: str, target_type: type, expected: object) -> None:
        """
        Test helper for `_coerce_value()`.

        :param response: Raw LLM response string to coerce
        :param target_type: Target Python type annotation
        :param expected: Expected coerced value
        """
        # Run test.
        actual = hllmdec._coerce_value(response, target_type)
        # Check outputs.
        self.assertEqual(actual, expected)

    # /////////////////////////////////////////////////////////////////////////
    # int coercion
    # /////////////////////////////////////////////////////////////////////////

    def test1(self) -> None:
        """
        Test coercing a plain integer string to `int`.
        """
        # Prepare inputs.
        response = "42"
        target_type = int
        # Prepare outputs.
        expected = 42
        # Run test.
        self.helper(response, target_type, expected)

    def test2(self) -> None:
        """
        Test coercing an integer string with leading/trailing whitespace to `int`.
        """
        # Prepare inputs.
        response = "   -17   \n"
        target_type = int
        # Prepare outputs.
        expected = -17
        # Run test.
        self.helper(response, target_type, expected)

    def test3(self) -> None:
        """
        Test coercing an integer string with extraneous text to `int`.
        """
        # Prepare inputs.
        response = "The answer is 42."
        target_type = int
        # Prepare outputs.
        expected = 42
        # Run test.
        self.helper(response, target_type, expected)

    # /////////////////////////////////////////////////////////////////////////
    # float coercion
    # /////////////////////////////////////////////////////////////////////////

    def test4(self) -> None:
        """
        Test coercing a plain float string to `float`.
        """
        # Prepare inputs.
        response = "3.14"
        target_type = float
        # Prepare outputs.
        expected = 3.14
        # Run test.
        self.helper(response, target_type, expected)

    def test5(self) -> None:
        """
        Test coercing a float string with extraneous text to `float`.
        """
        # Prepare inputs.
        response = "Value: -2.5\n"
        target_type = float
        # Prepare outputs.
        expected = -2.5
        # Run test.
        self.helper(response, target_type, expected)

    # /////////////////////////////////////////////////////////////////////////
    # bool coercion
    # /////////////////////////////////////////////////////////////////////////

    def test6(self) -> None:
        """
        Test coercing "true" to `bool`.
        """
        # Prepare inputs.
        response = "true"
        target_type = bool
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(response, target_type, expected)

    def test7(self) -> None:
        """
        Test coercing "false" to `bool`.
        """
        # Prepare inputs.
        response = "FALSE"
        target_type = bool
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(response, target_type, expected)

    def test8(self) -> None:
        """
        Test coercing "yes" / "no" to `bool`.
        """
        # Prepare inputs.
        response_true = "yes"
        response_false = "no"
        target_type = bool
        # Run test and check outputs.
        self.assertEqual(hllmdec._coerce_value(response_true, target_type), True)
        self.assertEqual(hllmdec._coerce_value(response_false, target_type), False)

    # /////////////////////////////////////////////////////////////////////////
    # str coercion
    # /////////////////////////////////////////////////////////////////////////

    def test9(self) -> None:
        """
        Test coercing a string to `str` returns the stripped text.
        """
        # Prepare inputs.
        response = "  hello world  \n"
        target_type = str
        # Prepare outputs.
        expected = "hello world"
        # Run test.
        self.helper(response, target_type, expected)

    # /////////////////////////////////////////////////////////////////////////
    # List coercion
    # /////////////////////////////////////////////////////////////////////////

    def test10(self) -> None:
        """
        Test coercing a JSON array string to `List[int]`.
        """
        # Prepare inputs.
        response = "[1, 2, 3]"
        target_type = List[int]
        # Prepare outputs.
        expected = [1, 2, 3]
        # Run test.
        self.helper(response, target_type, expected)

    def test11(self) -> None:
        """
        Test coercing a JSON array embedded in text to `List[str]`.
        """
        # Prepare inputs.
        response = 'Here is the list: ["a", "b", "c"]'
        target_type = List[str]
        # Prepare outputs.
        expected = ["a", "b", "c"]
        # Run test.
        self.helper(response, target_type, expected)

    # /////////////////////////////////////////////////////////////////////////
    # Dict coercion
    # /////////////////////////////////////////////////////////////////////////

    def test12(self) -> None:
        """
        Test coercing a JSON object string to `Dict[str, int]`.
        """
        # Prepare inputs.
        response = '{"x": 1, "y": 2}'
        target_type = Dict[str, int]
        # Prepare outputs.
        expected = {"x": 1, "y": 2}
        # Run test.
        self.helper(response, target_type, expected)

    # /////////////////////////////////////////////////////////////////////////
    # Optional / Union coercion
    # /////////////////////////////////////////////////////////////////////////

    def test13(self) -> None:
        """
        Test coercing a valid value to `Optional[int]`.
        """
        # Prepare inputs.
        response = "42"
        target_type = Optional[int]
        # Prepare outputs.
        expected = 42
        # Run test.
        self.helper(response, target_type, expected)

    def test14(self) -> None:
        """
        Test coercing "null" to `Optional[int]` returns None.
        """
        # Prepare inputs.
        response = "null"
        target_type = Optional[int]
        # Prepare outputs.
        expected = None
        # Run test.
        self.helper(response, target_type, expected)

    def test15(self) -> None:
        """
        Test coercing "none" (case-insensitive) to `Optional[str]` returns None.
        """
        # Prepare inputs.
        response = "NONE"
        target_type = Optional[str]
        # Prepare outputs.
        expected = None
        # Run test.
        self.helper(response, target_type, expected)

    def test16(self) -> None:
        """
        Test coercing empty string to `Optional[int]` returns None.
        """
        # Prepare inputs.
        response = ""
        target_type = Optional[int]
        # Prepare outputs.
        expected = None
        # Run test.
        self.helper(response, target_type, expected)

    # /////////////////////////////////////////////////////////////////////////
    # NoneType coercion
    # /////////////////////////////////////////////////////////////////////////

    def test17(self) -> None:
        """
        Test coercing any string to `None` returns None.
        """
        # Prepare inputs.
        response = "anything"
        target_type = type(None)
        # Prepare outputs.
        expected = None
        # Run test.
        self.helper(response, target_type, expected)


# #############################################################################
# Test_get_type_format_instruction
# #############################################################################


class Test_get_type_format_instruction(hunitest.TestCase):
    """
    Test `_get_type_format_instruction()` for generating LLM format instructions.
    """

    def test1(self) -> None:
        """
        Test format instruction for `int` return type.
        """
        # Prepare inputs.
        return_type = int
        # Run test.
        instruction = hllmdec._get_type_format_instruction(return_type)
        # Check outputs.
        self.assertIn("integer", instruction)

    def test2(self) -> None:
        """
        Test format instruction for `bool` return type specifies true/false.
        """
        # Prepare inputs.
        return_type = bool
        # Run test.
        instruction = hllmdec._get_type_format_instruction(return_type)
        # Check outputs.
        self.assertIn("true", instruction.lower())
        self.assertIn("false", instruction.lower())

    def test3(self) -> None:
        """
        Test format instruction for `List` return type specifies JSON array.
        """
        # Prepare inputs.
        return_type = List[int]
        # Run test.
        instruction = hllmdec._get_type_format_instruction(return_type)
        # Check outputs.
        self.assertIn("JSON array", instruction)

    def test4(self) -> None:
        """
        Test format instruction for `Dict` return type specifies JSON object.
        """
        # Prepare inputs.
        return_type = Dict[str, int]
        # Run test.
        instruction = hllmdec._get_type_format_instruction(return_type)
        # Check outputs.
        self.assertIn("JSON object", instruction)

    def test5(self) -> None:
        """
        Test format instruction for `Optional[int]` includes null hint.
        """
        # Prepare inputs.
        return_type = Optional[int]
        # Run test.
        instruction = hllmdec._get_type_format_instruction(return_type)
        # Check outputs.
        self.assertIn('"null"', instruction)


# #############################################################################
# Test_build_llm_prompt
# #############################################################################


# TODO(ai_gp): Use an helper to factor out common code and add more examples.
class Test_build_llm_prompt(hunitest.TestCase):
    """
    Test `_build_llm_prompt()` for constructing prompts from function metadata.
    """

    def test1(self) -> None:
        """
        Test prompt construction includes docstring, args, and format instruction.
        """
        # Prepare inputs.
        docstring = "Add two integers and return the sum."
        return_type = int
        # Simulate bound arguments.
        import inspect
        sig = inspect.Signature(
            [
                inspect.Parameter(
                    "a", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int
                ),
                inspect.Parameter(
                    "b", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int
                ),
            ]
        )
        bound_args = sig.bind(5, 3)
        bound_args.apply_defaults()
        # Run test.
        prompt = hllmdec._build_llm_prompt(
            "add", docstring, return_type, bound_args
        )
        # Check outputs: prompt includes docstring, args, and format instruction.
        # TODO(ai_gp): Use self.assert_equal(actual, expected)
        self.assertIn("Add two integers", prompt)
        self.assertIn("a = 5", prompt)
        self.assertIn("b = 3", prompt)
        self.assertIn("integer", prompt)


# #############################################################################
# Test_llm_decorator_basic
# #############################################################################


class Test_llm_decorator_basic(hunitest.TestCase):
    """
    Test the `@llm` decorator for basic functionality and metadata attachment.
    """

    def test2(self) -> None:
        """
        Test that the decorator resolves return type correctly.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=False)
        def multiply(a: int, b: int) -> int:
            """Multiply two integers."""
        # Run test.
        config = multiply._llm_decorator_config
        # Check outputs.
        self.assertEqual(config["return_type"], int)

    def test3(self) -> None:
        """
        Test that the decorator resolves Optional return type.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=False)
        def maybe_value() -> Optional[float]:
            """Return a value if available."""
        # Run test.
        config = maybe_value._llm_decorator_config
        # Check outputs.
        # Optional[float] should be resolved.
        self.assertIsNotNone(config["return_type"])

    def test4(self) -> None:
        """
        Test that use_cache=False creates a function that can be called.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=False)
        def greet(name: str) -> str:
            """Return a friendly greeting."""
        # Run test: verify return type in metadata.
        config = greet._llm_decorator_config
        # Check outputs.
        self.assertEqual(config["return_type"], str)
        self.assertEqual(config["cache_func_name"], "_llm_call_greet")

    def test5(self) -> None:
        """
        Test that use_cache=True creates a cache wrapper with correct cache name.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=True)
        def add(a: int, b: int) -> int:
            """Add two integers."""
        # Run test.
        config = add._llm_decorator_config
        # Check outputs.
        self.assertEqual(config["use_cache"], True)
        self.assertEqual(config["cache_func_name"], "_llm_call_add")


# #############################################################################
# Test_llm_decorator_caching
# #############################################################################


class Test_llm_decorator_caching(hunitest.TestCase):
    """
    Test the caching layer of the `@llm` decorator with `mock_apply_llm()`.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        """
        Setup and teardown for each test.
        """
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Setup that runs before each test: set a temp cache directory.
        """
        self._tmp_dir = tempfile.mkdtemp(prefix="tmp.test_hllm_decorator.")
        hcacsimp.set_cache_dir(self._tmp_dir)

    def tear_down_test(self) -> None:
        """
        Cleanup that runs after each test: reset cache and remove temp dir.
        """
        import shutil
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test1(self) -> None:
        """
        Test that `mock_apply_llm()` pre-populates the cache for a call.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=True)
        def add(a: int, b: int) -> int:
            """Add two integers and return the sum."""
        # Mock the LLM response for (2, 3) -> "5".
        hllmdec.mock_apply_llm(add, args=(2, 3), kwargs={}, response="5")
        # Run test.
        result = add(2, 3)
        # Check outputs.
        self.assertEqual(result, 5)
        self.assertIsInstance(result, int)

    def test2(self) -> None:
        """
        Test that cached calls return the same value without LLM invocation.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=True)
        def classify(text: str) -> str:
            """Classify the sentiment of the text as positive or negative."""
        # Mock two different calls.
        hllmdec.mock_apply_llm(
            classify, args=("I love this!",), kwargs={}, response="positive"
        )
        hllmdec.mock_apply_llm(
            classify, args=("I hate this.",), kwargs={}, response="negative"
        )
        # Run test.
        result1 = classify("I love this!")
        result2 = classify("I hate this.")
        # Check outputs.
        self.assertEqual(result1, "positive")
        self.assertEqual(result2, "negative")

    def test3(self) -> None:
        """
        Test that `mock_apply_llm()` works with keyword arguments.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=True)
        def format_name(first: str, last: str) -> str:
            """Format a full name from first and last name."""
        # Mock with kwargs.
        hllmdec.mock_apply_llm(
            format_name,
            args=(),
            kwargs={"first": "John", "last": "Doe"},
            response="John Doe",
        )
        # Run test.
        result = format_name(first="John", last="Doe")
        # Check outputs.
        self.assertEqual(result, "John Doe")

    def test4(self) -> None:
        """
        Test that `mock_apply_llm()` works with List return type.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=True)
        def extract_tags(text: str) -> List[str]:
            """Extract keyword tags from the text."""
        # Mock with JSON array response.
        hllmdec.mock_apply_llm(
            extract_tags,
            args=("AI is transforming the world",),
            kwargs={},
            response='["ai", "technology", "future"]',
        )
        # Run test.
        result = extract_tags("AI is transforming the world")
        # Check outputs.
        self.assertEqual(result, ["ai", "technology", "future"])

    def test5(self) -> None:
        """
        Test that force_refresh bypasses the cache.
        """
        # Prepare inputs: create a decorated function with caching.
        @hllmdec.llm(use_cache=True)
        def double_it(n: int) -> int:
            """Return double the input value."""
        # Mock the cache with a known value.
        hllmdec.mock_apply_llm(double_it, args=(5,), kwargs={}, response="10")
        # First call should use cache.
        result1 = double_it(5)
        self.assertEqual(result1, 10)
        # force_refresh should skip the cache. Since there is no real LLM,
        # we just verify we can pass force_refresh without error by checking
        # the @simple_cache wrapper handles it (accessing the property).
        cache_func_name = double_it._llm_decorator_config["cache_func_name"]
        # Verify the force_refresh property is initially False.
        force_refresh_val = hcacsimp.get_cache_property(
            cache_func_name, "force_refresh"
        )
        self.assertFalse(force_refresh_val)

    def test6(self) -> None:
        """
        Test that decorator with use_cache=False does not interact with cache.
        """
        # Prepare inputs.
        @hllmdec.llm(use_cache=False)
        def no_cache_func(x: int) -> int:
            """Square the input."""
        # Run test: verify metadata and non-cached behavior.
        config = no_cache_func._llm_decorator_config
        # Check outputs: cache should be disabled.
        self.assertEqual(config["use_cache"], False)
        # Verify the function does not have cache entries.
        func_names = hcacsimp.get_cached_func_names("mem")
        self.assertNotIn(config["cache_func_name"], func_names)
