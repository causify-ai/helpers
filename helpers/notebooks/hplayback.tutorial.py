# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# CONTENTS:
# - [hplayback Tutorial](#hplayback-tutorial)
#   - [Imports](#imports)
#   - [1. Mental Model](#1.-mental-model)
#   - [2. Recording with `@record` and `recording()`](#2.-recording-with-`@record`-and-`recording()`)
#   - [3. Replaying with `MockDict`](#3.-replaying-with-`mockdict`)
#   - [4. Replaying with `MockSequence`](#4.-replaying-with-`mocksequence`)
#   - [5. Patching with `unittest.mock`](#5.-patching-with-`unittest.mock`)
#   - [6. Complex Types via Pickle Fallback](#6.-complex-types-via-pickle-fallback)
#   - [Summary](#summary)

# %% [markdown]
# <a name='hplayback-tutorial'></a>
# # hplayback Tutorial
#
# This tutorial demonstrates `hplayback` - a record/replay system that
# captures `(args, kwargs, result)` triples from real function calls into a
# JSON fixture, then replays them in unit tests so the tests never hit the
# original backend.
#
# **Key features:**
# - Inert `@record` decorator: zero runtime cost when recording is off.
# - `recording()` context manager: scope when capture is active.
# - JSON-first fixture format: diff-friendly and human-readable.
# - `MockDict`: order-independent replay keyed on `(args, kwargs)`.
# - `MockSequence`: ordered replay that asserts each call matches.
# - Pickle fallback for values `json` cannot serialize natively.

# %% [markdown]
# <a name='imports'></a>
# ## Imports

# %%
import logging
import os
import tempfile

import helpers.hdbg as hdbg
import helpers.hplayback as hplayba

hdbg.init_logger(verbosity=logging.INFO)
_LOG = logging.getLogger(__name__)

# Use a scratch directory so the tutorial does not pollute the repo.
SCRATCH_DIR = tempfile.mkdtemp(prefix="hplayback_tutorial_")
_LOG.info("Using scratch dir: %s", SCRATCH_DIR)

# %% [markdown]
# <a name='1.-mental-model'></a>
# ## 1. Mental Model
#
# Two workflows live in `hplayback`:
#
# 1. **Record once**: Run the real code with a recording switch flipped on.
#    Every call to the decorated function is appended to a JSON fixture file.
#    The fixture is committed to the repo.
# 2. **Replay forever**: Unit tests load the fixture and substitute a mock
#    for the decorated function. The mock returns the recorded result for
#    each `(args, kwargs)` key, so the tests run offline.
#
# The decorator (`@record`) is inert by default - leaving it permanently on
# a function adds only a single attribute check per call.
#
# Two replay modes are available:
# - `MockDict`: looks up the result by `(args, kwargs)`. Order-independent.
# - `MockSequence`: replays in capture order, asserting each call's args.

# %% [markdown]
# <a name='2.-recording-with-`@record`-and-`recording()`'></a>
# <a name='2.-recording-with-record-and-recording'></a>
# ## 2. Recording with `@record` and `recording()`
#
# Decorate the function you want to capture with `@hplayba.record()`,
# passing the path to the fixture file. The decorator is **inert** until
# you wrap a block in `with hplayba.recording(func):`.

# %%
fixture_path = os.path.join(SCRATCH_DIR, "add.json")


@hplayba.record(fixture_path)
def add(a: int, b: int) -> int:
    """
    Sum two integers, simulating a function whose I/O is worth recording.
    """
    return a + b


# %%
# Outside `recording()`, the decorator is a no-op: no fixture file is
# created, and the function behaves identically to an undecorated version.
result = add(2, 3)
print(f"add(2, 3) = {result}")
print(f"Fixture written? {os.path.exists(fixture_path)}")

# %%
# Inside `recording()`, each call is captured.
with hplayba.recording(add):
    add(2, 3)
    add(10, 20)
    add(100, 200)
# On exit, the buffer is flushed to disk.
print(f"Fixture written? {os.path.exists(fixture_path)}")

# %%
# The fixture is plain JSON for simple types.
with open(fixture_path) as f:
    print(f.read())

# %% [markdown]
# Calls made outside `recording()` are not captured, even if the function
# is decorated. This keeps the decorator safe to leave on a function
# permanently in production code.

# %%
# These calls happen outside the context and are not added to the fixture.
add(999, 1)
add(7, 8)
# The fixture still has only the three records from above.
with open(fixture_path) as f:
    print(f.read())

# %% [markdown]
# <a name='3.-replaying-with-`mockdict`'></a>
# <a name='3.-replaying-with-mockdict'></a>
# ## 3. Replaying with `MockDict`
#
# `MockDict` is the order-independent replay mode. It loads a fixture and
# acts as a callable mapping `(args, kwargs) -> result`. Use it when the
# function under test is a pure mapping from inputs to outputs (e.g., a
# `gh` CLI wrapper).

# %%
mock_add = hplayba.MockDict(fixture_path)
# Calls can happen in any order.
print(f"mock_add(10, 20) = {mock_add(10, 20)}")
print(f"mock_add(2, 3)   = {mock_add(2, 3)}")
print(f"mock_add(100, 200) = {mock_add(100, 200)}")

# %%
# Calls with unrecorded arguments raise an assertion error.
try:
    mock_add(999, 1)
