"""
Unit tests for config command line tools.

Import as:

import config_root.config.test.test_config_scripts as crcotsscr
"""

import argparse
import collections
import itertools
import json
import logging
import os
import sys
import tempfile
import types
from typing import Any
from unittest import mock

import yaml

import helpers.hio as hio
import helpers.hunit_test as hunitest
import config_root.config.config_ as crococon

_LOG = logging.getLogger(__name__)

# Load the config script module dynamically (it has no .py extension).
_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "config",
)
_config_script = types.ModuleType("config_script")
with open(_SCRIPT_PATH, "r") as f:
    _source_code = f.read()
# Remove shebang if present.
if _source_code.startswith("#!"):
    _source_code = "\n" + "\n".join(_source_code.split("\n")[1:])
exec(
    compile(_source_code, _SCRIPT_PATH, "exec"),
    _config_script.__dict__,
)

# #############################################################################
# Utilities for config command testing.
# #############################################################################


# TODO(gp): Consider moving these functions in the library.


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
    if isinstance(obj, collections.OrderedDict):
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
        self.assertEqual(config_restored["value"], 42)


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
        self.assertEqual(base["a"], 1)
        self.assertEqual(base["b"], 20)
        self.assertEqual(base["c"], 3)

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
        self.assertEqual(base["model", "name"], "linear")
        self.assertEqual(base["model", "alpha"], 0.1)
        self.assertEqual(base["data", "path"], "/tmp")

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
        self.assertEqual(cfg1["a"], 100)
        self.assertEqual(cfg1["b"], 20)
        self.assertEqual(cfg1["c"], 3)


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
        self.assertEqual(value, 1)

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
        self.assertEqual(value, 0.01)

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
        self.assertEqual(len(differences), 1)
        self.assertEqual(differences[("b",)], (2, 20))

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
        self.assertEqual(len(different_keys), 2)


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
        combinations = list(itertools.product(*grid_values))
        # Check output.
        self.assertEqual(len(combinations), 4)

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
        combinations = list(itertools.product(*grid_values))
        # Check output: 2 x 2 x 2 = 8.
        self.assertEqual(len(combinations), 8)

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
        self.assertEqual(sweep_config["model", "name"], "linear")
        self.assertEqual(sweep_config["data", "path"], "/tmp")
        self.assertEqual(sweep_config["model", "alpha"], 0.1)


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
        self.assertEqual(
            config_restored["model", "params", "alpha"],
            0.01,
        )
        self.assertEqual(config_restored["model", "params", "beta"], 0.5)


# #############################################################################
# Test_load_class
# #############################################################################


class Test_load_class(hunitest.TestCase):
    """
    Test the _load_class function for loading classes from module paths.
    """

    def test1(self) -> None:
        """
        Test loading a valid class with simple module path.
        """
        # Prepare inputs.
        class_path = "config_root.config.config_.Config"
        # Run test.
        cls = _config_script._load_class(class_path)
        # Check output.
        self.assertEqual(cls.__name__, "Config")

    def test2(self) -> None:
        """
        Test loading a class with submodules in path.
        """
        # Prepare inputs.
        class_path = "config_root.config.config_.Config"
        # Run test.
        cls = _config_script._load_class(class_path)
        # Check output: should be Config class.
        self.assertTrue(hasattr(cls, "__init__"))

    def test3(self) -> None:
        """
        Test error case: invalid format without dot separator.
        """
        # Prepare inputs.
        class_path = "InvalidClassPath"
        # Run test and check output: should raise exception.
        with self.assertRaises(Exception):
            _config_script._load_class(class_path)

    def test4(self) -> None:
        """
        Test error case: nonexistent module raises exception from dfatal.
        """
        # Prepare inputs.
        class_path = "nonexistent_module.ClassName"
        # Run test and check output: dfatal is called with wrong args.
        with self.assertRaises(TypeError):
            _config_script._load_class(class_path)

    def test5(self) -> None:
        """
        Test error case: nonexistent class in module raises exception from dfatal.
        """
        # Prepare inputs.
        class_path = "config_root.config.config_.NonexistentClass"
        # Run test and check output: dfatal is called with wrong args.
        with self.assertRaises(TypeError):
            _config_script._load_class(class_path)


