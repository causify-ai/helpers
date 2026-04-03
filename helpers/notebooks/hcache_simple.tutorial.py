# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# CONTENTS:
# - [hcache_simple Tutorial](#hcache_simple-tutorial)
#   - [Setup](#setup)
#   - [1. Basic Caching](#1.-basic-caching)
#   - [2. Cache Performance Monitoring](#2.-cache-performance-monitoring)
#   - [3. Cache Management](#3.-cache-management)
#   - [4. Dynamic Runtime Parameters](#4.-dynamic-runtime-parameters)
#   - [5. Configurable Cache Locations](#5.-configurable-cache-locations)
#   - [6. Per-Function Configuration](#6.-per-function-configuration)
#   - [7. Excluding Keys from Cache](#7.-excluding-keys-from-cache)
#   - [8. S3 Integration (Team Cache Sharing)](#8.-s3-integration-(team-cache-sharing))
#   - [9. Binary Data with Pickle](#9.-binary-data-with-pickle)
#   - [Summary](#summary)

# %% [markdown]
# <a name='hcache_simple-tutorial'></a>
# # hcache_simple Tutorial
#
# This tutorial demonstrates the `hcache_simple` module - a lightweight caching system with memory, disk, and S3 storage.
#
# **Key Features:**
# - Simple decorator-based caching
# - Memory and disk persistence (JSON or pickle)
# - S3 sync for team cache sharing
# - Per-function configuration
# - Performance monitoring
# - Auto-pull from S3 on first cache miss

# %% [markdown]
# <a name='setup'></a>
# ## Setup

# %%
import logging
import time

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg

hdbg.init_logger(verbosity=logging.INFO)
_LOG = logging.getLogger(__name__)

# %% [markdown]
# <a name='1.-basic-caching'></a>
# ## 1. Basic Caching
#
# The `@simple_cache` decorator caches function results automatically.
#
# - First call: Computes result and stores in cache
# - Subsequent calls: Returns cached result instantly
# - Cache is stored in memory and on disk (JSON format)


# %%
@hcacsimp.simple_cache(cache_type="json")
def expensive_computation(x: int) -> int:
    """
    Simulate expensive computation.
    """
    _LOG.info("Computing result for x=%s (this takes 2 seconds)...", x)
    time.sleep(2)
    return x**2


# %%
# First call - computes and caches.
print("First call with x=5:")
result = expensive_computation(5)
print(f"Result: {result}\n")
# Second call - returns from cache instantly.
print("Second call with x=5 (from cache):")
result = expensive_computation(5)
print(f"Result: {result}")

# %% [markdown]
# <a name='2.-cache-performance-monitoring'></a>
# ## 2. Cache Performance Monitoring
#
# Track cache efficiency with performance metrics:
# - **hits**: Number of times result was retrieved from cache
# - **misses**: Number of times function had to compute result
# - **tot**: Total number of function calls
# - **hit_rate**: Percentage of cache hits

# %%
# Enable performance monitoring.
hcacsimp.enable_cache_perf("expensive_computation")
# Make some calls.
expensive_computation(10)  # Miss - first call with x=10.
expensive_computation(10)  # Hit - cached result.
expensive_computation(10)  # Hit - cached result.
expensive_computation(20)  # Miss - first call with x=20.
# Check performance stats.
print("\nPerformance Statistics:")
print(hcacsimp.get_cache_perf_stats("expensive_computation"))

# %% [markdown]
# <a name='3.-cache-management'></a>
# ## 3. Cache Management
#
# Control cache lifecycle with these operations:
# - `flush_cache_to_disk()`: Write memory cache to disk
# - `reset_mem_cache()`: Clear memory cache (keeps disk cache)
# - `force_cache_from_disk()`: Reload cache from disk
# - `cache_stats_to_str()`: View cache statistics

# %%
# View current cache state.
print("Cache statistics:")
print(hcacsimp.cache_stats_to_str("expensive_computation"))
# Flush to disk (ensure persistence).
hcacsimp.flush_cache_to_disk("expensive_computation")
print("\nFlushed to disk")
# Clear memory cache.
hcacsimp.reset_mem_cache("expensive_computation")
print("Memory cache cleared")
print(hcacsimp.cache_stats_to_str("expensive_computation"))
# Reload from disk.
hcacsimp.force_cache_from_disk("expensive_computation")
print("\nReloaded from disk")
print(hcacsimp.cache_stats_to_str("expensive_computation"))

