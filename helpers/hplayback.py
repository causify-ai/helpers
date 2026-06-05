"""
Record runtime calls of a function into a fixture file and replay them in tests
without contacting the original backend.

Import as:

import helpers.hplayback as hplayba
"""

import base64
import contextlib
import functools
import json
import logging
import pickle
import unittest.mock as umock
from typing import Any, Callable, Dict, Iterator, List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio

_LOG = logging.getLogger(__name__)


# #############################################################################
# Serialization helpers
# #############################################################################
# Fixture files are JSON so they stay diff-friendly and human-readable for
# the common case of simple types (strings, numbers, lists, dicts). Values
# that `json` cannot serialize natively (DataFrames, dataclasses, custom
# objects, ...) are wrapped in a `{"__pickle__": "<base64>"}` sentinel and
# round-trip through `pickle`.
#
# Trust boundary: only load fixtures produced by code you trust.
# `pickle.loads()` executes arbitrary code, so a fixture file is as
# privileged as any code in the repo.


_PICKLE_SENTINEL = "__pickle__"


def _encode_pickle(obj: Any) -> str:
    """
    Encode `obj` as an ASCII-safe base64-pickle string.

    :param obj: any pickleable Python object
    :return: base64-encoded pickle bytes
    """
    return base64.b64encode(pickle.dumps(obj)).decode("ascii")


def _decode_pickle(blob: str) -> Any:
    """
    Inverse of `_encode_pickle`.

    :param blob: base64-encoded pickle bytes produced by `_encode_pickle`
    :return: the original Python object
    """
    return pickle.loads(base64.b64decode(blob))


def _pickle_fallback(obj: Any) -> Dict[str, str]:
    """
    `json.dumps()` `default=` hook that wraps non-JSON-native values in a
    sentinel dict carrying a base64-pickle blob.

    :param obj: value `json` cannot serialize natively
    :return: sentinel dict `{"__pickle__": "<base64 pickle>"}`
    """
    return {_PICKLE_SENTINEL: _encode_pickle(obj)}


