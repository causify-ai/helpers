"""
Import as:

import helpers.hllm_decorator as hllmdeco
"""

import functools
import hashlib
import inspect
import json
import logging
import re
import typing
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hllm as hllm
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): Add a set_model / get_model to set a global model to be
# used when calling this code unless it's specified in the function

# #############################################################################
# Constants
# #############################################################################

# Regex pattern to extract the first JSON array from a string response.
_JSON_ARRAY_PATTERN = re.compile(r"\[.*\]", re.DOTALL)
# Regex pattern to extract the first JSON object from a string response.
_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


# #############################################################################
# Private helpers.
# #############################################################################


# Mapping from Python types to prompt instruction fragments that tell the LLM
# how to format its output for a given return type.
_TYPE_FORMAT_INSTRUCTIONS: Dict[Any, str] = {
    int: "Return ONLY a single integer number, no other text.",
    float: "Return ONLY a single floating-point number, no other text.",
    bool: 'Return ONLY "true" or "false", no other text.',
    str: "Return ONLY the requested string value, no extra commentary.",
}


def _get_type_format_instruction(return_type: Any) -> str:
    """
    Build a format instruction string for the LLM prompt based on return type.

    The instruction tells the LLM exactly how to format its response so that
    the post-processing coercion step can parse it reliably.

    :param return_type: The return type annotation from the function signature
    :return: A format instruction string to append to the LLM prompt
    """
    # Check for simple types in the format map.
    if return_type in _TYPE_FORMAT_INSTRUCTIONS:
        return _TYPE_FORMAT_INSTRUCTIONS[return_type]
    # Handle typing generics.
    origin = typing.get_origin(return_type)
    if origin is list or origin is List:
        # List[...] -> return a JSON array.
        return "Return ONLY a valid JSON array, no other text."
    if origin is dict or origin is Dict:
        # Dict[...] -> return a JSON object.
        return "Return ONLY a valid JSON object, no other text."
    if origin is Union:
        # Handle Optional (Union[X, None]) and general unions.
        type_args = typing.get_args(return_type)
        non_none_args = [t for t in type_args if t is not type(None)]
        if len(non_none_args) == 1:
            # Optional[X] -> recurse with the inner type.
            inner_type = non_none_args[0]
            return _get_type_format_instruction(inner_type) + (
                ' If the answer is not available, return "null".'
            )
        # General Union: instruct JSON output as the safest format.
        return "Return ONLY the result, no other text."
    # Fallback for unrecognized types.
    return "Return ONLY the result, no other text."


