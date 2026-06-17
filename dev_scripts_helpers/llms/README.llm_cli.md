# `llm_cli.py`: Workflow & Architecture

## Summary
`llm_cli.py` is a general-purpose CLI for applying LLM transformations to text
files or inline text, wrapping `helpers.hllm_cli.apply_llm()` into a pipeline:
- read input
- (optionally extract a chunk)
- select a system prompt 
- call an LLM
- (optionally lint)
- write output

- Supports:
  - multiple input sources (file, stdin, inline text)
  - chunk selection with reassembly
  - flexible prompt sources (inline/file/rule/skill)
  - 3 backend implementations (library, executable, mock)

## Structure of the Dir
- This directory contains the CLI layer and orchestration logic:
  - `llm_cli.py`: CLI entry point with argparse and `_main()`
  - `lib_llm_cli.py`: Orchestration logic for input resolution, chunk extraction,
    full-text processing, prompt resolution, and lint routing

## Description of Executables

### Llm_cli.py

#### What It Does
General-purpose CLI to apply LLM transformations to text files or text input

- Supports multiple input sources: file, stdin, inline text
- Chunk selection with file reassembly (select mode)
- Flexible system prompts: inline string, file, rule spec, skill reference
- 3 backend implementations: library (fastest, with cost tracking), executable
  (subprocess), mock (testing only)
- Optional output linting, progress bars, token cost tracking, dry-run preview
one.

### Specifying a rule

// TODO(gp): Improve 

- Execute a rule on a single file using one of these formats:
  - Full path (path:line:header format with header validation)
    ```
    --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions"
    ```
  - Line number only (extracts the section starting at that line)
    ```
    --rule ".claude/skills/coding.rules.md:58"
    ```
  - Keyword search: (searches for unique matching rule using rigrule)
    ```
    --rule "dassert"
    ```

### Selecting

// TODO(gp): Improve 

            r"""Select text range as START:END
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
"""

#### Examples
- Simplest test:
  ```
  > llm_cli.py --input_text " " -p "Explain recursion in 100 words" -o - --dry_run
  > llm_cli.py --input_text "Explain recursion in 10 words" -o -
  ```

- Basic file transform with inline prompt:
  ```bash
  > llm_cli.py -i input.txt -o output.txt -p "Summarize this"
  ```

- In-place editing of a file:
  ```bash
  > llm_cli.py -i input.txt
  ```

- Read from stdin, write to stdout:
  ```bash
  > echo "What is 2+2?" | llm_cli.py -i - -o -
  ```

- Read from stdin, write to file:
  ```bash
  > cat input.txt | llm_cli.py -i - -o output.txt
  ```

- Input text via command line:
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output output.txt
  ```

- Print to screen instead of file:
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output -
  > llm_cli.py -i input.txt -o -
  ```

- With system prompt from file:
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt_file system_prompt.txt
  ```

- With system prompt and specific model:
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt "You are a helpful assistant" \
      --model gpt-4
  ```

- With progress bar (auto-estimates output size):
  ```bash
  > llm_cli.py -i input.txt -o output.txt -b
  > llm_cli.py -i input.txt -o output.txt --progress_bar
  ```

- With progress bar and explicit output size:
  ```bash
  > llm_cli.py -i input.txt -o output.txt --expected_num_chars 5000
  ```

- With automatic output linting:
  ```bash
  > llm_cli.py -i input.txt -o output.txt --lint
  > llm_cli.py -i input.txt --lint
  ```

- Apply single rule from rules file to chunk (in place):
  ```bash
  > llm_cli.py \
      -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt \
      --rule '.claude/skills/slides.rules.md:58:# Slide Organization' \
      -m
  ```

- Apply entire skill to file (in place):
  ```bash
  > llm_cli.py \
      -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt \
      --skill slides.criticize_structure
  ```

- Apply prompt to chunk of file selected by line range (in place):
  ```bash
  > llm_cli.py \
      -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt \
      --select 133:162 \
      -pf .claude/skills/slides.fix_errors/SKILL.md \
      -m
  ```

- Apply style to graphviz diagram in place:
  ```bash
  > llm_cli.py \
      -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt \
      --select 205 \
      -pf .claude/templates/graphviz.template.md \
      -m
  ```

- Fix errors in specific slide selection with linting:
  ```bash
  > llm_cli.py \
      -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt \
      --select 482 \
      -pf .claude/skills/slides.fix_errors/SKILL.md \
      --lint \
      -m
  ```

