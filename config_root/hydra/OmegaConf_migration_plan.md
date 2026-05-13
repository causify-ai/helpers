# OmegaConf Migration Plan

## Executive Summary

This document describes the migration from the custom `Config` class to Hydra/OmegaConf for configuration management across the platform. 

## Port DagBuilders

DagBuilders are the first component being migrated, serving as the reference implementation for patterns that will be applied to other parts of the codebase.

### What Changed

Previously, DagBuilders used the custom `Config` class:
```python
def get_config_template(self) -> cconfig.Config:
    dict_ = {
        self._get_nid("filter_ath"): {
            "transformer_kwargs": {
                "start_time": datetime.time(9, 30),
                "end_time": datetime.time(16, 0),
            },
        },
    }
    config = cconfig.Config.from_dict(dict_)
    return config

def _get_dag(self, config: cconfig.Config, mode: str = "strict") -> dtfcore.DAG:
    dag = dtfcore.DAG(mode=mode)
    node = dtfcore.ColumnTransformer(
        nid,
        transformer_func=cofinanc.set_non_ath_to_nan,
        **config[nid].to_dict(),
    )
    dag.append_to_tail(node)
    return dag
```

Now, DagBuilders use OmegaConf with custom resolvers:
```python
# Module-level resolver registration
omcfg.OmegaConf.register_new_resolver(
    "to_time",
    lambda s: datetime.datetime.strptime(s, "%H:%M").time(),
    replace=True
)

omcfg.OmegaConf.register_new_resolver(
    "builtin",
    lambda name: getattr(builtins, name),
    replace=True
)

def as_tuple(*args: Any) -> dict:
    """Generate Hydra recipe to build a real Python tuple."""
    return {"_target_": "builtins.tuple", "_args_": [list(args)]}

def get_config_template(self) -> omcfg.DictConfig:
    dict_ = {
        self._get_nid("filter_ath"): {
            "transformer_kwargs": {
                "start_time": "${to_time:09:30}",  # Resolver converts string → datetime.time
                "end_time": "${to_time:16:00}",
            },
        },
        self._get_nid("resample"): {
            "in_col_groups": [
                as_tuple("close"),  # Creates _target_ recipe for tuple
                as_tuple("volume"),
            ],
            "permitted_exceptions": as_tuple("${builtin:ValueError}"),
        },
        self._get_nid("predict"): {
            "transformer_kwargs": {
                "weights": {
                    "_target_": "pandas.Series",  # Instantiation pattern
                    "data": [-0.209, -0.223, 0.304, -0.264],
                    "index": ["lag0", "lag1", "lag2", "lag3"],
                    "name": "prediction",
                },
            },
        },
    }
    config = omcfg.OmegaConf.create(dict_)  # Create unstructured config
    return config

def _get_dag(self, config: omcfg.DictConfig, mode: str = "strict") -> dtfcore.DAG:
    resolved_config = hydutil.instantiate(config, _convert_="all")  # Resolves everything!
    dag = dtfcore.DAG(mode=mode)
    node = dtfcore.ColumnTransformer(
        nid,
        transformer_func=cofinanc.set_non_ath_to_nan,
        **resolved_config[nid],  # Use resolved config directly
    )
    dag.append_to_tail(node)
    return dag
```

### Key Patterns

#### 1. Custom Resolvers for Non-Primitive Types

**Problem:** OmegaConf only natively supports primitives (str, int, float, bool, list, dict). We need datetime.time, exception types, and other Python objects.

**Solution:** Custom resolvers that convert strings to Python objects at resolution time.

```python
# Datetime resolver
"${to_time:09:30}" → datetime.time(9, 30)

# Builtin types resolver
"${builtin:ValueError}" → ValueError (the class itself)
```

#### 2. The `_target_` Instantiation Pattern

**Problem:** We need to create complex Python objects (tuples, pd.Series, custom classes) from configuration.

**Solution:** Hydra's `_target_` pattern + `hydra.utils.instantiate()`.

