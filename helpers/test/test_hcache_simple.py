import json
import logging
import os
import pickle
from typing import Any, Dict

import pandas as pd

import helpers.hcache_simple as hcacsimp
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


@hcacsimp.simple_cache(cache_type="json")
def _cached_function(x: int) -> int:
    """
    Return double the input and cache it using JSON on disk.
    """
    res = x * 2
    return res


@hcacsimp.simple_cache(cache_type="pickle")
def _cached_pickle_function(x: int) -> int:
    """
    Return the square of the input and cache it using pickle on disk.
    """
    res = x**2
    return res


@hcacsimp.simple_cache(cache_type="json")
def _multi_arg_func(a: int, b: int) -> int:
    """
    Return the sum of two numbers.
    """
    res = a + b
    return res


@hcacsimp.simple_cache(cache_type="json")
def _refreshable_function(x: int) -> int:
    """
    Return x multiplied by 10 and update the call count.
    """
    _refreshable_function.call_count += 1
    res = x * 10
    return res


_refreshable_function.call_count = 0


@hcacsimp.simple_cache(cache_type="json")
def _kwarg_func(a: int, b: int = 0) -> int:
    """
    Return the difference between a and b.
    """
    res = a - b
    return res


@hcacsimp.simple_cache(cache_type="json")
def _dummy_cached_function(x: int) -> int:
    """
    Return x plus 100.
    """
    res = x + 100
    return res


# #############################################################################
# BaseCacheTest
# #############################################################################


class BaseCacheTest(hunitest.TestCase):
    """
    Reset cache properties and in-memory caches before each test and remove
    disk cache files afterward.
    """

    def setUp(self) -> None:
        # Reset persistent user cache properties.
        hcacsimp.reset_cache_property("user")
        try:
            hcacsimp.reset_cache_property("system")
        except OSError:
            system_file = hcacsimp.get_cache_property_file("system")
            if os.path.exists(system_file):
                os.remove(system_file)
        # Reset caches for all cached functions using their full names.
        for func_name in [
            "_cached_function",
            "_cached_pickle_function",
            "_multi_arg_func",
            "_refreshable_function",
            "_kwarg_func",
            "_dummy_cached_function",
        ]:
            try:
                hcacsimp.reset_cache(func_name)
            except AssertionError:
                # Reset only the in-memory cache for the function.
                hcacsimp.reset_mem_cache(func_name)
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

    def tearDown(self) -> None:
        # Remove cache files created on disk.
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
                # Remove the cache file from disk.
                os.remove(fname)
        system_file = hcacsimp.get_cache_property_file("system")
        if os.path.exists(system_file):
            os.remove(system_file)


# #############################################################################
# Test_get_cache
# #############################################################################


class Test_get_cache(BaseCacheTest):
    """
    Verify that get_cache returns correct in-memory cache data.
    """

    def test(self) -> None:
        """
        Verify that get_cache returns a cache with the expected key and value.
        """
        # Prepare input.
        _cached_function(2)
        # Call function to test.
        cache: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # CHeck output.
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
        # Prepare input.
        _cached_function(3)
        # Call function to test.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Define the expected cache file name.
        cache_file: str = "cache._cached_function.json"
        # Assert that the cache file exists on disk.
        self.assertTrue(
            os.path.exists(cache_file), "Cache file should exist on disk."
        )

    def test2(self) -> None:
        """
        Verify that the disk cache file contains the expected key and value.
        """
        # Call _cached_function with input 3 to populate the cache.
        _cached_function(3)
        # Flush the cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Define the expected cache file name.
        cache_file: str = "cache._cached_function.json"
        # Open the cache file for reading with UTF-8 encoding.
        with open(cache_file, "r", encoding="utf-8") as f:
            # Load the JSON data from the file into a dictionary.
            disk_cache: Dict[str, Any] = json.load(f)
        # Assert that the key "(3,)" is present in the disk cache.
        self.assertIn("(3,)", disk_cache)
        # Assert that the value for key "(3,)" is 6.
        self.assertEqual(disk_cache["(3,)"], 6)


# #############################################################################
# Test_reset_mem_cache
# #############################################################################


