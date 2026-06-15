"""
Import as:

import helpers.test.test_hcheck_types as htthcty
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import helpers.hunit_test as hunitest

import helpers.hcheck_types as hchetype

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test helper functions used by the tests
# #############################################################################


def _add_ints(a: int, b: int) -> int:
    """
    Add two integers.
    """
    return a + b


def _greet(name: str, *, greeting: str = "Hello") -> str:
    """
    Format a greeting message.
    """
    return f"{greeting}, {name}!"


# #############################################################################
# Test_check_types_function
# #############################################################################


class Test_check_types_function(hunitest.TestCase):
    """
    Test the `check_types()` decorator on standalone functions.
    """

    def test1(self) -> None:
        """
        Test that a function with correct types passes validation.
        """
        # Prepare inputs.
        decorated = hchetype.check_types(_add_ints)
        # Prepare outputs.
        expected = 5
        # Run test.
        actual = decorated(2, 3)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that passing the wrong argument type raises `AssertionError`.
        """
        # Prepare inputs.
        decorated = hchetype.check_types(_add_ints)
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            decorated("not_an_int", 3)
        # Check outputs.
        actual = str(cm.exception)
        self.assertIn("'a' must be an instance of", actual)

    def test3(self) -> None:
        """
        Test that returning the wrong type raises `AssertionError`.

        We wrap a function whose return type hint is `int` but actually
        returns a string.
        """
        # Prepare inputs.

        @hchetype.check_types
        def _bad_return() -> int:
            return "not_an_int"

        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            _bad_return()
        # Check outputs.
        actual = str(cm.exception)
        self.assertIn("'return value' must be an instance of", actual)

    def test4(self) -> None:
        """
        Test that keyword arguments are type-checked.
        """
        # Prepare inputs.
        decorated = hchetype.check_types(_greet)
        # Prepare outputs.
        expected = "Hi, Alice!"
        # Run test.
        actual = decorated("Alice", greeting="Hi")
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_check_types_with_optional
# #############################################################################