```python
# Tuples
as_tuple("close", "volume") → {
    "_target_": "builtins.tuple",
    "_args_": [["close", "volume"]]
}

# pandas.Series
{
    "_target_": "pandas.Series",
    "data": [1, 2, 3],
    "index": ["a", "b", "c"],
    "name": "my_series"
}
```

When you call `hydutil.instantiate(config, _convert_="all")`, Hydra:
1. Resolves all `${}` expressions
2. Finds all `_target_` keys
3. Imports the target class/function
4. Calls it with the provided arguments
5. Returns fully instantiated Python objects

#### 3. Resolution Timing

**Critical concept:** Configuration resolution happens in two phases:

1. **Config creation** (`get_config_template()`): Creates OmegaConf DictConfig with unresolved strings like `"${to_time:09:30}"`
2. **Config resolution** (`_get_dag()`): Calls `hydutil.instantiate()` which resolves all expressions and creates Python objects

This separation is powerful because:
- Configs can be inspected, serialized, and overridden before resolution
- CLI overrides work on the unresolved config
- Resolution only happens when needed (lazy evaluation)

### Why This Approach?

We considered two approaches:

#### Option 1: YAML Files + Python Topology (Rejected for Now)
```yaml
# conf/pipelines/mock1_dag.yaml
filter_ath:
  transformer_kwargs:
    start_time: "09:30"
    end_time: "16:00"
```

```python
# mock1_pipeline.py - only topology, no config
def _get_dag(self, config: omcfg.DictConfig):
    node = dtfcore.ColumnTransformer(...)  # Config loaded from YAML
```

**Problem:** DAG definition is split across two files:
- Configuration in YAML
- Topology (node order, connections) in Python

For complex pipelines, you need to read both files to understand the full DAG. This cognitive overhead outweighs the benefits for simple to medium pipelines.


#### Option 2: OmegaConf in Python (Current Approach)
```python
config = omcfg.OmegaConf.create(dict_)  # OmegaConf, but still in Python
```

**Benefits:**
- **Single file**: Both config and topology in one place
- **Gradual migration**: Can move to YAML later without changing logic
- **Hydra-ready**: Using OmegaConf + resolvers + instantiate prepares code for Phase 2
- **Developer velocity**: Researchers can read one file to understand the pipeline
- **Type-rich**: Support for datetime.time, pd.Series, tuples, exception types

**Trade-off:** Still writing config in Python instead of YAML, but this is intentional for maintainability at our current scale.

### Recommended Shared Library

To support OmegaConf usage across the platform, we provide a reusable resolver and helper library at `helpers_root/config_root/hydra/resolvers.py`:

```python
# helpers_root/config_root/hydra/resolvers.py
"""
Shared OmegaConf resolvers and helpers for platform-wide configuration management.

Import as:
    import config_root.hydra.resolvers as crhresol
"""

import builtins
import datetime
from typing import Any
import omegaconf as omcfg


def register_resolvers():
    """
    Register all OmegaConf resolvers for the platform.

    Call this once at module initialization before using any configs.

    Registered resolvers:
    - to_time: Convert string to datetime.time (e.g., "${to_time:09:30}")
    - builtin: Access Python builtin types (e.g., "${builtin:ValueError}")
    """
    # Datetime resolver
    omcfg.OmegaConf.register_new_resolver(
        "to_time",
        lambda s: datetime.datetime.strptime(s, "%H:%M").time(),
        replace=True,
    )

    # Builtin types resolver
    omcfg.OmegaConf.register_new_resolver(
        "builtin",
        lambda name: getattr(builtins, name),
        replace=True,
    )


def as_tuple(*args: Any) -> dict:
    """
    Generate Hydra recipe to build a real Python tuple.

    This helper creates a configuration dict that Hydra will instantiate
    as a tuple when hydra.utils.instantiate() is called.

    :param args: Elements to include in the tuple
    :return: Dict with _target_ key for Hydra instantiation

    Example:
        as_tuple("close", "volume")
        → {"_target_": "builtins.tuple", "_args_": [["close", "volume"]]}

        # After hydra.utils.instantiate():
        → ("close", "volume")
    """
    return {"_target_": "builtins.tuple", "_args_": [list(args)]}
```