# TODO(gp): Add a mode strict to make sure the input is 1-1 with something
# that can be coerced (e.g., not removing invalid chars).
def _coerce_value(response: str, target_type: Any) -> Any:
    """
    Parse a raw LLM response string into the target Python type.

    Handles:
    - simple types (`int`, `float`, `bool`, `str`)
    - JSON containers (`List`, `Dict`)
    - `Optional` / `Union` types by walking the type tree and attempting
      successive coercions.

    :param response: Raw text response from the LLM
    :param target_type: The target Python type annotation
    :return: The parsed value coerced to `target_type`
    """
    hdbg.dassert_isinstance(response, str)
    # Normalize whitespace.
    stripped = response.strip()
    # Handle NoneType early: "null" or empty string maps to None.
    if target_type is type(None):
        return None
    # If the target type is str, return as-is.
    if target_type is str:
        return stripped
    # Handle typing generics: extract the origin type.
    origin = typing.get_origin(target_type)
    # --- Union / Optional ---
    if origin is Union:
        type_args = typing.get_args(target_type)
        # Check for NoneType first: "null", "none", or empty string -> None.
        lowered = stripped.lower()
        if lowered in ("null", "none", "") and type(None) in type_args:
            return None
        # Try each union branch in order, returning the first that succeeds.
        for candidate_type in type_args:
            if candidate_type is type(None):
                continue
            try:
                return _coerce_value(stripped, candidate_type)
            except (ValueError, json.JSONDecodeError, TypeError):
                pass
        raise ValueError(
            "Could not coerce '%s' to any type in union %s"
            % (stripped, type_args)
        )
    # --- List ---
    if origin is list or origin is List:
        # Try to extract and parse a JSON array from the response.
        match = _JSON_ARRAY_PATTERN.search(stripped)
        json_str = match.group(0) if match else stripped
        parsed = json.loads(json_str)
        hdbg.dassert_isinstance(
            parsed, list, "Expected JSON array, got %s", type(parsed).__name__
        )
        # Recurse into element type if specified.
        type_args = typing.get_args(target_type)
        if type_args:
            element_type = type_args[0]
            # For str elements, use them directly since json.loads already
            # returns native strings. For other types, serialize back to
            # JSON to re-parse via the coercion pipeline.
            if element_type is str:
                parsed = [str(e) for e in parsed]
            else:
                parsed = [
                    _coerce_value(json.dumps(e), element_type) for e in parsed
                ]
        return parsed
    # --- Dict ---
    if origin is dict or origin is Dict:
        match = _JSON_OBJECT_PATTERN.search(stripped)
        json_str = match.group(0) if match else stripped
        parsed = json.loads(json_str)
        hdbg.dassert_isinstance(
            parsed, dict, "Expected JSON object, got %s", type(parsed).__name__
        )
        return parsed
    # --- Simple types ---
    # Simple coercions raise ValueError (not AssertionError) so they can be
    # caught by the Union handler above.
    if target_type is int:
        # Remove any non-numeric characters except minus sign and digits.
        cleaned = re.sub(r"[^0-9\-]", "", stripped)
        if cleaned == "":
            raise ValueError("No integer found in response '%s'" % stripped)
        return int(cleaned)
    if target_type is float:
        # Remove any non-numeric characters except minus, digits, and dot.
        cleaned = re.sub(r"[^0-9\.\-]", "", stripped)
        if cleaned == "":
            raise ValueError("No float found in response '%s'" % stripped)
        return float(cleaned)
    if target_type is bool:
        lowered = stripped.lower()
        if lowered in ("true", "yes", "1"):
            return True
        if lowered in ("false", "no", "0"):
            return False
        raise ValueError("Cannot coerce '%s' to bool" % stripped)
    # Fallback: return the raw string.
    hdbg.dassert_eq(
        target_type,
        str,
        "Unsupported type for coercion: %s",
        target_type,
    )
    return stripped


def _build_llm_prompt(
    func_name: str,
    docstring: str,
    return_type: Any,
    bound_args: inspect.BoundArguments,
) -> str:
    """
    Build the complete LLM prompt from a function's metadata and arguments.

    The prompt consists of:
    1. A task description from the function docstring
    2. The function arguments as key-value pairs
    3. Format instructions derived from the return type annotation

    :param func_name: Name of the decorated function
    :param docstring: Docstring of the decorated function (the task description)
    :param return_type: The return type annotation
    :param bound_args: The bound arguments from the function call
    :return: A complete prompt string to send to the LLM
    """
    prompt_parts: List[str] = []
    # Add the task description from the docstring.
    prompt_parts.append(docstring)
    prompt_parts.append("")
    # Add the input arguments as key-value pairs.
    prompt_parts.append("Input:")
    for param_name, param_value in bound_args.arguments.items():
        # Format each argument as `param_name = value`.
        prompt_parts.append("  %s = %s" % (param_name, repr(param_value)))
    prompt_parts.append("")
    # Add format instruction based on the return type.
    format_instr = _get_type_format_instruction(return_type)
    prompt_parts.append(format_instr)
    # Join into a single prompt string.
    prompt = "\n".join(prompt_parts)
    return prompt