# %% [markdown]
# <a name='4.-dynamic-runtime-parameters'></a>
# ## 4. Dynamic Runtime Parameters
#
# Control caching behavior per function call:
# - `force_refresh=True`: Bypass cache and recompute
# - `abort_on_cache_miss=True`: Raise error if not in cache
# - `report_on_cache_miss=True`: Log warning on cache miss


# %%
@hcacsimp.simple_cache(cache_type="json")
def data_processor(data: str) -> str:
    """
    Process data string.
    """
    _LOG.info("Processing: %s", data)
    time.sleep(1)
    return data.upper()


# %%
# Normal call - caches result.
result = data_processor("hello")
print(f"First call: {result}")
# Force refresh - recomputes even though cached.
result = data_processor("hello", force_refresh=True)
print(f"Force refresh: {result}")
# Report on cache miss.
result = data_processor("world", report_on_cache_miss=True)
print(f"With report: {result}")

# %% [markdown]
# <a name='5.-configurable-cache-locations'></a>
# ## 5. Configurable Cache Locations
#
# Customize where cache files are stored globally:
# - `set_cache_dir()`: Change cache directory
# - `set_cache_file_prefix()`: Change cache file prefix

# %%
# Set custom cache directory.
import os
import tempfile

cache_dir = tempfile.mkdtemp()
hcacsimp.set_cache_dir(cache_dir)
print(f"Cache directory set to: {cache_dir}")
# Set custom prefix.
hcacsimp.set_cache_file_prefix("my_project")
print("Cache file prefix set to: my_project")


# New cached function will use these settings.
@hcacsimp.simple_cache(cache_type="json")
def custom_location_func(x: int) -> int:
    return x * 3


# Call function.
result = custom_location_func(7)
# Verify cache file location.
cache_files = [f for f in os.listdir(cache_dir) if "my_project" in f]
print(f"\nCache files created: {cache_files}")

# %% [markdown]
# <a name='6.-per-function-configuration'></a>
# ## 6. Per-Function Configuration
#
# Override global settings for specific functions:
# - Each function can have its own cache directory
# - Each function can have its own cache prefix
# - Useful for organizing different types of caches


# %%
@hcacsimp.simple_cache(
    cache_type="json",
    cache_dir="/tmp/function_a_cache",
    cache_prefix="func_a",
)
def function_a(x: int) -> int:
    return x + 100


@hcacsimp.simple_cache(
    cache_type="json",
    cache_dir="/tmp/function_b_cache",
    cache_prefix="func_b",
)
def function_b(x: int) -> int:
    return x + 200


# %%
# Call both functions - each uses its own cache location.
result_a = function_a(5)
result_b = function_b(5)
print(f"function_a(5) = {result_a}")
print(f"function_b(5) = {result_b}")
# Verify separate cache files.
print("\nfunction_a cache location:")
print(hcacsimp.cache_stats_to_str("function_a"))
print("\nfunction_b cache location:")
print(hcacsimp.cache_stats_to_str("function_b"))

# %% [markdown]
# <a name='7.-excluding-keys-from-cache'></a>
# ## 7. Excluding Keys from Cache
#
# Some parameters should not affect cache lookup:
# - Session IDs
# - Logger objects
# - Timestamps
# - Random seeds (when you want same result)
#
# Use `exclude_keys` to ignore these parameters.


# %%
@hcacsimp.simple_cache(
    cache_type="json",
    exclude_keys=["session_id", "timestamp"],
)
def api_call(query: str, session_id: str, timestamp: float) -> str:
    """
    Simulate API call where session_id and timestamp don't affect result.
    """
    _LOG.info("Making API call for query: %s", query)
    time.sleep(1)
    return f"Response for: {query}"


# %%
# These calls have different session_id and timestamp but return cached result.
result1 = api_call("search python", session_id="abc123", timestamp=1.0)
print(f"First call: {result1}")
result2 = api_call("search python", session_id="xyz789", timestamp=2.0)
print(f"Second call (from cache despite different session/timestamp): {result2}")
# Different query triggers cache miss.
result3 = api_call("search java", session_id="abc123", timestamp=1.0)
print(f"Third call (different query, cache miss): {result3}")

