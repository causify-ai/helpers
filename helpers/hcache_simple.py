"""
Detailed documentation at
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
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Memory cache.
# #############################################################################

# Basic type for caching data: func_name -> key -> value properties. E.g.,
# ```
# {
#     "slow_square": {
#         "{\"args\": [4], \"kwargs\": {}}": 16
#     }
# }
# ```
_CacheType = Dict[str, Dict[str, Any]]

# Create global variable for the memory cache.
if "_CACHE" not in globals():
    _LOG.debug("Creating _CACHE")
    _CACHE: _CacheType = {}


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

_SYSTEM_PROPERTIES = ["type", "write_through", "exclude_keys"]


def get_main_cache_dir() -> str:
    git_dir = hgit.find_git_root()
    cache_dir = os.path.abspath(git_dir)
    return cache_dir


# Create global variable for the cache directory.
if "_CACHE_DIR" not in globals():
    _LOG.debug("Creating _CACHE_DIR")
    _CACHE_DIR = get_main_cache_dir()


def set_cache_dir(cache_dir: str) -> None:
    """
    Set the cache directory.
    """
    global _CACHE_DIR
    hdbg.dassert_isinstance(cache_dir, str)
    _CACHE_DIR = os.path.abspath(cache_dir)
    hio.create_dir(_CACHE_DIR, incremental=True)
    _LOG.debug("Setting _CACHE_DIR to %s", _CACHE_DIR)


def get_cache_dir() -> str:
    """
    Get the cache directory.
    """
    return _CACHE_DIR


def get_cache_property_file() -> str:
    """
    Get the cache property file name.

    :return: The cache property file name.
    """
    val = os.path.join(get_cache_dir(), "tmp.cache_property.pkl")
    return val


def _get_initial_cache_property() -> _CacheType:
    """
    Get the initial cache property from disk or create an empty one.

    :return: A dictionary containing cache properties.
    """
    file_name_ = get_cache_property_file()
    if os.path.exists(file_name_):
        _LOG.debug("Loading from %s", file_name_)
        with open(file_name_, "rb") as file:
            val = pickle.load(file)
    else:
        # func_name -> key -> value properties.
        val = {}
    val = cast(_CacheType, val)
    return val


# Create global variables for the cache properties.
if "_CACHE_PROPERTY" not in globals():
    _LOG.debug("Creating _CACHE_PROPERTY")
    _CACHE_PROPERTY = _get_initial_cache_property()


def _check_valid_cache_property(property_name: str) -> None:
    """
    Verify that a cache property name is valid for the given type.

    :param property_name: The property name to validate.
    """
    _LOG.debug(hprint.func_signature_to_str())
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
        "type",
    ]
    hdbg.dassert_in(property_name, valid_properties)


def set_cache_property(func_name: str, property_name: str, val: Any) -> None:
    """
    Set a property for the cache of a given function name.

    :param func_name: The name of the function whose cache property is
        to be set.
    :param property_name: The name of the property to set.
    :param val: The value to set for the property.
    """
    _LOG.debug(hprint.func_signature_to_str())
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
    _LOG.debug("Updating %s", file_name)
    # Make sure the dict is well-formed.
    for func_name_tmp in cache_property:
        hdbg.dassert_isinstance(func_name_tmp, str)
        _LOG.debug(
            "func_name_tmp='%s' -> %s",
            func_name_tmp,
            cache_property[func_name_tmp],
        )
    with open(file_name, "wb") as file:
        pickle.dump(cache_property, file)


def get_cache_property(func_name: str, property_name: str) -> Union[bool, Any]:
    """
    Get the value of a property for the cache of a given function name.
    """
    _LOG.debug(hprint.func_signature_to_str())
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
    _LOG.debug("before cache_property=%s", cache_property)
    # Iterate over a list of keys to avoid modifying the dictionary during iteration
    for func_name_tmp in list(cache_property.keys()):
        # Only remove non-system properties from the function's property dict
        func_prop = cache_property[func_name_tmp]
        for property_name_tmp in list(func_prop.keys()):
            if property_name_tmp not in _SYSTEM_PROPERTIES:
                del func_prop[property_name_tmp]
    _LOG.debug("after cache_property=%s", cache_property)
    # Update values on the disk.
    _LOG.debug("Updating %s", file_name)
    with open(file_name, "wb") as file:
        pickle.dump(cache_property, file)


# #############################################################################
# Get cache.
# #############################################################################

# Functions to retrieve cache (both memory and disk).


def get_cache_func_names(type_: str) -> List[str]:
    """
    Retrieve the cache function names based on the specified type.

    :param type_: The type of cache to retrieve ('all', 'mem', or
        'disk').
    :return: A list of function names corresponding to the specified
        cache type.
    """
    if type_ == "all":
        mem_func_names = get_cache_func_names("mem")
        disk_func_names = get_cache_func_names("disk")
        val = sorted(set(mem_func_names + disk_func_names))
    elif type_ == "mem":
        mem_func_names = sorted(list(_CACHE.keys()))
        val = mem_func_names
    elif type_ == "disk":
        disk_func_names = glob.glob(os.path.join(get_cache_dir(), "tmp.cache.*"))
        disk_func_names = [os.path.basename(cache) for cache in disk_func_names]
        disk_func_names = [
            re.sub(r"tmp\.cache\.(.*)\.(json|pkl)", r"\1", cache)
            for cache in disk_func_names
        ]
        disk_func_names = sorted(disk_func_names)
        val = disk_func_names
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
    _LOG.debug("cache_property=%s", cache_property)
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
    _LOG.debug("Creating _CACHE_PERF")
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
    :return: A string with the cache performance statistics.
        E.g., `slow_square: hits=2 misses=0 tot=2 hit_rate=1.00`.
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


def _get_cache_file_name(func_name: str) -> str:
    """
    Get the cache file name for a given function.

    :param func_name: The name of the function.
    :return: The cache file name with appropriate extension.
    """
    _LOG.debug("func_name='%s'", func_name)
    hdbg.dassert_isinstance(func_name, str)
    file_name = os.path.join(get_cache_dir(), f"tmp.cache.{func_name}")
    cache_type = get_cache_property(func_name, "type")
    _LOG.debug(hprint.to_str("cache_type"))
    if cache_type == "pickle":
        file_name += ".pkl"
    elif cache_type == "json":
        file_name += ".json"
    elif cache_type is None:
        # Cache type not set - try to infer from existing files.
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


def _save_cache_dict_to_disk(func_name: str, data: Dict) -> None:
    """
    Save a cache dictionary to the disk cache.

    :param func_name: The name of the function.
    :param data: The cache data to save.
    """
    # Get the filename for the disk cache.
    file_name = _get_cache_file_name(func_name)
    cache_type = get_cache_property(func_name, "type")
    _LOG.debug(hprint.to_str("file_name cache_type"))
    # Infer cache type from file extension if not set.
    if cache_type is None:
        if file_name.endswith(".pkl"):
            cache_type = "pickle"
        else:
            cache_type = "json"
    if cache_type == "pickle":
        with open(file_name, "wb") as file:
            pickle.dump(data, file)
    elif cache_type == "json":
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, sort_keys=True, ensure_ascii=False)
    else:
        raise ValueError(f"Invalid cache type '{cache_type}'")


def get_disk_cache(func_name: str) -> Dict:
    """
    Retrieve the disk cache for a given function.

    :param func_name: The name of the function.
    :return: A dictionary containing the cache data.
    """
    file_name = _get_cache_file_name(func_name)
    # If the disk cache doesn't exist, create it.
    if not os.path.exists(file_name):
        _LOG.debug("No cache from disk")
        data: _CacheType = {}
        _save_cache_dict_to_disk(func_name, data)
    # Load data.
    cache_type = get_cache_property(func_name, "type")
    _LOG.debug(hprint.to_str("cache_type"))
    # Infer cache type from file extension if not set.
    if cache_type is None:
        if file_name.endswith(".pkl"):
            cache_type = "pickle"
        else:
            cache_type = "json"
    if cache_type == "pickle":
        with open(file_name, "rb") as file:
            data = pickle.load(file)
    elif cache_type == "json":
        with open(file_name, "r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        raise ValueError(f"Invalid cache type '{cache_type}'")
    return data


# #############################################################################
# Stats.
# #############################################################################


def cache_stats_to_str(func_name: str = "") -> Optional["pd.DataFrame"]:  # noqa: F821
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
        for func_name in get_cache_func_names("all"):
            result_tmp = cache_stats_to_str(func_name)
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

    :param func_name: The name of the function. If empty, apply to all
        cached functions.
    """
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cache_func_names("all"):
            force_cache_from_disk(func_name_tmp)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    _LOG.debug("func_name='%s'", func_name)
    # Get disk cache.
    disk_cache = get_disk_cache(func_name)
    _LOG.debug("disk_cache=%s", len(disk_cache))
    # Update the memory cache.
    global _CACHE
    _CACHE[func_name] = disk_cache


