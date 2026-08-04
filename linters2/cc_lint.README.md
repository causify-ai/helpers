# cc_lint.py

Claude Code integration for topic-based formatting.

## What It Does

- Invokes Claude Code with topic-based or skill-based linting rules
- Detects file types by extension and path pattern to select appropriate rules
- Integrates with Claude rules and skills system for formatting and validation
- Supports batch processing with progress bars for multiple files

## Examples

- Format specific Python files based on their types:
  ```bash
  > cc_lint.py --files "file1.py file2.py"
  ```

- Apply a specific coding rule to a file, isntead of the default
  ```bash
  > cc_lint.py --files "file.py" --topic coding
  ```

- Lint modified files in the repository:
  ```bash
  > cc_lint.py --modified
  ```

- Preview command without executing (dry-run), saved to
  `tmp.cc_lint_dry_run.txt` instead of printed to screen:
  ```bash
  > cc_lint.py --dry_run --files "*.md"
  ```

- Process multiple files with progress feedback:
  ```bash
  > cc_lint.py --files "src/*.py" --topic coding
  ```

- Use a different model:
  ```bash
  > cc_lint.py \
    --files dev_scripts_helpers/scraping/download_link_articles.py \
    --skill "coding.add_comments" \
    --model deepseek/deepseek-v4-flash
  ```

- Apply a rule to a file
  ```bash
  > cc_lint.py --files "file.py" --rule <RULE>
  ```

- Only create TODOs instead of applying the transforms
  ```bash
  > cc_lint.py --files "file.py" --add_todos
  ```

## Rule Application Mechanisms

- Execute a rule on a single file using one of these formats:
  - Full path `path:line:header format with header validation`
    ```
    --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions"
    ```
  - Line number only extracting the section starting at that line
    ```
    --rule ".claude/skills/coding.rules.md:58"
    ```
  - Keyword search: searches for unique matching rule using rigrule
    ```
    --rule "dassert"
    ```

- `--mode` controls how rules are applied
  - `one_shot_with_cc` (the default) applies all rules in a single
    Claude Code invocation instead
  - `one_shot`: same prompt as `one_shot_with_cc` but using API instead
    of executable
  - `session`: one session shared across all chunks, for rules that depend on
    each other
  - `stateless`: a fresh session per chunk, giving each chunk uniform cost and
    full attention

- `--mode` is orthogonal to `--topic`/`--skill`/`--rule`: any of them can
  be combined with any `--mode`
  - What gets chunked depends on the combination:
    - `--topic`: one chunk per H1 section across the topic's rule files
    - `--rule`: the rule text, split into one chunk per H1 section when it
      has more than one, else kept as a single chunk
    - `--skill`: a single, non-decomposed `/{skill} {file_path}` chunk
- Preview incremental application without executing, saved to
  `tmp.cc_lint_dry_run.txt` instead of printed to screen:
  ```bash
  > cc_lint.py --files "file.py" --mode stateless --dry_run
  ```

- Every chunk sent as a rule requires a
  structured `LLM> NO-OP` / `LLM> CHANGED: <summary>` reply so a compliant
  rule produces zero edits
  - Useful for complex files requiring step-by-step rule application
- a `--skill` chunk does not, since it invokes Claude Code's own skill loader
  instead of declarative rule prose

## Rules and Chunking Interactions
- Control rule chunking in `--mode session`/`stateless` for `--topic`/default
  path only
  - Split at H1 instead of the default H2, and carry the parent H1 title into
    each H2+ chunk:
    ```bash
    > cc_lint.py --files "file.py" --mode stateless \
        --rule_level 1
    ```
  - Greedily pack consecutive small same-H1 chunks up to a token budget:
    ```bash
    > cc_lint.py --files "file.py" --mode stateless \
        --merge_small_rules --max_chunk_tokens 1500
    ```
  - Drop chunks an LLM pre-pass finds inapplicable to the file, logging what was
    discarded:
    ```bash
    > cc_lint.py --files "file.py" --mode stateless \
        --filter_rules_by_relevance
    ```
  - Reorder chunks via an LLM pre-pass: semantic, then structural, then
    formatting, with the Verification checklist always last:
    ```bash
    > cc_lint.py --files "file.py" --mode stateless \
      --order_rules_by_dependency
    ```
  - These four flags are orthogonal and can be combined so that they are applied
    in order:
    - split (`--rule_level`)
    - merge (`--merge_small_rules`)
    - filter (`--filter_rules_by_relevance`)
    - order (`--order_rules_by_dependency`)