# %% [markdown]
# <a name='8.-s3-integration-(team-cache-sharing)'></a>
# ## 8. S3 Integration (Team Cache Sharing)
#
# **Note:** These examples are commented out because they require AWS credentials.
# Uncomment and configure to use S3 caching.
#
# **S3 Features:**
# - `auto_sync_s3=True`: Automatically upload cache updates to S3
# - Auto-pull: On first cache miss, automatically downloads from S3 (no manual pull needed!)
# - Team sharing: Multiple developers/machines share the same cache
# - Backup: S3 serves as persistent backup for local caches
#
# **Usage:**
# 1. Configure S3 globally or per-function
# 2. First call on any machine computes and uploads to S3
# 3. Other machines automatically pull from S3 on first cache miss
# 4. Updates are automatically synced to S3 (if `auto_sync_s3=True`)

# %%
# # Global S3 configuration (applies to all cached functions).
# hcacsimp.set_s3_bucket("s3://my-team-bucket")
# hcacsimp.set_s3_prefix("cache/shared")
# hcacsimp.set_aws_profile("my-aws-profile")
#
# @hcacsimp.simple_cache(
#     cache_type="json",
#     auto_sync_s3=True,  # Auto-upload to S3 after updates.
# )
# def expensive_llm_call(prompt: str) -> str:
#     """
#     Simulate expensive LLM API call.
#     """
#     time.sleep(3)
#     return f"LLM response to: {prompt}"
#
# # First call on any machine - computes and uploads to S3.
# result = expensive_llm_call("Summarize this document")
# print(f"Result: {result}")
#
# # On another machine - auto-pulls from S3 on first call!
# # No manual pull_cache_from_s3() needed.
# result = expensive_llm_call("Summarize this document")
# print(f"Result from S3 cache: {result}")

# %%
# # Per-function S3 configuration (overrides global settings).
# @hcacsimp.simple_cache(
#     cache_type="json",
#     s3_bucket="s3://project-specific-bucket",
#     s3_prefix="cache/llm",
#     aws_profile="project-profile",
#     auto_sync_s3=True,
# )
# def project_specific_cache(data: str) -> str:
#     return f"Processed: {data}"
#
# result = project_specific_cache("test data")

# %% [markdown]
# <a name='9.-binary-data-with-pickle'></a>
# ## 9. Binary Data with Pickle
#
# For complex Python objects (DataFrames, models, etc.), use pickle format:
# - `cache_type="pickle"`: Stores any Python object
# - Supports DataFrames, numpy arrays, custom classes, etc.
# - Trade-off: Not human-readable like JSON

# %%
import pandas as pd


@hcacsimp.simple_cache(cache_type="pickle")
def create_dataframe(rows: int) -> pd.DataFrame:
    """
    Create a DataFrame (can't be cached as JSON easily).
    """
    _LOG.info("Creating DataFrame with %s rows...", rows)
    time.sleep(1)
    return pd.DataFrame(
        {
            "id": range(rows),
            "value": [x**2 for x in range(rows)],
        }
    )


# %%
# First call - computes and caches DataFrame.
df = create_dataframe(5)
print("First call:")
print(df)
# Second call - returns cached DataFrame instantly.
df = create_dataframe(5)
print("\nSecond call (from cache):")
print(df)

# %% [markdown]
# <a name='summary'></a>
# ## Summary
#
# The `hcache_simple` module provides:
# - **Easy caching**: Just add `@simple_cache` decorator
# - **Multiple storage layers**: Memory (fast) → Disk (persistent) → S3 (shared)
# - **Flexible configuration**: Global and per-function settings
# - **Performance monitoring**: Track cache efficiency
# - **Team collaboration**: Share caches via S3 with auto-pull
# - **Format support**: JSON (human-readable) or pickle (binary)
#
# **Key Design:**
# - Memory cache for speed
# - Disk cache for persistence across sessions
# - S3 cache for team sharing and backup
# - Auto-pull from S3 on first cache miss (no manual intervention needed)
#
# For full documentation, see: `docs/tools/helpers/all.hcache_simple.explanation.md`
