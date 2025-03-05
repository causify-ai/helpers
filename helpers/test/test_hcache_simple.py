import json
import os
import pickle

import pandas as pd

import helpers.hcache_simple as hcacsimp
import helpers.hunit_test as hunitest


# Module-level cached functions to avoid including `self` in the cache keys.
@hcacsimp.simple_cache(cache_type="json")
def cached_function(x):
    return x * 2


@hcacsimp.simple_cache(cache_type="pickle")
def cached_pickle_function(x):
    return x**2


# #############################################################################
# TestHCacheSimple
# #############################################################################


class TestHCacheSimple(hunitest.TestCase):

    def setUp(self) -> None:
        """
        Run before each test case.

        Ensures that both memory and disk caches, as well as persistent
        user cache properties, are cleared.
        """
        # Reset user properties.
        hcacsimp.reset_cache_property("user")
        # Reset caches for our test functions.
        try:
            hcacsimp.reset_cache("cached_function")
        except AssertionError:
            hcacsimp.reset_mem_cache("cached_function")
        try:
            hcacsimp.reset_cache("cached_pickle_function")
        except AssertionError:
            hcacsimp.reset_mem_cache("cached_pickle_function")

    def tearDown(self) -> None:
        """
        Clean up any cache files created on disk after each test.
        """
        for fname in [
            "cache.cached_function.json",
            "cache.cached_pickle_function.pkl",
            "cache.dummy_cached_function.json",
        ]:
            if os.path.exists(fname):
                os.remove(fname)

    def test_memory_caching(self):
        """
        Test that function results are correctly cached in memory.
        """
        self.assertEqual(cached_function(2), 4)
        # Second call should hit the cache.
        self.assertEqual(cached_function(2), 4)

        cache = hcacsimp.get_cache("cached_function")
        self.assertIn(
            "(2,)", cache, msg="Cache key '(2,)' should exist in memory."
        )
        self.assertEqual(cache["(2,)"], 4)

    def test_disk_caching(self):
        """
        Test that disk caching works as expected.
        """
        cached_function(3)  # Compute and store in memory.
        hcacsimp.flush_cache_to_disk("cached_function")  # Save to disk.

        cache_file = "cache.cached_function.json"
        self.assertTrue(
            os.path.exists(cache_file), msg="Cache file should exist on disk."
        )

        with open(cache_file, "r", encoding="utf-8") as f:
            disk_cache = json.load(f)

        self.assertIn("(3,)", disk_cache)
        self.assertEqual(disk_cache["(3,)"], 6)

    def test_cache_reset(self):
        """
        Verify that cache resets properly.
        """
        cached_function(5)
        self.assertIn("(5,)", hcacsimp.get_cache("cached_function"))

        # Reset the memory cache.
        hcacsimp.reset_mem_cache("cached_function")
        self.assertNotIn("(5,)", hcacsimp.get_cache("cached_function"))

        # Write to disk and then try resetting disk cache.
        cached_function(6)
        hcacsimp.flush_cache_to_disk("cached_function")
        # reset_disk_cache is not implemented (it asserts), so we expect an AssertionError.
        with self.assertRaises(AssertionError):
            hcacsimp.reset_disk_cache("cached_function")
        self.assertTrue(os.path.exists("cache.cached_function.json"))

    def test_pickle_cache(self):
        """
        Ensure that pickle-based caching works correctly.
        """
        cached_pickle_function(4)
        hcacsimp.flush_cache_to_disk("cached_pickle_function")

        cache_file = "cache.cached_pickle_function.pkl"
        self.assertTrue(
            os.path.exists(cache_file),
            msg="Pickle cache file should exist on disk.",
        )

        with open(cache_file, "rb") as f:
            disk_cache = pickle.load(f)

        self.assertIn("(4,)", disk_cache)
        self.assertEqual(disk_cache["(4,)"], 16)

    def test_force_cache_from_disk(self):
        """
        Ensure that forcing cache from disk updates the memory cache.
        """
        cached_function(7)
        hcacsimp.flush_cache_to_disk("cached_function")

        # Reset the in-memory cache.
        hcacsimp.reset_mem_cache("cached_function")
        # Use get_mem_cache to check the in-memory cache only.
        self.assertNotIn(
            "(7,)",
            hcacsimp.get_mem_cache("cached_function"),
            msg="In-memory cache should be empty after reset.",
        )

        # Force loading cache from disk.
        hcacsimp.force_cache_from_disk("cached_function")
        self.assertIn(
            "(7,)",
            hcacsimp.get_cache("cached_function"),
            msg="After forcing, the cache should contain the key from disk.",
        )

    def test_cache_perf(self):
        """
        Test cache performance tracking.
        """
        hcacsimp.enable_cache_perf("cached_function")

        cached_function(8)  # First call: cache miss.
        cached_function(8)  # Second call: cache hit.

        stats = hcacsimp.get_cache_perf_stats("cached_function")
        self.assertIn("hits=1", stats)
        self.assertIn("misses=1", stats)

    def test_cache_function_list(self):
        """
        Ensure that cached function names are properly retrieved.
        """
        cached_function(9)
        mem_funcs = hcacsimp.get_cache_func_names("mem")
        self.assertIn("cached_function", mem_funcs)

    def test_parametrized_cache(self):
        """
        Test caching with multiple input values.
        """
        test_cases = [(1, 2), (2, 4), (3, 6)]
        for input_value, expected_output in test_cases:
            self.assertEqual(cached_function(input_value), expected_output)

    def test_abort_on_cache_miss(self):
        """
        Test that setting abort_on_cache_miss raises an error on a cache miss.
        """
        hcacsimp.set_cache_property(
            "user", "cached_function", "abort_on_cache_miss", True
        )
        hcacsimp.reset_mem_cache("cached_function")
        with self.assertRaises(ValueError) as context:
            cached_function(10)
        self.assertIn("Cache miss for key", str(context.exception))
        # Reset property for future tests.
        hcacsimp.set_cache_property(
            "user", "cached_function", "abort_on_cache_miss", False
        )

    def test_report_on_cache_miss(self):
        """
        Test that setting report_on_cache_miss returns a specific value on a
        cache miss.
        """
        hcacsimp.set_cache_property(
            "user", "cached_function", "report_on_cache_miss", True
        )
        hcacsimp.reset_mem_cache("cached_function")
        result = cached_function(11)
        self.assertEqual(result, "_cache_miss_")
        hcacsimp.set_cache_property(
            "user", "cached_function", "report_on_cache_miss", False
        )

    def test_force_refresh(self):
        """
        Test that force_refresh forces the underlying function to be called
        even if cached.
        """
        call_count = {"count": 0}

        @hcacsimp.simple_cache(cache_type="json")
        def refreshable_function(x):
            call_count["count"] += 1
            return x * 10

        result1 = refreshable_function(3)
        self.assertEqual(result1, 30)
        result2 = refreshable_function(3)
        self.assertEqual(result2, 30)
        self.assertEqual(
            call_count["count"],
            1,
            msg="Underlying function should be called only once.",
        )
        # Enable force refresh.
        hcacsimp.set_cache_property(
            "user", "refreshable_function", "force_refresh", True
        )
        result3 = refreshable_function(3)
        self.assertEqual(result3, 30)
        self.assertEqual(
            call_count["count"],
            2,
            msg="Underlying function should be called again with force_refresh.",
        )
        # Cleanup: disable force_refresh.
        hcacsimp.set_cache_property(
            "user", "refreshable_function", "force_refresh", False
        )

    def test_cache_property_to_str(self):
        """
        Test conversion of cache properties to a string representation.
        """
        hcacsimp.set_cache_property(
            "user", "cached_function", "force_refresh", True
        )
        prop_str = hcacsimp.cache_property_to_str("user", "cached_function")
        self.assertIn("force_refresh: True", prop_str)

    def test_set_get_cache_property(self):
        """
        Test setting and getting a cache property.
        """
        hcacsimp.set_cache_property(
            "user", "cached_function", "report_on_cache_miss", True
        )
        value = hcacsimp.get_cache_property(
            "user", "cached_function", "report_on_cache_miss"
        )
        self.assertTrue(value)

    def test_reset_cache_property(self):
        """
        Test that resetting cache properties clears user properties.
        """
        hcacsimp.set_cache_property(
            "user", "cached_function", "report_on_cache_miss", True
        )
        self.assertTrue(
            hcacsimp.get_cache_property(
                "user", "cached_function", "report_on_cache_miss"
            )
        )
        hcacsimp.reset_cache_property("user")
        # After reset, property should return False (default).
        self.assertFalse(
            hcacsimp.get_cache_property(
                "user", "cached_function", "report_on_cache_miss"
            )
        )

    def test_get_cache_func_names_disk(self):
        """
        Test that get_cache_func_names returns function names for disk cache.
        """
        cached_function(2)
        hcacsimp.flush_cache_to_disk("cached_function")
        disk_funcs = hcacsimp.get_cache_func_names("disk")
        self.assertIn("cached_function", disk_funcs)

    def test_get_cache_func_names_all(self):
        """
        Test that get_cache_func_names returns function names for all caches.
        """
        cached_function(2)
        hcacsimp.flush_cache_to_disk("cached_function")
        all_funcs = hcacsimp.get_cache_func_names("all")
        self.assertIn("cached_function", all_funcs)
        # Also check for the pickle function if already used.
        cached_pickle_function(2)
        hcacsimp.flush_cache_to_disk("cached_pickle_function")
        all_funcs = hcacsimp.get_cache_func_names("all")
        self.assertIn("cached_pickle_function", all_funcs)

    def test_get_disk_cache_no_file(self):
        """
        Test that get_disk_cache creates a new cache file if none exists.
        """
        fname = "cache.cached_function.json"
        if os.path.exists(fname):
            os.remove(fname)
        disk_cache = hcacsimp.get_disk_cache("cached_function")
        self.assertEqual(disk_cache, {})
        self.assertTrue(
            os.path.exists(fname),
            msg="Disk cache file should be created if not present.",
        )

    def test_invalid_cache_property(self):
        """
        Test that setting an invalid cache property raises an AssertionError.
        """
        with self.assertRaises(AssertionError):
            hcacsimp.set_cache_property(
                "user", "cached_function", "invalid_prop", True
            )

    def test_invalid_cache_type_in_decorator(self):
        """
        Test that using an invalid cache_type in the decorator raises an error.
        """
        with self.assertRaises(AssertionError):

            @hcacsimp.simple_cache(cache_type="invalid")
            def invalid_cached_func(x):
                return x

    def test_get_cache_perf_stats_without_enable(self):
        """
        Test that getting cache performance stats without enabling returns an
        empty string.
        """
        stats = hcacsimp.get_cache_perf_stats("cached_function")
        self.assertEqual(stats, "")

    def test_disable_cache_perf(self):
        """
        Test that disabling cache performance returns None for get_cache_perf.
        """
        hcacsimp.enable_cache_perf("cached_function")
        hcacsimp.disable_cache_perf("cached_function")
        self.assertIsNone(hcacsimp.get_cache_perf("cached_function"))

    def test_cache_stats_to_str(self):
        """
        Test that cache_stats_to_str returns a DataFrame with the expected
        structure.
        """

        # Define a dummy cached function.
        @hcacsimp.simple_cache(cache_type="json")
        def dummy_cached_function(x):
            return x + 100

        dummy_cached_function(1)
        stats_df = hcacsimp.cache_stats_to_str("dummy_cached_function")
        self.assertIsInstance(stats_df, pd.DataFrame)
        self.assertIn("memory", stats_df.columns)
        self.assertIn("disk", stats_df.columns)
