import json
import logging
import os
import pickle
from typing import Any, Dict

import pandas as pd
import pytest

import helpers.hcache_simple as hcacsimp
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


@hcacsimp.simple_cache(cache_type="json")
def _cached_function(x: int) -> int:
    """
    Return double the input and cache it using JSON.

    :param x: input integer to be doubled
    :return: doubled value (x * 2)
    """
    res = x * 2
    return res


@hcacsimp.simple_cache(cache_type="pickle")
def _cached_pickle_function(x: int) -> int:
    """
    Return the square of the input and cache it using pickle.

    :param x: input integer to be squared
    :return: squared value (x**2)
    """
    res = x**2
    return res


@hcacsimp.simple_cache(cache_type="json")
def _multi_arg_func(a: int, b: int) -> int:
    """
    Return the sum of two numbers.

    :param a: first number
    :param b: second number
    :return: sum of a and b.
    """
    res = a + b
    return res


@hcacsimp.simple_cache(cache_type="json")
def _refreshable_function(x: int) -> int:
    """
    Return x multiplied by 10 and update the call count.

    :param x: The input integer
    :return: The result of multiplying x by 10
    """
    _refreshable_function.call_count += 1
    res = x * 10
    return res


# Initialize the call counter for the refreshable function.
_refreshable_function.call_count = 0


@hcacsimp.simple_cache(cache_type="json")
def _kwarg_func(a: int, b: int = 0) -> int:
    """
    Return the difference between a and b.

    :param a: The minuend
    :param b: The subtrahend (defaults to 0)
    :return: The difference (a - b)
    """
    res = a - b
    return res


@hcacsimp.simple_cache(cache_type="json")
def _dummy_cached_function(x: int) -> int:
    """
    Return x plus 100. Used primarily for testing cache statistics.

    :param x: The input integer
    :return: value (x + 100)
    """
    res = x + 100
    return res


# #############################################################################
# BaseCacheTest
# #############################################################################