**Usage Example:**
```python
import config_root.hydra.resolvers as crhresol
import omegaconf as omcfg
import hydra.utils as hydutil

# Register resolvers once at module level
crhresol.register_resolvers()

def create_config() -> omcfg.DictConfig:
    """Create configuration using resolvers and helpers."""
    dict_ = {
        "data_source": {
            # Use datetime resolver
            "start_time": "${to_time:09:30}",
            "end_time": "${to_time:16:00}",
            # Use tuple helper
            "columns": [
                crhresol.as_tuple("close", "volume"),
                crhresol.as_tuple("high", "low"),
            ],
            # Use builtin resolver
            "allowed_errors": crhresol.as_tuple("${builtin:ValueError}"),
        },
        "model": {
            # Use _target_ for custom objects
            "weights": {
                "_target_": "pandas.Series",
                "data": [0.5, 0.3, 0.2],
                "index": ["a", "b", "c"],
            },
        },
    }
    return omcfg.OmegaConf.create(dict_)

def use_config():
    """Demonstrate config resolution."""
    config = create_config()

    # At this point, config contains unresolved strings:
    # config.data_source.start_time = "${to_time:09:30}"

    # Resolve all expressions and instantiate objects
    resolved = hydutil.instantiate(config, _convert_="all")

    # Now we have actual Python objects:
    # resolved.data_source.start_time = datetime.time(9, 30)
    # resolved.data_source.columns[0] = ("close", "volume")
    # resolved.model.weights = pd.Series([0.5, 0.3, 0.2], index=["a", "b", "c"])
```

### Long-Term Vision: Three Phases

The current approach (Phase 0) is pragmatic, but Hydra's true power emerges through three evolutionary phases.

The main idea is to re-think the `DagBuilder` pattern which currently defines:
- per-node DAG configuration
- DAG topology 

With Hydra's capabilities it is natural to move configuration to YAML files instead of having it as Python code. However, then the problem is that we have configuration in a YAML file but DAG topology is still inside Python (i.e., `DagBuilder._get()`). We may want to consider defining a DAG purely using a YAML file.

TODO(Grisha): think this through more carefully.

#### Phase 1: The YAML Migration 

**Goal:** Move static configuration out of Python into YAML files.

**What Changes:**

1. Delete `get_config_template()` from Python
2. Create YAML config files: `conf/pipelines/mock1_dag.yaml`
3. Python contains only execution logic (_get_dag)

**Before (Python):**
```python
# mock1_pipeline.py
def get_config_template(self) -> omcfg.DictConfig:
    dict_ = {
        self._get_nid("resample"): {
            "transformer_kwargs": {"rule": "5T"},
        },
    }
    return omcfg.OmegaConf.create(dict_)
```

**After (YAML + Python):**
```yaml
# conf/pipelines/mock1_dag.yaml
resample:
  transformer_kwargs:
    rule: 5T
```

```python
# mock1_pipeline.py
# get_config_template() deleted

@hydra.main(config_path="conf/pipelines", config_name="mock1_dag")
def main(config: omcfg.DictConfig):
    builder = Mock1_DagBuilder()
    dag = builder._get_dag(config)
```

**Benefits:**

1. **Researcher-friendly:** No Python knowledge required to understand/modify hyperparameters
2. **CLI overrides:** `python main.py resample.transformer_kwargs.rule=10T`
3. **Parameter sweeps:** Test 50 different timeframes without code changes
   ```bash
   python main.py --multirun resample.transformer_kwargs.rule=1T,5T,10T,30T,1H
   ```
4. **Version control:** Clear diffs for config changes
5. **Environment-specific configs:** dev.yaml, prod.yaml, backtest.yaml


#### Phase 2: Modular Node Composition 

**Goal:** Break configs into reusable component libraries.

