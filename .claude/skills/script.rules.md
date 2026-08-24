- This document contains conventions for CLI scripts

# Script Skeleton

## Follow the `_parse()` / `_main(parser)` Structure

- Every script defines exactly these two functions, plus an entry guard
  ```python
  def _parse() -> argparse.ArgumentParser:
      parser = argparse.ArgumentParser(
          description=__doc__,
          formatter_class=hparser.CustomHelpFormatter,
      )
      ...
      return parser


  def _main(parser: argparse.ArgumentParser) -> None:
      args = parser.parse_args()
      hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
      ...


  if __name__ == "__main__":
      _main(_parse())
  ```
- Follow the template `dev_scripts_helpers/coding_tools/script_template.py`

## Template Script for Processing Input/Output
- A script that reads from stdin/file and writes to stdout/file follows
  `dev_scripts_helpers/coding_tools/transform_template.py`

## Template Script for Parallel Workload
- A script that runs a workload in parallel follows
  `dev_scripts_helpers/coding_tools/parallel_script_template.py`

## `_parse()` Returns the Parser, Never a `Namespace`

- `_parse()` builds and returns the `argparse.ArgumentParser`; it must never
  call `.parse_args()` itself
- `_main(parser)` is the only place that calls `parser.parse_args()`, exactly
  once

- **Bad**: `_parse()` parses args itself, so `_main()` gets a `Namespace` and
  calling `.parse_args()` on it crashes
  ```python
  def _parse() -> argparse.Namespace:
      parser = argparse.ArgumentParser(...)
      return parser.parse_args()


  def _main(parser: argparse.Namespace) -> None:
      args = parser.parse_args()  # AttributeError: Namespace has no parse_args
  ```
- **Good**: `_parse()` returns the parser, `_main()` parses once
  ```python
  def _parse() -> argparse.ArgumentParser:
      parser = argparse.ArgumentParser(...)
      return parser


  def _main(parser: argparse.ArgumentParser) -> None:
      args = parser.parse_args()
  ```

## Use the Module Docstring as the Parser Description

- Pass `description=__doc__` instead of hardcoding a separate description
  string, and set `formatter_class=hparser.CustomHelpFormatter`
- This keeps the `--help` output and the module docstring in sync
- **Bad**
  ```python
  """
  Script to process data files.
  """


  def _parse() -> argparse.ArgumentParser:
      parser = argparse.ArgumentParser(description="Script to process data files.")
      return parser
  ```
- **Good**
  ```python
  """
  Script to process data files.
  """

  import helpers.hparser as hparser


  def _parse() -> argparse.ArgumentParser:
      parser = argparse.ArgumentParser(
          description=__doc__,
          formatter_class=hparser.CustomHelpFormatter,
      )
      return parser
  ```

## Document Usage Examples in the Docstring

- Introduce usage examples with the markdown header `# Usage Example`
- Format each example as a bullet point (short description ending in `:`)
  followed on the next line by the command prefixed with `>`, separated from
  the next example by a blank line
- Refer to the script by its simple filename: no full path, no leading `./`,
  no `python` prefix, since scripts are executable and `PATH`-resolved

- **Bad**
  ```python
  """
  Usage: python ./convert_epub_to_md.py input.epub output.md
  """
  ```
- **Good**
  ```python
  """
  # Usage Example

  - Print the GitHub URL for a file on the current branch:
  > to_github.py --input helpers/hdbg.py

  - Print the GitHub URL and open it in the default web browser:
  > to_github.py --input helpers/hdbg.py --open
  """
  ```

## Make Scripts Executable

- Every script has a shebang (`#!/usr/bin/env python`) and is `chmod +x`'d so
  it runs as `./script.py` without a `python` prefix

- If the script needs external (non-stdlib, non-`helpers`) packages, use the
  `uv run` shebang with inline dependencies instead:
  ```python
  #!/usr/bin/env -S uv run

  # /// script
  # dependencies = ["pydeps", "networkx", "pyyaml", "graphviz"]
  # ///
  ```

# Standard Argument Helpers

## Prefer the Canonical Helper Over Hand-Rolled Flags

- Before adding a new flag, check the catalog below for an equivalent option
  group; if one exists, call that helper instead of hand-rolling the flags
