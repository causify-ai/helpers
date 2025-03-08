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
         - Reset persistent user and system cache properties.
         - Reset in-memory caches for all cached functions.
         - Set specific cache properties needed for the tests.
        """
        # Reset persistent user cache properties.
        hcacsimp.reset_cache_property("user")
        try:
            hcacsimp.reset_cache_property("system")
        except OSError:
            # If there is an OSError, remove the system cache property file manually.
            system_file = hcacsimp.get_cache_property_file("system")
            if os.path.exists(system_file):
                os.remove(system_file)
        # Reset caches for all cached functions.
        for func_name in [
            "_cached_function",
            "_cached_pickle_function",
            "_multi_arg_func",
            "_refreshable_function",
            "_kwarg_func",
            "_dummy_cached_function",
        ]:
            try:
                # Reset both disk and in-memory cache.
                hcacsimp.reset_cache(func_name)
            except AssertionError:
                # If resetting the full cache fails, reset only the in-memory cache.
                hcacsimp.reset_mem_cache(func_name)
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

            - Remove cache files created on disk.
            - Remove the system cache property file.
        """
        # List of expected cache file names.
        for fname in [
            # Disk cache file for _cached_function (JSON format).
            "cache._cached_function.json",
            # Disk cache file for _cached_pickle_function (pickle format).
            "cache._cached_pickle_function.pkl",
            # Disk cache file for _multi_arg_func.
            "cache._multi_arg_func.json",
            # Disk cache file for _refreshable_function.
            "cache._refreshable_function.json",
            # Disk cache file for _kwarg_func.
            "cache._kwarg_func.json",
            # Disk cache file for _dummy_cached_function.
            "cache._dummy_cached_function.json",
        ]:
            # Check if the cache file exists on disk.
            if os.path.exists(fname):
                os.remove(fname)
        # Remove the system cache property file if it exists.
        system_file = hcacsimp.get_cache_property_file("system")
        if os.path.exists(system_file):
            os.remove(system_file)


# #############################################################################
# Test_get_cache
# #############################################################################


