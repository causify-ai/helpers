<!--ts-->
   * [show_imports](#show_imports)
      * [Basic usage](#basic-usage)
      * [Visualize dependencies at a directory level](#visualize-dependencies-at-a-directory-level)
      * [Visualize external dependencies](#visualize-external-dependencies)
      * [Visualize level X dependencies](#visualize-level-x-dependencies)
      * [Visualize cyclic dependencies](#visualize-cyclic-dependencies)
      * [Pydeps-dependent limitations](#pydeps-dependent-limitations)
         * [NotModuleError](#notmoduleerror)
         * [Modules above the target directory](#modules-above-the-target-directory)
      * [Run the tool on our codebase -- pre-docker procedure](#run-the-tool-on-our-codebase----pre-docker-procedure)
   * [detect_import_cycles](#detect_import_cycles)
      * [Basic usage](#basic-usage-1)



<!--te-->

# show_imports

A tool for visualizing dependencies among files and packages.

## Basic usage

```bash
>./show_imports.py [flags] <target_directory>
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
>./show_imports.py --out_filename example/output/basic.png example/input
```

Will produce the following output:

![Basic usage output](/import_check/example/output/basic.png)

## Visualize dependencies at a directory level

To visualize dependencies at a directory level, specify `--dir` option.

Example:

```bash
>./show_imports.py --dir --out_filename example/output/directory_deps.png example/input
```

Output:

![Directory dependencies](/import_check/example/output/directory_deps.png)

## Visualize external dependencies

By default, external dependencies are not visualized. You can turn them on by
specifying the `--ext` option.

Example:

```bash
>./show_imports.py --ext --out_filename example/output/external_deps.png example/input
```

Output:

![External dependencies](/import_check/example/output/external_deps.png)

## Visualize level X dependencies

When you want to stop analyzing dependencies at a certain directory level, you
can set the `--max_level` option.

Example:

```bash
>./show_imports.py --max_level 2 --out_filename example/output/max_level_deps.png example/input
```

Output:

![Maximum level dependencies](/import_check/example/output/max_level_deps.png)

## Visualize cyclic dependencies

When you want to visualize cyclic dependencies only, you can set the
`--show_cycles` option.

Example:

```bash
>./show_imports.py --show_cycles --out_filename example/output/cyclic_deps.png example/input
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
- There are certain requirements related to the presence of _modules_ in and
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
>./detect_import_cycles.py <target_directory>
```

The script will either exit with an error, logging the groups of files with
circular dependencies, or will pass, logging that no cyclic imports have been
detected.

The script uses `show_imports.py` for the dependency retrieval and therefore
inherits its [limitations](#pydeps-dependent-limitations).

For the `import_check/example/input` directory, the script will produce the
following output, detecting two import cycles:

```bash
>./detect_import_cycles.py example/input
```

```bash
ERROR detect_import_cycles.py _main:73    Cyclic imports detected: (input.subdir2.subdir3.file1, input.subdir2.subdir3.file2)
ERROR detect_import_cycles.py _main:73    Cyclic imports detected: (input.subdir4.file1, input.subdir4.file2, input.subdir4.file3)
```
