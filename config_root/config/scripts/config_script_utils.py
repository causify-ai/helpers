"""
Utility functions for config script.

Import as:

import config_root.config.scripts.config_script_utils as crcscsut
"""

import argparse
import collections
import importlib
import itertools
import json
import logging
import os
from typing import Any

import yaml

import config_root.config.config_ as crococon
import helpers.hdbg as hdbg
import helpers.hio as hio

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_DUMMY = crococon.DUMMY

# #############################################################################
# Helpers
# #############################################################################


def _load_config(path: str) -> crococon.Config:
    """
    Load a config from YAML file.

    :param path: path to YAML file
    :return: Config object
    """
    hdbg.dassert_file_exists(path)
    text = hio.from_file(path)
    data = yaml.safe_load(text)
    if data is None:
        data = {}
    config = crococon.Config.from_dict(data)
    return config


def _save_config(config: crococon.Config, path: str) -> None:
    """
    Save a config to YAML file.

    :param config: Config object
    :param path: path to YAML file to write
    """
    yaml_text = _config_to_yaml(config)
    hio.to_file(path, yaml_text)
    _LOG.info("Saved config to '%s'", path)


def _config_to_yaml(config: crococon.Config) -> str:
    """
    Convert a Config to YAML string.

    :param config: Config object
    :return: YAML string
    """
    data = config.to_dict()
    # Convert OrderedDict to regular dict for YAML compatibility.
    data = _convert_to_dict(data)
    yaml_text = yaml.dump(data, default_flow_style=False, sort_keys=False)
    return yaml_text


def _convert_to_dict(obj: Any) -> Any:
    """
    Recursively convert OrderedDict to regular dict.

    :param obj: object to convert
    :return: converted object
    """
    if isinstance(obj, collections.OrderedDict):
        return {k: _convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, dict):
        return {k: _convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_convert_to_dict(v) for v in obj)
    else:
        return obj


def _yaml_to_config(text: str) -> crococon.Config:
    """
    Convert YAML string to Config.

    :param text: YAML text
    :return: Config object
    """
    data = yaml.safe_load(text)
    if data is None:
        data = {}
    config = crococon.Config.from_dict(data)
    return config


def _load_class(class_path: str) -> type:
    """
    Load a Python class from a module path string.

    :param class_path: "module.submodule.ClassName"
    :return: class object
    """
    parts = class_path.rsplit(".", 1)
    if len(parts) != 2:
        hdbg.dfatal(f"Invalid class path: {class_path}")
    module_path, class_name = parts
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        hdbg.dfatal(f"Failed to load class {class_path}: {str(e)}")
    return cls


def _has_dummy(config: crococon.Config) -> bool:
    """
    Check if config contains DUMMY placeholders.

    :param config: Config object
    :return: True if DUMMY values found
    """
    flattened = config.flatten()
    for value in flattened.values():
        if value == _DUMMY:
            return True
    return False


def _get_dummy_keys(config: crococon.Config) -> list:
    """
    Get list of keys that have DUMMY values.

    :param config: Config object
    :return: list of key tuples
    """
    flattened = config.flatten()
    dummy_keys = []
    for key, value in flattened.items():
        if value == _DUMMY:
            dummy_keys.append(key)
    return dummy_keys


def _diff_configs(cfg1: crococon.Config, cfg2: crococon.Config) -> str:
    """
    Show differences between two configs.

    :param cfg1: first Config
    :param cfg2: second Config
    :return: diff output string
    """
    flat1 = cfg1.flatten()
    flat2 = cfg2.flatten()
    all_keys = set(flat1.keys()) | set(flat2.keys())
    all_keys = sorted(all_keys)
    lines = []
    for key in all_keys:
        val1 = flat1.get(key, "<missing>")
        val2 = flat2.get(key, "<missing>")
        if val1 != val2:
            key_str = ".".join(str(k) for k in key)
            lines.append(f"  {key_str}:")
            lines.append(f"    - {val1}")
            lines.append(f"    + {val2}")
    if not lines:
        return "Configs are identical."
    return "\n".join(lines)


# #############################################################################
# Commands
# #############################################################################


def cmd_template(args: argparse.Namespace) -> int:
    """
    Generate config template from builder class.
    """
    _LOG.info("Generating template from '%s'", args.builder)
    try:
        cls = _load_class(args.builder)
        instance = cls()
        if not hasattr(instance, "get_config_template"):
            hdbg.dfatal(
                "Class does not have get_config_template method",
                args.builder,
            )
        config = instance.get_config_template()
        yaml_text = _config_to_yaml(config)
        if args.out:
            hio.to_file(args.out, yaml_text)
            _LOG.info("Template saved to '%s'", args.out)
        else:
            print(yaml_text, end="")
        return 0
    except Exception as e:
        _LOG.error("Error generating template: %s", str(e))
        return 3