class Test_get_cache(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that get_cache returns a cache with the expected key and value.
        """
        # Populate the cache by calling _cached_function.
        _cached_function(2)
        # Retrieve the in-memory cache for _cached_function.
        cache: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Assert that the key "(2,)" is in the cache and its value is 4.
        self.assertIn("(2,)", cache)
        self.assertEqual(cache["(2,)"], 4)


# #############################################################################
# Test_flush_cache_to_disk
# #############################################################################


class Test_flush_cache_to_disk(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that flushing creates a cache file on disk.
        """
        # Call _cached_function to populate the cache.
        _cached_function(3)
        # Flush the cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Define expected cache file name.
        cache_file: str = "cache._cached_function.json"
        # Assert that the cache file now exists on disk.
        self.assertTrue(
            os.path.exists(cache_file), "Cache file should exist on disk."
        )

    def test2(self) -> None:
        """
        Verify that the disk cache file contains the expected key and value.
        """
        # Populate cache and flush to disk.
        _cached_function(3)
        # Flush the cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Define the expected cache file name.
        cache_file: str = "cache._cached_function.json"
        # Open and load the disk cache file.
        with open(cache_file, "r", encoding="utf-8") as f:
            # Load the JSON data from the file into a dictionary.
            disk_cache: Dict[str, Any] = json.load(f)
        # Assert that the disk cache contains the key "(3,)" with the correct value.
        self.assertIn("(3,)", disk_cache)
        # Assert that the value for key "(3,)" is 6.
        self.assertEqual(disk_cache["(3,)"], 6)


# #############################################################################
# Test_reset_mem_cache
# #############################################################################


class Test_reset_mem_cache(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that the cache is empty after `reset_mem_cache` is called.
        """
        # Populate the in-memory cache.
        _cached_function(5)
        # Reset the in-memory cache.
        hcacsimp.reset_mem_cache("_cached_function")
        # Retrieve the cache after reset.
        cache_after: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Verify that the key "(5,)" is no longer in the cache.
        self.assertNotIn("(5,)", cache_after)


# #############################################################################
# Test_force_cache_from_disk
# #############################################################################


class Test_force_cache_from_disk(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that the memory cache is empty after a reset.
        """
        # Populate cache and flush to disk.
        _cached_function(7)
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Reset in-memory cache.
        hcacsimp.reset_mem_cache("_cached_function")
        mem_cache: Dict[str, Any] = hcacsimp.get_mem_cache("_cached_function")
        # Ensure that the in-memory cache is empty.
        self.assertNotIn(
            "(7,)", mem_cache, "Memory cache should be empty after reset."
        )

    def test2(self) -> None:
        """
        Populate disk cache, reset memory, force reload, and verify that the
        key appears.
        """
        # Populate cache, flush to disk, and then reset in-memory cache.
        _cached_function(7)
        hcacsimp.flush_cache_to_disk("_cached_function")
        hcacsimp.reset_mem_cache("_cached_function")
        _LOG.debug("Force reload disk cache for '_cached_function'")
        # Force reload cache from disk.
        hcacsimp.force_cache_from_disk("_cached_function")
        full_cache: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Assert that the key is restored in the in-memory cache.
        self.assertIn(
            "(7,)", full_cache, "After forcing, disk key should appear in memory."
        )


# #############################################################################
# Test_get_cache_perf
# #############################################################################


class Test_get_cache_perf(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that performance tracking records hits and misses correctly.
        """
        # Enable performance tracking.
        hcacsimp.enable_cache_perf("_cached_function")
        _LOG.debug("Call _cached_function(8) twice")
        # First call should be a miss.
        _cached_function(8)
        # Second call should be a hit.
        _cached_function(8)
        # Retrieve performance statistics.
        stats: str = hcacsimp.get_cache_perf_stats("_cached_function")
        # Verify that one hit and one miss are recorded.
        self.assertIn("hits=1", stats)
        self.assertIn("misses=1", stats)

    def test2(self) -> None:
        """
        Verify that disabling performance tracking returns None.
        """
        # Disable performance tracking.
        hcacsimp.disable_cache_perf("_cached_function")
        # Assert that performance data is no longer available.
        self.assertIsNone(hcacsimp.get_cache_perf("_cached_function"))


# #############################################################################
# Test_set_cache_property
# #############################################################################


class Test_set_cache_property(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that setting a valid cache property works and can be retrieved.
        """
        # Set a valid cache property.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "report_on_cache_miss", True
        )
        # Retrieve and verify the property.
        val: bool = hcacsimp.get_cache_property(
            "user", "_cached_function", "report_on_cache_miss"
        )
        self.assertTrue(val)

    def test2(self) -> None:
        """
        Verify that resetting cache properties clears previously set
        properties.
        """
        # Set and verify the cache property.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "report_on_cache_miss", True
        )
        self.assertTrue(
            hcacsimp.get_cache_property(
                "user", "_cached_function", "report_on_cache_miss"
            )
        )
        # Reset all user cache properties.
        hcacsimp.reset_cache_property("user")
        # Verify that the property is no longer True.
        self.assertFalse(
            hcacsimp.get_cache_property(
                "user", "_cached_function", "report_on_cache_miss"
            )
        )

    def test3(self) -> None:
        """
        Verify that setting an invalid cache property raises an error.
        """
        # Verify that setting an invalid property raises an error.
        with self.assertRaises(AssertionError):
            hcacsimp.set_cache_property(
                "user", "_cached_function", "invalid_prop", True
            )

    def test4(self) -> None:
        """
        Verify return of a string containing the property value.
        """
        # Set force_refresh property and verify that it appears in the properties string.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "force_refresh", True
        )
        prop_str: str = hcacsimp.cache_property_to_str("user", "_cached_function")
        # Check output.
        self.assertIn("force_refresh: True", prop_str)


# #############################################################################
# Test_get_cache_func_names
# #############################################################################