class Test_check_types_with_optional(hunitest.TestCase):
    """
    Test the `check_types()` decorator with `Optional` type hints.
    """

    def test1(self) -> None:
        """
        Test that `None` is accepted for `Optional[int]`.
        """

        @hchetype.check_types
        def _optional_param(x: Optional[int]) -> Optional[int]:
            return x

        # Prepare inputs.
        # Prepare outputs.
        expected = None
        # Run test.
        actual = _optional_param(None)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that `None` is accepted for return type `Optional[str]`.
        """

        @hchetype.check_types
        def _optional_return(x: int) -> Optional[str]:
            if x > 0:
                return str(x)
            return None

        # Prepare inputs.
        # Prepare outputs.
        expected = None
        # Run test.
        actual = _optional_return(-1)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_check_types_with_collections
# #############################################################################


class Test_check_types_with_collections(hunitest.TestCase):
    """
    Test the `check_types()` decorator with collection type hints
    (List, Dict, Tuple).
    """

    def test1(self) -> None:
        """
        Test that `List[int]` accepts a list (origin-type check).
        """

        @hchetype.check_types
        def _sum_list(data: List[int]) -> int:
            return sum(data)

        # Prepare inputs.
        data = [1, 2, 3]
        # Prepare outputs.
        expected = 6
        # Run test.
        actual = _sum_list(data)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that `Dict[str, int]` accepts a dict (origin-type check).
        """

        @hchetype.check_types
        def _count_keys(data: Dict[str, int]) -> int:
            return len(data)

        # Prepare inputs.
        data = {"a": 1, "b": 2}
        # Prepare outputs.
        expected = 2
        # Run test.
        actual = _count_keys(data)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that passing a non-list to `List[int]` raises `AssertionError`.
        """

        @hchetype.check_types
        def _sum_list(data: List[int]) -> int:
            return sum(data)

        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            _sum_list("not_a_list")
        # Check outputs.
        actual = str(cm.exception)
        self.assertIn("'data' must be an instance of", actual)

    def test4(self) -> None:
        """
        Test that `Tuple[int, str]` accepts a tuple (origin-type check).
        """

        @hchetype.check_types
        def _process_pair(data: Tuple[int, str]) -> str:
            return f"{data[0]}: {data[1]}"

        # Prepare inputs.
        data = (42, "answer")
        # Prepare outputs.
        expected = "42: answer"
        # Run test.
        actual = _process_pair(data)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_check_types_with_any
# #############################################################################


class Test_check_types_with_any(hunitest.TestCase):
    """
    Test the `check_types()` decorator with `Any` type hints (should skip
    type checking).
    """

    def test1(self) -> None:
        """
        Test that `Any` parameter type hint skips type checking.
        """

        @hchetype.check_types
        def _identity(x: Any) -> Any:
            return x

        # Prepare inputs.
        # Prepare outputs.
        expected_int = 42
        expected_str = "hello"
        # Run test and check outputs.
        actual_int = _identity(42)
        self.assertEqual(actual_int, expected_int)
        actual_str = _identity("hello")
        self.assertEqual(actual_str, expected_str)

    def test2(self) -> None:
        """
        Test that a parameter without type hint is skipped.
        """

        @hchetype.check_types
        def _no_hint(x, y: int) -> int:
            hdbg = __import__("helpers.hdbg", fromlist=["hdbg"])
            hdbg.dassert_isinstance(y, int)
            return y

        # Prepare inputs.
        # Prepare outputs.
        expected = 42
        # Run test.
        actual = _no_hint("anything", 42)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_check_types_method
# #############################################################################


class Test_check_types_method(hunitest.TestCase):
    """
    Test the `check_types()` decorator on class methods.
    """

    def test1(self) -> None:
        """
        Test that the decorator works on instance methods (skips `self`).
        """

        class _Calculator:
            @hchetype.check_types
            def add(self, a: int, b: int) -> int:
                return a + b

        # Prepare inputs.
        calc = _Calculator()
        # Prepare outputs.
        expected = 5
        # Run test.
        actual = calc.add(2, 3)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that type mismatch on a method parameter raises `AssertionError`.
        """

        class _Calculator:
            @hchetype.check_types
            def add(self, a: int, b: int) -> int:
                return a + b

        # Prepare inputs.
        calc = _Calculator()
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            calc.add("bad", 3)
        # Check outputs.
        actual = str(cm.exception)
        self.assertIn("'a' must be an instance of", actual)

    def test3(self) -> None:
        """
        Test that the decorator works on static methods.
        """

        class _Utils:
            @staticmethod
            @hchetype.check_types
            def concat(a: str, b: str) -> str:
                return a + b

        # Prepare inputs.
        # Prepare outputs.
        expected = "helloworld"
        # Run test.
        actual = _Utils.concat("hello", "world")
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_check_types_union
# #############################################################################


class Test_check_types_union(hunitest.TestCase):
    """
    Test the `check_types()` decorator with `Union` type hints.
    """

    def test1(self) -> None:
        """
        Test that `Union[int, str]` accepts either type.
        """

        @hchetype.check_types
        def _to_string(x: Union[int, str]) -> str:
            return str(x)

        # Prepare inputs.
        # Prepare outputs.
        expected_int = "42"
        expected_str = "hello"
        # Run test and check outputs.
        actual_int = _to_string(42)
        self.assertEqual(actual_int, expected_int)
        actual_str = _to_string("hello")
        self.assertEqual(actual_str, expected_str)

    def test2(self) -> None:
        """
        Test that `Union[int, str]` rejects a mismatched type.
        """

        @hchetype.check_types
        def _to_string(x: Union[int, str]) -> str:
            return str(x)

        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            _to_string([1, 2, 3])
        # Check outputs.
        actual = str(cm.exception)
        self.assertIn("'x' must be one of types:", actual)