class BaseCacheTest(hunitest.TestCase):
    """
    Base test class to provide common setup and teardown functionality.

    Instead of using setUp/tearDown, we use set_up_test/tear_down_test
    along with a pytest fixture that ensures these methods run before
    and after each test.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        # Run common setup before each test.
        self.set_up_test()
        yield
        # Run common teardown after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test:

         - Set specific cache properties needed for the tests.
        """
        # Set the cache properties for each function.
        hcacsimp.set_cache_property("system", "_cached_function", "type", "json")
        hcacsimp.set_cache_property(
            "system", "_cached_pickle_function", "type", "pickle"
        )
        hcacsimp.set_cache_property("system", "_multi_arg_func", "type", "json")
        hcacsimp.set_cache_property(
            "system", "_refreshable_function", "type", "json"
        )
        hcacsimp.set_cache_property("system", "_kwarg_func", "type", "json")
        hcacsimp.set_cache_property(
            "system", "_dummy_cached_function", "type", "json"
        )

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test:
            - Reset cache(in-memory, disk).
            - Reset system cache properties.
        """
        # Reset caches for all cached functions.
        for func_name in [
            "_cached_function",
            "_cached_pickle_function",
            "_multi_arg_func",
            "_refreshable_function",
            "_kwarg_func",
            "_dummy_cached_function",
        ]:
            # Reset both disk and in-memory cache.
            hcacsimp.reset_cache(func_name=func_name, interactive=False)
        # Reset system cache properties.
        try:
            hcacsimp.reset_cache_property("system")
        except OSError:
            # If there is an OSError, remove the system cache property file manually.
            system_file = hcacsimp.get_cache_property_file("system")
            if os.path.exists(system_file):
                os.remove(system_file)


# #############################################################################
# Test_get_cache
# #############################################################################


class Test_get_cache(BaseCacheTest):
    """
    Test get_cache functionality for retrieving cached values.
    """

    def test1(self) -> None:
        """
        Verify that get_cache returns a cache with the expected key and value.
        """
        # Prepare inputs.
        input_val = 2
        expected_key = '{"args": [2], "kwargs": {}}'
        expected_value = 4
        # Run test.
        _cached_function(input_val)
        cache: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Check outputs.
        self.assertIn(expected_key, cache)
        self.assert_equal(cache[expected_key], expected_value)


# #############################################################################
# Test_flush_cache_to_disk
# #############################################################################


class Test_flush_cache_to_disk(BaseCacheTest):
    """
    Test flush_cache_to_disk functionality for persisting cache to disk.
    """

    def test1(self) -> None:
        """
        Verify that flushing creates a cache file on disk.
        """
        # Prepare inputs.
        input_val = 3
        cache_file = "cache._cached_function.json"
        # Run test.
        _cached_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Check outputs.
        self.assertTrue(
            os.path.exists(cache_file), "Cache file should exist on disk."
        )

    def test2(self) -> None:
        """
        Verify that the disk cache file contains the expected key and value.
        """
        # Prepare inputs.
        input_val = 3
        expected_key = '{"args": [3], "kwargs": {}}'
        expected_value = 6
        cache_file = "cache._cached_function.json"
        # Run test.
        _cached_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_function")
        with open(cache_file, "r", encoding="utf-8") as f:
            disk_cache: Dict[str, Any] = json.load(f)
        # Check outputs.
        self.assertIn(expected_key, disk_cache)
        self.assert_equal(disk_cache[expected_key], expected_value)


# #############################################################################
# Test_reset_mem_cache
# #############################################################################


class Test_reset_mem_cache(BaseCacheTest):
    """
    Test reset_mem_cache functionality for clearing in-memory cache.
    """

    def test1(self) -> None:
        """
        Verify that the cache is empty after `reset_mem_cache` is called.
        """
        # Prepare inputs.
        input_val = 5
        expected_key = '{"args": [5], "kwargs": {}}'
        # Run test.
        _cached_function(input_val)
        hcacsimp.reset_mem_cache("_cached_function")
        cache_after: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Check outputs.
        self.assertNotIn(expected_key, cache_after)


# #############################################################################
# Test_force_cache_from_disk
# #############################################################################


class Test_force_cache_from_disk(BaseCacheTest):
    """
    Test force_cache_from_disk functionality for loading cache from disk.
    """

    def test1(self) -> None:
        """
        Verify that the memory cache is empty after a reset.
        """
        # Prepare inputs.
        input_val = 7
        expected_key = '{"args": [7], "kwargs": {}}'
        # Run test.
        _cached_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_function")
        hcacsimp.reset_mem_cache("_cached_function")
        mem_cache: Dict[str, Any] = hcacsimp.get_mem_cache("_cached_function")
        # Check outputs.
        self.assertNotIn(
            expected_key,
            mem_cache,
            "Memory cache should be empty after reset.",
        )

    def test2(self) -> None:
        """
        Populate disk cache, reset memory, force reload, and verify that the
        key appears.
        """
        # Prepare inputs.
        input_val = 7
        expected_key = '{"args": [7], "kwargs": {}}'
        # Run test.
        _cached_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_function")
        hcacsimp.reset_mem_cache("_cached_function")
        _LOG.debug("Force reload disk cache for '_cached_function'")
        hcacsimp.force_cache_from_disk("_cached_function")
        full_cache: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Check outputs.
        self.assertIn(
            expected_key,
            full_cache,
            "After forcing, disk key should appear in memory.",
        )


# #############################################################################
# Test_get_cache_perf
# #############################################################################


class Test_get_cache_perf(BaseCacheTest):
    """
    Test cache performance tracking functionality.
    """

    def test1(self) -> None:
        """
        Verify that performance tracking records hits and misses correctly.
        """
        # Prepare inputs.
        input_val = 8
        # Run test.
        hcacsimp.enable_cache_perf("_cached_function")
        _LOG.debug("Call _cached_function(8) twice")
        _cached_function(input_val)
        _cached_function(input_val)
        stats: str = hcacsimp.get_cache_perf_stats("_cached_function")
        # Check outputs.
        self.assertIn("hits=1", stats)
        self.assertIn("misses=1", stats)

    def test2(self) -> None:
        """
        Verify that disabling performance tracking returns None.
        """
        # Run test.
        hcacsimp.disable_cache_perf("_cached_function")
        perf_data = hcacsimp.get_cache_perf("_cached_function")
        # Check outputs.
        self.assertIsNone(perf_data)


# #############################################################################
# Test_set_cache_property
# #############################################################################


class Test_set_cache_property(BaseCacheTest):
    """
    Test set_cache_property and get_cache_property functionality.
    """

    def test1(self) -> None:
        """
        Verify that setting a valid cache property works and can be retrieved.
        """
        # Run test.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "report_on_cache_miss", True
        )
        val: bool = hcacsimp.get_cache_property(
            "user", "_cached_function", "report_on_cache_miss"
        )
        # Check outputs.
        self.assertTrue(val)

    def test2(self) -> None:
        """
        Verify that resetting cache properties clears previously set
        properties.
        """
        # Run test.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "report_on_cache_miss", True
        )
        self.assertTrue(
            hcacsimp.get_cache_property(
                "user", "_cached_function", "report_on_cache_miss"
            )
        )
        hcacsimp.reset_cache_property("user")
        val_after_reset: bool = hcacsimp.get_cache_property(
            "user", "_cached_function", "report_on_cache_miss"
        )
        # Check outputs.
        self.assertFalse(val_after_reset)

    def test3(self) -> None:
        """
        Verify that setting an invalid cache property raises an error.
        """
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            hcacsimp.set_cache_property(
                "user", "_cached_function", "invalid_prop", True
            )

    def test4(self) -> None:
        """
        Verify return of a string containing the property value.
        """
        # Run test.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "force_refresh", True
        )
        prop_str: str = hcacsimp.cache_property_to_str(
            "user", "_cached_function"
        )
        # Check outputs.
        self.assertIn("force_refresh: True", prop_str)


# #############################################################################
# Test_get_cache_func_names
# #############################################################################


class Test_get_cache_func_names(BaseCacheTest):
    """
    Test get_cache_func_names functionality for retrieving cached function names.
    """

    def test1(self) -> None:
        """
        Verify that memory cache function names include `_cached_function`.
        """
        # Prepare inputs.
        input_val = 9
        # Run test.
        _cached_function(input_val)
        mem_funcs = hcacsimp.get_cache_func_names("mem")
        # Check outputs.
        self.assertIn("_cached_function", mem_funcs)

    def test2(self) -> None:
        """
        Verify that all cache function names include both JSON and pickle
        functions.
        """
        # Prepare inputs.
        input_val = 2
        # Run test.
        _cached_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_function")
        _cached_pickle_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_pickle_function")
        all_funcs = hcacsimp.get_cache_func_names("all")
        # Check outputs.
        self.assertIn("_cached_function", all_funcs)
        self.assertIn("_cached_pickle_function", all_funcs)

    def test3(self) -> None:
        """
        Verify that disk cache function names include `_cached_function` after
        flushing.
        """
        # Prepare inputs.
        input_val = 2
        # Run test.
        _cached_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_function")
        disk_funcs = hcacsimp.get_cache_func_names("disk")
        # Check outputs.
        self.assertIn("_cached_function", disk_funcs)


# #############################################################################
# Test_cache_stats_to_str
# #############################################################################


class Test_cache_stats_to_str(BaseCacheTest):
    """
    Test cache_stats_to_str functionality for generating cache statistics.
    """

    def test1(self) -> None:
        """
        Verify that cache_stats_to_str returns a DataFrame with 'memory' and
        'disk' columns.
        """
        # Prepare inputs.
        input_val = 1
        # Run test.
        _dummy_cached_function(input_val)
        stats_df: pd.DataFrame = hcacsimp.cache_stats_to_str(
            "_dummy_cached_function"
        )
        # Check outputs.
        self.assertIsInstance(stats_df, pd.DataFrame)
        self.assertIn("memory", stats_df.columns)
        self.assertIn("disk", stats_df.columns)


# #############################################################################
# Test__kwarg_func
# #############################################################################


class Test__kwarg_func(BaseCacheTest):
    """
    Test caching behavior with keyword arguments.
    """

    def test1(self) -> None:
        """
        Test that verifies keyword arguments are handled correctly by the
        cache.
        """
        # Prepare inputs.
        arg_a = 5
        kwarg_b1 = 3
        kwarg_b2 = 10
        # Run test.
        res1: int = _kwarg_func(arg_a, b=kwarg_b1)
        res2: int = _kwarg_func(arg_a, b=kwarg_b2)
        # Check outputs.
        self.assertNotEqual(res1, res2)


# #############################################################################
# Test__multi_arg_func
# #############################################################################


class Test__multi_arg_func(BaseCacheTest):
    """
    Test caching behavior with multiple positional arguments.
    """

    def test1(self) -> None:
        """
        Verify that the cache for _multi_arg_func contains the correct key.
        """
        # Prepare inputs.
        arg1 = 1
        arg2 = 2
        expected_key = '{"args": [1, 2], "kwargs": {}}'
        # Run test.
        _multi_arg_func(arg1, arg2)
        cache: Dict[str, Any] = hcacsimp.get_cache("_multi_arg_func")
        # Check outputs.
        self.assertIn(expected_key, cache)


# #############################################################################
# Test__cached_pickle_function
# #############################################################################


class Test__cached_pickle_function(BaseCacheTest):
    """
    Test caching with pickle serialization.
    """

    def test1(self) -> None:
        """
        Ensure that _cached_pickle_function returns the correct value and disk
        file.
        """
        # Prepare inputs.
        input_val = 4
        expected_result = 16
        expected_key = '{"args": [4], "kwargs": {}}'
        cache_file = "cache._cached_pickle_function.pkl"
        # Run test.
        res: int = _cached_pickle_function(input_val)
        hcacsimp.flush_cache_to_disk("_cached_pickle_function")
        with open(cache_file, "rb") as f:
            disk_cache: Dict[str, Any] = pickle.load(f)
        # Check outputs.
        self.assert_equal(res, expected_result)
        self.assertIn(expected_key, disk_cache)
        self.assert_equal(disk_cache[expected_key], expected_result)


# #############################################################################
# Test__refreshable_function
# #############################################################################


class Test__refreshable_function(BaseCacheTest):
    """
    Test force_refresh cache property functionality.
    """

    def test1(self) -> None:
        """
        Verify that `_refreshable_function` is called only once initially.
        """
        # Prepare inputs.
        _refreshable_function.call_count = 0
        input_val = 3
        expected_call_count = 1
        # Run test.
        _refreshable_function(input_val)
        _refreshable_function(input_val)
        # Check outputs.
        self.assert_equal(
            _refreshable_function.call_count,
            expected_call_count,
        )

    def test2(self) -> None:
        """
        Verify that enabling `force_refresh` causes `_refreshable_function` to
        be re-called.
        """
        # Prepare inputs.
        input_val = 3
        expected_result = 30
        expected_call_count = 2
        # Run test.
        res: int = _refreshable_function(input_val)
        hcacsimp.set_cache_property(
            "user", "_refreshable_function", "force_refresh", True
        )
        _refreshable_function(input_val)
        # Check outputs.
        self.assert_equal(res, expected_result)
        self.assert_equal(
            _refreshable_function.call_count,
            expected_call_count,
        )
