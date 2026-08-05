#!/usr/bin/env python
"""
Manage the `hcache_simple` function cache from the command line.

Usage examples:
```
# Print stats for all cached functions.
> manage_cache.py --action print_info

# Clear everything (memory + disk).
> manage_cache.py --action clear_all

# Clear only the in-process memory layer.
> manage_cache.py --action clear_mem

# Clear only disk files.
> manage_cache.py --action clear_disk

# Run a self-contained smoke test.
> manage_cache.py --action test
```

Import as:

import dev_scripts_helpers.coding_tools.manage_cache as dsccomaca
"""

import argparse
import logging

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hselect_action as hselacti

_LOG = logging.getLogger(__name__)

# #############################################################################
# Valid actions.
# #############################################################################

_VALID_ACTIONS = [
    # Clear both memory and disk caches for all functions.
    "clear_all",
    # Clear only the in-process memory cache for all functions.
    "clear_mem",
    # Clear only disk cache files for all functions.
    "clear_disk",
    # Print entry-count stats for all locally cached functions.
    "print_info",
    # Run a smoke test of the cache round-trip.
    "test",
]
_DEFAULT_ACTIONS = ["print_info"]

# #############################################################################
# Smoke-test function.
# #############################################################################

# The function name used by the smoke test, derived from the decorated name.
_TEST_FUNC_NAME = "manage_cache_test_func"


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def manage_cache_test_func() -> str:
    """
    Return a large string to exercise the cache round-trip.

    :return: a 1 MB string of `#` characters
    """
    _LOG.info("Executing manage_cache_test_func (cache miss)")
    txt = "#" * 1024**2
    return txt


def _run_smoke_test() -> None:
    """
    Run a smoke test exercising write, read, and reset operations.

    The test uses a custom cache directory under `/tmp` so it does not
    pollute the main project cache.
    """
    cache_dir = "/tmp/manage_cache.test"
    _LOG.info("Smoke test: using cache_dir='%s'", cache_dir)
    hcacsimp.set_cache_property(_TEST_FUNC_NAME, "cache_dir", cache_dir)
    # Reset any leftover state.
    hcacsimp.reset_disk_cache(_TEST_FUNC_NAME, interactive=False)
    hcacsimp.reset_mem_cache(_TEST_FUNC_NAME)
    # First call: must be a cache miss (function executes).
    _LOG.info("Call 1 (expect miss)...")
    manage_cache_test_func()
    _LOG.info(
        "Stats after call 1:\n%s", hcacsimp.cache_stats_to_str(_TEST_FUNC_NAME)
    )
    # Drop memory only; second call must reload from disk.
    hcacsimp.reset_mem_cache(_TEST_FUNC_NAME)
    _LOG.info("Call 2 (expect disk hit)...")
    manage_cache_test_func()
    _LOG.info(
        "Stats after call 2:\n%s", hcacsimp.cache_stats_to_str(_TEST_FUNC_NAME)
    )
    _LOG.info("Smoke test complete.")


# #############################################################################
# Argument parsing and main.
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    print(hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True))
    # Execute selected actions.
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if not to_execute:
            continue
        if action == "clear_all":
            _LOG.info("Clearing all caches (memory + disk)...")
            hcacsimp.reset_cache(interactive=False)
        elif action == "clear_mem":
            _LOG.info("Clearing memory cache...")
            hcacsimp.reset_mem_cache()
        elif action == "clear_disk":
            _LOG.info("Clearing disk cache...")
            hcacsimp.reset_disk_cache(interactive=False)
        elif action == "print_info":
            txt = hcacsimp.cache_stats_to_str()
            if txt is not None:
                print(txt.to_string())
            else:
                _LOG.info("No cached functions found.")
        elif action == "test":
            _run_smoke_test()
        else:
            raise ValueError(f"Invalid action='{action}'")
    hdbg.dassert_eq(
        len(actions), 0, "There are unprocessed actions: %s", str(actions)
    )


if __name__ == "__main__":
    _main(_parse())
