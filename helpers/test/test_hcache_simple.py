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
def _cached_json_double(x: int) -> int:
    """
    Return double the input and cache it using JSON.

    :param x: input integer to be doubled
    :return: doubled value (x * 2)
    """
    res = x * 2
    return res


@hcacsimp.simple_cache(cache_type="pickle")
def _cached_pickle_square(x: int) -> int:
    """
    Return the square of the input and cache it using pickle.

    :param x: input integer to be squared
    :return: squared value (x**2)
    """
    res = x**2
    return res


@hcacsimp.simple_cache(cache_type="json")
def _cached_multi_arg_sum(a: int, b: int) -> int:
    """
    Return the sum of two numbers.

    :param a: first number
    :param b: second number
    :return: sum of a and b.
    """
    res = a + b
    return res


@hcacsimp.simple_cache(cache_type="json")
def _cached_refreshable_func(x: int) -> int:
    """
    Return x multiplied by 10 and update the call count.

    :param x: The input integer
    :return: The result of multiplying x by 10
    """
    _cached_refreshable_func.call_count += 1
    res = x * 10
    return res


# Initialize the call counter for the refreshable function.
_cached_refreshable_func.call_count = 0


@hcacsimp.simple_cache(cache_type="json")
def _cached_kwarg_diff(a: int, b: int = 0) -> int:
    """
    Return the difference between a and b.

    :param a: The minuend
    :param b: The subtrahend (defaults to 0)
    :return: The difference (a - b)
    """
    res = a - b
    return res


@hcacsimp.simple_cache(cache_type="json")
def _cached_add_100(x: int) -> int:
    """
    Return x plus 100. Used primarily for testing cache statistics.

    :param x: The input integer
    :return: value (x + 100)
    """
    res = x + 100
    return res



# #############################################################################
# _BaseCacheTest
# #############################################################################

class _BaseCacheTest(hunitest.TestCase):
    """
    Base test class to provide common setup and teardown functionality.

    Instead of using setUp/tearDown, we use set_up_test/tear_down_test along
    with a pytest fixture that ensures these methods run before and after each
    test.
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
        _LOG.debug("set_up_test")
        self._cache_dir = hcacsimp.get_cache_dir()
        hcacsimp.set_cache_dir(hcacsimp.get_cache_dir())

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test:
            - Reset cache(in-memory, disk).
            - Reset cache properties.
        """
        _LOG.debug("tear_down_test")
        hcacsimp.reset_cache("", interactive=False)
        hcacsimp.reset_cache_property()
        hcacsimp.set_cache_dir(self._cache_dir)



# #############################################################################
# Test_get_cache
# #############################################################################

class Test_get_cache(_BaseCacheTest):
    """
    Test get_cache functionality for retrieving cached values.
    """

    def test1(self) -> None:
        """
        Verify that get_cache returns a cache with the expected key and value.
        """
        # Populate the cache by calling _cached_json_double.
        _cached_json_double(2)
        # Retrieve the in-memory cache for _cached_json_double.
        cache: Dict[str, Any] = hcacsimp.get_cache("_cached_json_double")
        # Assert that the key '{"args": [2], "kwargs": {}}' is in the cache and its value is 4.
        self.assertIn('{"args": [2], "kwargs": {}}', cache)
        self.assertEqual(cache['{"args": [2], "kwargs": {}}'], 4)



# #############################################################################
# Test_flush_cache_to_disk
# #############################################################################

class Test_flush_cache_to_disk(_BaseCacheTest):
    """
    Test flush_cache_to_disk functionality for persisting cache to disk.
    """

    def test1(self) -> None:
        """
        Verify that flushing creates a cache file on disk.
        """
        # Call _cached_json_double to populate the cache.
        _cached_json_double(3)
        # Flush the cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        # Define expected cache file name.
        cache_file: str = os.path.join(
            hcacsimp.get_main_cache_dir(), "tmp.cache._cached_json_double.json"
        )
        # Assert that the cache file now exists on disk.
        self.assertTrue(
            os.path.exists(cache_file), "Cache file should exist on disk."
        )

    def test2(self) -> None:
        """
        Verify that the disk cache file contains the expected key and value.
        """
        # Populate cache and flush to disk.
        _cached_json_double(3)
        # Flush the cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        # Define the expected cache file name.
        cache_file: str = os.path.join(
            hcacsimp.get_main_cache_dir(), "tmp.cache._cached_json_double.json"
        )
        # Open and load the disk cache file.
        with open(cache_file, "r", encoding="utf-8") as f:
            # Load the JSON data from the file into a dictionary.
            disk_cache: Dict[str, Any] = json.load(f)
        # Assert that the disk cache contains the key '{"args": [3], "kwargs": {}}' with the correct value.
        self.assertIn('{"args": [3], "kwargs": {}}', disk_cache)
        # Assert that the value for key '{"args": [3], "kwargs": {}}' is 6.
        self.assertEqual(disk_cache['{"args": [3], "kwargs": {}}'], 6)



