# Config Module
Hierarchical configuration management system for building, validating, and
manipulating configuration objects across the platform.

## Directory Structure
- `notebooks/`
  - Gallery notebooks demonstrating Config and ConfigDict usage patterns and
    examples
- `test/`
  - Unit tests covering Config, ConfigList, ConfigBuilder, and ConfigListBuilder
    functionality

## Files

### Core Module Files
- `__init__.py`
  - Module initialization importing and re-exporting all public classes and
    functions

- `config_.py`
  - Core `Config` class for hierarchical, nested configuration management with
    compound key support

- `config_builder.py`
  - Utilities for dynamically building Config objects from Python code strings
    and module paths

- `config_list.py`
  - `ConfigList` class for managing ordered collections of Config objects with
    validation

- `config_list_builder.py`
  - Utilities for creating config lists with universe and time-period management
    and tiling

- `config_utils.py`
  - Helper functions for config validation, serialization, I/O, and comparison
    operations

### Documentation
- `config_example.txt`
  - Example configuration file demonstrating Config usage patterns and syntax

## Key Concepts

### Config Class
Provides hierarchical, nested configuration management with:

- Compound key access for nested values
- Write-after-use tracking to prevent accidental overwrites
- Serialization and deserialization support
- Deep copy capabilities

### ConfigList
Container for managing multiple Config objects:

- Validation to prevent duplicates
- Iterator support for batch processing
- Helper methods for single-config retrieval

### Config Builders
Dynamic configuration creation:

- `ConfigBuilder`: Execute Python strings to instantiate Config objects
- `ConfigListBuilder`: Generate config lists with universe definitions and time
  periods

## Usage
- Import the module:
  ```python
  import config_root.config as cconfig
  ```

- Create a config:
  ```python
  config = cconfig.Config()
  config["key1", "key2"] = value
  ```

- Build configs dynamically:
  ```python
  config_list = cconfig.get_config_list_from_builder("module.path.builder_function()")
  ```