- A hand-rolled equivalent is any of:
  - A differently-named flag for the same concept (`--out_dir` instead of
    `--dst_dir`, `--preview` instead of `--dry_run`)
  - A one-sided boolean (`--foo` with no `--no_foo`)
  - A same-named flag with different/incompatible semantics
- Import the module under its standard alias and call the helper in `_parse()`
  ```python
  import helpers.hselect_input_output as hseinout
  import helpers.hparser as hparser

  def _parse() -> argparse.ArgumentParser:
      parser = argparse.ArgumentParser(...)
      hseinout.add_input_output_args(parser, in_required=True, out_required=False)
      hparser.add_verbosity_arg(parser)
      return parser
  ```
- **Bad**: hand-rolled input/output flags
  ```python
  parser.add_argument("--in_file", type=str, required=True)
  parser.add_argument("--out_file", type=str, default="")
  ```
- **Good**: canonical helper, standard `-i/--input` / `-o/--output` surface
  ```python
  hseinout.add_input_output_args(parser, in_required=True, out_required=False)
  ```

## Verbosity Arg Is Mandatory, Paired With `init_logger`

- Every script calls `hparser.add_verbosity_arg(parser)` in `_parse()` and
  `hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)` as the
  first line of `_main()`

- **Bad**: missing `use_exec_path`, or call is conditional
  ```python
  hdbg.init_logger(args.log_level)
  ```
  ```python
  if args.log:
      hdbg.init_logger(verbosity=args.log_level)
  ```
- **Good**
  ```python
  hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
  ```

## Do Not Use `action="store_true"` for a Path-Valued Flag

- A flag that carries a path or string value must use `action="store"` (the
  default), never `action="store_true"`, even if it also sets a default
- **Bad**: `--dst_dir` can never be set to a custom directory from the CLI
  ```python
  parser.add_argument("--dst_dir", action="store_true", default="./out")
  ```
- **Good**
  ```python
  parser.add_argument("--dst_dir", action="store", default="./out")
  ```

## Catalog of Option Groups

- Each entry gives the helper to call and the exact flags/help text it adds;
  do not restate this help text by hand in a script's own `add_argument()`
  calls

### File Selection
- Use `helpers.hselect_input_output.add_file_selection_args()`

  ```verbatim
  -i, --input FILE      Select a single file
  --files FILES
                        Select specific files (space-separated list in a single argument)
  --from_file FROM_FILE
                        Path to file containing one file path per line
  --modified            Select only files modified in the client (staged and unstaged)
  --branch              Select only files modified with respect to the branch point
  --last_commit         Select only files part of the previous commit
  --all_files            Select all repo files
  ```

### Input/Output
- Use `helpers.hselect_input_output.add_input_output_args()`

  ```verbatim
  -i, --input INPUT     Input file or `-` for stdin
  -o, --output OUTPUT   Output file or `-` for stdout
  --input_files INPUT_FILES [INPUT_FILES ...]
                        One or more files (space-separated, shell globs
                        supported) or comma-separated list
  --from_file FROM_FILE
                        Path to a file containing a list of files to process
                        (one per line)
  ```

<!-- TODO(ai_gp): rename `--input_files` to `--files` to match
`add_multi_file_args()` below -->

### Destination Directory
- Use `helpers.hselect_input_output.add_dst_dir_arg()`

  ```verbatim
  --dst_dir DST_DIR     Directory storing the results
  --overwrite           Delete existing destination directory if it already exists
  ```

### Limit Range
- Use `helpers.hselect_input_output.add_limit_range_arg()`

  ```verbatim
  --limit LIMIT         Limit processing to item range X:Y (integers >= 1, inclusive)
  ```

### Multi-file Selection
- Use `helpers.hselect_input_output.add_multi_file_args()`

  ```verbatim
  --files FILES         Comma-separated list of files to process (e.g.,
                        'file1.txt,file2.txt,file3.txt')
  --from_files FROM_FILES
                        Path to file containing one file path per line
  -i, --input INPUT     File to process (can be specified multiple times)
  ```

