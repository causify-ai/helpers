# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
# !sudo /bin/bash -c "(source /venv/bin/activate; pip install hydra-core omegaconf)"

# %%
# %load_ext autoreload
# %autoreload 2

import dataclasses
import enum
import logging
import os
import tempfile
from typing import Any, List

import hydra
import numpy as np
import omegaconf as omcfg
import pandas as pd

import helpers.hdbg as hdbg

# %%
hdbg.init_logger(verbosity=logging.INFO)

_LOG = logging.getLogger(__name__)

# %% [markdown]
# # OmegaConf

# %% [markdown]
# ## Create OmegaConf object

# %%
# From dictionary.
my_dict = {"server": {"host": "localhost", "port": 8080}}
cfg_dict = omcfg.OmegaConf.create(my_dict)
_LOG.info(cfg_dict)

# %%
# From YAML string.
yaml_string = """
database:
  user: root
  password: secret_password
"""
cfg_yaml = omcfg.OmegaConf.create(yaml_string)
_LOG.info(cfg_yaml)

# %%
# Empty config.
cfg_empty = omcfg.OmegaConf.create()
# Add keys dynamically.
cfg_empty.app_name = "pipeline_v1"
_LOG.info(cfg_empty)

# %% [markdown]
# ## Access patterns

# %%
data = {
    "pipeline": {
        "name": "daily_retrain",
        "steps": ["filter", "resample", "train"],
    },
    "hyperparameters": {"learning_rate": 0.01},
}
cfg = omcfg.OmegaConf.create(data)
_LOG.info(cfg)

# %%
# Dot notation.
_LOG.info(cfg.pipeline.name)
_LOG.info(cfg.pipeline.steps[0])

# %%
# Dictionary access.
_LOG.info(cfg["hyperparameters"]["learning_rate"])

# %%
# Safe access. By default there is no `batch_size` key, but the user can define a default value in case
# a key is missing.
key_name = "batch_size"
_LOG.info(cfg.hyperparameters.get(key_name))
_LOG.info(cfg.hyperparameters.get(key_name, 32))


# %% [markdown]
# ## Supported types


# %%
class RunMode(enum.Enum):
    TRAIN = "train"
    EVAL = "eval"
    TEST = "test"


# A dictionary containing ONLY supported types.
supported_data = {
    # Primitives
    "integer_val": 42,
    "float_val": 3.14159,
    "boolean_val": True,
    "string_val": "dataflow_pipeline",
    "none_val": None,
    # Collections.
    "list_val": [1, 2, 3],
    "dict_val": {"nested_key": "nested_value"},
    "tuple_val": (0, 1, 2),
    # Enums.
    "current_mode": RunMode.TRAIN,
}
cfg = omcfg.OmegaConf.create(supported_data)
_LOG.info(cfg)

# %%
# Note that as YAML does not support tuples, OmegaConf converts tuples into lists.
_LOG.info(cfg.tuple_val)

# %%
# It throws an error when assigning values of unsupported types.
unsupported_data = {"timestamp": pd.Timestamp("2020-01-01")}
try:
    cfg = omcfg.OmegaConf.create(unsupported_data)
except omcfg.errors.UnsupportedValueType as e:
    _LOG.info("Error Type: %s", type(e).__name__)
    _LOG.info("Error Message: %s", e)

# %% [markdown]
# ## DictConfig vs ListConfig

# %%
# DictConfig: key, value pairs.
dict_data = {"model": "resnet", "layers": 50}
cfg_dict = omcfg.OmegaConf.create(dict_data)
_LOG.info(type(cfg_dict))
_LOG.info(cfg_dict["layers"])

# %%
# ListConfig (Ordered Sequence).
list_data = ["accuracy", "f1_score", "loss"]
cfg_list = omcfg.OmegaConf.create(list_data)
# Access ListConfig strictly using integer index.
_LOG.info(type(cfg_list))
_LOG.info(cfg_list[0])

