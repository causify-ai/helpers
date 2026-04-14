import copy
import logging
import os
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

    Instead of using setUp/tearDown, we use set_up_test/tear_down_test
    along with a pytest fixture that ensures these methods run before
    and after each test.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self, monkeypatch):
        # Store monkeypatch for use in tests.
        self.monkeypatch = monkeypatch
        # Run common setup before each test.
        self.set_up_test()
        yield
        # Run common teardown after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test:

        - Isolate all global variables to prevent race conditions.
        - Set cache directory to test scratch space.
        """
        _LOG.debug("set_up_test")
        super().setUp()
        # Isolate configuration globals.
        scratch_space = self.get_scratch_space()
        self.monkeypatch.setattr(hcacsimp, "_CACHE_DIR", scratch_space)
        self.monkeypatch.setattr(
            hcacsimp, "_CACHE_FILE_PREFIX", hcacsimp._CACHE_FILE_PREFIX
        )
        self.monkeypatch.setattr(hcacsimp, "_S3_BUCKET", hcacsimp._S3_BUCKET)
        self.monkeypatch.setattr(hcacsimp, "_S3_PREFIX", hcacsimp._S3_PREFIX)
        self.monkeypatch.setattr(hcacsimp, "_AWS_PROFILE", hcacsimp._AWS_PROFILE)
        # Isolate data structure globals.
        self.monkeypatch.setattr(hcacsimp, "_CACHE", {})
        # Use deepcopy for _CACHE_PROPERTY to preserve decorator-set properties.
        self.monkeypatch.setattr(
            hcacsimp, "_CACHE_PROPERTY", copy.deepcopy(hcacsimp._CACHE_PROPERTY)
        )
        self.monkeypatch.setattr(hcacsimp, "_CACHE_PERF", {})
        self.monkeypatch.setattr(hcacsimp, "_S3_AUTO_PULL_ATTEMPTED", set())

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test.

        All global variables are isolated via monkeypatch, so they are
        automatically restored after each test.
        """
        _LOG.debug("tear_down_test")


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
        # Assert that the key '{"args": [2], "kwargs": {}}' is in the cache and
        # its value is 4.
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
        cache_file = hcacsimp._get_cache_file_name("_cached_json_double")
        # Assert that the cache file now exists on disk.
        self.assertTrue(
            os.path.exists(cache_file),
            f"Cache file {cache_file} should exist on disk.",
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
        cache_file = hcacsimp._get_cache_file_name("_cached_json_double")
        # # Open and load the disk cache file.
        disk_cache = hcacsimp._load_func_cache_data_from_file(cache_file, "json")
        # Assert that the disk cache contains the key '{"args": [3], "kwargs":
        # {}}' with the correct value.
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
# Test_get_cached_func_names
# #############################################################################


class Test_get_cached_func_names(_BaseCacheTest):
    """
    Test get_cached_func_names functionality for retrieving cached function
    names.
    """

    def test1(self) -> None:
        """
        Verify that memory cache function names include `_cached_json_double`.
        """
        # Populate in-memory cache.
        _cached_json_double(9)
        # Retrieve function names from the memory cache.
        mem_funcs = hcacsimp.get_cached_func_names("mem")
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
        # Retrieve all local cached function names (both memory and disk).
        all_funcs = hcacsimp.get_cached_func_names("local")
        # Check output.
        self.assertIn("_cached_json_double", all_funcs)
        self.assertIn("_cached_pickle_square", all_funcs)

    def test3(self) -> None:
        """
        Verify that disk cache function names include `_cached_json_double`
        after flushing.
        """
        # Flush JSON cache to disk and verify disk cache function names.
        _cached_json_double(2)
        # Flush _cached_json_double cache to disk.
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        # Retrieve function names from the disk cache.
        disk_funcs = hcacsimp.get_cached_func_names("disk")
        # Check output.
        self.assertIn("_cached_json_double", disk_funcs)

    def test4(self) -> None:
        """
        Verify that disk-cached function names include functions with custom
        cache_dir and cache_prefix.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        custom_cache_dir = os.path.join(scratch_dir, "custom_cache")

        # Create a cached function with custom cache location.
        @hcacsimp.simple_cache(
            cache_type="json",
            cache_dir=custom_cache_dir,
            cache_prefix="custom_prefix",
        )
        def _custom_location_func(x: int) -> int:
            return x * 3

        # Run.
        _custom_location_func(5)
        hcacsimp.flush_cache_to_disk("_custom_location_func")
        disk_funcs = hcacsimp.get_cached_func_names("disk")
        # Check.
        self.assertIn("_custom_location_func", disk_funcs)


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
        Verify that the cache for _cached_multi_arg_sum contains the correct
        key.
        """
        # Populate the cache.
        _cached_multi_arg_sum(1, 2)
        cache: Dict[str, Any] = hcacsimp.get_cache("_cached_multi_arg_sum")
        _LOG.debug("cache=%s", cache)
        # Verify that the cache key is formatted as '{"args": [1, 2], "kwargs": {}}'.
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
        cache_file = hcacsimp._get_cache_file_name("_cached_pickle_square")
        # Open and load the pickle cache file.
        func_cache_data = hcacsimp._load_func_cache_data_from_file(
            cache_file, "pickle"
        )
        _LOG.debug("func_cache_data=%s", func_cache_data)
        # Verify the result and cache contents.
        self.assertEqual(res, 16)
        self.assertIn('{"args": [4], "kwargs": {}}', func_cache_data)
        self.assertEqual(func_cache_data['{"args": [4], "kwargs": {}}'], 16)


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
        Verify that enabling `force_refresh` causes `_cached_refreshable_func`
        to be re-called.
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
        Verify that reset_cache_perf with empty func_name resets all functions.
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
        hcacsimp.set_cache_property(
            "_cached_multi_arg_sum", "write_through", True
        )
        # Run test.
        result = hcacsimp.cache_property_to_str("")
        # Check outputs.
        self.assertIn("_cached_json_double", result)
        self.assertIn("_cached_multi_arg_sum", result)
        self.assertIn("force_refresh: True", result)
        self.assertIn("write_through: True", result)


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
        cache_file1 = hcacsimp._get_cache_file_name("_cached_json_double")
        self.assertFalse(os.path.exists(cache_file1))
        cache_file2 = hcacsimp._get_cache_file_name("_cached_multi_arg_sum")
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
        cache_file1 = hcacsimp._get_cache_file_name("_cached_json_double")
        self.assertTrue(os.path.exists(cache_file1))
        #
        cache_file2 = hcacsimp._get_cache_file_name("_cached_multi_arg_sum")
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
# Test_get_cached_func_names_invalid
# #############################################################################


class Test_get_cached_func_names_invalid(_BaseCacheTest):
    """
    Test get_cached_func_names with invalid type parameter.
    """

    def test1(self) -> None:
        """
        Verify that get_cached_func_names raises ValueError for invalid type.
        """
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            hcacsimp.get_cached_func_names("invalid_type")
        self.assertIn("Invalid type", str(cm.exception))


# #############################################################################
# Test__get_cache_file_name
# #############################################################################


class Test__get_cache_file_name(_BaseCacheTest):
    """
    Test _get_cache_file_name for various configurations.
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

    def test2(self) -> None:
        """
        Test global cache_dir + global cache_prefix (default fallback).

        Verifies that when no per-function properties are set, the
        function falls back to global cache_dir and cache_prefix.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        # Run.
        actual = hcacsimp._get_cache_file_name(func_name)
        # Check.
        global_cache_dir = hcacsimp.get_cache_dir()
        global_cache_prefix = hcacsimp.get_cache_file_prefix()
        expected = os.path.join(
            global_cache_dir, f"{global_cache_prefix}.{func_name}.json"
        )
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test per-function cache_dir + global cache_prefix.

        Verifies that per-function cache_dir is used while falling back
        to global cache_prefix.
        """
        # Prepare inputs.
        custom_dir = "/tmp/custom_test_dir"
        func_name = "_cached_json_double"
        hcacsimp.set_cache_property(func_name, "cache_dir", custom_dir)
        # Run.
        actual = hcacsimp._get_cache_file_name(func_name)
        # Check.
        global_cache_prefix = hcacsimp.get_cache_file_prefix()
        expected = os.path.join(
            custom_dir, f"{global_cache_prefix}.{func_name}.json"
        )
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test global cache_dir + per-function cache_prefix.

        Verifies that per-function cache_prefix is used while falling
        back to global cache_dir.
        """
        # Prepare inputs.
        custom_prefix = "custom_prefix"
        func_name = "_cached_json_double"
        hcacsimp.set_cache_property(func_name, "cache_prefix", custom_prefix)
        # Run.
        actual = hcacsimp._get_cache_file_name(func_name)
        # Check.
        global_cache_dir = hcacsimp.get_cache_dir()
        expected = os.path.join(
            global_cache_dir, f"{custom_prefix}.{func_name}.json"
        )
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test per-function cache_dir + per-function cache_prefix.

        Verifies that both per-function cache_dir and cache_prefix are
        used when both are set (no fallback to global values).
        """
        # Prepare inputs.
        custom_dir = "/tmp/custom_test_dir_both"
        custom_prefix = "custom_prefix_both"
        func_name = "_cached_json_double"
        hcacsimp.set_cache_property(func_name, "cache_dir", custom_dir)
        hcacsimp.set_cache_property(func_name, "cache_prefix", custom_prefix)
        # Run.
        actual = hcacsimp._get_cache_file_name(func_name)
        # Check.
        expected = os.path.join(custom_dir, f"{custom_prefix}.{func_name}.json")
        self.assertEqual(actual, expected)

    def test6(self) -> None:
        """
        Test file path format for pickle cache type.

        Verifies that _get_cache_file_name returns correct file
        extension for pickle (.pkl) cache type.
        """
        # Prepare inputs.
        func_name = "_cached_pickle_square"
        # Run.
        actual = hcacsimp._get_cache_file_name(func_name)
        # Check.
        self.assertTrue(actual.endswith(".pkl"))
        self.assertIn(func_name, actual)

    def test7(self) -> None:
        """
        Test file path format for json cache type.

        Verifies that _get_cache_file_name returns correct file
        extensions for json (.json) cache type.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        # Run.
        actual = hcacsimp._get_cache_file_name(func_name)
        # Check.
        self.assertTrue(actual.endswith(".json"))
        self.assertIn(func_name, actual)


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

    def test1(self) -> None:
        """
        Verify that setting force_refresh property forces cache refresh.
        """
        # Prepare inputs.
        _cache_mode_function(10)
        initial_count = _cache_mode_function.call_count
        # Set force_refresh property.
        hcacsimp.set_cache_property("_cache_mode_function", "force_refresh", True)
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

    def test1(self) -> None:
        """
        Verify that abort_on_cache_miss=True raises error on cache miss.
        """
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            _abort_test_function(100, abort_on_cache_miss=True)
        self.assertIn("Cache miss", str(cm.exception))


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

    def test1(self) -> None:
        """
        Verify that report_on_cache_miss=True returns '_cache_miss_' on miss.
        """
        # Run test.
        result = _report_test_function(200, report_on_cache_miss=True)
        # Check outputs.
        self.assertEqual(result, "_cache_miss_")


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

    def test1(self) -> None:
        """
        Verify that write_through=True automatically writes to disk.
        """
        # Run test.
        _write_through_function(11)
        # Check outputs.
        cache_file = hcacsimp._get_cache_file_name("_write_through_function")
        self.assertTrue(os.path.exists(cache_file))
        #
        disk_cache = hcacsimp._load_func_cache_data_from_file(cache_file, "json")
        self.assertIn('{"args": [11], "kwargs": {}}', disk_cache)
        self.assertEqual(disk_cache['{"args": [11], "kwargs": {}}'], 99)


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


# #############################################################################
# Module-level helpers for new tests.
# #############################################################################


@hcacsimp.simple_cache(cache_type="json")
def _test_intrinsic_func_intrinsic(x: int) -> int:
    """
    Return x times 3. Named with `_intrinsic` suffix to test suffix stripping.

    :param x: input integer
    :return: x * 3
    """
    res = x * 3
    return res


@hcacsimp.simple_cache(cache_type="json", exclude_keys=["session_id"])
def _test_exclude_keys_func(x: int, *, session_id: str = "") -> int:
    """
    Return x times 2, ignoring session_id for caching purposes.

    :param x: input integer
    :param session_id: session identifier (excluded from cache key)
    :return: x * 2
    """
    res = x * 2
    return res


@hcacsimp.simple_cache(cache_type="json", write_through=False)
def _test_no_write_through(x: int) -> int:
    """
    Return x plus 1, with write_through disabled.

    :param x: input integer
    :return: x + 1
    """
    res = x + 1
    return res


# #############################################################################
# Test_sanity_check_function_cache
# #############################################################################


class Test_sanity_check_function_cache(_BaseCacheTest):
    """
    Test sanity_check_function_cache for validating function cache dicts.
    """

    def test1(self) -> None:
        """
        Verify that sanity_check_function_cache passes for valid cache data.
        """
        # Prepare inputs.
        func_cache_data = {'{"args": [1], "kwargs": {}}': 2}
        # Run test.
        hcacsimp.sanity_check_function_cache(func_cache_data)
        # Check outputs (no exception raised).

    def test2(self) -> None:
        """
        Verify that sanity_check_function_cache passes for empty dict when
        assert_on_empty=False.
        """
        # Prepare inputs.
        func_cache_data: dict = {}
        # Run test.
        hcacsimp.sanity_check_function_cache(
            func_cache_data, assert_on_empty=False
        )
        # Check outputs (no exception raised).


# #############################################################################
# Test_sanity_check_cache
# #############################################################################


class Test_sanity_check_cache(_BaseCacheTest):
    """
    Test sanity_check_cache for validating nested cache dicts.
    """

    def test1(self) -> None:
        """
        Verify that sanity_check_cache passes for valid nested cache data.
        """
        # Prepare inputs.
        cache_data = {"my_func": {'{"args": [1], "kwargs": {}}': 42}}
        # Run test.
        hcacsimp.sanity_check_cache(cache_data)
        # Check outputs (no exception raised).

    def test2(self) -> None:
        """
        Verify that sanity_check_cache passes for empty dict when
        assert_on_empty=False.
        """
        # Prepare inputs.
        cache_data: dict = {}
        # Run test.
        hcacsimp.sanity_check_cache(cache_data, assert_on_empty=False)
        # Check outputs (no exception raised).


# #############################################################################
# Test_cache_data_to_str
# #############################################################################


class Test_cache_data_to_str(_BaseCacheTest):
    """
    Test cache_data_to_str for converting cache data to a string.
    """

    def test1(self) -> None:
        """
        Verify that cache_data_to_str returns a string with the function name
        and cache key.
        """
        # Prepare inputs.
        cache_data = {"my_func": {'{"args": [1], "kwargs": {}}': 42}}
        # Run test.
        result = hcacsimp.cache_data_to_str(cache_data)
        # Check outputs.
        self.assertIn("my_func", result)
        self.assertIn('{"args": [1], "kwargs": {}}', result)
        self.assertIn("42", result)


# #############################################################################
# Test_get_cache_property_system
# #############################################################################


class Test_get_cache_property_system(_BaseCacheTest):
    """
    Test get_cache_property for system properties on unknown functions.
    """

    def test1(self) -> None:
        """
        Verify that get_cache_property returns None for a system property when
        the function is not in the cache property dict.
        """
        # Run test.
        val = hcacsimp.get_cache_property("_nonexistent_func_xyz", "type")
        # Check outputs.
        self.assertIsNone(val)


# #############################################################################
# Test_set_cache_property_new_func
# #############################################################################


class Test_set_cache_property_new_func(_BaseCacheTest):
    """
    Test set_cache_property for a brand new function not yet in cache property.
    """

    def test1(self) -> None:
        """
        Verify that set_cache_property creates a new entry for a function that
        was not previously registered.
        """
        # Run test.
        hcacsimp.set_cache_property("_brand_new_func_xyz", "force_refresh", True)
        # Check outputs.
        val = hcacsimp.get_cache_property("_brand_new_func_xyz", "force_refresh")
        self.assertTrue(val)


# #############################################################################
# Test_cache_property_to_str_no_props
# #############################################################################


class Test_cache_property_to_str_no_props(_BaseCacheTest):
    """
    Test cache_property_to_str for a function with no properties in the cache.
    """

    def test1(self) -> None:
        """
        Verify that cache_property_to_str returns the function name header even
        when the function has no registered cache properties.
        """
        # Run test with a function name not in _CACHE_PROPERTY.
        result = hcacsimp.cache_property_to_str("_nonexistent_func_xyz")
        # Check outputs.
        self.assertIn("_nonexistent_func_xyz", result)


# #############################################################################
# Test__get_cache_file_name_auto_detect
# #############################################################################


class Test__get_cache_file_name_auto_detect(_BaseCacheTest):
    """
    Test _get_cache_file_name when cache type is None (auto-detect from disk).
    """

    def test1(self) -> None:
        """
        Verify that _get_cache_file_name infers .pkl extension when a .pkl file
        exists on disk.
        """
        # Prepare inputs: create a valid .pkl file in the cache dir.
        cache_dir = hcacsimp.get_cache_dir()
        func_name = "_auto_detect_pkl_func"
        pkl_path = os.path.join(cache_dir, f"tmp.cache_simple.{func_name}.pkl")
        hcacsimp._save_func_cache_data_to_file(pkl_path, "pickle", {})
        # Run test.
        file_name = hcacsimp._get_cache_file_name(func_name)
        # Check outputs.
        self.assertTrue(file_name.endswith(".pkl"))

    def test2(self) -> None:
        """
        Verify that _get_cache_file_name infers .json extension when a .json
        file exists on disk.
        """
        # Prepare inputs: create a valid .json file in the cache dir.
        cache_dir = hcacsimp.get_cache_dir()
        func_name = "_auto_detect_json_func"
        json_path = os.path.join(cache_dir, f"tmp.cache_simple.{func_name}.json")
        hcacsimp._save_func_cache_data_to_file(json_path, "json", {})
        # Run test.
        file_name = hcacsimp._get_cache_file_name(func_name)
        # Check outputs.
        self.assertTrue(file_name.endswith(".json"))

    def test3(self) -> None:
        """
        Verify that _get_cache_file_name defaults to .json when no file exists.
        """
        # Prepare inputs: use a brand new function name with no disk file.
        func_name = "_no_file_func_xyz"
        # Run test.
        file_name = hcacsimp._get_cache_file_name(func_name)
        # Check outputs.
        self.assertTrue(file_name.endswith(".json"))


# #############################################################################
# Test__save_func_cache_data_to_file_infer
# #############################################################################


class Test__save_func_cache_data_to_file_infer(_BaseCacheTest):
    """
    Test _save_func_cache_data_to_file when cache_type is None (inferred from
    file extension).
    """

    def test1(self) -> None:
        """
        Verify that _save_func_cache_data_to_file infers pickle format from
        .pkl extension when cache_type is None.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "tmp_test_infer.pkl")
        data = {'{"args": [1], "kwargs": {}}': 42}
        # Run test.
        hcacsimp._save_func_cache_data_to_file(file_name, None, data)
        # Check outputs.
        self.assertTrue(os.path.exists(file_name))
        loaded = hcacsimp._load_func_cache_data_from_file(file_name, "pickle")
        self.assertEqual(loaded, data)


# #############################################################################
# Test__load_func_cache_data_from_file_infer
# #############################################################################


class Test__load_func_cache_data_from_file_infer(_BaseCacheTest):
    """
    Test _load_func_cache_data_from_file when cache_type is None (inferred from
    file extension).
    """

    def test1(self) -> None:
        """
        Verify that _load_func_cache_data_from_file infers pickle format from
        .pkl extension when cache_type is None.
        """
        # Prepare inputs: save a pickle file.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "tmp_test_load_infer.pkl")
        data = {'{"args": [5], "kwargs": {}}': 25}
        hcacsimp._save_func_cache_data_to_file(file_name, "pickle", data)
        # Run test with None cache_type (should infer from .pkl).
        result = hcacsimp._load_func_cache_data_from_file(file_name, None)
        # Check outputs.
        self.assertEqual(result, data)


# #############################################################################
# Test_reset_disk_cache_no_file
# #############################################################################


class Test_reset_disk_cache_no_file(_BaseCacheTest):
    """
    Test reset_disk_cache when the target function has no disk cache file.
    """

    def test1(self) -> None:
        """
        Verify that reset_disk_cache does not raise when the function has no
        cache file on disk.
        """
        # Prepare inputs: use a function that has never been cached to disk.
        func_name = "_cached_json_double"
        # Ensure no disk file exists.
        hcacsimp.reset_disk_cache(func_name, interactive=False)
        cache_file = hcacsimp._get_cache_file_name(func_name)
        self.assertFalse(os.path.exists(cache_file))
        # Run test: reset again when no file exists (should not raise).
        hcacsimp.reset_disk_cache(func_name, interactive=False)
        # Check outputs (no exception raised).


# #############################################################################
# Test_mock_cache
# #############################################################################


class Test_mock_cache(_BaseCacheTest):
    """
    Test mock_cache for inserting values directly into the cache.
    """

    def test1(self) -> None:
        """
        Verify that mock_cache inserts a value into the function cache that can
        be retrieved as a cache hit.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        cache_key = '{"args": [99], "kwargs": {}}'
        value = 198
        # Run test.
        hcacsimp.mock_cache(func_name, cache_key, value)
        # Check outputs.
        cache = hcacsimp.get_cache(func_name)
        self.assertEqual(cache[cache_key], value)

    def test2(self) -> None:
        """
        Verify that a mocked cache value causes a cache hit when the decorated
        function is called.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        cache_key = '{"args": [77], "kwargs": {}}'
        value = 154
        # Run test.
        hcacsimp.mock_cache(func_name, cache_key, value)
        result = _cached_json_double(77, abort_on_cache_miss=True)
        # Check outputs.
        self.assertEqual(result, value)


# #############################################################################
# Test_mock_cache_from_args_kwargs
# #############################################################################


class Test_mock_cache_from_args_kwargs(_BaseCacheTest):
    """
    Test mock_cache_from_args_kwargs for inserting values via args/kwargs.
    """

    def test1(self) -> None:
        """
        Verify that mock_cache_from_args_kwargs inserts the correct value into
        the cache for the given args and kwargs.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        args = (55,)
        kwargs: dict = {}
        value = 110
        # Run test.
        hcacsimp.mock_cache_from_args_kwargs(func_name, args, kwargs, value)
        # Check outputs.
        expected_key = '{"args": [55], "kwargs": {}}'
        cache = hcacsimp.get_cache(func_name)
        self.assertEqual(cache[expected_key], value)


# #############################################################################
# Test_mock_cache_from_disk
# #############################################################################


class Test_mock_cache_from_disk(_BaseCacheTest):
    """
    Test mock_cache_from_disk for bulk-inserting cache data from a dict.
    """

    def test1(self) -> None:
        """
        Verify that mock_cache_from_disk populates the cache from a dict of
        pre-computed values.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        func_cache_data = {
            '{"args": [33], "kwargs": {}}': 66,
            '{"args": [44], "kwargs": {}}': 88,
        }
        # Run test.
        hcacsimp.mock_cache_from_disk(func_name, func_cache_data)
        # Check outputs.
        cache = hcacsimp.get_cache(func_name)
        self.assertEqual(cache['{"args": [33], "kwargs": {}}'], 66)
        self.assertEqual(cache['{"args": [44], "kwargs": {}}'], 88)


# #############################################################################
# Test_simple_cache_intrinsic
# #############################################################################


class Test_simple_cache_intrinsic(_BaseCacheTest):
    """
    Test simple_cache decorator with a function whose name ends in _intrinsic.
    """

    def test1(self) -> None:
        """
        Verify that the _intrinsic suffix is stripped and the cache key uses
        the base function name.
        """
        # Run test.
        result = _test_intrinsic_func_intrinsic(5)
        # Check outputs.
        self.assertEqual(result, 15)
        # Cache should be stored under the base name (without _intrinsic).
        cache = hcacsimp.get_cache("_test_intrinsic_func")
        self.assertIn('{"args": [5], "kwargs": {}}', cache)


# #############################################################################
# Test_simple_cache_existing_type
# #############################################################################


class Test_simple_cache_existing_type(_BaseCacheTest):
    """
    Test that simple_cache preserves a pre-existing cache type setting.
    """

    def test1(self) -> None:
        """
        Verify that applying simple_cache with cache_type='json' does not
        override an existing 'pickle' type already set for the function.
        """
        # Prepare inputs: set the type before decoration.
        hcacsimp.set_cache_property("_inline_type_func", "type", "pickle")

        def _inline_type_func(x: int) -> int:
            return x

        # Apply decorator with a different cache_type.
        hcacsimp.simple_cache(cache_type="json")(_inline_type_func)
        # Check outputs: type should remain 'pickle'.
        val = hcacsimp.get_cache_property("_inline_type_func", "type")
        self.assertEqual(val, "pickle")


# #############################################################################
# Test_simple_cache_exclude_keys
# #############################################################################


class Test_simple_cache_exclude_keys(_BaseCacheTest):
    """
    Test simple_cache decorator with exclude_keys parameter.
    """

    def test1(self) -> None:
        """
        Verify that calls with the same primary arg but different excluded
        kwargs produce a single cache entry (the excluded key is ignored).
        """
        # Run test: two calls with same x but different session_id.
        result1 = _test_exclude_keys_func(5, session_id="abc")
        result2 = _test_exclude_keys_func(5, session_id="xyz")
        # Check outputs.
        self.assertEqual(result1, 10)
        self.assertEqual(result2, 10)
        # Only one cache entry should exist.
        cache = hcacsimp.get_cache("_test_exclude_keys_func")
        self.assertEqual(len(cache), 1)


# #############################################################################
# Test_simple_cache_no_write_through
# #############################################################################


class Test_simple_cache_no_write_through(_BaseCacheTest):
    """
    Test simple_cache decorator with write_through=False.
    """

    def test1(self) -> None:
        """
        Verify that with write_through=False the computed value is not
        automatically persisted to disk after a function call.
        """
        # Run test.
        result = _test_no_write_through(7)
        self.assertEqual(result, 8)
        # Reset memory cache so that reading goes to disk.
        hcacsimp.reset_mem_cache("_test_no_write_through")
        # Check outputs: disk cache should not contain the computed value.
        disk_cache = hcacsimp.get_disk_cache("_test_no_write_through")
        self.assertNotIn('{"args": [7], "kwargs": {}}', disk_cache)


# #############################################################################
# Test_global_cache_file_prefix
# #############################################################################


class Test_global_cache_file_prefix(_BaseCacheTest):
    """
    Test global cache file prefix configuration.
    """

    def test1(self) -> None:
        """
        Verify that set_cache_file_prefix changes the cache file prefix.
        """
        # Prepare inputs.
        custom_prefix = "my_test_cache"
        # Run.
        hcacsimp.set_cache_file_prefix(custom_prefix)
        _ = _cached_json_double(5)
        # Check.
        cache_file = hcacsimp._get_cache_file_name("_cached_json_double")
        self.assertIn(custom_prefix, cache_file)

    def test2(self) -> None:
        """
        Verify that get_cache_file_prefix returns the configured prefix.
        """
        # Prepare inputs.
        custom_prefix = "test_prefix"
        hcacsimp._CACHE_FILE_PREFIX = custom_prefix
        # Run.
        actual = hcacsimp.get_cache_file_prefix()
        # Check.
        self.assertEqual(actual, custom_prefix)


# #############################################################################
# Test helper functions for per-function configuration
# #############################################################################


@hcacsimp.simple_cache(
    cache_type="json",
    cache_dir="/tmp/custom_cache",
    cache_prefix="project_cache",
)
def _test_per_function_cache_dir_and_prefix(x: int) -> int:
    """
    Test function with custom cache directory and prefix.

    :param x: input integer
    :return: x * 2
    """
    res = x * 2
    return res


@hcacsimp.simple_cache(
    cache_type="json",
    cache_dir="/tmp/custom_cache",
)
def _test_per_function_cache_dir(x: int) -> int:
    """
    Test function with custom cache directory and default prefix.

    :param x: input integer
    :return: x * 2
    """
    res = x * 2
    return res


@hcacsimp.simple_cache(
    cache_type="json",
    cache_prefix="project_cache",
)
def _test_per_function_prefix(x: int) -> int:
    """
    Test function with custom prefix and default directory.

    :param x: input integer
    :return: x * 3
    """
    res = x * 3
    return res


@hcacsimp.simple_cache(
    cache_type="json",
    s3_bucket="s3://decorator-bucket",
    s3_prefix="decorator/prefix",
    aws_profile="decorator-profile",
)
def _test_per_function_s3_configs(x: int) -> int:
    """
    Test function with all S3 parameters set via decorator.

    :param x: input integer
    :return: x * 6
    """
    return x * 6


# #############################################################################
# Test_per_function_cache_dir
# #############################################################################


class Test_per_function_cache_dir(_BaseCacheTest):
    """
    Test per-function cache directory configuration.
    """

    def test1(self) -> None:
        """
        Test cache_dir configured via decorator parameter.

        Verifies that when cache_dir is set in the @simple_cache
        decorator, the cache file is created in the specified custom
        directory.
        """
        # Run.
        _ = _test_per_function_cache_dir(10)
        # Check.
        # Verify cache file is in decorator-specified directory.
        cache_file = hcacsimp._get_cache_file_name("_test_per_function_cache_dir")
        self.assertIn("/tmp/custom_cache", cache_file)
        # Flush to disk to verify file creation.
        hcacsimp.flush_cache_to_disk("_test_per_function_cache_dir")
        self.assertTrue(os.path.exists(cache_file))

    def test2(self) -> None:
        """
        Test that cache_dir can be retrieved.

        Verifies that cache_dir property set via decorator can be
        retrieved using get_cache_property.
        """
        # Run.
        cache_dir = hcacsimp.get_cache_property(
            "_test_per_function_cache_dir", "cache_dir"
        )
        # Check.
        self.assertEqual(cache_dir, "/tmp/custom_cache")

    def test3(self) -> None:
        """
        Test cache_dir configured via set_cache_property() function call.

        Verifies that cache_dir can be set manually via
        set_cache_property() for functions without cache_dir in their
        decorator.
        """
        # Prepare inputs.
        custom_dir = self.get_scratch_space() + "/manual_cache"
        # Set cache_dir manually.
        hcacsimp.set_cache_property(
            "_cached_json_double", "cache_dir", custom_dir
        )
        # Run.
        _ = _cached_json_double(10)
        # Check.
        # Verify cache file is in manually-set directory.
        cache_file = hcacsimp._get_cache_file_name("_cached_json_double")
        self.assertIn(custom_dir, cache_file)
        # Flush to disk to verify file creation.
        hcacsimp.flush_cache_to_disk("_cached_json_double")
        self.assertTrue(os.path.exists(cache_file))

    def test4(self) -> None:
        """
        Test get/set cache_dir property API.

        Verifies that cache_dir can be stored and retrieved via
        get/set_cache_property functions.
        """
        # Prepare inputs.
        custom_dir = "/tmp/test_cache_dir"
        # Run.
        hcacsimp.set_cache_property(
            "_cached_json_double", "cache_dir", custom_dir
        )
        actual = hcacsimp.get_cache_property("_cached_json_double", "cache_dir")
        # Check.
        self.assertEqual(actual, custom_dir)


# #############################################################################
# Test_per_function_cache_prefix
# #############################################################################


class Test_per_function_cache_prefix(_BaseCacheTest):
    """
    Test per-function cache prefix configuration.
    """

    def test1(self) -> None:
        """
        Test cache_prefix configured via decorator parameter.

        Verifies that when cache_prefix is set in the @simple_cache
        decorator, the cache file name uses the specified custom prefix.
        """
        # Run.
        _ = _test_per_function_prefix(7)
        # Check.
        cache_file = hcacsimp._get_cache_file_name("_test_per_function_prefix")
        self.assertIn("project_cache", cache_file)

    def test2(self) -> None:
        """
        Test that cache_prefix can be retrieved.

        Verifies that cache_prefix property set via decorator can be
        retrieved using get_cache_property.
        """
        # Run.
        cache_prefix = hcacsimp.get_cache_property(
            "_test_per_function_prefix", "cache_prefix"
        )
        # Check.
        self.assertEqual(cache_prefix, "project_cache")

    def test3(self) -> None:
        """
        Test cache_prefix configured via set_cache_property() function call.

        Verifies that cache_prefix can be set manually via
        set_cache_property() for functions without cache_prefix in their
        decorator.
        """
        # Prepare inputs.
        custom_prefix = "test_prefix"
        # Set cache_prefix manually.
        hcacsimp.set_cache_property(
            "_cached_json_double", "cache_prefix", custom_prefix
        )
        # Run.
        _ = _cached_json_double(7)
        # Check.
        cache_file = hcacsimp._get_cache_file_name("_cached_json_double")
        self.assertIn(custom_prefix, cache_file)

    def test4(self) -> None:
        """
        Test get/set cache_prefix property API.

        Verifies that cache_prefix can be stored and retrieved via
        get/set_cache_property functions.
        """
        # Prepare inputs.
        custom_prefix = "my_project_cache"
        # Run.
        hcacsimp.set_cache_property(
            "_cached_json_double", "cache_prefix", custom_prefix
        )
        actual = hcacsimp.get_cache_property(
            "_cached_json_double", "cache_prefix"
        )
        # Check.
        self.assertEqual(actual, custom_prefix)


# #############################################################################
# Test_per_function_cache_dir_and_prefix
# #############################################################################


class Test_per_function_cache_dir_and_prefix(_BaseCacheTest):
    """
    Test per-function cache directory and prefix configured together.
    """

    def test1(self) -> None:
        """
        Test both cache_dir and cache_prefix configured via decorator.

        Verifies that when both cache_dir and cache_prefix are set in
        the @simple_cache decorator, both are applied correctly to the
        cache file path.
        """
        # Run.
        _ = _test_per_function_cache_dir_and_prefix(10)
        # Check.
        cache_file = hcacsimp._get_cache_file_name(
            "_test_per_function_cache_dir_and_prefix"
        )
        # Verify custom directory is used.
        self.assertIn("/tmp/custom_cache", cache_file)
        # Verify custom prefix is used.
        self.assertIn("project_cache", cache_file)
        # Flush to disk to verify file creation.
        hcacsimp.flush_cache_to_disk("_test_per_function_cache_dir_and_prefix")
        self.assertTrue(os.path.exists(cache_file))

    def test2(self) -> None:
        """
        Test that cache_dir and cache_prefix can be retrieved.

        Verifies that both cache_dir and cache_prefix properties set via
        decorator can be retrieved using get_cache_property.
        """
        # Run.
        cache_dir = hcacsimp.get_cache_property(
            "_test_per_function_cache_dir_and_prefix", "cache_dir"
        )
        cache_prefix = hcacsimp.get_cache_property(
            "_test_per_function_cache_dir_and_prefix", "cache_prefix"
        )
        # Check.
        self.assertEqual(cache_dir, "/tmp/custom_cache")
        self.assertEqual(cache_prefix, "project_cache")


# #############################################################################
# Test_s3_configuration
# #############################################################################


class Test_s3_configuration(_BaseCacheTest):
    """
    Test S3 configuration (global and per-function).
    """

    def test1(self) -> None:
        """
        Verify that set_s3_bucket stores bucket with s3:// prefix.
        """
        # Prepare inputs.
        bucket = "my-test-bucket"
        # Run.
        hcacsimp.set_s3_bucket(bucket)
        actual = hcacsimp.get_s3_bucket()
        # Check.
        self.assertEqual(actual, "s3://my-test-bucket")

    def test2(self) -> None:
        """
        Verify that set_s3_bucket preserves existing s3:// prefix.
        """
        # Prepare inputs.
        bucket = "s3://my-test-bucket"
        # Run.
        hcacsimp.set_s3_bucket(bucket)
        actual = hcacsimp.get_s3_bucket()
        # Check.
        self.assertEqual(actual, "s3://my-test-bucket")

    def test3(self) -> None:
        """
        Verify that set_s3_prefix and get_s3_prefix work correctly.
        """
        # Prepare inputs.
        prefix = "cache/project1"
        # Run.
        hcacsimp.set_s3_prefix(prefix)
        actual = hcacsimp.get_s3_prefix()
        # Check.
        self.assertEqual(actual, prefix)

    def test4(self) -> None:
        """
        Verify that set_aws_profile and get_aws_profile work correctly.
        """
        # Prepare inputs.
        profile = "my-aws-profile"
        # Run.
        hcacsimp.set_aws_profile(profile)
        actual = hcacsimp.get_aws_profile()
        # Check.
        self.assertEqual(actual, profile)

    def test5(self) -> None:
        """
        Verify that per-function s3_bucket can be set and retrieved.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        s3_bucket = "s3://function-specific-bucket"
        # Run.
        hcacsimp.set_cache_property(func_name, "s3_bucket", s3_bucket)
        actual = hcacsimp.get_cache_property(func_name, "s3_bucket")
        # Check.
        self.assertEqual(actual, s3_bucket)

    def test6(self) -> None:
        """
        Verify that per-function s3_prefix can be set and retrieved.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        s3_prefix = "custom/prefix"
        # Run.
        hcacsimp.set_cache_property(func_name, "s3_prefix", s3_prefix)
        actual = hcacsimp.get_cache_property(func_name, "s3_prefix")
        # Check.
        self.assertEqual(actual, s3_prefix)

    def test7(self) -> None:
        """
        Verify that per-function aws_profile can be set and retrieved.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        aws_profile = "function-aws-profile"
        # Run.
        hcacsimp.set_cache_property(func_name, "aws_profile", aws_profile)
        actual = hcacsimp.get_cache_property(func_name, "aws_profile")
        # Check.
        self.assertEqual(actual, aws_profile)

    def test8(self) -> None:
        """
        Verify that auto_sync_s3 property can be set and retrieved.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        auto_sync = True
        # Run.
        hcacsimp.set_cache_property(func_name, "auto_sync_s3", auto_sync)
        actual = hcacsimp.get_cache_property(func_name, "auto_sync_s3")
        # Check.
        self.assertEqual(actual, auto_sync)


# #############################################################################
# Test_per_function_s3_decorator
# #############################################################################


class Test_per_function_s3_decorator(_BaseCacheTest):
    """
    Test S3 configuration set via decorator parameters.
    """

    def test1(self) -> None:
        """
        Test that all S3 decorator parameters are stored correctly.
        """
        # Run.
        s3_bucket = hcacsimp.get_cache_property(
            "_test_per_function_s3_configs", "s3_bucket"
        )
        s3_prefix = hcacsimp.get_cache_property(
            "_test_per_function_s3_configs", "s3_prefix"
        )
        aws_profile = hcacsimp.get_cache_property(
            "_test_per_function_s3_configs", "aws_profile"
        )
        # Check.
        self.assertEqual(s3_bucket, "s3://decorator-bucket")
        self.assertEqual(s3_prefix, "decorator/prefix")
        self.assertEqual(aws_profile, "decorator-profile")


# #############################################################################
# Test__get_s3_cache_path
# #############################################################################


class Test__get_s3_cache_path(_BaseCacheTest):
    """
    Test _get_s3_cache_path function.
    """

    def test1(self) -> None:
        """
        Test S3 path with global bucket and no prefix.
        """
        # Prepare inputs.
        hcacsimp.set_s3_bucket("s3://my-bucket")
        # Run.
        actual = hcacsimp._get_s3_cache_path("_cached_json_double")
        # Check.
        self.assertIn("s3://my-bucket", actual)
        self.assertIn("_cached_json_double", actual)

    def test2(self) -> None:
        """
        Test S3 path with global bucket and prefix.
        """
        # Prepare inputs.
        hcacsimp.set_s3_bucket("s3://my-bucket")
        hcacsimp.set_s3_prefix("cache/data")
        # Run.
        actual = hcacsimp._get_s3_cache_path("_cached_json_double")
        # Check.
        self.assertIn("s3://my-bucket/cache/data", actual)
        self.assertIn("_cached_json_double", actual)

    def test3(self) -> None:
        """
        Test S3 path with per-function bucket overriding global.
        """
        # Prepare inputs.
        hcacsimp.set_s3_bucket("s3://global-bucket")
        hcacsimp.set_cache_property(
            "_cached_json_double", "s3_bucket", "s3://function-bucket"
        )
        # Run.
        actual = hcacsimp._get_s3_cache_path("_cached_json_double")
        # Check.
        self.assertIn("s3://function-bucket", actual)
        self.assertNotIn("global-bucket", actual)

    def test4(self) -> None:
        """
        Test S3 path with per-function prefix overriding global.
        """
        # Prepare inputs.
        hcacsimp.set_s3_bucket("s3://my-bucket")
        hcacsimp.set_s3_prefix("global/prefix")
        hcacsimp.set_cache_property(
            "_cached_json_double", "s3_prefix", "function/prefix"
        )
        # Run.
        actual = hcacsimp._get_s3_cache_path("_cached_json_double")
        # Check.
        self.assertIn("s3://my-bucket/function/prefix", actual)
        self.assertNotIn("global/prefix", actual)

    def test5(self) -> None:
        """
        Test S3 path with decorator-configured bucket and prefix.
        """
        # Run.
        actual = hcacsimp._get_s3_cache_path("_test_per_function_s3_configs")
        # Check.
        self.assertIn("s3://decorator-bucket/decorator/prefix", actual)
        self.assertIn("_test_per_function_s3_configs", actual)

    def test6(self) -> None:
        """
        Test that ValueError is raised when S3 bucket is not configured.
        """
        # Run and check.
        with self.assertRaises(ValueError) as cm:
            hcacsimp._get_s3_cache_path("_cached_json_double")
        self.assertEqual(str(cm.exception), "S3 bucket not configured")


# #############################################################################
# Test__extract_func_name_from_cache_file
# #############################################################################


class Test__extract_func_name_from_cache_file(_BaseCacheTest):
    """
    Test _extract_func_name_from_cache_file function.
    """

    def test1(self) -> None:
        """
        Test extraction from JSON cache file with standard prefix.
        """
        # Prepare inputs.
        cache_file_name = "tmp.cache_simple._cached_json_double.json"
        # Run.
        actual = hcacsimp._extract_func_name_from_cache_file(cache_file_name)
        # Check.
        self.assertEqual(actual, "_cached_json_double")

    def test2(self) -> None:
        """
        Test extraction from pickle cache file.
        """
        # Prepare inputs.
        cache_file_name = "tmp.cache_simple._cached_pickle_square.pkl"
        # Run.
        actual = hcacsimp._extract_func_name_from_cache_file(cache_file_name)
        # Check.
        self.assertEqual(actual, "_cached_pickle_square")

    def test3(self) -> None:
        """
        Test extraction with custom prefix.
        """
        # Prepare inputs.
        cache_file_name = "my_project_cache._my_function.json"
        # Run.
        actual = hcacsimp._extract_func_name_from_cache_file(cache_file_name)
        # Check.
        self.assertEqual(actual, "_my_function")

    def test4(self) -> None:
        """
        Test extraction returns None for invalid file name.
        """
        # Prepare inputs.
        cache_file_name = "invalid_filename"
        # Run.
        actual = hcacsimp._extract_func_name_from_cache_file(cache_file_name)
        # Check.
        self.assertIsNone(actual)

    def test5(self) -> None:
        """
        Test extraction returns None for file without extension.
        """
        # Prepare inputs.
        cache_file_name = "cache.function_name"
        # Run.
        actual = hcacsimp._extract_func_name_from_cache_file(cache_file_name)
        # Check.
        self.assertIsNone(actual)

    def test6(self) -> None:
        """
        Test extraction with custom prefix and dir.
        """
        # Prepare inputs.
        cache_file_name = "my_dir/my_project_cache._my_function.json"
        # Run.
        actual = hcacsimp._extract_func_name_from_cache_file(cache_file_name)
        # Check.
        self.assertEqual(actual, "_my_function")

    def test7(self) -> None:
        """
        Test extraction when custom prefix has dots in it.
        """
        # Prepare inputs.
        cache_file_name = "dir1/dir2/my.project.cache._my_function.json"
        # Run.
        actual = hcacsimp._extract_func_name_from_cache_file(cache_file_name)
        # Check.
        self.assertEqual(actual, "_my_function")


# #############################################################################
# Test__check_s3_configured
# #############################################################################


class Test__check_s3_configured(_BaseCacheTest):
    """
    Test _check_s3_configured function.
    """

    def test1(self) -> None:
        """
        Test returns False when S3 bucket is not explicitly configured.
        """
        # Run.
        actual = hcacsimp._check_s3_configured()
        # Check.
        self.assertFalse(actual)

    def test2(self) -> None:
        """
        Test returns True when global S3 bucket is configured.
        """
        # Prepare inputs.
        hcacsimp.set_s3_bucket("s3://my-bucket")
        # Run.
        actual = hcacsimp._check_s3_configured()
        # Check.
        self.assertTrue(actual)

    def test3(self) -> None:
        """
        Test returns True when per-function S3 bucket is configured.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        hcacsimp.set_cache_property(
            func_name, "s3_bucket", "s3://function-bucket"
        )
        # Run.
        actual = hcacsimp._check_s3_configured(func_name)
        # Check.
        self.assertTrue(actual)

    def test4(self) -> None:
        """
        Test per-function bucket overrides missing global bucket.
        """
        # Prepare inputs.
        func_name = "_cached_json_double"
        hcacsimp.set_cache_property(
            func_name, "s3_bucket", "s3://function-bucket"
        )
        # Run.
        actual_with_func = hcacsimp._check_s3_configured(func_name)
        actual_without_func = hcacsimp._check_s3_configured()
        # Check.
        self.assertTrue(actual_with_func)
        self.assertFalse(actual_without_func)

    def test5(self) -> None:
        """
        Test with decorator-configured S3 bucket.
        """
        # Run.
        actual = hcacsimp._check_s3_configured("_test_per_function_s3_configs")
        # Check.
        self.assertTrue(actual)