def _rehydrate(obj: Any) -> Any:
    """
    Walk a JSON-decoded structure and convert pickle sentinels back to Python
    objects.

    A dict whose only key is `_PICKLE_SENTINEL` is replaced with the
    pickled value; all other dicts and lists are recursed into.

    :param obj: value returned by `json.loads()`
    :return: structure with sentinels rehydrated
    """
    if isinstance(obj, dict):
        if list(obj.keys()) == [_PICKLE_SENTINEL]:
            return _decode_pickle(obj[_PICKLE_SENTINEL])
        return {k: _rehydrate(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rehydrate(x) for x in obj]
    return obj


# #############################################################################
# Storage
# #############################################################################


def _save_records(file_path: str, records: List[Dict[str, Any]]) -> None:
    """
    Write `records` to `file_path` as JSON.

    Simple types stay human-readable; values `json` cannot serialize
    natively are wrapped in a `{"__pickle__": "<base64>"}` sentinel via
    `_pickle_fallback()`.

    :param file_path: path to the output file
    :param records: list of records to save
    """
    hio.create_enclosing_dir(file_path, incremental=True)
    encoded = json.dumps(records, indent=2, default=_pickle_fallback)
    hio.to_file(file_path, encoded)


def _load_records(file_path: str) -> List[Dict[str, Any]]:
    """
    Read records previously written by `_save_records()`.

    Pickle sentinels emitted by `_pickle_fallback()` are rehydrated back
    to Python objects.

    :param file_path: path to the fixture file
    :return: list of records
    """
    hdbg.dassert_file_exists(file_path)
    records = _rehydrate(json.loads(hio.from_file(file_path)))
    hdbg.dassert_isinstance(records, list)
    return records


# #############################################################################
# Record / replay
# #############################################################################


def record(file_path: str) -> Callable:
    """
    Decorate a function so it can be recorded into `file_path`.

    The decorator is inert by default and adds no recording overhead
    beyond one attribute check per call. Turn recording on with
    `recording()`.

    :param file_path: path to the fixture file written when recording
        stops
    :return: decorator that wraps the target function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if wrapper._record_active:  # type: ignore[attr-defined]
                wrapper._record_buffer.append(  # type: ignore[attr-defined]
                    {
                        "args": list(args),
                        "kwargs": dict(kwargs),
                        "result": result,
                    }
                )
            return result

        # Per-function state lives on the wrapper, so each decorated function
        # owns its on/off flag and its buffer with no cross-talk and no need
        # for a separate registry.
        wrapper._record_file_path = file_path  # type: ignore[attr-defined]
        wrapper._record_active = False  # type: ignore[attr-defined]
        wrapper._record_buffer = []  # type: ignore[attr-defined]
        return wrapper

    return decorator


@contextlib.contextmanager
def recording(func: Callable) -> Iterator[None]:
    """
    Capture calls to `func` inside the block, then write the fixture.

    On entry, drops any previously buffered records and flips recording on.
    On exit, flushes the buffer to `func`'s fixture file and flips recording
    off, even if the block raises.

    :param func: function decorated with `@record`
    """
    hdbg.dassert(
        hasattr(func, "_record_buffer"),
        "%s is not decorated with @record",
        getattr(func, "__qualname__", func),
    )
    func._record_buffer = []  # type: ignore[attr-defined]
    func._record_active = True  # type: ignore[attr-defined]
    try:
        yield
    finally:
        func._record_active = False  # type: ignore[attr-defined]
        if func._record_buffer:  # type: ignore[attr-defined]
            _save_records(
                func._record_file_path,  # type: ignore[attr-defined]
                func._record_buffer,  # type: ignore[attr-defined]
            )


def _make_lookup_key(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """
    Build a deterministic JSON key for `(args, kwargs)`.

    `default=str` falls back to `str()` for types `json.dumps()` cannot
    serialize natively. For recorded GH commands (plain strings) this is
    exact; for richer args, equality is by string representation.

    :param args: positional arguments
    :param kwargs: keyword arguments
    :return: stable JSON string identifying the call
    """
    payload = {"args": list(args), "kwargs": kwargs}
    return json.dumps(payload, sort_keys=True, default=str)


# #############################################################################
# MockDict
# #############################################################################


class MockDict:
    """
    Replay recorded calls as an order-independent `(args, kwargs) -> result`
    map.

    Use when the function under test is a pure mapping from inputs to
    outputs.
    """

    def __init__(self, file_path: str) -> None:
        """
        Build the lookup table from the records in `file_path`.

        :param file_path: fixture file produced by `@record` +
            `recording()`
        """
        self._file_path = file_path
        records = _load_records(file_path)
        self._lookup: Dict[str, Any] = {}
        for rec in records:
            key = _make_lookup_key(tuple(rec["args"]), rec["kwargs"])
            # Last entry wins when a call repeats.
            self._lookup[key] = rec["result"]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Return the recorded result for the given arguments.

        :param args: positional arguments of the replayed call
        :param kwargs: keyword arguments of the replayed call
        :return: result captured for the matching call
        """
        key = _make_lookup_key(args, kwargs)
        hdbg.dassert_in(
            key,
            self._lookup,
            "No recorded call for args=%s kwargs=%s in '%s'",
            args,
            kwargs,
            self._file_path,
        )
        return self._lookup[key]

    def patch(self, target: str) -> Any:
        """
        Patch `target` with this mock as `side_effect`.

        :param target: dotted path of the function to replace
        :return: `unittest.mock` patch object
        """
        return umock.patch(target, side_effect=self)


# #############################################################################
# MockSequence
# #############################################################################


class MockSequence:
    """
    Replay recorded calls in capture order, asserting args at each step.

    Use when call order matters or when the same function is called
    multiple times with distinct inputs.
    """

    def __init__(self, file_path: str) -> None:
        """
        Load the sequence from `file_path` and place the cursor at the start.

        :param file_path: fixture file produced by `@record` +
            `recording()`
        """
        self._file_path = file_path
        self._records = _load_records(file_path)
        self._idx = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Verify `(args, kwargs)` matches the next recorded call and return its
        result.

        :param args: positional arguments of the replayed call
        :param kwargs: keyword arguments of the replayed call
        :return: result captured at the current cursor position
        """
        hdbg.dassert_lt(
            self._idx,
            len(self._records),
            "Sequence exhausted after %d call(s) in '%s'",
            len(self._records),
            self._file_path,
        )
        rec = self._records[self._idx]
        hdbg.dassert_eq(
            list(args),
            list(rec["args"]),
            "Sequence call %d: positional args mismatch",
            self._idx,
        )
        hdbg.dassert_eq(
            kwargs,
            rec["kwargs"],
            "Sequence call %d: keyword args mismatch",
            self._idx,
        )
        result = rec["result"]
        self._idx += 1
        return result

    def reset(self) -> None:
        """
        Move the cursor back to the start of the sequence.
        """
        self._idx = 0

    def patch(self, target: str) -> Any:
        """
        Patch `target` with this mock as `side_effect`.

        :param target: dotted path of the function to replace
        :return: `unittest.mock` patch object
        """
        return umock.patch(target, side_effect=self)
