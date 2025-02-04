import os
import json
import pickle

import helpers.hunit_test as hunitest
import helpers.hcache_simple as hcache


class TestHCacheSimple(hunittest.TestCase):
    
    def setUp(self) -> None:
        """
        Run before each test case. Ensures cache is cleared before every test.
        """
        hcache.reset_cache("cached_function")
        hcache.reset_cache("cached_pickle_function")

    @hcache.simple_cache(cache_type="json")
    def cached_function(self, x):
        return x * 2

    @hcache.simple_cache(cache_type="pickle")
    def cached_pickle_function(self, x):
        return x ** 2

    def test_memory_caching(self):
        """
        Test if function results are correctly cached in memory.
        """
        self.assertEqual(self.cached_function(2), 4)
        self.assertEqual(self.cached_function(2), 4)  # Should be retrieved from cache

        cache = hcache.get_cache("cached_function")
        self.assertIn("(2,)", cache)  # Cached key exists
        self.assertEqual(cache["(2,)"], 4)  # Cached value is correct

    def test_disk_caching(self):
        """
        Test if disk caching works as expected.
        """
        self.cached_function(3)  # Compute and store in memory
        hcache.flush_cache_to_disk("cached_function")  # Save to disk

        cache_file = "cache.cached_function.json"
        self.assertTrue(os.path.exists(cache_file))

        with open(cache_file, "r") as f:
            disk_cache = json.load(f)

        self.assertIn("(3,)", disk_cache)
        self.assertEqual(disk_cache["(3,)"], 6)

    def test_cache_reset(self):
        """
        Verify that cache resets properly.
        """
        self.cached_function(5)
        self.assertIn("(5,)", hcache.get_cache("cached_function"))

        hcache.reset_mem_cache("cached_function")
        self.assertNotIn("(5,)", hcache.get_cache("cached_function"))

        self.cached_function(6)
        hcache.flush_cache_to_disk("cached_function")
        hcache.reset_disk_cache("cached_function")
        self.assertFalse(os.path.exists("cache.cached_function.json"))

    def test_pickle_cache(self):
        """
        Ensure that pickle-based caching works correctly.
        """
        self.cached_pickle_function(4)  # Compute and store in memory
        hcache.flush_cache_to_disk("cached_pickle_function")  # Save to disk

        cache_file = "cache.cached_pickle_function.pkl"
        self.assertTrue(os.path.exists(cache_file))

        with open(cache_file, "rb") as f:
            disk_cache = pickle.load(f)

        self.assertIn("(4,)", disk_cache)
        self.assertEqual(disk_cache["(4,)"], 16)

    def test_force_cache_from_disk(self):
        """
        Ensure that forcing cache from disk updates the memory cache.
        """
        self.cached_function(7)
        hcache.flush_cache_to_disk("cached_function")

        hcache.reset_mem_cache("cached_function")
        self.assertNotIn("(7,)", hcache.get_cache("cached_function"))

        hcache.force_cache_from_disk("cached_function")
        self.assertIn("(7,)", hcache.get_cache("cached_function"))

    def test_cache_perf(self):
        """
        Test cache performance tracking.
        """
        hcache.enable_cache_perf("cached_function")

        self.cached_function(8)  # First call (miss)
        self.cached_function(8)  # Second call (hit)

        stats = hcache.get_cache_perf_stats("cached_function")
        self.assertIn("hits=1", stats)
        self.assertIn("misses=1", stats)

    def test_cache_function_list(self):
        """
        Ensure that cached function names are properly retrieved.
        """
        self.cached_function(9)
        self.assertIn("cached_function", hcache.get_cache_func_names("mem"))

    def test_parametrized_cache(self):
        """
        Test caching with multiple input values.
        """
        test_cases = [(1, 2), (2, 4), (3, 6)]
        for input_value, expected_output in test_cases:
            self.assertEqual(self.cached_function(input_value), expected_output)

