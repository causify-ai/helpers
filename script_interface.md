- This file contains the information about the parser interface and conventions
  to make scripts have a consistent interface

# Parser functions

## File selection options

- Code: `helpers.hselect_input_output.add_file_selection_args(parser)`

- The output is:
  ```verbatim
    -i, --input FILE      Select a single file

    --files FILES
                          Select specific files (space-separated list in a single argument)
    --from_file FROM_FILE
                          Path to file containing one file path per line
    --modified            Select only files modified in the client (staged and unstaged)
    --branch              Select only files modified with respect to the branch point
    --last_commit         Select only files part of the previous commit
    --all                 Select all repo files
  ```

## Output options

- The output is:
  ```verbatim
    -o, --output FILE
    --output_dir ...
    --output_file
  ```

## File type filtering options

- Code: `helpers.hselect_input_output.add_file_type_filter_args(parser, file_types_default="py,ipynb,md")`

- The output is:
  ```verbatim
    --file_types FILE_TYPES
                          Comma-separated list of file extensions to process (e.g., 'py,ipynb,md,txt') Available: py (Python), ipynb (Jupyter), md (Markdown), txt (Text) Default: 'py,ipynb,md'
    --skip_file_types SKIP_FILE_TYPES
                          Comma-separated list of file extensions to skip (e.g., 'txt') Empty string means skip no extensions
  ```

## Boolean on/off options

- Code: `helpers.hparser.add_bool_arg(parser, "run_diff_script", default_value=True)`

- The output is:
  ```verbatim
    --run_diff_script
    --no_run_diff_script
  ```

## Verbosity options

- Code: `helpers.hparser.add_verbosity_arg(parser)`

- The output is:
  ```verbatim
    -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                          Set the logging level
    --no_report_command_line
                          Disable printing of executed commands
  ```

## Output metadata options

- Code: `helpers.hparser.add_json_output_metadata_args(parser)`

- The output is:
  ```verbatim
    --json_output_metadata JSON_OUTPUT_METADATA
                          File storing the output metadata of this script in JSON format
  ```

## Input/output options

- Code: `helpers.hselect_input_output.add_input_output_args(parser)`

- The output is:
  ```verbatim
    -i, --input INPUT     Input file or `-` for stdin
    -o, --output OUTPUT   Output file or `-` for stdout
    --input_files INPUT_FILES [INPUT_FILES ...]
                          One or more files (space-separated, shell globs supported) or comma-separated list
    --from_file FROM_FILE
                          Path to a file containing a list of files to process (one per line)
  ```

## Destination directory options

- Code: `helpers.hselect_input_output.add_dst_dir_arg(parser, dst_dir_required=False, dst_dir_default=".")`

- The output is:
  ```verbatim
    --dst_dir DST_DIR     Directory storing the results
    --overwrite           Delete existing destination directory if it already exists
  ```

## Limit range options

- Code: `helpers.hselect_input_output.add_limit_range_arg(parser)`

- The output is:
  ```verbatim
    --limit LIMIT         Limit processing to item range X:Y (integers >= 1, inclusive)
  ```

## Multi-file selection options

- Code: `helpers.hselect_input_output.add_multi_file_args(parser)`

- The output is:
  ```verbatim
    --files FILES         Comma-separated list of files to process (e.g., 'file1.txt,file2.txt,file3.txt')
    --from_files FROM_FILES
                          Path to file containing one file path per line
    -i, --input INPUT     File to process (can be specified multiple times)
  ```

## Action selection options

- Code: `helpers.hselect_action.add_action_arg(parser, valid_actions=["a", "b", "c"], default_actions=["a", "b"])`

- The output is:
  ```verbatim
    -a, --action ACTION   Actions to execute (see available actions below)
    -sa, --skip_action SKIP_ACTION
                          Actions to skip from default set (see available actions below)
    -e, --enable ENABLE_ACTION
                          Enable additional actions on top of defaults (see available actions below)
    --all                 Run all the actions (a b)

    Available actions:
    - a
    - b
    - c

    Default actions:
    - a
    - b
  ```

