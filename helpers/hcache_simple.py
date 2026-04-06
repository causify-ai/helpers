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
from typing import Any, Callable, Dict, List, Optional, Union, cast

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
# - By passing keyword arguments to the decorated function.
#   - E.g., `type_`
# - By using a special keyword argument (`force_refresh`, `abort_on_cache_miss`,
#   `report_on_cache_miss`) cache_mode`) when calling the decorated function.
# - By setting cache properties
#   - E.g., set_cache_property("func_name", "force_refresh", True)

# - There are two types of properties:
#   - `User Properties`: Configurable by the user to alter caching behavior.
#      E.g.,
#     - `abort_on_cache_miss`: Whether to raise an error if a cache miss occurs
#     - `report_on_cache_miss`: Whether to return a special value ("_cache_miss_")
#       on a cache miss
#     - `enable_perf`: Whether to enable performance statistics tracking (hits,
#       misses, total calls)
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
    _AWS_PROFILE: Optional[str] = "ck"

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


def get_aws_profile() -> Optional[str]:
    """
    Get the AWS profile for S3 access.

    :return: AWS profile name or None if not configured
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


def _get_initial_cache_property() -> _CacheType:
    """
    Get the initial cache property from disk or create an empty one.

    :return: A dictionary containing cache properties.
    """
    file_name_ = get_cache_property_file()
    if os.path.exists(file_name_):
        _LOG.trace("Loading from %s", file_name_)
        # TODO(gp): Use _load_data_from_file, if possible.
        with open(file_name_, "rb") as file:
            val = pickle.load(file)
    else:
        # func_name -> key -> value properties.
        val = {}
    val = cast(_CacheType, val)
    return val


# Create global variables for the cache properties.
if "_CACHE_PROPERTY" not in globals():
    _LOG.trace("Creating _CACHE_PROPERTY")
    _CACHE_PROPERTY = _get_initial_cache_property()


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
        # Enable performance stats (e.g., miss, hit, tot for the cache).
        "enable_perf",
        # Force to refresh the value.
        "force_refresh",
        # TODO(gp): "force_refresh_once"
        # json or pickle cache type.
        "type",
        # cache mode.
        "mode",
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

    :param func_name: The name of the function whose cache property is
        to be set.
    :param property_name: The name of the property to set.
    :param val: The value to set for the property.
    """
    _LOG.trace(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_isinstance(property_name, str)
    _check_valid_cache_property(property_name)
    # Assign value.
    cache_property = _CACHE_PROPERTY
    if func_name not in cache_property:
        cache_property[func_name] = {}
    dict_ = cache_property[func_name]
    dict_[property_name] = val
    # Update values on the disk.
    file_name = get_cache_property_file()
    _LOG.trace("Updating %s", file_name)
    # Make sure the dict is well-formed.
    for func_name_tmp in cache_property:
        hdbg.dassert_isinstance(func_name_tmp, str)
        _LOG.trace(
            "func_name_tmp='%s' -> %s",
            func_name_tmp,
            cache_property[func_name_tmp],
        )
    hio.create_enclosing_dir(file_name, incremental=True)
    _save_func_cache_data_to_file(file_name, "pickle", cache_property)


def get_cache_property(func_name: str, property_name: str) -> Union[bool, Any]:
    """
    Get the value of a property for the cache of a given function name.
    """
    _LOG.trace(hprint.func_signature_to_str())
    _check_valid_cache_property(property_name)
    # Read data.
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
    Reset the cache property for the given type.
    """
    file_name = get_cache_property_file()
    _LOG.warning("Resetting %s", file_name)
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
    # Update values on the disk.
    _LOG.trace("Updating %s", file_name)
    hio.create_enclosing_dir(file_name, incremental=True)
    _save_func_cache_data_to_file(file_name, "pickle", cache_property)


# #############################################################################
# Get cache.
# #############################################################################

# Functions to retrieve cache (both memory and disk).


def get_cache_func_names(type_: str) -> List[str]:
    """
    Retrieve the function names cached with the specified type.

    For 'disk' type, this function discovers caches in:
    - Global cache directory with global prefix
    - Custom cache locations configured via per-function decorator options

    :param type_: the type of cache to retrieve ('all', 'mem', or 'disk')
    :return: names of functions cached with the specified type
    """
    if type_ == "all":
        mem_func_names = get_cache_func_names("mem")
        disk_func_names = get_cache_func_names("disk")
        val = sorted(set(mem_func_names + disk_func_names))
    elif type_ == "mem":
        mem_func_names = sorted(list(_CACHE.keys()))
        val = mem_func_names
    elif type_ == "disk":
        all_func_names = set()
        # Search global cache directory.
        prefix = get_cache_file_prefix()
        cache_dir = get_cache_dir()
        disk_func_names = glob.glob(os.path.join(cache_dir, f"{prefix}.*"))
        disk_func_names = [os.path.basename(cache) for cache in disk_func_names]
        # Exclude the cache property file.
        property_file_name = os.path.basename(get_cache_property_file())
        disk_func_names = [
            cache for cache in disk_func_names if cache != property_file_name
        ]
        escaped_prefix = re.escape(prefix)
        pattern = rf"{escaped_prefix}\.(.*)\.(json|pkl)"
        disk_func_names = [
            re.sub(pattern, r"\1", cache) for cache in disk_func_names
        ]
        all_func_names.update(disk_func_names)
        # Search custom cache locations from _CACHE_PROPERTY.
        cache_property = _CACHE_PROPERTY
        for func_name_tmp in cache_property:
            # Check if this function has custom cache location.
            func_cache_dir = cache_property[func_name_tmp].get("cache_dir")
            func_cache_prefix = cache_property[func_name_tmp].get("cache_prefix")
            # If it has custom location, search there.
            if func_cache_dir or func_cache_prefix:
                # Check if cache file exists for this function.
                file_name = _get_cache_file_name(func_name_tmp)
                if os.path.exists(file_name):
                    all_func_names.add(func_name_tmp)
        val = sorted(list(all_func_names))
    else:
        raise ValueError(f"Invalid type '{type_}'")
    return val


def cache_property_to_str(func_name: str = "") -> str:
    """
    Convert cache properties to a string representation.

    :param func_name: The name of the function whose cache properties
        are to be converted.
    :return: A string representation of the cache properties. E.g.,
        ```
        # func_name=slow_square
        type: json
        write_through: False
        exclude_keys: []
        ```
    """
    txt: List[str] = []
    if func_name == "":
        func_names = get_cache_func_names("all")
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
    _CACHE_PERF: Dict[str, Dict[str, int]] = {}


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
        for func_name_tmp in get_cache_func_names("all"):
            disable_cache_perf(func_name_tmp)
        return
    _CACHE_PERF[func_name] = None


def reset_cache_perf(func_name: str = "") -> None:
    """
    Reset cache performance statistics for a given function.
    """
    if func_name == "":
        for func_name_tmp in get_cache_func_names("all"):
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


def _get_s3_cache_path(func_name: str) -> str:
    """
    Get the full S3 path for a cache file.

    :param func_name: the name of the function
    :return: the S3 path (e.g., "s3://bucket/prefix/cache_file.json")
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
    base_name = os.path.basename(_get_cache_file_name(func_name))
    if s3_prefix:
        s3_path = f"{bucket}/{s3_prefix}/{base_name}"
    else:
        s3_path = f"{bucket}/{base_name}"
    return s3_path


def _check_s3_configured(func_name: Optional[str] = None) -> bool:
    """
    Check if S3 is properly configured.

    :param func_name: the name of the function to check per-function S3
        settings
    :return: True if S3 is configured, False otherwise
    """
    # Check whether per-function S3 bucket is defined.
    if func_name:
        func_s3_bucket = get_cache_property(func_name, "s3_bucket")
        if func_s3_bucket:
            return True
    # Check global bucket.
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
    :return: True if download successful, False otherwise
    """
    if not _check_s3_configured(func_name):
        return False
    # Get local file and S3 path.
    local_file = _get_cache_file_name(func_name)
    s3_path = _get_s3_cache_path(func_name)
    # Check for per-function aws_profile, otherwise use global.
    func_aws_profile = get_cache_property(func_name, "aws_profile")
    if func_aws_profile:
        aws_profile = func_aws_profile
    else:
        aws_profile = get_aws_profile()
    _LOG.info("Downloading cache from %s", s3_path)
    # Check if S3 file exists.
    s3fs_ = hs3.get_s3fs(aws_profile)
    if not s3fs_.exists(s3_path):
        _LOG.debug("No S3 cache found for '%s'", func_name)
        return False
    # Download from S3.
    cache_type = get_cache_property(func_name, "type")
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
    if func_name == "":
        for func_name_tmp in get_cache_func_names("disk"):
            push_cache_to_s3(func_name_tmp)
        return
    _LOG.info("Pushing cache to S3 for '%s'", func_name)
    # Flush memory cache to disk.
    flush_cache_to_disk(func_name)
    # Upload to S3.
    _upload_cache_to_s3(func_name)


def pull_cache_from_s3(func_name: str = "") -> None:
    """
    Pull cache from S3 to local storage for a given function.

    If no function name is provided, pulls caches using a two-phase approach:
    - Phase 1: Pulls all functions in local _CACHE_PROPERTY (respects
      per-function S3 config)
    - Phase 2: Lists global S3 bucket and pulls any functions found there

    Functions cached with custom s3_bucket on another
    machine are UNPULLABLE without sharing _CACHE_PROPERTY file.
    - The custom bucket location is stored only in the originating machine's
      _CACHE_PROPERTY
    - Without it, the pull attempts to use global bucket and fails
    - Workaround: Share _CACHE_PROPERTY file or use global S3 bucket for team
      collaboration

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
            return
    pulled_funcs = set()
    # Pull caches for all functions in _CACHE_PROPERTY.
    cache_property = _CACHE_PROPERTY
    for func_name_tmp in cache_property:
        pull_cache_from_s3(func_name_tmp)
        pulled_funcs.add(func_name_tmp)
    # List files from global S3 bucket for functions not in _CACHE_PROPERTY.
    if _check_s3_configured():
        bucket = get_s3_bucket()
        prefix = get_s3_prefix()
        aws_profile = get_aws_profile()
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
            s3_files = []
        # Extract function names from S3 file names.
        for s3_file in s3_files:
            base_name = os.path.basename(s3_file)
            # Extract function name from cache file name with format
            # <any_prefix>.func_name.json/pkl.
            pattern = r"^(.+)\.([^\.]+)\.(?:json|pkl)$"
            match = re.match(pattern, base_name)
            if match:
                func_name_tmp = match.group(2)
                # Pull cache if not already pulled.
                if func_name_tmp not in pulled_funcs:
                    pull_cache_from_s3(func_name_tmp)
                    pulled_funcs.add(func_name_tmp)


def sync_cache_with_s3(func_name: str = "") -> None:
    """
    Sync cache between local and S3 (bidirectional merge).

    Downloads S3 cache, merges with local, and uploads result.

    :param func_name: the name of the function. If empty, sync all
        caches
    """
    if func_name == "":
        for func_name_tmp in get_cache_func_names("all"):
            sync_cache_with_s3(func_name_tmp)
        return
    _LOG.info("Syncing cache with S3 for '%s'", func_name)
    # Get current local cache.
    local_cache = get_mem_cache(func_name).copy()
    local_disk_cache = get_disk_cache(func_name).copy()
    local_cache.update(local_disk_cache)
    # Download from S3.
    success = _download_cache_from_s3(func_name)
    if success:
        # Load S3 cache.
        s3_cache = get_disk_cache(func_name)
        # Merge: local takes precedence.
        s3_cache.update(local_cache)
        # Save merged cache.
        _save_cache_dict_to_disk(func_name, s3_cache)
        # Upload back to S3.
        _upload_cache_to_s3(func_name)
        # Update memory cache.
        global _CACHE
        _CACHE[func_name] = s3_cache
    else:
        # No S3 cache, just upload local.
        push_cache_to_s3(func_name)


# #############################################################################
# Stats.
# #############################################################################


def cache_stats_to_str(
    func_name: str = "",
) -> Optional["pd.DataFrame"]:  # noqa: F821
    """
    Print the cache stats for a function or for all functions.

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

    if func_name == "":
        result = []
        for func_name_tmp in get_cache_func_names("all"):
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


def force_cache_from_disk(func_name: str = "") -> None:
    """
    Force loading the cache from disk and update the memory cache.

    :param func_name: the name of the function. If empty, apply to all
        cached functions
    """
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cache_func_names("all"):
            force_cache_from_disk(func_name_tmp)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    _LOG.trace("func_name='%s'", func_name)
    # Get disk cache.
    disk_cache = get_disk_cache(func_name)
    _LOG.trace("disk_cache=%s", len(disk_cache))
    # Update the memory cache.
    global _CACHE
    _CACHE[func_name] = disk_cache


def get_mem_cache(func_name: str) -> _CacheType:
    """
    Retrieve the memory cache for a given function.

    :param func_name: the name of the function
    :return: memory cache data
    """
    mem_cache = _CACHE.get(func_name, {})
    return mem_cache


def flush_cache_to_disk(func_name: str = "") -> None:
    """
    Flush the memory cache to disk and update the memory cache.

    :param func_name: the name of the function. If empty, apply to all
        cached functions
    """
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cache_func_names("all"):
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
    # Save merged cache to disk.
    _save_cache_dict_to_disk(func_name, disk_cache)
    # Update the memory cache.
    global _CACHE
    _CACHE[func_name] = disk_cache


def get_cache(func_name: str) -> _CacheType:
    """
    Retrieve the cache for a given function name.

    This function implements a three-tier cache lookup:
    1. Memory cache (fastest)
    2. Disk cache (persistent)
    3. S3 cache (shared, if configured)

    If S3 is configured and cache is not in memory/disk, attempts to pull
    from S3 automatically (once per function per session).

    :param func_name: The name of the function whose cache is to be
        retrieved.
    :return: A dictionary containing the cache data.
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
                _CACHE[func_name] = func_cache_data
                return func_cache_data
    # Return empty since no cache is available.
    empty_cache: _CacheType = {}
    _CACHE[func_name] = empty_cache
    return empty_cache


# #############################################################################
# Reset cache.
# #############################################################################

# Functions to reset cache (both memory and disk).


def reset_mem_cache(func_name: str = "") -> None:
    """
    Reset the memory cache for a given function.

    :param func_name: The name of the function. If empty, reset all
        memory caches.
    """
    _LOG.trace(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(func_name, str)
    if func_name == "":
        _LOG.trace("Before resetting memory cache:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cache_func_names("all"):
            reset_mem_cache(func_name=func_name_tmp)
        _LOG.trace("After:\n%s", cache_stats_to_str())
        return
    _CACHE[func_name] = {}
    del _CACHE[func_name]


def reset_disk_cache(func_name: str = "", interactive: bool = True) -> None:
    """
    Reset the disk cache for a given function name.

    If `func_name` is empty, reset all disk cache files.
    :param func_name: The name of the function whose disk cache is to
        be reset. If empty, reset all disk cache files.
    :param interactive: If True, prompt the user for confirmation before
        resetting the disk cache.
    """
    _LOG.trace(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_isinstance(interactive, bool)
    if interactive:
        hsystem.query_yes_no(
            f"Are you sure you want to reset the disk cache for func_name={func_name}?"
        )
    if func_name == "":
        _LOG.trace("Before resetting disk cache:\n%s", cache_stats_to_str())
        prefix = get_cache_file_prefix()
        cache_files = glob.glob(os.path.join(get_cache_dir(), f"{prefix}.*"))
        _LOG.warning("Resetting disk cache")
        for file_name in cache_files:
            if os.path.isfile(file_name):
                os.remove(file_name)
        _LOG.trace("After:\n%s", cache_stats_to_str())
        return
    #
    file_name = _get_cache_file_name(func_name)
    if os.path.exists(file_name):
        _LOG.warning("Removing cache file '%s'", file_name)
        os.remove(file_name)


def reset_cache(func_name: str = "", interactive: bool = True) -> None:
    """
    Reset both memory and disk cache for a given function.

    :param func_name: The name of the function. If empty, reset all
        caches.
    :param interactive: If True, prompt the user for confirmation before
        resetting the disk cache.
    """
    _LOG.trace(hprint.func_signature_to_str())
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
    aws_profile: Optional[str] = None,
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
        existing_type = get_cache_property(func_name, "type")
        if not existing_type:
            set_cache_property(func_name, "type", cache_type)
        # Store per-function cache settings.
        if cache_dir is not None:
            set_cache_property(func_name, "cache_dir", cache_dir)
        if cache_prefix is not None:
            set_cache_property(func_name, "cache_prefix", cache_prefix)
        # Store per-function S3 settings.
        if s3_bucket is not None:
            set_cache_property(func_name, "s3_bucket", s3_bucket)
        if s3_prefix is not None:
            set_cache_property(func_name, "s3_prefix", s3_prefix)
        if aws_profile is not None:
            set_cache_property(func_name, "aws_profile", aws_profile)
        if auto_sync_s3:
            set_cache_property(func_name, "auto_sync_s3", auto_sync_s3)
        # Handle mutable default argument.
        exclude_keys_list: List[str] = (
            exclude_keys if exclude_keys is not None else []
        )

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
            # Also exclude cache_mode since it's a control parameter.
            excluded_keys = set(exclude_keys_list) | {"cache_mode"}
            kwargs_for_cache_key = {
                k: v for k, v in kwargs.items() if k not in excluded_keys
            }
            # Prepare kwargs for the actual function call.
            # Keep cache_mode since the wrapped function may need it in its signature.
            kwargs_for_func = kwargs.copy()
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
                _LOG.trace(
                    "Updating cache with key='%s' value='%s'", cache_key, value
                )
                if write_through:
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