def cmd_validate(args: argparse.Namespace) -> int:
    """
    Validate config for DUMMY placeholders and unknown keys.
    """
    _LOG.info("Validating config from '%s'", args.config)
    try:
        config = _load_config(args.config)
        # Check for DUMMY placeholders.
        if _has_dummy(config):
            dummy_keys = _get_dummy_keys(config)
            _LOG.error(
                "Config has DUMMY placeholders: %s",
                dummy_keys,
            )
            return 1
        # Check for unknown keys if builder is provided.
        if args.builder:
            _LOG.info("Validating against builder '%s'", args.builder)
            try:
                cls = _load_class(args.builder)
                instance = cls()
                if not hasattr(instance, "_validate_config_and_dag"):
                    _LOG.warning(
                        "Builder does not have _validate_config_and_dag method"
                    )
                else:
                    # Call validation method.
                    instance._validate_config_and_dag(config)
            except Exception as e:
                _LOG.error("Unknown config keys detected: %s", str(e))
                return 2
        _LOG.info("Config is valid.")
        return 0
    except Exception as e:
        _LOG.error("Error validating config: %s", str(e))
        return 3


def cmd_merge(args: argparse.Namespace) -> int:
    """
    Merge multiple configs left-to-right.
    """
    if len(args.configs) < 2:
        hdbg.dfatal("merge requires at least 2 config files")
    _LOG.info("Merging %d configs", len(args.configs))
    try:
        # Load base config.
        result = _load_config(args.configs[0])
        _LOG.info("Loaded base config from '%s'", args.configs[0])
        # Merge remaining configs.
        for config_file in args.configs[1:]:
            override = _load_config(config_file)
            result.update(override, update_mode="overwrite")
            _LOG.info("Merged config from '%s'", config_file)
        # Output result.
        yaml_text = _config_to_yaml(result)
        if args.out:
            hio.to_file(args.out, yaml_text)
            _LOG.info("Merged config saved to '%s'", args.out)
        else:
            print(yaml_text, end="")
        return 0
    except Exception as e:
        _LOG.error("Error merging configs: %s", str(e))
        return 3


def cmd_set(args: argparse.Namespace) -> int:
    """
    Set a single key in a config.
    """
    _LOG.info(
        "Setting key='%s' to value='%s' in config '%s'",
        args.key,
        args.value,
        args.config,
    )
    try:
        config = _load_config(args.config)
        # Set update_mode to overwrite to allow setting existing keys.
        config.update_mode = "overwrite"
        # Parse key as dot-notation.
        key_parts = args.key.split(".")
        key_tuple = tuple(key_parts)
        # Try to convert value to appropriate type.
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        config[key_tuple] = value
        _LOG.info("Set %s to %s", args.key, value)
        # Determine output file.
        out_file = args.out if args.out else args.config
        _save_config(config, out_file)
        return 0
    except Exception as e:
        _LOG.error("Error setting config key: %s", str(e))
        return 3


def cmd_get(args: argparse.Namespace) -> int:
    """
    Get a single key from a config.
    """
    _LOG.info("Getting key='%s' from config '%s'", args.key, args.config)
    try:
        config = _load_config(args.config)
        # Parse key as dot-notation.
        key_parts = args.key.split(".")
        key_tuple = tuple(key_parts)
        # Get value.
        try:
            value = config[key_tuple]
            print(value)
            return 0
        except KeyError:
            _LOG.error("Key not found: %s", args.key)
            return 1
    except Exception as e:
        _LOG.error("Error getting config key: %s", str(e))
        return 3


def cmd_diff(args: argparse.Namespace) -> int:
    """
    Show differences between two configs.
    """
    _LOG.info("Comparing configs '%s' and '%s'", args.config1, args.config2)
    try:
        cfg1 = _load_config(args.config1)
        cfg2 = _load_config(args.config2)
        diff_text = _diff_configs(cfg1, cfg2)
        print(diff_text)
        return 0
    except Exception as e:
        _LOG.error("Error diffing configs: %s", str(e))
        return 3


def cmd_sweep(args: argparse.Namespace) -> int:
    """
    Generate a list of configs from a parameter grid.
    """
    _LOG.info(
        "Generating sweep configs from base='%s' grid='%s'",
        args.config,
        args.grid,
    )
    try:
        # Load base config.
        base_config = _load_config(args.config)
        # Load grid.
        hdbg.dassert_file_exists(args.grid)
        grid_text = hio.from_file(args.grid)
        grid_data = yaml.safe_load(grid_text)
        # Create output directory.
        hio.create_dir(args.out_dir, incremental=False)
        # Generate all combinations.
        grid_keys = list(grid_data.keys())
        grid_values = [grid_data[k] for k in grid_keys]
        count = 0
        for combination in itertools.product(*grid_values):
            # Create config for this combination.
            config = base_config.copy()
            # Set update_mode to overwrite to allow setting existing keys.
            config.update_mode = "overwrite"
            for key_path, value in zip(grid_keys, combination):
                key_parts = key_path.split(".")
                key_tuple = tuple(key_parts)
                config[key_tuple] = value
            # Save to file.
            out_file = os.path.join(args.out_dir, f"config_{count:03d}.yaml")
            _save_config(config, out_file)
            count += 1
        _LOG.info("Generated %d sweep configs in '%s'", count, args.out_dir)
        return 0
    except Exception as e:
        _LOG.error("Error generating sweep configs: %s", str(e))
        return 3
