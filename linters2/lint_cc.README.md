# lint_cc.py

Claude Code integration for topic-based intelligent formatting.

## What It Does

- Invokes Claude Code with intelligent topic-based or skill-based linting rules
- Detects file types by extension and path pattern to select appropriate rules
- Integrates with Claude rules and skills system for formatting and validation
- Supports batch processing with progress bars for multiple files

## Examples

- Format specific Python files:
  ```bash
  > lint_cc.py --files "file1.py file2.py"
  ```

- Apply a specific coding rule to a file:
  ```bash
  > lint_cc.py --topic coding --files "file.py"
  ```

- Lint modified files in the repository:
  ```bash
  > lint_cc.py --modified
  ```

- Preview command without executing (dry-run):
  ```bash
  > lint_cc.py --dry_run --files "*.md"
  ```

- Process multiple files with progress feedback:
  ```bash
  > lint_cc.py --files "src/*.py" --topic coding
  ```

- Use a different model:
  ```bash
  linters2/lint_cc.py --files dev_scripts_helpers/scraping/download_link_articles.py --skill "coding.add_comments" --model deepseek/deepseek-v4-flash
  ```

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

- Apply rules incrementally, one rule per Claude interaction:
  ```bash
  > lint_cc.py --files "file.py" --apply_incrementally
  ```
  - Extracts H1 sections from rule files
  - Sends each rule to Claude Code as its own turn, re-anchored on the target
    file path
  - Requires a structured `LLM> NO-OP` / `LLM> CHANGED: <summary>` reply so a
    compliant rule produces zero edits
  - Useful for complex files requiring step-by-step rule application

- Choose the context strategy for `--apply_incrementally`:
  ```bash
  > lint_cc.py --files "file.py" --apply_incrementally --incremental_mode session
  ```
  - `stateless` (default): a fresh session per rule, giving each rule uniform
    cost and full attention
  - `session`: one session shared across all rules, for rules that depend on
    each other

- Preview incremental application without executing:
  ```bash
  > lint_cc.py --files "file.py" --apply_incrementally --dry_run
  ```

## Software Architecture

### Data Flow

- `_main()`
  - Selects files
  - Asserts that at most one of `--topic`, `--skill`, `--rule`,
    `--apply_incrementally` is set
  - Loops over files calling `_process_file()`
    - `_process_file()` dispatches to one of the modes:
      - **Default / `--topic`**:
        - `_build_prompt()` assembles one prompt (role + rule file references +
          "do not change behavior" instruction)
        - `_run_claude_code()` writes it to `tmp.lint_cc.prompt.txt` and shells
          out to the `cc` wrapper as a subprocess
      - **`--skill`** / **`--rule`**:
        - same `_run_claude_code()` path, with the prompt built from
          `hmarsele.find_skill()` or `hmarsele.extract_rule_from_file()` instead
          of `_build_prompt()`
      - **`--apply_incrementally`**:
        - `_process_file_incrementally()`
          - builds the system prompt via `_build_incremental_system_prompt()`
            (role + templates + "do not change behavior")
          - builds a message list via `_build_incremental_messages()`
            - one H1 section per topic rule file (`_extract_h1_sections()`), each
              templated by `_build_rule_message()` into a message that re-anchors
              on the target file path and demands a structured `LLM> NO-OP` /
              `LLM> CHANGED: <summary>` reply
          - hands the system prompt and messages to `PromptSequencer.execute()`
            from `dev_scripts_helpers/ai/cc_lib.py`, which
            - runs under `--incremental_mode`'s `context_strategy`: `stateless`
              opens a fresh `ClaudeSDKClient` per message, `session` shares one
              client across all messages
            - parses each reply's no-op contract via `_parse_rule_outcome()`,
              exposed as `get_outcomes()`
        - Topic inference (`_infer_topic_from_filename()`) is shared by all four
          modes whenever `--topic` is not given explicitly
  - After `_process_file()` returns, `_main()` runs post-processing from
    `topic_info` (`jupytext --sync`, `hlint.lint_file()`) for every mode

### Design Patterns

- **In-process session vs. subprocess delegation**:
  - the single-shot paths write a prompt file and shell out to the `cc` wrapper,
    piping output through `extract_cc_log2.py`
  - the incremental path talks to `claude_agent_sdk.ClaudeSDKClient` directly,
    with `--incremental_mode` choosing whether one session spans all messages
    or each message gets its own
- **Permission callback for scoping**: file-modification safety is enforced by an
  SDK `can_use_tool` callback (`_make_file_scope_guard()`), not by prompt wording
- **No-op contract over free-form replies**: each rule message demands a
  structured `LLM> NO-OP` / `LLM> CHANGED: <summary>` reply instead of letting
  the model narrate freely, so a compliant file produces zero edits instead of
  forced churn

### Invariants

- Exactly one action mode is active per invocation (`--topic`, `--skill`,
  `--rule`, or `--apply_incrementally`)
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
- Post-processing (`jupytext --sync`, `hlint.lint_file()`) runs whenever
  `topic_info` is populated