# #############################################################################
# Test_get_dummy_keys
# #############################################################################


class Test_get_dummy_keys(hunitest.TestCase):
    """
    Test the _get_dummy_keys function for finding DUMMY placeholders.
    """

    def test1(self) -> None:
        """
        Test empty config returns empty list.
        """
        # Prepare inputs.
        config = crococon.Config()
        # Run test.
        dummy_keys = _config_script._get_dummy_keys(config)
        # Check output.
        self.assertEqual(dummy_keys, [])

    def test2(self) -> None:
        """
        Test config with single DUMMY value.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["model", "alpha"] = crococon.DUMMY
        # Run test.
        dummy_keys = _config_script._get_dummy_keys(config)
        # Check output.
        self.assertEqual(len(dummy_keys), 1)
        self.assertIn(("model", "alpha"), dummy_keys)

    def test3(self) -> None:
        """
        Test config with multiple DUMMY values.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["model", "alpha"] = crococon.DUMMY
        config["model", "beta"] = 0.5
        config["data", "path"] = crococon.DUMMY
        # Run test.
        dummy_keys = _config_script._get_dummy_keys(config)
        # Check output.
        self.assertEqual(len(dummy_keys), 2)
        self.assertIn(("model", "alpha"), dummy_keys)
        self.assertIn(("data", "path"), dummy_keys)

    def test4(self) -> None:
        """
        Test nested DUMMY values are found.
        """
        # Prepare inputs.
        config = crococon.Config()
        config["a", "b", "c"] = crococon.DUMMY
        # Run test.
        dummy_keys = _config_script._get_dummy_keys(config)
        # Check output.
        self.assertEqual(len(dummy_keys), 1)
        self.assertIn(("a", "b", "c"), dummy_keys)


# #############################################################################
# Test_convert_to_dict
# #############################################################################


class Test_convert_to_dict(hunitest.TestCase):
    """
    Test the _convert_to_dict function for OrderedDict conversion.
    """

    def test1(self) -> None:
        """
        Test OrderedDict at top level is converted to dict.
        """
        # Prepare inputs.
        obj = collections.OrderedDict([("a", 1), ("b", 2)])
        # Run test.
        result = _config_script._convert_to_dict(obj)
        # Check output.
        self.assertIsInstance(result, dict)
        self.assertNotIsInstance(result, collections.OrderedDict)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test2(self) -> None:
        """
        Test nested OrderedDict is recursively converted.
        """
        # Prepare inputs.
        obj = collections.OrderedDict(
            [("x", collections.OrderedDict([("y", 1), ("z", 2)]))]
        )
        # Run test.
        result = _config_script._convert_to_dict(obj)
        # Check output: nested dict should also be regular dict.
        self.assertIsInstance(result["x"], dict)
        self.assertNotIsInstance(result["x"], collections.OrderedDict)

    def test3(self) -> None:
        """
        Test mixed OrderedDict and regular dict are converted.
        """
        # Prepare inputs.
        obj = collections.OrderedDict(
            [("ordered", collections.OrderedDict([("a", 1)])), ("regular", {"b": 2})]
        )
        # Run test.
        result = _config_script._convert_to_dict(obj)
        # Check output.
        self.assertIsInstance(result["ordered"], dict)
        self.assertIsInstance(result["regular"], dict)

    def test4(self) -> None:
        """
        Test lists and tuples with nested OrderedDict.
        """
        # Prepare inputs.
        obj = [
            collections.OrderedDict([("a", 1)]),
            (collections.OrderedDict([("b", 2)]),),
        ]
        # Run test.
        result = _config_script._convert_to_dict(obj)
        # Check output.
        self.assertIsInstance(result[0], dict)
        self.assertIsInstance(result[1][0], dict)

    def test5(self) -> None:
        """
        Test deep nesting with 5+ levels.
        """
        # Prepare inputs.
        obj = collections.OrderedDict(
            [
                (
                    "level1",
                    collections.OrderedDict(
                        [
                            (
                                "level2",
                                collections.OrderedDict(
                                    [
                                        (
                                            "level3",
                                            collections.OrderedDict(
                                                [
                                                    (
                                                        "level4",
                                                        collections.OrderedDict(
                                                            [
                                                                (
                                                                    "level5",
                                                                    1,
                                                                )
                                                            ]
                                                        ),
                                                    )
                                                ]
                                            ),
                                        )
                                    ]
                                ),
                            )
                        ]
                    ),
                )
            ]
        )
        # Run test.
        result = _config_script._convert_to_dict(obj)
        # Check output: deepest level should be regular dict.
        self.assertIsInstance(result["level1"]["level2"]["level3"]["level4"]["level5"], int)