**Problem:** Mock2 shares 80% of nodes with Mock1. Currently, we copy-paste the entire config.

**What Changes:**

Create a library of reusable node configs with Hydra's defaults list.

**Directory Structure:**
```
conf/
├── pipelines/
│   ├── mock1_dag.yaml
│   └── mock2_dag.yaml
└── nodes/
    ├── filter_ath/
    │   ├── standard.yaml    # 09:30-16:00
    │   └── extended.yaml    # 04:00-20:00
    ├── resample/
    │   ├── 1T_bars.yaml
    │   ├── 5T_bars.yaml
    │   └── 1H_bars.yaml
    └── predict/
        ├── static_weights.yaml
        └── xgboost_model.yaml
```

**Config Composition:**
```yaml
# conf/pipelines/mock1_dag.yaml
defaults:
  - /nodes/filter_ath/standard@filter_ath
  - /nodes/resample/5T_bars@resample
  - /nodes/compute_ret_0@compute_ret_0
  - /nodes/predict/static_weights@predict
  - _self_

# Pipeline-specific overrides
resample:
  reindex_like_input: false
```

**Runtime Composition:**
```bash
# Use different resample frequency
python main.py pipeline=mock1_dag resample=1H_bars

# Swap prediction method
python main.py pipeline=mock1_dag predict=xgboost_model

# Compose on the fly
python main.py \
  pipeline=mock1_dag \
  filter_ath=extended \
  resample=1H_bars \
  predict=xgboost_model
```

**Benefits:**

1. **DRY Principle:** Define each node type once, reuse everywhere
2. **Mix and match:** Swap components without touching code
3. **A/B testing:** Compare prediction methods by changing one argument
4. **Team library:** Share well-tested node configs across projects
5. **Progressive refinement:** Start simple, add complexity only where needed

**Example - Researcher Workflow:**
```bash
# Baseline experiment
python main.py experiment=baseline

# Test faster resampling
python main.py experiment=baseline resample=1T_bars

# Test ML prediction
python main.py experiment=baseline predict=xgboost_model

# Multi-run sweep
python main.py --multirun \
  experiment=baseline \
  resample=1T_bars,5T_bars,10T_bars \
  predict=static_weights,xgboost_model
```

#### Phase 3: Data-Driven Topology 

**Goal:** Move DAG topology (node order, connections) into configuration.

**Current Problem:** `_get_dag()` hardcodes topology using `append_to_tail()`:
```python
def _get_dag(self, config: omcfg.DictConfig) -> dtfcore.DAG:
    dag = dtfcore.DAG()
    # Topology hardcoded in Python!
    dag.append_to_tail(filter_node)
    dag.append_to_tail(resample_node)
    dag.append_to_tail(compute_ret_node)
    return dag
```

**Solution:** Separate nodes (components) from edges (wiring) in config.

**YAML Configuration:**
```yaml
# conf/pipelines/branching_dag.yaml

# 1. THE COMPONENTS (unordered dictionary of nodes).
nodes:
  filter_ath:
    _target_: dtfcore.ColumnTransformer
    nid: filter_ath
    transformer_func:
      _target_: hydra.utils.get_method
      path: cofinanc.set_non_ath_to_nan
    col_mode: replace_all
    transformer_kwargs:
      start_time: "${to_time:09:30}"
      end_time: "${to_time:16:00}"

  generate_alpha_1:
    _target_: dtfcore.GroupedColDfToDfTransformer
    nid: generate_alpha_1
    transformer_func:
      _target_: hydra.utils.get_method
      path: cofeatur.compute_technical_indicators
    in_col_groups: [["${to_tuple:vwap}"]]
    # ... kwargs ...

  generate_alpha_2:
    _target_: dtfcore.GroupedColDfToDfTransformer
    nid: generate_alpha_2
    transformer_func:
      _target_: hydra.utils.get_method
      path: cofeatur.compute_momentum_features
    in_col_groups: [["${to_tuple:vwap}"]]
    # ... kwargs ...

  ensemble_predict:
    _target_: dtfcore.GroupedColDfToDfTransformer
    nid: ensemble_predict
    transformer_func:
      _target_: hydra.utils.get_method
      path: csigproc.compute_weighted_ensemble
    # ... kwargs ...

# 2. THE TOPOLOGY (explicit wiring).
edges:
  - [filter_ath, generate_alpha_1]    # Branch 1
  - [filter_ath, generate_alpha_2]    # Branch 2
  - [generate_alpha_1, ensemble_predict]  # Merge 1
  - [generate_alpha_2, ensemble_predict]  # Merge 2
```