## `--add_todos` mode
- With `--add_todos` instead of applying rules directly, annotate violations with
  comments so a human (or a later pass) can act on them:
  ```
  # TODO(ai_gp): <what to do and why> (<rule_file>:<line_number>:<rule header
  line>)
  ```
  - E.g., a violation of `.claude/skills/testing.rules.md`'s `## Use Context
    Manager Syntax for Multiple Mocks` section becomes:
    ```python
    # TODO(ai_gp): Do this and that (testing.rules.md:1081:## Use Context Manager Syntax for Multiple Mocks)
    ```

- `--add_todos` is orthogonal to `--mode`/`--topic`/`--rule`
  - It cannot be combined with `--skill` since a skill invocation owns its own
    prompt

## Software Architecture

### Data Flow

- `_main()`
  - Selects files
  - Check options and compatibility, e.g.,
    - Asserts that at most one of `--topic`, `--skill`, and `--rule` is set
    - Asserts that `--add_todos` is not combined with `--skill`
  - Loops over files calling `_process_file()`
    - `_process_file()` dispatches on `args.mode` first, then on the "what"
      (`--topic`/`--skill`/`--rule`):
    - `--mode session` / `--mode stateless`:
      - `_process_file_incrementally()` builds the system prompt via
        `_build_incremental_system_prompt()` (role + templates + "do not
        change behavior", plus `_build_add_todos_instructions()` when
        `--add_todos` is set), then builds a message list depending on the
        "what":
        - `--skill`: a single `/{skill} {file_path}` message (via
          `hmarsele.find_skill()`), sent as-is; `--add_todos` has no effect
          here, since the skill owns its own prompt
        - `--rule`: `hmarsele.extract_rule_from_file()`'s text, split into
          per-H1-section messages via `_build_incremental_messages_for_rule()`
          when it carries more than one, else a single message; each
          message's `rule_file` is derived from the part of `--rule` before
          the first `:`
        - `--topic` / default: `_build_incremental_messages()`
          - builds one `RuleChunk` per section across the topic's rule files
            via `_build_rule_chunks()` (split at `--rule_level`, carrying the
            parent H1 title and source rule file into each chunk; merged up
            to `--max_chunk_tokens` when `--merge_small_rules` is set, never
            crossing a rule-file boundary)
          - optionally `_filter_relevant_chunks()` and
            `_order_chunks_by_dependency()` (each one cheap
            `hllmcli.apply_llm()` pre-pass) when `--filter_rules_by_relevance`/
            `--order_rules_by_dependency` are set
          - every chunk is templated by `_build_rule_message()` into a message
            that re-anchors on the target file path and demands a structured
            `LLM> NO-OP` / `LLM> CHANGED: <summary>` reply; with
            `--add_todos`, the message asks Claude Code to check (not
            apply) the rule and cite the chunk's `rule_file`
        - Hands the system prompt and messages to `PromptSequencer.execute()`
          from `dev_scripts_helpers/ai/cc_lib.py`, which
          - Runs under `--mode`'s `context_strategy`: `stateless` opens a
            fresh `ClaudeSDKClient` per message, `session` shares one client
            across all messages
          - Parses each reply's no-op contract via `_parse_rule_outcome()`,
            exposed as `get_outcomes()`
      - `--mode one_shot_with_cc` / mode one_shot`:
        - Both build the exact same prompt via the shared
          `_build_one_shot_prompt()`, mirroring the `--topic`/`--skill`/ `--rule`
          dispatch above (with `_build_prompt()` used for the `--topic`,
          appending
          `_build_add_todos_instructions()` when `--add_todos` is set), and
          only differ in how that prompt is executed:
          - `one_shot_with_cc`: `_run_claude_code()` writes the prompt to
            `tmp.cc_lint.prompt.txt` and shells out to the `cc` wrapper as a
            subprocess
          - `one_shot`: `_process_file_one_shot_via_sequencer()` sends the
            prompt as a single `PromptSequencer.execute()` message, in-process
      - Topic inference (`_infer_topic_from_filename()`) is used by every
        branch above whenever `--topic` is not given explicitly
      - `--dry_run` (orthogonal to `--mode`/`--topic`/`--skill`/`--rule`):
        `_run_claude_code()`, `_process_file_one_shot_via_sequencer()`, and
        `_process_file_incrementally()` each write their full, untrimmed
        dry-run output (prompt/messages and the command that would have run,
        where applicable) to `tmp.cc_lint_dry_run.txt` instead of executing
        or printing to screen
  - After `_process_file()` returns, `_main()` runs post-processing from
    `topic_info` (`jupytext --sync`, `hlint.lint_file()`) for every mode