# %% [markdown]
# ## Variable interpolation

# %%
# Set a dummy environment variable for the sake of the tutorial.
os.environ["PIPELINE_ENV"] = "production"
yaml_data = """
# 1. Base Variables.
server:
  host: "10.0.0.1"
  port: 8080

# 2. Internal Interpolation (referencing other keys).
database:
  # This points directly to server.host above!
  connection_url: "jdbc:mysql://${server.host}:${server.port}/my_db"

# 3. Environment Variable Interpolation.
# Fetches variables straight from your OS
execution:
  mode: "${oc.env:PIPELINE_ENV}"

# 4. Relative Interpolation.
# One can reference relative to the current node using dots
metrics:
  base_dir: "/logs"
  # '.' means look in the current 'metrics' block
  training_log: "${.base_dir}/train.csv"
"""
# OmegaConf uses "lazy" evaluation, meaning that interpolation is evaluated at the moment the
# user accesses a key.
cfg = omcfg.OmegaConf.create(yaml_data)
_LOG.info(cfg)

# %%
_LOG.info("Connection URL: %s", cfg.database.connection_url)
_LOG.info("Execution Mode: %s", cfg.execution.mode)
_LOG.info("Training Log: %s", cfg.metrics.training_log)

# %%
# If we change the base host, the connection URL automatically updates.
cfg.server.host = "192.168.1.100"
_LOG.info("Updated connection URL: %s", cfg.database.connection_url)

# %% [markdown]
# ## Read-only mode & missing values

# %%
# '???' means this key must be filled in before it is accessed.
yaml_data = """
training:
  batch_size: 32
  dataset_path: ???
"""
cfg = omcfg.OmegaConf.create(yaml_data)
try:
    _LOG.info(cfg.training.dataset_path)
except omcfg.errors.MissingMandatoryValue as e:
    _LOG.info("Error Type: %s", type(e).__name__)
    _LOG.info("Error Message: %s", e)

# %%
# Struct mode locks config structure, i.e., does not allow creating new keys.
omcfg.OmegaConf.set_struct(cfg, True)
try:
    # Try to add a new key.
    cfg.training.sample_size = 64
except omcfg.errors.ConfigAttributeError as e:
    _LOG.info("Error Type: %s", type(e).__name__)
    _LOG.info("Error Message: %s", e)

# %%
# But modifying an existing key still works perfectly in struct mode
cfg.training.batch_size = 64
_LOG.info("Updated batch_size to: %s", cfg.training.batch_size)

# %%
# Freeze the config completely, i.e. also prevent from modifying existing key values.
omcfg.OmegaConf.set_readonly(cfg, True)
try:
    # Try to modify an existing key.
    cfg.training.batch_size = 128
except omcfg.errors.ReadonlyConfigError as e:
    _LOG.info("Error Type: %s", type(e).__name__)
    _LOG.info("Error Message: %s", e)

# %% [markdown]
# ## Structured configs

# %%
# Tell OmegaConf how to turn a string into a pd.Timestamp by registiring a custom solver.
omcfg.OmegaConf.register_new_resolver(
    "to_timestamp", lambda s: pd.Timestamp(s), replace=True
)


# %%
# Define the Schema using 'Any' for complex types.
@dataclasses.dataclass
class MarketFilterSchema:
    filter_name: str = "ath_filter"
    col_mode: str = "replace_all"
    start_time: Any = None
    end_time: Any = None


# %%
# If building the config purely in Python, the user can just assign a timestamp using
# the resolver syntax.
cfg_python = omcfg.OmegaConf.structured(MarketFilterSchema)
cfg_python.start_time = "${to_timestamp:2026-05-08 10:00:00}"
_LOG.info(type(cfg_python.start_time))
_LOG.info(cfg_python.start_time)