### File Type Filtering
- Use `helpers.hselect_input_output.add_file_type_filter_args()`
  ```verbatim
  --file_types FILE_TYPES
                        Comma-separated list of file extensions to process.
                        - Available: py (Python), ipynb (Jupyter), md
                          (Markdown), txt (Text)
                        - Default: 'py,ipynb,md'
  --skip_file_types SKIP_FILE_TYPES
                        Comma-separated list of file extensions to skip (e.g.,
                        'txt')
                        - Empty string means skip no extensions
  ```

### Boolean On/off
- Use `helpers.hparser.add_bool_arg()`
  ```verbatim
  --run_diff_script
  --no_run_diff_script
  ```

### Verbosity
- Use `helpers.hparser.add_verbosity_arg()`
  ```verbatim
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --no_report_command_line
                        Disable printing of executed commands
  ```

### JSON Output Metadata
- Use `helpers.hparser.add_json_output_metadata_args()`
  ```verbatim
  --json_output_metadata JSON_OUTPUT_METADATA
                        File storing the output metadata of this script in JSON
                        format
  ```

### Action Selection
- Use `helpers.hselect_action.add_action_arg()`
  ```verbatim
  --action ACTION       Add an action to the list of actions to execute
  --skip_action SKIP_ACTION
                        Remove an action from the list of actions to execute
  --all_actions         Run all the valid actions (a b c)
  --clear_actions       Start from an empty list of actions

  ## Available actions:
  - a
  - b
  - c

  ## Default actions:
  - a
  - b
  ```

### Markdown Select
- Use `helpers.hmarkdown_select.add_select_arg()`
  ```verbatim
  --select SELECT       Select text range as START:END
                        Examples:
                        - '## Section 1:## Section 2'"
                        - 'Section 1:Section 2',
                        - ':END'
                        - 'START:' (extracts until next same-level header)
                        - 'START' (extracts until next same-level header)
                        - 'START:END' (where END is 'END' for EOF)
                        - START/END can be a
                            - header (with # or * prefix)
                            - title substring
                            - line number
  ```

### Rule
- Use `helpers.hmarkdown_select.add_rule_cli_arg()`
  ```verbatim
  --rule RULE           Rule specification used as system prompt. Formats:
                        - 'path/to/rules.md': whole file
                        - 'path/to/rules.md:LINE': header section at LINE
                        - 'path/to/rules.md:LINE:# Section Name': with name validation
                        - 'dassert': a single result of rigrule
  ```

### Cache Control
- Use `helpers.hcache_simple.add_cache_control_arg()`
  ```verbatim
  --cache_mode {REFRESH_CACHE,DISABLE_CACHE,HIT_CACHE_OR_ABORT}
                        Override cache behavior for all cache functions. REFRESH_CACHE
                        repopulates, DISABLE_CACHE bypasses, HIT_CACHE_OR_ABORT raises on miss.
  --cache_debug         Log at WARNING level for every cache call whether the result was
                        served from cache, computed on miss, or recomputed because of `cache_mode`
  ```

### Daemon
- Use `helpers.hdaemon.add_daemon_arg()`
  ```verbatim
  --daemon              Watch input file for changes and regenerate on change
  ```

### Open
- Use `helpers.hdocker.add_open_arg()`
  ```verbatim
  --open                Open the output file on macOS
  ```
- Pair with `helpers.hdocker.open_file_on_macos()` to act on the flag; do not
  duplicate either function locally

### Dockerized Script
- Use `helpers.hdocker.add_dockerized_script_arg()`
  ```verbatim
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  ```

### Parallel Processing
- Use `helpers.hjoblib.add_parallel_processing_arg()`
  ```verbatim
  --dry_run             Print the workload and exit without running it
  --no_incremental      Skip workload already performed
  --force               Confirm that one wants to remove the previous results. It works
                        only together with --no_incremental
  --num_threads NUM_THREADS
                        Number of threads to use:
                        - '-1' to use all CPUs;
                        - '1' to use one-thread at the time but using the parallel execution
                          (mainly used for debugging)
                        - 'serial' to serialize the execution without using parallel execution
  --no_keep_order
  --num_func_per_task NUM_FUNC_PER_TASK
                        Number of function execute in a (parallel) task of the workload.
                        `None` means automatically decided by the function
  --skip_on_error       Continue execution after encountering an error
  --num_attempts NUM_ATTEMPTS
                        Repeat running an experiment up to `num_attempts` times
  ```

