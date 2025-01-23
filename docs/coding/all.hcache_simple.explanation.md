# `helpers.hcache_simple`

<!-- toc -->

- [Introduction](#introduction)
- [Core Features](#core-features)
- [Key Functions](#key-functions)
  * [`@simple_cache`](#simple_cache)
  * [`enable_cache_perf`](#enable_cache_perf)
  * [`get_cache_perf_stats`](#get_cache_perf_stats)
  * [`set_cache_property`](#set_cache_property)
  * [`reset_cache`](#reset_cache)
  * [`cache_stats_to_str`](#cache_stats_to_str)
  * [`flush_cache_to_disk`](#flush_cache_to_disk)
  * [`reset_disk_cache`](#reset_disk_cache)
  * [`reset_mem_cache`](#reset_mem_cache)
- [Best Practices](#best-practices)
  * [When to Use Caching](#when-to-use-caching)
  * [Monitoring and Debugging](#monitoring-and-debugging)
  * [Cache Management](#cache-management)
- [Troubleshooting](#troubleshooting)

<!-- tocstop -->

## Introduction

The `hcache_simple` module provides a lightweight and configurable caching
mechanism for Python functions. This tool optimizes function performance by
storing results in memory or on disk, reducing redundant computations. This
document explains the purpose of each function, how to use them, and
troubleshooting tips to ensure seamless integration.

---

## Core Features

- **Efficient Caching**: Provides decorators to enable caching for Python
  functions.
- **Performance Monitoring**: Tracks cache hits, misses, and total calls.
- **Memory and Disk Storage**: Supports in-memory caching and persistence on
  disk (JSON or Pickle formats).
- **Customizable Configuration**: Allows users to adjust caching behaviors such
  as forced refresh and cache miss reporting.

---

## Key Functions

### `@simple_cache`

**Purpose**: The primary decorator to enable caching for functions.

- **Parameters**:
  - `cache_type`: Determines the format for cache storage (`"json"` or
    `"pickle"`).
  - `write_through`: Ensures changes to the cache are immediately written to
    disk.
- **How to Use**:
  - Add `@simple_cache` above the function definition.
  - Example:

    ```python
    @simple_cache(cache_type="json", write_through=True)
    def slow_function(x):
        return x ** 2
    ```

---

### `enable_cache_perf`

**Purpose**: Enables cache performance monitoring for the specified function.

- **How to Verify**:
  - Call `enable_cache_perf("function_name")`.
  - Use `get_cache_perf_stats` to view performance metrics.
- **Troubleshooting**:
  - If no data appears, ensure the function is decorated with `@simple_cache`.

---

### `get_cache_perf_stats`

**Purpose**: Retrieves performance metrics, including hits, misses, and the hit
rate.

- **Output**: A string containing statistics like:

  ```bash
  slow_square: hits=5 misses=2 tot=7 hit_rate=0.71
  ```

---

### `set_cache_property`

**Purpose**: Sets advanced properties for cache behavior.

- **Parameters**:
- `type_`: `"user"` or `"system"`.
- `func_name`: Name of the cached function.
- `property_name`: Property to configure (e.g., `"force_refresh"`,
  `"abort_on_cache_miss"`).
- `val`: Value to set for the property.
- **Example**:
- Enable forced refresh:

  ```python
  set_cache_property("user", "slow_function", "force_refresh", True)
  ```

---

### `reset_cache`

**Purpose**: Resets memory and disk caches for a function or all functions.

- **How to Use**:
- Reset a specific function's cache:

  ```python
  reset_cache("slow_function")
  ```

- Reset all caches:

  ```python
  reset_cache()
  ```

- **Troubleshooting**:
- Ensure `reset_disk_cache` is implemented correctly in the module.

---

### `cache_stats_to_str`

**Purpose**: Returns a structured summary of cache data for a specific function
or all functions.

- **Output**:
- Number of cached items in memory and on disk, such as:
  
  ```bash
  slow_function
  memory: 2
  disk: 5
  ```

---

### `flush_cache_to_disk`

**Purpose**: Saves memory cache data to disk for persistence across program
runs.

- **When to Use**:
- Use this before shutting down a long-running application to avoid losing
  cached results.

---

### `reset_disk_cache`

**Purpose**: Clears the disk cache for a specific function or all functions.

- **How to Use**:
- Reset a specific function's disk cache:

  ```python
  reset_disk_cache("slow_function")
  ```

- Reset all disk caches:

  ```python
  reset_disk_cache()
  ```

- **Verification**:

- After execution, ensure related cache files (e.g., `cache.slow_function.json`)
  are deleted from the disk.

---

### `reset_mem_cache`

**Purpose**: Clears the memory cache for a specific function or all functions.

- **When to Use**:
- To free up memory without affecting disk cache.

---

## Best Practices

### When to Use Caching

- Use `@simple_cache` for functions with expensive computations or API calls
  with consistent results.
- Choose `cache_type="pickle"` for faster serialization or `"json"` for
  human-readable caching.

### Monitoring and Debugging

- Always enable performance monitoring with `enable_cache_perf`.
- Regularly check cache statistics using `get_cache_perf_stats`.

### Cache Management

- Use `reset_cache` judiciously to avoid unintended data loss.
- Periodically flush memory cache to disk with `flush_cache_to_disk` for
  persistence.

---

## Troubleshooting

- **Cache Miss When Expected**:
- Verify that the function is decorated with `@simple_cache`.
- Check if `force_refresh` is enabled and disable it if unnecessary:

  ```python
  set_cache_property("user", "function_name", "force_refresh", False)
  ```

- **Disk Cache Not Found**:
- Ensure the function name matches the cache file name.
- Verify that `cache_type` is correctly set in the decorator.

---
