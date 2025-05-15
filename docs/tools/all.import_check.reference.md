<!-- toc -->

- [show_imports](#show_imports)
  * [Basic usage](#basic-usage)
  * [Visualize dependencies at a directory level](#visualize-dependencies-at-a-directory-level)
  * [Visualize external dependencies](#visualize-external-dependencies)
  * [Visualize level X dependencies](#visualize-level-x-dependencies)
  * [Visualize cyclic dependencies](#visualize-cyclic-dependencies)
  * [Pydeps-dependent limitations](#pydeps-dependent-limitations)
    + [NotModuleError](#notmoduleerror)
    + [Modules above the target directory](#modules-above-the-target-directory)
  * [Run the tool on our codebase -- pre-docker procedure](#run-the-tool-on-our-codebase----pre-docker-procedure)
- [detect_import_cycles](#detect_import_cycles)
  * [Basic usage](#basic-usage-1)
- [show_deps](#show_deps)
  * [Overview](#overview)
  * [Command usage](#command-usage)
  * [Examples](#examples)
    + [Generate a text report](#generate-a-text-report)
    + [Generate a DOT file for visualization](#generate-a-dot-file-for-visualization)
    + [Limit analysis to a specific directory depth](#limit-analysis-to-a-specific-directory-depth)
    + [Focus on cyclic dependencies](#focus-on-cyclic-dependencies)
  * [Options](#options)
  * [Limitations](#limitations)
  * [Running the tool on our codebase](#running-the-tool-on-our-codebase)

<!-- tocstop -->

# show_imports

A tool for visualizing dependencies among files and packages.

## Basic usage

```bash
> show_imports.py [flags] <target_directory>
```

The script will produce by default an output `.png` file named
`<target_directory>_dependencies.png`, you can change the default output name or
image format by specifying the `--out_filename` and `--out_format` options.

In the following examples we will analyze an example input directory
`example/input` that you can find in the `import_check/` dir. It is structured
as follows:

```text
example
├── input
    ├── __init__.py
    ├── subdir1
    │   ├── file1.py
    │   ├── file2.py
    │   └── __init__.py
    ├── subdir2
    │    ├── file1.py
    │    ├── file2.py
    │    ├── __init__.py
    │    └── subdir3
    │        ├── file1.py
    │        ├── file2.py
    │        ├── file3.py
    │        └── __init__.py
    └── subdir4
        ├── file1.py
        ├── file2.py
        ├── file3.py
        └── __init__.py
```

Basic usage example:

```bash
> show_imports.py --out_filename example/output/basic.png example/input
```

Will produce the following output:

![Basic usage output](/import_check/example/output/basic.png)

## Visualize dependencies at a directory level

To visualize dependencies at a directory level, specify `--dir` option.

Example:

```bash
> show_imports.py --dir --out_filename example/output/directory_deps.png example/input
```

Output:

![Directory dependencies](/import_check/example/output/directory_deps.png)

## Visualize external dependencies

By default, external dependencies are not visualized. You can turn them on by
specifying the `--ext` option.

Example:

```bash
> show_imports.py --ext --out_filename example/output/external_deps.png example/input
```

Output:

![External dependencies](/import_check/example/output/external_deps.png)

## Visualize level X dependencies

When you want to stop analyzing dependencies at a certain directory level, you
can set the `--max_level` option.

Example:

```bash
> show_imports.py --max_level 2 --out_filename example/output/max_level_deps.png example/input
```

Output:

![Maximum level dependencies](/import_check/example/output/max_level_deps.png)

## Visualize cyclic dependencies

When you want to visualize cyclic dependencies only, you can set the
`--show_cycles` option.

Example:

```bash
> show_imports.py --show_cycles --out_filename example/output/cyclic_deps.png example/input
```

Output:

![Cyclic dependencies](/import_check/example/output/cyclic_deps.png)

## Pydeps-dependent limitations

`show_imports` is based on the [`pydeps`](https://github.com/thebjorn/pydeps)
tool for detecting dependencies among imports, therefore it shares some of the
its limitations:

- The output contains only files which have at least one import, or are imported
  in at least one other file
- Only files that can be found by using the Python import machinery will be
  considered (e.g., if a module is missing or not installed, it will not be
  included regardless of whether it is being imported)
- All the imports inside submodules should be absolute
- There are certain requirements related to the presence of modules in and
  above the target directory, which are described in detail below
  - Here, a module is a directory that contains an `__init__.py` file

### NotModuleError

Suppose we run the `show_imports` script on a target directory `input_dir`. The
script will check the `input_dir` and all of its subdirectories of any level. A
`NotModuleError` will be raised if any of them

- Contain Python files (directly or in any of their subdirectories of any level)
  _and_
- Are not modules

Example of an acceptable structure for `input_dir` as a target directory:

```text
input_dir
├── __init__.py
├── subdir1
│   ├── file1.py
│   └── __init__.py
└── subdir2
    └── __init__.py
```

Examples of input directories for which `show_imports` will fail with a
`NotModuleError`:

- `input_dir/subdir1` contains Python files but is not a module

```text
input_dir
├── __init__.py
├── subdir1
│   └── file1.py
└── subdir2
    └── __init__.py
```

```bash
__main__.NotModuleError: The following dirs have to be modules (add `__init__.py`): ['input_dir/subdir1']
```

- `input_dir` contains subdirectories with Python files (`input_dir/subdir1`)
  but is not a module

```text
input_dir
├── subdir1
│   ├── file1.py
│   └── __init__.py
└── subdir2
    └── __init__.py
```

```bash
__main__.NotModuleError: The following dirs have to be modules (add `__init__.py`): ['input_dir']
```

### Modules above the target directory

Suppose we run the `show_imports` script on a target directory `input_dir`. The
dependencies will be retrieved and shown for the files

- Under `input_dir` (including the files in its subdirectories of any level)
  _and_
- In the directories above `input_dir`
  - If these directories are modules themselves and there is no non-module
    directory between them and `input_dir`

For example,

- All the directories in following structure are modules
- Therefore, if `import_check` or any of the subdirectories are passed as a
  target directory (e.g. `example/input`, `example/input/subdir1`,
  `example/input/subdir2/subdir3`, etc), all the dependencies in `import_check`
  will be shown

```text
import_check
├── __init__.py
├── show_imports.py
├── detect_import_cycles.py
└── example
    ├── __init__.py
    └── input
        ├── __init__.py
        ├── subdir1
        │   ├── file1.py
        │   ├── file2.py
        │   └── __init__.py
        └── subdir2
             ├── file1.py
             ├── file2.py
             ├── __init__.py
             └── subdir3
                 ├── file1.py
                 ├── file2.py
                 ├── file3.py
                 └── __init__.py
```

- In the following structure `import_check/example` is not a module
- Therefore, if `import_check/example/input` or any of its subdirectories are
  passed as a target directory, all the dependencies in
  `import_check/example/input` will be shown, but not the dependencies of the
  files above it
- If `import_check` or `import_check/example` are passed as a target directory,
  a `NotModuleError` will be raised, see [above](#notmoduleerror)

```text
import_check
├── __init__.py
├── show_imports.py
├── detect_import_cycles.py
└── example
    └── input
        ├── __init__.py
        ├── subdir1
        │   ├── file1.py
        │   ├── file2.py
        │   └── __init__.py
        └── subdir2
             ├── file1.py
             ├── file2.py
             ├── __init__.py
             └── subdir3
                 ├── file1.py
                 ├── file2.py
                 ├── file3.py
                 └── __init__.py
```

In practice, this means that if all the directories containing Python files in
the repository are modules, the output of the `show_imports` script will always
show the dependencies for the whole repository.

If it is necessary to run `show_imports` only for a specific directory, it has
to be located directly inside a non-module directory (like
`import_check/example/input`, which is located in a non-module
`import_check/example`).

## Run the tool on our codebase -- pre-docker procedure

- Activate `helpers` environment:
  - From the `helpers` root:
    ```bash
    poetry shell; export PYTHONPATH=$PYTHONPATH:$(pwd)
    ```
- Run the tool on the target repo. E.g., analyze for cyclic dependencies
  ```bash
  <path for the show_imports.py script> --show_cycles \
                                        --out_format svg \
                                        --out_filename cyclic_dependencies.svg \
                                        <absolute path for the target repo>
  ```

# detect_import_cycles

A tool for detecting circular dependencies among files and packages.

## Basic usage

```bash
> detect_import_cycles.py <target_directory>
```

The script will either exit with an error, logging the groups of files with
circular dependencies, or will pass, logging that no cyclic imports have been
detected.

The script uses `show_imports.py` for the dependency retrieval and therefore
inherits its [limitations](#pydeps-dependent-limitations).

For the `import_check/example/input` directory, the script will produce the
following output, detecting two import cycles:

```bash
> detect_import_cycles.py example/input
```

```bash
ERROR detect_import_cycles.py _main:73    Cyclic imports detected: (input.subdir2.subdir3.file1, input.subdir2.subdir3.file2)
ERROR detect_import_cycles.py _main:73    Cyclic imports detected: (input.subdir4.file1, input.subdir4.file2, input.subdir4.file3)
```

# show_deps

## Overview

- Analyzes Python files in a directory for intra-directory import dependencies
- Generates:
  - A text report, or
  - A DOT file for visualization
- Useful for understanding module relationships within a project
- Supports options to:
  - Limit analysis depth
  - Focus on cyclic dependencies

## Command usage

```bash
> i show_deps [--directory <directory>] [--format <format>] [--output_file <file>] [--max_level <level>] [--show_cycles]
```

- **Default behavior**: Produces a text report, printed to stdout.
- **Options**:
  - `--directory`: Specifies the directory to analyze (default: current
    directory).
  - `--format`: Sets the output format (`text` or `dot`, default: `text`).
  - `--output_file`: Saves the report to a file (default: stdout for text,
    `dependency_graph.dot` for DOT).
  - `--max_level`: Limits the directory depth for analysis (e.g., `2` for two
    levels).
  - `--show_cycles`: Filters the report to show only cyclic dependencies
    (default: false).

## Examples

The examples below analyze the `helpers` directory, which contains
subdirectories like `notebooks/`.

### Generate a text report

Create a text report of all intra-directory dependencies:

```bash
> i show_deps --directory helpers --format text > report.txt
```

Output in `report.txt`:

```text
helpers/notebooks/gallery_parquet.py imports helpers/hdbg.py, helpers/hio.py
helpers/hdbg.py has no dependencies
helpers/hio.py has no dependencies
...
```

### Generate a DOT file for visualization

Create a DOT file for visualization:

```bash
> i show_deps --directory helpers --format dot --output_file dependency_graph.dot
>dot -Tsvg dependency_graph.dot -o dependency_graph.svg
>open dependency_graph.svg
```

For large graphs, use the `neato` layout engine:

```bash
>neato -Tsvg dependency_graph.dot -o dependency_graph.svg -Goverlap=scale -Gsep=+0.5 -Gepsilon=0.01
>open dependency_graph.svg
```

### Limit analysis to a specific directory depth

Restrict analysis to a certain depth with `--max_level` (e.g., `--max_level 2`
includes `helpers/notebooks/`, excludes deeper subdirectories):

```bash
> i show_deps --directory helpers --format text --max_level 2 > report_max_level.txt
```

Output in `report_max_level.txt`:

```text
helpers/notebooks/gallery_parquet.py imports helpers/hdbg.py, helpers/hio.py
helpers/hdbg.py has no dependencies
helpers/hio.py has no dependencies
...
```

Visualize the limited graph:

```bash
> i show_deps --directory helpers --format dot --output_file dependency_graph.dot --max_level 2
>neato -Tsvg dependency_graph.dot -o dependency_graph.svg -Goverlap=scale -Gsep=+0.5 -Gepsilon=0.01
>open dependency_graph.svg
```

### Focus on cyclic dependencies

Show only cyclic dependencies with `--show_cycles`:

```bash
> i show_deps --directory helpers --format text --show_cycles > report_cycles.txt
```

Output in `report_cycles.txt` (if cycles exist):

```text
helpers/module_d.py imports helpers/module_e.py
helpers/module_e.py imports helpers/module_d.py
...
```

Visualize the cyclic dependencies:

```bash
> i show_deps --directory helpers --format dot --output_file dependency_graph.dot --show_cycles
> neato -Tsvg dependency_graph.dot -o dependency_graph.svg -Goverlap=scale -Gsep=+0.5 -Gepsilon=0.01
> open dependency_graph.svg
```

## Options

- `--directory <path>`: Directory to analyze (default: `.`).
- `--format <text|dot>`: Output format (default: `text`).
- `--output_file <file>`: File to save the report (default: stdout for text,
  `dependency_graph.dot` for DOT).
- `--max_level <int>`: Maximum directory depth to analyze (e.g., `2`).
- `--show_cycles`: Show only cyclic dependencies (e.g., `module_d` importing
  `module_e` and vice versa).

## Limitations

- Analyzes only intra-directory imports; external imports (e.g., `numpy`) are
  ignored.
- Imports must resolve within the directory (e.g., `helpers.hdbg` to
  [`/helpers/hdbg.py)`](/helpers/hdbg.py)).
- Directories with Python files must be modules (contain `__init__.py`), or a
  `NotModuleError` is raised.

Example of a valid structure:

```text
helpers
├── __init__.py
├── notebooks
│   ├── gallery_parquet.py
│   └── __init__.py
└── hdbg.py
```

Example causing `NotModuleError`:

```text
helpers
├── __init__.py
├── notebooks
│   └── gallery_parquet.py
└── hdbg.py
```

```bash
NotModuleError: The following dirs have to be modules (add `__init__.py`): ['helpers/notebooks']
```

## Running the tool on our codebase

1. **Activate the `helpers` environment**: From the `helpers` root directory:

   ```bash
   > poetry shell; export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

2. **Generate a dependency report**: Create a text report:

   ```bash
   > i show_deps --directory helpers --format text > report.txt
   ```

   Or create a DOT file for visualization:

   ```bash
   > i show_deps --directory helpers --format dot --output_file dependency_graph.dot
   ```

3. **Visualize the graph** (optional): Convert the DOT file to SVG and view:
   ```bash
   > neato -Tsvg dependency_graph.dot -o dependency_graph.svg -Goverlap=scale -Gsep=+0.5 -Gepsilon=0.01
   > open dependency_graph.svg
   ```

**Troubleshooting**: If `invoke` fails (e.g.,
`No idea what '--output_file' is!`), use the fallback script:

```bash
> generate_deps.py
> neato -Tsvg dependency_graph.dot -o dependency_graph.svg -Goverlap=scale -Gsep=+0.5 -Gepsilon=0.01
> open dependency_graph.svg
```

**Tips**: The `generate_deps.py` script applies customizations like filtering
nodes with no dependencies and shortening labels (e.g., removing `helpers/`
prefix). Adjust Graphviz attributes (`ranksep=2.0`, `nodesep=1.0`,
`splines=spline`, `overlap=false`, `fontsize=10`) for better visualization.

**Last review**:
- 2025-05-14, GP Saggese
- 2025-05-01, Ehaab Basil
