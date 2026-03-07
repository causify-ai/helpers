"""
Unit tests for config command line tools.

Import as:

import config_root.config.test.test_config_scripts as crcotsscr
"""

import logging
import os
from collections import OrderedDict
from itertools import product
from typing import Any

import yaml

import helpers.hio as hio
import helpers.hunit_test as hunitest
import config_root.config.config_ as crococon

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test helpers - Utilities for config command testing
# #############################################################################


def _load_config_from_yaml(yaml_text: str) -> crococon.Config:
    """
    Helper to convert YAML text to Config.
    """
    data = yaml.safe_load(yaml_text)
    if data is None:
        data = {}
    config = crococon.Config.from_dict(data)
    return config


def _convert_orderdict_to_dict(obj: Any) -> Any:
    """
    Recursively convert OrderedDict to regular dict.
    """
    if isinstance(obj, OrderedDict):
        return {k: _convert_orderdict_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, dict):
        return {k: _convert_orderdict_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_convert_orderdict_to_dict(v) for v in obj)
    else:
        return obj


def _config_to_yaml(config: crococon.Config) -> str:
    """
    Helper to convert Config to YAML text.
    """
    data = config.to_dict()
    # Convert OrderedDict to regular dict for YAML compatibility.
    data = _convert_orderdict_to_dict(data)
    yaml_text = yaml.dump(data, default_flow_style=False, sort_keys=False)
    return yaml_text


# #############################################################################
# Test_yaml_config_conversion
# #############################################################################


class Test_yaml_config_conversion(hunitest.TestCase):
    """
    Test conversion between Config and YAML formats.
    """

    def test1(self) -> None:
        """
        Test basic config to YAML and back.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["a", "b"] = 1
        config["a", "c"] = 2
        config["d"] = 3

        # Convert to YAML and back.
        yaml_text = _config_to_yaml(config)
        config_restored = _load_config_from_yaml(yaml_text)

        # Check outputs.
        self.assert_equal(str(config), str(config_restored))

    def test2(self) -> None:
        """
        Test nested config structure.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["model", "name"] = "linear"
        config["model", "params", "alpha"] = 0.01
        config["model", "params", "beta"] = 0.5
        config["data", "path"] = "/tmp/data"

        # Convert to YAML and back.
        yaml_text = _config_to_yaml(config)
        config_restored = _load_config_from_yaml(yaml_text)

        # Check outputs.
        self.assert_equal(str(config), str(config_restored))

    def test3(self) -> None:
        """
        Test config with single value.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["value"] = 42

        # Convert to YAML and back.
        yaml_text = _config_to_yaml(config)
        config_restored = _load_config_from_yaml(yaml_text)

        # Check outputs.
        self.assert_equal(config_restored["value"], 42)


# #############################################################################
# Test_has_dummy
# #############################################################################


class Test_has_dummy(hunitest.TestCase):
    """
    Test DUMMY placeholder detection.
    """

    def test1(self) -> None:
        """
        Test config with no DUMMY values.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["a"] = 1
        config["b"] = 2

        # Run test.
        flattened = config.flatten()
        has_dummy = any(v == crococon.DUMMY for v in flattened.values())

        # Check output.
        self.assertFalse(has_dummy)

    def test2(self) -> None:
        """
        Test config with DUMMY values.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["a"] = 1
        config["b"] = crococon.DUMMY

        # Run test.
        flattened = config.flatten()
        has_dummy = any(v == crococon.DUMMY for v in flattened.values())

        # Check output.
        self.assertTrue(has_dummy)

    def test3(self) -> None:
        """
        Test nested config with DUMMY in nested structure.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["model", "name"] = "linear"
        config["model", "alpha"] = crococon.DUMMY

        # Run test.
        flattened = config.flatten()
        has_dummy = any(v == crococon.DUMMY for v in flattened.values())

        # Check output.
        self.assertTrue(has_dummy)


# #############################################################################
# Test_merge_configs
# #############################################################################


