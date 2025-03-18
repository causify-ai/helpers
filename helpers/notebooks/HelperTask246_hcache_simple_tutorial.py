# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <a name='this-module-covers:'></a>
# <a name='this-tutorial-provides-a-detailed-walkthrough-of-the-hcache_simple-module,-which-implements-a-lightweight-caching-mechanism.-caching-can-significantly-improve-performance-for-functions-with-expensive-computations-by-storing-and-reusing-their-results.'></a>
# <a name='using-hcache_simple-for-caching-in-python'></a>
#
# # Using hcache_simple for Caching in Python
#
# ## This tutorial provides a detailed walkthrough of the hcache_simple module, which implements a lightweight caching mechanism. Caching can significantly improve performance for functions with expensive computations by storing and reusing their results.
#
#

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


# <a name='setting-up-caching-with-@hcsi.simple_cache'></a>
#
# ## Setting up Caching with @hcsi.simple_cache
#
# The @hcsi.simple_cache decorator is the core feature of hcache_simple. It enables caching for a function and supports both memory- and disk-based storage (json or pickle format).
#
# We'll demonstrate this with a function that simulates a slow computation.
#


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def slow_square(x):
    """
    Simulate a slow function that computes the square of a number.

    The `@hcsi.simple_cache` decorator caches the results of this
    function to avoid recomputation for the same input.
    """
    time.sleep(2)  # Simulate a time-consuming computation
    return x**2


# <a name='explanation-of-the-decorator-parameters'></a>
#
# ## Explanation of the Decorator Parameters
#
#     - cache_type="json": The cache will be stored in JSON format on disk.
#     - write_through=True: Any changes to the cache will be written to disk immediately.
#

# <a name='demonstration:-first-and-subsequent-calls'></a>
#
# ## Demonstration: First and Subsequent Calls
#
# Let's see how caching works:
#
#     - On the first call with a specific input, the function takes time to compute.
#     - On subsequent calls with the same input, the result is retrieved instantly from the cache.
#
#

# First call: Result is computed and cached.
print("First call (expected delay):")
result = slow_square(4)
print(f"Result: {result}")

# Second call: Result is retrieved from the cache.
print("\nSecond call (retrieved from cache):")
result = slow_square(4)
print(f"Result: {result}")

# <a name='the-hcache_simple-module-provides-utilities-to-track-cache-performance-metrics,-such-as-the-total-number-of-calls,-cache-hits,-and-cache-misses.'></a>
# <a name='monitoring-cache-performance'></a>
# ## Monitoring Cache Performance
#
# ### The hcache_simple module provides utilities to track cache performance metrics, such as the total number of calls, cache hits, and cache misses.
# Explanation of Performance Metrics
#
#     - Total Calls (tot): The total number of times the function was invoked.
#     - Cache Hits (hits): The number of times the result was retrieved from the cache.
#     - Cache Misses (misses): The number of times the function had to compute the result due to a cache miss.
#     - Hit Rate: The percentage of calls where the result was retrieved from the cache.
#
#

# Enable cache performance monitoring for `slow_square`.
hcacsimp.enable_cache_perf("slow_square")

# Retrieve and display cache performance statistics.
print("\nCache Performance Stats:")
print(hcacsimp.get_cache_perf_stats("slow_square"))

# +
# Enable performance tracking before calling the function.
hcacsimp.enable_cache_perf("slow_square")

print("First call (expected delay):")
result = slow_square(4)  # This call will be recorded as a cache miss.
print(f"Result: {result}")

print("\nSecond call (retrieved from cache):")
result = slow_square(4)  # This call will be recorded as a cache hit.
print(f"Result: {result}")

print("\nCache Performance Stats:")
print(hcacsimp.get_cache_perf_stats("slow_square"))
# -


# <a name='flush-cache-to-disk'></a>
# <a name='advanced-features'></a>
# ## Advanced Features
#
# ## Flush Cache to Disk
# The following cell writes the current in‑memory cache to disk. This is useful if you want persistence across sessions.
#

print("Flushing cache to disk for 'slow_square'...")
hcacsimp.flush_cache_to_disk("slow_square")
print("Cache stats after flushing to disk:")
print(hcacsimp.cache_stats_to_str("slow_square"))


# <a name='reset-in‑memory-cache'></a>
# ## Reset In‑Memory Cache
#
# Here we reset the in‑memory cache. After this, the in‑memory cache will be empty until reloaded from disk.

print("\nResetting in-memory cache for 'slow_square'...")
hcacsimp.reset_mem_cache("slow_square")
print("Cache stats after resetting in-memory cache:")
print(hcacsimp.cache_stats_to_str("slow_square"))

# <a name='force-cache-from-disk'></a>
# ## Force Cache from Disk
# Now we force the in‑memory cache to update from disk. This should repopulate our cache based on the disk copy.
#

print("\nForcing cache from disk for 'slow_square'...")
hcacsimp.force_cache_from_disk("slow_square")
print("Cache stats after forcing cache from disk:")
print(hcacsimp.cache_stats_to_str("slow_square"))

# <a name='attempt-to-reset-disk-cache'></a>
# ## Attempt to Reset Disk Cache
#
# The `reset_disk_cache` function is currently not implemented (it contains an assertion).
# We'll catch the expected error to confirm its behavior.
#

try:
    print(
        "\nAttempting to reset disk cache for 'slow_square' (expected to fail)..."
    )
    hcacsimp.reset_disk_cache("slow_square")
except AssertionError:
    print("reset_disk_cache raised an AssertionError as expected.")

# <a name='viewing-cache-statistics'></a>
# ## Viewing Cache Statistics
#
# The hcsi.cache_stats_to_str function provides a summary of the current cache state, including the number of items stored in memory and on disk.
# Explanation of Cache Storage
#
#     - Memory Cache: Stores results in memory for quick access.
#     - Disk Cache: Stor# Display cache statistics.
#
#

# Display cache statistics.
print("\nCache Statistics:")
print(hcacsimp.cache_stats_to_str("slow_square"))
