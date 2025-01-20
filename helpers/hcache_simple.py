import glob
import logging
import functools
import time
import json
import pickle
import os
import hashlib
from typing import Any, Callable, Dict, List, Tuple, Union

import pandas as pd
import gspread_pandas
import re
import numpy as np
from IPython.display import display
import numpy as np
from gspread_pandas import Spread, Client

from tqdm.autonotebook import tqdm

import helpers.hdbg as hdbg
import helpers.hcache as hcache
import helpers.hpandas as hpandas
import helpers.hprint as hprint
import helpers.hsystem as hsystem


_LOG = logging.getLogger(__name__)


# #############################################################################
# Cache
# #############################################################################


if "_CACHE" not in globals():
    _LOG.debug("Creating _CACHE")
    _CACHE = {}


# Cache performance.


if "_CACHE_PERF" not in globals():
    _LOG.debug("Creating _CACHE_PERF")
    _CACHE_PERF = {}


def enable_cache_perf(func_name: str) -> None:
    _CACHE_PERF[func_name] = {"tot": 0, "hits": 0, "misses": 0}


def disable_cache_perf(func_name: str) -> None:
    _CACHE_PERF[func_name] = None


def get_cache_perf(func_name: str) -> Union[Dict, None]:
    if func_name in _CACHE_PERF:
        return _CACHE_PERF[func_name]
    return None


def get_cache_perf_stats(func_name: str) -> str:
    """
    Get the cache performance statistics for a given function.

    :param func_name: The name of the function whose cache performance stats are
        to be retrieved.
    :returns: A string with the cache performance statistics.
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
        f"{func_name}: hits={hits} misses={misses} tot={tot} hit_rate"
        f"={hit_rate:.2f}"
    )
    return txt


# Cache properties.


if "_CACHE_PROPERTY" not in globals():
    _LOG.debug("Creating _CACHE_PROPERTY")
    if os.path.exists("cache_property.pkl"):
        _LOG.debug("Loading from cache_property.pkl")
        _CACHE_PROPERTY = pickle.load(open("cache_property.pkl", "rb"))
    else:
        # func_name -> key -> value properties.
        _CACHE_PROPERTY = {}


def _check_valid_cache_property(property_name: str) -> None:
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
    ]
    hdbg.dassert_in(property_name, valid_properties)


def set_cache_property(func_name: str, property_name: str, val: bool) -> None:
    """
    Set a property for the cache of a given function name.

    :param func_name: The name of the function whose cache property is to be set.
    :param property_name: The name of the property to set.
    :param val: The value to set for the property.
    """
    _check_valid_cache_property(property_name)
    # Assign value.
    global _CACHE_PROPERTY
    if func_name not in _CACHE_PROPERTY:
        _CACHE_PROPERTY[func_name] = {}
    dict_ = _CACHE_PROPERTY[func_name]
    dict_[property_name] = val
    # Update values on the disk.
    _LOG.debug("Updating the cache_property.pkl")
    pickle.dump(_CACHE_PROPERTY, open("cache_property.pkl", "wb"))


def get_cache_property(func_name: str, property_name: str) -> bool:
    """
    Get the value of a property for the cache of a given function name.
    """
    _check_valid_cache_property(property_name)
    # Read data.
    value = _CACHE_PROPERTY.get(func_name, {}).get(property_name, False)
    return value


def reset_cache_property() -> bool:
    _LOG.warning("Resetting cache_property.pkl")
    # Empty the values.
    global _CACHE_PROPERTY
    _CACHE_PROPERTY = {}
    # Update values on the disk.
    _LOG.debug("Updating the cache_property.pkl")
    pickle.dump(_CACHE_PROPERTY, open("cache_property.pkl", "wb"))


def cache_property_to_str(func_name: str) -> str:
    """
    Convert cache properties to a string representation.

    :param func_name: The name of the function whose cache properties are to be
        converted.
    :returns: A string representation of the cache properties.
    """
    txt: List[str] = []
    txt.append("# func_name=%s" % func_name)
    if func_name in _CACHE_PROPERTY:
        for k, v in _CACHE_PROPERTY[func_name].items():
            txt.append("%s: %s" % (k, v))
    txt = "\n".join(txt)
    return txt


# Disk cache.


# CACHE_TYPE = "pickle"
CACHE_TYPE = "json"


def _get_cache_file_name(func_name: str) -> str:
    file_name = "cache.%s" % func_name
    if CACHE_TYPE == "pickle":
        file_name += ".pkl"
    elif CACHE_TYPE == "json":
        file_name += ".json"
    else:
        raise ValueError("Invalid cache type '%s'" % CACHE_TYPE)
    return file_name


def _save_cache_dict_to_disk(func_name: str, data: Dict) -> None:
    """
    Save a cache dictionary into the disk cache.
    """
    # Get the filename for the disk cache.
    file_name = _get_cache_file_name(func_name)
    # Save the data to the disk cache.
    if CACHE_TYPE == "pickle":
        with open(file_name, "wb") as file:
            pickle.dump(data, file)
    elif CACHE_TYPE == "json":
        with open(file_name, "w") as file:
            json.dump(data, file)
    else:
        raise ValueError("Invalid cache type '%s'" % CACHE_TYPE)


def get_disk_cache(func_name: str) -> Dict:
    file_name = _get_cache_file_name(func_name)
    # If the disk cache doesn't exist, create it.
    if not os.path.exists(file_name):
        _LOG.debug("No cache from disk")
        data = {}
        _save_cache_dict_to_disk(func_name, data)
    # Load data.
    if CACHE_TYPE == "pickle":
        with open(file_name, "rb") as file:
            data = pickle.load(file)
    elif CACHE_TYPE == "json":
        with open(file_name, "r") as file:
            data = json.load(file)
    else:
        raise ValueError("Invalid cache type '%s'" % CACHE_TYPE)
    return data


def force_cache_from_disk(func_name: str = "") -> None:
    """
    Force to get the cache from disk and update the memory cache.
    """
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name in get_cache_func_names("all"):
            force_cache_from_disk(func_name)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    _LOG.debug("func_name='%s'", func_name)
    # Get disk cache.
    disk_cache = get_disk_cache(func_name)
    _LOG.debug("disk_cache=%s", len(disk_cache))
    # Update the memory cache.
    global _CACHE
    _CACHE[func_name] = disk_cache


def flush_cache_to_disk(func_name: str = "") -> None:
    """
    Flush the cache to disk and update the memory cache.
    """
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name in get_cache_func_names("all"):
            flush_cache_to_disk(func_name)
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


# Get cache.


def get_cache_func_names(type_: str) -> List[str]:
    """
    Retrieve the cache function names based on the specified type.

    :param type_: The type of cache to retrieve ('all', 'mem', or 'disk').
    :return: A list of function names corresponding to the specified cache type.
    """
    if type_ == "all":
        mem_func_names = get_cache_func_names("mem")
        disk_func_names = get_cache_func_names("disk")
        return sorted(set(mem_func_names + disk_func_names))
    elif type_ == "mem":
        mem_func_names = sorted(list(_CACHE.keys()))
        return mem_func_names
    elif type_ == "disk":
        disk_func_names = glob.glob(f"cache.*")
        disk_func_names = [
            re.sub(r"cache\.(.*)\.(json|pkl)", r"\1", cache)
            for cache in disk_func_names
        ]
        disk_func_names = sorted(disk_func_names)
        return disk_func_names
    else:
        raise ValueError("Invalid type '%s'" % type_)


def get_mem_cache(func_name: str) -> Dict[str, Any]:
    if func_name in _CACHE:
        mem_cache = _CACHE[func_name]
    else:
        mem_cache = {}
    return mem_cache


def get_cache(func_name: str) -> Dict:
    """
    Retrieve the cache for a given function name.

    :param func_name: The name of the function whose cache is to be retrieved.
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