def _compute_callable_hash(func: Callable, model: str) -> str:
    """
    Compute a stable hash over the function source and model.

    This hash is used as a cache-key fragment so that cached results
    automatically invalidate when the function body or model changes.

    Falls back to using the function name if the source code is not
    available (e.g., for dynamically-defined functions in interactive
    environments).

    :param func: The decorated function
    :param model: The LLM model name
    :return: A 32-character MD5 hex digest
    """
    try:
        source = inspect.getsource(func)
    except OSError:
        # Fall back to the qualified name when source is not available
        # (e.g., in interactive sessions or for dynamically-defined functions).
        source = "%s.%s" % (
            getattr(func, "__module__", ""),
            getattr(func, "__qualname__", func.__name__),
        )
    payload = source + "||" + model
    return hashlib.md5(payload.encode()).hexdigest()


# #############################################################################
# Core @llm decorator.
# #############################################################################


def llm(
    *,
    use_cache: bool = True,
    model: str = "",
    system_prompt: str = "",
    temperature: float = 0.1,
) -> Callable:
    r"""
    Decorator that transforms a type-annotated function stub into an LLM call.

    The decorated function body is replaced: instead of executing the
    function body, the decorator constructs a prompt from the docstring
    and the call arguments, sends it to an LLM via `hllm.get_completion()`,
    and coerces the response to match the function's return type annotation.

    When `use_cache=True` (the default), the raw LLM responses are cached
    on disk via `hcache_simple.simple_cache`. Repeated calls with identical
    arguments skip the LLM entirely.

    Usage:

    ```
    @hllmdec.llm()
    def summarize(text: str) -> str:
        \"""
        Summarize the given text in one sentence.
        \"""

    result = summarize("Long article text here...")
    ```

    :param use_cache: If True, cache LLM responses via `simple_cache`
    :param model: LLM model to use (empty string for default)
    :param system_prompt: System prompt to use (empty string for default)
    :param temperature: Temperature for LLM sampling
    :return: A decorator that transforms the function stub
    """

    def decorator(func: Callable) -> Callable:
        # Record the function source hash for cache invalidation.
        func_name = getattr(func, "__name__", "unknown_function")
        _LOG.debug(
            "Decorating '%s' with @llm (use_cache=%s, model='%s')",
            func_name,
            use_cache,
            model,
        )
        # Resolve type hints once at decoration time.
        type_hints = typing.get_type_hints(func)
        return_type = type_hints.get("return", str)
        # Capture the function signature for argument binding.
        sig = inspect.signature(func)
        # Build the function source hash for cache-key construction.
        func_source_hash = _compute_callable_hash(func, model)
        # Construct a unique cache function name that incorporates the user
        # function name so that multiple @llm-decorated functions have
        # independent caches.
        cache_func_name = "_llm_call_%s" % func_name

        # Define the core operation that calls the LLM.
        # This inner function is wrapped with @simple_cache when caching is
        # enabled so that identical calls avoid redundant LLM invocations.
        def _make_llm_call(
            prompt: str,
        ) -> str:
            """
            Call the LLM and return the raw text response.

            This function is separated so it can be independently cached
            by `@simple_cache` without caching the coercion step.

            :param prompt: The constructed user prompt
            :return: Raw text response from the LLM
            """
            _LOG.debug(
                "Calling LLM for '%s' with model='%s'",
                func_name,
                model,
            )
            response = hllm.get_completion(
                prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
            )
            return response

        # Set the function name for the cache so it is unique per user
        # function.
        _make_llm_call.__name__ = cache_func_name
        # Optionally wrap with caching.
        if use_cache:
            _call_llm = hcacsimp.simple_cache(
                cache_type="json",
                write_through=True,
                cache_prefix="tmp.cache_llm_decorator",
            )(_make_llm_call)
        else:
            _call_llm = _make_llm_call

        @functools.wraps(func)
        def wrapper(
            *args: Any,
            force_refresh: bool = False,
            **kwargs: Any,
        ) -> Any:
            """
            Execute the LLM-backed function.

            :param args: Positional arguments matching the original signature
            :param force_refresh: If True, bypass cache for this call
            :param kwargs: Keyword arguments matching the original signature
            :return: The LLM response coerced to the declared return type
            """
            # Bind the caller's arguments to the function signature.
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            # Build the prompt from the docstring, args, and return type.
            docstring = (func.__doc__ or "").strip()
            prompt = _build_llm_prompt(
                func_name, docstring, return_type, bound_args
            )
            _LOG.debug(
                "Built prompt for '%s':\n%s",
                func_name,
                hprint.indent(prompt),
            )
            # Call the LLM (with or without caching).
            # Pass force_refresh only when caching is enabled (the @simple_cache
            # wrapper accepts it as a keyword argument).
            if use_cache:
                raw_response = _call_llm(prompt, force_refresh=force_refresh)
            else:
                raw_response = _call_llm(prompt)
            _LOG.debug(
                "Raw LLM response for '%s': '%s'", func_name, raw_response
            )
            # Coerce the raw response to the declared return type.
            coerced = _coerce_value(raw_response, return_type)
            return coerced

        # Attach metadata for introspection and tooling.
        wrapper._llm_decorator_config = {
            "use_cache": use_cache,
            "model": model,
            "temperature": temperature,
            "system_prompt": system_prompt,
            "return_type": return_type,
            "func_source_hash": func_source_hash,
            "cache_func_name": cache_func_name,
        }
        # Store the original function for reference.
        wrapper._llm_decorator_original_func = func
        return wrapper

    return decorator


