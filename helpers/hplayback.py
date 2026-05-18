"""
Code to record and replay function calls, and to automatically generate unit
tests for functions.

Import as:

import helpers.hplayback as hplayba
"""

import functools
import inspect
import json
import logging
import os
import unittest.mock as umock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import jsonpickle  # type: ignore
import jsonpickle.ext.pandas as jepand  # type: ignore
import pandas as pd

import config_root.config as cconfig
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint

jepand.register_handlers()

_LOG = logging.getLogger(__name__)


# TODO(gp): Use repr to serialize:
# >>> a = {"hello": [1, 2, (3, 4)]}
# >>> repr(a)
# "{'hello': [1, 2, (3, 4)]}"
# TODO(gp): Add more types.
# TODO(gp): -> _to_python_code
def to_python_code(obj: Any) -> str:
    """
    Serialize an object into a string of Python code.

    :param obj: an object to serialize
    :return: a string of Python code building the object
    """
    output = []
    if isinstance(obj, (int, float)):
        # Float 2.5 -> "2.5".
        output.append(str(obj))
    elif isinstance(obj, str):
        # String test -> '"test"'.
        # Use jsonpickle to handle double quotes.
        output.append(jsonpickle.encode(obj))
    elif isinstance(obj, list):
        # List ["a", 1] -> '["a", 1]'.
        output_tmp = "["
        for el in obj:
            output_tmp += to_python_code(el) + ", "
        output_tmp = output_tmp.rstrip(", ") + "]"
        output.append(output_tmp)
    elif isinstance(obj, tuple):
        # Tuple ["a", 1] -> '["a", 1]'.
        output_tmp = "("
        for el in obj:
            output_tmp += to_python_code(el) + ", "
        output_tmp = output_tmp.rstrip(", ") + ")"
        output.append(output_tmp)
    elif isinstance(obj, dict):
        # Dict {"a": 1} -> '{"a": 1}'.
        output_tmp = "{"
        for key in obj:
            output_tmp += (
                to_python_code(key) + ": " + to_python_code(obj[key]) + ", "
            )
        output_tmp = output_tmp.rstrip(", ") + "}"
        output.append(output_tmp)
    elif isinstance(obj, pd.DataFrame):
        # Dataframe with a column "a" and row values 1, 2 ->
        # "pd.DataFrame.from_dict({'a': [1, 2]})".
        vals = obj.to_dict(orient="list")
        output.append(f"pd.DataFrame.from_dict({vals})")
    elif isinstance(obj, pd.Series):
        # Series init as pd.Series([1, 2])
        output.append(
            f'pd.Series(data={obj.tolist()}, index={obj.index}, name="{obj.name}", '
            f"dtype={obj.dtype})"
        )
    elif isinstance(obj, cconfig.Config):
        # Config -> python_code -> "cconfig.Config.from_python(python_code)"
        val = obj.to_python()
        output.append(f'cconfig.Config.from_python("{val}")')
    else:
        # Use `jsonpickle` for serialization.
        _LOG.warning(
            "Type %s not found in serialization function: using jsonpickle.",
            type(obj),
        )
        output.append(f"r'{jsonpickle.encode(obj)}'")
    output = "\n".join(output)
    return output


# #############################################################################
# Playback
# #############################################################################