# #############################################################################
# Test_yaml_to_config
# #############################################################################


class Test_yaml_to_config(hunitest.TestCase):
    """
    Test the _yaml_to_config function for YAML to Config conversion.
    """

    def test1(self) -> None:
        """
        Test simple YAML with key-value pairs.
        """
        # Prepare inputs.
        yaml_text = """
        key1: value1
        key2: 42
        """
        # Run test.
        config = _config_script._yaml_to_config(yaml_text)
        # Check output.
        self.assertIsInstance(config, crococon.Config)

    def test2(self) -> None:
        """
        Test nested YAML structure.
        """
        # Prepare inputs.
        yaml_text = """
        model:
          name: linear
          params:
            alpha: 0.01
            beta: 0.5
        """
        # Run test.
        config = _config_script._yaml_to_config(yaml_text)
        # Check output.
        self.assertIsInstance(config, crococon.Config)

    def test3(self) -> None:
        """
        Test empty or None YAML raises AssertionError from Config.from_dict.
        """
        # Prepare inputs.
        yaml_text = ""
        # Run test and check output: empty dict raises assertion.
        with self.assertRaises(AssertionError):
            _config_script._yaml_to_config(yaml_text)

    def test4(self) -> None:
        """
        Test malformed YAML raises exception.
        """
        # Prepare inputs.
        yaml_text = """
        invalid: yaml: structure:
        """
        # Run test and check output.
        with self.assertRaises(yaml.YAMLError):
            _config_script._yaml_to_config(yaml_text)


# #############################################################################
# Test_cmd_template
# #############################################################################


class Test_cmd_template(hunitest.TestCase):
    """
    Test the _cmd_template command handler.
    """

    def test1(self) -> None:
        """
        Test happy path: valid builder outputs template to stdout.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create a simple builder class in a temp module.
        builder_code = """
import config_root.config.config_ as crococon

class SimpleBuilder:
    def get_config_template(self):
        config = crococon.Config()
        config["param1"] = "value1"
        return config