# #############################################################################
# Test_reset_mem_cache
# #############################################################################

class Test_reset_mem_cache(_BaseCacheTest):
    """
    Test reset_mem_cache functionality for clearing in-memory cache.
    """

    def test1(self) -> None:
        """
        Verify that the cache is empty after `reset_mem_cache` is called.
        """
        # Populate the in-memory cache.
        _cached_json_double(5)
        # Reset the in-memory cache.
        hcacsimp.reset_mem_cache("_cached_json_double")
        # Retrieve the memory cache after reset.
        cache_after: Dict[str, Any] = hcacsimp.get_mem_cache(
            "_cached_json_double"
        )
        # Verify that the key '{"args": [5], "kwargs": {}}' is no longer in the cache.
        self.assertNotIn('{"args": [5], "kwargs": {}}', cache_after)



# #############################################################################
# Test_force_cache_from_disk
# #############################################################################

class Test_force_cache_from_disk(_BaseCacheTest):
    """
    Test force_cache_from_disk functionality for loading cache from disk.
    """

    def test1(self) -> None:
        """
        Verify that the memory cache is empty after a reset.
        """
        # Populate cache and flush to disk.
        _cached_json_double(7)
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        # Reset in-memory cache.
        hcacsimp.reset_mem_cache("_cached_json_double")
        mem_cache: Dict[str, Any] = hcacsimp.get_mem_cache("_cached_json_double")
        # Ensure that the in-memory cache is empty.
        self.assertNotIn(
            '{"args": [7], "kwargs": {}}',
            mem_cache,
            "Memory cache should be empty after reset.",
        )

    def test2(self) -> None:
        """
        Populate disk cache, reset memory, force reload, and verify that the
        key appears.
        """
        # Populate cache, flush to disk, and then reset in-memory cache.
        _cached_json_double(7)
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        hcacsimp.reset_mem_cache("_cached_json_double")
        _LOG.debug("Force reload disk cache for '_cached_json_double'")
        # Force reload cache from disk.
        hcacsimp.force_cache_from_disk("_cached_json_double")
        full_cache: Dict[str, Any] = hcacsimp.get_cache("_cached_json_double")
        # Assert that the key is restored in the in-memory cache.
        self.assertIn(
            '{"args": [7], "kwargs": {}}',
            full_cache,
            "After forcing, disk key should appear in memory.",
        )



# #############################################################################
# Test_get_cache_perf
# #############################################################################

class Test_get_cache_perf(_BaseCacheTest):
    """
    Test cache performance tracking functionality.
    """

    def test1(self) -> None:
        """
        Verify that performance tracking records hits and misses correctly.
        """
        # Enable performance tracking.
        hcacsimp.enable_cache_perf("_cached_json_double")
        _LOG.debug("Call _cached_json_double(8) twice")
        # First call should be a miss.
        _LOG.debug("# First call should be a miss")
        _cached_json_double(8)
        # Second call should be a hit.
        _LOG.debug("# Second call should be a hit")
        _cached_json_double(8)
        # Retrieve performance statistics.
        stats: str = hcacsimp.get_cache_perf_stats("_cached_json_double")
        # Verify that one hit and one miss are recorded.
        self.assertIn("hits=1", stats)
        self.assertIn("misses=1", stats)

    def test2(self) -> None:
        """
        Verify that disabling performance tracking returns None.
        """
        # Disable performance tracking.
        hcacsimp.disable_cache_perf("_cached_json_double")
        # Assert that performance data is no longer available.
        self.assertIsNone(hcacsimp.get_cache_perf("_cached_json_double"))



# #############################################################################
# Test_set_cache_property
# #############################################################################