def get_mem_cache(func_name: str) -> _CacheType:
    """
    Retrieve the memory cache for a given function.

    :param func_name: The name of the function.
    :return: A dictionary containing the memory cache data.
    """
    mem_cache = _CACHE.get(func_name, {})
    return mem_cache


def flush_cache_to_disk(func_name: str = "") -> None:
    """
    Flush the memory cache to disk and update the memory cache.

    :param func_name: The name of the function. If empty, apply to all
        cached functions.
    """
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cache_func_names("all"):
            flush_cache_to_disk(func_name_tmp)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    _LOG.debug("func_name='%s'", func_name)
    # Get memory cache.
    mem_cache = get_mem_cache(func_name)
    _LOG.debug("mem_cache=%s", len(mem_cache))
    # Get disk cache.
    disk_cache = get_disk_cache(func_name)
    _LOG.debug("disk_cache=%s", len(disk_cache))
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

    :param func_name: The name of the function whose cache is to be
        retrieved.
    :return: A dictionary containing the cache data.
    """
    global _CACHE
    if func_name in _CACHE:
        _LOG.debug("Loading mem cache for '%s'", func_name)
        cache = get_mem_cache(func_name)
    else:
        _LOG.debug("Loading disk cache for '%s'", func_name)
        cache = get_disk_cache(func_name)
        _CACHE[func_name] = cache
    return cache


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
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(func_name, str)
    if func_name == "":
        _LOG.info("Before resetting memory cache:\n%s", cache_stats_to_str())
        for func_name_tmp in get_cache_func_names("all"):
            reset_mem_cache(func_name=func_name_tmp)
        _LOG.info("After:\n%s", cache_stats_to_str())
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

    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_isinstance(interactive, bool)
    if interactive:
        hsystem.query_yes_no(
            f"Are you sure you want to reset the disk cache for func_name={func_name}?"
        )
    if func_name == "":
        _LOG.info("Before resetting disk cache:\n%s", cache_stats_to_str())
        cache_files = glob.glob(os.path.join(get_cache_dir(), "tmp.cache.*"))
        _LOG.warning("Resetting disk cache")
        for file_name in cache_files:
            if os.path.isfile(file_name):
                os.remove(file_name)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    #
    file_name = _get_cache_file_name(func_name)
    if os.path.exists(file_name):
        _LOG.warning("Removing cache file '%s'", file_name)
        os.remove(file_name)


def reset_cache(func_name: str = "", interactive: bool = True) -> None:
    """
    Reset both memory and disk cache for a given function.

    :param func_name: The name of the function. If empty, reset all caches.
    :param interactive: If True, prompt the user for confirmation before
        resetting the disk cache.
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(func_name, str)
    hdbg.dassert_isinstance(interactive, bool)
    reset_mem_cache(func_name=func_name)
    reset_disk_cache(func_name=func_name, interactive=interactive)


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


