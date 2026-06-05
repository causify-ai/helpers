# Config Command Scripts

Command-line tools for managing hierarchical configuration objects.

## Files

- `config`: Main CLI tool for configuration management

## Purpose

The `config` command provides utilities for working with hierarchical DAG
configurations:

- **template**: Generate a configuration template from a builder class with DUMMY placeholders
- **validate**: Check configurations for missing values and unknown keys
- **merge**: Combine multiple configuration files (later files override earlier)
- **set**: Update a single configuration key
- **get**: Retrieve a configuration value by key
- **diff**: Show differences between two configurations
- **sweep**: Generate multiple configurations from a parameter grid

## Subcommands

### template

Print the config template for a builder (with DUMMY markers).

```bash
config template --builder module.ClassName [--out FILE]
```

### validate

Check a config for DUMMY placeholders and unknown keys.

```bash
config validate --config FILE --builder CLASS_PATH [--dag FILE]
```

Exit codes:
- `0`: config is valid
- `1`: DUMMY placeholders found
- `2`: unknown config keys
- `3`: parse error

### merge

Merge two or more config files (later files override earlier).

```bash
config merge BASE.yaml OVERRIDE.yaml ... [--out FILE]
```

### set

Override a single key in a config file.

```bash
config set --config FILE --key KEY_PATH --value VALUE [--out FILE]
```

Key path uses dot notation: `source.start_date`

### get

Read a single key from a config file.

```bash
config get --config FILE --key KEY_PATH
```

Prints the value; exits 1 if key not found.

### diff

Show differences between two configs.

```bash
config diff CONFIG1 CONFIG2
```

### sweep

Generate a list of configs from a parameter grid.

```bash
config sweep --config FILE --grid GRID_FILE [--out-dir DIR]
```

Grid file is YAML format:
```yaml
model.lookback: [30, 60, 90]
model.alpha: [0.01, 0.1, 1.0]
```

Generates one config file per combination into output directory.

## Examples

```bash
# Get the template, fill required fields, validate
config template --builder myproject.MyBuilder --out template.yaml
config set --config template.yaml --key source.start_date --value 2020-01-01 \
           --out filled.yaml
config validate --config filled.yaml --builder myproject.MyBuilder

# Merge base config with environment override
config merge base.yaml prod_override.yaml --out prod.yaml

# Sweep over lookback and regularization
config sweep --config base.yaml --grid grid.yaml --out-dir ./sweep_configs/

# Show differences
config diff base.yaml override.yaml
```

## Configuration Format

Configurations are stored in YAML format for human readability:

```yaml
source:
  start_date: 2020-01-01
  end_date: 2021-12-31
model:
  lookback: 30
  alpha: 0.01
```

Templates may contain DUMMY placeholders for required fields:

```yaml
database:
  host: __DUMMY__
  port: __DUMMY__
```

## Exit Codes

- `0`: Success
- `1`: DUMMY placeholders found in config
- `2`: Unknown configuration keys detected
- `3`: Parse or file I/O error