class Test_set_cache_property(_BaseCacheTest):
    """
    Test set_cache_property and get_cache_property functionality.
    """

    def test1(self) -> None:
        """
        Verify that setting a valid cache property works and can be retrieved.
        """
        # Set a valid cache property.
        hcacsimp.set_cache_property(
            "_cached_json_double", "report_on_cache_miss", True
        )
        # Retrieve and verify the property.
        val: bool = hcacsimp.get_cache_property(
            "_cached_json_double", "report_on_cache_miss"
        )
        self.assertTrue(val)

    def test2(self) -> None:
        """
        Verify that resetting cache properties clears previously set
        properties.
        """
        # Set and verify the cache property.
        hcacsimp.set_cache_property(
            "_cached_json_double", "report_on_cache_miss", True
        )
        self.assertTrue(
            hcacsimp.get_cache_property(
                "_cached_json_double", "report_on_cache_miss"
            )
        )
        # Reset all cache properties.
        hcacsimp.reset_cache_property()
        # Verify that the property is no longer True.
        self.assertFalse(
            hcacsimp.get_cache_property(
                "_cached_json_double", "report_on_cache_miss"
            )
        )

    def test3(self) -> None:
        """
        Verify that setting an invalid cache property raises an error.
        """
        # Verify that setting an invalid property raises an error.
        with self.assertRaises(AssertionError):
            hcacsimp.set_cache_property(
                "_cached_json_double", "invalid_prop", True
            )

    def test4(self) -> None:
        """
        Verify return of a string containing the property value.
        """
        # Set force_refresh property and verify that it appears in the properties string.
        hcacsimp.set_cache_property("_cached_json_double", "force_refresh", True)
        prop_str: str = hcacsimp.cache_property_to_str("_cached_json_double")
        # Check output.
        self.assertIn("force_refresh: True", prop_str)



# #############################################################################
# Test_get_cache_func_names
# #############################################################################

class Test_get_cache_func_names(_BaseCacheTest):
    """
    Test get_cache_func_names functionality for retrieving cached function names.
    """

    def test1(self) -> None:
        """
        Verify that memory cache function names include `_cached_json_double`.
        """
        # Populate in-memory cache.
        _cached_json_double(9)
        # Retrieve function names from the memory cache.
        mem_funcs = hcacsimp.get_cache_func_names("mem")
        # Check output.
        self.assertIn("_cached_json_double", mem_funcs)

    def test2(self) -> None:
        """
        Verify that all cache function names include both JSON and pickle
        functions.
        """
        # Populate and flush caches for JSON and pickle functions.
        _cached_json_double(2)
        # Flush _cached_json_double cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        # Call _cached_pickle_square with input 2.
        _cached_pickle_square(2)
        # Flush _cached_pickle_square cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_pickle_square")
        # Retrieve all cache function names (both memory and disk).
        all_funcs = hcacsimp.get_cache_func_names("all")
        # Check output.
        self.assertIn("_cached_json_double", all_funcs)
        self.assertIn("_cached_pickle_square", all_funcs)

    def test3(self) -> None:
        """
        Verify that disk cache function names include `_cached_json_double` after
        flushing.
        """
        # Flush JSON cache to disk and verify disk cache function names.
        _cached_json_double(2)
        # Flush _cached_json_double cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        # Retrieve function names from the disk cache.
        disk_funcs = hcacsimp.get_cache_func_names("disk")
        # Check output.
        self.assertIn("_cached_json_double", disk_funcs)



# #############################################################################
# Test_cache_stats_to_str
# #############################################################################

class Test_cache_stats_to_str(_BaseCacheTest):
    """
    Test cache_stats_to_str functionality for generating cache statistics.
    """

    def test1(self) -> None:
        """
        Verify that cache_stats_to_str returns a DataFrame with 'memory' and
        'disk' columns.
        """
        # Populate cache.
        _cached_add_100(1)
        stats_df: pd.DataFrame = hcacsimp.cache_stats_to_str("_cached_add_100")
        # Assert that the returned object is a DataFrame.
        self.assertIsInstance(stats_df, pd.DataFrame)
        # Verify that it contains the 'memory' and 'disk' columns.
        self.assertIn("memory", stats_df.columns)
        self.assertIn("disk", stats_df.columns)



# #############################################################################
# Test__cached_kwarg_diff
# #############################################################################

class Test__cached_kwarg_diff(_BaseCacheTest):
    """
    Test caching behavior with keyword arguments.
    """

    def test1(self) -> None:
        """
        Test that verifies keyword arguments are handled correctly by the
        cache.
        """
        # Call with different keyword argument values.
        res1: int = _cached_kwarg_diff(5, b=3)
        res2: int = _cached_kwarg_diff(5, b=10)
        # Both calls should return the different result as both args, kwargs are used for caching.
        self.assertNotEqual(res1, res2)



