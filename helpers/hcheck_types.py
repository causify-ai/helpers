"""
Import as:

import helpers.hcheck_types as hchecty
"""

import functools
import inspect
import logging
import typing
from typing import Any, Callable, TypeVar, Union, cast

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# Type variable for the decorated function.
F = TypeVar("F", bound=Callable[..., Any])

# Changelog:
# - v0.1 (2026-06-13): Initial implementation

# #############################################################################
# Private helpers
# #############################################################################


def _check_value_type(
    value: Any,
    expected_type: Any,
    name: str,
) -> None:
    """
    Check that a value matches an expected type hint using `hdbg.dassert_isinstance()`.

    Handles parameterized generics by extracting the origin type (e.g.,
    `List[int]` becomes `list`), and expands `Union` types (including
    `Optional`) into a tuple of acceptable types. Skips checking when
    the type hint is `Any`.

    :param value: The value to check
    :param expected_type: The expected type from the type hint
    :param name: Name of the parameter or "return value" for error messages
    """
    # Skip checking if the type hint is `Any`.
    if expected_type is Any:
        return
    # Get the origin type for parameterized generics.
    origin = typing.get_origin(expected_type)
    if origin is not None:
        # Handle Union types (including Optional).
        if origin is Union:
            type_args = typing.get_args(expected_type)
            hdbg.dassert_isinstance(
                value,
                type_args,
                "'%s' must be one of types: %s",
                name,
                type_args,
            )
            return
        # For other generics (List, Dict, Tuple, etc.), check the origin.
        hdbg.dassert_isinstance(
            value,
            origin,
            "'%s' must be an instance of '%s', got '%s'",
            name,
            origin,
            type(value).__name__,
        )
        return
    # For simple types, check directly.
    hdbg.dassert_isinstance(
        value,
        expected_type,
        "'%s' must be an instance of '%s', got '%s'",
        name,
        expected_type,
        type(value).__name__,
    )


# #############################################################################
# check_types decorator
# #############################################################################


def check_types(func: F) -> F:
    """
    Decorator that checks argument and return types at runtime.

    Uses Python's type hints via `typing.get_type_hints()` and function
    signature introspection via `inspect.signature()` to enforce type
    correctness. Before calling the decorated function, checks that all
    arguments match their type hints. After the function returns, checks
    that the return value matches the return type hint.

    :param func: The function to decorate
    :return: The wrapped function with runtime type checking
    """
    # Resolve type hints, including forward references (string annotations).
    type_hints = typing.get_type_hints(func)
    # Get the function signature for argument binding.
    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Bind caller arguments to parameter names.
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        # Check each argument's type against its type hint.
        for param_name, param_value in bound_args.arguments.items():
            # Skip `self` and `cls` parameters for methods.
            if param_name in ("self", "cls"):
                continue
            if param_name in type_hints:
                expected_type = type_hints[param_name]
                _check_value_type(param_value, expected_type, param_name)
        # Execute the wrapped function.
        result = func(*args, **kwargs)
        # Check return type hint if present.
        if "return" in type_hints:
            return_type = type_hints["return"]
            # Skip checking if the return type is NoneType (function returns None).
            if return_type is not type(None):
                _check_value_type(result, return_type, "return value")
        return result

    return cast(F, wrapper)