class Playback:
    @staticmethod
    def _get_test_file_name(file_with_code: str) -> str:
        """
        Construct the test file name based on the file with the code to test.

        :param file_with_code: path to file with code to test.
        :return: path to the file with generated test.
        """
        # Get directory and filename of the testing code.
        dirname_with_code, filename_with_code = os.path.split(file_with_code)
        dirname_with_test = os.path.join(dirname_with_code, "test")
        # Construct test file.
        test_file = os.path.join(
            dirname_with_test, f"test_by_playback_{filename_with_code}"
        )
        return test_file

    def _update_code_to_existing(self) -> None:
        """
        Get existing content from the file with test.

        If the file doesn't exist - creates it.
        """
        # Create test file if it doesn't exist.
        if not os.path.exists(self._test_file):
            hio.create_enclosing_dir(self._test_file, True)
            hio.to_file(self._test_file, "", mode="w")
        else:
            # Get already existing content in the test file.
            self._code = hio.from_file(self._test_file).split("\n")
            self._file_exists = True

    def _append(self, string: str, num_tabs: int = 0) -> None:
        """
        Add indented line to the code.
        """
        num_spaces = num_tabs * 4
        self._code.append(hprint.indent(string, num_spaces=num_spaces))

    def __init__(
        self,
        mode: str,
        to_file: Optional[bool] = None,
        max_tests: Optional[int] = None,
    ) -> None:
        """
        Initialize the class variables.

        :param mode: the type of unit test to be generated (e.g. "assert_equal")
        :param to_file: save playback output to the file
            test/test_by_playback_<orig_filename>.py
        :param max_tests: limit a number of generated tests for the testing
            function. Can be useful if the function is called a lot of times
            during the execution.
        """
        _LOG.debug(hprint.to_str("mode to_file max_tests"))
        hdbg.dassert_in(mode, ("check_string", "assert_equal"))
        self.mode = mode
        # TODO(gp): Factor out in a function but need to discard one more level
        #  in the stack trace.
        cur_frame = inspect.currentframe()
        self._func_name = cur_frame.f_back.f_code.co_name  # type: ignore
        # We can use kw arguments for all args. Python supports this.
        self._kwargs = cur_frame.f_back.f_locals.copy()  # type: ignore
        # It treats all arguments defined before itself as arguments. If this
        # is done, it will mess up the function call that will be created in
        # `Playback.run`.
        expected_arg_count = cur_frame.f_back.f_code.co_argcount  # type: ignore
        if "kwargs" in self._kwargs:
            expected_arg_count += 1
        _LOG.debug(hprint.to_str("expected_arg_count"))
        # TODO(gp): Is this necessary?
        # hdbg.dassert_eq(
        #    expected_arg_count,
        #    len(cur_frame.f_back.f_locals),  # type: ignore
        #    msg="the Playback class should be the first thing instantiated in"
        #       " a function.",
        # )
        # If the function is a method, store the parent class so we can also
        # create that in the test.
        if "self" in self._kwargs:
            x = self._kwargs.pop("self")
            self._parent_class = x
            self._code = [
                f"# Test created for {cur_frame.f_back.f_globals['__name__']}"  # type: ignore
                f".{x.__class__.__name__}.{self._func_name}."
            ]
        else:
            self._parent_class = None
            self._code = [
                # pylint: disable=line-too-long
                f"# Test created for {cur_frame.f_back.f_globals['__name__']}.{self._func_name}."  # type: ignore
            ]
        self._append("")
        # Check if need to write the code directly to file.
        self._to_file = to_file if to_file is not None else False
        # Find filename to write the code.
        file_with_code = cur_frame.f_back.f_code.co_filename  # type: ignore
        self._test_file = self._get_test_file_name(file_with_code)
        # Check if file exists, need to keep code already here.
        self._file_exists = False
        if self._to_file:
            self._update_code_to_existing()
        # Limit number of tests per tested function.
        self._max_tests = max_tests or float("+inf")

    @staticmethod
    def test_code(output: str) -> None:
        # Try to execute in a fake environment.
        # ```
        # local_env = {}
        # _ = exec(output, local_env)
        # ```
        _ = exec(output)  # pylint: disable=exec-used

    def _check_code(self, func_output: Any) -> None:
        """
        Generate test code that makes an assertion.
        """
        if self.mode == "check_string":
            if isinstance(func_output, (pd.DataFrame, pd.Series, str)):
                if not isinstance(func_output, str):
                    self._append(
                        "actual = hpandas.df_to_str(actual, num_rows=None)", 2
                    )
            if not isinstance(func_output, (str, bytes)):
                self._append("actual = str(actual)", 2)
            self._append("# Check output.", 2)
            self._append("self.check_string(actual)", 2)
        elif self.mode == "assert_equal":
            self._append("# Define expected output.", 2)
            func_output_as_code = to_python_code(func_output)
            self._append(f"expected = {func_output_as_code}", 2)
            if not isinstance(
                func_output, (int, float, str, list, dict, pd.DataFrame)
            ):
                self._append("expected = jsonpickle.decode(expected)", 2)

            if isinstance(func_output, (pd.DataFrame, pd.Series)):
                self._append(
                    "actual = hpandas.df_to_str(actual, num_rows=None)", 2
                )
                self._append(
                    "expected = hpandas.df_to_str(expected, num_rows=None)", 2
                )
            self._append("# Compare actual and expected output.", 2)
            self._append("self.assertEqual(actual, expected)", 2)
        else:
            raise ValueError(f"Invalid mode='{self.mode}'")

    def _add_imports(self, additional: Optional[List[str]] = None) -> None:
        """
        Add the code with imports.
        """
        # Add imports.
        self._append("import helpers.hpandas as hpandas")
        self._append("import helpers.hunit_test as hunitest")
        self._append("import jsonpickle")
        self._append("import pandas as pd")
        self._append("import config_root.config as cconfi")
        for a in additional or []:
            self._append(a)
        self._code.extend(["", ""])

    def _get_class_name_string(self) -> str:
        """
        Get a string for the test code with the name of the test class.

        I.e. "class TestMyMethod(hunitest.TestCase):".
        """
        test_name = (
            self._parent_class.__class__.__name__
            if self._parent_class is not None
            else ""
        )
        test_name += "".join(
            [x.capitalize() for x in self._func_name.split("_")]
        )
        class_string = f"class Test{test_name}(hunitest.TestCase):"
        return class_string

    def _get_class_count(self) -> int:
        """
        Find a number of already generated tests for the method.
        """
        class_string = self._get_class_name_string()
        count = 0
        for line in self._code:
            count += line == class_string
        return count

    def _add_test_class(self) -> None:
        """
        Add the code with the test class definition and the test method
        definition.
        """
        # Add test class and test method.
        class_string = self._get_class_name_string()
        # Find how many times method was tested.
        count = self._get_class_count()
        if count >= self._max_tests:
            # If it was already tested enough times, raise.
            raise IndexError(f"{self._max_tests} tests already generated")
        # Otherwise, continue to create a test code.
        self._append(class_string)
        self._append(f"def test{count + 1}(self) -> None:", 1)

    def _add_function_call(self) -> None:
        """
        Add a call of the function to test to the test code.
        """
        self._append("# Call function to test.", 2)
        if self._parent_class is None:
            fnc_call = [f"{k}={k}" for k in self._kwargs.keys()]
            self._append(f"actual = {self._func_name}({', '.join(fnc_call)})", 2)
        else:
            var_code = to_python_code(self._parent_class)
            # Re-create the parent class.
            self._append(f"cls = {var_code}", 2)
            self._append("cls = jsonpickle.decode(cls)", 2)
            fnc_call = [f"{k}={k}" for k in self._kwargs.keys()]
            # Call the method as a child of the parent class.
            self._append(
                f"actual = cls.{self._func_name}({', '.join(fnc_call)})", 2
            )

    def _add_var_definitions(self) -> None:
        """
        Add variables definitions for the function to test.
        """
        if self._kwargs:
            self._append("# Define input variables.", 2)
        for key in self._kwargs:
            as_python = to_python_code(self._kwargs[key])
            self._append(f"{key} = {as_python}", 2)
            # Decode back to an actual Python object, if necessary.
            if not isinstance(
                self._kwargs[key],
                (
                    int,
                    float,
                    str,
                    list,
                    dict,
                    pd.DataFrame,
                    pd.Series,
                    cconfig.Config,
                ),
            ):
                self._append(f"{key} = jsonpickle.decode({key})", 2)

    def _gen_code(self) -> str:
        """
        Construct string with all generated test code.
        """
        code = "\n".join(self._code) + "\n"
        _LOG.debug("code=\n%s", code)
        if self._to_file:
            hio.to_file(self._test_file, code)
        return code

    def run(self, func_output: Any) -> str:
        """
        Generate a unit test for the function.

        The unit test compares the actual function output with the expected
        `func_output`.

        :param func_output: the expected function output
        :return: the code of the unit test
        """
        if self._to_file and self._file_exists:
            # Imports were added before, so skip.
            pass
        else:
            # Start with imports.
            self._add_imports()
        # Count if we reached max number of tests generated for a single function.
        try:
            self._add_test_class()
        except IndexError as exception:
            # If there are already enough tests, not add anything.
            _LOG.warning(str(exception))
            return ""
        self._add_var_definitions()
        self._add_function_call()
        self._check_code(func_output)
        return self._gen_code()