# Stats.


def cache_stats_to_str(func_name: str = "") -> pd.DataFrame:
    """
    find_email:
      memory: -
      disk: 1044

    verify_email:
      memory: -
      disk: 2322
    """
    if func_name == "":
        result = []
        for func_name in get_cache_func_names("all"):
            result_tmp = cache_stats_to_str(func_name)
            result.append(result_tmp)
        result = pd.concat(result)
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
    #
    # txt = hprint.indent("\n".join(txt))
    #
    # txt = func_name + ":\n" + txt
    return result


# Reset cache.


def reset_mem_cache(func_name: str = "") -> None:
    global _CACHE
    if func_name == "":
        _LOG.info("Before:\n%s", cache_stats_to_str())
        for func_name in get_cache_func_names("all"):
            reset_mem_cache(func_name)
        _LOG.info("After:\n%s", cache_stats_to_str())
        return
    _CACHE[func_name] = {}
    del _CACHE[func_name]


def reset_disk_cache(func_name: str = "") -> None:
    assert 0
    if func_name == "":
        cache_files = glob.glob(f"cache.*")
        for file_name in cache_files:
            os.remove(file_name)
        return
    file_name = _get_cache_file_name(func_name)
    os.remove(file_name)


# Decorator


def simple_cache(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get the function name.
        func_name = func.__name__
        if func_name.endswith("_intrinsic"):
            func_name = func_name[: -len("_intrinsic")]
        # Get the cache.
        cache = hyamm.get_cache(func_name)
        # Get the key.
        # key = (args, frozenset(kwargs.items()))
        key = args
        key = str(key)
        _LOG.debug("key=%s", key)
        # Get the cache properties.
        cache_perf = hyamm.get_cache_perf(func_name)
        _LOG.debug("cache_perf is None=%s", cache_perf is None)
        # Update the performance stats.
        if cache_perf:
            hdbg.dassert_in("tot", cache_perf)
            cache_perf["tot"] += 1
        # Handle a forced refresh.
        force_refresh = hyamm.get_cache_property(func_name, "force_refresh")
        _LOG.debug("force_refresh=%s", force_refresh)
        if not force_refresh and key in cache:
            # Update the performance stats.
            if cache_perf:
                cache_perf["hits"] += 1
            # Retrieve the value from the cache.
            value = cache[key]
        else:
            # Update the performance stats.
            if cache_perf:
                cache_perf["misses"] += 1
            # Abort on cache miss.
            abort_on_cache_miss = hyamm.get_cache_property(
                func_name, "abort_on_cache_miss"
            )
            _LOG.debug("abort_on_cache_miss=%s", abort_on_cache_miss)
            if abort_on_cache_miss:
                raise ValueError("Cache miss for key='%s'" % key)
            # Report on cache miss.
            report_on_cache_miss = hyamm.get_cache_property(
                func_name, "report_on_cache_miss"
            )
            _LOG.debug("report_on_cache_miss=%s", report_on_cache_miss)
            if report_on_cache_miss:
                _LOG.debug("Cache miss for key='%s'", key)
                return "_cache_miss_"
            # Access the intrinsic function.
            value = func(*args, **kwargs)
            # Update cache.
            cache[key] = value
            _LOG.debug("Updating cache with key='%s' value='%s'", key, value)
        return value
    return wrapper