"""
Detailed documentation at.

- //helpers/docs/tools/helpers/all.hcache_simple.explanation.md
- //helpers/notebooks/hcache_simple.tutorial.ipynb

Import as:

import helpers.hcache_simple as hcacsimp
"""

import functools
import glob
import json
import logging
import os
import pickle
import re
from typing import Any, Callable, Dict, List, Optional

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hs3 as hs3
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Disable tracing for production code.
_LOG.trace = lambda *args, **kwargs: None
# _LOG.trace = _LOG.debug

# #############################################################################
# Memory cache.
# #############################################################################

# Type for the cache of a single function: key -> value properties. E.g.,
# ```
# {
#     "{\"args\": [4], \"kwargs\": {}}": 16
# }
# ```
_FunctionCacheType = Dict[str, Any]

# Basic type for caching data: func_name -> key -> value properties. E.g.,
# ```
# {
#     "slow_square": {
#         "{\"args\": [4], \"kwargs\": {}}": 16
#     }
# }
# ```
_CacheType = Dict[str, _FunctionCacheType]

# Type for cache property storage: func_name -> property_name -> property_value. E.g.,
# ```
# {
#     "slow_square": {
#         "type": "json",
#         "cache_dir": "/tmp/cache",
#         "write_through": True
#     }
# }
# ```
_CachePropertyType = Dict[str, Dict[str, Any]]

# Create global variable for the memory cache.
if "_CACHE" not in globals():
    _LOG.trace("Creating _CACHE")
    _CACHE: _CacheType = {}


def sanity_check_function_cache(
    func_cache_data: _FunctionCacheType, *, assert_on_empty: bool = True
) -> None:
    """
    Sanity check the function cache data.

    :param func_cache_data: The function cache data to check.
    :param assert_on_empty: If True, assert that the function cache data
        is not empty.
    """
    hdbg.dassert_isinstance(func_cache_data, dict)
    if assert_on_empty:
        hdbg.dassert_ne(len(func_cache_data), 0, "Function data is empty")
    for cache_key, cached_value in func_cache_data.items():
        hdbg.dassert_isinstance(cache_key, str)
        hdbg.dassert_ne(cache_key, "", "Cache key is empty")
        # cached_value can be any type, so no type check needed.
        _ = cached_value


def sanity_check_cache(
    cache_data: _CacheType, *, assert_on_empty: bool = True
) -> None:
    """
    Sanity check the cache data.

    :param cache_data: The cache data to check.
    :param assert_on_empty: If True, assert that the cache data is not
        empty.
    """
    hdbg.dassert_isinstance(cache_data, dict)
    if assert_on_empty:
        hdbg.dassert_ne(len(cache_data), 0, "Cache data is empty")
    for func_name, func_cache_data in cache_data.items():
        hdbg.dassert_isinstance(func_name, str)
        hdbg.dassert_ne(func_name, "", "Function name is empty")
        sanity_check_function_cache(
            func_cache_data, assert_on_empty=assert_on_empty
        )


def cache_data_to_str(cache_data: _CacheType) -> str:
    """
    Convert cache data to a human-readable string.

    :param cache_data: The cache data to convert.
    :return: A string representation of the cache data.
    """
    txt = []
    txt.append(hprint.frame("Cache data"))
    hdbg.dassert_isinstance(cache_data, dict)
    for func_name, func_data in cache_data.items():
        txt.append(f"# func_name={func_name}")
        hdbg.dassert_isinstance(func_data, dict)
        for cache_key, cached_value in func_data.items():
            txt.append(f"  cache_key={cache_key} cached_value={cached_value}")
    result = "\n".join(txt)
    return result


# #############################################################################
# Cache properties.
# #############################################################################

# There are several ways to control caching behavior:
# - By passing special control parameters to the decorated function:
#   `force_refresh`, `abort_on_cache_miss`, `report_on_cache_miss`, `cache_mode`
# - By setting cache properties:
#   - E.g., set_cache_property("func_name", "write_through", False)

# - There are two types of properties:
#   - `User Properties`: Configurable by the user to alter caching behavior.
#      E.g.,
#     - `abort_on_cache_miss`: Whether to raise an error if a cache miss occurs
#     - `report_on_cache_miss`: Whether to return a special value ("_cache_miss_")
#       on a cache miss
#     - `force_refresh`: Whether to bypass the cache and refresh the value
#   - `System Properties`:
#     - cache type (e.g., "json" or "pickle")
#     - write through (e.g., True or False)
#     - exclude keys (e.g., ["password", "api_key"])
#     - per-function cache location (cache_dir, cache_prefix)
#     - per-function S3 configuration (s3_bucket, s3_prefix, aws_profile, auto_sync_s3)

_SYSTEM_PROPERTIES = [
    "type",
    "write_through",
    "exclude_keys",
    "cache_dir",
    "cache_prefix",
    "s3_bucket",
    "s3_prefix",
    "aws_profile",
    "auto_sync_s3",
]


def get_main_cache_dir() -> str:
    """
    Get the main cache directory (git root).

    :return: The absolute path to the main cache directory.
    """
    git_dir = hgit.find_git_root()
    cache_dir = os.path.abspath(git_dir)
    return cache_dir


# Create global variable for the cache directory.
if "_CACHE_DIR" not in globals():
    _LOG.trace("Creating _CACHE_DIR")
    _CACHE_DIR = get_main_cache_dir()


def set_cache_dir(cache_dir: str) -> None:
    """
    Set the cache directory.
    """
    global _CACHE_DIR
    hdbg.dassert_isinstance(cache_dir, str)
    _CACHE_DIR = os.path.abspath(cache_dir)
    hio.create_dir(_CACHE_DIR, incremental=True)
    _LOG.trace("Setting _CACHE_DIR to %s", _CACHE_DIR)


def get_cache_dir() -> str:
    """
    Get the cache directory.
    """
    return _CACHE_DIR


# Create global variable for the cache file prefix.
if "_CACHE_FILE_PREFIX" not in globals():
    _LOG.trace("Creating _CACHE_FILE_PREFIX")
    _CACHE_FILE_PREFIX = "tmp.cache_simple"


def set_cache_file_prefix(prefix: str) -> None:
    """
    Set the cache file prefix.

    :param prefix: prefix to use for cache files
    """
    global _CACHE_FILE_PREFIX
    hdbg.dassert_isinstance(prefix, str)
    hdbg.dassert_ne(prefix, "", "Cache file prefix cannot be empty")
    if prefix.endswith("."):
        _LOG.warning(
            "Prefix '%s' ends with '.' - cache files will have '..' in names",
            prefix,
        )
    _CACHE_FILE_PREFIX = prefix
    _LOG.trace("Setting _CACHE_FILE_PREFIX to %s", _CACHE_FILE_PREFIX)


def get_cache_file_prefix() -> str:
    """
    Get the cache file prefix.

    :return: cache file prefix
    """
    return _CACHE_FILE_PREFIX


# #############################################################################
# S3 cache configuration.
# #############################################################################

# Create global variable for S3 bucket.
if "_S3_BUCKET" not in globals():
    _LOG.trace("Creating _S3_BUCKET")
    _S3_BUCKET: Optional[str] = None

# Create global variable for S3 prefix.
if "_S3_PREFIX" not in globals():
    _LOG.trace("Creating _S3_PREFIX")
    _S3_PREFIX: str = "cache"

# Create global variable for AWS profile.
if "_AWS_PROFILE" not in globals():
    _LOG.trace("Creating _AWS_PROFILE")
    _AWS_PROFILE: str = "ck"

# Create global variable to track S3 auto-pull attempts.
if "_S3_AUTO_PULL_ATTEMPTED" not in globals():
    _LOG.trace("Creating _S3_AUTO_PULL_ATTEMPTED")
    _S3_AUTO_PULL_ATTEMPTED: set = set()