# %%
# If loading from a YAML file, use the resolver syntax.
yaml_data = """
filter_name: "custom_market_hours"
start_time: "${to_timestamp:2026-05-07 09:30:00}"
end_time: "${to_timestamp:2026-05-07 16:00:00}"
"""
# Merge the strict schema with the incoming YAML data.
cfg_yaml = omcfg.OmegaConf.merge(
    omcfg.OmegaConf.structured(MarketFilterSchema),
    omcfg.OmegaConf.create(yaml_data),
)
_LOG.info("Type loaded from YAML: %s", type(cfg_yaml.start_time))
_LOG.info(
    "Value: %s, %s", cfg_yaml.start_time.day_name(), cfg_yaml.start_time.time()
)

# %% [markdown]
# ## Merging configs

# %%
# Base configuration.
base_yaml = """
pipeline:
  name: "default_dag"
  retries: 3

model:
  type: "linear"
  # A list of features to use.
  features: ["close", "volume", "vwap"]
"""
# Overrides.
experiment_yaml = """
pipeline:
  # Overrides the name, but leaves 'retries' alone.
  name: "weekend_experiment_dag"

model:
  # Drop 'vwap' and just use 'close' and 'volume'.
  features: ["close", "volume"]
"""
cfg_base = omcfg.OmegaConf.create(base_yaml)
cfg_user = omcfg.OmegaConf.create(experiment_yaml)
# Merging configs.
merged_cfg = omcfg.OmegaConf.merge(cfg_base, cfg_user)
_LOG.info((omcfg.OmegaConf.to_yaml(merged_cfg)))

# %% [markdown]
# ## Serialization

# %%
# Register the resolver.
omcfg.OmegaConf.register_new_resolver(
    "to_timestamp", lambda s: pd.Timestamp(s), replace=True
)


# Define the strict schema.
@dataclasses.dataclass
class MarketFilterSchema:
    filter_name: str = "custom_market_hours"
    start_time: Any = None
    end_time: Any = None


# Incoming YAML data using the resolver syntax.
yaml_data = """
filter_name: "custom_market_hours"
start_time: "${to_timestamp:2026-05-07 09:30:00}"
end_time: "${to_timestamp:2026-05-07 16:00:00}"
"""
# Create the config.
cfg_original = omcfg.OmegaConf.merge(
    omcfg.OmegaConf.structured(MarketFilterSchema),
    omcfg.OmegaConf.create(yaml_data),
)
# Verify the original has a real Timestamp.
_LOG.info("Original Type before saving: %s", type(cfg_original.start_time))
# The File I/O test.
with tempfile.NamedTemporaryFile(suffix=".yaml") as fp:
    # SAVE: We use resolve=False (default). This saves the string "${to_timestamp:...}" because
    # we cannot save `pd.Timestamp` to YAML.
    omcfg.OmegaConf.save(config=cfg_original, f=fp.name, resolve=False)
    # LOAD: OmegaConf reads the YAML string back into memory.
    cfg_loaded = omcfg.OmegaConf.load(fp.name)
    # Verify the loaded config still correctly builds the Pandas object.
    _LOG.info("Loaded Type from file: %s", type(cfg_loaded.start_time))
    _LOG.info(
        "Loaded Value: %s %s",
        cfg_loaded.start_time.day_name(),
        cfg_loaded.start_time.time(),
    )
    # Assertions.
    assert cfg_original == cfg_loaded

# %% [markdown]
# # Hydra

# %% [markdown]
# Hydra works mainly with CLI, so showing only a few basic examples in the current Jupyter notebook.

# %% [markdown]
# ## Instantiate

# %%
yaml_config = """
my_node:
  _target_: sklearn.preprocessing.FunctionTransformer
  validate: false
  # Hydra will evaluate this inner block first, grab the numpy function,
  # and pass it directly to the 'func' argument of FunctionTransformer.
  func:
    _target_: hydra.utils.get_method
    path: numpy.log1p
"""
cfg = omcfg.OmegaConf.create(yaml_config)
# A single call to instantiate() handles the entire nested tree.
transformer = hydra.utils.instantiate(cfg.my_node)
_LOG.info("Built Object: %s", type(transformer))
_LOG.info("Injected Function: %s", transformer.func.__name__)
_LOG.info(cfg)

