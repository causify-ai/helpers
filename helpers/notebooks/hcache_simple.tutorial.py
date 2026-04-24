# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Using hcache_simple for Caching in Python
#
# This tutorial provides a detailed walkthrough of the `hcache_simple` module,
# which implements a lightweight caching mechanism.

# %%
# %load_ext autoreload
# %autoreload 2

# %%
# Import necessary modules.
import logging
import time

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg

# %%
hdbg.init_logger(verbosity=logging.INFO)

_LOG = logging.getLogger(__name__)


# %%
# Force a reload.
import importlib

importlib.reload(hcacsimp)

# %% [markdown]
# ## Setting up caching
#
# The `@hcsi.simple_cache` decorator enables caching for a function and supports both memory- and disk-based storage (json or pickle format).
#
# We'll demonstrate this with a function that simulates a slow computation.


# %%
# cache_type="json": The cache will be stored in JSON format on disk.
# write_through=True: Any changes to the cache will be written to disk immediately.
@hcacsimp.simple_cache(cache_type="json", write_through=True)
def slow_square(x):
    """
    Simulate a slow function that computes the square of a number.

    The `@hcsi.simple_cache` decorator caches the results of this
    function to avoid recomputation for the same input.
    """
    # Simulate a time-consuming computation.
    print("Computing ...")
    time.sleep(2)
    return x**2


# %%
print(hcacsimp.cache_property_to_str("slow_square"))

# %% [markdown]
# ## Demonstration: First and Subsequent Calls
#
# Let's see how caching works:
#
# - On the first call with a specific input, the function takes time to compute.
# - On subsequent calls with the same input, the result is retrieved instantly from the cache.

# %%
cache_file = hcacsimp._get_cache_file_name("slow_square")
hdbg.dassert_eq(cache_file, "/app/tmp.cache_simple.slow_square.json")

hcacsimp.reset_cache(interactive=False)
hcacsimp.reset_cache_property()

# %%
# !ls /app/tmp.cache_simple.*

# %%
# There should be no cache file yet.
# !ls -l $cache_file

# %%
# First call is slow: the result is computed and cached.
print("# First call (expected delay):")
result = slow_square(4)
print(f"Result: {result}")

# %%
# The cache file is created and stores the content.
# !cat $cache_file

# %%
# Second call is fast: the result is retrieved from the cache.
print("# Second call (retrieved from cache):")
result = slow_square(4)
print(f"Result: {result}")

# %%
# Call another value -> cache miss.
result = slow_square(3)
print(f"Result: {result}")

# %%
# !cat $cache_file

# %% [markdown]
# ## Monitoring Cache Performance
#
# The `hcache_simple` module provides utilities to track cache performance metrics,
# such as the total number of calls, cache hits, and cache misses.

# %%
# Enable cache performance monitoring for the function `slow_square`.
hcacsimp.enable_cache_perf("slow_square")

# %%
# Retrieve and display cache performance statistics.
print("# Cache Performance Stats:")
print(hcacsimp.get_cache_perf_stats("slow_square"))

# %% [markdown]
# Explanation of Performance Metrics
#
# - Total Calls (tot): The total number of times the function was invoked.
# - Cache Hits (hits): The number of times the result was retrieved from the cache.
# - Cache Misses (misses): The number of times the function had to compute the result due to a cache miss.
# - Hit Rate: The percentage of calls where the result was retrieved from the cache.

# %%
hcacsimp.reset_cache(interactive=False)
hcacsimp.reset_cache_perf("slow_square")

print("# First call (expected delay):")
result = slow_square(4)  # This call will be recorded as a cache miss.
print(f"Result: {result}")

print("\n# Second call (retrieved from cache):")
result = slow_square(4)  # This call will be recorded as a cache hit.
print(f"Result: {result}")

print("\n# Cache performance stats:")
print(hcacsimp.get_cache_perf_stats("slow_square"))


# %% [markdown]
# ## Flush Cache to Disk

# %%
# The following cell writes the current in‑memory cache to disk. This is useful
# if you want persistence across sessions.
print("# Flushing cache to disk for 'slow_square'...")
hcacsimp.flush_cache_to_disk("slow_square")

# The `hcsi.cache_stats_to_str` function provides a summary of the current cache
# state, including the number of items stored in memory and on disk.
print("\n# Cache stats:")
print(hcacsimp.cache_stats_to_str("slow_square"))


# %% [markdown]
# ## Reset In‑Memory Cache
#
# Now reset the in‑memory cache. After this, the in‑memory cache will be empty until reloaded from disk.

# %%
print("# Resetting in-memory cache for 'slow_square'...")
hcacsimp.reset_mem_cache("slow_square")

print("\n# Cache stats:")
print(hcacsimp.cache_stats_to_str("slow_square"))

# %% [markdown]
# ## Force Cache from Disk
#
# Now we force the in‑memory cache to update from disk. This should repopulate our
# cache based on the disk copy.

# %%
print("# Forcing cache from disk for 'slow_square'...")
hcacsimp.force_cache_from_disk("slow_square")

print("\n# Cache stats:")
print(hcacsimp.cache_stats_to_str("slow_square"))

# %% [markdown]
# ## Attempt to Reset Disk Cache
#
# The `reset_disk_cache` function is currently not implemented (it contains an assertion).
# We'll catch the expected error to confirm its behavior.

# %%
try:
    print(
        "\nAttempting to reset disk cache for 'slow_square' (expected to fail)..."
    )
    hcacsimp.reset_disk_cache("slow_square")
except AssertionError:
    print("reset_disk_cache raised an AssertionError as expected.")

# %% [markdown]
# # Dynamic parameters

# %% [markdown]
# ## force_refresh

# %%
print(hcacsimp.get_cache_perf_stats("slow_square"))
hcacsimp.reset_cache_perf("slow_square")
print(hcacsimp.get_cache_perf_stats("slow_square"))

# %%
slow_square(4)

# %%
print(hcacsimp.get_cache_perf_stats("slow_square"))

# %%
# Force a recompute.
slow_square(4, force_refresh=True)

# %%
print(hcacsimp.get_cache_perf_stats("slow_square"))

# %% [markdown]
# ## abort_on_cache_miss

# %%
hcacsimp.reset_cache(interactive=False)

# %%
# This call doesn't abort since it's not a cache miss.
slow_square(4, abort_on_cache_miss=True)

# %%
# This call aborts since it's a cache miss.
try:
    slow_square(16, abort_on_cache_miss=True)
except ValueError as e:
    print(e)

# %%
slow_square(16, report_on_cache_miss=True)

# %%