# #############################################################################
# Test__cached_multi_arg_sum
# #############################################################################

class Test__cached_multi_arg_sum(_BaseCacheTest):
    """
    Test caching behavior with multiple positional arguments.
    """

    def test1(self) -> None:
        """
        Verify that the cache for _cached_multi_arg_sum contains the correct key.
        """
        # Populate the cache.
        _cached_multi_arg_sum(1, 2)
        cache: Dict[str, Any] = hcacsimp.get_cache("_cached_multi_arg_sum")
        print("cache__ ", cache)
        # Verify that the cache key is formatted as  '{"args": [1, 2], "kwargs": {}}'.
        self.assertIn('{"args": [1, 2], "kwargs": {}}', cache)



# #############################################################################
# Test__cached_pickle_square
# #############################################################################

class Test__cached_pickle_square(_BaseCacheTest):
    """
    Test caching with pickle serialization.
    """

    def test1(self) -> None:
        """
        Ensure that _cached_pickle_square returns the correct value and disk
        file.
        """
        # Call the function to square the input.
        res: int = _cached_pickle_square(4)
        # Flush the cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_pickle_square")
        cache_file: str = os.path.join(
            hcacsimp.get_main_cache_dir(), "tmp.cache._cached_pickle_square.pkl"
        )
        # Open and load the pickle cache file.
        with open(cache_file, "rb") as f:
            disk_cache: Dict[str, Any] = pickle.load(f)
        # Verify the result and cache contents.
        self.assertEqual(res, 16)
        self.assertIn('{"args": [4], "kwargs": {}}', disk_cache)
        self.assertEqual(disk_cache['{"args": [4], "kwargs": {}}'], 16)



# #############################################################################
# Test__cached_refreshable_func
# #############################################################################

class Test__cached_refreshable_func(_BaseCacheTest):
    """
    Test force_refresh cache property functionality.
    """

    def test1(self) -> None:
        """
        Verify that `_cached_refreshable_func` is called only once initially.
        """
        # Reset call counter.
        _cached_refreshable_func.call_count = 0
        # Call the function twice with the same input.
        _cached_refreshable_func(3)
        _cached_refreshable_func(3)
        # Verify that the function was only called once (cache hit on the second
        # call).
        self.assertEqual(
            _cached_refreshable_func.call_count,
            1,
            "Function should be called only once initially.",
        )

    def test2(self) -> None:
        """
        Verify that enabling `force_refresh` causes `_cached_refreshable_func` to
        be re-called.
        """
        # Call the function normally.
        res: int = _cached_refreshable_func(3)
        # Enable force_refresh so that the function will be re-called.
        hcacsimp.set_cache_property(
            "_cached_refreshable_func", "force_refresh", True
        )
        # Verify that the function returns the correct value (3 * 10 = 30).
        self.assertEqual(res, 30)
        # Verify that the function's call count has incremented, indicating it
        # was re-called.
        self.assertEqual(
            _cached_refreshable_func.call_count,
            2,
            "Function should be re-called when force_refresh is enabled.",
        )



# #############################################################################
# Test_reset_cache_perf
# #############################################################################

class Test_reset_cache_perf(_BaseCacheTest):
    """
    Test reset_cache_perf functionality for resetting performance statistics.
    """

    def test1(self) -> None:
        """
        Verify that reset_cache_perf resets stats for a single function.
        """
        # Prepare inputs.
        hcacsimp.enable_cache_perf("_cached_json_double")
        _cached_json_double(5)
        _cached_json_double(5)
        # Run test.
        hcacsimp.reset_cache_perf("_cached_json_double")
        # Check outputs.
        perf = hcacsimp.get_cache_perf("_cached_json_double")
        self.assertEqual(perf["tot"], 0)
        self.assertEqual(perf["hits"], 0)
        self.assertEqual(perf["misses"], 0)

    def test2(self) -> None:
        """
        Verify that reset_cache_perf with empty func_name resets all
        functions.
        """
        # Prepare inputs.
        hcacsimp.enable_cache_perf("_cached_json_double")
        hcacsimp.enable_cache_perf("_cached_multi_arg_sum")
        _cached_json_double(1)
        _cached_multi_arg_sum(1, 2)
        # Run test.
        hcacsimp.reset_cache_perf("")
        # Check outputs.
        perf1 = hcacsimp.get_cache_perf("_cached_json_double")
        perf2 = hcacsimp.get_cache_perf("_cached_multi_arg_sum")
        self.assertEqual(perf1["tot"], 0)
        self.assertEqual(perf2["tot"], 0)