**Universal Python Builder:**
```python
class UniversalDagBuilder(dtfcore.DagBuilder):

    def _get_dag(self, config: omcfg.DictConfig, mode: str = "strict") -> dtfcore.DAG:
        dag = dtfcore.DAG(mode=mode)

        # 1. Instantiate all nodes
        # Hydra builds all objects at once from config.nodes
        resolved_nodes = hydutil.instantiate(config.nodes, _convert_="all")
        # Result: {"filter_ath": ColumnTransformer(...),
        #          "generate_alpha_1": GroupedColDfToDfTransformer(...), ...}

        # 2. Add nodes to graph
        for nid, node_object in resolved_nodes.items():
            dag.add_node(node_object)

        # 3. Wire topology from edge list
        for parent_nid, child_nid in config.edges:
            dag.add_edge(parent_nid, child_nid)

        return dag
```

**Benefits:**

1. **Topology swapping:** Test if a feature branch is useful by commenting out 2 lines in YAML
2. **Complex DAGs:** Branching, merging, multi-path execution without Python complexity
3. **Visual tools:** Generate DAG diagrams directly from YAML
4. **A/B topologies:** Compare different pipeline structures
5. **Library reuse:** Import node definitions from shared library, arrange uniquely

**Real-World Example:**
```bash
# Test removing alpha_2 from ensemble
# Just edit YAML, comment out 2 edges:
# - [filter_ath, generate_alpha_2]
# - [generate_alpha_2, ensemble_predict]

python main.py pipeline=branching_dag

# Compare 3-feature vs 2-feature ensemble automatically
python main.py --multirun pipeline=branching_dag,branching_dag_no_alpha2
```

### Execution plan

1. Install `OmegaConf` and `Hydra` to the main Docker container 
2. Prepare instructions for ClaudeCode to update the entire codebase using Mock1DagBuilder as a reference
3. Update the `csfy` repo first
4. We may need to re-encrypt some models in the `orange` repo
5. Update `DagBuilders` in `lemonade`
6. Make sure all the tests pass

## Porting System Classes to OmegaConf

System classes follow similar patterns to DagBuilders but manage entire ML systems composed of multiple components (MarketData, DAG, Portfolio, Broker, DagRunner). However, Systems introduce critical architectural challenges that require paradigm shifts.

### Removing Config-Specific Patterns

#### 1. Compound Key Access

**Current Config pattern:**
```python
# Compound tuple keys for nested access
system.config["market_data_config", "asset_ids"] = [101, 102]
system.config["dag_config", "resample", "transformer_kwargs", "rule"] = "5T"

# Reading compound keys
asset_ids = system.config["market_data_config", "asset_ids"]
rule = system.config["dag_config", "resample", "transformer_kwargs", "rule"]
```

**Problem:** OmegaConf doesn't support tuple-based compound keys. This is a Config-specific feature for navigating nested dictionaries.

**OmegaConf replacement:**
```python
# Dot notation (preferred - clean and Pythonic)
system.config.market_data_config.asset_ids = [101, 102]
system.config.dag_config.resample.transformer_kwargs.rule = "5T"

# Reading with dot notation
asset_ids = system.config.market_data_config.asset_ids
rule = system.config.dag_config.resample.transformer_kwargs.rule

# Or bracket notation (when keys have special characters or are dynamic)
system.config["market_data_config"]["asset_ids"] = [101, 102]
asset_ids = system.config["market_data_config"]["asset_ids"]
```