# #############################################################################


def json_pretty_print(parsed: Any) -> str:
    """
    Pretty print a JSON object.

    :param parsed: a JSON object
    :return: a prettified JSON object
    """
    if isinstance(parsed, str):
        parsed = json.loads(parsed)
    # `ret = pprint.pformat(parsed)
    ret = json.dumps(parsed, indent=4, sort_keys=True)
    return ret


def round_trip_convert(obj1: Any, log_level: int) -> Any:
    """
    Encode and decode with `jsonpickle` ensuring the object remains the same.

    :param obj1: the initial object
    :param log_level: the level of logging
    :return: the object after encoding and decoding
    """
    _LOG.log(log_level, "# obj1=\n%s", obj1)
    _LOG.log(log_level, "class=%s", type(obj1))
    # Encode.
    frozen = jsonpickle.encode(obj1)
    _LOG.log(log_level, "# frozen=\n%s", json_pretty_print(frozen))
    # Decode.
    obj2 = jsonpickle.decode(frozen)
    _LOG.log(log_level, "# obj2=\n%s", obj2)
    _LOG.log(log_level, "class=%s", type(obj1))
    # Check whether the decoded version is the same as the initial object.
    if str(type(obj1)).startswith("<class '"):
        # TODO(gp): Check the str representation.
        pass
    else:
        if isinstance(obj1, pd.DataFrame):
            hdbg.dassert(obj1.equals(obj2), "obj1=\n%s\nobj2=\n%s", obj1, obj2)
        else:
            hdbg.dassert_eq(obj1, obj2)
    return obj2