## Markdown select options

- Code: `helpers.hmarkdown_select.add_select_arg(parser, required=False)`

- The output is:
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

## Rule options

- Code: `helpers.hmarkdown_select.add_rule_cli_arg(group)`

- The output is:
  ```verbatim
    --rule RULE           Rule specification used as system prompt. Formats:
                          - 'path/to/rules.md': whole file
                          - 'path/to/rules.md:LINE': header section at LINE
                          - 'path/to/rules.md:LINE:# Section Name': with name validation
                          - 'dassert': a single result of rigrule
  ```

## Cache control options

- Code: `helpers.hcache_simple.add_cache_control_arg(parser)`

- The output is:
  ```verbatim
    --cache_mode {REFRESH_CACHE,DISABLE_CACHE,HIT_CACHE_OR_ABORT}
                          Override cache behavior for all cache functions. REFRESH_CACHE
                          repopulates, DISABLE_CACHE bypasses, HIT_CACHE_OR_ABORT raises on miss.
    --cache_debug         Log at WARNING level for every cache call whether the result was
                          served from cache, computed on miss, or recomputed because of `cache_mode`
  ```

## Daemon options

- Code: `helpers.hdaemon.add_daemon_arg(parser)`

- The output is:
  ```verbatim
    --daemon              Watch input file for changes and regenerate on change
  ```

## Open options

- Code: `helpers.hdocker.add_open_arg(parser)`

- The output is:
  ```verbatim
    --open                Open the output file on macOS
  ```

## Dockerized script options

- Code: `helpers.hdocker.add_dockerized_script_arg(parser)`

- The output is:
  ```verbatim
    --dockerized_force_rebuild
                          Force to rebuild the Docker container
    --dockerized_use_sudo
                          Use sudo inside the container
  ```

## Parallel processing options

- Code: `helpers.hjoblib.add_parallel_processing_arg(parser, num_threads_default="1")`

- The output is:
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

## LLM prompt options

- Code: `helpers.hllm_cli.add_llm_prompt_arg(parser)`

- The output is:
  ```verbatim
    --debug               Print before/after the transform
    -p, --prompt PROMPT   Prompt to apply
    -f, --fast_model      Use a fast LLM model vs a high-quality one
  ```

## LLM options

- Code: `helpers.hllm_cli.add_llm_args(parser)`

- The output is:
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
    --rule RULE           Rule specification used as system prompt (see add_rule_cli_arg above)
    --model MODEL         Optional model name to use (e.g., 'gpt-4', 'claude-3-opus').
                          Default: openrouter/deepseek/deepseek-v4-flash
    --backend {executable,library,mock}
                          LLM backend to use: 'executable' (CLI), 'library' (Python), or 'mock' (testing)
    -b, --progress_bar    Enable progress bar with automatic estimation (input length * 1.0)
    --expected_num_chars EXPECTED_NUM_CHARS
                          Expected number of characters in output (enables progress bar with explicit size)
  ```

## S3 options

- Code: `helpers.hs3.add_s3_args(parser)`

- The output is:
  ```verbatim
    --aws_profile AWS_PROFILE
                          The AWS profile to use for `.aws/credentials` or for env vars
    --s3_path S3_PATH     Full S3 dir path to use (e.g., `s3://alphamatic-data/foobar/`),
                          overriding any other setting
  ```

## Config override options

- Code: `config_root.config.config_utils.add_config_override_args(parser)`

- The output is:
  ```verbatim
    --set_config_value SET_CONFIG_VALUE
                          See `apply_config()` for detailed description.
  ```

## Pandoc backend options

- Code: `dev_scripts_helpers.dockerize.lib_pandoc.add_pandoc_backend_arg(parser, default="auto")`

- The output is:
  ```verbatim
    --pandoc_backend {auto,dockerized,host}
                          How to run `pandoc`: `auto` uses the host binary and falls back to
                          Docker otherwise, `dockerized` always runs pandoc in Docker, `host`
                          always runs the host binary
  ```