# #############################################################################
# Test_disable_cache_perf
# #############################################################################

class Test_disable_cache_perf(_BaseCacheTest):
    """
    Test disable_cache_perf functionality for disabling performance tracking.
    """

    def test1(self) -> None:
        """
        Verify that disable_cache_perf with empty func_name disables all
        functions.
        """
        # Prepare inputs.
        hcacsimp.enable_cache_perf("_cached_json_double")
        hcacsimp.enable_cache_perf("_cached_multi_arg_sum")
        _cached_json_double(1)
        _cached_multi_arg_sum(1, 2)
        # Run test.
        hcacsimp.disable_cache_perf("")
        # Check outputs.
        perf1 = hcacsimp.get_cache_perf("_cached_json_double")
        perf2 = hcacsimp.get_cache_perf("_cached_multi_arg_sum")
        # After disabling, perf should be None.
        self.assertIsNone(perf1)
        self.assertIsNone(perf2)



# #############################################################################
# Test_get_cache_perf_stats
# #############################################################################

class Test_get_cache_perf_stats(_BaseCacheTest):
    """
    Test get_cache_perf_stats for retrieving performance statistics.
    """

    def test1(self) -> None:
        """
        Verify that get_cache_perf_stats returns empty string when no stats
        exist.
        """
        # Prepare inputs.
        # Ensure no perf stats exist for a non-tracked function.
        hcacsimp.disable_cache_perf("_cached_json_double")
        # Run test.
        stats = hcacsimp.get_cache_perf_stats("_cached_json_double")
        # Check outputs.
        self.assertEqual(stats, "")



# #############################################################################
# Test_cache_property_to_str
# #############################################################################

class Test_cache_property_to_str(_BaseCacheTest):
    """
    Test cache_property_to_str for converting properties to string.
    """

    def test1(self) -> None:
        """
        Verify that cache_property_to_str with empty func_name returns all
        functions.
        """
        # Prepare inputs.
        # Call functions to ensure they are cached.
        _cached_json_double(1)
        _cached_multi_arg_sum(1, 2)
        hcacsimp.set_cache_property("_cached_json_double", "force_refresh", True)
        hcacsimp.set_cache_property("_cached_multi_arg_sum", "enable_perf", True)
        # Run test.
        result = hcacsimp.cache_property_to_str("")
        # Check outputs.
        self.assertIn("_cached_json_double", result)
        self.assertIn("_cached_multi_arg_sum", result)
        self.assertIn("force_refresh: True", result)
        self.assertIn("enable_perf: True", result)



# #############################################################################
# Test_reset_mem_cache_all
# #############################################################################

class Test_reset_mem_cache_all(_BaseCacheTest):
    """
    Test reset_mem_cache with empty func_name parameter.
    """

    def test1(self) -> None:
        """
        Verify that reset_mem_cache with empty func_name resets all caches.
        """
        # Prepare inputs.
        _cached_json_double(1)
        _cached_multi_arg_sum(2, 3)
        # Run test.
        hcacsimp.reset_mem_cache("")
        # Check outputs.
        cache1 = hcacsimp.get_mem_cache("_cached_json_double")
        cache2 = hcacsimp.get_mem_cache("_cached_multi_arg_sum")
        self.assertEqual(len(cache1), 0)
        self.assertEqual(len(cache2), 0)



# #############################################################################
# Test_reset_disk_cache_all
# #############################################################################

class Test_reset_disk_cache_all(_BaseCacheTest):
    """
    Test reset_disk_cache with empty func_name parameter.
    """

    def test1(self) -> None:
        """
        Verify that reset_disk_cache with empty func_name removes all cache
        files.
        """
        # Prepare inputs.
        _cached_json_double(1)
        _cached_multi_arg_sum(2, 3)
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        hcacsimp.flush_cache_to_disk("_cached_multi_arg_sum")
        # Run test.
        hcacsimp.reset_disk_cache("", interactive=False)
        # Check outputs.
        cache_file1 = os.path.join(
            hcacsimp.get_main_cache_dir(), "tmp.cache._cached_json_double.json"
        )
        self.assertFalse(os.path.exists(cache_file1))
        cache_file2 = os.path.join(
            hcacsimp.get_main_cache_dir(), "tmp.cache._cached_multi_arg_sum.json"
        )
        self.assertFalse(os.path.exists(cache_file2))