#### 2. Removing `get_and_mark_as_used()`

**Current Config pattern:**
```python
class DagBuilder:
    def get_trading_period(
        self, config: cconfig.Config, mark_key_as_used: bool
    ) -> str:
        # Get value and mark it as "used"
        key = ("dag_config", "resample", "transformer_kwargs", "rule")
        val: str = config.get_and_mark_as_used(
            key, mark_key_as_used=mark_key_as_used
        )
        return val

```

**Problem:** OmegaConf doesn't have built-in usage tracking. The `.get_and_mark_as_used()` method and `mark_key_as_used` pattern are Config-specific.

**Remove usage tracking (simplest)**
```python
class DagBuilder:
    def get_trading_period(self, config: omcfg.DictConfig) -> str:
        # Direct access without tracking
        val: str = config.dag_config.resample.transformer_kwargs.rule
        return val
```

**Pros:**
- Simplest migration
- OmegaConf provides missing key errors by default
- Structured configs provide type validation

**Cons:**
- Lose ability to detect unused keys
- No explicit validation that all config was consumed

### Rethinking "Example" Functions

The codebase contains many "example" functions like `get_Mock1_NonTime_ForecastSystem_for_simulation_example1()` and `get_Mock1_HistoricalDag_example1()`. Their purpose is to **hard-wire specific parameter values** for common use cases (tests, simulations, specific configurations).

TODO(Grisha): check if this would work.

**Current pattern:**
```python
def get_Mock1_NonTime_ForecastSystem_for_simulation_example1(
    backtest_config: str,
) -> dtfsys.NonTime_ForecastSystem:
    # 1. Instantiate System (gets base config template)
    system = dasmmfosy.Mock1_NonTime_ForecastSystem()

    # 2. Hard-wire specific params for this "example"
    system.config["backtest_config", "freq_as_pd_str"] = "M"
    system.config["backtest_config", "lookback_as_pd_str"] = "10D"

    # 3. Build complex objects in Python
    vendor = "mock1"
    universe = ivcu.get_vendor_universe(vendor, mode="trade", version="v1")
    df = cofinanc.get_MarketData_df6(universe)
    system.config["market_data_config", "im_client_ctor"] = icdc.get_DataFrameClient_example1
    system.config["market_data_config", "im_client_config"] = cconfig.Config().from_dict({"df": df})

    return system
```

**Key insight:** Example functions are essentially **config overlays** - they take a base template and add/override specific values for a particular use case.

**Problem:** With Hydra/OmegaConf, these functions become redundant because we have better, more declarative patterns available.

#### Alternative Approaches

**Option 1: YAML Config Files (Most Hydra-native)**

Move pure configuration to YAML files:

```yaml
# conf/systems/mock1_simulation_example1.yaml
backtest_config:
  freq_as_pd_str: M
  lookback_as_pd_str: 10D

market_data_config:
  vendor: mock1
  mode: trade
  universe_version: v1
```

```python
# Simple factory using YAML overlay
def get_system_from_yaml(config_name: str) -> System:
    system = Mock1_NonTime_ForecastSystem()

    # Load overlay and merge with base template
    overlay = OmegaConf.load(f"conf/systems/{config_name}.yaml")
    system.config = OmegaConf.merge(system.config, overlay)

    # Python code only for non-serializable objects
    df = cofinanc.get_MarketData_df6(universe)
    system.config.market_data_config.im_client_config = OmegaConf.create({"df": df})

    return system

# Usage
system = get_system_from_yaml("mock1_simulation_example1")
```

**Or with Hydra's @hydra.main:**
```python
@hydra.main(config_path="conf/systems", config_name="mock1_simulation_example1")
def main(cfg: DictConfig):
    system = Mock1_NonTime_ForecastSystem()
    system.set_config(cfg)
    # Run system...
```

**Pros:**
- Declarative, easy to read/diff in version control
- CLI overrides: `python main.py backtest_config.freq_as_pd_str=Y`
- Hydra composition: Mix-and-match configs via defaults list
- No Python code to maintain for pure config