def set_s3_bucket(bucket: str) -> None:
    """
    Set the S3 bucket for cache storage.

    :param bucket: S3 bucket name (e.g., "my-bucket" or "s3://my-
        bucket")
    """
    global _S3_BUCKET
    hdbg.dassert_isinstance(bucket, str)
    hdbg.dassert_ne(bucket, "", "S3 bucket cannot be empty")
    # Keep s3:// prefix if present, otherwise add it.
    if not bucket.startswith("s3://"):
        bucket = f"s3://{bucket}"
    _S3_BUCKET = bucket
    _LOG.trace("Setting _S3_BUCKET to %s", _S3_BUCKET)


def get_s3_bucket() -> Optional[str]:
    """
    Get the S3 bucket for cache storage.

    :return: S3 bucket name with s3:// prefix, or None if not configured
    """
    return _S3_BUCKET


def set_s3_prefix(prefix: str) -> None:
    """
    Set the S3 prefix for cache files.

    :param prefix: S3 prefix path (e.g., "cache" or "app/cache")
    """
    global _S3_PREFIX
    hdbg.dassert_isinstance(prefix, str)
    # Remove leading/trailing slashes.
    prefix = prefix.strip("/")
    _S3_PREFIX = prefix
    _LOG.trace("Setting _S3_PREFIX to %s", _S3_PREFIX)


def get_s3_prefix() -> str:
    """
    Get the S3 prefix for cache files.

    :return: S3 prefix path
    """
    return _S3_PREFIX


def set_aws_profile(profile: str) -> None:
    """
    Set the AWS profile for S3 access.

    :param profile: AWS profile name (e.g., "ck", "csfy")
    """
    global _AWS_PROFILE
    hdbg.dassert_isinstance(profile, str)
    hdbg.dassert_ne(profile, "", "AWS profile cannot be empty")
    _AWS_PROFILE = profile
    _LOG.trace("Setting _AWS_PROFILE to %s", _AWS_PROFILE)


def get_aws_profile() -> str:
    """
    Get the AWS profile for S3 access.

    :return: AWS profile name
    """
    return _AWS_PROFILE


def get_cache_property_file() -> str:
    """
    Get the cache property file name.

    :return: The cache property file name.
    """
    prefix = get_cache_file_prefix()
    val = os.path.join(get_cache_dir(), f"{prefix}_property.pkl")
    return val


def _get_initial_cache_property() -> _CachePropertyType:
    """
    Get the initial cache property (empty dict for session-scoped storage).

    Properties are not loaded from disk - they are set by decorators
    and runtime calls within the current session only.

    :return: An empty dictionary for cache properties.
    """
    # func_name -> property_name -> property_value.
    # Start empty - decorators will populate on import.
    val: _CachePropertyType = {}
    return val


# Create global variables for the cache properties.
# Properties are session-scoped (in-memory only, not persisted to disk).
if "_CACHE_PROPERTY" not in globals():
    _LOG.trace("Creating _CACHE_PROPERTY")
    _CACHE_PROPERTY: _CachePropertyType = _get_initial_cache_property()