- Test a model via OpenRouter:
  ```bash
  > llm_cli.py \
      --input_text "Say hello" \
      --model "openrouter/anthropic/claude-haiku-4.5" \
      --backend executable \
      -o -
  ```

- Summarize text with linting:
  ```bash
  > llm_cli.py -p "Summarize in 5 bullets, <200 words" \
      -i We_should_be_more_tired_than_the_model.hn_comments.txt \
      --model openrouter/anthropic/claude-haiku-4.5 --lint
  ```

- Dry run to verify prompt/input before spending credits:
  ```bash
  > llm_cli.py -i input.txt -p "Translate to French" --dry_run
  ```

- Raw `llm` command passthrough:
  ```bash
  > llm_cli.py --llm_cmd "llm chat --model gpt-4"
  ```

## Architecture

### 3-Layer Stack
- `llm_cli.py` is part of a 3-layer architecture:

<!-- TODO(ai_gp): Convert to mermaid C4 -->

```
┌───────────────────────────────────────────┐
│ llm_cli.py          (151 lines)           │
│ CLI entry point: argparse, _main()        │
├───────────────────────────────────────────┤
│ lib_llm_cli.py      (637 lines)           │
│ Orchestration logic: input resolution,    │
│ select-mode chunking, full-text processing,│
│ prompt resolution, lint routing.          │
├───────────────────────────────────────────┤
│ helpers/hllm_cli.py (1625+ lines)         │
│ Core library: apply_llm() backends,       │
│ batch processing, TokenStats,             │
│ DataFrame integration, argument builder.  │
└───────────────────────────────────────────┘
```

### Pipeline Stages
The script processes data through 5 sequential stages:

**1. Input Resolution**

| Source      | Flag                 | Notes                                           |
| ----------- | -------------------- | ----------------------------------------------- |
| File        | `-i <path>`          | Reads full file content                         |
| stdin       | `-i -`               | Pipe input, e.g. `cat f.txt \| llm_cli.py -i -` |
| Inline text | `--input_text <str>` | Direct text from command line                   |

Resolved by `lib_llm_cli._get_input_output_files()` → returns
`(input_file, input_text, output_file)` tuple

**2. Output Destination**

| Destination | Flag        | Notes                                         |
| ----------- | ----------- | --------------------------------------------- |
| File        | `-o <path>` | Write to file                                 |
| stdout      | `-o -`      | Print to screen                               |
| In-place    | `-m`        | Overwrite input file; requires file input     |
| Default     | _(omitted)_ | Writes in-place to input file (with info log) |

**3. Chunk Extraction (Optional: Select Mode)**
When `--select <token>` is passed, the script:

1. Parses select spec via `hmarsele.parse_select_arg()`: supports line ranges
   (e.g. `133:162`), header titles (e.g. `## Introduction`), slide titles, regex
   patterns
2. Locates chunk boundaries via `hmarsele.get_chunk_bounds()`
3. Extracts only the chunk text for LLM processing
4. After LLM returns, **reassembles** the file: replaces the chunk with the
   LLM's response, preserving everything outside the chunk

This is the main differentiator from a naive file-in/file-out workflow. The
surrounding file content is never sent to the LLM: only the selected chunk

**4. Prompt Resolution**
System prompt comes from exactly one of three mutually exclusive sources:

| Source        | Flag             | Mechanism                                                                          |
| ------------- | ---------------- | ---------------------------------------------------------------------------------- |
| Inline string | `-p <text>`      | Used directly                                                                      |
| File          | `-pf <path>`     | Read from file via `hio.from_file()`                                               |
| Rule file     | `--rule <spec>`  | Extracts a section from a `.rules.md` file via `hmarsele.extract_rule_from_file()` |
| Skill         | `--skill <name>` | Resolved to a SKILL.md path via `hmarsele.find_skill()`                            |

The rule spec format is `path:line:topic`, e.g
`.claude/skills/slides.rules.md:58:# Slide Organization`

**5. LLM Call & Post-Processing**
The actual LLM call goes to `hllmcli.apply_llm()`, which supports 3 backends:

| Backend    | Flag                          | Behavior                                                                    |
| ---------- | ----------------------------- | --------------------------------------------------------------------------- |
| library    | `--backend library` (default) | Calls `llm` Python library directly; can report token costs via `tokencost` |
| executable | `--backend executable`        | Spawns `llm` CLI subprocess; no cost reporting                              |
| mock       | `--backend mock`              | Returns MD5 hash of input+prompt; for testing only                          |