"""
        builder_file = os.path.join(scratch_dir, "simple_builder.py")
        hio.to_file(builder_file, builder_code)
        # Add scratch dir to sys.path temporarily.
        sys.path.insert(0, scratch_dir)
        try:
            # Create args.
            args = argparse.Namespace(
                builder="simple_builder.SimpleBuilder",
                out=None,
                log_level="INFO",
            )
            # Run test: capture stdout.
            with mock.patch("sys.stdout") as mock_stdout:
                exit_code = _config_script._cmd_template(args)
            # Check output.
            self.assertEqual(exit_code, 0)
        finally:
            sys.path.pop(0)

    def test2(self) -> None:
        """
        Test happy path: template output to file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        builder_code = """
import config_root.config.config_ as crococon

class SimpleBuilder:
    def get_config_template(self):
        config = crococon.Config()
        config["param1"] = "value1"
        return config
"""
        builder_file = os.path.join(scratch_dir, "simple_builder.py")
        hio.to_file(builder_file, builder_code)
        out_file = os.path.join(scratch_dir, "template.yaml")
        sys.path.insert(0, scratch_dir)
        try:
            # Create args.
            args = argparse.Namespace(
                builder="simple_builder.SimpleBuilder",
                out=out_file,
                log_level="INFO",
            )
            # Run test.
            exit_code = _config_script._cmd_template(args)
            # Check output.
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(out_file))
        finally:
            sys.path.pop(0)

    def test3(self) -> None:
        """
        Test error case: builder lacks get_config_template method.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        module_name = f"no_template_builder_{id(self)}"
        builder_code = """
class NoTemplateBuilder:
    pass
