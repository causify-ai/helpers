## ruff

ruff is a fast Python linter and code formatter.

```
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
```

- We want to exclude certain files, e.g., files under `outcomes`
  ```
  > ruff ... --exclude  '**/outcomes/**' --exclude '**/import_check/example/**'
  ```

### Config

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

```bash
> ruff check $DIR
helpers/notebooks/cache.ipynb:cell 11:1:7: F821 Undefined name `dict_`
helpers/notebooks/cache.ipynb:cell 12:3:7: F821 Undefined name `dict_`
...
Found 62 errors.
No fixes available (2 hidden fixes can be enabled with the `--unsafe-fixes` option).
```

> ruff format --line-length 80

ruff check --exclude  '**/outcomes/**' --exclude '**/import_check/example/**' --output-format concise --fix

ruff check --output-format concise