**Optional post-processing**

- **Linting** (`--lint`): formats output via `flowmark` library
- **Dry run** (`--dry_run`): logs what would be sent to the LLM without calling
  it: useful to verify prompt/input selection before spending API credits
- **Character cap** (`--max_chars <N>`): truncates input to N chars (warning
  logged) to avoid context window overflows
- **Stats persistence** (`--stat_file <path>`): saves `TokenStats` (tokens,
  cost, elapsed time) as JSON
- **Progress bar** (`-b` or `--expected_num_chars <N>`): shows a tqdm progress
  bar during LLM streaming

## Core Functions in `lib_llm_cli.py`

### `_llm_cli()`: Main Orchestrator
The central routing function called by `llm_cli.py:_main()`. Sequence:

1. Init logger (suppresses INFO during stdin→stdout pipes unless DEBUG)
2. Optionally install LLM plugins (`llm-openrouter`, `llm-anthropic`)
3. Short-circuit: if `--llm_cmd` passed, execute raw `llm` command and exit
4. Resolve input/output files via `_get_input_output_files()`
5. Estimate expected output chars for progress bar
6. Resolve system prompt via `_get_system_prompt()`
7. Route to **select mode** `_process_selected_text()` or **full-text mode**
   `_process_full_text()`
8. Log token stats and optionally persist to stat file

### `_process_selected_text()`: Select Mode
For `--select` operations. Flow:
```
read input file → parse select markers → locate chunk bounds
→ extract chunk → (cap with max_chars) → apply_llm() → (lint)
→ splice response back into file → write (in-place or output)
```

Returns `TokenStats`

### `_process_full_text()`: Full-text Mode
For all other operations (input text, file, stdin). Flow:
```
read input (string / file / stdin) → (cap with max_chars)
→ apply_llm() → (lint) → write to output
```

Returns `TokenStats`

### `_get_input_output_files()`: I/O Resolution
Determines `(input_file, input_text, output_file)` from CLI args. Handles stdin
(`-`), in-place editing, and output-to-stdout cases

### `_get_system_prompt()`: Prompt Resolution
Reads system prompt from one source: file path, rule spec, or inline string
Validates exactly one is provided

## Helper Functions
| Function                    | Purpose                                                                    |
| --------------------------- | -------------------------------------------------------------------------- |
| `_limit_input_text()`       | Truncates input to `max_chars` with warning                                |
| `_get_expected_num_chars()` | Estimates output size for progress bar from input length or explicit value |
| `install_models()`          | Installs `llm-openrouter` and `llm-anthropic` plugins if missing           |
| `execute_llm_command()`     | Runs arbitrary `llm ...` shell commands                                    |
| `_is_plugin_installed()`    | Checks if an llm plugin module is registered                               |
| `_log_plugin_versions()`    | Logs all installed `llm*` package versions                                 |

## Backend Architecture (`helpers/hllm_cli.py`)
Three backends implement the same interface
`(input_str, system_prompt, model, expected_num_chars) → (response, TokenStats)`:
```
apply_llm()
  ├── backend="library"
  │   └── _apply_llm_via_library()
  │       └── llm.get_model().prompt()  (streaming or bulk)
  ├── backend="executable"  
  │   └── _apply_llm_via_executable()
  │       └── subprocess: llm --system <prompt> --model <model> <input>
  └── backend="mock"
      └── _apply_llm_via_mock()
          └── MD5(input + system_prompt)
```

- The `library` backend can report token-level costs via `tokencost` when
  available; the `executable` backend cannot (costs report 0)

## TokenStats
`TokenStats` (`@dataclass`) is the cost-accounting unit:
```
input_tokens, output_tokens,
cost_from_tokencost, cost_from_llm_library,
elapsed_time_in_seconds, tokens_per_second
```

Key methods:

| Method                      | Purpose                                                          |
| --------------------------- | ---------------------------------------------------------------- |
| `to_str()`                  | Human-readable cost string (`$X.XX`, `X.XXc`, or `X.XXu$`)       |
| `to_float()`                | Single cost value (prefers tokencost, falls back to llm library) |
| `aggregate(list)`           | Sums multiple TokenStats into one                                |
| `to_file()` / `from_file()` | JSON persistence                                                 |

## Batch Processing (Library Layer)
`helpers/hllm_cli.py` provides batch processing for DataFrame workflows via
`apply_llm_prompt_to_df()` with 3 modes:

