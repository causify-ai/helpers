# cc_lint.py

Claude Code integration for topic-based intelligent formatting.

## What It Does

- Invokes Claude Code with intelligent topic-based or skill-based linting rules
- Detects file types by extension and path pattern to select appropriate rules
- Integrates with Claude rules and skills system for formatting and validation
- Supports batch processing with progress bars for multiple files

## Examples

- Format specific Python files:
  ```bash
  > cc_lint.py --files "file1.py file2.py"
  ```

- Apply a specific coding rule to a file:
  ```bash
  > cc_lint.py --topic coding --files "file.py"
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
  > linters2/cc_lint.py \
    --files dev_scripts_helpers/scraping/download_link_articles.py \
    --skill "coding.add_comments" \
    --model deepseek/deepseek-v4-flash
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

- Apply rules incrementally, one chunk per Claude interaction, with a fresh
  session per chunk (`--mode stateless`) or one session shared across all
  chunks (`--mode session`):
  ```bash
  > cc_lint.py --files "file.py" --mode stateless
  > cc_lint.py --files "file.py" --mode session
  ```
  - `stateless`: a fresh session per chunk, giving each chunk uniform cost and
    full attention
  - `session`: one session shared across all chunks, for rules that depend on
    each other
  - `--mode` is orthogonal to `--topic`/`--skill`/`--rule`/default: any of
    them can be combined with any `--mode`, e.g.
    ```bash
    > cc_lint.py --files "file.py" --skill coding.fix_inline --mode stateless
    > cc_lint.py --files "file.py" --rule ".claude/skills/coding.rules.md" --mode session
    ```
  - What gets chunked depends on the combination:
    - `--topic` / default: one chunk per H1 section across the topic's rule
      files
    - `--rule`: the rule text, split into one chunk per H1 section when it
      has more than one (whole-file spec), else kept as a single chunk
      (line-anchored spec)
    - `--skill`: a single, non-decomposed `/{skill} {file_path}` chunk
  - Every chunk sent as a rule (`--topic`/default/`--rule`) requires a
    structured `LLM> NO-OP` / `LLM> CHANGED: <summary>` reply so a compliant
    rule produces zero edits; a `--skill` chunk does not, since it invokes
    Claude Code's own skill loader instead of declarative rule prose
  - Useful for complex files requiring step-by-step rule application
  - `--mode one_shot` (the default) applies all rules in a single Claude Code
    invocation instead

- Preview incremental application without executing, saved to
  `tmp.cc_lint_dry_run.txt` instead of printed to screen:
  ```bash
  > cc_lint.py --files "file.py" --mode stateless --dry_run
  ```

## Software Architecture

### Data Flow

- `_main()`
  - Selects files
  - Asserts that at most one of `--topic`, `--skill`, and `--rule` is set
    (`--mode` is orthogonal and not part of this check)
  - Loops over files calling `_process_file()`
    - `_process_file()` dispatches on `args.mode` first, then on the "what"
      (`--topic`/`--skill`/`--rule`/default):
      - **`--mode session` / `--mode stateless`**:
        - `_process_file_incrementally()` builds the system prompt via
          `_build_incremental_system_prompt()` (role + templates + "do not
          change behavior"), then builds a message list depending on the
          "what":
          - `--skill`: a single `/{skill} {file_path}` message (via
            `hmarsele.find_skill()`), sent as-is
          - `--rule`: `hmarsele.extract_rule_from_file()`'s text, split into
            per-H1-section messages via `_build_incremental_messages_for_rule()`
            when it carries more than one, else a single message
          - `--topic` / default: `_build_incremental_messages()`, one H1
            section per topic rule file (`_extract_h1_sections()`), each
            templated by `_build_rule_message()` into a message that
            re-anchors on the target file path and demands a structured
            `LLM> NO-OP` / `LLM> CHANGED: <summary>` reply
        - hands the system prompt and messages to `PromptSequencer.execute()`
          from `dev_scripts_helpers/ai/cc_lib.py`, which
          - runs under `--mode`'s `context_strategy`: `stateless` opens a
            fresh `ClaudeSDKClient` per message, `session` shares one client
            across all messages
          - parses each reply's no-op contract via `_parse_rule_outcome()`,
            exposed as `get_outcomes()`
      - **`--mode one_shot`** (the default):
        - **Default** / `--topic`
          - `_build_prompt()` assembles one prompt (role + rule file references +
            "do not change behavior" instruction)
          - `_run_claude_code()` writes it to `tmp.cc_lint.prompt.txt` and shells
            out to the `cc` wrapper as a subprocess
        - `--skill` / `--rule`:
          - same `_run_claude_code()` path, with the prompt built from
            `hmarsele.find_skill()` or `hmarsele.extract_rule_from_file()` instead
            of `_build_prompt()`
      - Topic inference (`_infer_topic_from_filename()`) is used by every
        branch above whenever `--topic` is not given explicitly
      - `--dry_run` (orthogonal to `--mode`/`--topic`/`--skill`/`--rule`):
        `_run_claude_code()` and `_process_file_incrementally()` each write
        their full, untrimmed dry-run output (prompt/messages and the
        command that would have run) to `tmp.cc_lint_dry_run.txt` instead
        of executing or printing to screen
  - After `_process_file()` returns, `_main()` runs post-processing from
    `topic_info` (`jupytext --sync`, `hlint.lint_file()`) for every mode

### Design Patterns

- **In-process session vs. subprocess delegation**:
  - the single-shot paths write a prompt file and shell out to the `cc` wrapper,
    piping output through `extract_cc_log2.py`
  - the incremental path talks to `claude_agent_sdk.ClaudeSDKClient` directly,
    with `--mode` choosing whether one session spans all messages or each
    message gets its own
- **Permission callback for scoping**: file-modification safety is enforced by an
  SDK `can_use_tool` callback (`_make_file_scope_guard()`), not by prompt wording
- **No-op contract over free-form replies**: each rule message demands a
  structured `LLM> NO-OP` / `LLM> CHANGED: <summary>` reply instead of letting
  the model narrate freely, so a compliant file produces zero edits instead of
  forced churn

### Invariants

- `--mode` (`one_shot`/`session`/`stateless`) and the "what"
  (`--topic`/`--skill`/`--rule`/default) are independent selections: exactly
  one "what" is active per invocation (enforced by an argparse mutually
  exclusive group plus `_main()`'s `num_exclusive` check), and it can be
  combined with any `--mode`
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
