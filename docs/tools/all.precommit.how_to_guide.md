## ruff

- `Ruff`:
  - is a fast Python linter and code formatter
  - supports over 700 linting rules from popular tools
  - is meant to be a single replacement for multiple tools (e.g., flake8, pylint,
    isort, pyupgrade)

```
> ruff -h
...
Commands:
  check    Run Ruff on the given files or directories
  rule     Explain a rule (or all rules)
  config   List or describe the available configuration options
  linter   List all supported upstream linters
  clean    Clear any caches in the current directory and any subdirectories
  format   Run the Ruff formatter on the given files or directories
  server   Run the language server
  analyze  Run analysis over Python source code
  version  Display Ruff's version
  help     Print this message or the help of the given subcommand(s)
...
```

### Config

- Often we want to exclude certain files in the repos, e.g., files under
  `outcomes`:
  ```bash
  > ruff ... --exclude  '**/outcomes/**' --exclude '**/import_check/example/**'
  ```

- By default we use the following options in `pyproject.toml`
  ```text
  [tool.ruff]
  line-length = 81
  target-version = "py311"
  fix = true
  exclude = [
    "**/outcomes/**",
    "**/import_check/example/**"
  ]
  output-format = "concise"

  [tool.ruff.lint]
  # E731 Do not assign a `lambda` expression, use a `def`
  ignore = ["E731"]
  ```

### ruff check

- Lint, auto-fix, and format code:
  ```bash
  > ruff check $DIR
  helpers/notebooks/cache.ipynb:cell 11:1:7: F821 Undefined name `dict_`
  helpers/notebooks/cache.ipynb:cell 12:3:7: F821 Undefined name `dict_`
  ...
  Found 62 errors.
  No fixes available (2 hidden fixes can be enabled with the `--unsafe-fixes` option).
  ```

- Interesting options are:
  ```text
      --fix                              Apply fixes to resolve lint violations
      --unsafe-fixes                     Include fixes that may not retain the original intent of the code
      --ignore-noqa                      Ignore any `# noqa` comments
      --output-format <OUTPUT_FORMAT>    Output serialization format for violations
  -o, --output-file <OUTPUT_FILE>        Specify file to write the linter output to (default: stdout)
      --statistics                       Show counts for every rule with at least one violation
      --add-noqa                         Enable automatic additions of `noqa` directives to failing lines
      --show-settings                    See the settings Ruff will use to lint a given Python file
  ```

### ruff format

- Format only:
  ```
  > ruff format --line-length 80
  ```

### ruff linter

- List all supported upstream linters
  ```bash
  > ruff linter
   AIR Airflow
   ERA eradicate
  FAST FastAPI
   YTT flake8-2020
   ANN flake8-annotations
  ASYNC flake8-async
  ...
  ```

### ruff analyze

- Can analyze the code base
  ```text
  > ruff analyze graph -h
  Generate a map of Python file dependencies or dependents

  Usage: ruff analyze graph [OPTIONS] [FILES]...

  Arguments:
    [FILES]...  List of files or directories to include [default: .]

  Options:
        --direction <DIRECTION>            The direction of the import map. By
                                           default, generates a dependency map, i.e., a map from file to files that
                                           it depends on. Use `--direction dependents` to generate a map from file
                                           to files that depend on it [default: dependencies] [possible values:
                                           dependencies, dependents]
        --detect-string-imports            Attempt to detect imports from string literals
        --preview                          Enable preview mode. Use `--no-preview` to disable
    -h, --help                             Print help (see more with '--help')
  ```

## pyrefly

- Pyrefly is a high-performance static type checker for Python

- Website: https://pyrefly.org/

- Type Checking: Analyzes Python code for type consistency before runtime
- Type Inference: Infers types for local variables and return values, even in
  un-annotated code
- Configurable through pyproject.toml

  ```bash
  > pyrefly -h

  Usage: pyrefly [OPTIONS] <COMMAND>

  Commands:
    check        Full type checking on a file or a project
    dump-config  Dump info about pyrefly's configuration. Use by replacing
                 `check` with `dump-config` in your pyrefly invocation
    init         Initialize a new pyrefly config in the given directory, or
                 migrate an existing mypy or pyright config to pyrefly
    lsp          Start an LSP server

  Options:
    -j, --threads <THREADS>  Number of threads to use for parallelization.
                             Setting the value to 1 implies sequential execution without any parallelism.
                             Setting the value to 0 means to pick the number of threads automatically
                             using default heuristics [default: 0]
        --color <COLOR>      Controls whether colored output is used
  ```