class Test_reset_mem_cache(BaseCacheTest):
    """
    Verify that reset_mem_cache properly clears the in-memory cache.
    """

    def test(self) -> None:
        """
        Verify that the cache is empty after reset_mem_cache is called.
        """
        # Call _cached_function with input 5 to populate the cache.
        _cached_function(5)
        # Reset the in-memory cache for _cached_function.
        hcacsimp.reset_mem_cache("_cached_function")
        # Retrieve the cache after the reset.
        cache_after: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Assert that the key "(5,)" is no longer in the cache.
        self.assertNotIn("(5,)", cache_after)


# #############################################################################
# Test_force_cache_from_disk
# #############################################################################


class Test_force_cache_from_disk(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that the memory cache is empty after a reset.
        """
        # Call _cached_function with input 7 to populate the cache.
        _cached_function(7)
        # Flush the in-memory cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Reset the in-memory cache.
        hcacsimp.reset_mem_cache("_cached_function")
        # Retrieve the in-memory cache.
        mem_cache: Dict[str, Any] = hcacsimp.get_mem_cache("_cached_function")
        # Assert that the key "(7,)" is not in the memory cache.
        self.assertNotIn(
            "(7,)", mem_cache, "Memory cache should be empty after reset."
        )

    def test2(self) -> None:
        """
        Populate disk cache, reset memory, force reload, and verify that the
        key appears.
        """
        # Call _cached_function with input 7 to populate the cache.
        _cached_function(7)
        # Flush the in-memory cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Reset the in-memory cache.
        hcacsimp.reset_mem_cache("_cached_function")
        # Log debug message indicating a forced cache reload from disk.
        _LOG.debug(
            "Test_force_cache_from_disk.test2: Force reload disk cache for '_cached_function'"
        )
        # Force the cache to be reloaded from disk.
        hcacsimp.force_cache_from_disk("_cached_function")
        # Retrieve the complete cache after reloading.
        full_cache: Dict[str, Any] = hcacsimp.get_cache("_cached_function")
        # Assert that the key "(7,)" appears in the reloaded cache.
        self.assertIn(
            "(7,)", full_cache, "After forcing, disk key should appear in memory."
        )


# #############################################################################
# Test_get_cache_perf
# #############################################################################


class Test_get_cache_perf(BaseCacheTest):
    """
    Verify that cache performance tracking works as expected.
    """

    def test1(self) -> None:
        """
        Verify that performance tracking records hits and misses correctly.
        """
        # Log debug message indicating that performance tracking is enabled.
        _LOG.debug(
            "Test_cache_performance.test1: Enable performance tracking for '_cached_function'"
        )
        # Enable cache performance tracking for _cached_function.
        hcacsimp.enable_cache_perf("_cached_function")
        # Log debug message indicating that _cached_function will be called twice.
        _LOG.debug("Test_cache_performance.test1: Call _cached_function(8) twice")
        # Call _cached_function with input 8 (expected to be a cache miss).
        _cached_function(8)
        # Call _cached_function with input 8 again (expected to be a cache hit).
        _cached_function(8)
        # Retrieve performance statistics for _cached_function.
        stats: str = hcacsimp.get_cache_perf_stats("_cached_function")
        # Assert that there is 1 cache hit.
        self.assertIn("hits=1", stats)
        # Assert that there is 1 cache miss.
        self.assertIn("misses=1", stats)

    def test2(self) -> None:
        """
        Verify that disabling performance tracking returns None.
        """
        # Log debug message indicating that performance tracking is being disabled.
        _LOG.debug(
            "Test_cache_performance.test2: Disable performance tracking for '_cached_function'"
        )
        # Disable cache performance tracking for _cached_function.
        hcacsimp.disable_cache_perf("_cached_function")
        # Assert that no performance data is available (i.e. None).
        self.assertIsNone(hcacsimp.get_cache_perf("_cached_function"))


# #############################################################################
# Test_set_cache_property
# #############################################################################


class Test_set_cache_property(BaseCacheTest):
    """
    Verify that set_cache_property and related functions work as expected.
    """

    def test1(self) -> None:
        """
        Verify that setting a valid cache property works and can be retrieved.
        """
        # Set property "report_on_cache_miss" to True for _cached_function.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "report_on_cache_miss", True
        )
        # Retrieve the value of the "report_on_cache_miss" property.
        val: bool = hcacsimp.get_cache_property(
            "user", "_cached_function", "report_on_cache_miss"
        )
        # Assert that the property value is True.
        self.assertTrue(val)

    def test2(self) -> None:
        """
        Verify that resetting cache properties clears previously set
        properties.
        """
        # Set property "report_on_cache_miss" to True.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "report_on_cache_miss", True
        )
        # Assert that the property is indeed True.
        self.assertTrue(
            hcacsimp.get_cache_property(
                "user", "_cached_function", "report_on_cache_miss"
            )
        )
        # Reset all cache properties for the "user" category.
        hcacsimp.reset_cache_property("user")
        # Assert that the property is no longer True after reset.
        self.assertFalse(
            hcacsimp.get_cache_property(
                "user", "_cached_function", "report_on_cache_miss"
            )
        )

    def test3(self) -> None:
        """
        Verify that setting an invalid cache property raises an AssertionError.
        """
        with self.assertRaises(AssertionError):
            # Attempt to set an invalid cache property.
            hcacsimp.set_cache_property(
                "user", "_cached_function", "invalid_prop", True
            )

    def test4(self) -> None:
        """
        Verify that cache_property_to_str returns a string containing the
        property value.
        """
        # Set the "force_refresh" property to True.
        hcacsimp.set_cache_property(
            "user", "_cached_function", "force_refresh", True
        )
        # Convert the cache properties to a string.
        prop_str: str = hcacsimp.cache_property_to_str("user", "_cached_function")
        # Assert that the string contains "force_refresh: True".
        self.assertIn("force_refresh: True", prop_str)


# #############################################################################
# Test_get_cache_func_names
# #############################################################################


class Test_get_cache_func_names(BaseCacheTest):

    def test1(self) -> None:
        """
        Verify that memory cache function names include '_cached_function'.
        """
        # Call _cached_function with input 9 to populate the memory cache.
        _cached_function(9)
        # Retrieve function names from the memory cache.
        mem_funcs = hcacsimp.get_cache_func_names("mem")
        # Assert that "_cached_function" is included in the memory cache function names.
        self.assertIn("_cached_function", mem_funcs)

    def test2(self) -> None:
        """
        Verify that 'all' cache function names include both JSON and pickle
        functions.
        """
        # Call _cached_function with input 2.
        _cached_function(2)
        # Flush _cached_function cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Call _cached_pickle_function with input 2.
        _cached_pickle_function(2)
        # Flush _cached_pickle_function cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_pickle_function")
        # Retrieve all cache function names (both memory and disk).
        all_funcs = hcacsimp.get_cache_func_names("all")
        # Assert that "_cached_function" is included.
        self.assertIn("_cached_function", all_funcs)
        # Assert that "_cached_pickle_function" is included.
        self.assertIn("_cached_pickle_function", all_funcs)

    def test3(self) -> None:
        """
        Verify that disk cache function names include '_cached_function' after
        flushing.
        """
        # Call _cached_function with input 2.
        _cached_function(2)
        # Flush _cached_function cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_function")
        # Retrieve function names from the disk cache.
        disk_funcs = hcacsimp.get_cache_func_names("disk")
        # Assert that "_cached_function" is among the disk cache function names.
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
        # Call _dummy_cached_function with input 1 to populate the cache.
        _dummy_cached_function(1)
        # Retrieve cache statistics as a DataFrame.
        stats_df: pd.DataFrame = hcacsimp.cache_stats_to_str(
            "_dummy_cached_function"
        )
        # Assert that the returned object is a pandas DataFrame.
        self.assertIsInstance(stats_df, pd.DataFrame)
        # Assert that the DataFrame contains a "memory" column.
        self.assertIn("memory", stats_df.columns)
        # Assert that the DataFrame contains a "disk" column.
        self.assertIn("disk", stats_df.columns)


# #############################################################################
# Test_kwarg_func
# #############################################################################


class Test_kwarg_func(BaseCacheTest):

    def _test1(self) -> None:
        """
        Verify that keyword arguments are ignored (use only positional
        arguments for cache keys).
        """
        # Call _kwarg_func with positional argument 5 and keyword argument b=3.
        res1: int = _kwarg_func(5, b=3)
        # Call _kwarg_func with positional argument 5 and keyword argument b=10.
        res2: int = _kwarg_func(5, b=10)
        # Assert that both results are equal.
        self.assertEqual(res1, res2)


# #############################################################################
# Test_multi_arg_func
# #############################################################################


class Test_multi_arg_func(BaseCacheTest):
    """
    Verify that _multi_arg_func caches multiple positional arguments correctly.
    """

    def _test1(self) -> None:
        """
        Verify that _multi_arg_func returns the correct sum.
        """
        # Call _multi_arg_func with inputs 1 and 2.
        res1: int = _multi_arg_func(1, 2)
        # Assert that the result equals 3.
        self.assertEqual(res1, 3)

    def _test2(self) -> None:
        """
        Verify that the cache for _multi_arg_func contains the correct key.
        """
        # Call _multi_arg_func with inputs 1 and 2 to populate the cache.
        _multi_arg_func(1, 2)
        # Retrieve the cache for _multi_arg_func.
        cache: Dict[str, Any] = hcacsimp.get_cache("_multi_arg_func")
        # Assert that the cache key is correctly formatted as either "(1, 2)" or "(1,2)".
        self.assertTrue("(1, 2)" in cache or "(1,2)" in cache)


# #############################################################################
# Test_cached_pickle_function
# #############################################################################


class Test_cached_pickle_function(BaseCacheTest):
    """
    Verify that _cached_pickle_function caches values using pickle.
    """

    def _test1(self) -> None:
        """
        Ensure that _cached_pickle_function returns the correct value and disk
        file.
        """
        # Log debug message indicating that _cached_pickle_function is being called.
        _LOG.debug(
            "Test_cached_pickle_function.test1: Call _cached_pickle_function(4)"
        )
        # Call _cached_pickle_function with input 4 and capture the result.
        res: int = _cached_pickle_function(4)
        # Flush the cache to disk for _cached_pickle_function.
        hcacsimp.flush_cache_to_disk("_cached_pickle_function")
        # Define the expected pickle cache file name.
        cache_file: str = "cache._cached_pickle_function.pkl"
        # Open the pickle cache file in binary read mode.
        with open(cache_file, "rb") as f:
            # Load the cached data from the pickle file into a dictionary.
            disk_cache: Dict[str, Any] = pickle.load(f)
        # Assert that the function returns 16.
        self.assertEqual(res, 16)
        # Assert that the disk cache contains the key "(4,)".
        self.assertIn("(4,)", disk_cache)
        # Assert that the value for key "(4,)" in the disk cache is 16.
        self.assertEqual(disk_cache["(4,)"], 16)


# #############################################################################
# Test_refreshable_function
# #############################################################################


class Test_refreshable_function(BaseCacheTest):
    """
    Verify that _refreshable_function respects the force_refresh property.
    """

    def _test1(self) -> None:
        """
        Verify that _refreshable_function is called only once initially.
        """
        # Reset the call count for _refreshable_function.
        _refreshable_function.call_count = 0
        # Call _refreshable_function with input 3.
        _refreshable_function(3)
        # Call _refreshable_function with input 3 again.
        _refreshable_function(3)
        # Assert that the call count remains 1.
        self.assertEqual(
            _refreshable_function.call_count,
            1,
            "Function should be called only once initially.",
        )

    def _test2(self) -> None:
        """
        Verify that enabling force_refresh causes _refreshable_function to be
        re-called.
        """
        # Call _refreshable_function with input 3 and capture the result.
        res: int = _refreshable_function(3)
        # Set the force_refresh property to True for _refreshable_function.
        hcacsimp.set_cache_property(
            "user", "_refreshable_function", "force_refresh", True
        )
        # Assert that the result is 30.
        self.assertEqual(res, 30)
        # Assert that the call count is now 2, indicating the function was re-called.
        self.assertEqual(
            _refreshable_function.call_count,
            2,
            "Function should be re-called when force_refresh is enabled.",
        )