# #############################################################################
# Test_force_cache_from_disk_all
# #############################################################################

class Test_force_cache_from_disk_all(_BaseCacheTest):
    """
    Test force_cache_from_disk with empty func_name parameter.
    """

    def test1(self) -> None:
        """
        Verify that force_cache_from_disk with empty func_name loads all
        caches.
        """
        # Prepare inputs.
        _cached_json_double(1)
        _cached_multi_arg_sum(2, 3)
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        hcacsimp.flush_cache_to_disk("_cached_multi_arg_sum")
        hcacsimp.reset_mem_cache("")
        # Run test.
        hcacsimp.force_cache_from_disk("")
        # Check outputs.
        cache1 = hcacsimp.get_mem_cache("_cached_json_double")
        cache2 = hcacsimp.get_mem_cache("_cached_multi_arg_sum")
        self.assertGreater(len(cache1), 0)
        self.assertGreater(len(cache2), 0)



# #############################################################################
# Test_flush_cache_to_disk_all
# #############################################################################

class Test_flush_cache_to_disk_all(_BaseCacheTest):
    """
    Test flush_cache_to_disk with empty func_name parameter.
    """

    def test1(self) -> None:
        """
        Verify that flush_cache_to_disk with empty func_name flushes all
        caches.
        """
        # Prepare inputs.
        _cached_json_double(1)
        _cached_multi_arg_sum(2, 3)
        # Run test.
        hcacsimp.flush_cache_to_disk("")
        # Check outputs.
        cache_file1 = os.path.join(
            hcacsimp.get_main_cache_dir(), "tmp.cache._cached_json_double.json"
        )
        self.assertTrue(os.path.exists(cache_file1))
        cache_file2 = os.path.join(
            hcacsimp.get_main_cache_dir(), "tmp.cache._cached_multi_arg_sum.json"
        )
        self.assertTrue(os.path.exists(cache_file2))



# #############################################################################
# Test_cache_stats_to_str_all
# #############################################################################

class Test_cache_stats_to_str_all(_BaseCacheTest):
    """
    Test cache_stats_to_str with empty func_name parameter.
    """

    def test1(self) -> None:
        """
        Verify that cache_stats_to_str with empty func_name returns stats for
        all functions.
        """
        # Prepare inputs.
        _cached_json_double(1)
        _cached_multi_arg_sum(2, 3)
        # Run test.
        result = hcacsimp.cache_stats_to_str("")
        # Check outputs.
        self.assertIsNotNone(result)
        self.assertIn("_cached_json_double", result.index)
        self.assertIn("_cached_multi_arg_sum", result.index)



# #############################################################################
# Test_get_cache_func_names_invalid
# #############################################################################

class Test_get_cache_func_names_invalid(_BaseCacheTest):
    """
    Test get_cache_func_names with invalid type parameter.
    """

    def test1(self) -> None:
        """
        Verify that get_cache_func_names raises ValueError for invalid type.
        """
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            hcacsimp.get_cache_func_names("invalid_type")
        self.assertIn("Invalid type", str(cm.exception))



# #############################################################################
# Test__get_cache_file_name
# #############################################################################

class Test__get_cache_file_name(_BaseCacheTest):
    """
    Test _get_cache_file_name for invalid cache type.
    """

    def test1(self) -> None:
        """
        Verify that _get_cache_file_name raises ValueError for invalid cache
        type.
        """
        # Prepare inputs.
        hcacsimp.set_cache_property("_cached_json_double", "type", "invalid")
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            hcacsimp._get_cache_file_name("_cached_json_double")
        self.assertIn("Invalid cache type", str(cm.exception))
        # Reset type to valid value for teardown.
        hcacsimp.set_cache_property("_cached_json_double", "type", "json")



# #############################################################################
# Test__save_cache_dict_to_disk
# #############################################################################

class Test__save_cache_dict_to_disk(_BaseCacheTest):
    """
    Test _save_cache_dict_to_disk for invalid cache type.
    """

    def test1(self) -> None:
        """
        Verify that _save_cache_dict_to_disk raises ValueError for invalid
        cache type.
        """
        # Prepare inputs.
        hcacsimp.set_cache_property("_cached_json_double", "type", "invalid")
        data = {"key": "value"}
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            hcacsimp._save_cache_dict_to_disk("_cached_json_double", data)
        self.assertIn("Invalid cache type", str(cm.exception))
        # Reset type to valid value for teardown.
        hcacsimp.set_cache_property("_cached_json_double", "type", "json")