class Test_merge_configs(hunitest.TestCase):
    """
    Test merging multiple configs.
    """

    def test1(self) -> None:
        """
        Test basic merge: override takes precedence.
        """
        # Prepare inputs.
        base = crococon.Config()
        base["a"] = 1
        base["b"] = 2

        override = crococon.Config()
        override["b"] = 20
        override["c"] = 3

        # Run test.
        base.update(override, update_mode="overwrite")

        # Check outputs.
        self.assert_equal(base["a"], 1)
        self.assert_equal(base["b"], 20)
        self.assert_equal(base["c"], 3)

    def test2(self) -> None:
        """
        Test merge with nested configs.
        """
        # Prepare inputs.
        base = crococon.Config()
        base["model", "name"] = "linear"
        base["model", "alpha"] = 0.01

        override = crococon.Config()
        override["model", "alpha"] = 0.1
        override["data", "path"] = "/tmp"

        # Run test.
        base.update(override, update_mode="overwrite")

        # Check outputs.
        self.assert_equal(base["model", "name"], "linear")
        self.assert_equal(base["model", "alpha"], 0.1)
        self.assert_equal(base["data", "path"], "/tmp")

    def test3(self) -> None:
        """
        Test merge with three configs left-to-right.
        """
        # Prepare inputs.
        cfg1 = crococon.Config()
        cfg1["a"] = 1
        cfg1["b"] = 2

        cfg2 = crococon.Config()
        cfg2["b"] = 20
        cfg2["c"] = 3

        cfg3 = crococon.Config()
        cfg3["a"] = 100

        # Run test.
        cfg1.update(cfg2, update_mode="overwrite")
        cfg1.update(cfg3, update_mode="overwrite")

        # Check outputs.
        self.assert_equal(cfg1["a"], 100)
        self.assert_equal(cfg1["b"], 20)
        self.assert_equal(cfg1["c"], 3)


# #############################################################################
# Test_set_get_config
# #############################################################################