# #############################################################################
# Convenience: mock LLM responses for testing.
# #############################################################################


def mock_apply_llm(
    func: Callable,
    *,
    args: Tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
    response: str = "",
) -> None:
    """
    Pre-populate the cache for a specific `@llm`-decorated function call.

    This allows tests to inject expected LLM responses without actually
    calling an LLM. The next time the decorated function is called with
    the same arguments, the cached response is returned.

    :param func: The `@llm`-decorated function whose cache to mock
    :param args: Positional arguments that identify the call
    :param kwargs: Keyword arguments that identify the call
    :param response: The raw text response to inject as the LLM output

    Example usage in tests:

    ```
    import helpers.hllm_decorator as hllmdec

    @hllmdec.llm()
    def add(a: int, b: int) -> int:
        \"""Add two integers.\"""

    # Pre-populate the cache with an expected LLM response.
    hllmdec.mock_apply_llm(add, args=(2, 3), kwargs={}, response="5")
    # The call returns 5 without hitting the LLM.
    result = add(2, 3)
    ```
    """
    if kwargs is None:
        kwargs = {}
    hdbg.dassert_isinstance(args, tuple, "args must be a tuple")
    hdbg.dassert_isinstance(kwargs, dict, "kwargs must be a dict")
    hdbg.dassert_isinstance(response, str)
    # Retrieve the original undecorated function and the cache function name
    # from the @llm wrapper metadata.
    hdbg.dassert(
        hasattr(func, "_llm_decorator_config"),
        "Function '%s' is not decorated with @llm",
        getattr(func, "__name__", str(func)),
    )
    original_func = func._llm_decorator_original_func
    cache_func_name = func._llm_decorator_config["cache_func_name"]
    # Build the prompt that would be generated for these arguments.
    type_hints = typing.get_type_hints(original_func)
    return_type = type_hints.get("return", str)
    sig = inspect.signature(original_func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()
    docstring = (original_func.__doc__ or "").strip()
    func_name = getattr(original_func, "__name__", "unknown_function")
    prompt = _build_llm_prompt(func_name, docstring, return_type, bound_args)
    # Mock the cache for the LLM-call function so that a subsequent call to
    # the decorated function returns the injected response.
    hcacsimp.mock_cache_from_args_kwargs(
        cache_func_name, (prompt,), {}, response
    )
    _LOG.debug(
        "Mocked LLM response for '%s' with args=%s kwargs=%s: '%s'",
        func_name,
        args,
        kwargs,
        response,
    )