### LLM Prompt
- Use `helpers.hllm_cli.add_llm_prompt_arg()`
  ```verbatim
  --debug               Print before/after the transform
  -p, --prompt PROMPT   Prompt to apply
  -f, --fast_model      Use a fast LLM model vs a high-quality one
  ```

### LLM
- Use `helpers.hllm_cli.add_llm_args()`
  ```verbatim
  -i, --input INPUT     Path to the input file containing text to process, or '-' for stdin
  --input_text INPUT_TEXT
                        Text input to process directly from command line
  -o, --output OUTPUT   Path to the output file where result will be saved (use '-' to
                        print to screen). If not specified, writes in-place to the input file
  -p, --system_prompt SYSTEM_PROMPT
                        Optional system prompt to guide the LLM's behavior
  --pf, --system_prompt_file SYSTEM_PROMPT_FILE
                        Optional path to file containing system prompt to guide the LLM's behavior
  --rule RULE           Rule specification used as system prompt (see the Rule group above)
  --model MODEL         Optional model name to use (e.g., 'gpt-4', 'claude-3-opus').
                        Default: openrouter/deepseek/deepseek-v4-flash
  --backend {executable,library,mock}
                        LLM backend to use: 'executable' (CLI), 'library' (Python), or 'mock' (testing)
  -b, --progress_bar    Enable progress bar with automatic estimation (input length * 1.0)
  --expected_num_chars EXPECTED_NUM_CHARS
                        Expected number of characters in output (enables
                        progress bar with explicit size)
  ```