def _get_cache_key(args: Any, kwargs: Any) -> str:
    cache_key = json.dumps(
        {"args": args, "kwargs": kwargs},
        sort_keys=True,
        default=str,
    )
    _LOG.debug("cache_key=%s", cache_key)
    return cache_key


def mock_cache(func_name: str, args: Any, kwargs: Any, value: Any) -> None:
    """
    Mock the cache for a given function.

    E.g., when testing a cached expensive function (e.g., an LLM call or
    downloading data) we can mock the cache to return a fixed value, instead of
    calling the function.

    :param func_name: The name of the function.
    :param args: The arguments for the function.
    :param kwargs: The keyword arguments for the function.
    :param value: The value to store in the cache.
    """
    # In general we should not use the main cache for mocking.
    hdbg.dassert_ne( get_cache_dir(), get_main_cache_dir(),
        msg="We do not use the main cache for mocking")
    # Get the cache key.
    cache_key = _get_cache_key(args, kwargs)
    # Get the cache.
    cache = get_cache(func_name)
    # Update cache.
    cache[cache_key] = value


# TODO(gp): Not sure that cache_mode is worth having the duplication.
def simple_cache(
    *,
    cache_type: str = "json",
    write_through: bool = True,
    exclude_keys: List[str] = None,
) -> Callable[..., Any]:
    """
    Decorate a function to cache its results.

    The cache is stored in memory and on disk.
    :param cache_type: The type of cache to use ('json' or 'pickle').
    :param write_through: If True, the cache is written to disk after
        each access.
    :param exclude_keys: A list of keys to exclude from the cache key.
    :return: A decorator that can be applied to a function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorate a function to cache its results.
        """
        hdbg.dassert_in(cache_type, ("json", "pickle"))
        func_name = getattr(func, "__name__", "unknown_function")
        if func_name.endswith("_intrinsic"):
            func_name = func_name[: -len("_intrinsic")]
        # Only set cache type if not already set (preserve existing setting).
        existing_type = get_cache_property(func_name, "type")
        if not existing_type:
            set_cache_property(func_name, "type", cache_type)
        # Handle mutable default argument.
        nonlocal exclude_keys
        if exclude_keys is None:
            exclude_keys = []

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
            :param force_refresh: If True, the cache is refreshed regardless of
                whether the key exists in the cache.
            :param abort_on_cache_miss: If True, an exception is raised if the
                key is not found in the cache.
            :param report_on_cache_miss: If True, a message is logged if the key
                is not found in the cache, and the function returns
                "_cache_miss_" instead of accessing the real value.
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
            excluded_keys = set(exclude_keys) | {"cache_mode"}
            kwargs_for_cache_key = {
                k: v for k, v in kwargs.items() if k not in excluded_keys
            }
            # Prepare kwargs for the actual function call (excluding cache
            # control params).
            kwargs_for_func = {
                k: v for k, v in kwargs.items() if k not in {"cache_mode"}
            }
            # `cache_mode` is a special keyword argument to control caching
            # behavior.
            if "cache_mode" in kwargs:
                cache_mode = kwargs.get("cache_mode")
                _LOG.debug("cache_mode=%s", cache_mode)
                if cache_mode == "REFRESH_CACHE":
                    # Force to refresh the cache.
                    _LOG.debug("Forcing cache refresh")
                    force_refresh = True
                if cache_mode == "HIT_CACHE_OR_ABORT":
                    # Abort if the cache is not hit.
                    _LOG.debug("Abort on cache miss")
                    abort_on_cache_miss = True
                if cache_mode == "DISABLE_CACHE":
                    # Disable the cache.
                    _LOG.debug("Disabling cache")
                    value = func(*args, **kwargs_for_func)
                    return value
            # Get the key.
            cache_key = _get_cache_key(args, kwargs_for_cache_key)
            # Get the cache properties.
            cache_perf = get_cache_perf(func_name)
            _LOG.debug("cache_perf is None=%s", cache_perf is None)
            # Update the performance stats.
            if cache_perf:
                hdbg.dassert_in("tot", cache_perf)
                cache_perf["tot"] += 1
            # Handle a forced refresh.
            force_refresh = force_refresh or get_cache_property(
                func_name, "force_refresh"
            )
            _LOG.debug("force_refresh=%s", force_refresh)
            if cache_key in cache and not force_refresh:
                _LOG.debug("Cache hit for key='%s'", cache_key)
                # Update the performance stats.
                if cache_perf:
                    cache_perf["hits"] += 1
                # Retrieve the value from the cache.
                value = cache[cache_key]
            else:
                _LOG.debug("Cache miss for key='%s'", cache_key)
                # Update the performance stats.
                if cache_perf:
                    cache_perf["misses"] += 1
                # Abort on cache miss.
                abort_on_cache_miss = abort_on_cache_miss or get_cache_property(
                    func_name, "abort_on_cache_miss"
                )
                _LOG.debug("abort_on_cache_miss=%s", abort_on_cache_miss)
                if abort_on_cache_miss:
                    raise ValueError(f"Cache miss for key='{cache_key}'")
                # Report on cache miss.
                report_on_cache_miss = (
                    report_on_cache_miss
                    or get_cache_property(func_name, "report_on_cache_miss")
                )
                _LOG.debug("report_on_cache_miss=%s", report_on_cache_miss)
                if report_on_cache_miss:
                    _LOG.debug("Cache miss for key='%s'", cache_key)
                    return "_cache_miss_"
                # Access the intrinsic function.
                value = func(*args, **kwargs_for_func)
                # Update cache.
                cache[cache_key] = value
                _LOG.debug(
                    "Updating cache with key='%s' value='%s'", cache_key, value
                )
                #
                if write_through:
                    _LOG.debug("Writing through to disk")
                    flush_cache_to_disk(func_name)
            return value

        return wrapper

    return decorator
