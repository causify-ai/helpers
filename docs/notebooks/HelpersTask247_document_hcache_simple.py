# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Using `hcache_simple` for Caching in Python
#
# This tutorial provides a detailed walkthrough of the `hcache_simple` module, which implements a lightweight caching mechanism. Caching can significantly improve performance for functions with expensive computations by storing and reusing their results.
#
# This module covers:
# - Setting up a function for caching.
# - Monitoring cache performance.
# - Forcing cache refresh.
# - Resetting cache data.
# - Viewing cache statistics.

# +
# Import necessary modules.
import logging
import time

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg

# +
hdbg.init_logger(verbosity=logging.INFO)

_LOG = logging.getLogger(__name__)


# -

# ## Setting up Caching with `@hcsi.simple_cache`
#
# The `@hcsi.simple_cache` decorator is the core feature of `hcache_simple`. It enables caching for a function and supports both memory- and disk-based storage (`json` or `pickle` format).
#
# We'll demonstrate this with a function that simulates a slow computation.


# %%
@hcacsimp.simple_cache(cache_type="json", write_through=True)
def slow_square(x):
    """
    Simulate a slow function that computes the square of a number.

    The `@hcsi.simple_cache` decorator caches the results of this
    function to avoid recomputation for the same input.
    """
    time.sleep(2)  # Simulate a time-consuming computation
    return x**2


# ### Explanation of the Decorator Parameters
# - `cache_type="json"`: The cache will be stored in JSON format on disk.
# - `write_through=True`: Any changes to the cache will be written to disk immediately.

# ## Demonstration: First and Subsequent Calls
# Let's see how caching works:
# 1. On the first call with a specific input, the function takes time to compute.
# 2. On subsequent calls with the same input, the result is retrieved instantly from the cache.

# First call: Result is computed and cached.
print("First call (expected delay):")
result = slow_square(4)
print(f"Result: {result}")

# Second call: Result is retrieved from the cache.
print("\nSecond call (retrieved from cache):")
result = slow_square(4)
print(f"Result: {result}")

# ## Monitoring Cache Performance
# The `hcache_simple` module provides utilities to track cache performance metrics, such as the total number of calls, cache hits, and cache misses.
#
# ### Explanation of Performance Metrics
# - **Total Calls (`tot`)**: The total number of times the function was invoked.
# - **Cache Hits (`hits`)**: The number of times the result was retrieved from the cache.
# - **Cache Misses (`misses`)**: The number of times the function had to compute the result due to a cache miss.
# - **Hit Rate**: The percentage of calls where the result was retrieved from the cache.

# Enable cache performance monitoring for `slow_square`.
hcacsimp.enable_cache_perf("slow_square")

# Retrieve and display cache performance statistics.
print("\nCache Performance Stats:")
print(hcacsimp.get_cache_perf_stats("slow_square"))

# ## Advanced Features
# ### 1. Forcing a Cache Refresh
# By default, the function retrieves results from the cache if available. However, you can force the function to recompute the result and update the cache by enabling the `force_refresh` property.

# Force refresh: The function recomputes the result even if it exists in the cache.
print("\nForce refresh enabled:")
hcacsimp.set_cache_property("user", "slow_square", "force_refresh", True)
result = slow_square(4)
print(f"Result: {result}")

# ### 2. Resetting the Cache
# If needed, you can clear the cache for a specific function. This is useful for resetting state or handling corrupted cache data.

# Reset the cache for `slow_square`.
print("\nResetting the cache:")
hcacsimp.reset_cache("slow_square")
print("Cache reset.")

# Recalculating after cache reset.
print("Recalculating after cache reset:")
result = slow_square(4)
print(f"Result: {result}")

# ## Viewing Cache Statistics
# The `hcsi.cache_stats_to_str` function provides a summary of the current cache state, including the number of items stored in memory and on disk.
#
# ### Explanation of Cache Storage
# - **Memory Cache**: Stores results in memory for quick access.
# - **Disk Cache**: Stores results on disk for persistence across program runs.

# Display cache statistics.
print("\nCache Statistics:")
print(hcacsimp.cache_stats_to_str("slow_square"))