### Design Patterns

- **In-process session vs. subprocess delegation**:
  - `--mode one_shot_with_cc` writes a prompt file and shells out to the `cc`
    wrapper, piping output through `extract_cc_log2.py`
  - `--mode one_shot / session / stateless` use `PromptSequencer` API using
    different number of messages
- **Shared prompt, independent execution for the one-shot modes**:
  - `_build_one_shot_prompt()` is the single source of truth for what
    `one_shot_with_cc`/`one_shot` send Claude Code, so the two modes can only
    differ in how the prompt is delivered, never in its content
- **Permission callback for scoping**:
  - File-modification safety is enforced by an SDK `can_use_tool` callback
    (`_make_file_scope_guard()`), not by prompt wording
- **No-op contract over free-form replies**:
  - Each rule message demands a structured `LLM> NO-OP` / `LLM> CHANGED:
    <summary>` reply instead of letting the model narrate freely
- **Bias toward inclusion on pre-pass failure**: `_filter_relevant_chunks()`
  keeps every chunk unfiltered when the LLM reply cannot be parsed as a JSON
  list or would discard every chunk, since silently dropping an applicable
  rule is worse than one extra no-op turn
- **Merge never crosses a parent H1 or rule-file boundary**:
  `_merge_small_chunks()` only packs consecutive chunks that share the same
  parent H1 title and source `rule_file`, so packing never folds, e.g., the
  `# Verification` checklist into an unrelated neighboring chunk, nor two
  same-titled sections from different rule files
- **Check, don't fix, under `--add_todos`**: `_build_add_todos_instructions()`
  is the single source of truth for the `# TODO(ai_gp): ...` comment format,
  shared by every prompt-building path (one-shot and incremental) instead of
  each path inventing its own wording

### Invariants

- `--mode` (`one_shot_with_cc`/`one_shot`/`session`/`stateless`) and the
  "what" (`--topic`/`--skill`/`--rule`/default) are independent selections:
  exactly one "what" is active per invocation (enforced by an argparse
  mutually exclusive group plus `_main()`'s `num_exclusive` check), and it
  can be combined with any `--mode`
- `--add_todos` cannot be combined with `--skill` (enforced by `_main()`),
  since a skill invocation is a command for Claude Code's own skill loader,
  not declarative rule prose to check
- The incremental path never edits a file other than the one passed to
  `_process_file_incrementally()`
  - Enforced at the tool-permission layer via `target_file`, independent of what
    the rule text says
- Every incremental rule message names the target file explicitly (see
  `_build_rule_message()`), so its referent cannot drift as the rule sequence
  grows
- Sessions do not inherit ambient Claude settings: `PromptSequencer` defaults
  `setting_sources` to `[]`, so user- and project-level `CLAUDE.md` files and
  hooks cannot change what a lint run does from one machine to another
- Every prompt (single-shot or per-rule) carries the "do not change the
  behavior or intent of the file" instruction
- With `--order_rules_by_dependency`, a chunk under the `# Verification` H1
  is always sorted last regardless of its LLM-assigned category (see
  `_is_verification_chunk()`), since it is a terminal gate rather than a
  rule to apply mid-sequence
- Post-processing (`jupytext --sync`, `hlint.lint_file()`) runs whenever
  `topic_info` is populated