# #############################################################################
# Test_get_disk_cache_invalid
# #############################################################################

class Test_get_disk_cache_invalid(_BaseCacheTest):
    """
    Test get_disk_cache for invalid cache type.
    """

    def test1(self) -> None:
        """
        Verify that get_disk_cache raises ValueError for invalid cache type.
        """
        # Prepare inputs.
        hcacsimp.set_cache_property("_cached_json_double", "type", "invalid")
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            hcacsimp.get_disk_cache("_cached_json_double")
        self.assertIn("Invalid cache type", str(cm.exception))
        # Reset type to valid value for teardown.
        hcacsimp.set_cache_property("_cached_json_double", "type", "json")


# #############################################################################
# Test_cache_mode
# #############################################################################


@hcacsimp.simple_cache(cache_type="json")
def _cache_mode_function(x: int) -> int:
    """
    Test function to verify cache_mode parameter.

    :param x: input integer
    :return: x * 5
    """
    _cache_mode_function.call_count += 1
    res = x * 5
    return res


_cache_mode_function.call_count = 0



# #############################################################################
# Test_cache_mode
# #############################################################################

class Test_cache_mode(_BaseCacheTest):
    """
    Test cache_mode parameter functionality.
    """

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test.
        """
        super().set_up_test()
        hcacsimp.set_cache_property("_cache_mode_function", "type", "json")
        _cache_mode_function.call_count = 0

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test.
        """
        super().tear_down_test()
        hcacsimp.reset_cache("_cache_mode_function", interactive=False)

    def test1(self) -> None:
        """
        Verify that setting force_refresh property forces cache refresh.
        """
        # Prepare inputs.
        _cache_mode_function(10)
        initial_count = _cache_mode_function.call_count
        # Set force_refresh property.
        hcacsimp.set_cache_property(
            "_cache_mode_function", "force_refresh", True
        )
        # Run test.
        result = _cache_mode_function(10)
        # Check outputs.
        self.assertEqual(result, 50)
        self.assertEqual(_cache_mode_function.call_count, initial_count + 1)

    def test2(self) -> None:
        """
        Verify that setting abort_on_cache_miss property aborts on cache miss.
        """
        # Prepare inputs.
        hcacsimp.set_cache_property(
            "_cache_mode_function", "abort_on_cache_miss", True
        )
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            _cache_mode_function(99)
        self.assertIn("Cache miss", str(cm.exception))

    def test3(self) -> None:
        """
        Verify that calling with different arguments bypasses cache.
        """
        # Prepare inputs.
        _cache_mode_function(15)
        initial_count = _cache_mode_function.call_count
        # Run test.
        result1 = _cache_mode_function(16)
        result2 = _cache_mode_function(17)
        # Check outputs.
        self.assertEqual(result1, 80)
        self.assertEqual(result2, 85)
        self.assertEqual(_cache_mode_function.call_count, initial_count + 2)


# #############################################################################
# Test_abort_on_cache_miss
# #############################################################################


@hcacsimp.simple_cache(cache_type="json")
def _abort_test_function(x: int) -> int:
    """
    Test function to verify abort_on_cache_miss parameter.

    :param x: input integer
    :return: x * 7
    """
    res = x * 7
    return res



# #############################################################################
# Test_abort_on_cache_miss
# #############################################################################

class Test_abort_on_cache_miss(_BaseCacheTest):
    """
    Test abort_on_cache_miss functionality.
    """

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test.
        """
        super().set_up_test()
        hcacsimp.set_cache_property("_abort_test_function", "type", "json")

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test.
        """
        super().tear_down_test()
        hcacsimp.reset_cache("_abort_test_function", interactive=False)

    def test1(self) -> None:
        """
        Verify that abort_on_cache_miss=True raises error on cache miss.
        """
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            _abort_test_function(100, abort_on_cache_miss=True)
        self.assertIn("Cache miss", str(cm.exception))


# #############################################################################
# Test_report_on_cache_miss
# #############################################################################


@hcacsimp.simple_cache(cache_type="json")
def _report_test_function(x: int) -> int:
    """
    Test function to verify report_on_cache_miss parameter.

    :param x: input integer
    :return: x * 8
    """
    res = x * 8
    return res



