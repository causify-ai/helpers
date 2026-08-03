# Phase 4: Checkpointing and Resume

## Journal Every Chunk Outcome

- Problem:
  - The observed run died partway through the sequence
  - Completed work was neither attributed nor resumable
  - `dev_scripts_helpers/ai/cc_lib.py` already defines `save_session_log()`, but
    `linters2/lint_cc.py` never calls it
- Change:
  - Write a JSON journal keyed by (`file_path`, `chunk_title`) holding:
    - `status`: one of `done`, `no_op`, `failed`, `skipped`
    - `cost_usd` and `num_turns`
  - Add `--resume` to skip entries already marked `done` or `no_op`
  - Reuse or extend `save_session_log()` rather than adding a parallel writer
- Done when: killing a run and rerunning with `--resume` continues where it
  stopped

## Bound Each Chunk

- Problem:
  - No per-prompt turn limit, so one rule can loop indefinitely
- Change:
  - Set `ClaudeAgentOptions.max_turns` to a small value per chunk

# Phase 5: Observability

## Report Real Cost and Usage

- Problem:
  - `PromptSequencer.execute()` concatenates `str(message)` for every message,
    including full tool inputs, and retains the result only to log its length
- Change:
  - Drop the concatenation
  - Capture the fields already carried by `ResultMessage`:
    - `total_cost_usd`
    - `usage`
    - `num_turns`
    - `is_error`
    - `terminal_reason`
  - Surface them from `get_execution_stats()` and in the journal
- Done when: the run prints total cost and per-chunk cost

## Show Inner Progress

- Problem:
  - The `tqdm` bar wraps only the outer file loop, so a long chunk sequence gives
    no progress or estimate
- Change:
  - Add a nested `tqdm` bar over the chunks of the current file
- Done when: a multi-file run reports progress at both levels

# Refactoring

- Problem:
  - `_build_prompt()` and `_build_incremental_messages()` each assemble the role,
    the templates, and the "do not change behavior" instruction, so the two modes
    can drift
- Change:
  - Factor the shared assembly into one builder used by both modes
  - Introduce the helpers:
    ```python
    def _build_rule_chunks(topic_info, *, level=2, max_tokens=1500) -> List[RuleChunk]
    def _filter_relevant_chunks(file_path, chunks) -> List[RuleChunk]
    def _apply_chunk(file_path, chunk, opts) -> ChunkResult
    ```
- Done when: the role and template text exists in exactly one place

# Verification

- Unit tests to add in `linters2/test/test_lint_cc.py`:
  - `_build_rule_chunks()` splits at the requested level and respects the token
    budget
  - `_build_rule_chunks()` carries the parent H1 title into each chunk
  - Chunk ordering puts the verification checklist last
  - The journal round-trips and `--resume` skips completed chunks
  - A fenced `# comment` line does not create a spurious chunk
- End-to-end checks:
  - `--dry_run` on a Python file, a test file, and a markdown file
  - A full run on a file known to be compliant, expecting `NO-OP` throughout and
    an unchanged file
  - A full run interrupted partway, then rerun with `--resume`

# Risks and Trade-Offs

- **Stateless mode loses cross-rule memory**:
  - Mitigated by keeping `--incremental_mode session` available
- **The relevance filter can discard a rule that did apply**:
  - Mitigated by logging discarded chunks and biasing the pre-pass toward
    inclusion
- **Per-chunk test runs are slow on large test files**:
  - Mitigated by `--verify_each_rule`, which can drop back to the `ast.parse()`
    gate only
- **Restricting the tool surface can block a legitimate rule**:
  - E.g., a rule that requires reading a sibling file for context
  - Mitigated by allowing reads anywhere while restricting writes to the target
- **Pinning the settings sources changes behavior for existing users**:
  - Mitigated by landing the change with a note in `linters2/lint_cc.README.md`