# #############################################################################
# Decorator
# #############################################################################


# TODO(gp): This approach doesn't work since we use introspection and so we probably
#  need to skip one level in the stack trace.


# Use the `playback` decorator as:
# ```
# import helpers.hplayback as hplayba
#
# @hplayba.playback
# def target_function(...):
#   ...
# ```


def playback(func: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        import helpers.hplayback as hplayba

        playback = hplayba.Playback("assert_equal")
        res = func(*args, **kwargs)
        code = playback.run(res)
        print(code)
        return res

    return wrapper(func)


# Inline the decorator as:
#
# 1) Rename `target_func` -> `target_func_tmp`
# ```
# def target_function_tmp(...):
#   ...
# ```
#
# 2) Add wrapper:
# ```
# def target_function_tmp(...):
#   ...
#
# from typing import Any
#
# def target_function(*args: Any, **kwargs: Any) -> Any:
#     import helpers.hplayback as hplayb
#     playback = hplayb.Playback("assert_equal")
#     res = target_func_tmp(*args, **kwargs)
#     code = playback.run(res)
#     print(code)
#     return res
# ```


# #############################################################################
# Record / replay system.
# #############################################################################

# A record describes a single function call captured by the `@record` decorator.
# It contains:
# - `args`: positional arguments of the call.
# - `kwargs`: keyword arguments of the call.
# - `result`: value returned by the call.
_RecordType = Dict[str, Any]

# Per-process set of fully qualified function names with active recording.
# A function decorated with `@record` only writes records when its qualified
# name appears in this set.
if "_RECORDING_ACTIVE" not in globals():
    _RECORDING_ACTIVE: Set[str] = set()


def _get_record_func_name(func: Callable) -> str:
    """
    Return the qualified name used to track recording state for `func`.

    :param func: function decorated with `@record`
    :return: fully qualified function name as stored on the wrapper
    """
    hdbg.dassert(
        hasattr(func, "__record_func_name__"),
        "Function '%s' is not decorated with @record",
        getattr(func, "__qualname__", func),
    )
    return getattr(func, "__record_func_name__")


def enable_recording(func: Callable) -> None:
    """
    Enable recording for a function decorated with `@record`.

    :param func: function decorated with `@record`
    """
    name = _get_record_func_name(func)
    _LOG.debug("Enabling recording for '%s'", name)
    _RECORDING_ACTIVE.add(name)


def disable_recording(func: Callable) -> None:
    """
    Disable recording for a function decorated with `@record`.

    :param func: function decorated with `@record`
    """
    name = _get_record_func_name(func)
    _LOG.debug("Disabling recording for '%s'", name)
    _RECORDING_ACTIVE.discard(name)


def is_recording_active(func: Callable) -> bool:
    """
    Return whether recording is active for a `@record`-decorated function.

    :param func: function decorated with `@record`
    :return: True if recording is active for `func`
    """
    name = _get_record_func_name(func)
    return name in _RECORDING_ACTIVE


def _save_records(file_path: str, records: List[_RecordType]) -> None:
    """
    Save a list of records to disk as a JSON file via `jsonpickle`.

    The outer file is JSON so that simple records (e.g., string args and
    list-of-dict results) remain human readable, while `jsonpickle` falls back
    to its own JSON-compatible encoding for objects that plain JSON cannot
    serialize (e.g., `DataFrame`, `Config`).

    :param file_path: path to the output file
    :param records: list of records to save
    """
    hio.create_enclosing_dir(file_path, incremental=True)
    # `jsonpickle.encode` forwards `indent` to the underlying JSON encoder,
    # giving us a multi-line, easy-to-inspect file.
    encoded = jsonpickle.encode(records, indent=2)
    hio.to_file(file_path, encoded)


def _load_records(file_path: str) -> List[_RecordType]:
    """
    Load a list of records previously saved by `_save_records`.

    :param file_path: path to the fixture file
    :return: list of records
    """
    hdbg.dassert_file_exists(file_path)
    text = hio.from_file(file_path)
    records = jsonpickle.decode(text)
    hdbg.dassert_isinstance(records, list)
    return records


def _append_record(
    file_path: str, args: Tuple[Any, ...], kwargs: Dict[str, Any], result: Any
) -> None:
    """
    Append a single call record to `file_path`, creating it if needed.

    :param file_path: path to the fixture file
    :param args: positional arguments of the recorded call
    :param kwargs: keyword arguments of the recorded call
    :param result: return value of the recorded call
    """
    # Reload-modify-write to keep the on-disk fixture consistent across crashes.
    if os.path.exists(file_path):
        records = _load_records(file_path)
    else:
        records = []
    record_entry: _RecordType = {
        "args": list(args),
        "kwargs": dict(kwargs),
        "result": result,
    }
    records.append(record_entry)
    _save_records(file_path, records)


def _make_lookup_key(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """
    Build a stable string key for a `(args, kwargs)` pair.

    Used by `MockDict` to index recorded calls regardless of order.

    :param args: positional arguments
    :param kwargs: keyword arguments
    :return: deterministic JSON string identifying the call
    """
    payload = {"args": list(args), "kwargs": kwargs}
    # `jsonpickle.encode` handles arbitrary Python objects, falling back to its
    # own encoding for types that plain JSON cannot serialize.
    key = jsonpickle.encode(payload)
    return key


def record(file_path: str, *, active: bool = False) -> Callable:
    """
    Decorator that records function calls to a fixture file.

    When recording is active, the decorator captures `(args, kwargs, result)`
    for each call into the JSON file at `file_path`. When recording is
    inactive, the wrapped function behaves exactly like the original.

    :param file_path: path to the fixture file
    :param active:
        - If True, recording is enabled by default
        - If False, recording is off until `enable_recording()` is called
    :return: decorator that wraps the target function
    """

    def decorator(func: Callable) -> Callable:
        func_name = f"{func.__module__}.{func.__qualname__}"
        if active:
            _RECORDING_ACTIVE.add(func_name)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            # Recording state is consulted at call time so that downstream
            # code (e.g., a CLI flag) can toggle it without re-importing.
            if func_name in _RECORDING_ACTIVE:
                _LOG.debug(
                    "Recording call to '%s' (file='%s')", func_name, file_path
                )
                _append_record(file_path, args, kwargs, result)
            return result

        # Expose metadata so `enable_recording`/`disable_recording` can find
        # the right global state entry from just the wrapped function.
        wrapper.__record_file_path__ = file_path  # type: ignore[attr-defined]
        wrapper.__record_func_name__ = func_name  # type: ignore[attr-defined]
        return wrapper

    return decorator


# #############################################################################
# _BaseMock
# #############################################################################


class _BaseMock:
    """
    Base class for record/replay mocks.

    Subclasses implement `__call__` to define how a recorded fixture is
    consumed (e.g., by lookup or by sequence).
    """

    def __init__(self, file_path: str) -> None:
        """
        Load records from `file_path`.

        :param file_path: path to a fixture file produced by `@record`
        """
        hdbg.dassert_file_exists(file_path)
        self._file_path = file_path
        self._records: List[_RecordType] = _load_records(file_path)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def patch(self, target: str) -> Any:
        """
        Return a `unittest.mock.patch` that replaces `target` with this mock.

        :param target: dotted path to the function to replace
            (e.g., `"helpers.lib_tasks_gh._gh_run_and_get_json"`)
        :return: patch object usable as a context manager or decorator
        """
        return umock.patch(target, side_effect=self)


# #############################################################################
# MockDict
# #############################################################################


class MockDict(_BaseMock):
    """
    Replay recorded calls as an order-independent dictionary lookup.

    The same `(args, kwargs)` always returns the same `result`, regardless of
    when the function is called. Use this when the function under test is a
    pure mapping from inputs to outputs.
    """

    def __init__(self, file_path: str) -> None:
        """
        Build an in-memory lookup from the records in `file_path`.

        :param file_path: path to a fixture file produced by `@record`
        """
        super().__init__(file_path)
        self._lookup: Dict[str, Any] = {}
        for rec in self._records:
            key = _make_lookup_key(tuple(rec["args"]), rec["kwargs"])
            # If the same call appears more than once, later entries win.
            self._lookup[key] = rec["result"]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Return the recorded result for the given arguments.

        :param args: positional arguments of the replayed call
        :param kwargs: keyword arguments of the replayed call
        :return: previously recorded result
        """
        key = _make_lookup_key(args, kwargs)
        hdbg.dassert_in(
            key,
            self._lookup,
            "No recorded call matches args=%s kwargs=%s in fixture '%s'",
            args,
            kwargs,
            self._file_path,
        )
        return self._lookup[key]


# #############################################################################
# MockSequence
# #############################################################################


class MockSequence(_BaseMock):
    """
    Replay recorded calls in the exact order they were captured.

    Each call asserts that the actual `(args, kwargs)` matches the expected
    `(args, kwargs)` at the current position. Use this when call order
    matters or when the same function is expected to be called multiple
    times with different inputs.
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize the sequence cursor at the beginning of the fixture.

        :param file_path: path to a fixture file produced by `@record`
        """
        super().__init__(file_path)
        self._idx = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Return the recorded result for the next call, after verifying args.

        :param args: positional arguments of the replayed call
        :param kwargs: keyword arguments of the replayed call
        :return: recorded result at the current sequence position
        """
        hdbg.dassert_lt(
            self._idx,
            len(self._records),
            "Sequence exhausted after %d call(s) in fixture '%s'",
            len(self._records),
            self._file_path,
        )
        rec = self._records[self._idx]
        # Verify the call matches what was recorded at this position.
        expected_args = list(rec["args"])
        expected_kwargs = rec["kwargs"]
        hdbg.dassert_eq(
            list(args),
            expected_args,
            "Sequence call %d: positional args do not match",
            self._idx,
        )
        hdbg.dassert_eq(
            kwargs,
            expected_kwargs,
            "Sequence call %d: keyword args do not match",
            self._idx,
        )
        result = rec["result"]
        self._idx += 1
        return result

    def reset(self) -> None:
        """
        Reset the sequence cursor to the beginning.
        """
        self._idx = 0