class Test_set_get_config(hunitest.TestCase):
    """
    Test setting and getting config keys with dot notation.
    """

    def test1(self) -> None:
        """
        Test set and get simple key.
        """
        # Prepare inputs.
        config = crococon.Config()

        # Run test: set.
        config[("a",)] = 1

        # Check output: get.
        value = config[("a",)]
        self.assert_equal(value, 1)

    def test2(self) -> None:
        """
        Test set and get nested key with dot notation.
        """
        # Prepare inputs.
        config = crococon.Config()

        # Run test: set via tuple.
        key_tuple = ("model", "alpha")
        config[key_tuple] = 0.01

        # Check output: get via tuple.
        value = config[key_tuple]
        self.assert_equal(value, 0.01)

    def test3(self) -> None:
        """
        Test get non-existent key raises KeyError.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["a"] = 1

        # Run test and check output.
        with self.assertRaises(KeyError):
            _ = config[("nonexistent",)]


# #############################################################################
# Test_diff_configs
# #############################################################################


class Test_diff_configs(hunitest.TestCase):
    """
    Test diffing two configs.
    """

    def test1(self) -> None:
        """
        Test identical configs.
        """
        # Prepare inputs.
        cfg1 = crococon.Config()
        cfg1["a"] = 1
        cfg1["b"] = 2

        cfg2 = crococon.Config()
        cfg2["a"] = 1
        cfg2["b"] = 2

        # Run test.
        flat1 = cfg1.flatten()
        flat2 = cfg2.flatten()
        is_equal = flat1 == flat2

        # Check output.
        self.assertTrue(is_equal)

    def test2(self) -> None:
        """
        Test different configs find differences.
        """
        # Prepare inputs.
        cfg1 = crococon.Config()
        cfg1["a"] = 1
        cfg1["b"] = 2

        cfg2 = crococon.Config()
        cfg2["a"] = 1
        cfg2["b"] = 20

        # Run test.
        flat1 = cfg1.flatten()
        flat2 = cfg2.flatten()
        differences = {
            k: (flat1[k], flat2[k]) for k in flat1 if flat1[k] != flat2[k]
        }

        # Check output.
        self.assert_equal(len(differences), 1)
        self.assert_equal(differences[("b",)], (2, 20))

    def test3(self) -> None:
        """
        Test configs with different keys.
        """
        # Prepare inputs.
        cfg1 = crococon.Config()
        cfg1["a"] = 1
        cfg1["b"] = 2

        cfg2 = crococon.Config()
        cfg2["a"] = 1
        cfg2["c"] = 3

        # Run test.
        flat1 = cfg1.flatten()
        flat2 = cfg2.flatten()
        all_keys = set(flat1.keys()) | set(flat2.keys())
        different_keys = []
        for k in all_keys:
            v1 = flat1.get(k, "<missing>")
            v2 = flat2.get(k, "<missing>")
            if v1 != v2:
                different_keys.append(k)

        # Check output.
        self.assert_equal(len(different_keys), 2)


# #############################################################################
# Test_sweep_configs
# #############################################################################


class Test_sweep_configs(hunitest.TestCase):
    """
    Test parameter sweep generation.
    """

    def test1(self) -> None:
        """
        Test sweep with 2 parameters x 2 values each = 4 configs.
        """
        # Prepare inputs.
        base_config = crococon.Config()
        base_config["model", "name"] = "linear"
        base_config["model", "alpha"] = 0.01

        grid_data = {"model.alpha": [0.01, 0.1], "model.beta": [0.5, 1.0]}

        # Run test.
        grid_keys = list(grid_data.keys())
        grid_values = [grid_data[k] for k in grid_keys]
        combinations = list(product(*grid_values))

        # Check output.
        self.assert_equal(len(combinations), 4)

    def test2(self) -> None:
        """
        Test sweep with 3 parameters creates correct combinations.
        """
        # Prepare inputs.
        grid_data = {
            "model.alpha": [0.01, 0.1],
            "model.beta": [0.5, 1.0],
            "data.size": [100, 1000],
        }

        # Run test.
        grid_keys = list(grid_data.keys())
        grid_values = [grid_data[k] for k in grid_keys]
        combinations = list(product(*grid_values))

        # Check output: 2 x 2 x 2 = 8.
        self.assert_equal(len(combinations), 8)

    def test3(self) -> None:
        """
        Test that sweep maintains base config values.
        """
        # Prepare inputs.
        base_config = crococon.Config()
        base_config["model", "name"] = "linear"
        base_config["model", "alpha"] = 0.01
        base_config["data", "path"] = "/tmp"

        grid_data = {"model.alpha": [0.1, 0.2]}

        # Run test: create one sweep config.
        grid_keys = list(grid_data.keys())
        grid_values = [grid_data[k] for k in grid_keys]
        combination = grid_values[0][0]  # Get first value of first key

        sweep_config = base_config.copy()
        # Set update_mode to overwrite to allow setting existing keys.
        sweep_config.update_mode = "overwrite"
        key_parts = grid_keys[0].split(".")
        key_tuple = tuple(key_parts)
        sweep_config[key_tuple] = combination

        # Check outputs: base values preserved, grid value updated.
        self.assert_equal(sweep_config["model", "name"], "linear")
        self.assert_equal(sweep_config["data", "path"], "/tmp")
        self.assert_equal(sweep_config["model", "alpha"], 0.1)


# #############################################################################
# Test_config_file_io
# #############################################################################


class Test_config_file_io(hunitest.TestCase):
    """
    Test reading and writing config files.
    """

    def test1(self) -> None:
        """
        Test write and read config from YAML file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "test_config.yaml")

        config = crococon.Config()
        config["a"] = 1
        config["b"] = 2

        # Run test: write.
        yaml_text = _config_to_yaml(config)
        hio.to_file(config_file, yaml_text)

        # Run test: read.
        yaml_read = hio.from_file(config_file)
        config_restored = _load_config_from_yaml(yaml_read)

        # Check output.
        self.assert_equal(str(config), str(config_restored))

    def test2(self) -> None:
        """
        Test config with nested structure.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "nested_config.yaml")

        config = crococon.Config()
        config["model", "name"] = "linear"
        config["model", "params", "alpha"] = 0.01
        config["model", "params", "beta"] = 0.5

        # Run test: write and read.
        yaml_text = _config_to_yaml(config)
        hio.to_file(config_file, yaml_text)
        yaml_read = hio.from_file(config_file)
        config_restored = _load_config_from_yaml(yaml_read)

        # Check output.
        self.assert_equal(
            config_restored["model", "params", "alpha"],
            0.01,
        )
        self.assert_equal(config_restored["model", "params", "beta"], 0.5)