# #############################################################################
# Test_report_on_cache_miss
# #############################################################################

class Test_report_on_cache_miss(_BaseCacheTest):
    """
    Test report_on_cache_miss functionality.
    """

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test.
        """
        super().set_up_test()
        hcacsimp.set_cache_property("_report_test_function", "type", "json")

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test.
        """
        super().tear_down_test()
        hcacsimp.reset_cache("_report_test_function", interactive=False)

    def test1(self) -> None:
        """
        Verify that report_on_cache_miss=True returns '_cache_miss_' on miss.
        """
        # Run test.
        result = _report_test_function(200, report_on_cache_miss=True)
        # Check outputs.
        self.assertEqual(result, "_cache_miss_")


# #############################################################################
# Test_write_through
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _write_through_function(x: int) -> int:
    """
    Test function to verify write_through parameter.

    :param x: input integer
    :return: x * 9
    """
    res = x * 9
    return res



# #############################################################################
# Test_write_through
# #############################################################################

class Test_write_through(_BaseCacheTest):
    """
    Test write_through functionality for automatic disk caching.
    """

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test.
        """
        super().set_up_test()
        hcacsimp.set_cache_property("_write_through_function", "type", "json")

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test.
        """
        super().tear_down_test()
        hcacsimp.reset_cache("_write_through_function", interactive=False)

    def test1(self) -> None:
        """
        Verify that write_through=True automatically writes to disk.
        """
        # Run test.
        _write_through_function(11)
        # Check outputs.
        cache_file = os.path.join(
            hcacsimp.get_main_cache_dir(),
            "tmp.cache._write_through_function.json",
        )
        self.assertTrue(os.path.exists(cache_file))
        with open(cache_file, "r", encoding="utf-8") as f:
            disk_cache = json.load(f)
        self.assertIn('{"args": [11], "kwargs": {}}', disk_cache)
        self.assertEqual(disk_cache['{"args": [11], "kwargs": {}}'], 99)


# #############################################################################
# Test_cache_mode_parameter
# #############################################################################


@hcacsimp.simple_cache(cache_type="json")
def _test_cache_mode_kwarg(x: int, **kwargs) -> int:
    """
    Test function that accepts kwargs to test cache_mode parameter.

    :param x: input integer
    :param kwargs: additional keyword arguments
    :return: x * 3
    """
    _test_cache_mode_kwarg.call_count += 1
    res = x * 3
    return res


_test_cache_mode_kwarg.call_count = 0



# #############################################################################
# Test_cache_mode_parameter
# #############################################################################

class Test_cache_mode_parameter(_BaseCacheTest):
    """
    Test cache_mode parameter as a keyword argument.
    """

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test.
        """
        super().set_up_test()
        hcacsimp.set_cache_property("_test_cache_mode_kwarg", "type", "json")
        _test_cache_mode_kwarg.call_count = 0

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test.
        """
        super().tear_down_test()
        hcacsimp.reset_cache("_test_cache_mode_kwarg", interactive=False)

    def test1(self) -> None:
        """
        Verify that cache_mode='REFRESH_CACHE' keyword forces refresh.
        """
        # Prepare inputs.
        _test_cache_mode_kwarg(20)
        initial_count = _test_cache_mode_kwarg.call_count
        # Run test.
        result = _test_cache_mode_kwarg(20, cache_mode="REFRESH_CACHE")
        # Check outputs.
        self.assertEqual(result, 60)
        self.assertEqual(_test_cache_mode_kwarg.call_count, initial_count + 1)

    def test2(self) -> None:
        """
        Verify that cache_mode='HIT_CACHE_OR_ABORT' raises error on miss.
        """
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            _test_cache_mode_kwarg(88, cache_mode="HIT_CACHE_OR_ABORT")
        self.assertIn("Cache miss", str(cm.exception))

    def test3(self) -> None:
        """
        Verify that cache_mode='DISABLE_CACHE' bypasses cache.
        """
        # Prepare inputs.
        _test_cache_mode_kwarg(30)
        initial_count = _test_cache_mode_kwarg.call_count
        # Run test.
        result1 = _test_cache_mode_kwarg(30, cache_mode="DISABLE_CACHE")
        result2 = _test_cache_mode_kwarg(30, cache_mode="DISABLE_CACHE")
        # Check outputs.
        self.assertEqual(result1, 90)
        self.assertEqual(result2, 90)
        self.assertEqual(_test_cache_mode_kwarg.call_count, initial_count + 2)