**Cons:**
- Can't handle Python objects (DataFrame, etc.) directly
- Requires keeping Python layer for object construction

**Option 2: Enrich `_get_system_config_template()` with Defaults**

Put reasonable defaults directly in the System template:

```python
class Mock1_NonTime_ForecastSystem:
    def _get_system_config_template(self) -> DictConfig:
        """Return config with sensible defaults for typical usage."""
        dag_builder = Mock1_DagBuilder()
        dag_config = dag_builder.get_config_template()

        dict_ = {
            # Backtest defaults
            "backtest_config": {
                "freq_as_pd_str": "M",
                "lookback_as_pd_str": "10D",
            },

            # Market data defaults
            "market_data_config": {
                "vendor": "mock1",
                "mode": "trade",
                "universe_version": "v1",
            },

            "dag_config": dag_config,
        }

        return OmegaConf.create(dict_)
```

**Usage:**
```python
# Just instantiate - already has good defaults
system = Mock1_NonTime_ForecastSystem()

# Override as needed
system.config.backtest_config.freq_as_pd_str = "Y"
```

**Pros:**
- Single source of truth
- No separate example functions
- Still overridable in Python or via Hydra

**Cons:**
- Mixes "template" with "concrete values"
- Multiple examples require multiple System classes or separate overlays

**Option 3: Config Builder Functions (Hybrid)**

Keep Python functions but return config overlays:

```python
def get_mock1_simulation_config() -> DictConfig:
    """Return config overlay for simulation example."""
    return OmegaConf.create({
        "backtest_config": {
            "freq_as_pd_str": "M",
            "lookback_as_pd_str": "10D",
        },
        "market_data_config": {
            "vendor": "mock1",
            "mode": "trade",
        },
    })

def get_mock1_realtime_config() -> DictConfig:
    """Return config overlay for realtime example."""
    return OmegaConf.create({
        "dag_runner_config": {
            "rt_timeout_in_secs_or_time": 600,
            "bar_duration_in_secs": 300,
        },
    })
```

**Usage:**
```python
system = Mock1_NonTime_ForecastSystem()
overlay = get_mock1_simulation_config()
system.config = OmegaConf.merge(system.config, overlay)
```

**Pros:**
- Can use Python logic to generate config
- Easy to handle Python objects (DataFrames, etc.)
- Composable (can merge multiple overlays)
- Test-friendly

**Cons:**
- Still Python code (not as declarative as YAML)
- Need to maintain separate builder functions

#### Recommended Migration Path

**Phase 0 (Current migration):**
Keep example functions but migrate to OmegaConf patterns:

```python
def get_Mock1_NonTime_ForecastSystem_for_simulation_example1() -> System:
    system = Mock1_NonTime_ForecastSystem()

    # Use dot notation instead of compound keys
    system.config.backtest_config.freq_as_pd_str = "M"
    system.config.backtest_config.lookback_as_pd_str = "10D"

    # Python objects still in Python
    df = cofinanc.get_MarketData_df6(universe)
    system.config.market_data_config.im_client_config = OmegaConf.create({"df": df})

    return system
```

**Phase 1 (YAML migration):**
Extract pure config to YAML, keep Python only for objects:

```yaml
# conf/systems/mock1_simulation_example1.yaml
backtest_config:
  freq_as_pd_str: M
  lookback_as_pd_str: 10D
market_data_config:
  vendor: mock1
  mode: trade
  universe_version: v1
```

```python
def get_Mock1_NonTime_ForecastSystem_for_simulation_example1() -> System:
    system = Mock1_NonTime_ForecastSystem()

    # Load and merge YAML overlay
    overlay = OmegaConf.load("conf/systems/mock1_simulation_example1.yaml")
    system.config = OmegaConf.merge(system.config, overlay)

    # Python only for non-serializable objects
    df = cofinanc.get_MarketData_df6(universe)
    system.config.market_data_config.im_client_config = OmegaConf.create({"df": df})

    return system
```