# %%
# Prove it actually works by passing in some dummy data.
data = np.array([[0.0, 1.0], [2.0, 3.0]])
# We call the class we just built.
result = transformer.transform(data)
_LOG.info("Original Data:\n %s", data)
_LOG.info("Transformed Data (log1p):\n %s", result)

# %%
# Notice the _partial_: true flag.
yaml_config = """
data_splitter:
  _target_: sklearn.model_selection.train_test_split
  _partial_: true
  test_size: 0.25
  random_state: 42
"""
cfg = omcfg.OmegaConf.create(yaml_config)
# Instantiate does not run the split. It returns a 'partial' object.
# The test_size and random_state are "baked in" to this object.
splitter_func = hydra.utils.instantiate(cfg.data_splitter)
_LOG.info("Type: %s", type(splitter_func))
_LOG.info("Baked-in keyword arguments: %s", splitter_func.keywords)

# %%
# We call the partial function and pass the missing runtime argument.
my_live_data = np.array([10, 20, 30, 40, 50, 60, 70, 80])
train_data, test_data = splitter_func(my_live_data)
_LOG.info("Original Data: %s", my_live_data)
_LOG.info("Train Split: %s", train_data)
_LOG.info("Test Split: %s", test_data)

# %% [markdown]
# ## Grouped configs

# %%
# Reset the state.
hydra.core.global_hydra.GlobalHydra.instance().clear()
config_path = "../config_example1"
with hydra.initialize(version_base=None, config_path=config_path):
    # Load the default composition (it should pull in 'linear.yaml').
    cfg_default = hydra.compose(config_name="base_config")
    _LOG.info("Default config: %s", omcfg.OmegaConf.to_yaml(cfg_default))
    # Swap the model group dynamically. By passing "model=rf", Hydra ignores
    # 'linear.yaml' and injects 'rf.yaml' instead.
    cfg_rf = hydra.compose(config_name="base_config", overrides=["model=rf"])
    _LOG.info("Overriden config: %s", omcfg.OmegaConf.to_yaml(cfg_rf))


# %% [markdown]
# ## ConfigStore


# %%
# Define base shapes.
@dataclasses.dataclass
class ModelConfig:
    name: str = "base_model"


@dataclasses.dataclass
class LinearModelConfig(ModelConfig):
    name: str = "Linear Regression"
    learning_rate: float = 0.01


@dataclasses.dataclass
class XGBoostModelConfig(ModelConfig):
    name: str = "XGBoost"
    n_estimators: int = 100


@dataclasses.dataclass
class PipelineConfig:
    defaults: List[Any] = dataclasses.field(
        default_factory=lambda: [{"model": "linear"}, "_self_"]
    )
    pipeline_name: str = "memory_pipeline"
    model: ModelConfig = omcfg.MISSING


# Get the global ConfigStore instance.
cs = hydra.core.config_store.ConfigStore.instance()
cs.store(name="my_main_config", node=PipelineConfig)
# Register the swappable components into a virtual 'model' group.
cs.store(group="model", name="linear", node=LinearModelConfig)
cs.store(group="model", name="xgboost", node=XGBoostModelConfig)
hydra.core.global_hydra.GlobalHydra.instance().clear()
# Instead of reading config from files, we read them from memory by setting `config_path`
# to None.
with hydra.initialize(version_base=None, config_path=None):
    # We tell it to load our main config, and we inject the xgboost model from the virtual group.
    cfg = hydra.compose(
        config_name="my_main_config",
        overrides=["model=xgboost", "pipeline_name=no_yaml_needed"],
    )
    _LOG.info(omcfg.OmegaConf.to_yaml(cfg))