class Test_get_cache_func_names(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that memory cache function names include `_cached_function`.
        """
        # Populate in-memory cache.
        _cached_function(9)
        # Retrieve function names from the memory cache.
        mem_funcs = hcacsimp.get_cache_func_names("mem")
        # Check output.
        self.assertIn("_cached_function", mem_funcs)

    def test2(self) -> None:
        """
        Verify that all cache function names include both JSON and pickle
        functions.
        """
        # Populate and flush caches for JSON and pickle functions.
        _cached_function(2)
        # Flush _cached_function cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Call _cached_pickle_function with input 2.
        _cached_pickle_function(2)
        # Flush _cached_pickle_function cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_pickle_function")
        # Retrieve all cache function names (both memory and disk).
        all_funcs = hcacsimp.get_cache_func_names("all")
        # Check output.
        self.assertIn("_cached_function", all_funcs)
        self.assertIn("_cached_pickle_function", all_funcs)

    def test3(self) -> None:
        """
        Verify that disk cache function names include `_cached_function` after
        flushing.
        """
        # Flush JSON cache to disk and verify disk cache function names.
        _cached_function(2)
        # Flush _cached_function cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Retrieve function names from the disk cache.
        disk_funcs = hcacsimp.get_cache_func_names("disk")
        # Check output.
        self.assertIn("_cached_function", disk_funcs)


# #############################################################################
# Test_cache_stats_to_str
# #############################################################################


class Test_cache_stats_to_str(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that cache_stats_to_str returns a DataFrame with 'memory' and
        'disk' columns.
        """
        # Populate cache.
        _dummy_cached_function(1)
        stats_df: pd.DataFrame = hcacsimp.cache_stats_to_str(
            "_dummy_cached_function"
        )
        # Assert that the returned object is a DataFrame.
        self.assertIsInstance(stats_df, pd.DataFrame)
        # Verify that it contains the 'memory' and 'disk' columns.
        self.assertIn("memory", stats_df.columns)
        self.assertIn("disk", stats_df.columns)


# #############################################################################
# Test__kwarg_func
# #############################################################################


class Test__kwarg_func(BaseCacheTest):

    def test1(self) -> None:
        """
        Test that verifies keyword arguments are handled correctly by the
        cache.
        """
        # Call with different keyword argument values.
        res1: int = _kwarg_func(5, b=3)
        res2: int = _kwarg_func(5, b=10)
        # Both calls should return the same result as only positional arguments are used for caching.
        self.assertEqual(res1, res2)


# #############################################################################
# Test__multi_arg_func
# #############################################################################


class Test__multi_arg_func(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that the cache for _multi_arg_func contains the correct key.
        """
        # Populate the cache.
        _multi_arg_func(1, 2)
        cache: Dict[str, Any] = hcacsimp.get_cache("_multi_arg_func")
        # Verify that the cache key is formatted as either "(1, 2)" or "(1,2)".
        self.assertTrue("(1, 2)" in cache or "(1,2)" in cache)


# #############################################################################
# Test__cached_pickle_function
# #############################################################################


class Test__cached_pickle_function(BaseCacheTest):

    def test1(self) -> None:
        """
        Ensure that _cached_pickle_function returns the correct value and disk
        file.
        """
        # Call the function to square the input.
        res: int = _cached_pickle_function(4)
        # Flush the cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_pickle_function")
        cache_file: str = "cache._cached_pickle_function.pkl"
        # Open and load the pickle cache file.
        with open(cache_file, "rb") as f:
            disk_cache: Dict[str, Any] = pickle.load(f)
        # Verify the result and cache contents.
        self.assertEqual(res, 16)
        self.assertIn("(4,)", disk_cache)
        self.assertEqual(disk_cache["(4,)"], 16)


# #############################################################################
# Test__refreshable_function
# #############################################################################


class Test__refreshable_function(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that `_refreshable_function` is called only once initially.
        """
        # Reset call counter.
        _refreshable_function.call_count = 0
        # Call the function twice with the same input.
        _refreshable_function(3)
        _refreshable_function(3)
        # Verify that the function was only called once (cache hit on the second call).
        self.assertEqual(
            _refreshable_function.call_count,
            1,
            "Function should be called only once initially.",
        )

    def test2(self) -> None:
        """
        Verify that enabling `force_refresh` causes `_refreshable_function` to
        be re-called.
        """
        # Call the function normally.
        res: int = _refreshable_function(3)
        # Enable force_refresh so that the function will be re-called.
        hcacsimp.set_cache_property(
            "user", "_refreshable_function", "force_refresh", True
        )
        # Verify that the function returns the correct value (3 * 10 = 30).
        self.assertEqual(res, 30)
        # Verify that the function's call count has incremented, indicating it was re-called.
        self.assertEqual(
            _refreshable_function.call_count,
            2,
            "Function should be re-called when force_refresh is enabled.",
        )