except AssertionError as e:
    print(f"AssertionError raised as expected:\n{str(e)[:200]}")

# %% [markdown]
# <a name='4.-replaying-with-`mocksequence`'></a>
# <a name='4.-replaying-with-mocksequence'></a>
# ## 4. Replaying with `MockSequence`
#
# `MockSequence` is the ordered replay mode. It expects calls in the exact
# sequence they were recorded, and asserts that each call's `(args,
# kwargs)` matches the recorded one. Use it when call order matters or
# when the same function is called multiple times with distinct inputs.

# %%
mock_seq = hplayba.MockSequence(fixture_path)
# Calls must happen in capture order: (2,3) then (10,20) then (100,200).
print(f"Call 1: {mock_seq(2, 3)}")
print(f"Call 2: {mock_seq(10, 20)}")
print(f"Call 3: {mock_seq(100, 200)}")

# %%
# An out-of-order call raises an assertion error.
mock_seq2 = hplayba.MockSequence(fixture_path)
try:
    mock_seq2(10, 20)
except AssertionError as e:
    print(f"AssertionError raised as expected:\n{str(e)[:200]}")

# %%
# `reset()` rewinds the cursor so the same fixture can be replayed again.
mock_seq3 = hplayba.MockSequence(fixture_path)
mock_seq3(2, 3)
mock_seq3.reset()
# After reset, the sequence starts over.
print(f"After reset, first call: {mock_seq3(2, 3)}")

# %% [markdown]
# <a name='5.-patching-with-`unittest.mock`'></a>
# <a name='5.-patching-with-unittestmock'></a>
# ## 5. Patching with `unittest.mock`
#
# Both `MockDict` and `MockSequence` expose a `patch()` method that wraps
# `unittest.mock.patch` and uses the mock as a `side_effect`. This is the
# typical usage in tests: patch the real function with the mock so other
# code that calls the real function picks up recorded results.

# %% [markdown]
# Imagine `add()` is buried deep in some helper that we want to test
# without running `add()` for real. We patch the dotted path and the
# downstream code is none the wiser.


# %%
def caller_that_uses_add() -> int:
    """
    Call `add()` indirectly; we want to test this offline.
    """
    return add(2, 3) + add(10, 20)


# %%
# Without patching, this calls the real `add()`.
print(f"Real result: {caller_that_uses_add()}")

# %%
# With `MockDict.patch()`, the call is intercepted and the recorded
# result is returned. Note we patch the module-qualified name of `add()`
# as it appears at the call site.
mock_dict = hplayba.MockDict(fixture_path)
with mock_dict.patch(f"{__name__}.add"):
    print(f"Mocked result: {caller_that_uses_add()}")

# %% [markdown]
# <a name='6.-complex-types-via-pickle-fallback'></a>
# ## 6. Complex Types via Pickle Fallback
#
# The fixture format is JSON, so simple types (str, int, list, dict) stay
# human-readable. Values that `json` cannot serialize natively are wrapped
# in a `{"__pickle__": "<base64>"}` sentinel and round-trip through
# `pickle`. This lets the same fixture file hold simple types inline and
# complex types as base64 blobs.
#
# **Trust boundary**: only load fixtures produced by code you trust.
# `pickle.loads()` executes arbitrary code, so a fixture is as privileged
# as any code in the repo.
#
# #############################################################################
# Token
# #############################################################################


# %%
# A custom class defined at module scope so `pickle` can find it by
# import path. Pickle cannot serialize classes defined inside a function.
class Token:
    """
    Tiny custom type used to exercise the pickle fallback.
    """

    def __init__(self, n: str) -> None:
        self.n = n

    def __repr__(self) -> str:
        return f"Token({self.n!r})"


complex_fixture = os.path.join(SCRATCH_DIR, "complex.json")


@hplayba.record(complex_fixture)
def make_object(name: str) -> Token:
    """
    Return a custom object that `json` cannot serialize natively.
    """
    return Token(name)


# %%
with hplayba.recording(make_object):
    make_object("alpha")
    make_object("beta")
# The fixture mixes inline JSON for args with a pickle sentinel for the
# complex `result` value.
with open(complex_fixture) as f:
    print(f.read())

# %%
# On replay, the sentinel is rehydrated back to the original object.
mock_obj = hplayba.MockDict(complex_fixture)
print(f"mock_obj('alpha') = {mock_obj('alpha')!r}")
print(f"mock_obj('beta')  = {mock_obj('beta')!r}")

# %% [markdown]
# <a name='summary'></a>
# ## Summary
#
# - Decorate the function you want to capture with `@hplayba.record(path)`.
#   Leaving the decorator on permanently is safe; it is inert outside
#   `recording()`.
# - Wrap the recording session in `with hplayba.recording(func):`. The
#   fixture file is written when the block exits.
# - Pick a replay class based on whether call order matters:
#   - `MockDict` for order-independent `(args, kwargs) -> result` lookup.
#   - `MockSequence` for in-order replay with per-call argument checks.
# - Use `mock.patch()` to substitute the real function in tests.
# - Complex types round-trip via a pickle+base64 sentinel inside the JSON
#   envelope.

# %%
# Cleanup the scratch directory.
import shutil

shutil.rmtree(SCRATCH_DIR, ignore_errors=True)
_LOG.info("Removed scratch dir: %s", SCRATCH_DIR)