**Phase 2 (Full Hydra composition):**
Eliminate example functions entirely, use pure Hydra:

```bash
# CLI replaces example functions
python run_system.py \
  system=mock1_nontime \
  +backtest=simulation_example1 \
  +market_data=mock1_v1

# Or multi-run for parameter sweeps
python run_system.py --multirun \
  system=mock1_nontime \
  +backtest=simulation_example1,simulation_example2 \
  backtest_config.freq_as_pd_str=M,Y
```

```yaml
# conf/backtest/simulation_example1.yaml
backtest_config:
  freq_as_pd_str: M
  lookback_as_pd_str: 10D

# conf/market_data/mock1_v1.yaml
market_data_config:
  vendor: mock1
  mode: trade
  universe_version: v1
```

#### Component Examples (DAG, MarketData, etc.)

Same pattern applies to component builders:

**Current:**
```python
def get_Mock1_HistoricalDag_example1(
    system: dtfsys.System, timestamp_column_name: str
) -> dtfcore.DAG:
    dag_builder = system.config["dag_builder_object"]
    # Maybe hard-wire some dag_config params
    dag = dag_builder.get_dag(system.config["dag_config"])
    return dag
```

**Phase 0 migration:**
```python
def get_Mock1_HistoricalDag_example1(
    system: dtfsys.System, timestamp_column_name: str
) -> dtfcore.DAG:
    # Update config as overlay
    system.config.dag_config.some_node.timestamp_col = timestamp_column_name

    # Recreate builder from class name or config
    dag_builder = Mock1_DagBuilder()
    dag = dag_builder.get_dag(system.config.dag_config)
    return dag
```

**Phase 1 migration:**
```yaml
# conf/dags/mock1_historical_example1.yaml
some_node:
  timestamp_col: end_datetime
  other_param: hardcoded_value
```

```python
def get_Mock1_HistoricalDag_example1(system: dtfsys.System) -> dtfcore.DAG:
    # Load dag-specific overlay
    overlay = OmegaConf.load("conf/dags/mock1_historical_example1.yaml")
    dag_config = OmegaConf.merge(system.config.dag_config, overlay)

    dag_builder = Mock1_DagBuilder()
    dag = dag_builder.get_dag(dag_config)
    return dag
```

#### Key Principles

1. **Example functions = config overlays**: They add/override config values on top of base template
2. **Phase 0**: Keep functions, make them OmegaConf-compatible
3. **Phase 1**: Extract pure config to YAML, keep Python for objects
4. **Phase 2**: Eliminate functions, use Hydra composition exclusively
5. **Gradual migration**: Each phase delivers value, can stop at any point

This approach makes configurations:
- **More discoverable**: YAML files in conf/ directory vs scattered Python functions
- **More composable**: Mix-and-match via Hydra defaults
- **More maintainable**: Change configs without touching code
- **More flexible**: CLI overrides for any parameter

### Config as Blueprint vs State Container

**Critical Issue:** The current System implementation uses `Config` as both:
1. A configuration blueprint (parameters, settings)
2. A state container (storing built Python objects)

**Why this breaks with OmegaConf:**

```python
# Current pattern.
system = System()
system.config["dag_runner_object"] = dag_runner  # Live Python object.
system.config["market_object"] = market_data    # Live Python object.

# Try to serialize...
OmegaConf.to_yaml(system.config)  
system.config.save_to_file("config.yaml") 
```

OmegaConf is designed for **serializable data only** (strings, ints, lists, dicts). When you store live Python objects in the config and try to serialize to YAML, the serializer fails.

**The Solution: Separate Blueprint from State**

```python
class System:
    def __init__(self):
        # Pure configuration blueprint (serializable)
        self._config: DictConfig = self._get_system_config_template()

        # Live object cache (NOT serializable, but that's OK)
        self._object_cache: Dict[str, Any] = {}
```

**Key Principle:**
- `self._config` = Pure data blueprint, always serializable
- `self._object_cache` = Live Python objects (MarketData, DAG, Portfolio, DagRunner)