def _check_valid_cache_property(property_name: str) -> None:
    """
    Verify that a cache property name is valid for the given type.

    :param property_name: The property name to validate.
    """
    _LOG.trace(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(property_name, str)
    valid_properties = [
        # Abort if there is a cache miss. This is used to make sure everything
        # is cached.
        "abort_on_cache_miss",
        # Report if there is a cache miss and return `_cache_miss_` instead of
        # accessing the real value.
        "report_on_cache_miss",
        # Force to refresh the value.
        "force_refresh",
        # TODO(gp): "force_refresh_once"
        # json or pickle cache type.
        "type",
        # Write-through mode: flush cache to disk after each update.
        "write_through",
        # List of keys to exclude from cache key generation.
        "exclude_keys",
        # Per-function cache directory.
        "cache_dir",
        # Per-function cache file prefix.
        "cache_prefix",
        # Per-function S3 bucket.
        "s3_bucket",
        # Per-function S3 prefix.
        "s3_prefix",
        # Per-function AWS profile.
        "aws_profile",
        # Auto-sync to S3 after cache updates.
        "auto_sync_s3",
    ]
    hdbg.dassert_in(property_name, valid_properties)


def _save_func_cache_data_to_file(
    file_name: str,
    cache_type: Optional[str],
    func_cache_data: _FunctionCacheType,
) -> None:
    """
    Save the function cache data to a file.

    :param file_name: The name of the file.
    :param func_cache_data: The function cache data to save.
    """
    # Infer cache type from file extension if not set.
    if cache_type is None:
        if file_name.endswith(".pkl"):
            cache_type = "pickle"
        else:
            cache_type = "json"
    hio.create_enclosing_dir(file_name, incremental=True)
    _LOG.trace("Saving to '%s'", file_name)
    # Save data.
    if cache_type == "pickle":
        with open(file_name, "wb") as file:
            pickle.dump(func_cache_data, file)
    elif cache_type == "json":
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(
                func_cache_data,
                file,
                indent=4,
                sort_keys=True,
                ensure_ascii=False,
            )
    else:
        raise ValueError(f"Invalid cache type '{cache_type}'")


def set_cache_property(func_name: str, property_name: str, val: Any) -> None:
    """
    Set a property for the cache of a given function name.

    Properties are session-scoped (lost on process restart). This allows
    temporary configuration changes without affecting other processes or
    persisting state across restarts.

    :param func_name: The name of the function whose cache property is
        to be set.
    :param property_name: The name of the property to set.
    :param val: The value to set for the property.
    """
    global _CACHE_PROPERTY
    _LOG.trace(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_isinstance(property_name, str)
    _check_valid_cache_property(property_name)
    # Store in memory only (session-scoped).
    cache_property = _CACHE_PROPERTY
    if func_name not in cache_property:
        cache_property[func_name] = {}
    cache_property[func_name][property_name] = val
    _LOG.trace(
        "Setting property %s='%s' for '%s' (session-scoped)",
        property_name,
        val,
        func_name,
    )


def get_cache_property(func_name: str, property_name: str) -> Any:
    """
    Get the value of a property for the cache of a given function name.

    Properties are session-scoped (stored in memory only).

    :return: The property value, which can be of any type depending on
        the property. Returns None if the property is not set (for
        system properties), or False (for user properties).
    """
    _LOG.trace(hprint.func_signature_to_str())
    _check_valid_cache_property(property_name)
    # Read from in-memory property storage.
    cache_property = _CACHE_PROPERTY
    if property_name in _SYSTEM_PROPERTIES:
        if func_name not in cache_property:
            return None
        value = cache_property[func_name].get(property_name)
    else:
        value = cache_property.get(func_name, {}).get(property_name, False)
    return value


def reset_cache_property() -> None:
    """
    Reset cache properties (clear runtime overrides).

    Removes all user properties (non-system properties like
    force_refresh, abort_on_cache_miss). System properties (type,
    cache_dir, etc.) are preserved as they come from decorators.

    This is useful for clearing temporary runtime configuration.
    """
    _LOG.warning("Resetting cache properties")
    # Empty the values.
    global _CACHE_PROPERTY
    cache_property = _CACHE_PROPERTY
    # Empty the values excluding the system properties like `type` and
    # `write_through`.
    _LOG.trace("before cache_property=%s", cache_property)
    # Iterate over a list of keys to avoid modifying the dictionary during iteration.
    for func_name_tmp in list(cache_property.keys()):
        # Only remove non-system properties from the function's property dict.
        func_prop = cache_property[func_name_tmp]
        for property_name_tmp in list(func_prop.keys()):
            if property_name_tmp not in _SYSTEM_PROPERTIES:
                del func_prop[property_name_tmp]
    _LOG.trace("after cache_property=%s", cache_property)


# #############################################################################
# Get cache.
# #############################################################################

# Functions to retrieve cache (both memory and disk).


def _get_valid_cache_prefixes() -> set:
    """
    Get all valid cache file prefixes.

    :return: set of valid prefixes (global + per-function custom
        prefixes)
    """
    global_prefix = get_cache_file_prefix()
    valid_prefixes = {global_prefix}
    for func_name_tmp in _CACHE_PROPERTY:
        func_prefix = get_cache_property(func_name_tmp, "cache_prefix")
        if func_prefix:
            valid_prefixes.add(func_prefix)
    return valid_prefixes


def _extract_func_names_from_cache_files(
    file_paths: List[str], valid_prefixes: set
) -> set:
    """
    Extract function names from cache file paths.

    :param file_paths: list of file paths to process
    :param valid_prefixes: set of valid cache prefixes to filter by
    :return: set of function names
    """
    func_names = set()
    pattern = r"^(.+)\.([^\.]+)\.(?:json|pkl)$"
    for file_path in file_paths:
        base_name = os.path.basename(file_path)
        match = re.match(pattern, base_name)
        if match:
            file_prefix = match.group(1)
            # Only include if prefix is valid for this project.
            if file_prefix in valid_prefixes:
                func_name = match.group(2)
                func_names.add(func_name)
    return func_names


def get_cached_func_names(type_: str) -> List[str]:
    """
    Retrieve the function names cached with the specified type.

    :param type_: the type of cache to retrieve:
        - 'mem': memory cache only
        - 'disk': disk cache only (includes global and custom local cache
          directories)
        - 's3': S3 cache only (includes global and custom S3 buckets)
        - 'local': local caches (mem + disk)
        - 'all': all caches (mem + disk + s3)
    :return: names of functions cached with the specified type
    """
    if type_ == "mem":
        # Only include functions with non-empty cache dicts.
        out = sorted([fn for fn in _CACHE.keys() if len(_CACHE[fn]) > 0])
    elif type_ == "disk":
        all_func_names = set()
        cache_dir = get_cache_dir()
        # Collect all valid prefixes.
        valid_prefixes = _get_valid_cache_prefixes()
        # Search global cache directory.
        disk_files = glob.glob(os.path.join(cache_dir, "*.json"))
        disk_files += glob.glob(os.path.join(cache_dir, "*.pkl"))
        property_file_name = os.path.basename(get_cache_property_file())
        # Filter out property file.
        disk_files = [
            f for f in disk_files if os.path.basename(f) != property_file_name
        ]
        # Extract function names from disk files.
        all_func_names.update(
            _extract_func_names_from_cache_files(disk_files, valid_prefixes)
        )
        # Search custom cache directories.
        for func_name_tmp in _CACHE_PROPERTY:
            func_cache_dir = get_cache_property(func_name_tmp, "cache_dir")
            if func_cache_dir:
                # Function has custom cache directory.
                file_name = _get_cache_file_name(func_name_tmp)
                if os.path.exists(file_name):
                    all_func_names.add(func_name_tmp)
        out = sorted(all_func_names)
    elif type_ == "s3":
        all_func_names = set()
        # Search global S3 bucket.
        if _check_s3_configured():
            bucket = get_s3_bucket()
            prefix = get_s3_prefix()
            aws_profile = get_aws_profile()
            func_names = _list_s3_cached_func_names(bucket, prefix, aws_profile)
            all_func_names.update(set(func_names))
        # Search custom S3 buckets.
        s3_configs = set()
        for func_name_tmp in _CACHE_PROPERTY:
            func_s3_bucket = get_cache_property(func_name_tmp, "s3_bucket")
            if func_s3_bucket:
                func_s3_prefix = get_cache_property(func_name_tmp, "s3_prefix")
                if not func_s3_prefix:
                    func_s3_prefix = get_s3_prefix()
                func_aws_profile = get_cache_property(
                    func_name_tmp, "aws_profile"
                )
                if not func_aws_profile:
                    func_aws_profile = get_aws_profile()
                config_key = (
                    func_s3_bucket,
                    func_s3_prefix,
                    func_aws_profile,
                )
                s3_configs.add(config_key)
        # List files from each unique S3 bucket config.
        for bucket, prefix, aws_profile in s3_configs:
            func_names = _list_s3_cached_func_names(bucket, prefix, aws_profile)
            all_func_names.update(set(func_names))
        out = sorted(all_func_names)
    elif type_ == "local":
        mem_func_names = get_cached_func_names("mem")
        disk_func_names = get_cached_func_names("disk")
        out = sorted(set(mem_func_names + disk_func_names))
    elif type_ == "all":
        local_func_names = get_cached_func_names("local")
        s3_func_names = get_cached_func_names("s3")
        out = sorted(set(local_func_names + s3_func_names))
    else:
        raise ValueError(
            f"Invalid type '{type_}'. Valid types: 'mem', 'disk', 's3', "
            "'local', 'all'"
        )
    return out


def cache_property_to_str(func_name: str = "") -> str:
    """
    Convert cache properties to a string representation.

    :param func_name: the name of the function whose cache properties
        are to be converted
    :return: a string representation of the cache properties. E.g.,
        ```
        # func_name=slow_square
        type: json
        write_through: False
        exclude_keys: []
        ```
    """
    txt: List[str] = []
    if func_name == "":
        func_names = get_cached_func_names("all")
        for func_name_tmp in func_names:
            txt.append(cache_property_to_str(func_name_tmp))
        result = "\n".join(txt)
        return result
    #
    txt.append(f"# func_name={func_name}")
    cache_property = _CACHE_PROPERTY
    _LOG.trace("cache_property=%s", cache_property)
    if func_name in cache_property:
        for k, v in cache_property[func_name].items():
            txt.append(f"{k}: {v}")
    result = "\n".join(txt)
    return result


# #############################################################################
# Cache performance.
# #############################################################################


# Create global variable for the cache performance.
if "_CACHE_PERF" not in globals():
    _LOG.trace("Creating _CACHE_PERF")
    # func_name -> perf properties (such as tot, hits, misses).
    # Note: Values can be None when performance tracking is disabled.
    _CACHE_PERF: Dict[str, Optional[Dict[str, int]]] = {}


def enable_cache_perf(func_name: str) -> None:
    """
    Enable cache performance statistics for a given function.
    """
    _CACHE_PERF[func_name] = {"tot": 0, "hits": 0, "misses": 0}


def disable_cache_perf(func_name: str = "") -> None:
    """
    Disable cache performance statistics for a given function.

    If `func_name` is empty, disable cache performance statistics for all
    functions.
    """
    if func_name == "":
        for func_name_tmp in get_cached_func_names("all"):
            disable_cache_perf(func_name_tmp)
        return
    _CACHE_PERF[func_name] = None


def reset_cache_perf(func_name: str = "") -> None:
    """
    Reset cache performance statistics for a given function.
    """
    if func_name == "":
        for func_name_tmp in get_cached_func_names("all"):
            reset_cache_perf(func_name_tmp)
        return
    _CACHE_PERF[func_name] = {"tot": 0, "hits": 0, "misses": 0}


def get_cache_perf(func_name: str) -> Optional[Dict[str, int]]:
    """
    Get the cache performance object for a given function.
    """
    if func_name in _CACHE_PERF:
        return _CACHE_PERF[func_name]
    return None


def get_cache_perf_stats(func_name: str) -> str:
    """
    Get the cache performance statistics for a given function.

    :param func_name: The name of the function whose cache performance
        stats are to be retrieved.
    :return: A string with the cache performance statistics. E.g.,
        `slow_square: hits=2 misses=0 tot=2 hit_rate=1.00`.
    """
    perf = get_cache_perf(func_name)
    if perf is None:
        _LOG.warning("No cache performance stats for '%s'", func_name)
        return ""
    hits = perf["hits"]
    misses = perf["misses"]
    tot = perf["tot"]
    hit_rate = hits / tot if tot > 0 else 0
    txt = (
        f"{func_name}: hits={hits} misses={misses} tot={tot}"
        f" hit_rate={hit_rate:.2f}"
    )
    return txt


# #############################################################################
# Disk cache.
# #############################################################################

# Functions to save and retrieve cache from disk.
# ```
# {
#     "{\"args\": [\"You are a calculator. Given input in the format \\\"a + b\\\", return only\\nthe sum as a number.\\n\\nReturn ONLY the numeric result, nothing else.\", \"10 + 15\", \"gpt-5-nano\"], \"kwargs\": {}}": [
#         "25",
#         3.195e-05
#     ],
#     "{\"args\": [\"You are a calculator. Given input in the format \\\"a + b\\\", return only\\nthe sum as a number.\\n\\nReturn ONLY the numeric result, nothing else.\", \"2 + 3\", \"gpt-5-nano\"], \"kwargs\": {}}": [
#         "5",
#         3.195e-05
#     ]
# }
# ```


def _get_cache_file_name(func_name: str) -> str:
    """
    Get the cache file name for a given function.

    The function returns the full cache file path including the local
    directory, configured globally or per-function.

    :param func_name: the name of the function
    :return: the cache file name with appropriate extension
    """
    _LOG.trace("func_name='%s'", func_name)
    hdbg.dassert_isinstance(func_name, str)
    # Check for per-function cache dir, otherwise use global.
    func_cache_dir = get_cache_property(func_name, "cache_dir")
    if func_cache_dir:
        cache_dir = func_cache_dir
    else:
        cache_dir = get_cache_dir()
    # Check for per-function cache file prefix, otherwise use global.
    func_cache_prefix = get_cache_property(func_name, "cache_prefix")
    if func_cache_prefix:
        prefix = func_cache_prefix
    else:
        prefix = get_cache_file_prefix()
    file_name = os.path.join(cache_dir, f"{prefix}.{func_name}")
    cache_type = get_cache_property(func_name, "type")
    _LOG.trace(hprint.to_str("cache_type"))
    if cache_type == "pickle":
        file_name += ".pkl"
    elif cache_type == "json":
        file_name += ".json"
    elif cache_type is None:
        # Try to infer cache type from existing files.
        if os.path.exists(file_name + ".pkl"):
            file_name += ".pkl"
        elif os.path.exists(file_name + ".json"):
            file_name += ".json"
        else:
            # Default to json if no file exists.
            file_name += ".json"
    else:
        raise ValueError(f"Invalid cache type '{cache_type}'")
    return file_name


def _save_cache_dict_to_disk(
    func_name: str, func_cache_data: _FunctionCacheType
) -> None:
    """
    Save a cache dictionary to the disk cache.

    :param func_name: The name of the function.
    :param func_cache_data: The function cache data to save.
    """
    # Get the filename for the disk cache.
    file_name = _get_cache_file_name(func_name)
    cache_type = get_cache_property(func_name, "type")
    _LOG.trace(hprint.to_str("file_name cache_type"))
    _save_func_cache_data_to_file(file_name, cache_type, func_cache_data)


def _load_func_cache_data_from_file(
    file_name: str, cache_type: Optional[str]
) -> _FunctionCacheType:
    """
    Load the function cache data from a file.

    :param file_name: the name of the file
    :param cache_type: the type of the cache
    :return: the function cache data
    """
    # Infer cache type from file extension if not set.
    if cache_type is None:
        if file_name.endswith(".pkl"):
            cache_type = "pickle"
        else:
            cache_type = "json"
    # Load data.
    _LOG.trace("Loading from '%s'", file_name)
    hdbg.dassert_file_exists(file_name)
    if cache_type == "pickle":
        with open(file_name, "rb") as file:
            func_cache_data = pickle.load(file)
    elif cache_type == "json":
        with open(file_name, "r", encoding="utf-8") as file:
            func_cache_data = json.load(file)
    else:
        raise ValueError(f"Invalid cache type '{cache_type}'")
    return func_cache_data


# TODO(gp): Maybe private?
def get_disk_cache(func_name: str) -> _FunctionCacheType:
    """
    Retrieve the disk cache for a given function.

    :param func_name: the name of the function
    :return: cache data, if it exists
    """
    file_name = _get_cache_file_name(func_name)
    # Return empty cache if the disk cache does not exist.
    if not os.path.exists(file_name):
        _LOG.trace("No cache file on disk")
        return {}
    # Load data from existing file.
    cache_type = get_cache_property(func_name, "type")
    _LOG.trace(hprint.to_str("cache_type"))
    func_cache_data = _load_func_cache_data_from_file(file_name, cache_type)
    return func_cache_data


# #############################################################################
# S3 cache.
# #############################################################################

# Functions to save and retrieve cache from S3.


def _build_s3_cache_path_for_type(func_name: str, cache_type: str) -> str:
    """
    Build S3 cache path for a specific cache type.

    :param func_name: the name of the function
    :param cache_type: the cache type ("json" or "pickle")
    :return: the S3 path with appropriate extension
    """
    # Check for per-function S3 bucket, otherwise use global.
    bucket = get_cache_property(func_name, "s3_bucket")
    if bucket:
        # Ensure s3:// prefix.
        if not bucket.startswith("s3://"):
            bucket = f"s3://{bucket}"
    else:
        bucket = get_s3_bucket()
    if bucket is None:
        raise ValueError("S3 bucket not configured")
    # Check for per-function S3 prefix, otherwise use global.
    s3_prefix = get_cache_property(func_name, "s3_prefix")
    if not s3_prefix:
        s3_prefix = get_s3_prefix()
    # Build cache file name with explicit type.
    func_cache_prefix = get_cache_property(func_name, "cache_prefix")
    if func_cache_prefix:
        prefix = func_cache_prefix
    else:
        prefix = get_cache_file_prefix()
    # Build filename with appropriate extension.
    if cache_type == "pickle":
        base_name = f"{prefix}.{func_name}.pkl"
    elif cache_type == "json":
        base_name = f"{prefix}.{func_name}.json"
    else:
        raise ValueError(f"Invalid cache type '{cache_type}'")
    # Construct S3 path.
    if s3_prefix:
        s3_path = f"{bucket}/{s3_prefix}/{base_name}"
    else:
        s3_path = f"{bucket}/{base_name}"
    return s3_path


def _get_s3_cache_path(func_name: str) -> str:
    """
    Get the full S3 path for a cache file.

    :param func_name: the name of the function
    :return: the S3 path (e.g., "s3://bucket/prefix/cache_file.json")
    """
    # Get cache type from properties.
    cache_type = get_cache_property(func_name, "type")
    if cache_type is None:
        raise ValueError(f"Cache type not set for function '{func_name}'")
    # Build the path.
    s3_path = _build_s3_cache_path_for_type(func_name, cache_type)
    return s3_path


def _extract_func_name_from_cache_file(cache_file_name: str) -> Optional[str]:
    """
    Extract function name from cache file name.

    Cache file names follow the format: <prefix>.<func_name>.<json|pkl>

    :param cache_file_name: the cache file name (e.g.,
        "cache.my_func.json")
    :return: the function name, or None if pattern does not match
    """
    pattern = r"^(.+)\.([^\.]+)\.(?:json|pkl)$"
    match = re.match(pattern, cache_file_name)
    if match:
        return match.group(2)
    return None


def _list_s3_cached_func_names(
    bucket: str,
    prefix: Optional[str],
    aws_profile: str,
) -> List[str]:
    """
    List names of functions cached in S3 bucket.

    :param bucket: S3 bucket path (e.g., "s3://my-bucket")
    :param prefix: S3 prefix path (e.g., "cache/shared")
    :param aws_profile: AWS profile name
    :return: names of functions cached in S3 bucket
    """
    # Build S3 directory path.
    if prefix:
        s3_dir = f"{bucket}/{prefix}"
    else:
        s3_dir = bucket
    # List files in S3 directory.
    try:
        s3_files = hs3.listdir(
            s3_dir,
            pattern="*",
            only_files=True,
            use_relative_paths=False,
            aws_profile=aws_profile,
        )
    except Exception as e:
        _LOG.warning("Failed to list S3 directory '%s': %s", s3_dir, e)
        return []
    # Collect all valid cache file prefixes.
    valid_prefixes = _get_valid_cache_prefixes()
    # Extract function names from S3 file names.
    func_names = _extract_func_names_from_cache_files(s3_files, valid_prefixes)
    out = sorted(func_names)
    return out


def _check_s3_configured(func_name: Optional[str] = None) -> bool:
    """
    Check if S3 is properly configured.

    :param func_name: the name of the function to check per-function S3
        settings
    :return: True if S3 is configured, False otherwise
    """
    # Check if per-function S3 bucket is defined.
    if func_name:
        func_s3_bucket = get_cache_property(func_name, "s3_bucket")
        if func_s3_bucket:
            return True
    # Check if global bucket is defined.
    bucket = get_s3_bucket()
    if bucket is None:
        _LOG.warning("S3 bucket not configured - use set_s3_bucket()")
        return False
    return True


def _upload_cache_to_s3(func_name: str) -> None:
    """
    Upload a cache file to S3.

    :param func_name: the name of the function
    """
    if not _check_s3_configured(func_name):
        return
    # Get local file.
    local_file = _get_cache_file_name(func_name)
    if not os.path.exists(local_file):
        _LOG.debug("No local cache file to upload for '%s'", func_name)
        return
    # Get S3 path.
    s3_path = _get_s3_cache_path(func_name)
    # Check for per-function AWS profile, otherwise use global.
    func_aws_profile = get_cache_property(func_name, "aws_profile")
    if func_aws_profile:
        aws_profile = func_aws_profile
    else:
        aws_profile = get_aws_profile()
    _LOG.info("Uploading cache to %s", s3_path)
    # Read local file and write to S3.
    cache_type = get_cache_property(func_name, "type")
    # Infer cache type from file extension if not set.
    if cache_type is None:
        if local_file.endswith(".pkl"):
            cache_type = "pickle"
        elif local_file.endswith(".json"):
            cache_type = "json"
        else:
            cache_type = "json"
    if cache_type == "pickle":
        # Read pickle files as bytes and write.
        with open(local_file, "rb") as f:
            data = f.read()
        s3fs_ = hs3.get_s3fs(aws_profile)
        with s3fs_.open(s3_path, "wb") as f:
            f.write(data)
    else:
        # Read JSON files as string and write.
        data = hio.from_file(local_file)
        hs3.to_file(data, s3_path, aws_profile=aws_profile)


def _download_cache_from_s3(func_name: str) -> bool:
    """
    Download a cache file from S3.

    The function downloads the cache file from S3 to the local cache
    directory, configured globally or per-function.

    :param func_name: the name of the function
    :return: True if download is successful, False otherwise
    """
    if not _check_s3_configured(func_name):
        return False
    # Check for per-function AWS profile, otherwise use global.
    func_aws_profile = get_cache_property(func_name, "aws_profile")
    if func_aws_profile:
        aws_profile = func_aws_profile
    else:
        aws_profile = get_aws_profile()
    s3fs_ = hs3.get_s3fs(aws_profile)
    # Check cache type to determine file extension.
    cache_type = get_cache_property(func_name, "type")
    # If type is unknown, try both extensions in S3.
    if cache_type is None:
        # Try both .json and .pkl extensions.
        for ext_type in ["json", "pickle"]:
            # Build S3 path for this type.
            s3_path_candidate = _build_s3_cache_path_for_type(func_name, ext_type)
            if s3fs_.exists(s3_path_candidate):
                # Set type property and use this path.
                cache_type = ext_type
                s3_path = s3_path_candidate
                set_cache_property(func_name, "type", cache_type)
                _LOG.debug("Found S3 cache with type=%s", ext_type)
                break
        else:
            # Neither extension found in S3.
            _LOG.debug("No S3 cache found for '%s'", func_name)
            return False
    else:
        # Type is known, get paths normally.
        s3_path = _get_s3_cache_path(func_name)
        if not s3fs_.exists(s3_path):
            _LOG.debug("No S3 cache found for '%s'", func_name)
            return False
    # Get local file path.
    local_file = _get_cache_file_name(func_name)
    _LOG.info("Downloading cache from %s", s3_path)
    # Download from S3.
    cache_type = get_cache_property(func_name, "type")
    # Infer cache type from file extension if not set.
    if cache_type is None:
        if s3_path.endswith(".pkl"):
            cache_type = "pickle"
        elif s3_path.endswith(".json"):
            cache_type = "json"
        else:
            cache_type = "json"
    hio.create_enclosing_dir(local_file, incremental=True)
    if cache_type == "pickle":
        # Read pickle files as bytes and write.
        with s3fs_.open(s3_path, "rb") as f:
            data = f.read()
        with open(local_file, "wb") as f:
            f.write(data)
    else:
        # Read JSON files as string and write.
        data = hs3.from_file(s3_path, aws_profile=aws_profile)
        hio.to_file(local_file, data)
    return True


def push_cache_to_s3(func_name: str = "") -> None:
    """
    Push local cache to S3 for a given function.

    :param func_name: the name of the function. If empty, push all
        caches
    """
    # Flush memory cache to disk.
    flush_cache_to_disk(func_name)
    funcs_to_push = [func_name] if func_name else get_cached_func_names("disk")
    for func_name_tmp in funcs_to_push:
        _LOG.info("Pushing cache to S3 for '%s'", func_name_tmp)
        # Upload to S3.
        _upload_cache_to_s3(func_name_tmp)


def pull_cache_from_s3(func_name: str = "") -> None:
    """
    Pull cache from S3 to local storage for a given function.

    If no function name is provided, pulls all functions cached on S3 and
    specified in _CACHE_PROPERTY and/or found in the global S3 bucket.

    Functions cached in a custom S3 bucket using another machine cannot be
    pulled without sharing the _CACHE_PROPERTY file.
    - Without it, the pull only retrieves cache files from the global bucket
    - For more info, see `docs/tools/helpers/all.hcache_simple.explanation.md`

    :param func_name: the name of the function. If empty, pull all
        discoverable caches
    """
    if func_name != "":
        _LOG.info("Pulling cache from S3 for '%s'", func_name)
        # Download from S3.
        success = _download_cache_from_s3(func_name)
        if success:
            # Load into memory cache.
            force_cache_from_disk(func_name)
        else:
            _LOG.warning("Failed to pull cache from S3 for '%s'", func_name)
        return
    # Discover all cached functions and pull each one.
    all_funcs = get_cached_func_names("s3")
    for func_name_tmp in all_funcs:
        pull_cache_from_s3(func_name_tmp)
    _LOG.info("Pulled %d functions from S3", len(all_funcs))


def sync_cache_with_s3(func_name: str = "") -> None:
    """
    Sync cache between local and S3 (bidirectional merge).

    Downloads S3 cache, merges with local, and uploads result to S3.

    If no function name is provided, syncs all discoverable functions.

    :param func_name: the name of the function. If empty, sync all
        caches
    """
    if func_name == "":
        # Discover all cached functions and sync each one.
        all_funcs = get_cached_func_names("all")
        for func_name_tmp in all_funcs:
            sync_cache_with_s3(func_name_tmp)
        _LOG.info("Synced %d functions with S3", len(all_funcs))
        return
    _LOG.info("Syncing cache with S3 for '%s'", func_name)
    # Get current local cache (disk + memory, memory takes precedence).
    local_cache = get_disk_cache(func_name).copy()
    local_cache.update(get_mem_cache(func_name).copy())
    # Download cache from S3.
    success = _download_cache_from_s3(func_name)
    if success:
        # Load S3 cache.
        s3_cache = get_disk_cache(func_name)
        # Merge; if available, local takes precedence over what was downloaded
        # from S3.
        s3_cache.update(local_cache)
        # Only save, upload, and store if merged cache is non-empty.
        # Do not create empty cache files or entries.
        if len(s3_cache) > 0:
            # Save merged cache.
            _save_cache_dict_to_disk(func_name, s3_cache)
            # Upload back to S3.
            _upload_cache_to_s3(func_name)
            # Update memory cache.
            global _CACHE
            _CACHE[func_name] = s3_cache
    else:
        # Upload local cache to S3.
        push_cache_to_s3(func_name)


# #############################################################################
# Stats.
# #############################################################################


def cache_stats_to_str(
    func_name: Optional[str] = "",
) -> Optional["pd.DataFrame"]:  # noqa: F821
    """
    Print the cache stats.

    If `func_name` is empty or None, returns stats for all functions with local cache
    (mem + disk).

    E.g.,
    ```
    find_email:
      memory: -
      disk: 1044

    verify_email:
      memory: -
      disk: 2322
    ```
    """
    # We want to limit the dependency from pandas in the cache.
    import pandas as pd

    # Handle None as empty string.
    if func_name is None:
        func_name = ""
    if func_name == "":
        result = []
        for func_name_tmp in get_cached_func_names("local"):
            result_tmp = cache_stats_to_str(func_name_tmp)
            result.append(result_tmp)
        if result:
            result = pd.concat(result)
        else:
            result = None
        return result
    result = {}
    # Memory cache.
    if func_name in _CACHE:
        result["memory"] = len(_CACHE[func_name])
    else:
        result["memory"] = "-"
    # Disk cache.
    file_name = _get_cache_file_name(func_name)
    if os.path.exists(file_name):
        disk_cache = get_disk_cache(func_name)
        result["disk"] = len(disk_cache)
    else:
        result["disk"] = "-"
    result = pd.Series(result).to_frame().T
    result.index = [func_name]
    return result


def force_cache_from_disk(func_name: Optional[str] = "") -> None:
    """
    Force loading the cache from disk and update the memory cache.

    :param func_name: the name of the function. If empty or None, apply
        to all discoverable functions with cache on local disk
    """
    # Handle None as empty string.
    if func_name is None:
        func_name = ""
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cached_func_names("disk"):
            force_cache_from_disk(func_name_tmp)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    _LOG.trace("func_name='%s'", func_name)
    # Get disk cache.
    disk_cache = get_disk_cache(func_name)
    _LOG.trace("disk_cache=%s", len(disk_cache))
    # Update the memory cache only if non-empty.
    # Do not store empty dicts to avoid phantom cached functions.
    if len(disk_cache) > 0:
        global _CACHE
        _CACHE[func_name] = disk_cache


def get_mem_cache(func_name: str) -> _FunctionCacheType:
    """
    Retrieve the memory cache for a given function.

    :param func_name: the name of the function
    :return: memory cache data
    """
    mem_cache = _CACHE.get(func_name, {})
    return mem_cache


def flush_cache_to_disk(func_name: Optional[str] = "") -> None:
    """
    Flush the memory cache to disk and update the memory cache.

    This merges memory cache with disk cache (memory takes precedence)
    and saves to disk, then updates memory with the merged result.

    :param func_name: the name of the function. If empty or None, apply
        to all functions with memory cache
    """
    # Handle None as empty string.
    if func_name is None:
        func_name = ""
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cached_func_names("mem"):
            flush_cache_to_disk(func_name_tmp)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    _LOG.trace("func_name='%s'", func_name)
    # Get memory cache.
    mem_cache = get_mem_cache(func_name)
    _LOG.trace("mem_cache=%s", len(mem_cache))
    # Get disk cache.
    disk_cache = get_disk_cache(func_name)
    _LOG.trace("disk_cache=%s", len(disk_cache))
    # Merge disk cache with memory cache.
    disk_cache.update(mem_cache)
    # Save merged cache to disk only if non-empty.
    # Do not create empty cache files.
    if len(disk_cache) > 0:
        _save_cache_dict_to_disk(func_name, disk_cache)
        # Update the memory cache.
        global _CACHE
        _CACHE[func_name] = disk_cache


def get_cache(func_name: str) -> _FunctionCacheType:
    """
    Retrieve the cache for a given function name.

    This function implements a three-tier cache lookup:
    1. Memory cache (fastest)
    2. Disk cache (persistent)
    3. S3 cache (shared, if configured)

    If S3 is configured and cache is not in memory/disk, attempts to pull
    from S3 automatically (once per function per session).

    :param func_name: the name of the function whose cache is to be
        retrieved
    :return: cache data
    """
    global _CACHE
    global _S3_AUTO_PULL_ATTEMPTED
    if func_name in _CACHE:
        _LOG.trace("Loading mem cache for '%s'", func_name)
        cache = get_mem_cache(func_name)
        # Return cache from memory.
        if cache:
            return cache
    # Try loading cache from local disk.
    _LOG.trace("Loading disk cache for '%s'", func_name)
    func_cache_data = get_disk_cache(func_name)
    if func_cache_data:
        _CACHE[func_name] = func_cache_data
        return func_cache_data
    # Try S3 auto-pull if configured.
    if func_name not in _S3_AUTO_PULL_ATTEMPTED:
        _S3_AUTO_PULL_ATTEMPTED.add(func_name)
        if _check_s3_configured(func_name):
            _LOG.trace(
                "Cache not in memory/disk for '%s', attempting S3 pull",
                func_name,
            )
            success = _download_cache_from_s3(func_name)
            if success:
                _LOG.trace("S3 pull succeeded for '%s'", func_name)
                # Reload from disk after S3 pull.
                func_cache_data = get_disk_cache(func_name)
                # Store in memory only if non-empty.
                if len(func_cache_data) > 0:
                    _CACHE[func_name] = func_cache_data
                return func_cache_data
    # Return empty dict without storing it in _CACHE.
    # Only store when we have actual cached data.
    empty_cache: _FunctionCacheType = {}
    return empty_cache


# #############################################################################
# Reset cache.
# #############################################################################

# Functions to reset cache (both memory and disk).


def reset_mem_cache(func_name: Optional[str] = "") -> None:
    """
    Reset the memory cache for a given function.

    :param func_name: The name of the function. If empty or None, reset
        all memory caches (for functions currently in memory).
    """
    _LOG.trace(hprint.func_signature_to_str())
    # Handle None as empty string.
    if func_name is None:
        func_name = ""
    hdbg.dassert_isinstance(func_name, str)
    if func_name == "":
        _LOG.trace("Before resetting memory cache:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cached_func_names("mem"):
            reset_mem_cache(func_name=func_name_tmp)
        _LOG.trace("After:\n%s", cache_stats_to_str())
        return
    # Delete if present.
    if func_name in _CACHE:
        del _CACHE[func_name]


def reset_disk_cache(
    func_name: Optional[str] = "", interactive: bool = True
) -> None:
    """
    Reset the disk cache for a given function name.

    If `func_name` is empty or None, reset all discoverable disk cache files:
    - All files in global cache directory matching global prefix
    - All files for functions with custom cache_dir/cache_prefix tracked in
      _CACHE_PROPERTY

    Note: This cannot discover orphaned cache files in custom directories
    for functions not tracked in _CACHE_PROPERTY.

    :param func_name: The name of the function whose disk cache is to
        be reset. If empty or None, reset all discoverable disk cache files.
    :param interactive: If True, prompt the user for confirmation before
        resetting the disk cache.
    """
    _LOG.trace(hprint.func_signature_to_str())
    # Handle None as empty string.
    if func_name is None:
        func_name = ""
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_isinstance(interactive, bool)
    if interactive:
        hsystem.query_yes_no(
            f"Are you sure you want to reset the disk cache for func_name={func_name}?"
        )
    if func_name == "":
        _LOG.trace("Before resetting disk cache:\n%s", cache_stats_to_str())
        _LOG.warning("Resetting disk cache")
        # Reset files in global cache directory.
        prefix = get_cache_file_prefix()
        cache_files = glob.glob(os.path.join(get_cache_dir(), f"{prefix}.*"))
        for file_name in cache_files:
            if os.path.isfile(file_name):
                os.remove(file_name)
        # Reset files in per-function cache directories.
        cache_property = _CACHE_PROPERTY
        for func_name_tmp in cache_property:
            func_props = cache_property[func_name_tmp]
            # Check if function has per-function cache dir or prefix.
            if "cache_dir" in func_props or "cache_prefix" in func_props:
                # Get cache file for this function.
                func_cache_file = _get_cache_file_name(func_name_tmp)
                if os.path.exists(func_cache_file):
                    _LOG.debug(
                        "Removing per-function cache file '%s'", func_cache_file
                    )
                    os.remove(func_cache_file)
        _LOG.trace("After:\n%s", cache_stats_to_str())
        return
    #
    file_name = _get_cache_file_name(func_name)
    if os.path.exists(file_name):
        _LOG.warning("Removing cache file '%s'", file_name)
        os.remove(file_name)


def reset_cache(func_name: Optional[str] = "", interactive: bool = True) -> None:
    """
    Reset both memory and disk cache for a given function.

    If `func_name` is empty or None, reset all discoverable caches:
    - All memory caches (for functions currently in memory)
    - All disk cache files in global cache directory matching global prefix
    - All disk cache files for functions with custom cache_dir/cache_prefix
      tracked in _CACHE_PROPERTY

    Note: This cannot discover orphaned cache files in custom directories
    for functions not tracked in _CACHE_PROPERTY.

    :param func_name: The name of the function. If empty or None, reset all
        discoverable caches.
    :param interactive: If True, prompt the user for confirmation before
        resetting the disk cache.
    """
    _LOG.trace(hprint.func_signature_to_str())
    # Handle None as empty string.
    if func_name is None:
        func_name = ""
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_isinstance(interactive, bool)
    reset_mem_cache(func_name=func_name)
    reset_disk_cache(func_name=func_name, interactive=interactive)


# #############################################################################
# Mock / unit test cache.
# #############################################################################


def _get_cache_key(args: Any, kwargs: Any) -> str:
    cache_key = json.dumps(
        {"args": args, "kwargs": kwargs},
        sort_keys=True,
        default=str,
    )
    _LOG.trace("cache_key=%s", cache_key)
    return cache_key


def mock_cache(func_name: str, cache_key: str, value: Any) -> None:
    """
    Mock the function cache for a given function and cache key.

    :param func_name: The name of the function.
    :param cache_key: The cache key.
    :param value: The value to store in the cache.
    """
    # We should not use the main cache directory for mocking.
    hdbg.dassert_ne(
        get_cache_dir(),
        get_main_cache_dir(),
        msg="Do not use the main cache directory for mocking",
    )
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_ne(func_name, "", "Function name is empty")
    hdbg.dassert_isinstance(cache_key, str)
    hdbg.dassert_ne(cache_key, "", "Cache key is empty")
    # Get the function cache.
    func_cache_data = get_cache(func_name)
    # Update the function cache.
    func_cache_data[cache_key] = value
    # Ensure the cache dict is stored in memory.
    global _CACHE
    _CACHE[func_name] = func_cache_data


def mock_cache_from_args_kwargs(
    func_name: str, args: Any, kwargs: Any, value: Any
) -> None:
    """
    Mock the function cache for a given function and args/kwargs.

    E.g., when testing a cached expensive function (e.g., an LLM call or
    downloading data) we can mock the cache to return a fixed value,
    instead of calling the function.

    :param func_name: The name of the function.
    :param args: The arguments for the function.
    :param kwargs: The keyword arguments for the function.
    :param value: The value to store in the cache.
    """
    hdbg.dassert_isinstance(args, tuple, "args is not a tuple: %s", args)
    hdbg.dassert_isinstance(kwargs, dict, "kwargs is not a dict: %s", kwargs)
    # Get the cache key.
    cache_key = _get_cache_key(args, kwargs)
    # Mock the cache.
    mock_cache(func_name, cache_key, value)


def mock_cache_from_disk(
    func_name: str, func_cache_data: _FunctionCacheType
) -> None:
    """
    Mock the function cache from disk data.

    :param func_name: The name of the function.
    :param cache_data: The cache data to mock.
    """
    hdbg.dassert_isinstance(func_name, str)
    sanity_check_function_cache(func_cache_data, assert_on_empty=True)
    for cache_key, cached_value in func_cache_data.items():
        mock_cache(func_name, cache_key, cached_value)


# #############################################################################
# Decorator
# #############################################################################

# - Decorated functions accept special keyword arguments to control caching
#   behavior:
#   - `force_refresh=True`: Bypass cache and recompute the result
#   - `abort_on_cache_miss=True`: Raise an exception if cache miss occurs
#   - `report_on_cache_miss=True`: Return "_cache_miss_" instead of computing on
#     cache miss
#   - `cache_mode`: Alternative way to control caching with predefined modes:
#     - `"REFRESH_CACHE"`: Force cache refresh (same as `force_refresh=True`)
#     - `"HIT_CACHE_OR_ABORT"`: Abort on cache miss (same as
#       `abort_on_cache_miss=True`)
#     - `"DISABLE_CACHE"`: Completely disable caching for this call


# TODO(gp): Not sure that cache_mode is worth having the duplication.
def simple_cache(
    *,
    cache_type: str = "json",
    write_through: bool = True,
    exclude_keys: Optional[List[str]] = None,
    cache_dir: Optional[str] = None,
    cache_prefix: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    s3_prefix: Optional[str] = None,
    aws_profile: str = "ck",
    auto_sync_s3: bool = False,
) -> Callable[..., Any]:
    """
    Decorate a function to cache its results.

    The cache is stored in memory and on disk, with optional S3 support.

    :param cache_type: type of cache to use ('json' or 'pickle')
    :param write_through: if True, the cache is written to disk after
        each access
    :param exclude_keys: keys to exclude from the cache key
    :param cache_dir: directory for this function's cache files. If
        None, uses global cache directory
    :param cache_prefix: prefix for this function's cache files. If
        None, uses global cache prefix
    :param s3_bucket: S3 bucket for this function's cache (e.g.,
        "s3://my-bucket"). If specified, enables S3 cache syncing for
        this function
    :param s3_prefix: S3 prefix path for this function's cache
    :param aws_profile: AWS profile for S3 access
    :param auto_sync_s3: if True, automatically sync to S3 after each
        cache update
    :return: a decorator that can be applied to a function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorate a function to cache its results.
        """
        hdbg.dassert_in(cache_type, ("json", "pickle"))
        func_name = getattr(func, "__name__", "unknown_function")
        if func_name.endswith("_intrinsic"):
            func_name = func_name[: -len("_intrinsic")]
        # Store function-specific properties.
        # Only set properties if not already set by runtime calls.
        # This allows runtime overrides to persist across module reloads
        # within the same session (e.g., notebook autoreload).
        existing_type = get_cache_property(func_name, "type")
        if not existing_type:
            set_cache_property(func_name, "type", cache_type)
        # Store per-function cache settings only if not already set.
        if (
            cache_dir is not None
            and get_cache_property(func_name, "cache_dir") is None
        ):
            set_cache_property(func_name, "cache_dir", cache_dir)
        if (
            cache_prefix is not None
            and get_cache_property(func_name, "cache_prefix") is None
        ):
            set_cache_property(func_name, "cache_prefix", cache_prefix)
        # Store per-function S3 settings only if not already set.
        if (
            s3_bucket is not None
            and get_cache_property(func_name, "s3_bucket") is None
        ):
            set_cache_property(func_name, "s3_bucket", s3_bucket)
        if (
            s3_prefix is not None
            and get_cache_property(func_name, "s3_prefix") is None
        ):
            set_cache_property(func_name, "s3_prefix", s3_prefix)
        if (
            aws_profile is not None
            and get_cache_property(func_name, "aws_profile") is None
        ):
            set_cache_property(func_name, "aws_profile", aws_profile)
        # Only set auto_sync_s3 if not already set.
        # Runtime value takes precedence over decorator argument.
        if get_cache_property(func_name, "auto_sync_s3") is None:
            set_cache_property(func_name, "auto_sync_s3", auto_sync_s3)
        # Only set write_through if not already set.
        if get_cache_property(func_name, "write_through") is None:
            set_cache_property(func_name, "write_through", write_through)
        # Only set exclude_keys if not already set.
        if get_cache_property(func_name, "exclude_keys") is None:
            # Handle mutable default argument.
            exclude_keys_list: List[str] = (
                exclude_keys if exclude_keys is not None else []
            )
            set_cache_property(func_name, "exclude_keys", exclude_keys_list)

        @functools.wraps(func)
        def wrapper(
            *args: Any,
            force_refresh: bool = False,
            abort_on_cache_miss: bool = False,
            report_on_cache_miss: bool = False,
            **kwargs: Any,
        ) -> Any:
            """
            Cache the results of the decorated function.

            :param args: Positional arguments for the function.
            :param force_refresh: If True, the cache is refreshed
                  regardless of whether the key exists in the cache.
            :param abort_on_cache_miss: If True, an exception is raised
                  if the key is not found in the cache.
            :param report_on_cache_miss: If True, a message is logged if
                  the key is not found in the cache, and the function
                  returns "_cache_miss_" instead of accessing the real
                  value.
            :param kwargs: Keyword arguments for the function.
            :return: The cached value or the result of the function.
            """
            # Get the function name.
            func_name = getattr(func, "__name__", "unknown_function")
            if func_name.endswith("_intrinsic"):
                func_name = func_name[: -len("_intrinsic")]
            # Get the cache.
            cache = get_cache(func_name)
            # Remove keys that should not be part of the cache key.
            # Read exclude_keys from property at runtime.
            exclude_keys_prop = get_cache_property(func_name, "exclude_keys")
            if exclude_keys_prop is None:
                exclude_keys_prop = []
            # Also exclude cache_mode since it's a control parameter.
            excluded_keys = set(exclude_keys_prop) | {"cache_mode"}
            kwargs_for_cache_key = {
                k: v for k, v in kwargs.items() if k not in excluded_keys
            }
            # Prepare kwargs for the actual function call excluding control
            # parameters.
            control_params = {
                "cache_mode",
                "force_refresh",
                "abort_on_cache_miss",
                "report_on_cache_miss",
            }
            kwargs_for_func = {
                k: v for k, v in kwargs.items() if k not in control_params
            }
            # `cache_mode` is a special keyword argument to control caching
            # behavior.
            if "cache_mode" in kwargs:
                cache_mode = kwargs.get("cache_mode")
                _LOG.trace("cache_mode=%s", cache_mode)
                if cache_mode == "REFRESH_CACHE":
                    # Force to refresh the cache.
                    _LOG.trace("Forcing cache refresh")
                    force_refresh = True
                if cache_mode == "HIT_CACHE_OR_ABORT":
                    # Abort if the cache is not hit.
                    _LOG.trace("Abort on cache miss")
                    abort_on_cache_miss = True
                if cache_mode == "DISABLE_CACHE":
                    # Disable the cache.
                    _LOG.trace("Disabling cache")
                    value = func(*args, **kwargs_for_func)
                    return value
            # Get the key.
            cache_key = _get_cache_key(args, kwargs_for_cache_key)
            # Update the performance stats.
            cache_perf = get_cache_perf(func_name)
            _LOG.trace("cache_perf is None=%s", cache_perf is None)
            if cache_perf:
                hdbg.dassert_in("tot", cache_perf)
                cache_perf["tot"] += 1
            # Handle a forced refresh.
            force_refresh = force_refresh or get_cache_property(
                func_name, "force_refresh"
            )
            _LOG.trace("force_refresh=%s", force_refresh)
            if cache_key in cache and not force_refresh:
                _LOG.trace("Cache hit for key='%s'", cache_key)
                # Highlight that a function was cached with a _LOG.warning,
                # even if a cache hit is not surprising.
                _LOG.warning("Cache hit for %s", func_name)
                # Update the performance stats.
                if cache_perf:
                    cache_perf["hits"] += 1
                # Retrieve the value from the cache.
                value = cache[cache_key]
            else:
                _LOG.trace("Cache miss for key='%s'", cache_key)
                # Update the performance stats.
                if cache_perf:
                    cache_perf["misses"] += 1
                # Abort on cache miss.
                abort_on_cache_miss = abort_on_cache_miss or get_cache_property(
                    func_name, "abort_on_cache_miss"
                )
                _LOG.trace("abort_on_cache_miss=%s", abort_on_cache_miss)
                if abort_on_cache_miss:
                    raise ValueError(f"Cache miss for key='{cache_key}'")
                # Report on cache miss.
                report_on_cache_miss = report_on_cache_miss or get_cache_property(
                    func_name, "report_on_cache_miss"
                )
                _LOG.trace("report_on_cache_miss=%s", report_on_cache_miss)
                if report_on_cache_miss:
                    _LOG.trace("Cache miss for key='%s'", cache_key)
                    return "_cache_miss_"
                # Access the intrinsic function.
                value = func(*args, **kwargs_for_func)
                # Update cache.
                cache[cache_key] = value
                # Ensure the cache dict is stored in memory.
                global _CACHE
                _CACHE[func_name] = cache
                _LOG.trace(
                    "Updating cache with key='%s' value='%s'", cache_key, value
                )
                # Read write_through from property at runtime.
                write_through_prop = get_cache_property(
                    func_name, "write_through"
                )
                if write_through_prop is None:
                    write_through_prop = write_through
                if write_through_prop:
                    _LOG.trace("Writing through to disk")
                    flush_cache_to_disk(func_name)
                    # Check if auto-sync to S3 is enabled.
                    auto_sync = get_cache_property(func_name, "auto_sync_s3")
                    if auto_sync:
                        _LOG.debug("Auto-syncing cache to S3 for '%s'", func_name)
                        _upload_cache_to_s3(func_name)
            return value

        return wrapper

    return decorator
