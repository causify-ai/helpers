<!-- toc -->

- [Coding Tools](#coding-tools)
  * [Structure of the Dir](#structure-of-the-dir)
  * [Description of Files](#description-of-files)
  * [Description of Executables](#description-of-executables)
    + [`compile_all.py`](#compile_allpy)
      - [What It Does](#what-it-does)
      - [Examples](#examples)
    + [`measure_import_times.py`](#measure_import_timespy)
      - [What It Does](#what-it-does-1)
      - [Examples](#examples-1)
    + [`grsync.py`](#grsyncpy)
      - [What It Does](#what-it-does-2)
      - [Examples](#examples-2)
    + [`find_unused_golden_files.py`](#find_unused_golden_filespy)
      - [What It Does](#what-it-does-3)
      - [Examples](#examples-3)
    + [`diff_to_vimdiff.py`](#diff_to_vimdiffpy)
      - [What It Does](#what-it-does-4)
      - [Examples](#examples-4)
    + [`reorder_python_code.py`](#reorder_python_codepy)
      - [What It Does](#what-it-does-5)
      - [Examples](#examples-5)
    + [`process_prof.py`](#process_profpy)
      - [What It Does](#what-it-does-6)
      - [Examples](#examples-6)
    + [`traceback_to_cfile.py`](#traceback_to_cfilepy)
      - [What It Does](#what-it-does-7)
      - [Examples](#examples-7)
    + [`url.py`](#urlpy)
      - [What It Does](#what-it-does-8)
      - [Examples](#examples-8)
    + [`toml_merge.py`](#toml_mergepy)
      - [What It Does](#what-it-does-9)
      - [Examples](#examples-9)
    + [`manage_cache.py`](#manage_cachepy)
      - [What It Does](#what-it-does-10)
      - [Examples](#examples-10)
    + [`print_pickle.py`](#print_picklepy)
      - [What It Does](#what-it-does-11)
      - [Examples](#examples-11)
    + [`parallel_script_template.py`](#parallel_script_templatepy)
      - [What It Does](#what-it-does-12)
      - [Examples](#examples-12)
    + [`split_in_files.py`](#split_in_filespy)
      - [What It Does](#what-it-does-13)
      - [Examples](#examples-13)

<!-- tocstop -->

# Coding Tools

Development utilities for code analysis, profiling, synchronization, and
refactoring.

## Structure of the Dir

- `develop/`
  - Development and experimental scripts

## Description of Files

- `clean_up_text_files.sh`
  - Ensures text files end with exactly one newline to satisfy linter
    requirements
- `code_stats.sh`
  - Counts files and lines of code across different file types in repository
- `compile_all.py`
  - Compiles all Python files in repository to check for syntax errors
- `create_class_diagram.sh`
  - Generates UML class diagrams from Python code using pyreverse and graphviz
- `ctags.sh`
  - Generates ctags file for Python code using dockerized universal-ctags
- `diff_to_vimdiff.py`
  - Transforms diff output into vimdiff script for interactive directory
    comparison
- `find_unused_golden_files.py`
  - Identifies golden test files with no corresponding test methods or vice
    versa
- `grsync.py`
  - Syncs directories between local and remote machines using rsync with
    git-aware exclusions
- `invite_github_collaborator.py`
  - Checks GitHub user status and sends repository collaboration invitations via
    API
- `manage_cache.py`
  - Manages hcache global cache with clear, list, and test operations
- `measure_import_times.py`
  - Measures and reports execution time for importing Python modules
- `parallel_script_template.py`
  - Template demonstrating parallel execution using hjoblib API
- `print_pickle.py`
  - Reads pickle file and displays contents using pretty print formatting
- `process_prof.py`
  - Post-processes cProfile output to generate statistics and call graphs
- `reorder_python_code.md`
  - Documentation explaining design and usage of reorder_python_code.py tool
- `reorder_python_code.py`
  - Reorganizes functions from single Python file into multiple files using
    markdown map
- `remove_jupyter_metadata.sh`
  - Strips output and metadata from Jupyter notebooks using gitleaks detection
- `run_profiling.sh`
  - Template script for running cProfile and line_profiler on Python code
- `script_template.py`
  - Template for creating new Python scripts with standard argument parsing and
    logging
- `split_in_files.py`
  - Splits file with special tags into separate output files with optional
    common section, supports multiple chunks per file and append mode
- `toml_merge.py`
  - Merges multiple pyproject.toml files handling dependencies and
    dev-dependencies
- `traceback_to_cfile.py`
  - Parses Python tracebacks and generates vim cfile for navigation
- `transform_template.py`
  - Template for scripts that read from stdin/file, transform, and write to
    stdout/file
- `url.py`
  - Converts between file paths, GitHub URLs, and Jupyter URLs

## Description of Executables

### `compile_all.py`

#### What It Does

- Compiles all Python files in current directory and subdirectories
- Checks for syntax errors without executing code
- Skips .git, tmp., and venv directories

#### Examples

**Compile all Python files in repository**

```bash
> ./compile_all.py
```

**Use as module import**

```bash
> python -c "import dev_scripts_helpers.compile_all"
```

### `measure_import_times.py`

#### What It Does

- Measures import time for every Python module found in directory
- Reports slowest imports sorted by execution time
- Saves results and errors to timestamped output files

#### Examples

**Measure imports in current directory**

```bash
> ./measure_import_times.py
```

**Measure imports in specific directory**

```bash
> ./measure_import_times.py --directory /path/to/project
```

**Measure with debug logging**

```bash
> ./measure_import_times.py -v DEBUG
```

### `grsync.py`

#### What It Does

- Synchronizes directories between local and remote machines using rsync
- Supports preview mode, force sync, and bidirectional sync
- Can generate file diff reports for comparison

#### Examples

**Preview sync to remote without executing**

```bash
> ./grsync.py --src_dir ~/src/project --config amp --action rsync --preview --dry_run
```

**Sync local directory to remote**

```bash
> ./grsync.py --src_dir ~/src/project --config amp --action rsync
```

**Generate diff report between local and remote**

```bash
> ./grsync.py --src_dir ~/src/project --config amp --action diff
```

**Verbose diff with full file listings**

```bash
> ./grsync.py --src_dir ~/src/project --config amp --action diff_verb
```

### `find_unused_golden_files.py`

#### What It Does

- Scans test directory for golden outcome files and test code
- Identifies golden files without corresponding test methods
- Reports test methods with check_string calls but no golden files

#### Examples

**Find unused golden files in current directory**

```bash
> ./find_unused_golden_files.py
```

**Analyze specific directory**

```bash
> ./find_unused_golden_files.py --dir_name /path/to/module
```

**Run with info-level logging**

```bash
> ./find_unused_golden_files.py -v INFO
```

### `diff_to_vimdiff.py`

#### What It Does

- Compares two directories and generates vimdiff script for interactive review
- Can filter to show only different file content or only missing files
- Supports comparing file lists or file contents

#### Examples

**Generate vimdiff script for two directories**

```bash
> ./diff_to_vimdiff.py --dir1 /path/to/dir1 --dir2 /path/to/dir2
```

**Compare only files with different content**

```bash
> ./diff_to_vimdiff.py --dir1 ~/src/branch1 --dir2 ~/src/branch2 --only_different_file_content
```

**Compare file lists instead of content**

```bash
> ./diff_to_vimdiff.py --dir1 ~/src/branch1 --dir2 ~/src/branch2 --compare_file_list
```

**Ignore certain files using regex**

```bash
> ./diff_to_vimdiff.py --dir1 ~/src/v1 --dir2 ~/src/v2 --ignore_files "test_.*\.py"
```

### `reorder_python_code.py`

#### What It Does

- Splits large Python file into multiple organized files
- Uses markdown map to specify target files and function groupings
- Preserves exact formatting, imports, and module headers

#### Examples

**Reorganize Python file using map**

```bash
> ./reorder_python_code.py --input_file helpers/hpandas.py --map_file hpandas_map.md
```

**Run with debug logging to see processing details**

```bash
> ./reorder_python_code.py --input_file module.py --map_file map.md -v DEBUG
```

### `process_prof.py`

#### What It Does

- Processes Python cProfile output files
- Generates statistics sorted by cumulative time
- Can create call graph visualizations using gprof2dot

#### Examples

**Show profiling statistics**

```bash
> ./process_prof.py --file_name prof.bin --action stats
```

**Generate call graph as PNG**

```bash
> ./process_prof.py --file_name prof.bin --action plot --ext png
```

**Generate call graph as PostScript**

```bash
> ./process_prof.py --file_name prof.bin --action plot --ext ps
```

### `traceback_to_cfile.py`

#### What It Does

- Parses Python traceback from log file or stdin
- Generates vim cfile for quick navigation to error locations
- Supports purifying paths to be relative to current client

#### Examples

**Parse pytest log and create cfile**

```bash
> ./traceback_to_cfile.py -i tmp.pytest.log
```

**Use newest log file automatically**

```bash
> ./traceback_to_cfile.py
```

**Parse traceback from clipboard**

```bash
> pbpaste | ./traceback_to_cfile.py -i -
```

**Open vim with cfile navigation**

```bash
> ./traceback_to_cfile.py -i error.log && vim -c "cfile cfile"
```

### `url.py`

#### What It Does

- Converts between file paths, GitHub URLs, and Jupyter URLs
- Validates URLs and checks file existence
- Generates commands for opening notebooks

#### Examples

**Convert GitHub URL to local path and Jupyter URL**

```bash
> ./url.py https://github.com/org/repo/blob/main/notebooks/analysis.ipynb
```

**Short output without headers**

```bash
> ./url.py --short /path/to/notebook.ipynb
```

### `toml_merge.py`

#### What It Does

- Merges multiple pyproject.toml files into single file
- Combines dependencies and dev-dependencies sections
- Asserts on conflicting package versions

#### Examples

**Merge two TOML files**

```bash
> ./toml_merge.py --in_file base/pyproject.toml --in_file extra/pyproject.toml --out_file merged.toml
```

**Merge multiple files with debug logging**

```bash
> ./toml_merge.py --in_file file1.toml --in_file file2.toml --in_file file3.toml --out_file result.toml -v DEBUG
```

### `manage_cache.py`

#### What It Does

- Manages hcache global cache for decorated functions
- Clears memory cache, disk cache, or both
- Provides cache info and test operations

#### Examples

**Clear all cache (memory and disk)**

```bash
> ./manage_cache.py --action clear_global_cache
```

**Clear only memory cache**

```bash
> ./manage_cache.py --action clear_global_mem_cache
```

**Show cache information**

```bash
> ./manage_cache.py --action print_cache_info
```

**List available actions**

```bash
> ./manage_cache.py --action list
```

### `print_pickle.py`

#### What It Does

- Loads and displays contents of pickle files in readable format
- Shows object type information and pretty-printed structure
- Supports configurable depth for nested data structures

#### Examples

**Print contents of a pickle file**

```bash
> ./print_pickle.py --input data.pkl
```

**Print with increased depth for nested structures**

```bash
> ./print_pickle.py --input cache.pkl --depth 5
```

**Print with debug logging**

```bash
> ./print_pickle.py --input file.pkl -v DEBUG
```

### `parallel_script_template.py`

#### What It Does

- Template demonstrating hjoblib parallel execution API
- Shows workload definition, error handling, and progress tracking
- Supports serial or parallel execution with configurable threads

#### Examples

**Run successful workload serially**

```bash
> ./parallel_script_template.py --workload success --num_threads serial
```

**Run workload with 4 parallel threads**

```bash
> ./parallel_script_template.py --workload success --num_threads 4
```

**Run failure workload to test error handling**

```bash
> ./parallel_script_template.py --workload failure --num_threads 3
```

**Run with randomization and specific seed**

```bash
> ./parallel_script_template.py --workload success --num_threads 2 --randomize --seed 42
```

### `split_in_files.py`

#### What It Does

- Reads a file containing special tags and splits it into separate output files
- Supports optional common section that is copied to all output files
- Allows multiple chunks with the same filename to be concatenated into one file
- Can append to existing files instead of overwriting them with `--append` flag
- Modifies input file after splitting: removes content between tags, keeps tags and untagged content
- Provides dry run mode to preview operations without writing files

#### Examples

**Split a file with tags into separate files in the same directory**

```bash
> ./split_in_files.py --input_file input.txt
```

**Split with custom output directory**

```bash
> ./split_in_files.py --input_file input.txt --output_dir ./output
```

**Append to existing files instead of overwriting**

```bash
> ./split_in_files.py --input_file input.txt --append
```

**Preview what would be done without writing files (dry run)**

```bash
> ./split_in_files.py --input_file input.txt --dry_run
```

**Keep the input file unchanged after splitting**

```bash
> ./split_in_files.py --input_file input.txt --preserve_input
```

**Split with verbose logging**

```bash
> ./split_in_files.py --input_file input.txt --output_dir ./output -v DEBUG
```