| Mode          | Function                               | Behavior                                                               |
| ------------- | -------------------------------------- | ---------------------------------------------------------------------- |
| individual    | `apply_llm_batch_individual()`         | N independent LLM calls, one per item                                  |
| shared_prompt | `apply_llm_batch_with_shared_prompt()` | Single `llm.Conversation`, items share context                         |
| combined      | `apply_llm_batch_combined()`           | All items in one prompt, expects JSON output; retries on parse failure |

The batch pipeline chunks items into configurable batch sizes, skips empty
values, tracks progress via tqdm, and aggregates costs. This is used by
higher-level scripts (e.g., `ai_review.py`) but not by `llm_cli.py` directly

## Error Handling & Guard Rails
- **Mutual exclusion**: Input via file XOR text XOR stdin (argparse mutual
  exclusion group). System prompts via inline XOR file XOR rule
- **In-place constraint**: `-m` requires file input, not stdin or inline text
- **Select constraint**: Select mode requires file input
- **Empty input**: Asserted non-empty for text input
- **Progress bar constraint**: `expected_num_chars` must be > 0
- **Backend validation**: Only `"executable"`, `"library"`, `"mock"` accepted
- **Cost divergence warning**: When both tokencost and llm library report cost
  but values differ, a warning is logged

## Usage Patterns

- Basic File Transform
```bash
llm_cli.py -i input.txt -o output.txt -p "Summarize this"
```

- In-place Chunk Transform (select Mode)
```bash
llm_cli.py -i doc.txt --select "## Introduction" -pf prompt.txt -m
```

- Rule-guided Transform
```bash
llm_cli.py -i slides.txt --rule '.claude/skills/slides.rules.md:58:# Slide Organization' -m
```

- Pipeline with Stdin/stdout
```bash
cat notes.txt | llm_cli.py -i - -o - -p "Fix grammar" --backend library
```

- Dry Run to Verify Prompt/input Before Spending Credits
```bash
llm_cli.py -i input.txt -p "Translate to French" --dry_run
```

- Arbitrary Llm Command Passthrough
```bash
llm_cli.py --llm_cmd "llm chat --model gpt-4"
```

- Basic usage with input and output files
  ```bash
  > llm_cli.py --input input.txt --output output.txt
  > llm_cli.py -i input.txt -o output.txt
  ```

- In-place editing (writes back to input file)
  ```bash
  > llm_cli.py --input input.txt
  > llm_cli.py -i input.txt
  ```

- Read from stdin and write to stdout
  ```bash
  > echo "What is 2+2?" | llm_cli.py --input - --output -
  ```

- Read from stdin and write to file
  ```bash
  > echo "What is 2+2?" | llm_cli.py --input - --output output.txt
  > cat input.txt | llm_cli.py -i - -o output.txt
  ```

- Basic usage with input text
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output output.txt
  ```

- Print to screen instead of file
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output -
  > llm_cli.py -i input.txt -o -
  > echo "What is 2+2?" | llm_cli.py -i - -o -
  ```

- Use llm CLI executable instead of library
  ```bash
  > llm_cli.py -i input.txt -o output.txt --use_llm_executable
  ```

- With system prompt and specific model
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt "You are a helpful assistant" \
      --model gpt-4
  ```

- With system prompt from file
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt_file system_prompt.txt
  ```

- With automatic progress bar (estimates output size)
  ```bash
  > llm_cli.py -i input.txt -o output.txt -b
  > llm_cli.py -i input.txt -o output.txt --progress_bar
  ```

- With progress bar and explicit output size
  ```bash
  > llm_cli.py -i input.txt -o output.txt --expected_num_chars 5000
  ```

- Apply linting to output file after processing
  ```bash
  > llm_cli.py -i input.txt -o output.txt --lint
  > llm_cli.py -i input.txt --lint  # In-place editing with linting
  ```

// TODO(ai_gp): Fix this

- Apply a single Claude rule to an entire set of slides (in place)
  ```bash
  > llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt --rule '.claude/skills/slides.rules.md:58:# Slide Organization'
  ```

- Apply an entire skill to an entire file (in place)
  ```
  > llm_cli.py -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt --skill slides.criticize_structure
  ```
  - `--skill slides.criticize_structure` is a shortcut for
    `-pf .claude/skills/slides.criticize_structure/SKILL.md`

- Apply a prompt to a chunk of file selected with lines (`--select X:Y`) in place
  (`-m`)
  ```
  > llm_cli.py -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt --select 133:162  -pf .claude/skills/slides.fix_errors/SKILL.md -m
  ```