"""
        builder_file = os.path.join(scratch_dir, f"{module_name}.py")
        hio.to_file(builder_file, builder_code)
        sys.path.insert(0, scratch_dir)
        try:
            # Create args.
            args = argparse.Namespace(
                builder=f"{module_name}.NoTemplateBuilder",
                out=None,
                log_level="INFO",
            )
            # Run test and check exit code.
            exit_code = _config_script._cmd_template(args)
            # The script catches the exception and returns 3 when dfatal is called.
            # Check output - should not be 0 (success).
            self.assertNotEqual(exit_code, 0)
        finally:
            sys.path.pop(0)
            if module_name in sys.modules:
                del sys.modules[module_name]

    def test4(self) -> None:
        """
        Test error case: invalid class path format.
        """
        # Prepare inputs.
        args = argparse.Namespace(
            builder="InvalidClassPath",
            out=None,
            log_level="INFO",
        )
        # Run test and check exit code.
        exit_code = _config_script._cmd_template(args)
        # Check output.
        self.assertEqual(exit_code, 3)

    def test5(self) -> None:
        """
        Test error case: nonexistent module.
        """
        # Prepare inputs.
        args = argparse.Namespace(
            builder="nonexistent_module.ClassName",
            out=None,
            log_level="INFO",
        )
        # Run test and check exit code.
        exit_code = _config_script._cmd_template(args)
        # Check output.
        self.assertEqual(exit_code, 3)

    def test6(self) -> None:
        """
        Test error case: class doesn't exist in module.
        """
        # Prepare inputs.
        args = argparse.Namespace(
            builder="config_root.config.config_.NonexistentClass",
            out=None,
            log_level="INFO",
        )
        # Run test and check exit code.
        exit_code = _config_script._cmd_template(args)
        # Check output.
        self.assertEqual(exit_code, 3)


# #############################################################################
# Test_cmd_validate
# #############################################################################


class Test_cmd_validate(hunitest.TestCase):
    """
    Test the _cmd_validate command handler.
    """

    def test1(self) -> None:
        """
        Test happy path: valid config with no DUMMY.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["param1"] = "value1"
        yaml_text = _config_to_yaml(config)
        hio.to_file(config_file, yaml_text)
        args = argparse.Namespace(
            config=config_file,
            builder=None,
            dag=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_validate(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test2(self) -> None:
        """
        Test happy path: valid config with valid builder validation.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        builder_code = """
import config_root.config.config_ as crococon

class SimpleBuilder:
    def _validate_config_and_dag(self, config):
        pass
"""
        builder_file = os.path.join(scratch_dir, "simple_builder.py")
        hio.to_file(builder_file, builder_code)
        config = crococon.Config()
        config["param1"] = "value1"
        yaml_text = _config_to_yaml(config)
        hio.to_file(config_file, yaml_text)
        sys.path.insert(0, scratch_dir)
        try:
            args = argparse.Namespace(
                config=config_file,
                builder="simple_builder.SimpleBuilder",
                dag=None,
                log_level="INFO",
            )
            # Run test.
            exit_code = _config_script._cmd_validate(args)
            # Check output.
            self.assertEqual(exit_code, 0)
        finally:
            sys.path.pop(0)

    def test3(self) -> None:
        """
        Test happy path: config with DUMMY placeholders returns exit 1.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["param1"] = crococon.DUMMY
        yaml_text = _config_to_yaml(config)
        hio.to_file(config_file, yaml_text)
        args = argparse.Namespace(
            config=config_file,
            builder=None,
            dag=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_validate(args)
        # Check output.
        self.assertEqual(exit_code, 1)

    def test4(self) -> None:
        """
        Test error case: builder validation fails returns exit 2.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        module_name = f"failing_validator_{id(self)}"
        builder_code = f"""
import config_root.config.config_ as crococon

class FailingValidator:
    def _validate_config_and_dag(self, config):
        raise ValueError("Validation failed")
"""
        builder_file = os.path.join(scratch_dir, f"{module_name}.py")
        hio.to_file(builder_file, builder_code)
        config = crococon.Config()
        config["param1"] = "value1"
        yaml_text = _config_to_yaml(config)
        hio.to_file(config_file, yaml_text)
        sys.path.insert(0, scratch_dir)
        try:
            args = argparse.Namespace(
                config=config_file,
                builder=f"{module_name}.FailingValidator",
                dag=None,
                log_level="INFO",
            )
            # Run test.
            exit_code = _config_script._cmd_validate(args)
            # Check output - should not be 0 (the script catches exception and returns 2).
            self.assertNotEqual(exit_code, 0)
        finally:
            sys.path.pop(0)
            if module_name in sys.modules:
                del sys.modules[module_name]

    def test5(self) -> None:
        """
        Test error case: builder lacks validation method logs warning.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        builder_code = """
class SimpleBuilder:
    pass
"""
        builder_file = os.path.join(scratch_dir, "simple_builder.py")
        hio.to_file(builder_file, builder_code)
        config = crococon.Config()
        config["param1"] = "value1"
        yaml_text = _config_to_yaml(config)
        hio.to_file(config_file, yaml_text)
        sys.path.insert(0, scratch_dir)
        try:
            args = argparse.Namespace(
                config=config_file,
                builder="simple_builder.SimpleBuilder",
                dag=None,
                log_level="INFO",
            )
            # Run test.
            exit_code = _config_script._cmd_validate(args)
            # Check output.
            self.assertEqual(exit_code, 0)
        finally:
            sys.path.pop(0)

    def test6(self) -> None:
        """
        Test error case: config file not found returns exit 3.
        """
        # Prepare inputs.
        args = argparse.Namespace(
            config="/nonexistent/config.yaml",
            builder=None,
            dag=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_validate(args)
        # Check output.
        self.assertEqual(exit_code, 3)


# #############################################################################
# Test_cmd_merge
# #############################################################################


class Test_cmd_merge(hunitest.TestCase):
    """
    Test the _cmd_merge command handler.
    """

    def test1(self) -> None:
        """
        Test happy path: merge two configs to stdout.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        config2 = crococon.Config()
        config2["a"] = 10
        config2["b"] = 2
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            configs=[config1_file, config2_file],
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_merge(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test2(self) -> None:
        """
        Test happy path: merge two configs to file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        out_file = os.path.join(scratch_dir, "merged.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        config2 = crococon.Config()
        config2["a"] = 10
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            configs=[config1_file, config2_file],
            out=out_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_merge(args)
        # Check output.
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(out_file))

    def test3(self) -> None:
        """
        Test happy path: merge three configs.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config3_file = os.path.join(scratch_dir, "config3.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        config2 = crococon.Config()
        config2["a"] = 10
        config3 = crococon.Config()
        config3["a"] = 100
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        hio.to_file(config3_file, _config_to_yaml(config3))
        args = argparse.Namespace(
            configs=[config1_file, config2_file, config3_file],
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_merge(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test4(self) -> None:
        """
        Test happy path: verify left-to-right precedence.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        out_file = os.path.join(scratch_dir, "merged.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        config1["b"] = 2
        config2 = crococon.Config()
        config2["b"] = 20
        config2["c"] = 3
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            configs=[config1_file, config2_file],
            out=out_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_merge(args)
        # Check output and verify precedence.
        self.assertEqual(exit_code, 0)
        merged_yaml = hio.from_file(out_file)
        merged_config = _load_config_from_yaml(merged_yaml)
        self.assertEqual(merged_config["a"], 1)
        self.assertEqual(merged_config["b"], 20)
        self.assertEqual(merged_config["c"], 3)

    def test5(self) -> None:
        """
        Test happy path: nested config merging with overwrite.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        out_file = os.path.join(scratch_dir, "merged.yaml")
        config1 = crococon.Config()
        config1["model", "alpha"] = 0.01
        config2 = crococon.Config()
        config2["model", "alpha"] = 0.1
        config2["model", "beta"] = 0.5
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            configs=[config1_file, config2_file],
            out=out_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_merge(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test6(self) -> None:
        """
        Test error case: missing base config returns exit 3.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config2 = crococon.Config()
        config2["a"] = 10
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            configs=["/nonexistent/config1.yaml", config2_file],
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_merge(args)
        # Check output.
        self.assertEqual(exit_code, 3)

    def test7(self) -> None:
        """
        Test error case: missing override config returns exit 3.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        hio.to_file(config1_file, _config_to_yaml(config1))
        args = argparse.Namespace(
            configs=[config1_file, "/nonexistent/config2.yaml"],
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_merge(args)
        # Check output.
        self.assertEqual(exit_code, 3)


# #############################################################################
# Test_cmd_set
# #############################################################################


class Test_cmd_set(hunitest.TestCase):
    """
    Test the _cmd_set command handler.
    """

    def test1(self) -> None:
        """
        Test happy path: set simple string value.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="b",
            value="hello",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test2(self) -> None:
        """
        Test happy path: set nested key with dot notation.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["model", "name"] = "linear"
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="model.alpha",
            value="0.01",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test3(self) -> None:
        """
        Test happy path: type inference with JSON number.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1  # Initialize with at least one value.
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="count",
            value="123",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test4(self) -> None:
        """
        Test happy path: type inference with JSON boolean.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1  # Initialize with at least one value.
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="flag",
            value="true",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test5(self) -> None:
        """
        Test happy path: type inference with JSON list.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1  # Initialize with at least one value.
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="items",
            value="[1, 2, 3]",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test6(self) -> None:
        """
        Test error case: setting dict value raises error (Config needs nested Config).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1  # Initialize with at least one value.
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="data",
            value='{"a": 1}',
            out=None,
            log_level="INFO",
        )
        # Run test: Config requires nested Config, not dict.
        exit_code = _config_script._cmd_set(args)
        # Check output: should return 3 (error).
        self.assertEqual(exit_code, 3)

    def test7(self) -> None:
        """
        Test happy path: fallback to string when JSON parse fails.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1  # Initialize with at least one value.
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="text",
            value="not-valid-json",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test8(self) -> None:
        """
        Test happy path: output to new file with --out.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        out_file = os.path.join(scratch_dir, "config_out.yaml")
        config = crococon.Config()
        config["b"] = 2  # Initialize with at least one value.
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="a",
            value="1",
            out=out_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(out_file))

    def test9(self) -> None:
        """
        Test happy path: no --out overwrites original file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1
        hio.to_file(config_file, _config_to_yaml(config))
        original_mtime = os.path.getmtime(config_file)
        args = argparse.Namespace(
            config=config_file,
            key="a",
            value="10",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test10(self) -> None:
        """
        Test error case: config file not found returns exit 3.
        """
        # Prepare inputs.
        args = argparse.Namespace(
            config="/nonexistent/config.yaml",
            key="a",
            value="1",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 3)

    def test11(self) -> None:
        """
        Test happy path: set deeply nested key creates intermediate structures.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["x"] = 1  # Initialize with at least one value.
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="a.b.c.d",
            value="deep",
            out=None,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_set(args)
        # Check output.
        self.assertEqual(exit_code, 0)


# #############################################################################
# Test_cmd_get
# #############################################################################


class Test_cmd_get(hunitest.TestCase):
    """
    Test the _cmd_get command handler.
    """

    def test1(self) -> None:
        """
        Test happy path: get existing simple key.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="a",
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_get(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test2(self) -> None:
        """
        Test happy path: get existing nested key with dot notation.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["model", "alpha"] = 0.01
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="model.alpha",
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_get(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test3(self) -> None:
        """
        Test happy path: value printed with exit code 0.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["value"] = 42
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="value",
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_get(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test4(self) -> None:
        """
        Test error case: key not found returns exit 1.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "config.yaml")
        config = crococon.Config()
        config["a"] = 1
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            key="nonexistent",
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_get(args)
        # Check output.
        self.assertEqual(exit_code, 1)

    def test5(self) -> None:
        """
        Test error case: config file not found returns exit 3.
        """
        # Prepare inputs.
        args = argparse.Namespace(
            config="/nonexistent/config.yaml",
            key="a",
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_get(args)
        # Check output.
        self.assertEqual(exit_code, 3)


# #############################################################################
# Test_cmd_diff
# #############################################################################


class Test_cmd_diff(hunitest.TestCase):
    """
    Test the _cmd_diff command handler.
    """

    def test1(self) -> None:
        """
        Test happy path: identical configs.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config = crococon.Config()
        config["a"] = 1
        config["b"] = 2
        hio.to_file(config1_file, _config_to_yaml(config))
        hio.to_file(config2_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config1=config1_file,
            config2=config2_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_diff(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test2(self) -> None:
        """
        Test happy path: different values show diff.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        config1["b"] = 2
        config2 = crococon.Config()
        config2["a"] = 1
        config2["b"] = 20
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            config1=config1_file,
            config2=config2_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_diff(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test3(self) -> None:
        """
        Test happy path: missing keys show diff.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        config1["b"] = 2
        config2 = crococon.Config()
        config2["a"] = 1
        config2["c"] = 3
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            config1=config1_file,
            config2=config2_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_diff(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test4(self) -> None:
        """
        Test happy path: extra keys show diff.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        config2 = crococon.Config()
        config2["a"] = 1
        config2["b"] = 2
        config2["c"] = 3
        hio.to_file(config1_file, _config_to_yaml(config1))
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            config1=config1_file,
            config2=config2_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_diff(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test5(self) -> None:
        """
        Test error case: first config not found returns exit 3.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config2_file = os.path.join(scratch_dir, "config2.yaml")
        config2 = crococon.Config()
        config2["a"] = 1
        hio.to_file(config2_file, _config_to_yaml(config2))
        args = argparse.Namespace(
            config1="/nonexistent/config1.yaml",
            config2=config2_file,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_diff(args)
        # Check output.
        self.assertEqual(exit_code, 3)

    def test6(self) -> None:
        """
        Test error case: second config not found returns exit 3.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config1_file = os.path.join(scratch_dir, "config1.yaml")
        config1 = crococon.Config()
        config1["a"] = 1
        hio.to_file(config1_file, _config_to_yaml(config1))
        args = argparse.Namespace(
            config1=config1_file,
            config2="/nonexistent/config2.yaml",
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_diff(args)
        # Check output.
        self.assertEqual(exit_code, 3)


# #############################################################################
# Test_cmd_sweep
# #############################################################################


class Test_cmd_sweep(hunitest.TestCase):
    """
    Test the _cmd_sweep command handler.
    """

    def test1(self) -> None:
        """
        Test happy path: 2x2 grid generates 4 configs.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        config["model", "name"] = "linear"
        grid_data = {"model.alpha": [0.01, 0.1], "model.beta": [0.5, 1.0]}
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 0)
        # Verify 4 configs generated.
        config_files = [f for f in os.listdir(out_dir) if f.startswith("config_")]
        self.assertEqual(len(config_files), 4)

    def test2(self) -> None:
        """
        Test happy path: 2x2x2 grid generates 8 configs.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        config["x"] = 1  # Initialize with at least one value.
        grid_data = {
            "model.alpha": [0.01, 0.1],
            "model.beta": [0.5, 1.0],
            "data.size": [100, 1000],
        }
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 0)
        # Verify 8 configs generated.
        config_files = [f for f in os.listdir(out_dir) if f.startswith("config_")]
        self.assertEqual(len(config_files), 8)

    def test3(self) -> None:
        """
        Test happy path: output directory created fresh.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        config["x"] = 1  # Initialize with at least one value.
        grid_data = {"model.alpha": [0.01, 0.1]}
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(out_dir))

    def test4(self) -> None:
        """
        Test happy path: config files numbered correctly.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        config["x"] = 1  # Initialize with at least one value.
        grid_data = {"model.alpha": [0.01, 0.1, 0.2]}
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 0)
        # Verify numbering.
        self.assertTrue(os.path.exists(os.path.join(out_dir, "config_000.yaml")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "config_001.yaml")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "config_002.yaml")))

    def test5(self) -> None:
        """
        Test happy path: base config values preserved in sweep.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        config["model", "name"] = "linear"
        config["data", "path"] = "/tmp"
        grid_data = {"model.alpha": [0.01, 0.1]}
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output and verify base values preserved.
        self.assertEqual(exit_code, 0)

    def test6(self) -> None:
        """
        Test happy path: grid parameters override base config values.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        config["model", "alpha"] = 0.01
        grid_data = {"model.alpha": [0.5, 1.0]}
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test7(self) -> None:
        """
        Test happy path: nested key paths in grid.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        config["x"] = 1  # Initialize with at least one value.
        grid_data = {"model.alpha": [0.01], "trainer.lr": [0.001]}
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 0)

    def test8(self) -> None:
        """
        Test error case: base config file not found returns exit 3.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        grid_data = {"model.alpha": [0.01]}
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config="/nonexistent/base.yaml",
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 3)

    def test9(self) -> None:
        """
        Test error case: grid file not found returns exit 3.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        config = crococon.Config()
        hio.to_file(config_file, _config_to_yaml(config))
        args = argparse.Namespace(
            config=config_file,
            grid="/nonexistent/grid.yaml",
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output.
        self.assertEqual(exit_code, 3)

    def test10(self) -> None:
        """
        Test error case: output directory exists with files (incremental=False).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        config_file = os.path.join(scratch_dir, "base.yaml")
        grid_file = os.path.join(scratch_dir, "grid.yaml")
        out_dir = os.path.join(scratch_dir, "sweep")
        # Create existing output directory with files.
        os.makedirs(out_dir)
        hio.to_file(os.path.join(out_dir, "existing.txt"), "data")
        config = crococon.Config()
        grid_data = {"model.alpha": [0.01]}
        hio.to_file(config_file, _config_to_yaml(config))
        hio.to_file(grid_file, yaml.dump(grid_data))
        args = argparse.Namespace(
            config=config_file,
            grid=grid_file,
            out_dir=out_dir,
            log_level="INFO",
        )
        # Run test.
        exit_code = _config_script._cmd_sweep(args)
        # Check output: should fail with exit 3 (incremental=False by default).
        self.assertEqual(exit_code, 3)
