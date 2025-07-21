<!-- toc -->

- [Ruff](#ruff)
  * [Config](#config)
  * [Ruff Check](#ruff-check)
  * [Ruff Format](#ruff-format)
  * [Ruff Linter](#ruff-linter)
  * [Ruff Analyze](#ruff-analyze)
- [Fixit](#fixit)
- [Pyrefly](#pyrefly)
- [Ty](#ty)
- [Pre-Commit](#pre-commit)

<!-- tocstop -->

# Tools for code quality 

## `pre-commit`

- The documentation is [https://pre-commit.com/](https://pre-commit.com/)

- The `.pre-commit-config.yaml` contains the configuration for `pre-commit`

  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.4.4
      hooks:
        - id: ruff
    - repo: local
      hooks:
        - id: fixit-lint
          name: fixit lint
          entry: fixit lint
          language: system
          types: [python]
        - id: pyrefly
          name: pyrefly lint
          entry: pyrefly lint
          language: system
          types: [python]
  ```

- To install:
  ```
  > pre-commit install
  > pip install pre-commit ruff fixit pyrefly
  ```
  - TODO(gp): Maybe we should install in the thin env?

- Run against all the files

  ```bash
  > pre-commit run --all-files
  ```

- Run against a subset of files
  ```bash
  > pre-commit run --files $(find helpers_root -type f)
  ```

## `ruff`

- Website: [https://docs.astral.sh/ruff/](https://docs.astral.sh/ruff/)

- `ruff`:
  - Is a fast Python linter and code formatter
  - Supports over 700 linting rules from popular tools
  - Is meant to be a single replacement for multiple tools (e.g., flake8,
    pylint, isort, pyupgrade)
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

### `ruff format`

- Format only:
  ```
  > ruff format --line-length 80
  ```

### `ruff linter`

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

### `ruff analyze`

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

## Linting

### `ruff check`

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

- Remove colors (useful for cfile)

  ```bash
  > ruff check . | less -R | cat | tee cfile
  > vic
  ```

- To select only a subset of errors
  ```
  # Skip the warnings
  > ruff check . --select E,F
  ```
  where:
  - E: pycodestyle errors
  - F: pyflakes errors
  - W: warnings
  - I: isort, etc.

### `ty`

- It's best to run `ty` inside the dev container to get the type hints of the
  installed packages
  ```bash
  docker> sudo bash -c "(source /venv/bin/activate; pip install --quiet ty)"
  docker> ty check --output-format concise --color never --exclude '**/outcomes/**' --exclude '**/import_check/example/**' .
	...
	error[unresolved-attribute] linters/utils.py:101:22: Type `list[str]` has no attribute `replace`
	error[unresolved-import] main_pytest.py:15:8: Cannot resolve imported module `junitparser`
	error[unresolved-import] tasks.py:122:10: Cannot resolve imported module `oms.lib_tasks_binance`
	...

	# To format the output for a cfile:
  docker> ty check ... | cut -d' ' -f2- | tee cfile
  ```

### `fixit`

- Website:
  [https://fixit.readthedocs.io/en/latest/index.html](https://fixit.readthedocs.io/en/latest/index.html)

- `fixit`
  - Configurable linting framework with support for auto-fixes
  - Custom "local" lint rules, and hierarchical configuration
  - Built on LibCST.

- Fixit doesn't seem to support toml

- Run on `helpers` dir

  ```bash
  > fixit lint .
  ```

- Fix automatically
  ```bash
  > fixit fix --automatic
  ```

### `pyrefly`

- Website: [https://pyrefly.org/](https://pyrefly.org/)

- Pyrefly is a high-performance static type checker for Python
  - Type Checking: Analyzes Python code for type consistency before runtime
  - Type Inference: Infers types for local variables and return values, even in
    un-annotated code
  - Configurable through `pyproject.toml`
    - TODO: Is this true?

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

- It's best to run `pyrefly` inside the dev container to get the type hints of
  the installed packages

  ```bash
  docker> sudo bash -c "(source /venv/bin/activate; pip install --quiet pyrefly)"
  ```

  ```bash
  docker> pyrefly check --color=never --output-format=min-text --project-excludes '**/outcomes/**' --project-excludes '**/import_check/example/**' --project-excludes '**/mkdocs.venv/**'
  ```

## Call graph and dependencies

### PyCG (Practical Call Graph Generator)

- GitHub: [https://github.com/vitsalis/PyCG](https://github.com/vitsalis/PyCG)  
	- Read only (349 stars)

### code2flow

- GitHub: [https://github.com/scottrogowski/code2flow](https://github.com/scottrogowski/code2flow)

- Install with:
	```bash
	> sudo /bin/bash \-c "(source /venv/bin/activate; pip install code2flow)"
	```

- Run with:
	```bash
	> code2flow helpers/hmarkdown*.py
	> open out.png
	```

### pycallgraph2

- GitHub: [https://github.com/daneads/pycallgraph2](https://github.com/daneads/pycallgraph2)
	- 236 stars

- Install with:
	```bash
	docker> sudo /bin/bash \-c "(source /venv/bin/activate; pip install pycallgraph2)"
	```

- Run with:
	```
	> pycallgraph graphviz \-- helpers/hmarkdown*.py
	```

### py-call-graph

- GitHub: [https://github.com/lewiscowles1986/py-call-graph](https://github.com/lewiscowles1986/py-call-graph)
- Doc:
	- [https://pycallgraph.readthedocs.io/en/master/](https://pycallgraph.readthedocs.io/en/master/)  
	- [https://pypi.org/project/python-call-graph/](https://pypi.org/project/python-call-graph/)

### pyan

- [https://github.com/davidfraser/pyan](https://github.com/davidfraser/pyan)  
- 692 stars

- Install with:
	```bash
	> sudo /bin/bash -c "(source /venv/bin/activate; pip install pyan3==1.1.1)"
	# Top of the tree is broken (https://github.com/Technologicat/pyan/issues/72)
	> sudo /bin/bash -c "(source /venv/bin/activate; pip install pyan3)"
	```

- Run with:
	```bash
	> pyan ./helpers/hmarkdown_filtering.py --dot --uses --no-defines > callgraph.dot
	> ./dev_scripts_helpers/documentation/dockerized_graphviz.py -i callgraph.dot -o c.png  
	> open c.png
	```

### `SnakeViz`

- Works on runtime profiling (not static), gives function timing & hierarchy

## Dependencies

### `pylint pyreverse`

- GitHub: [https://github.com/pylint-dev/pylint](https://github.com/pylint-dev/pylint)  
- Doc:
	- https://pylint.readthedocs.io/en/latest/
	- https://pylint.readthedocs.io/en/latest/additional_tools/pyreverse/index.html

### `Pydeps`

- GitHub: [https://github.com/thebjorn/pydeps](https://github.com/thebjorn/pydeps)  
- Doc: [https://pydeps.readthedocs.io/en/latest/](https://pydeps.readthedocs.io/en/latest/)

- Run with
	```
	> pydeps helpers --noshow --show-dot -o import_graph.dot
	```

### `snakefood`

- GitHub: https://github.com/blais/snakefood

## Measuring complexity

### `radon`
- Static analysis for complexity, can complement class structure graphs

### `xenon`
- Enforces complexity thresholds based on Radon
- Built on Radon

### `lizard`
- Measures cyclomatic complexity for many languages

## Finding dead code

### Vulture
- Finds dead (unused) code
- GitHub: https://github.com/jendrikseipp/vulture

## Detecting copy-paste

### `pylint symilar`

- Docs: https://pylint.readthedocs.io/en/latest/additional_tools/symilar/index.html

### `lizard`

- Install with:
	```bash
	> pip install lizard
	```

- Run with:
	```bash
	> lizard \-Eduplicate helpers/test/test\_hmarkdown\_coloring.py helpers/test/test\_hmarkdown.py

	Duplicate block:  
	\--------------------------  
	./dev\_scripts\_helpers/llms/llm\_prompts.py:1129 \~ 1151  
	./dev\_scripts\_helpers/llms/llm\_prompts.py:1151 \~ 1177  
	./dev\_scripts\_helpers/llms/llm\_prompts.py:1177 \~ 1219  
	./dev\_scripts\_helpers/llms/llm\_prompts.py:1219 \~ 1256  
	./dev\_scripts\_helpers/llms/llm\_prompts.py:1256 \~ 1280  
	./dev\_scripts\_helpers/llms/llm\_prompts.py:1280 \~ 1312  
	./dev\_scripts\_helpers/llms/llm\_prompts.py:1377 \~ 1425
	```

### `jscpd`

- Install with:
	```
	docker> sudo npm install -g jscpd
	```

- Run with:
	```
	> jscpd --languages python --reporters console,path/to/your/code
	> jscpd --format=python --reporters console helpers
	```

- It doesn't seem to work