- Apply a style to graphviz in place
  ```
  > llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt --select 205 -m -pf .claude/templates/graphviz.template.md
  ```

- Apply 
  ```
  llm_cli.py -i msml610/lectures_source/Lesson06.2-Using_Bayesian_Networks.txt -pf /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/slides.fix_errors/SKILL.md --select 482 --lint -m
  ```

- Test a model
  ```
  > llm_cli.py --input_text "Say hello" --model "openrouter/anthropic/claude-haiku-4.5" --backend executable -o -
  Hello! 👋 How are you doing today? Is there anything I can help you with?
  Total cost: Cost: 0.00u$, Elapsed: 8.47s (input_tokens=0, output_tokens=0, cost_from_llm_library=0.0, cost_from_tokencost=0.0, )
  ```

- Summarize text and then lint the answer
  ```
  > llm_cli.py -p "Summarize the following text in 5 bullet points and less than 200 words" --input We_should_be_more_tired_than_the_model.hn_comments.txt --model openrouter/anthropic/claude-haiku-4.5 --lint
  ```

- Apply a single rule
  ```
  > llm_cli.py  --rule '.claude/skills/slides.rules.md:58:# Slide Organization'
  ```

## Argument Reference

| Flag                           | Dest                | Default       | Description                           |
| ------------------------------ | ------------------- | ------------- | ------------------------------------- |
| `-i` / `--input`               | input               |: | Input file path or `-` for stdin      |
| `--input_text`                 | input_text          |: | Input text from command line          |
| `-o` / `--output`              | output              | `""`          | Output file or `-` for stdout         |
| `-m` / `--modify_in_place`     | modify_in_place     | `False`       | Edit input file in-place              |
| `-p` / `--system_prompt`       | system_prompt       | `""`          | System prompt inline                  |
| `-pf` / `--system_prompt_file` | system_prompt_file  | `""`          | System prompt from file               |
| `--rule`                       | rule                | `""`          | Rule spec (`file:line:topic`)         |
| `--select`                     | select              | `""`          | Chunk selection (line/header/regex)   |
| `--model`                      | model               | `gpt-4o-mini` | LLM model name                        |
| `--backend`                    | backend             | `library`     | Backend: library, executable, mock    |
| `--lint`                       | lint                | `False`       | Lint output after processing          |
| `--dry_run`                    | dry_run             | `False`       | Preview without calling LLM           |
| `--max_chars`                  | max_chars           | `0`           | Truncate input to N chars             |
| `-b` / `--progress_bar`        | progress_bar        | `False`       | Show progress bar                     |
| `--expected_num_chars`         | expected_num_chars  | `0`           | Explicit output size for progress bar |
| `--stat_file`                  | stat_file           | `""`          | JSON path for token stats             |
| `--llm_cmd`                    | llm_cmd             | `""`          | Raw llm command to execute            |
| `--install_llm_plugins`        | install_llm_plugins | `False`       | Install llm plugins before processing |
| `--log_level`                  | log_level           |: | Verbosity level                       |

- The architecture of the script has several stages:
  - Read input:
      - `--input <file>`: it can be a file, stdin (using `-`)
      - `--input_text <text>`: text specified via command line
  - (Optional) Extract a chunk of input:
      - `--select <token>`: various selection criteria
      - `--modify_in_place`: replace a chunk of file with the output
  - Select a prompt:
      - `-p`: prompt specified from command line
      - `-pf <file>`: prompt from a file
      - `--rule <topic>`: use a file from a `.claude/skills/<topic>.rules.md`
      - `--skill <skill>`: use a file from a `.claude/skill/<skill>/SKILL.md`
  - (Optional)
    - `--lint`: A linting step
  - Write output
      - `--output`: it can be a file, stdout (using `-`), or in place (`-m`)


- Models are specified in the same way used for `llm`
  - `anthropic/claude-haiku-4-5-20251001`
  - `anthropic/claude-opus-4.8`
  - `anthropic/claude-sonnet-4.6`
  - `gpt-4o-mini`
  - `openrouter/anthropic/claude-haiku-4.5`
  - `openrouter/deepseek/deepseek-v4-flash`
  - `openrouter/meta-llama/llama-3.1-8b-instruct`
  - `openrouter/openai/gpt-oss-120b`
  - `openrouter/openai/gpt-oss-20b`

// TODO(ai_gp): Improve this
- Note that you can't use Claude Subscription with llm_cli.py since you don't
  have an API key for metered