### S3
- Use `helpers.hs3.add_s3_args()`
  ```verbatim
  --aws_profile AWS_PROFILE
                        The AWS profile to use for `.aws/credentials` or for env vars
  --s3_path S3_PATH     Full S3 dir path to use (e.g., `s3://alphamatic-data/foobar/`),
                        overriding any other setting
  ```

### Config Override
- Use `config_root.config.config_utils.add_config_override_args()`
  ```verbatim
  --set_config_value SET_CONFIG_VALUE
                        See `apply_config()` for detailed description.
  ```

### Pandoc Backend
- Use `dev_scripts_helpers.dockerize.lib_pandoc.add_pandoc_backend_arg()`
  ```verbatim
  --pandoc_backend {auto,dockerized,host}
                        How to run `pandoc`: `auto` uses the host binary and falls back to
                        Docker otherwise, `dockerized` always runs pandoc in Docker, `host`
                        always runs the host binary
  ```

# Dry Run

## Add `--dry_run` as a Standard Flag

- If the script already calls `helpers.hjoblib.add_parallel_processing_arg()`
  (see the Parallel Processing catalog entry above), `--dry_run` comes for
  free; do not redeclare it
- Otherwise declare it by hand as a plain boolean flag
  ```python
  parser.add_argument(
      "--dry_run",
      action="store_true",
      help="Show what would be done without actually doing it",
  )
  ```
- Thread `dry_run` through function signatures as a keyword-only `bool`
  parameter, not a global; the only place that reads `args.dry_run` is
  `_main()`

## Guard the Side Effect, Not the Whole Function

- Wrap only the code that mutates state (file writes, network calls,
  subprocess execution, git/gh commands) in `if dry_run: ... else: ...`; keep
  computing and logging surrounding context (counts, paths, plans) outside
  the guard so a dry run still produces useful output
- Mirror the real branch's log message in the dry-run branch, just prefixed
  with the `[DRY_RUN]` tag and phrased as "Would ..."
- **Good** (`dev_scripts_helpers/thin_client/create_all_helpers_links.py`)
  ```python
  if dry_run:
      _LOG.warning("[DRY_RUN] Would create '%s' to vimdiff %d file(s)", target_path, num_files)
  else:
      _LOG.info("Creating '%s' to vimdiff %d file(s)", target_path, num_files)
      _create_link(...)
  ```
- For a top-level command wrapper that runs a single blocking operation
  (`helpers.hsystem.system()`, `helpers.hjoblib.parallel_execute()`), an
  early return right after the log line is fine, since there's no separate
  "real" branch left to fall through to
  ```python
  if dry_run:
      _LOG.warning("As per user request, not executing command:\n%s", cmd)
      return 0, ""
  ```

## Log With `_LOG.warning`, Never `_LOG.info` or `print`

- Dry-run notices use `_LOG.warning` so they stand out from the surrounding
  INFO-level narration regardless of `-v`

- **Bad**
  ```python
  _LOG.info("[DRY_RUN] Would remove '%s'", path)
  ```
- **Good**
  ```python
  _LOG.warning("[DRY_RUN] Would remove '%s'", path)
  ```

## Tag Every Message With the Literal `[DRY_RUN]` Prefix

- Prefix with `[DRY_RUN]`: underscore, all caps, matching the flag's own name (see
  "Underscore Case, Not Hyphens" below), so the tag is greppable and consistent with
  the flag it reports on
- Follow the tag with "Would <verb>" describing the skipped action, then the same
  `%s`/`%d` lazy-formatting arguments the real branch's message would use (see the
  logging conventions in `coding.rules.md`)

- **Bad**
  ```python
  _LOG.info("[DRY-RUN] Would create field: '%s'", name)
  _LOG.warning("DRY RUN: Would save to %s", output_file)
  ```
- **Good**
  ```python
  _LOG.warning("[DRY_RUN] Would create '%s' to vimdiff %d file(s)", target_path, num_files)
  _LOG.warning("[DRY_RUN] Would save merged summary to '%s'", output_file)
  ```

## Test That the Side Effect Did Not Happen

- A unit test for `dry_run=True` asserts the absence of the side effect
  (e.g., `hdbg.dassert_path_not_exists(...)`), not just that the call didn't
  raise
- **Good** (`helpers/test/test_hsystem.py`)
  ```python
  def test_dry_run(self) -> None:
      temp_file_name = ...
      hsystem.system("ls", output_file=temp_file_name, dry_run=True)
      hdbg.dassert_path_not_exists(temp_file_name)
  ```

# Command-Line Argument Naming and Style

## Underscore Case, Not Hyphens

- Use only underscores as separators in flag names, for both the long-form
  name and the resulting `Namespace` attribute
- **Bad**: `--dry-run`, `--skip-post-transforms`, `--operation-ids`
- **Good**: `--dry_run`, `--skip_post_transforms`, `--operation_ids`

## Match the Canonical Name, Even When a Helper Does Not Apply

- When a concept has no dedicated helper but overlaps one that does (e.g., a
  script-specific "skip processing without side effects" flag), name it after
  the closest canonical flag (`--dry_run`, not `--preview`) so scripts stay
  greppable and consistent
- If a flag name would collide with a standard one but mean something
  different (e.g., a script's own `--action` with fixed `choices=` instead of
  the composable action registry), rename the script's flag instead of
  reusing the standard name with different semantics

## Provide the Standard Short Alias

- `-i`/`-o` are reserved for input/output; give them to any flag playing that
  role, and do not repurpose them for something else
- **Bad**: `--output` with no `-o`
- **Good**: `-o, --output`

## Do Not Repeat Default Values in Help Text

- The `default=` parameter already documents the default; do not restate it
  in `help=`
- **Bad**
  ```python
  parser.add_argument("--browser", default="safari", help="Browser to use (default: safari)")
  ```
- **Good**
  ```python
  parser.add_argument("--browser", default="safari", help="Browser to use")
  ```

## Use Mutually Exclusive Groups for Conflicting Options

- When two options are mutually exclusive, enforce it with
  `parser.add_mutually_exclusive_group()` instead of validating by hand in
  `_main()`
- **Bad**
  ```python
  parser.add_argument("--input_file", default="")
  parser.add_argument("--input_text", default="")

  def _main(args: argparse.Namespace) -> None:
      if args.input_file and args.input_text:
          raise ValueError("Cannot specify both")
  ```
- **Good**
  ```python
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--input_file", default="")
  group.add_argument("--input_text", default="")
  ```

# Renaming or Replacing a Flag

## Update Every Caller, Not Just the Script

- A flag rename or replacement is not done until every reference is updated:
  other scripts that invoke this one, `invoke` tasks
  (`helpers/lib_tasks/lib_tasks_*.py`), and markdown docs (READMEs, this file)
  that mention the old flag name
- Grep for the old flag name repo-wide before considering the change
  complete
  ```bash
  > grep -rn -- "--old_flag_name" --include="*.py" --include="*.md"
  ```
